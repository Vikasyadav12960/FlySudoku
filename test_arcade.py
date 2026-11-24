import random
import tkinter as tk
import unittest
from unittest.mock import patch

from arcade import build
from arcade_rules import CELLS, PEERS, attach, center, count_solutions, neighbors, puzzle, race_move


class ArcadeTests(unittest.TestCase):
    def test_unique_boards(self):
        for blanks in (14, 20, 24):
            for seed in range(12):
                board, solution = puzzle(blanks, random.Random(seed))
                self.assertEqual(count_solutions(board), 1)
                self.assertTrue(all(solution[i] not in {solution[j] for j in PEERS[i]} for i in CELLS))
                self.assertTrue(all(not n or solution[i] == n for i,n in enumerate(board)))

    def test_race_rules(self):
        self.assertEqual(race_move(0,4),(4,22))
        self.assertEqual(race_move(25,3),(28,8))
        self.assertEqual(race_move(99,3),(99,99))
        self.assertEqual(race_move(99,1),(100,100))

    def test_pop_and_drop(self):
        field = {(0,0):1,(1,0):1,(2,0):2,(0,8):3}
        self.assertEqual(attach(field,(0,1),1),4)
        self.assertEqual(field,{(0,8):3})
        self.assertTrue(all((1,3) in neighbors(n) for n in neighbors((1,3))))

    def test_desktop_games(self):
        root = tk.Tk()
        self.addCleanup(root.destroy)
        root.withdraw()
        sudoku, race, bubbles, memory = build(root)
        root.update_idletasks()
        original = sudoku.fixed.copy()
        sudoku.hint()
        sudoku.undo()
        self.assertEqual(sudoku.values, original)
        for i in CELLS:
            if not original[i]:
                sudoku.select(i)
                sudoku.put(sudoku.solution[i])
        self.assertIn("Solved!", sudoku.status["text"])
        race.pos[0] = 99
        with patch("arcade.random.randint", return_value=1):
            race.roll_button.invoke()
        self.assertIn("wins", race.status["text"])
        race.reset()
        self.assertEqual(race.pos, [0,0])

        # Advance the same animation callback Tk schedules, without real-time waits.
        bubbles.field = {(0,4):0,(0,5):0}
        bubbles.color = 0
        bubbles.fire()
        for _ in range(160):
            if bubbles.timer is None:
                break
            bubbles.after_cancel(bubbles.timer)
            bubbles.tick()
        self.assertTrue(bubbles.over)
        self.assertFalse(bubbles.field)
        bubbles.reset()
        bubbles.rotate(1.24)
        bubbles.fire()
        for _ in range(300):
            if bubbles.timer is None:
                break
            bubbles.after_cancel(bubbles.timer)
            bubbles.tick()
        self.assertIsNone(bubbles.shot)

        mismatch = next(i for i in range(1,16) if memory.deck[i] != memory.deck[0])
        memory.flip(0)
        memory.flip(mismatch)
        memory.reset()
        self.assertIsNone(memory.timer)
        for word in set(memory.deck):
            for i,card in enumerate(memory.deck):
                if card == word:
                    memory.flip(i)
        self.assertIn("All pairs found in 8 turns", memory.status["text"])


if __name__ == "__main__":
    unittest.main()
