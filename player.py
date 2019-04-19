import math
import bresenham


class Player(object):
    def __init__(self):
        self.ACCELERATION= 5
        self.ROTATION_SPEED = 180

        self.x = 0
        self.y = 0
        self.speed = 0
        self.rotation = 0

        self.acceleration_command = 0
        self.rotation_command = 0

        self.sensors = [-30, 0, 30]
        self.sensory_input = [-1 for _ in self.sensors]
        self.sensor_depth = 50

        self.score = 0
        self.collision = False
        self.human_player = False
        self.alive = True

    def act(self, delta_time):
        self.speed += self.acceleration_command * self.ACCELERATION * delta_time
        self.speed = max(self.speed, 0)

        # forces rotation to be in range [0, 360]
        self.rotation += self.rotation_command * self.ROTATION_SPEED * delta_time
        self.rotation = (self.rotation + 360) % 360

        movement = self.step(self.speed)
        self.change_position(movement)

    def plan(self):
        pass

    def step(self, distance, rotation_offset=0):
        rotation_rad = math.radians(-(self.rotation + rotation_offset) + 90)
        x = math.cos(rotation_rad) * distance
        y = math.sin(rotation_rad) * distance
        return x, y

    def sense(self, track):
        sensory_input = []
        for s in self.sensors:
            x2, y2 = self.step(self.sensor_depth, rotation_offset=s)
            pixel_x1 = int(round(self.x))
            pixel_x2 = int(round(self.x + x2))
            pixel_y1 = int(round(self.y))
            pixel_y2 = int(round(self.y + y2))
            line_of_sight = bresenham.get_line(
                (pixel_x1, pixel_y1),
                (pixel_x2, pixel_y2)
            )
            for i, pixel in enumerate(line_of_sight):
                if track.boundaries[pixel]:
                    sensory_input.append(i)
                    break
            else:
                sensory_input.append(-1)
        self.sensory_input = sensory_input

    def set_position(self, coordinate):
        self.x = coordinate[0]
        self.y = coordinate[1]

    def change_position(self, delta_coordinate):
        self.x += delta_coordinate[0]
        self.y += delta_coordinate[1]


class HumanPlayer(Player):
    def __init__(self):
        super().__init__()
        self.human_player = True
