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
        self.rotation_speed = 50
        
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
        self.rotation = (self.rotation + 360) % 360 # forces rotation to be in range [0, 360]
        
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
        self.background = 0
        self.borders = track.boundries
        self.botsing = 0

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
        if self.borders[int(self.player_0.x), int(self.player_0.y)] > 125:
            self.botsing = self.borders[int(self.player_0.x), int(self.player_0.y)]
        else:
            self.botsing = 0
        
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
        "botsing: {botsing}\n" \
        "x: {x}\n" \
        "y: {y}\n" \
        "fps: {fps}" 
        
    
        text = text_format.format(
            speed=self.player_0.speed,
            movement=self.player_0.acceleration_command,
            fps=self.fps,
            rotation=self.player_0.rotation,
            botsing=self.botsing,
            x=self.player_0.x,
            y=self.player_0.y
        )
        arcade.draw_text(text, 0, 0, arcade.color.WHITE, 12)
    
class Track(object):
    def __init__(self):
        track_img = Image \
            .open('track.png') \
            .convert('RGB')
        self.width = track_img.width
        self.height = track_img.height
        
        raw_data = np.asarray(track_img)
        transposed_data = np.transpose(raw_data, (1, 0, 2))
        flipped_data = np.flip(transposed_data, 1) # flip Y axis
        self.boundries = flipped_data[:, :, 0] # red channel is boundry
        print(self.boundries.shape)
        

def main():
    track = Track()
    racer_game = RacerGame(track)
    racer_game.setup()
    arcade.run()
        
if __name__ == "__main__":
    main()