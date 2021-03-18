import sys
import numpy as np

from pysc2.lib import actions
from pysc2.env import sc2_env
from pysc2 import maps
from absl import flags
from tqdm import tqdm

import mtb_agent4Directions as mtb_agent
from qtable import QTable

FLAGS = flags.FLAGS
flags.DEFINE_boolean("replay", False, "If you want to save replay")
flags.DEFINE_boolean("scratch", True, "If you want to continue with an existing Q-table")
flags.DEFINE_boolean("visualize", False, "If you want to visualize PySC2 window")
flags.DEFINE_integer("episodes", 100, "Number of episodes")
flags.DEFINE_integer("steps", 1_900, "Number of steps in each episode")


def main():
    FLAGS(sys.argv)

    AGENT_INTERFACE_FORMAT = sc2_env.AgentInterfaceFormat(
            feature_dimensions=sc2_env.Dimensions(screen=64, minimap=16))

    # Create environment
    with sc2_env.SC2Env(map_name=maps.get('MoveToBeacon'),
                        players=[sc2_env.Agent(sc2_env.Race.terran)],
                        visualize=FLAGS.visualize,
                        agent_interface_format=AGENT_INTERFACE_FORMAT,
                        step_mul= 1) as env:

        # Set type of agent
        if FLAGS.scratch:
            agent = mtb_agent.MoveToBeaconAgent(FLAGS.episodes - 5)
        else:
            agent = mtb_agent.MoveToBeaconAgent(FLAGS.episodes - 5, load_qt='saves/mtb_qtable.npy', load_st='saves/mtb_states.npy')

        # Loop of game
        for i in tqdm(range(1, FLAGS.episodes+1), ascii=True, unit="episode"):
            obs = env.reset()

            ep_reward = 0
            agent.qtable.set_actual_episode(i + 1)

            marineActualPos = mtb_agent.get_marine_pos(obs[0])
            beaconActualPos = mtb_agent.get_beacon_pos(obs[0])

            func = actions.FunctionCall(mtb_agent._SELECT_ARMY, [mtb_agent._SELECT_ALL])
            state = -1
            oldDist = 0
            action = -1

            error = False

            actualTime = 2.0
            timeForAction = 0.75
            lastTime = (obs[0]).observation["game_loop"] / 16
            delta = 0.0
            for j in range(FLAGS.steps):
                marineActualPos = mtb_agent.get_marine_pos(obs[0])
                
                if actualTime >= timeForAction:

                    obs = env.step(actions=[func])
                    actualTime = 0.0
                    # if we could move
                    if state != -1:

                        next_state, newDist, _ = mtb_agent.get_state(obs[0])
                        beaconNewPos = mtb_agent.get_beacon_pos(obs[0])

                        reward = oldDist - newDist
                        if beaconActualPos[0] != beaconNewPos[0] or beaconActualPos[1] != beaconNewPos[1]:
                            reward = 5
                            beaconActualPos[0] = beaconNewPos[0]
                            beaconActualPos[1] = beaconNewPos[1]
                        ep_reward += reward
                        agent.qtable.learn(state, action, reward, next_state)

                    state, action, func, oldDist, marinePosibleNextPosition = agent.step(obs[0])

                # if we didnt end our action and we can move
                elif mtb_agent._MOVE_SCREEN in obs[0].observation['available_actions']: 
                        obs = env.step(actions=[func])
                # if we cant move we select army
                else:
                    obs = env.step(actions=[actions.FunctionCall(mtb_agent._SELECT_ARMY, [mtb_agent._SELECT_ALL])])
            
                realTime = ((obs[0]).observation["game_loop"] / 16)
                delta = realTime - lastTime
                lastTime = realTime
                actualTime += delta
        
        # Save replay of the game
        if FLAGS.replay:
            env.save_replay(mtb_agent.MoveToBeaconAgent.__name__)

        
        # Save Q-Table and states
        agent.qtable.save_qtable('saves/mtb_qtable.npy')
        agent.qtable.save_states('saves/mtb_states.npy')

if __name__ == "__main__":
    main()