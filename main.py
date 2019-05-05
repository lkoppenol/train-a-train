from game import Engine, Environment
from player import HumanPlayer, Ai
import pygame


def main():
    track = Environment('track.png')
    players = [HumanPlayer, HumanPlayer, HumanPlayer]
    game_engine = Engine(track, players)
    game_engine.bind_action(pygame.K_0, lambda _: game_engine.add_player(Ai))
    game_engine.play()


if __name__ == "__main__":
    main()
