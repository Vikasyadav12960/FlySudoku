# FlySudoku · Flight Lab

An autonomous game arcade for the browser and desktop. Watch the fly try a move, inspect the reward, then run the same game with the learned policy frozen.

## Play in your browser

Open `web/index.html` on your computer, or visit your deployed Netlify site on a phone or laptop. The fly starts playing 6×6 Sudoku immediately. Select another game to switch environments. **Pause** holds the board, **Step** takes one action, and **Speed** changes the time between actions.

**Train policy** updates action values as the fly plays. **Evaluate policy** freezes those values and disables random exploration. Tied actions are still chosen at random. The Sudoku agent sees legal candidates and previously rejected attempts. The environment checks its choice against the puzzle’s unique solution. The two-fly race uses dice and records finishes.

Use **Save JSON** before leaving or reloading the page. **Load JSON** restores action values and round history from either edition and starts a fresh evaluation round. The board in progress is session-only. All game code runs locally in the browser.

## Deploy this branch to Netlify

1. In Netlify, import [Vikasyadav12960/FlySudoku](https://github.com/Vikasyadav12960/FlySudoku) from GitHub.
2. Select the branch containing those files. Leave **Base directory** and **Build command** empty. The included `netlify.toml` sets **Publish directory** to `web`. No environment variables or functions are needed.
3. Deploy and open the assigned site URL. The first board should advance on its own. Choose **Pause** and **Step** to inspect an individual move.

For a manual deploy, download this branch as a ZIP, extract it and drag the **web** folder into [Netlify Drop](https://app.netlify.com/drop).

## Desktop edition

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
