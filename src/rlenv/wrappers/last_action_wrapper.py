import numpy as np
from rlenv.models import Observation
from .rlenv_wrapper import RLEnvWrapper, RLEnv


class LastActionWrapper(RLEnvWrapper):
    """Env wrapper that adds the last action taken by the agents to the extra features."""
    def __init__(self, env: RLEnv) -> None:
        assert len(env.extra_feature_shape) == 1, "Adding last action is only possible with 1D extras"
        super().__init__(env)
        self._extra_feature_shape = (env.extra_feature_shape[0] + self.n_actions, )

    @property
    def extra_feature_shape(self):
        return self._extra_feature_shape

    def reset(self):
        obs = super().reset()
        return self._add_last_action(obs, None)

    def step(self, actions):
        obs_, reward, done, info = super().step(actions)
        obs_ = self._add_last_action(obs_, actions)
        return obs_, reward, done, info

    def _add_last_action(self, obs: Observation, last_actions: np.ndarray[np.int64] | None):
        one_hot_actions = np.zeros((self.n_agents, self.n_actions), dtype=np.float32)
        if last_actions is not None:
            index = np.arange(self.n_agents)
            one_hot_actions[index, last_actions] = 1.
        obs.extras = np.concatenate([obs.extras, one_hot_actions], axis=-1)
        return obs
