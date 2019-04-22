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

from PIL import Image
import numpy as np
import arcade
import math
import bresenham


class Engine(arcade.Window):
    """
    The game engine, consiting of 2 seperate loops. A GUI loop which triggers Engine.on_draw(), and the game loop which
    triggers Engine.update().
    """
    def __init__(self, track, scale, players):
        super().__init__(int(track.width / 0.3), int(track.height / 0.3))

        # TODO: setup function
        self.track = track
        self.players = players
        for player in players:
            player.set_position(track.start)

        self.background = arcade.load_texture('track_bg.png')
        self.fps = 0
        self.scale = scale
        self.score = dict()
        self.clock = 0

        self.game_status = 0
        
        self.keys = {
            arcade.key.UP: False,
            arcade.key.DOWN: False,
            arcade.key.LEFT: False,
            arcade.key.RIGHT: False
        }

        self.ACCELERATION = 5
        self.ROTATION_SPEED = 180
        self.GAME_LENGTH = 10

    def on_draw(self):
        """
        Called by arcade for every frame.
        Draws the background, player and possibly debug information
        :return: Nothing
        """
        arcade.start_render()

        # Draw background
        arcade.draw_texture_rectangle(
            self.width // 2,
            self.height // 2,
            self.width,
            self.height,
            self.background
        )

        # Draw players
        for player in self.players:
            self._draw_train(player)
            for sensor in player.sensors:
                self._draw_sensor(player, sensor)

        # Draw other
        self._draw_debug()

    def update(self, delta_time):
        """
        Called by the arcade library or headless mode. Equals 1 game turn.
        A game consists of a sense-plan-act-resolve loop for every player, followed by a check if game is over yet.

        :param delta_time: the time passed since previous turn in seconds.
        :return: Nothing
        """
        # TODO: fix delta_time for optimal gaming experience
        delta_time = 0.01

        # Total game time
        self.clock += delta_time

        # Perform the sense-plan-act-resolve loop. The resolve can be per player as there is no possible interaction.
        for player in self.players:
            if player.alive:
                # TODO: pass speed and rotations as input
                percepts = player.sense(self.track, self.keys)
                acceleration_command, rotation_command = player.plan(percepts)
                movement = self.act(player, acceleration_command, rotation_command, delta_time)
                self.resolve(player, movement)

        # Check if there is a player that is alive
        for player in self.players:
            if player.alive:
                break
        else:
            arcade.close_window()
            self.game_status = 1

        # Check if game time is run out
        if self.clock > self.GAME_LENGTH:
            arcade.close_window()
            self.game_status = 1

        self.fps = 1 / delta_time

    def act(self, player, acceleration_command, rotation_command, delta_time):
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

    def resolve(self, player, destination):
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

    def on_key_press(self, key, modifiers):
        """
        Called by arcade when a key is pressed. The active arrow keys are stored and passed to Player.sense() in the
        game loop.

        :param key: id of the key that is pressed arcade.key.STATIC
        :param modifiers: not used
        :return: nothing
        """
        if key in self.keys.keys():
            self.keys[key] = True

    def on_key_release(self, key, modifiers):
        """
        Called by arcade when a key is released. The active arrow keys are stored and passed to Player.sense() in the
        game loop.

        :param key: id of the key that is pressed arcade.key.STATIC
        :param modifiers: not used
        :return: nothing
        """
        if key in self.keys.keys():
            self.keys[key] = False

    def _draw_train(self, player):
        """
        Draw the train for a given player. Scales the position to game window pixel coordinates.

        :param player: child class of Player
        :return: nothing
        """
        scaled_x, scaled_y = player.get_position(scale=self.scale)

        arcade.draw_circle_outline(
            scaled_x,
            scaled_y,
            2,
            arcade.color.WHITE,
            2
        )

        sprite = arcade.Sprite("car.png", center_x=scaled_x, center_y=scaled_y, scale=0.1)
        sprite.angle = -player.rotation + 90
        sprite.draw()

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
            color = arcade.color.GREEN
        else:
            distance = sensor.percept
            color = arcade.color.WHITE

        # Set target
        target = self.track.translate(
            player.position,
            distance,
            sensor.get_absolute_angle()
        )

        # Scale and draw
        scaled_x_1, scaled_y_1 = player.get_position(scale=self.scale)
        scaled_x_2, scaled_y_2 = [p * self.scale for p in target]
        arcade.draw_line(
            scaled_x_1,
            scaled_y_1,
            scaled_x_2,
            scaled_y_2,
            color,
            1
        )

    def _draw_debug(self):
        """
        Draw debug information on the screen.
        :return: nothing
        """
        #TODO: show more information
        text_format = "fps: {fps:.0f}"

        text = text_format.format(
            fps=self.fps
        )
        arcade.draw_text(text, 0, 0, arcade.color.WHITE, 12)


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
        flipped_data = np.flip(transposed_data, 1)

        # red channel is boundary (walls)
        red_channel = flipped_data[:, :, 0]
        boundaries = red_channel >= 128

        # blue channel is finish
        blue_channel = flipped_data[:, :, 2]
        finish = np.transpose(np.nonzero(blue_channel))

        # green channel is starting point
        green_channel = flipped_data[:, :, 1]
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
        rotation_rad = math.radians(-rotation + 90)
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
