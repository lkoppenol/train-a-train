"""
@Author Laurens Koppenol

The game engine for a 2D racing game, using the arcade library. Built to demonstrate the concept behavioral learning.

Custom track can be built in paint, please see the Environment object for more information.

Example usage:
track = Environment('track.png')
players = [HumanPlayer(), Ai()]
game_engine = Engine(track, 1 / 0.3, players)
arcade.run()
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

import bresenham


def dropped_frame_checker(seconds_per_frame):
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


class Drawables(object):
    freetype.init()
    background = pygame.image.load('track_bg.png')
    track = pygame.image.load('track.png')
    train = pygame.image.load('train.png')
    font = freetype.Font('roboto.ttf')


class Engine(object):
    """
    The game engine, consiting of 2 seperate loops. A GUI loop which triggers Engine.on_draw(), and the game loop which
    triggers Engine.update().
    """
    RUNNING = 0
    FINISHED = 1
    SECONDS_PER_FRAME = 1/30
    SCALE = 1/0.3
    ACCELERATION = 5
    ROTATION_SPEED = 180

    def __init__(self, track, player_types):
        pygame.init()

        self.game_status = Engine.RUNNING
        self.track = track

        self.players = self._setup_players(player_types)
        self.keys = self._setup_keys()
        self.screen = self._setup_screen()
        self.game_settings = self._setup_game_settings()
        self.key_bindings = self._setup_key_bindings()

        random.seed(42)

    def play(self, stop_on_death=True):
        while self.is_running():
            self._turn()

            if stop_on_death and self._is_game_over():
                self._end_game()

            if self.game_settings['fps_limiter']:
                time_to_next_frame = self.SECONDS_PER_FRAME - time.time() % self.SECONDS_PER_FRAME
                time.sleep(time_to_next_frame)

    def is_running(self):
        return self.game_status == Engine.RUNNING

    def add_player(self, player_class):
        player_id = len(self.players)
        player = self._init_player(player_class, player_id)
        self.players.append(player)
        return self

    def bind_action(self, key, action):
        self.key_bindings[key] = action

    def _init_player(self, player_class, player_id):
        player = player_class()
        player.set_position(self.track.start)
        player.id = player_id
        player.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        return player

    def _setup_players(self, player_types):
        players = []
        for i, player_type in enumerate(player_types):
            player = self._init_player(player_type, i)
            players.append(player)
        return players

    def _setup_screen(self):
        size = (
            int(self.track.width * Engine.SCALE),
            int(self.track.height * Engine.SCALE)
        )
        screen = pygame.display.set_mode(size)

        Drawables.background = pygame.transform.scale(Drawables.background, size)
        Drawables.track = pygame.transform.scale(Drawables.track, size)
        Drawables.train = pygame.transform.scale(Drawables.train, (78, 21))
        Drawables.font.size = Engine.SCALE * 3

        return screen

    def _setup_key_bindings(self):
        key_bindings = {
            pygame.K_1: self._toggle_draw_train,
            pygame.K_2: self._toggle_draw_sensors,
            pygame.K_3: self._toggle_draw_background,
            pygame.K_4: self._toggle_fps_limiter
        }
        return key_bindings

    @staticmethod
    def _setup_keys():
        keys = {
            pygame.K_LEFT: False,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_RIGHT: False
        }
        return keys

    @staticmethod
    def _setup_game_settings():
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
        A game consists of a sense-plan-act-resolve loop for every player, followed by a check if game is over yet.

        :return: Nothing
        """
        self._handle_pygame_events()
        for player in self.players:
            self._player_turn(player)

        self._draw()

    def _player_turn(self, player):
        # Perform the sense-plan-act-resolve loop. The resolve can be per player as there is no possible interaction.
        if player.alive:
            # TODO: pass speed and rotations as input
            percepts = player.sense(self.track, self.keys)
            acceleration_command, rotation_command = player.plan(percepts)
            movement = self._act(player, acceleration_command, rotation_command, self.SECONDS_PER_FRAME)
            self._resolve(player, movement)

    def _is_game_over(self):
        # Check if there is a player that is alive
        for player in self.players:
            if player.alive:
                return False
        else:
            return True

    def _end_game(self):
        pygame.quit()
        self.game_status = Engine.FINISHED

    def _draw(self):
        """
        Called by arcade for every frame.
        Draws the background, player and possibly debug information
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
        new_speed = player.speed + acceleration_command * self.ACCELERATION * delta_time
        player.speed = max(new_speed, 0)

        # forces rotation to be in range [0, 360]
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
        if key_event.key in [pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_RIGHT]:
            key_active = key_event.type == pygame.KEYDOWN
            self.keys[key_event.key] = key_active
        elif key_event.type == pygame.KEYDOWN:
            try:
                action = self.key_bindings[key_event.key]
                action()
            except KeyError:
                pass

    def _toggle_draw_train(self):
        self.game_settings['train'] = (self.game_settings['train'] + 1) % 3
        logger.debug(f"Drawing train toggled, status now {self.game_settings['train']}")

    def _toggle_draw_sensors(self):
        self.game_settings['sensors'] = not self.game_settings['sensors']
        logger.debug(f"Drawing sensors toggled, status now {self.game_settings['sensors']}")

    def _toggle_draw_background(self):
        self.game_settings['background'] = (self.game_settings['background'] + 1) % 3
        logger.debug(f"Drawing background toggled, status now {self.game_settings['background']}")

    def _toggle_fps_limiter(self):
        self.game_settings['fps_limiter'] = not self.game_settings['fps_limiter']
        logger.debug(f"FPS limiter toggled, status now {self.game_settings['fps_limiter']}")

    def _draw_score(self):
        # Background
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
            Drawables.font.render_to(
                self.screen,
                (0, y),
                score_text,
                fgcolor=player.color
            )

    def _draw_background(self):
        # Draw background
        if self.game_settings['background'] == 0:
            self.screen.blit(Drawables.background, (0, 0))
        elif self.game_settings['background'] == 1:
            self.screen.blit(Drawables.track, (0, 0))
        elif self.game_settings['background'] == 2:
            self.screen.fill((0, 0, 0))

    def _draw_train(self, player):
        """
        Draw the train for a given player. Scales the position to game window pixel coordinates.

        :param player: child class of Player
        :return: nothing
        """
        scaled_x, scaled_y = player.get_position(scale=self.SCALE)
        if self.game_settings['train'] == 0:
            sprite = pygame.transform.rotate(Drawables.train, -player.rotation + 90)
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
        # Determine color and length based on percept value.
        if sensor.percept is None:
            distance = sensor.depth
            color = (0, 255, 0)
        else:
            distance = sensor.percept
            color = (255, 255, 255)

        # Set target
        target = self.track.translate(
            player.position,
            distance,
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
    def __init__(self, path):
        """
        :param path: path to a png with track information
        """
        track_img = Image.open(path)
        self.path = path
        self.width = track_img.width
        self.height = track_img.height
        self.boundaries, self.finish, self.start = self.parse_track(track_img)
        self.distance_matrix = self.get_distance_matrix()

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
