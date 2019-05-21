"""
:author: Laurens Koppenol

The game engine for a 2D racing game, using the pygame library. Built to demonstrate the concept behavioral learning.

Custom track can be built in paint, please see :doc:`getting-started` for more information.

"""

import time
import functools
import math
import random

from PIL import Image
import numpy as np
from loguru import logger
import pygame
from pygame import freetype

from src import bresenham

freetype.init()


def dropped_frame_checker(seconds_per_frame):
    # Decorator that checks if a function is executed within frame time, and if not how many frame are skipped
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            planned_next_frame = int(time.time() / seconds_per_frame)
            f(*args, **kwargs)
            actual_next_frame = int(time.time() / seconds_per_frame)
            if planned_next_frame != actual_next_frame:
                frames_skipped = actual_next_frame - planned_next_frame
                logger.warning(f"game thread skipped {frames_skipped} frame(s)")
        return wrapper
    return decorator


class Engine(object):
    """
    The game engine is responsible for the game logic per turn, listening game events (key inputs) and drawing the game.
    Can be kicked off by calling engine.play(), which repeatedly calls engine._turn().
    """
    RUNNING = 0
    FINISHED = 1
    SECONDS_PER_FRAME = 1/30  # Step size of turns. Slows down the game if frames are dropped
    SCALE = 1/0.3  # Changing might ruin gaming experience
    ACCELERATION = 5
    ROTATION_SPEED = 180

    def __init__(self, environment, players):
        """
        :param environment: instance of game.Environment
        :param players: iterable of subclasses of player.Player
        """
        pygame.init()

        self.game_status = Engine.RUNNING
        self.track = environment

        self.players = []
        self._setup_players(players)

        self.keys = self._setup_keys()
        self.screen = self._setup_graphics()
        self.game_settings = self._setup_game_settings()
        self.key_bindings = self._setup_key_bindings()

        random.seed(42)

    def play(self, stop_on_death=True):
        """
        Start the game!
        Does not start a thread; will hold execution until game is completed.
        :param stop_on_death: Wether to stop if all players are ded irl
        :return: self
        """
        while self.is_running():
            self._turn()

            if stop_on_death and self._is_game_over():
                self._end_game()

            if self.game_settings['fps_limiter']:
                time_to_next_frame = self.SECONDS_PER_FRAME - time.time() % self.SECONDS_PER_FRAME
                time.sleep(time_to_next_frame)
        return self

    def is_running(self):
        """
        Check if all players are ded irl
        :return: boolean
        """
        return self.game_status == Engine.RUNNING

    def add_player(self, player):
        """
        Add a player to the game while the game is running.
        :param player: instance of player.Player
        :return: self
        """
        player_id = len(self.players)
        player = self._init_player(player, player_id)
        self.players.append(player)
        return self

    def bind_action(self, key, action):
        """
        Bind an action to a pygame key. Example usage:

        > game_engine.bind_action(pygame.K_a, lambda: print(123))
        prints 123 when 'a' is pressed during the game.

        :param key: pygame key index
        :param action: function to call
        :return:
        """
        self.key_bindings[key] = action

    def get_scores(self):
        """
        Get a dictionary of scores on the scoreboard.

        :return: dict {player_id: score}
        """
        scores = {
            player.id: player.score for player in self.players
        }
        return scores

    def get_player(self, player_id):
        """
        Get the player object that corresponds with given player_id

        :param player_id: integer
        :return: player.Player object
        """
        player = self.players[player_id]
        return player

    def get_best_player(self):
        """
        Get the player object of the player with the lowest score (furthest in the race)

        :return: player.Player object
        """
        scores = self.get_scores()
        best_player_id = min(scores, key=scores.get)
        best_player = self.get_player(best_player_id)
        return best_player

    def get_worst_player(self):
        """
        Get the player object of the player with the highest score (furthest from the finish)

        :return: player.Player object
        """
        scores = self.get_scores()
        best_player_id = max(scores, key=scores.get)
        best_player = self.get_player(best_player_id)
        return best_player

    def remove_all_players(self, keep=list()):
        """
        Destroys the reference to all existing players

        :param keep: optional list of player.Player instances to keep
        :return: self
        """
        self.players = keep
        return self

    def _init_player(self, player, player_id):
        """
        Set position, color and id for a player

        :param player: player.Player
        :param player_id: id to give to player
        :return: player
        """
        player.set_position(self.track.start)
        player.id = player_id
        player.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        return player

    def _setup_players(self, players):
        """
        initialise all starting players

        :param players: list of player.Player objects
        :return: self
        """
        for player in players:
            self.add_player(player)
        return self

    def _setup_graphics(self):
        """
        Prepare the pygame graphics

        :return: pygame.screen canvas to draw on
        """
        size = (
            int(self.track.width * Engine.SCALE),
            int(self.track.height * Engine.SCALE)
        )
        pygame.display.set_caption('Train-a-Train')
        icon = pygame.image.load('visuals/icon.png')
        pygame.display.set_icon(icon)
        screen = pygame.display.set_mode(size)

        train = pygame.image.load('visuals/train.png')
        self.train = pygame.transform.scale(train, (78, 21))

        font_size = Engine.SCALE * 3
        self.roboto_font = freetype.Font('visuals/roboto.ttf', size=font_size)

        return screen

    def _setup_key_bindings(self):
        """
        # Set up the initial key bindings using a dictionary of keys to listen to with corresponding functions. This
        makes it easy to add new functions to new keys.

        :return: dict of key bindings.
        """
        key_bindings = {
            pygame.K_1: self._toggle_draw_train,
            pygame.K_2: self._toggle_draw_sensors,
            pygame.K_3: self._toggle_draw_background,
            pygame.K_4: self._toggle_fps_limiter
        }
        return key_bindings

    @staticmethod
    def _setup_keys():
        """
        Gives the arrow keys a special status. The game will keep track per turn whether the key was down or not.

        :return: dict of keys and down-status
        """
        keys = {
            pygame.K_LEFT: False,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_RIGHT: False
        }
        return keys

    @staticmethod
    def _setup_game_settings():
        """
        Game settings that can be toggled using the initial key bindings

        :return: dict of options
        """
        toggle_options = dict(
            train=0,
            sensors=False,
            background=0,
            fps_limiter=True
        )
        return toggle_options

    @dropped_frame_checker(SECONDS_PER_FRAME)
    def _turn(self):
        """
        A game turn consists of a check of keyboard events, a resolve loop per player and a drawing fase.

        :return: Nothing
        """
        self._handle_pygame_events()
        for player in self.players:
            self._player_turn(player)

        self._draw()

    def _player_turn(self, player):
        """
        Perform the sense-plan-act-resolve loop. The resolve can be per player as there is no possible interaction.

        :param player: player.Player object
        :return: Nothing
        """
        if player.alive:
            percepts = player.sense(self.track, self.keys)
            acceleration_command, rotation_command = player.plan(percepts)
            movement = self._act(player, acceleration_command, rotation_command, self.SECONDS_PER_FRAME)
            self._resolve(player, movement)

    def _is_game_over(self):
        """
        Check if there is a player that is alive

        :return: True if any player is alive
        """
        for player in self.players:
            if player.alive:
                return False
        else:
            return True

    def _end_game(self):
        """
        Gracefully close pygame

        :return: self
        """
        pygame.quit()
        self.game_status = Engine.FINISHED
        return self

    def _draw(self):
        """
        Called for every frame.
        Can draws the background, player (including sensors) and score.
        Drawing is done by placing drawables on the canvas (self.screen) and calling pygame.display.update()

        :return: Nothing
        """
        self._draw_background()

        # Draw players
        for player in self.players:
            self._draw_train(player)
            if self.game_settings['sensors']:
                for sensor in player.sensors:
                    self._draw_sensor(player, sensor)

        self._draw_score()

        pygame.display.update()

    def _act(self, player, acceleration_command, rotation_command, delta_time):
        """
        Based on the selected actions of the player, the player state is altered

        :param player: a child class of Player
        :param acceleration_command: between -1 (breaking) and 1 (accelerating)
        :param rotation_command: between -1 (left) and 1 (right)
        :param delta_time: time since last turn in seconds
        :return: target location of the player (x, y)
        """
        acceleration_command = max(-1, acceleration_command)  # prevent cheating
        acceleration_command = min(1, acceleration_command)  # prevent cheating
        new_speed = player.speed + acceleration_command * self.ACCELERATION * delta_time
        player.speed = max(new_speed, 0)

        # forces rotation to be in range [0, 360]
        rotation_command = max(-1, rotation_command)  # prevent cheating
        rotation_command = min(1, rotation_command)  # prevent cheating
        new_rotation = player.rotation + rotation_command * self.ROTATION_SPEED * delta_time
        player.rotation = (new_rotation + 360) % 360

        destination = self.track.translate(player.position, player.speed, player.rotation)
        return destination

    def _resolve(self, player, destination):
        """
        Alter the position of the player and check if this causes a finish or collission

        :param player: a child class of Player
        :param destination: target location of the player (x, y)
        :return: nothing
        """
        player.set_position(destination)

        score = self.track.get_distance(player)
        if score > 0:
            player.score = score

        collision = self.track.check_collision(player)
        if collision or player.score == 1:
            player.alive = False
            # TODO: Handle score

    def _handle_pygame_events(self):
        """
        Handles all key events that have occured since last loop The active arrow keys are stored and passed to
        Player.sense() in the game loop.

        :return: nothing
        """
        events = pygame.event.get()
        for event in events:
            if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                self._handle_key_event(event)

    def _handle_key_event(self, key_event):
        if key_event.key in self.keys.keys():
            key_active = key_event.type == pygame.KEYDOWN
            self.keys[key_event.key] = key_active
        elif key_event.type == pygame.KEYDOWN:
            try:
                action = self.key_bindings[key_event.key]
                action()
            except KeyError:
                pass

    def _toggle_draw_train(self):
        """
        Set the draw status of train to either full (0), basic(1) or none(2)

        :return: nothing
        """
        self.game_settings['train'] = (self.game_settings['train'] + 1) % 3
        logger.debug(f"Drawing train toggled, status now {self.game_settings['train']}")

    def _toggle_draw_sensors(self):
        """
        Set the draw status of the sensors to True or False

        :return: nothing
        """
        self.game_settings['sensors'] = not self.game_settings['sensors']
        logger.debug(f"Drawing sensors toggled, status now {self.game_settings['sensors']}")

    def _toggle_draw_background(self):
        """
        Set the draw status of background to either full(0), boundaries(1) or nothing(2)

        :return:
        """
        self.game_settings['background'] = (self.game_settings['background'] + 1) % 3
        logger.debug(f"Drawing background toggled, status now {self.game_settings['background']}")

    def _toggle_fps_limiter(self):
        """
        Toggle whether to limit the number of frames that pass.

        :return:
        """
        self.game_settings['fps_limiter'] = not self.game_settings['fps_limiter']
        logger.debug(f"FPS limiter toggled, status now {self.game_settings['fps_limiter']}")

    def _draw_score(self):
        """
        Draw a vertical bar with scores per player

        :return:
        """
        pygame.draw.rect(
            self.screen,
            (0, 0, 0),
            pygame.Rect(
                0,
                0,
                self.screen.get_width() * 0.05,
                self.screen.get_height()
            )
        )

        for i, player in enumerate(self.players):
            score_text = f"{player.id:03} - {player.score:03.0f}"
            y = i * 3 * Engine.SCALE
            self.roboto_font.render_to(
                self.screen,
                (0, y),
                score_text,
                fgcolor=player.color
            )

    def _draw_background(self):
        """
        Draw the background based on given option

        :return:
        """
        if self.game_settings['background'] == 0:
            self.screen.blit(self.track.drawables['background'], (0, 0))
        elif self.game_settings['background'] == 1:
            self.screen.blit(self.track.drawables['raw'], (0, 0))
        elif self.game_settings['background'] == 2:
            self.screen.blit(self.track.drawables['distance_matrix'], (0, 0))
        elif self.game_settings['background'] == 3:
            self.screen.fill((0, 0, 0))

    def _draw_train(self, player):
        """
        Draw the train for a given player. Scales the position to game window pixel coordinates.

        :param player: child class of Player
        :return: nothing
        """
        scaled_x, scaled_y = player.get_position(scale=self.SCALE)
        if self.game_settings['train'] == 0:
            sprite = pygame.transform.rotate(self.train, -player.rotation + 90)
            self._draw_sprite(sprite, scaled_x, scaled_y)
        elif self.game_settings['train'] == 1:
            # Set target
            target = self.track.translate(
                player.position,
                3,
                player.rotation
            )

            # Scale and draw
            scaled_origin = player.get_position(scale=self.SCALE)
            scaled_target = [p * self.SCALE for p in target]
            pygame.draw.line(
                self.screen,
                player.color,
                scaled_origin,
                scaled_target,
                5
            )
        elif self.game_settings['train'] == 2:
            pass

    def _draw_sensor(self, player, sensor):
        """
        Draw given sensor for given player. Scales the target and destination of sensor to given location. Currently
        only supports line-like sensors that have the following attributes: percept, depth, get_absolute_angle()

        :param player: subclass of Player
        :param sensor: Sensor object, see DistanceSensor for example
        :return: nothing
        """
        if sensor.is_drawable:
            # Determine color and length based on percept value.
            if sensor.percept is sensor.depth:
                color = (0, 255, 0)
            else:
                color = (255, 255, 255)

            # Set target
            target = self.track.translate(
                player.position,
                sensor.percept,
                sensor.get_absolute_angle()
            )

            # Scale and draw
            scaled_origin = player.get_position(scale=self.SCALE)
            scaled_target = [p * self.SCALE for p in target]
            pygame.draw.line(
                self.screen,
                color,
                scaled_origin,
                scaled_target
            )

    def _draw_sprite(self, sprite, x, y):
        """
        Draw a sprite based on given center coordinates

        :param sprite: pygame sprite
        :param x: horizontal scaled gui coordinate
        :param y: vertical scaled gui coordinate
        :return: nothing
        """
        width = sprite.get_width()
        height = sprite.get_height()

        corner_x = x - 0.5 * width
        corner_y = y - 0.5 * height

        self.screen.blit(sprite, (corner_x, corner_y))


