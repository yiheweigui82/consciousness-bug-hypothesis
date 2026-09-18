"""Improved simulation for the Consciousness Bug Hypothesis.

Contrasts THREE error conditions:

  B0 - solvable        : outcome = action            (error fully action-correctable)
  B1 - external noise  : outcome = action XOR noise  (irreducible, but exogenous)
  B2 - self-coupled    : outcome = action XOR (prev_action & noise)
                         (irreducible, AND partly self-caused)

Hypothesis prediction (sharp):
  B2 should drive MORE self-modeling than B0 or B1,
  because only in B2 does the agent have reason to model "itself"
  as a cause of persistent error.
  B1 should NOT drive self-modeling: the error is someone else's fault.

Run:
    python simulation.py --episodes 800 --seed 1
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


class PredictionErrorEnv(gym.Env):
    """Observation: [target, previous_action, previous_outcome]."""

    metadata = {"render_modes": []}

    def __init__(self, noise_mode: str = "solvable", max_steps: int = 20):
        super().__init__()
        self.noise_mode = noise_mode  # 'solvable' | 'external' | 'self_coupled'
        self.max_steps = max_steps
        self.observation_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(3,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(2)
        self.t = 0
        self.target = 0
        self.previous_action = 0
        self.previous_outcome = 0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.t = 0
        self.target = int(self.np_random.integers(0, 2))
        self.previous_action = 0
        self.previous_outcome = 0
        return self._obs(), {}

    def _obs(self):
        return np.array(
            [self.target, self.previous_action, self.previous_outcome],
            dtype=np.float32)

    def step(self, action):
        action = int(action)
        noise = int(self.np_random.integers(0, 2))

        if self.noise_mode == "solvable":
            outcome = action
            self_contrib = 0.0
            ext_contrib = 0.0
        elif self.noise_mode == "external":
            # Irreducible, exogenous: error is not the agent's fault.
            outcome = action ^ noise
            self_contrib = 0.0
            ext_contrib = 1.0
        elif self.noise_mode == "self_coupled":
            # Irreducible AND partly self-caused: error depends on the agent's
            # OWN previous action interacting with noise. The agent has reason
            # to model "itself" as part of the cause.
            coupled = self.previous_action & noise
            outcome = action ^ coupled
            self_contrib = float(coupled)
            ext_contrib = float(noise)
        else:
            raise ValueError(self.noise_mode)

        reward = 1.0 if outcome == self.target else -1.0

        self.previous_action = action
        self.previous_outcome = outcome
        self.t += 1
        terminated = self.t >= self.max_steps
        self.target = int(self.np_random.integers(0, 2))

        return self._obs(), reward, terminated, False, {
            "outcome": outcome,
            "noise": noise,
            "self_contrib": self_contrib,
            "ext_contrib": ext_contrib,
        }


class Agent(nn.Module):
    def __init__(self, obs_dim=3, hidden=64):
        super().__init__()
        self.body = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
        )
        self.policy = nn.Linear(hidden, 2)
        self.outcome_pred = nn.Linear(hidden, 2)
        # self-prediction now targets the agent's OWN internal representation
        # evolution (a one-step latent prediction), not its action.
        self.self_pred = nn.Linear(hidden, hidden)
        # error attribution: 0=external, 1=self-caused, 2=unknown
        self.error_attr = nn.Linear(hidden, 3)

    def forward(self, obs):
        h = self.body(obs)
        return {
            "h": h,
            "policy": self.policy(h),
            "outcome_pred": self.outcome_pred(h),
            "self_pred": self.self_pred(h),
            "error_attr": self.error_attr(h),
        }


@dataclass
class Stats:
    reward: float = 0.0
    prediction_error: float = 0.0
    self_prediction_error: float = 0.0  # MSE on self-latent prediction
    self_causal_attribution: float = 0.0  # fraction correctly calling error self-caused
    ext_attribution: float = 0.0         # fraction correctly calling error external


def set_seed(seed: int):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)


def train(mode: str, episodes: int, seed: int):
    set_seed(seed)
    env = PredictionErrorEnv(noise_mode=mode)
    agent = Agent()
    opt = optim.Adam(agent.parameters(), lr=3e-3)

    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        h_prev = None

        while not done:
            x = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
            out = agent(x)

            if random.random() < 0.10:
                action = env.action_space.sample()
            else:
                action = int(out["policy"].argmax(dim=-1).item())

            next_obs, reward, terminated, truncated, info = env.step(action)

            target_outcome = torch.tensor([info["outcome"]], dtype=torch.long)
            target_action = torch.tensor([action], dtype=torch.long)

            loss_outcome = nn.functional.cross_entropy(out["outcome_pred"], target_outcome)

            # Self-prediction: predict the NEXT internal representation.
            # In B2, the next representation depends partly on the agent's own
            # previous action (self-caused error), so this is genuinely harder
            # and more meaningful than predicting the action label.
            loss_self = 0.0
            if h_prev is not None:
                loss_self = nn.functional.mse_loss(out["self_pred"], h_prev.detach())

            # Error attribution (3-way): 0=external, 1=self-caused, 2=unknown.
            if info["self_contrib"] > 0:
                attr_target = torch.tensor([1], dtype=torch.long)
            elif info["ext_contrib"] > 0:
                attr_target = torch.tensor([0], dtype=torch.long)
            else:
                attr_target = torch.tensor([2], dtype=torch.long)
            loss_attr = nn.functional.cross_entropy(out["error_attr"], attr_target)

            policy_loss = -torch.tensor(reward) * torch.log_softmax(
                out["policy"], dim=-1)[0, action]

            loss = loss_outcome + 0.5 * loss_self + 0.5 * loss_attr + policy_loss

            opt.zero_grad(); loss.backward(); opt.step()

            h_prev = out["h"].detach()
            obs = next_obs
            done = terminated or truncated

    return agent, env


@torch.no_grad()
def evaluate(agent, env, episodes=300):
    reward_sum = 0.0
    errors = []
    self_mse = []
    self_attr_correct = 0
    ext_attr_correct = 0
    total_steps = 0

    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        h_prev = None

        while not done:
            x = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
            out = agent(x)
            action = int(out["policy"].argmax(dim=-1).item())
            next_obs, reward, terminated, truncated, info = env.step(action)

            pred_outcome = int(out["outcome_pred"].argmax(dim=-1).item())
            pred_attr = int(out["error_attr"].argmax(dim=-1).item())

            reward_sum += reward
            errors.append(float(pred_outcome != info["outcome"]))

            if h_prev is not None:
                self_mse.append(float(nn.functional.mse_loss(
                    out["self_pred"], h_prev).item()))

            # Attribution correctness: did the agent correctly blame itself
            # (B2 self-caused) or an external cause (B1)?
            if info["self_contrib"] > 0:
                self_attr_correct += int(pred_attr == 1)
                total_steps += 1
            elif info["ext_contrib"] > 0:
                ext_attr_correct += int(pred_attr == 0)
                total_steps += 1

            h_prev = out["h"].detach()
            obs = next_obs
            done = terminated or truncated

    return Stats(
        reward=reward_sum / episodes,
        prediction_error=float(np.mean(errors)),
        self_prediction_error=float(np.mean(self_mse)) if self_mse else float("nan"),
        self_causal_attribution=float(self_attr_correct / max(total_steps, 1)),
        ext_attribution=float(ext_attr_correct / max(total_steps, 1)),
    )


def run(args):
    rows = []
    for mode, label in [
        ("solvable", "B0 solvable"),
        ("external", "B1 external_noise"),
        ("self_coupled", "B2 self_coupled"),
    ]:
        agent, env = train(mode, args.episodes, args.seed)
        rows.append((label, evaluate(agent, env, episodes=args.eval_episodes)))

    print("\n=== Consciousness Bug Hypothesis — improved experiment ===")
    print("Prediction: B2 (self-coupled error) should drive MORE self-modeling\nthan B0 or B1. B1 (external error) should drive the LEAST.\n")

    header = f"{'condition':<22}{'reward':>9}{'pred_err':>9}{'selfMSE':>9}{'selfAttr':>9}{'extAttr':>9}"
    print(header)
    for label, s in rows:
        print(f"{label:<22}{s.reward:>9.3f}{s.prediction_error:>9.3f}{s.self_prediction_error:>9.3f}{s.self_causal_attribution:>9.3f}{s.ext_attribution:>9.3f}")

    print("\nThe crucial column is selfAttr (correctly blaming 'myself' for\npersistent error) and selfMSE (cost of predicting my own latent state).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=800)
    parser.add_argument("--eval-episodes", type=int, default=300)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    run(args)

