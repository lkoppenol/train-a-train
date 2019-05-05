from random import random
from abc import abstractmethod, ABC
import pygame


class Player(ABC):
    def __init__(self):
        self.position = (0, 0)
        self.speed = 0
        self.rotation = 0

        self.score = 0
        self.human_player = False
        self.alive = True

        self.sensors = []

    @abstractmethod
    def plan(self, percepts):
        pass

    @abstractmethod
    def sense(self, track, keys):
        pass

    def set_position(self, coordinate):
        self.position = coordinate

    def get_position(self, pixel=False, scale=1):
        if pixel:
            position = [int(round(p)) * scale for p in self.position]
            return position
        else:
            position = [p * scale for p in self.position]
            return position

    def change_position(self, delta_coordinate):
        self.position = (
            self.position[0] + delta_coordinate[0],
            self.position[1] + delta_coordinate[1]
        )


class HumanPlayer(Player):
    def __init__(self):
        super().__init__()
        self.human_player = True

    def sense(self, track, keys):
        return keys
        
    def plan(self, percepts):
        # use boolean as int trick to get -1, 0 or 1 from keys (both keys => 0)
        acceleration_command = percepts[pygame.K_UP] - percepts[pygame.K_DOWN]
        rotation_command = percepts[pygame.K_RIGHT] - percepts[pygame.K_LEFT]
        return acceleration_command, rotation_command


class Ai(Player):
    SENSOR_DISTANCE = 50

    def __init__(self, random_change=False):
        super().__init__()
        self.rules = [[random() - 0.5 for _ in range(4)] for __ in range(2)]
        if random_change:
            if type(random_change) is float:
                self._neighborhood_search(random_change)
            else:
                self._neighborhood_search()

        self.sensors += [DistanceSensor(self, a, Ai.SENSOR_DISTANCE) for a in [-30, 0, 30]]

    def give_birth(self):
        baby = Ai()
        baby.rules = self.rules
        baby._neighborhood_search(0.5)
        return baby

    def sense(self, track, keys):
        percepts = [s.perceive(track) for s in self.sensors]
        return percepts

    def plan(self, percepts):
        rule_totals = []
        for rule in self.rules:
            rule_total = rule[-1]
            for i, s in enumerate(percepts):
                if s is None:
                    s = Ai.SENSOR_DISTANCE
                rule_total += rule[i] * s
            rule_totals.append(rule_total)

        if rule_totals[0] > rule_totals[1]:
            rotation_command = 1
        else:
            rotation_command = -1

        acceleration_command = self.speed < 3

        return acceleration_command, rotation_command

    def _neighborhood_search(self, learning_rate=0.5):
        self.rules = [[r + learning_rate * (random() - 0.5) for r in r_set]for r_set in self.rules]


class DistanceSensor(object):
    def __init__(self, player, angle, depth):
        self.player = player
        self.angle = angle
        self.depth = depth
        self.percept = None
        self.is_drawable = True  # Sensor must have percept, depth and get_absolute_angle() to be drawable

    def perceive(self, track):
        percept = track.ray_trace_to_wall(
            self.player.position,
            self.player.rotation + self.angle,
            self.depth
        )
        self.percept = percept
        return percept

    def get_absolute_angle(self):
        absolute_angle = self.player.rotation + self.angle
        return absolute_angle
