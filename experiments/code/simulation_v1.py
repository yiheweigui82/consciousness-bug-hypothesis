"""Minimal runnable simulation for the Consciousness Bug Hypothesis.  [ORIGINAL v1]

This is a behavioral toy model, NOT a consciousness detector.

It compares two environments:
1. solvable: the agent can reduce prediction error by choosing the correct action;
2. unsolvable: a hidden disturbance makes part of the outcome uncontrollable.

The agent learns:
- a policy;
- a one-step outcome predictor;
- a self-predictor for its next action;
- an error-attribution head.

The main question:
Does persistent uncontrollable prediction error increase grounded
self-reference / self-model usage?

== KNOWN LIMITATION (v1) ==
As released, this script shows a ceiling effect: "grounded self-reference"
and "self-prediction accuracy" saturate at 1.000 in BOTH conditions, because
the self-prediction head learns to predict the agent's ACTION, which is
perfectly predictable under a stable policy. It therefore cannot distinguish
solvable from unsolvable error.

See simulation.py (v2) for a corrected design that targets the agent's
internal representation and error ATTRIBUTION instead of action labels.

Requirements:
    pip install -r requirements.txt

Run:
    python simulation.py --episodes 3000 --seed 1
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
    """
    Observation:
        [target, previous_action, previous_outcome]

    The target is binary.
    Solvable condition:
        outcome = action
    Unsolvable condition:
        outcome = action XOR hidden_noise

    Reward:
        +1 when outcome == target, else -1.

    In the unsolvable condition, hidden_noise creates irreducible
    prediction error. The action still affects the outcome, so the
    agent has a reason to model its own previous action.
    """

    metadata = {"render_modes": []}

    def __init__(self, uncontrollable: bool, max_steps: int = 20):
        super().__init__()
        self.uncontrollable = uncontrollable
        self.max_steps = max_steps
        self.observation_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(3,), dtype=np.float32
        )
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
            dtype=np.float32,
        )

    def step(self, action):
        action = int(action)

        hidden_noise = int(self.np_random.integers(0, 2)) if self.uncontrollable else 0
        outcome = action ^ hidden_noise

        reward = 1.0 if outcome == self.target else -1.0

        self.previous_action = action
        self.previous_outcome = outcome
        self.t += 1

        terminated = self.t >= self.max_steps
        self.target = int(self.np_random.integers(0, 2))

        return self._obs(), reward, terminated, False, {
            "outcome": outcome,
            "hidden_noise": hidden_noise,
        }


class Agent(nn.Module):
    def __init__(self, obs_dim=3, hidden=64):
        super().__init__()
        self.body = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
        )
        self.policy = nn.Linear(hidden, 2)
        self.outcome_pred = nn.Linear(hidden, 2)
        self.self_pred = nn.Linear(hidden, 2)
        self.error_attr = nn.Linear(hidden, 2)

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
    self_reference: float = 0.0
    self_prediction_accuracy: float = 0.0
    error_attribution_accuracy: float = 0.0


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def train(uncontrollable: bool, episodes: int, seed: int):
    set_seed(seed)

    env = PredictionErrorEnv(uncontrollable=uncontrollable)
    agent = Agent()
    opt = optim.Adam(agent.parameters(), lr=3e-3)

    total_reward = 0.0

    for _ in range(episodes):
        obs, _ = env.reset()
        done = False

        while not done:
            x = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
            out = agent(x)

            # Epsilon-greedy exploration.
            if random.random() < 0.10:
                action = env.action_space.sample()
            else:
                action = int(out["policy"].argmax(dim=-1).item())

            next_obs, reward, terminated, truncated, info = env.step(action)

            target_outcome = torch.tensor([info["outcome"]], dtype=torch.long)
            target_action = torch.tensor([action], dtype=torch.long)

            # The hidden disturbance is the true source of irreducible error.
            target_noise = torch.tensor([info["hidden_noise"]], dtype=torch.long)

            # Outcome prediction is trained against the actual outcome.
            loss_outcome = nn.functional.cross_entropy(
                out["outcome_pred"], target_outcome
            )

            # Self-prediction asks the representation to learn to predict its own action.
            loss_self = nn.functional.cross_entropy(
                out["self_pred"], target_action
            )

            # Error attribution: 0 = externally solvable, 1 = hidden disturbance.
            loss_attr = nn.functional.cross_entropy(
                out["error_attr"], target_noise
            )

            # Policy objective.
            policy_loss = -torch.tensor(reward) * torch.log_softmax(
                out["policy"], dim=-1
            )[0, action]

            loss = loss_outcome + 0.5 * loss_self + 0.5 * loss_attr + policy_loss

            opt.zero_grad()
            loss.backward()
            opt.step()

            total_reward += reward
            obs = next_obs
            done = terminated or truncated

    return agent, env, total_reward


@torch.no_grad()
def evaluate(agent, env, episodes=500):
    reward_sum = 0.0
    errors = []
    self_acc = []
    attr_acc = []

    # "Grounded self-reference" proxy:
    # count a self-model signal only when the self-prediction head correctly
    # predicts the action AND the action has causal relevance to the outcome.
    grounded_self_reference = 0

    total_steps = 0

    for _ in range(episodes):
        obs, _ = env.reset()
        done = False

        while not done:
            x = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
            out = agent(x)

            action = int(out["policy"].argmax(dim=-1).item())
            next_obs, reward, terminated, truncated, info = env.step(action)

            pred_outcome = int(out["outcome_pred"].argmax(dim=-1).item())
            pred_self = int(out["self_pred"].argmax(dim=-1).item())
            pred_attr = int(out["error_attr"].argmax(dim=-1).item())

            reward_sum += reward
            errors.append(float(pred_outcome != info["outcome"]))
            self_acc.append(float(pred_self == action))
            attr_acc.append(float(pred_attr == info["hidden_noise"]))

            # In this toy environment, the chosen action directly contributes
            # to the outcome (XOR hidden noise), so correctly predicting one's
            # own action is a grounded self-model signal.
            grounded_self_reference += int(pred_self == action)
            total_steps += 1

            obs = next_obs
            done = terminated or truncated

    return Stats(
        reward=reward_sum / episodes,
        prediction_error=float(np.mean(errors)),
        self_reference=grounded_self_reference / total_steps,
        self_prediction_accuracy=float(np.mean(self_acc)),
        error_attribution_accuracy=float(np.mean(attr_acc)),
    )


def run(args):
    rows = []

    for condition, uncontrollable in [
        ("solvable_control", False),
        ("uncontrollable_error", True),
    ]:
        agent, env, _ = train(
            uncontrollable=uncontrollable,
            episodes=args.episodes,
            seed=args.seed,
        )
        stats = evaluate(agent, env, episodes=args.eval_episodes)

        rows.append((condition, stats))

    print("\n=== Consciousness Bug Toy Experiment ===")
    print("NOTE: These metrics measure behavior, not subjective consciousness.\n")

    for condition, s in rows:
        print(condition)
        print(f"  mean episode reward:        {s.reward: .3f}")
        print(f"  outcome prediction error:  {s.prediction_error: .3f}")
        print(f"  grounded self-reference:   {s.self_reference: .3f}")
        print(f"  self-prediction accuracy:  {s.self_prediction_accuracy: .3f}")
        print(f"  error attribution accuracy:{s.error_attribution_accuracy: .3f}")
        print()

    a = rows[0][1]
    b = rows[1][1]

    print("Difference (uncontrollable - solvable)")
    print(f"  prediction error: {b.prediction_error - a.prediction_error:+.3f}")
    print(f"  self-reference:  {b.self_reference - a.self_reference:+.3f}")
    print(f"  self-model acc.:  {b.self_prediction_accuracy - a.self_prediction_accuracy:+.3f}")
    print(f"  attribution acc.:  {b.error_attribution_accuracy - a.error_attribution_accuracy:+.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=3000)
    parser.add_argument("--eval-episodes", type=int, default=500)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    run(args)
