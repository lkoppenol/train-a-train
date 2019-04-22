import arcade
from game import Engine, Environment
from player import HumanPlayer, Ai


def main():
    gui = True

    track = Environment('track.png')

    players = [HumanPlayer(), Ai()]

    game_engine = Engine(track, 1 / 0.3, players)

    if gui:
        arcade.run()
    else:
        while game_engine.game_status == 0:
            game_engine.update(0.1)


if __name__ == "__main__":
    main()
