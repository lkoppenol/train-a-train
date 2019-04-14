import arcade
import math
from PIL import Image
import numpy as np
import bresenham


class Car(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
        self.speed = 0
        self.rotation = 0
        
        self.acceleration = 5
        self.rotation_speed = 180
        
        self.acceleration_command = 0
        self.rotation_command = 0

        self.sensors = [-30, 0, 30]
        self.sensory_input = [-1 for _ in self.sensors]
            
    def draw(self, scale):
        self._draw_car(scale)
        self._draw_sensors(scale)
            
    def _draw_car(self, scale):
        scaled_x = self.x * scale
        scaled_y = self.y * scale

        arcade.draw_circle_outline(
            scaled_x,
            scaled_y,
            2,
            arcade.color.WHITE,
            2
        )

    def _draw_sensors(self, scale):
        scaled_x = self.x * scale
        scaled_y = self.y * scale

        for s in self.sensors:
            line_target = self._step(3 * scale, rotation_offset=s)
            arcade.draw_line(
                scaled_x,
                scaled_y,
                scaled_x + line_target[0],
                scaled_y + line_target[1],
                arcade.color.WHITE,
                3
            )

    def move(self, delta_time):
        self.speed += self.acceleration_command * self.acceleration * delta_time
        self.speed = max(self.speed, 0)

        # forces rotation to be in range [0, 360]
        self.rotation += self.rotation_command * self.rotation_speed * delta_time
        self.rotation = (self.rotation + 360) % 360
        
        movement = self._step(self.speed)
        self.x += movement[0]
        self.y += movement[1]

    def _step(self, distance, rotation_offset=0):
        rotation_rad = math.radians(-(self.rotation + rotation_offset) + 90)
        x = math.cos(rotation_rad) * distance
        y = math.sin(rotation_rad) * distance
        return x, y

    def sense(self, track, distance):
        sensory_input = []
        for s in self.sensors:
            x2, y2 = self._step(distance, rotation_offset=s)
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
        

class RacerGame(arcade.Window):
    def __init__(self, track, scale):
        super().__init__(track.width * scale, track.height * scale)
        
        self.background = arcade.load_texture('track.png')
        self.fps = 0
        self.track = track
        self.collision = False
        self.player_0 = Car(track.start[0], track.start[1])
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

        self.player_0.draw(self.scale)
        self._draw_debug()
        
    def update(self, delta_time):
        self.player_0.move(delta_time)
        self.fps = 1 / delta_time
        self.collision = self.track.check_collision(
            self.player_0.x,
            self.player_0.y
        )

        self.score = self.track.get_distance(
            self.player_0.x,
            self.player_0.y
        )

        self.player_0.sense(self.track, 3)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.player_0.acceleration_command = 1
        elif key == arcade.key.DOWN:
            self.player_0.acceleration_command = -1
        elif key == arcade.key.LEFT:
            self.player_0.rotation_command = -1
        elif key == arcade.key.RIGHT:
            self.player_0.rotation_command = 1

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.player_0.acceleration_command = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_0.rotation_command = 0
 
    def _draw_debug(self):
        text_format = "speed: {speed}\n" \
            "movement: {movement}\n" \
            "rotation: {rotation}\n" \
            "collision: {collision}\n" \
            "x: {x}\n" \
            "y: {y}\n" \
            "score: {score}\n" \
            "sense: {sense}\n" \
            "fps: {fps}"

        text = text_format.format(
            speed=self.player_0.speed,
            movement=self.player_0.acceleration_command,
            fps=self.fps,
            rotation=self.player_0.rotation,
            collision=self.collision,
            x=self.player_0.x,
            y=self.player_0.y,
            score=self.track.get_distance(self.player_0.x, self.player_0.y),
            sense=self.player_0.sensory_input
        )
        arcade.draw_text(text, 0, 0, arcade.color.WHITE, 12)


class Track(object):
    def __init__(self, path):
        track_img = Image.open(path)
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

    def check_collision(self, x, y):
        pixel_x = int(round(x))
        pixel_y = int(round(y))
        collision = self.boundaries[pixel_x, pixel_y]
        return collision

    def get_distance(self, x, y):
        pixel_x = int(round(x))
        pixel_y = int(round(y))
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
    track = Track('track.png')
    RacerGame(track, 10)
    arcade.run()


if __name__ == "__main__":
    main()
