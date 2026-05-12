"""
src/navigation/rl_controller.py
PPO-based energy-aware navigation controller.
Wraps Stable-Baselines3 PPO with evaluation and checkpointing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger


class RLNavigationController:
    """
    PPO actor-critic navigation policy.

    Reward: R(t) = α·T(t) − β·E(t) − γ·P(t)
      - T(t): number of actively tracked targets
      - E(t): energy consumed this step
      - P(t): ID-switch and track-loss penalty

    Network: 2-layer MLP, 256 hidden units, tanh activation.
    """

    def __init__(self, cfg: dict, env=None):
        self.cfg = cfg
        self.rl_cfg = cfg["rl"]
        self.env = env
        self.model = None
        self._checkpoint_dir = Path(cfg["logging"]["checkpoint_dir"]) / "rl"
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # ── Build model ───────────────────────────────────────────────────────────

    def build(self, env=None) -> None:
        """Instantiate PPO model from config."""
        try:
            from stable_baselines3 import PPO
            from stable_baselines3.common.callbacks import (
                EvalCallback, CheckpointCallback
            )
        except ImportError:
            logger.error("stable-baselines3 not installed. Run: pip install stable-baselines3")
            return

        if env is not None:
            self.env = env

        if self.env is None:
            raise ValueError("Environment must be provided before calling build().")

        rl = self.rl_cfg
        # Only enable TensorBoard logging if the package is available
        try:
            import tensorboard  # noqa: F401
            tb_log = str(Path(self.cfg["logging"]["log_dir"]) / "ppo")
        except ImportError:
            tb_log = None
            logger.warning("tensorboard not installed — TensorBoard logging disabled.")

        self.model = PPO(
            policy=rl["policy"],
            env=self.env,
            learning_rate=rl["learning_rate"],
            n_steps=rl["n_steps"],
            batch_size=rl["batch_size"],
            n_epochs=rl["n_epochs"],
            gamma=rl["gamma"],
            gae_lambda=rl["gae_lambda"],
            clip_range=rl["clip_range"],
            ent_coef=rl["ent_coef"],
            vf_coef=rl["vf_coef"],
            max_grad_norm=rl["max_grad_norm"],
            policy_kwargs=dict(
                net_arch=rl["policy_kwargs"]["net_arch"],
            ),
            tensorboard_log=tb_log,
            verbose=1,
        )
        logger.info("PPO model built successfully.")
        logger.info(f"  Network: {rl['policy_kwargs']['net_arch']}")
        logger.info(f"  LR: {rl['learning_rate']} | γ: {rl['gamma']} | λ: {rl['gae_lambda']}")

    # ── Training ──────────────────────────────────────────────────────────────

    def train(self, total_timesteps: Optional[int] = None) -> None:
        """Train PPO for the configured number of timesteps."""
        if self.model is None:
            raise RuntimeError("Call build() before train().")

        from stable_baselines3.common.callbacks import (
            EvalCallback, CheckpointCallback, CallbackList
        )

        total_steps = total_timesteps or self.rl_cfg["total_timesteps"]
        eval_freq = self.rl_cfg["eval_freq"]
        save_freq = self.cfg["logging"]["save_freq"]

        checkpoint_cb = CheckpointCallback(
            save_freq=save_freq,
            save_path=str(self._checkpoint_dir),
            name_prefix="ppo_aerial_tracking",
        )

        callbacks = CallbackList([checkpoint_cb])

        logger.info(f"Starting PPO training for {total_steps:,} timesteps ...")
        self.model.learn(
            total_timesteps=total_steps,
            callback=callbacks,
            progress_bar=True,
        )
        logger.success("Training complete.")
        self.save("final")

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict(self, obs: np.ndarray,
                deterministic: bool = True) -> np.ndarray:
        """Return action for a single observation."""
        if self.model is None:
            raise RuntimeError("Model not built or loaded.")
        action, _ = self.model.predict(obs, deterministic=deterministic)
        return action

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, tag: str = "latest") -> None:
        path = self._checkpoint_dir / f"ppo_{tag}"
        self.model.save(str(path))
        logger.info(f"Model saved → {path}.zip")

    def load(self, path: str) -> None:
        try:
            from stable_baselines3 import PPO
            self.model = PPO.load(path, env=self.env)
            logger.info(f"Model loaded ← {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

    # ── Evaluation ────────────────────────────────────────────────────────────

    def evaluate(self, n_episodes: int = 10) -> dict:
        """Run evaluation episodes and return aggregate stats."""
        if self.model is None or self.env is None:
            raise RuntimeError("Model and env required for evaluation.")

        episode_rewards, episode_lengths = [], []
        track_counts, energy_totals, id_switches = [], [], []

        for ep in range(n_episodes):
            obs, _ = self.env.reset()
            done = False
            ep_reward, ep_steps = 0.0, 0
            ep_tracks, ep_energy, ep_switches = [], 0.0, 0

            while not done:
                action = self.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated
                ep_reward += reward
                ep_steps += 1
                ep_tracks.append(info.get("n_tracks", 0))
                ep_energy = info.get("energy_consumed", 0.0)
                ep_switches += info.get("id_switches", 0)

            episode_rewards.append(ep_reward)
            episode_lengths.append(ep_steps)
            track_counts.append(np.mean(ep_tracks))
            energy_totals.append(ep_energy)
            id_switches.append(ep_switches)
            logger.info(f"  Episode {ep+1:02d}: reward={ep_reward:.1f} "
                        f"tracks={np.mean(ep_tracks):.1f} "
                        f"energy={ep_energy:.1f}J "
                        f"id_sw={ep_switches}")

        results = {
            "mean_reward": float(np.mean(episode_rewards)),
            "std_reward": float(np.std(episode_rewards)),
            "mean_tracks": float(np.mean(track_counts)),
            "mean_energy_J": float(np.mean(energy_totals)),
            "mean_id_switches": float(np.mean(id_switches)),
            "mean_episode_length": float(np.mean(episode_lengths)),
        }
        logger.success(f"Evaluation results: {results}")
        return results
