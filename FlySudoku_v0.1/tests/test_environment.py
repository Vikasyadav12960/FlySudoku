import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flysudoku.environment import SudokuEnv, count_solutions, valid
from flysudoku.agent import LinearAgent

class EnvironmentTests(unittest.TestCase):
    def test_generated_puzzle_unique(self):
        for seed in range(20):
            env=SudokuEnv(seed=seed)
            self.assertEqual(count_solutions(env.board),1)
            self.assertEqual(count_solutions(env.solution),1)
    def test_solution_valid(self):
        env=SudokuEnv(seed=4)
        for r in range(4):
            self.assertEqual(set(env.solution[r]),{1,2,3,4})
        for c in range(4):
            self.assertEqual({env.solution[r][c] for r in range(4)},{1,2,3,4})
    def test_invalid_duplicate_rejected(self):
        env=SudokuEnv(seed=8)
        empties=[(r,c) for r in range(4) for c in range(4) if not env.board[r][c]]
        r,c=empties[0]
        existing=next((v for v in range(1,5) if v in env.board[r]),None)
        if existing is None:
            self.skipTest("No row clue in generated puzzle")
        _,reward,_,_=env.step((r,c,existing))
        self.assertEqual(reward,-1)
        self.assertEqual(env.board[r][c],0)
    def test_agent_checkpoint(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"agent.json"
            a=LinearAgent(); a.save(p)
            b=LinearAgent.load(p)
            self.assertEqual(a.weights,b.weights)

if __name__=="__main__": unittest.main()
