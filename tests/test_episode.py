import numpy as np
import random
from rlenv.models import EpisodeBuilder, Transition, Episode, RLEnv
from rlenv import wrappers
from .mock_env import MockEnv


def generate_episode(env: RLEnv) -> Episode:
    obs = env.reset()
    episode = EpisodeBuilder()
    while not episode.is_finished:
        action = env.action_space.sample()
        next_obs, r, done, truncated, info = env.step(action)
        episode.add(Transition(obs, action, r, done, info, next_obs, truncated))
        obs = next_obs
    return episode.build()


def test_episode_builder_is_done():
    env = MockEnv(2)
    obs = env.reset()
    # Set the 'done' flag
    builder = EpisodeBuilder()
    assert not builder.is_finished
    builder.add(Transition(obs, np.array([0, 0]), 0, False, {}, obs, False))
    assert not builder.is_finished
    builder.add(Transition(obs, np.array([0, 0]), 0, True, {}, obs, False))
    assert builder.is_finished

    # Set the 'truncated' flag
    builder = EpisodeBuilder()
    assert not builder.is_finished
    builder.add(Transition(obs, np.array([0, 0]), 0, False, {}, obs, False))
    assert not builder.is_finished
    builder.add(Transition(obs, np.array([0, 0]), 0, False, {}, obs, True))
    assert builder.is_finished


def test_build_not_finished_episode_fails():
    builder = EpisodeBuilder()
    try:
        builder.build()
        assert False, "Should have raised an AssertionError"
    except AssertionError:
        pass
    env = MockEnv(2)
    obs = env.reset()
    builder.add(
        Transition(
            obs=obs,
            action=np.array([0, 0]),
            reward=0,
            done=False,
            info={},
            obs_=obs,
            truncated=False,
        )
    )
    try:
        builder.build()
        assert False, "Should have raised an AssertionError"
    except AssertionError:
        pass


def test_returns():
    env = MockEnv(2)
    obs = env.reset()
    builder = EpisodeBuilder()
    n_steps = 20
    gamma = 0.95
    rewards = []
    for i in range(n_steps):
        done = i == n_steps - 1
        r = random.random()
        rewards.append(r)
        builder.add(Transition(obs, np.array([0, 0]), r, done, {}, obs, False))
    episode = builder.build()
    returns = episode.compute_returns(discount=gamma)
    for i, r in enumerate(returns):
        G_t = rewards[-1]
        for j in range(len(rewards) - 2, i - 1, -1):
            G_t = rewards[j] + gamma * G_t
        assert abs(r - G_t) < 1e-6


def test_dones_not_set_when_truncated():
    # The time limit issues a 'truncated' flag at t=10 but the episode should not be done
    env = wrappers.TimeLimit(MockEnv(2), MockEnv.END_GAME - 1)
    episode = generate_episode(env)
    # The episode sould be truncated but not done
    assert np.all(episode.dones == 0)
    padded = episode.padded(MockEnv.END_GAME * 2)
    assert np.all(padded.dones == 0)


def test_done_when_time_limit_reached_with_extras():
    env = wrappers.TimeLimit(MockEnv(2), MockEnv.END_GAME - 1, add_extra=True)
    episode = generate_episode(env)
    # The episode sould be truncated but not done
    assert episode.dones[-1] == 1.0
    padded = episode.padded(MockEnv.END_GAME * 2)
    assert np.all(padded.dones[len(episode) - 1:] == 1)


def test_dones_set_with_paddings():
    # The time limit issues a 'truncated' flag at t=10 but the episode should not be done
    env = MockEnv(2)
    episode = generate_episode(env)
    # The episode sould be truncated but not done
    assert np.all(episode.dones[:-1] == 0)
    assert episode.dones[-1] == 1
    padded = episode.padded(MockEnv.END_GAME * 2)
    assert np.all(padded.dones[: MockEnv.END_GAME - 1] == 0)
    assert np.all(padded.dones[MockEnv.END_GAME - 1 :] == 1)


def test_truncated_and_done():
    env = wrappers.TimeLimit(MockEnv(2), MockEnv.END_GAME)
    obs = env.reset()
    episode = EpisodeBuilder()
    done = truncated = False
    while not episode.is_finished:
        action = env.action_space.sample()
        next_obs, r, done, truncated, info = env.step(action)
        episode.add(Transition(obs, action, r, done, info, next_obs, truncated))
        obs = next_obs
    assert done and truncated
    episode = episode.build()

    assert np.all(episode.dones[:-1] == 0)
    assert episode.dones[-1] == 1


def test_masks():
    env = wrappers.TimeLimit(MockEnv(2), 10)
    episode = generate_episode(env)
    assert np.all(episode.mask == 1)
    padded = episode.padded(25)
    assert np.all(padded.mask[:10] == 1)
    assert np.all(padded.mask[10:] == 0)


def test_padded_raises_error_with_too_small_size():
    env = MockEnv(2)
    episode = generate_episode(env)
    try:
        episode.padded(1)
        assert False
    except ValueError:
        pass


def test_padded():
    env = wrappers.TimeLimit(MockEnv(2), 10)

    for i in range(5, 11):
        env._step_limit = i
        episode = generate_episode(env)
        assert len(episode) == i
        padded = episode.padded(10)
        assert padded._observations.shape[0] == 11
        assert padded.obs.shape[0] == 10
        assert padded.obs_.shape[0] == 10
        assert padded.actions.shape[0] == 10
        assert padded.rewards.shape[0] == 10
        assert padded.dones.shape[0] == 10
        assert padded.extras.shape[0] == 10
        assert padded.extras_.shape[0] == 10
        assert padded.available_actions.shape[0] == 10
        assert padded.available_actions_.shape[0] == 10
        assert padded.mask.shape[0] == 10


def test_retrieve_episode_transitions():
    env = wrappers.TimeLimit(MockEnv(2), 10)
    episode = generate_episode(env)
    transitions = list(episode.transitions())
    assert len(transitions) == 10
    assert all(not t.done for t in transitions)
    assert all(not t.truncated for t in transitions[:-1])
    assert transitions[-1].truncated


def test_iterate_on_episode():
    env = wrappers.TimeLimit(MockEnv(2), 10)
    episode = generate_episode(env)
    for i, t in enumerate(episode):  # type: ignore
        assert not t.done
        if i == 9:
            assert t.truncated
        else:
            assert not t.truncated
