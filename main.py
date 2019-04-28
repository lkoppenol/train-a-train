from game import Engine, Environment
from player import HumanPlayer, Ai
import time


def main():
    track = Environment('track.png')

    players = [HumanPlayer()]

    game_engine = Engine(track, 1 / 0.3, players)

    seconds_per_frame = 1/30

    while game_engine.is_running():
        planned_next_frame = int(time.time() / seconds_per_frame)

        game_engine.update(seconds_per_frame)
        game_engine.on_draw()
        actual_next_frame = int(time.time() / seconds_per_frame)
        if planned_next_frame != actual_next_frame:
            frames_skipped = actual_next_frame - planned_next_frame
            print(f"game thread skipped {frames_skipped} frame(s)")
        time_to_next_frame = seconds_per_frame - time.time() % seconds_per_frame
        time.sleep(time_to_next_frame)



if __name__ == "__main__":
    main()
