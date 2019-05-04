from game import Engine, Environment
from player import HumanPlayer, Ai


def main():
    track = Environment('track.png')
    players = [HumanPlayer, HumanPlayer, HumanPlayer]
    game_engine = Engine(track, players)
    game_engine.bind_action_to_0(game_engine.add_player, (Ai, ))
    game_engine.play()


if __name__ == "__main__":
    main()
