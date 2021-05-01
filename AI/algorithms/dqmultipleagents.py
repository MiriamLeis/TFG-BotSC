import keras
import os
import itertools
import random

import numpy as np

from keras import Model
from keras.layers import Dense, Input
from collections import deque

from algorithms.abstract_agent import AbstractAgent
from algorithms.dqagent import DQAgent

class DQMultipleAgent(AbstractAgent):
    def __init__(self, agent, total_episodes):
        super().__init__()
        self.agent = agent
        
        info = self.agent.get_info()

        self.networks = []
        for ag in info['agents']:
            self.networks.append(DQAgent(agent=ag, total_episodes=total_episodes))

    '''
        Return basic information
    '''
    def get_args(self):
        return self.agent.get_args()

    '''
        Prepare agent for next episode
    '''
    def prepare(self, env, ep):
        for net in self.networks:
            net.prepare(env=env, ep=ep)

    '''
        Update basic values
    '''
    def update(self, env, deltaTime):
        for net in self.networks:
            net.update(env=env, deltaTime=deltaTime)
        
    '''
        Update basic values
    '''
    def late_update(self, env, deltaTime):
        for net in self.networks:
            net.late_update(env=env, deltaTime=deltaTime)

    '''
        Do step of the environment
        Return PySC2 environment obs
    '''
    def step(self, env, environment):
        for net in self.networks:
            net.step(env=env, environment=environment)

    def train(self):
        for net in self.networks:
            net.train()

    '''
        Return action with maxium reward
    '''
    def get_max_action(self, env):
        for net in self.networks:
            net.get_max_action(env=env)

    '''
        Choose action for current state.
        This action could be random or the one with maxium reward, depending on epsilon value.
    '''
    def choose_action(self, env):
        for net in self.networks:
            net.choose_action(env=env)

    '''
        Save models to specify file
    '''              
    def save(self, filepath):
        cont = 1
        for net in self.networks:
            net.save(filepath=filepath + '_' + cont)
            cont += 1

    '''
        Load models from specify file
    '''        
    def load(self, filepath):
        cont = 1
        for net in self.networks:
            net.load(filepath=filepath + '_' + cont)
            cont += 1