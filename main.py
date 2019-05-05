from game import Engine, Environment
from player import HumanPlayer, Ai
import pygame


def main():
    track = Environment('track.png')
    game_engine = Engine(track, [])
    game_engine.bind_action(pygame.K_9, lambda: game_engine.add_player(Ai()))
    game_engine.bind_action(pygame.K_0, lambda: new_player(game_engine))
    game_engine.bind_action(pygame.K_q, lambda: game_engine.remove_all_players())
    game_engine.play(False)


def new_player(game_engine):
    best_player = game_engine.get_best_player()
    baby = best_player.give_birth()
    game_engine.add_player(baby)


if __name__ == "__main__":
    main()
