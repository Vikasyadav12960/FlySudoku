# FlySudoku · Flight Lab

From PowerShell in this folder, run:

```powershell
.\PLAY.cmd
```

Or double-click **PLAY.cmd**. Install Python 3.11+ with Tcl/Tk if needed. No packages, downloads or accounts are required to play offline.

**Watch the fly.** A new 6×6 Sudoku opens with a fly already choosing moves. Accepted digits appear in mint. The fly moves to each attempt, receives feedback, and starts a fresh board after the round. The side panel selects its environment.

| Environment | What the fly does |
|---|---|
| 6×6 Sudoku | Chooses a legal cell and digit using candidate counts. The environment checks against the unique solution, rewards correct attempts and rejects incorrect ones. |
| Memory pairs | Learns the value of exploring unseen cards and selecting known pairs using only previously revealed symbols. |
| Bubble launch | Traces possible shots, including wall bounces, and learns which neighboring-color patterns reward a shot. |
| Snakes & Ladders | Two flies roll and race automatically. This chance-only game records outcomes without fitting a policy. |

**Train and load.** Training starts automatically. Use **Fast** to run more trials or **Pause** to inspect the board. **Evaluate policy** starts a fresh round with exploration disabled and the learned values frozen. The panel shows actions, immediate reward, learned mean and completed rounds. Switching games or modes starts a fresh round and retains learned values.

**Save result…** writes a JSON file containing each game's action values and completed-round records. **Load result…** restores those results and starts an evaluation. Save before closing to keep training. Scores describe these simulations, not a benchmark against a human or another model.

The visual reference is [HEREISCB/flybrain](https://github.com/HEREISCB/flybrain): watch a fly act in an environment and inspect its behavior. Flight Lab uses an original Tkinter interface and a small contextual bandit with 12% training exploration. It does not implement FlyBrain's biological neural simulation.

Run the checks with `python -m unittest test_arcade -v`.
