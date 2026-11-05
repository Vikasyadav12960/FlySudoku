"""Small trainable contextual policy; deliberately not a Sudoku solver."""
from __future__ import annotations
import json, math, random
from pathlib import Path

class LinearAgent:
    """Scores each (cell,digit) action from observable board features.

    Learning is a simple reward-weighted preference update. It is a baseline for
    experimentation, not a biologically faithful model of synaptic plasticity.
    """
    def __init__(self, seed: int = 17, learning_rate: float = 0.015, epsilon: float = 0.25):
        self.rng = random.Random(seed)
        self.learning_rate = learning_rate
        self.epsilon = epsilon
        self.weights = [0.0] * 8
        self.episodes = 0
        self.recent_rewards: list[float] = []

    @staticmethod
    def features(board, r, c, v):
        row_used = sum(1 for x in board[r] if x)
        col_used = sum(1 for i in range(4) if board[i][c])
        br, bc = (r // 2) * 2, (c // 2) * 2
        box_used = sum(1 for i in range(br, br+2) for j in range(bc, bc+2) if board[i][j])
        row_conflicts = sum(board[r][j] == v for j in range(4))
        col_conflicts = sum(board[i][c] == v for i in range(4))
        box_conflicts = sum(board[i][j] == v for i in range(br,br+2) for j in range(bc,bc+2))
        return [1.0, r/3, c/3, v/4, row_used/4, col_used/4, box_used/4,
                float(row_conflicts + col_conflicts + box_conflicts > 0)]

    def choose(self, board, actions):
        if not actions:
            return None
        if self.rng.random() < self.epsilon:
            return self.rng.choice(actions)
        scored = []
        for a in actions:
            x = self.features(board, *a)
            scored.append((sum(w*f for w, f in zip(self.weights, x)), a))
        best = max(s for s, _ in scored)
        ties = [a for s, a in scored if abs(s-best) < 1e-9]
        return self.rng.choice(ties)

    def update(self, trajectory, total_reward):
        # Reward-weighted preference update over visited state-action features.
        scale = max(-1.0, min(1.0, total_reward / 20.0))
        for x in trajectory:
            for i, f in enumerate(x):
                self.weights[i] += self.learning_rate * scale * f
        self.episodes += 1
        self.recent_rewards.append(float(total_reward))
        self.recent_rewards = self.recent_rewards[-100:]

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps({
            "format": 1, "weights": self.weights, "episodes": self.episodes,
            "learning_rate": self.learning_rate, "epsilon": self.epsilon,
            "recent_rewards": self.recent_rewards
        }, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format") != 1 or len(data.get("weights", [])) != 8:
            raise ValueError("Unsupported or damaged checkpoint.")
        obj = cls(learning_rate=float(data["learning_rate"]), epsilon=float(data["epsilon"]))
        obj.weights = [float(x) for x in data["weights"]]
        obj.episodes = int(data["episodes"])
        obj.recent_rewards = list(data.get("recent_rewards", []))
        return obj
