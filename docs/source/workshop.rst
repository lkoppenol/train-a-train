Workshop
=========================================


Exercises
---------

1. Run the game and finish
~~~~~~~~~~~~~~~~~~~~~~~~~~

1.1 Run the game without errors!

- Yeah you met the requirements!
- Doesn't work? Is your Python >= 3.7 and did you install the requirements?

1.2 Start racing!

- Can you finish without crashing?

1.3. Try a different track!

- Which tracks are available?
- Change the code to run a different track

1.4 Add a NaiveAi player. Can you beat him?

2. Advanced options
~~~~~~~~~~~~~~~~~~~

2.1 Add a key binding which creates a new HumanPlayer

2.2 Add a key binding to remove all players except the best player

2.3 Create your own track! Can you finish it?

3. Start subclassing!
~~~~~~~~~~~~~~~~~~~~~

3.1 Create a new HumanPlayer called HoomanPlayer which has left and right reversed

3.2 Add sensors to the human player and visualize them! Try to finish the race with a black background and sensors
visible!

3.3 Make your HoomanPlayer break as you are about to hit a wall. Play with different sensors depths!

3.4 Make your HoomanPlayer accelerate automatically

3.5 Give the steering controls to your HoomanPlayer as well!

**3.6 You are now more than ready to start on the challenge!**


Challenge
---------

**Who can make the best Ai?** The team that scores the lowest score wins. Made it to the finish? Fastest team wins!

- Finale will be played on an unknown track!!
- The game will be played on the big screen.
- All teams stop programming the same time
- Time is measured in number of turns
- Ties are broken based on time
- If no teams finishes there can still be a tie. But shame on you!


Write your **WinningAi** so that it can be used as follow and hand in all required files before the deadline.

.. code-block:: python

    from src.game import Engine, Environment
    from yourmodule import WinningAi


    def main():
        track = Environment('super_secret_final_map')

        game_engine = Engine(
            environment=track,
            players=[WinningAi()]
        )

        game_engine.play()


    if __name__ == "__main__":
        main()


