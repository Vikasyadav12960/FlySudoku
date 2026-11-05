from __future__ import annotations
import csv, random
from pathlib import Path
from .environment import SudokuEnv
from .agent import LinearAgent

EXPERIMENTS = Path("experiments")

def train(agent: LinearAgent, episodes: int, seed: int, progress=None):
    EXPERIMENTS.mkdir(exist_ok=True)
    path = EXPERIMENTS / "training_log.csv"
    write_header = not path.exists()
    rng = random.Random(seed)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["episode", "seed", "reward", "solved", "moves", "epsilon"])
        for ep in range(episodes):
            env = SudokuEnv(seed=rng.randrange(1_000_000_000))
            trajectory, total, moves = [], 0.0, 0
            while not env.done and moves < 20:
                actions = env.legal_actions()
                if not actions:
                    break
                action = agent.choose(env.observation(), actions)
                trajectory.append(agent.features(env.board, *action))
                _, reward, _, _ = env.step(action)
                total += reward
                moves += 1
            agent.update(trajectory, total)
            writer.writerow([agent.episodes, seed, round(total, 3), int(env.is_solved()), moves, agent.epsilon])
            if progress:
                progress(ep + 1, episodes, total, env.is_solved())
    agent.save(EXPERIMENTS / "agent_checkpoint.json")
    return path

def evaluate(agent: LinearAgent, episodes: int = 100, seed: int = 90210):
    rng = random.Random(seed)
    solved = 0
    rewards, moves_list = [], []
    for _ in range(episodes):
        env = SudokuEnv(seed=rng.randrange(1_000_000_000))
        total, moves = 0.0, 0
        # Greedy evaluation: no exploration, no learning updates.
        old_epsilon = agent.epsilon
        agent.epsilon = 0.0
        while not env.done and moves < 20:
            action = agent.choose(env.observation(), env.legal_actions())
            if action is None:
                break
            _, reward, _, _ = env.step(action)
            total += reward
            moves += 1
        agent.epsilon = old_epsilon
        solved += int(env.is_solved())
        rewards.append(total)
        moves_list.append(moves)
    EXPERIMENTS.mkdir(exist_ok=True)
    path = EXPERIMENTS / "evaluation_log.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["episode", "reward", "solved", "moves"])
        for i, (r, m) in enumerate(zip(rewards, moves_list), 1):
            w.writerow([i, round(r, 3), int(r > 0 and m <= 16), m])
    return {"episodes": episodes, "solved": solved, "solve_rate": solved / episodes,
            "mean_reward": sum(rewards) / episodes, "mean_moves": sum(moves_list) / episodes,
            "log": str(path)}
