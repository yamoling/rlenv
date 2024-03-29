import numpy as np
from rlenv.models import RLEnv, Observation
from .rlenv_wrapper import RLEnvWrapper


class AgentId(RLEnvWrapper):
    """RLEnv wrapper that adds a one-hot encoding of the agent id."""

    def __init__(self, env: RLEnv):
        assert len(env.extra_feature_shape) == 1, "AgentIdWrapper only works with single dimension extras"
        super().__init__(env, extra_feature_shape=(env.n_agents + env.extra_feature_shape[0],))
        self._identity = np.identity(env.n_agents, dtype=np.float32)

    def step(self, actions):
        obs, r, done, truncated, info = super().step(actions)
        return self._add_one_hot(obs), r, done, truncated, info

    def reset(self):
        return self._add_one_hot(super().reset())

    def _add_one_hot(self, observation: Observation):
        observation.extras = np.concatenate([observation.extras, self._identity], axis=-1)
        return observation
