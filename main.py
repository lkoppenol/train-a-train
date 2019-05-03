from game import Engine, Environment
from player import HumanPlayer, Ai
import time


def main():
    track = Environment('track.png')

    players = [HumanPlayer()]

    game_engine = Engine(track, players)

    game_engine.play()




if __name__ == "__main__":
    main()
