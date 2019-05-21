Adding AI
=========

Subclassing Player
------------------
Creating a new type of player is as simple as subclassing the Player object and implementing the `sense` and `plan`
methods. An example is shown below.

.. code-block:: python

    class HumanPlayer(Player):
        def __init__(self):
            super().__init__()

        def sense(self, track, keys):
            # do something with pressed keys and the track
            return percepts

        def plan(self, percepts):
            # use the percepts as gotten by `sense()` and return an acceleration_command and rotation_command in range
            # [-1, 1]
            return acceleration_command, rotation_command

Example AI
----------

An example AI can be found in :doc:`player`. Look for the NaiveAi() class. It uses linear distance sensors, which can be
found in the same module.

Controlling AI
--------------

Below concept demonstrates how to control the flow of AI players during the game.

.. code-block:: python

    from src.game import Engine, Environment
    from src.player import Ai
    import pygame


    def main():
        track = Environment('assen')
        game_engine = Engine(track, [Ai()])
        game_engine.bind_action(pygame.K_9, lambda: game_engine.add_player(Ai()))
        game_engine.bind_action(pygame.K_0, lambda: new_player(game_engine))
        game_engine.bind_action(pygame.K_q, lambda: game_engine.remove_all_players(keep=[game_engine.get_best_player()]))
        game_engine.play(False)


    def new_player(game_engine):
        best_player = game_engine.get_best_player()
        baby = best_player.give_birth()
        game_engine.add_player(baby)


    if __name__ == "__main__":
        main()