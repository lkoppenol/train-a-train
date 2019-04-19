import arcade
from game_engine import GameEngine, Track
from player import HumanPlayer, Player


from random import random


class Ai(Player):
    def __init__(self, rules, random_change=False):
        super().__init__()
        self.rules = rules
        if random_change:
            self._neighborhood_search()

    @classmethod
    def from_file(cls, path, random_change=False):
        with open(path, 'r') as rule_file:
            rules = [[float(r) for r in r_set.split(',')] for r_set in rule_file.readlines()]
        return cls(rules, random_change)

    @classmethod
    def random_initialization(cls):
        rules = [[random() - 0.5 for _ in range(4)] for __ in range(4)]
        return cls(rules, False)

    def plan(self):
        rule_totals = []
        for rule in self.rules:
            rule_total = rule[-1]
            for i, s in enumerate(self.sensory_input):
                rule_total += rule[i] * s
            rule_totals.append(rule_total)

        if rule_totals[0] > rule_totals[1]:
            self.rotation_command = 1
        else:
            self.rotation_command = -1

        if rule_totals[2] > rule_totals[3]:
            self.acceleration_command = 1
        else:
            self.acceleration_command= -1

    def _neighborhood_search(self, learning_rate=0.5):
        self.rules = [[r + learning_rate * (random() - 0.5) for r in r_set]for r_set in self.rules]

    def save(self, path):
        with open(path, 'w') as rule_file:
            file = "\n".join([",".join([str(r) for r in r_set]) for r_set in self.rules])
            rule_file.write(file)




def main():
    gui = True

    track = Track('track.png')

    players = []
    #players = [HumanPlayer()]
    players += [Ai.from_file('rules.csv', True) for _ in range(1)]
    #players += [Ai.random_initialization() for _ in range(5)]
    players += [Ai.from_file('rules.csv', False) for _ in range(1)]

    game_engine = GameEngine(track, 1/0.3, players)

    if gui:
        arcade.run()
    else:
        while game_engine.game_status == 0:
            game_engine.update(0.1)

    best = [None, None]
    for k, v in game_engine.score.items():
        s = v[0] * 10 + v[1]
        if best[1] is None or s < best[1]:
            best = [k, s]

    players[best[0]].save('rules.csv')
    print(best[1])







if __name__ == "__main__":
    main()
