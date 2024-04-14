from typing import Any
import numpy as np
from rlenv.models import RLEnv, DiscreteActionSpace
from rlenv.wrappers import TimeLimit


class PymarlAdapter:
    """
    There is no official interface for PyMARL but aims at complying
    with the pymarl-qplex code base.
    """

    def __init__(self, env: RLEnv[DiscreteActionSpace], episode_limit: int):
        assert len(env.observation_shape) == 1, "Only 1D observations are supported because they must be concatenated with 1D extras"
        self.env = TimeLimit(env, episode_limit)
        self.episode_limit = episode_limit
        self.current_observation = None

    def step(self, actions) -> tuple[float, bool, dict[str, Any]]:
        """Returns reward, terminated, info"""
        obs, reward, done, truncated, info = self.env.step(actions)
        self.current_observation = obs
        return list(reward)[0], done or truncated, info

    def get_obs(self):
        """Returns all agent observations in a list"""
        if self.current_observation is None:
            raise ValueError("No observation available. Call reset() first.")
        return np.concatenate([self.current_observation.data, self.current_observation.extras], axis=-1)

    def get_obs_agent(self, agent_id: int):
        """Returns observation for agent_id"""
        return self.get_obs()[agent_id]

    def get_obs_size(self):
        """Returns the shape of the observation"""
        return self.env.observation_shape[0]

    def get_state(self):
        return self.env.get_state()

    def get_state_size(self):
        """Returns the shape of the state"""
        return self.env.state_shape[0]

    def get_avail_actions(self):
        return self.env.available_actions()

    def get_avail_agent_actions(self, agent_id):
        """Returns the available actions for agent_id"""
        return self.env.available_actions()

    def get_total_actions(self):
        """Returns the total number of actions an agent could ever take"""
        # Note: This is only suitable for a discrete 1 dimensional action space for each agent
        return self.env.n_actions

    def reset(self):
        """Returns initial observations and states"""
        self.current_observation = self.env.reset()

    def render(self):
        return self.env.render("human")

    def close(self):
        return

    def seed(self):
        self.env.seed(0)

    def save_replay(self):
        return

    def get_env_info(self):
        env_info = {
            "state_shape": self.get_state_size(),
            "obs_shape": self.get_obs_size(),
            "n_actions": self.get_total_actions(),
            "n_agents": self.env.n_agents,
            "episode_limit": self.env.step_limit,
        }
        try:
            env_info["unit_dim"] = self.env.agent_state_size
        except NotImplementedError:
            pass
        return env_info
