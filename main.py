from game import Engine, Environment
from player import HumanPlayer


def main():
    track = Environment('track.png')
    players = [HumanPlayer, HumanPlayer, HumanPlayer]
    game_engine = Engine(track, players)
    game_engine.play()


if __name__ == "__main__":
    main()
