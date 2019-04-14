import arcade
import math
from PIL import Image
import numpy as np


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
            
    def draw(self):
        self._draw_car()
            
    def _draw_car(self):
        arcade.draw_circle_outline(
            self.x,
            self.y,
            2,
            arcade.color.WHITE,
            2
        )
        
        line_target = self._step(5)
        arcade.draw_line(
            self.x,
            self.y,
            self.x + line_target[0],
            self.y + line_target[1],
            arcade.color.WHITE,
            3
        )

    def move(self, delta_time):
        self.speed += self.acceleration_command * self.acceleration * delta_time
        self.rotation += self.rotation_command * self.rotation_speed * delta_time
        # forces rotation to be in range [0, 360]
        self.rotation = (self.rotation + 360) % 360
        
        movement = self._step(self.speed)
        self.x += movement[0]
        self.y += movement[1]
        
    def _step(self, distance):
        rotation_rad = math.radians(-self.rotation + 90)
        x = math.cos(rotation_rad) * distance
        y = math.sin(rotation_rad) * distance
        return x, y
        

class RacerGame(arcade.Window):
    def __init__(self, track):
        super().__init__(track.width, track.height)
        
        arcade.set_background_color(arcade.color.WHITE)
        self.fps = 0
        self.background = None
        self.boundaries = track.boundaries
        self.collision = 0

    def setup(self):
        self.player_0 = Car(125, 125)
        self.background = arcade.load_texture('track.png')
        
    def on_draw(self):
        arcade.start_render()
        arcade.draw_texture_rectangle(
            self.width // 2,
            self.height // 2,
            self.width,
            self.height,
            self.background
        )
        
        self.player_0.draw()      
        self._draw_debug()
        
    def update(self, delta_time):
        self.player_0.move(delta_time)
        self.fps = 1 / delta_time
        self.check_collision()

    def check_collision(self):
        self.collision = self.boundaries[int(self.player_0.x), int(self.player_0.y)]

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
            "fps: {fps}"

        text = text_format.format(
            speed=self.player_0.speed,
            movement=self.player_0.acceleration_command,
            fps=self.fps,
            rotation=self.player_0.rotation,
            collision=self.collision,
            x=self.player_0.x,
            y=self.player_0.y
        )
        arcade.draw_text(text, 0, 0, arcade.color.WHITE, 12)


class Track(object):
    def __init__(self, path):
        track_img = Image.open(path)
        self.width = track_img.width
        self.height = track_img.height
        self.boundaries = self.parse_track(track_img)

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

        # boolean borders
        boundaries = red_channel >= 128
        return boundaries


def main():
    track = Track('track.png')
    racer_game = RacerGame(track)
    racer_game.setup()
    arcade.run()


if __name__ == "__main__":
    main()