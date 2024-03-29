import keras
import os
import itertools
import random

import numpy as np

from keras import Model
from keras.layers import Dense, Input
from collections import deque

from agents.abstract_agent import AbstractAgent

class DQAgent(AbstractAgent):
    def __init__(self, info):
        self.learning = info['learn']
        self.total_episodes = info['episodes']

        self.actions = info['actions']
        self.discount = info['discount']
        self.rep_mem_size = info['replay_mem_size']
        self.min_rep_mem_size = info['learn_every']
        self.min_rep_mem_total = info['min_replay_mem_size']
        self.minibatch_size = info['minibatch_size']
        self.update_time = info['update_time']
        self.max_cases = info['max_cases']
        self.cases_to_delete = info['cases_to_delete']

        # main model
        # model that we are not fitting every step
        # gets trained every step
        self.model = self.__create_model(num_states=info['num_states'], hidden_nodes=info['hidden_nodes'], hidden_layers=info['hidden_layer'])

        # target model
        # this is what we .predict against every step
        self.target_model = self.__create_model(num_states=info['num_states'], hidden_nodes=info['hidden_nodes'], hidden_layers=info['hidden_layer'])
        self.target_model.set_weights(self.model.get_weights()) # do it again after a while

        self.replay_memory = deque(maxlen=self.rep_mem_size)
        self.target_update_counter = 0

    '''
        Prepare agent for next episode
    '''
    def prepare(self, env, episode):
        self.__set_epsilon(episode=episode)
        self.action = 0
        self.current_state = env.get_state()

    '''
        Update basic values
    '''
    def update(self, env, deltaTime):
        self.new_state = env.get_state()
        self.reward = env.get_reward(action=self.action)
        env.update(deltaTime=deltaTime)

        # train
        if self.learning:
            self.train()

        # late update
        self.current_state = self.new_state

        # get action
        if self.learning:
            self._choose_action(env=env)
        else:
            self._get_max_action(env=env)

    '''
        Execute Deep Q-Learning algorithm
    '''
    def train(self):
        self.__update_replay_memory(transition=(self.current_state, self.action, self.reward, self.new_state))

        if len(self.replay_memory) < self.min_rep_mem_total:
            return
        if len(self.replay_memory) > self.max_cases:
            # delete leftovers 
            self.replay_memory = deque(itertools.islice(self.replay_memory, self.cases_to_delete, None))

        self.min_rep_mem_total += self.min_rep_mem_size

        minibatch = random.sample(self.replay_memory, self.minibatch_size)
        
        good = [x for x in self.replay_memory if x[2] not in [0]]
        minibatch += good
        self.replay_memory = [x for x in self.replay_memory if x not in good]

        current_states = np.array([transition[0] for transition in minibatch])
        current_qs_list = self.model.predict(current_states)

        new_current_states = np.array([transition[3] for transition in minibatch])
        future_qs_list = self.target_model.predict(new_current_states)

        X = [] # feature sets   /  images
        y = [] # labels         /  actions

        # current_states get from index 0 so current_state has to be in 0 position
        # same with new_current_state
        ## ALGORITHM
        for index, (current_state, action, reward, new_current_state) in enumerate(minibatch):
            max_future_q = np.max(future_qs_list[index])
            new_q = reward + self.discount * max_future_q

            current_qs = current_qs_list[index]
            current_qs[action] = new_q

            X.append(current_state)
            y.append(current_qs)



        self.model.fit(np.array(X), np.array(y), batch_size=self.min_rep_mem_size, verbose=0, 
            shuffle=False)

        #updating to determinate if we want to update target_model yet
        self.target_update_counter += 1

        # copy weights from the main network to target network
        if self.target_update_counter > self.update_time:
            self.target_model.set_weights(self.model.get_weights())
            self.target_update_counter = 0
        
    '''
        Save models to specify file
    '''              
    def save(self, filepath):
        keras.models.save_model(self.model, os.getcwd() + filepath + '.h5')

    '''
        Load models from specify file
    '''        
    def load(self, filepath):
        self.model = keras.models.load_model(os.getcwd() + filepath + '.h5')
        self.target_model = keras.models.load_model(os.getcwd() + filepath + '.h5')

    '''
        (Protected method)
        Return action with maxium reward
    '''
    def _get_max_action(self, env):
        cases = self.__get_qs(self.current_state)
        self.action = np.argmax(cases)
        env.get_action(action=self.action)
        
        print("Estado: ", self.current_state)
        print("Casos: ", cases)
        print("---")

    '''
        (Protected method)
        Choose action for current state.
        This action could be random or the one with maxium reward, depending on epsilon value.
    '''
    def _choose_action(self, env):
        if np.random.rand() > self.epsilon:
            self.action = np.random.choice(self.actions)
            env.get_action(action=self.action)
        else:
            self._get_max_action(env=env)
    
    '''
        (Private method)
        Create target model and network model with specify characteristics
    '''
    def __create_model(self, num_states, hidden_nodes = 25, hidden_layers = 1):
        # layers
        inputs = Input(shape=(num_states,))
        x = Dense(hidden_nodes, activation='relu')(inputs)
        for i in range(1, hidden_layers):
            x = Dense(hidden_nodes + (20 * i), activation='relu')(x)
        outputs = Dense(len(self.actions))(x)

        # creation
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(loss="mse", optimizer='adam', metrics=['accuracy'])
    
        model.summary()
        return model

    '''
        (Private method)
        Update replay memory with our observation space
    '''
    def __update_replay_memory(self, transition):
        # transition -> our observation space
        self.replay_memory.append(transition)

    '''
        (Private method)
        Predict current state
    '''
    def __get_qs(self, state):
        # return last layer of neural network
        stateArray = np.array(self.current_state)
        return self.model.predict(stateArray.reshape(-1, *stateArray.shape))[0]

    '''
        (Private method)
        Update epsilon value
    '''
    def __set_epsilon(self, episode):
        self.epsilon = (episode / (self.total_episodes - (self.total_episodes / 3)))