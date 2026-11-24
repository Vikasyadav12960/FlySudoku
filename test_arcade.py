import json
import random
import tempfile
import unittest
from pathlib import Path
import tkinter as tk

from arcade import Lab
from fly_policy import Brain, NAMES
from fly_worlds import WORLDS
from arcade_rules import puzzle, count_solutions


class FlightTests(unittest.TestCase):
    def test_unique(self):
        for seed in range(16):
            board,_ = puzzle(22,random.Random(seed))
            self.assertEqual(count_solutions(board),1)

    def test_autonomous_rounds(self):
        rng = random.Random(42)
        brain = Brain()
        for name in NAMES:
            world = WORLDS[name](rng)
            for _ in range(500):
                action,key = brain.choose(name,world.actions(),rng,True)
                reward,done,won,_ = world.move(action)
                if name != "Snakes & Ladders":
                    brain.learn(name,key,reward)
                if done:
                    break
            self.assertTrue(done,name)
            if name in ("Sudoku","Memory pairs"):
                self.assertTrue(won)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"result.json"
            brain.results["Sudoku"].append(dict(moves=33,won=True,training=True))
            brain.save(path)
            loaded = Brain.load(path)
            self.assertEqual(loaded.values,brain.values)
            self.assertEqual(loaded.results,brain.results)
            path.write_text('{"version":9}')
            with self.assertRaises(ValueError):
                Brain.load(path)

    def test_window(self):
        root = tk.Tk()
        root.withdraw()
        lab = Lab(root,random.Random(11))
        self.addCleanup(lab.close)
        for name in NAMES:
            lab.select(name)
            root.after_cancel(lab.tick_id)
            lab.step()
            self.assertEqual(lab.moves,1)
            self.assertTrue(lab.cv.find_withtag("fly"))
        lab.select("Sudoku")
        lab.switch_mode()
        before = json.dumps(lab.brain.values)
        for _ in range(80):
            root.after_cancel(lab.tick_id)
            lab.step()
        self.assertEqual(before,json.dumps(lab.brain.values))
        self.assertTrue(lab.brain.results["Sudoku"])
        lab.toggle()
        self.assertIsNone(lab.tick_id)
