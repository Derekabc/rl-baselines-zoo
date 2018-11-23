import os
import argparse

import gym
import numpy as np
from stable_baselines.common.vec_env import VecVideoRecorder, VecFrameStack, VecNormalize

from .utils import ALGOS, create_test_env

parser = argparse.ArgumentParser()
parser.add_argument('--env', help='environment ID', type=str, default='CartPole-v1')
parser.add_argument('-f', '--folder', help='Log folder', type=str, default='trained_agents')
parser.add_argument('-o', '--output-folder', help='Output folder', type=str, default='logs/videos/')
parser.add_argument('--algo', help='RL Algorithm', default='ppo2',
                    type=str, required=False, choices=list(ALGOS.keys()))
parser.add_argument('-n', '--n-timesteps', help='number of timesteps', default=1000,
                    type=int)
parser.add_argument('--n-envs', help='number of environments', default=1,
                    type=int)
parser.add_argument('--deterministic', action='store_true', default=False,
                    help='Use deterministic actions')
parser.add_argument('--seed', help='Random generator seed', type=int, default=0)
parser.add_argument('--no-render', action='store_true', default=False,
                    help='Do not render the environment (useful for tests)')
args = parser.parse_args()

env_id = args.env
algo = args.algo
folder = args.folder
video_folder = args.output_folder
seed = args.seed
deterministic = args.deterministic
video_length = args.n_timesteps
n_envs = args.n_envs

model_path = "{}/{}/{}.pkl".format(folder, algo, env_id)

stats_path = "{}/{}/{}/".format(folder, algo, env_id)
if not os.path.isdir(stats_path):
    stats_path = None

is_atari = 'NoFrameskip' in env_id

env = create_test_env(env_id, n_envs=n_envs, is_atari=is_atari,
                      stats_path=stats_path, norm_reward=False,
                      seed=seed, log_dir=None, should_render=not args.no_render)

model = ALGOS[algo].load(model_path)

obs = env.reset()

# Note: apparently it renders by default
env = VecVideoRecorder(env, video_folder,
                       record_video_trigger=lambda x: x == 0, video_length=video_length,
                       name_prefix="{}-{}".format(algo, env_id))

env.reset()
for _ in range(video_length + 1):
    # action = [env.action_space.sample()]
    action, _ = model.predict(obs, deterministic=deterministic)
    if isinstance(env.action_space, gym.spaces.Box):
        action = np.clip(action, env.action_space.low, env.action_space.high)
    obs, _, _, _ = env.step(action)

# Workaround for https://github.com/openai/gym/issues/893
if n_envs == 1 and 'Bullet' not in env_id and not is_atari:
    env = env.venv
    # DummyVecEnv
    while isinstance(env, VecNormalize) or isinstance(env, VecFrameStack):
        env = env.venv
    env.envs[0].env.close()
else:
    # SubprocVecEnv
    env.close()
