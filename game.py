import arcade
import math
from PIL import Image
import numpy as np
import bresenham


class Player(object):
    def __init__(self):
        self.speed = 0
        self.rotation = 0
        
        self.acceleration = 5
        self.rotation_speed = 180
        
        self.acceleration_command = 0
        self.rotation_command = 0

        self.sensors = [-30, 0, 30]
        self.sensory_input = [-1 for _ in self.sensors]

        self.score = 0
        self.collision = False

    def act(self, delta_time):
        self.speed += self.acceleration_command * self.acceleration * delta_time
        self.speed = max(self.speed, 0)

        # forces rotation to be in range [0, 360]
        self.rotation += self.rotation_command * self.rotation_speed * delta_time
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

    def sense(self, track, distance):
        sensory_input = []
        for s in self.sensors:
            x2, y2 = self.step(distance, rotation_offset=s)
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
        

class GameEngine(arcade.Window):
    def __init__(self, track, scale, players):
        super().__init__(track.width * scale, track.height * scale)

        self.track = track

        for player in players:
            player.set_position(track.start)
        self.players = players

        self.background = arcade.load_texture(track.path)
        self.fps = 0
        self.scale = scale

    def on_draw(self):
        arcade.start_render()
        arcade.draw_texture_rectangle(
            self.width // 2,
            self.height // 2,
            self.width,
            self.height,
            self.background
        )

        for player in self.players:
            self._draw_car(player)
            self._draw_sensors(player)

        self._draw_debug()

    def update(self, delta_time):
        for player in self.players:
            # Sense
            player.sense(self.track, 3)

            # Plan
            player.plan()

            # Act
            player.act(delta_time)

            # Resolve
            player.collision = self.track.check_collision(player)

            score = self.track.get_distance(player)

            if score > 0:
                player.score = score

            if player.collision or player.score == 1:
                self.score = score
                arcade.close_window()

        self.fps = 1 / delta_time

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.players[0].acceleration_command = 1
        elif key == arcade.key.DOWN:
            self.players[0].acceleration_command = -1
        elif key == arcade.key.LEFT:
            self.players[0].rotation_command = -1
        elif key == arcade.key.RIGHT:
            self.players[0].rotation_command = 1

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.players[0].acceleration_command = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.players[0].rotation_command = 0

    def _draw_car(self, player):
        scaled_x = player.x * self.scale
        scaled_y = player.y * self.scale

        arcade.draw_circle_outline(
            scaled_x,
            scaled_y,
            2,
            arcade.color.WHITE,
            2
        )

    def _draw_sensors(self, player):
        scaled_x = player.x * self.scale
        scaled_y = player.y * self.scale

        for s in player.sensors:
            line_target = player.step(3 * self.scale, rotation_offset=s)
            arcade.draw_line(
                scaled_x,
                scaled_y,
                scaled_x + line_target[0],
                scaled_y + line_target[1],
                arcade.color.WHITE,
                3
            )
 
    def _draw_debug(self):
        text_format = "fps: {fps:.0f}"

        text = text_format.format(
            fps=self.fps
        )
        arcade.draw_text(text, 0, 0, arcade.color.WHITE, 12)


class Track(object):
    def __init__(self, path):
        track_img = Image.open(path)
        self.path = path
        self.width = track_img.width
        self.height = track_img.height
        self.boundaries, self.finish, self.start = self.parse_track(track_img)
        self.distance_matrix = self.get_distance_matrix()

    @staticmethod
    def parse_track(track_img):
        rgb_img = track_img.convert('RGB')
        raw_data = np.asarray(rgb_img)

        # flip x and y dimensions
        transposed_data = np.transpose(raw_data, (1, 0, 2))

        # flip Y axis
        flipped_data = np.flip(transposed_data, 1)

        # red channel is boundry
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
        pixel_x = int(round(player.x))
        pixel_y = int(round(player.y))
        collision = self.boundaries[pixel_x, pixel_y]
        return collision

    def get_distance(self, player):
        pixel_x = int(round(player.x))
        pixel_y = int(round(player.y))
        distance = self.distance_matrix[pixel_x, pixel_y]
        return distance

    def get_distance_matrix(self):
        finish_points = [(i[0], i[1]) for i in self.finish]
        distance_matrix = self.recursive_distance(
            distance_matrix=np.zeros(self.boundaries.shape),
            points=finish_points,
            distance=1
        )
        return distance_matrix

    def recursive_distance(self, distance_matrix, points, distance):
        # Set distance values
        for point in points:
            distance_matrix[point] = distance

        # Determine neighbor points
        valid_next_points = set()
        for point in points:
            for dx in [-1, 1]:
                for dy in [-1, 1]:
                    next = (
                        point[0] + dx,
                        point[1] + dy
                    )
                    try:
                        if (not self.boundaries[next]) and distance_matrix[next] == 0:
                            valid_next_points.add(next)
                    except IndexError:
                        pass

        # Next iteration
        if len(valid_next_points) > 0:
            distance_matrix = self.recursive_distance(
                distance_matrix,
                valid_next_points,
                distance + 1
            )
        return distance_matrix


def main():
    gui = True

    track = Track('track.png')

    g = GameEngine(track, 10, [Player()])
    arcade.run()
    print(g.score)




if __name__ == "__main__":
    main()