class Environment(object):
    """
    Object that takes a png image and transforms it into a racing track. To create a new track take the following into
    account:
    Walls must have red-channel >= 128
    Starting position is the first pixel with green-channel >= 128
    Finish are all pixels with blue-channel >= 128

    To determine score all pixels that are reachable from the finish are given their manhattan distance to the nearest
    finish point.

    This class also contains environment related helper functions.
    """
    def __init__(self, track):
        """

        :param track: must correspond to the name of a folder in tracks/foldername
        """
        track_path = f'tracks/{track}/track.png'
        background_path = f'tracks/{track}/track_bg.png'

        track_img = Image.open(track_path)
        self.width = track_img.width
        self.height = track_img.height
        self.boundaries, self.finish, self.start = self.parse_track(track_img)
        self.distance_matrix = self.get_distance_matrix()

        self.drawables = self._setup_drawables(track_path, background_path)

    @staticmethod
    def parse_track(track_img):
        """
        Extract track boundaries, start and finish from a png-pillow image.

        :param track_img: png-pillow image
        :return: boundaries, finish and start as Numpy ndarrays
        """
        rgb_img = track_img.convert('RGB')
        raw_data = np.asarray(rgb_img)

        # transpose x and y and flip y to match the arcade coordinates
        transposed_data = np.transpose(raw_data, (1, 0, 2))

        # red channel is boundary (walls)
        red_channel = transposed_data[:, :, 0]
        boundaries = red_channel >= 128

        # blue channel is finish
        blue_channel = transposed_data[:, :, 2]
        finish = np.transpose(np.nonzero(blue_channel))

        # green channel is starting point
        green_channel = transposed_data[:, :, 1]
        start = np.transpose(np.nonzero(green_channel))[0]

        return boundaries, finish, start

    def check_collision(self, player):
        """
        check if a given player is colliding with a boundary (red pixel)

        :param player: subclass of Player
        :return: True or False
        """
        pixel_x, pixel_y = player.get_position(pixel=True)
        collision = self.boundaries[pixel_x, pixel_y]
        return collision

    def get_distance(self, player):
        """
        Check how many pixels (manhattan distance) a player is located from the finish

        :param player: subclass of Player
        :return: integer, 0 for wall, 1 for finish, > 1 for anything else
        """
        pixel_x, pixel_y = player.get_position(pixel=True)
        distance = self.distance_matrix[pixel_x, pixel_y]
        return distance

    def ray_trace_to_wall(self, position, angle, distance):
        """
        Use the bresenham algorithm to find the nearest wall over a angle and distance, returns None if no wall found.
        See the bresenham module for more information about the algorithm.

        :param position: origin (x, y)
        :param angle: angle in degrees
        :param distance: int or float
        :return: distance to nearest wall or None
        """
        origin = self.location_to_pixel(position)
        target = self.translate(position, distance, angle, pixel=True)

        line_of_sight = bresenham.get_line(
            origin,
            target
        )
        for i, pixel in enumerate(line_of_sight):
            if self.boundaries[pixel]:
                return i
        else:
            return None

    def get_distance_matrix(self):
        """
        Generate the distance map with manhattan distances to the finish by calling the private recursive_distance
        function.

        :return: numpy ndarray with distances
        """
        finish_points = [(i[0], i[1]) for i in self.finish]
        distance_matrix = self._recursive_distance(
            distance_matrix=np.zeros(self.boundaries.shape),
            points=finish_points,
            distance=1
        )
        return distance_matrix

    def _distance_matrix_to_drawable(self):
        # Unreadable ugly ass function
        # TODO: beautify
        drawable = self.distance_matrix * (255 / self.distance_matrix.max())
        w, h = drawable.shape
        grayscale = np.empty((w, h, 3), dtype=np.uint8)
        grayscale[:, :, 2] = grayscale[:, :, 1] = grayscale[:, :, 0] = drawable
        surface = pygame.surfarray.make_surface(grayscale)
        size = (
            int(self.width * Engine.SCALE),
            int(self.height * Engine.SCALE)
        )
        drawable = pygame.transform.scale(surface, size)
        return drawable

    def _recursive_distance(self, distance_matrix, points, distance):
        """
        Find all neighboring pixels and give them value distance + 1

        :param distance_matrix: Numpy ndarray with current distances
        :param points: List of coorindates
        :param distance: current distance
        :return: numpy ndarray with distances
        """
        # Set distance values
        for point in points:
            distance_matrix[point] = distance

        # Determine neighbor points
        valid_next_points = set()
        for point in points:
            for dx in [-1, 1]:
                for dy in [-1, 1]:
                    one_further = (
                        point[0] + dx,
                        point[1] + dy
                    )
                    try:
                        if (not self.boundaries[one_further]) and distance_matrix[one_further] == 0:
                            valid_next_points.add(one_further)
                    except IndexError:
                        pass

        # Next iteration
        if len(valid_next_points) > 0:
            distance_matrix = self._recursive_distance(
                distance_matrix,
                valid_next_points,
                distance + 1
            )
        return distance_matrix

    def _setup_drawables(self, track_path, background_path):
        """
        Use the track sprites to create fitting images for the game

        :param track_path: path to the raw track
        :param background_path: path to the fancy background for the track
        :return: dict(background, raw)
        """
        size = (
            int(self.width * Engine.SCALE),
            int(self.height * Engine.SCALE)
        )

        background = pygame.image.load(background_path)
        scaled_background = pygame.transform.scale(background, size)

        track = pygame.image.load(track_path)
        scaled_track = pygame.transform.scale(track, size)

        distance_matrix_drawable = self._distance_matrix_to_drawable()

        drawables = dict(
            background=scaled_background,
            raw=scaled_track,
            distance_matrix=distance_matrix_drawable
        )

        return drawables

    @staticmethod
    def translate(position, distance, rotation, pixel=False):
        """
        Translate a coordinaten given a distance and rotation. Can round to integer pixel coordinates

        :param position: origin (x, y)
        :param distance: int or float
        :param rotation: angle in degrees
        :param pixel: whether to round to integer pixel coorindates
        :return: new position (x, y)
        """
        rotation_rad = math.radians(rotation - 90)
        d_x = math.cos(rotation_rad) * distance
        d_y = math.sin(rotation_rad) * distance

        x = position[0] + d_x
        y = position[1] + d_y

        if pixel:
            x, y = Environment.location_to_pixel((x, y))
        return x, y

    @staticmethod
    def location_to_pixel(coordinate):
        """
        Round a coordinate to integer pixel coordinates

        :param coordinate: (x, y)
        :return: (int, int)
        """
        rounded_coordinate = (
            int(round(coordinate[0])),
            int(round(coordinate[1]))
        )
        return rounded_coordinate
