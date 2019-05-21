"""
:author: Laurens Koppenol

Module to handle players. See :doc:`ai-players` on how to create new players

"""
from abc import abstractmethod, ABC
import pygame


class Player(ABC):
    """
    Abstract class. Subclass this if you want to make a new player. See readthedocs for more info.
    """
    def __init__(self):
        """
        Set initial values for player
        """
        self.position = (0, 0)
        self.speed = 0
        self.rotation = 90

        self.score = 0
        self.alive = True

        self.sensors = []

    @abstractmethod
    def sense(self, track, keys):
        """
        Meant to get information about the environment from the track / key input

        :param track: Environment object
        :param keys: dictionary of keys
        :return: percepts
        """
        pass

    @abstractmethod
    def plan(self, percepts):
        """
        Use percepts to get an action

        :param percepts: output of sense() function
        :return: acceleration_command, rotation_command. both in range [-1, 1]
        """
        pass

    def set_position(self, coordinate):
        """
        Set new player position

        :param coordinate: new coordinate (x, y)
        :return: Nothing
        """
        self.position = coordinate

    def get_position(self, pixel=False, scale=1):
        """
        Get player position

        :param pixel: wether to round down to full pixels
        :param scale: whether to scale (for drawing purposes)
        :return: coordinates (x, y)
        """
        if pixel:
            position = [int(round(p)) * scale for p in self.position]
            return position
        else:
            position = [p * scale for p in self.position]
            return position

    def change_position(self, delta_coordinate):
        """
        Adjust player position

        :param delta_coordinate: incremental coordaintes (dx, dy)
        :return: Nothing
        """
        self.position = (
            self.position[0] + delta_coordinate[0],
            self.position[1] + delta_coordinate[1]
        )


class HumanPlayer(Player):
    """
    Human Player that does not have sensors but responds to key input
    """
    def __init__(self):
        super().__init__()

    def sense(self, track, keys):
        """
        Nothing is sensed, keys are passed on to plan() function.

        :param track: Environment object
        :param keys: dictionary of keys
        :return: keys dictionary
        """
        return keys
        
    def plan(self, percepts):
        """
        Listen to key input.

        :param percepts: dict of keys that are pressed
        :return: acceleration_command, rotation_command
        """
        # use boolean as int trick to get -1, 0 or 1 from keys (both keys => 0)
        acceleration_command = percepts[pygame.K_UP] - percepts[pygame.K_DOWN]
        rotation_command = percepts[pygame.K_RIGHT] - percepts[pygame.K_LEFT]
        return acceleration_command, rotation_command


class NaiveAi(Player):
    """
    Super simple Naive AI that will try to stay away from the walls. User ray-tracing sensors (DistanceSensor).
    """
    SENSOR_DISTANCE = 60

    def __init__(self):
        """
        Initialize and add 2 ray-tracing sensors.
        """
        super().__init__()
        self.sensors += [DistanceSensor(self, a, NaiveAi.SENSOR_DISTANCE) for a in [-30, 30]]

    def sense(self, track, keys):
        """
        Calls its sensors using the track information to find distance to the walls.

        :param track: Environment object
        :param keys: Not used
        :return: a list with distances per sensor
        """
        percepts = [s.perceive(track) for s in self.sensors]
        return percepts

    def plan(self, percepts):
        """
        Use the percepts to choose actions. This naive AI will match a certain speed and rotate away from the nearest
        visible wall.

        :param percepts:
        :return: acceleration_command, rotation_command
        """
        if percepts[0] > percepts[1]:
            rotation_command = -1
        else:
            rotation_command = 1

        acceleration_command = self.speed < 1  # accelerate if going slow

        return acceleration_command, rotation_command


class DistanceSensor(object):
    """
    Linear distance sensor using a simple raytracing algorithm. This sensor is drawable because it has percept, depth
    and a get_absolute_angle function. At the moment this is required to be drawn.
    """
    def __init__(self, player, angle, depth):
        """
        :param player: The player the sensor belongs to
        :param angle: angle offset in degrees
        :param depth: depth of vision
        """
        self.player = player
        self.angle = angle
        self.depth = depth
        self.percept = None
        self.is_drawable = True  # Sensor must have percept, depth and get_absolute_angle() to be drawable

    def perceive(self, track):
        """
        Update the sensor values. Returns them and sets them as internal value. Returns max depth if nothing is
        perceived

        :param track: Environment object
        :return: distance value
        """
        percept = track.ray_trace_to_wall(
            self.player.position,
            self.player.rotation + self.angle,
            self.depth
        )
        if percept is None:
            percept = self.depth
        self.percept = percept
        return percept

    def get_absolute_angle(self):
        """
        Use the player's angle and the sensor's offset to return the absolute angle of the sensor.

        :return: angle in degrees
        """
        absolute_angle = self.player.rotation + self.angle
        return absolute_angle
