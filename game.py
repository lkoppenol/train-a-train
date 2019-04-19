import arcade
from game_engine import GameEngine, Track
from player import HumanPlayer, Player




def main():
    track = Track('track.png')

    game_engine = GameEngine(track, 10, [HumanPlayer()])
    arcade.run()
    print(game_engine.score)




if __name__ == "__main__":
    main()
