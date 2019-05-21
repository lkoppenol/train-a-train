Advanced options
=========================================

Tricks for pro's
----------------

- Press "1" to cycle between "fancy train", "minimal line" and "invisible"
- Press "2" to cycle between "not showing sensors", "showing sensors". This requires the player to have drawable
  sensors. See :doc:`ai-players` for more information about sensors
- Press "3" to cycle between "fancy map", "raw map", "score map" and "no map"
- Press "4" to toggle the frame rate limiter

Custom key bindings
-------------------
Custom actions can be bound to custom keys to control the game play during the game. Keys can be found on in the
`pygame docs <https://www.pygame.org/docs/ref/key.html>`_. More documentation on this and other functions can be found
in the :doc:`api-reference`, specifically :doc:`game`

.. code-block:: python

   game_engine.bind_action(pygame.K_q, lambda: print(123))

The following will not work because it will print instantly and give None as function to bind_action.

.. code-block:: python

   game_engine.bind_action(pygame.K_q, print(123))  # BAD EXAMPLE

The following example destroys all players except the best one when Q is pressed.

.. code-block:: python

    def custom_action():
     game_engine.remove_all_players(keep=[game_engine.get_best_player()])

    game_engine.bind_action(pygame.K_q, custom_action)


Custom tracks
-------------
Of course you want to create your own maps! All you have to do is the following:

- Create a new folder in ./tracks/
- Start your favorite image editor, for example `paint.net <https://www.getpaint.net/>`_.
- Draw your favorite track, using the following colors
   - Use #000000 for the track
   - Use #FF0000 for the walls
   - Use #00FF00 for the starting location (the first pixel found with over 50% green is picked as starting point)
   - use #0000FF for finish. This can be a line
- Store as `track.png` AND as `track_bg.png`
- OPTIONALLY use a different graphic for `track_bg.png`. Make sure it has the same pixel ratio as `track.png`
