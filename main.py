from src.game import Engine, Environment
from src.player import HumanPlayer, NaiveAi


def main():
    track = Environment('assen')
    game_engine = Engine(track, [HumanPlayer(), NaiveAi()])
    game_engine.play()


if __name__ == "__main__":
    main()
