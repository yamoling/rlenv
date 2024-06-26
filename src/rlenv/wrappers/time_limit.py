from dataclasses import dataclass
from typing import Optional, TypeVar
import numpy as np

from rlenv.models import ActionSpace, Observation
from .rlenv_wrapper import RLEnvWrapper, RLEnv

A = TypeVar("A", bound=ActionSpace)


@dataclass
class TimeLimit(RLEnvWrapper[A]):
    """
    Limits the number of time steps for an episode. When the number of steps is reached, then the episode is truncated.

    - If the `add_extra` flag is set to True, then an extra signal is added to the observation, which is the ratio of the
    current step over the maximum number of steps. In this case, the done flag is also set to True when the maximum
    number of steps is reached.
    - The `truncated` flag is only set to `True` when the maximum number of steps is reached and the episode is not done.
    - The `truncation_penalty` is subtracted from the reward when the episode is truncated. This is only possible when
    the `add_extra` flag is set to True, otherwise the agent is not able to anticipate this penalty.
    """

    step_limit: int
    add_extra: bool
    truncation_penalty: float

    def __init__(self, env: RLEnv[A], step_limit: int, add_extra: bool = False, truncation_penalty: Optional[float] = None) -> None:
        assert len(env.extra_feature_shape) == 1
        extras_shape = env.extra_feature_shape
        if add_extra:
            dims = env.extra_feature_shape[0]
            extras_shape = (dims + 1,)
        super().__init__(env, extra_feature_shape=extras_shape)
        self.step_limit = step_limit
        self._current_step = 0
        self.add_extra = add_extra
        if truncation_penalty is None:
            truncation_penalty = 0.0
        else:
            assert add_extra, "The truncation penalty can only be set when the add_extra flag is set to True, otherwise agents are not able to anticipate this punishment."
        assert truncation_penalty >= 0, "The truncation penalty must be a positive value."
        self.truncation_penalty = truncation_penalty

    def reset(self):
        self._current_step = 0
        obs = super().reset()
        if self.add_extra:
            self.add_time_extra(obs)
        return obs

    def step(self, actions):
        self._current_step += 1
        obs_, reward, done, truncated, info = super().step(actions)
        if self.add_extra:
            self.add_time_extra(obs_)
        # If we reach the time limit
        if self._current_step >= self.step_limit:
            # And the episode is not done
            if not done:
                # then we set the truncation flag
                truncated = True
                if self.add_extra:
                    done = True
        if truncated:
            reward -= self.truncation_penalty
        return obs_, reward, done, truncated, info

    def add_time_extra(self, obs: Observation):
        time_ratio = np.full(
            (self.n_agents, 1),
            self._current_step / self.step_limit,
            dtype=np.float32,
        )
        obs.extras = np.concatenate([obs.extras, time_ratio], axis=-1)
