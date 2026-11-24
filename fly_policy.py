"""Small contextual bandit and inspectable, versioned training results."""
import json
import math
import os
from pathlib import Path
import random
import tempfile

NAMES = ("Sudoku", "Snakes & Ladders", "Bubble launch", "Memory pairs")


class Brain:
    def __init__(self):
        self.values = {name: {} for name in NAMES}
        self.results = {name: [] for name in NAMES}

    def choose(self, game, actions, rng, training):
        # Each action carries a feature key obtained only from observable state.
        if training and rng.random() < 0.12:
            return rng.choice(actions)
        table = self.values[game]
        score = max(table.get(key, [0, 0])[1] for _, key in actions)
        return rng.choice([pair for pair in actions if table.get(pair[1], [0, 0])[1] == score])

    def learn(self, game, key, reward):
        count, mean = self.values[game].get(key, [0, 0.0])
        self.values[game][key] = [count + 1, mean + (reward - mean) / (count + 1)]

    def save(self, path):
        path = Path(path)
        data = {"version": 1, "values": self.values, "results": self.results}
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf8") as tmp:
            filename = tmp.name
        try:
            Path(filename).write_text(json.dumps(data), encoding="utf8")
            os.replace(filename, path)
        finally:
            Path(filename).unlink(missing_ok=True)

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf8"))
        def check(valid):
            if not valid:
                raise ValueError("Choose a FlySudoku lab result saved by this version.")
        check(isinstance(data, dict) and data.get("version") == 1)
        brain = cls()
        for field in ("values", "results"):
            check(isinstance(data.get(field), dict) and set(data[field]) == set(NAMES))
        for name in NAMES:
            table = data["values"][name]
            check(isinstance(table, dict))
            for key, row in table.items():
                check(isinstance(key, str) and isinstance(row, list) and len(row) == 2)
                check(type(row[0]) is int and row[0] > 0 and type(row[1]) in (int,float) and math.isfinite(row[1]) and abs(row[1]) <= 10)
            records = data["results"][name]
            check(isinstance(records,list))
            for record in records:
                check(isinstance(record,dict) and type(record.get("moves")) is int and record["moves"] > 0
                      and type(record.get("won")) is bool and type(record.get("training")) is bool)
        brain.values = data["values"]
        brain.results = data["results"]
        return brain
