Running
=========================================
Run the following code and a game window should appear.

.. code-block:: bash

   python main.py

Playing the game
----------------
The train can be controlled much like an actual train, using the arrow keys. Game rules:

- Pressing left or right will cause the train to rotate respectively counter-clockwise or clockwise. The turning speed
  for a human player is fixed. For an AI slower turning is possible.
- Pressing up or down will increase or decrease the speed. The minimum speed is 0. Again, acceleration is fixed for
  human players. There is no maximum speed.
- Crashing into a wall will cause a player to die
- Finishing causes a player to die
- By default, if all players are dead, the game shuts down. To prevent this call game_engine.play(stop_on_death=False)
- Score is shown on a panel on the left. Please bring reading glasses. Score is calculated as distance to the finish,
  meaning a lower score is better!
- The game can be run in headless mode to finish really fast. Makes it very hard for human players. Use the `headless`
  kwargs in the Engine init for this.

main.py explained
-----------------
A track is loaded by calling its name. The name corresponds to a subfolder in the tracks folder, which contains the data
and graphics for the track. When this function is called the walls, starting location, finish and scoring map are
prepared.

.. code-block:: python

    track = Environment('assen')

Secondly, the game engine is initialized. The game engine is responsible for the game logic per turn, listening game
events (key inputs) and drawing the game. The engine can be instantiated in headless mode.

.. code-block:: python

    game_engine = Engine(track, [HumanPlayer()])

The game engine can be kicked off by calling engine.play(), which repeatedly calls game_engine._turn().

.. code-block:: python

    game_engine.play()