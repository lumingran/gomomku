# -*- coding: utf-8 -*-

from __future__ import print_function
import theano
import theano.tensor as T
import lasagne
import pickle


class PolicyValueNet():
    def __init__(self, board_width, board_height, model_file=None):
        self.board_width = board_width
        self.board_height = board_height
        self.learning_rate = T.scalar('learning_rate')
        self.l2_const = 1e-4
        self.create_policy_value_net()
        self._loss_train_op()
        if model_file:
            try:
                net_params = pickle.load(open(model_file, 'rb'))
            except:
                net_params = pickle.load(open(model_file, 'rb'),
                                         encoding='bytes')
            lasagne.layers.set_all_param_values(
                    [self.policy_net, self.value_net], net_params
                    )

    def create_policy_value_net(self):
        self.state_input = T.tensor4('state')
        self.winner = T.vector('winner')
        self.mcts_probs = T.matrix('mcts_probs')
        network = lasagne.layers.InputLayer(
                shape=(None, 4, self.board_width, self.board_height),
                input_var=self.state_input
                )
        network = lasagne.layers.Conv2DLayer(
                network, num_filters=32, filter_size=(3, 3), pad='same')
        network = lasagne.layers.Conv2DLayer(
                network, num_filters=64, filter_size=(3, 3), pad='same')
        network = lasagne.layers.Conv2DLayer(
                network, num_filters=128, filter_size=(3, 3), pad='same')
        policy_net = lasagne.layers.Conv2DLayer(
                network, num_filters=4, filter_size=(1, 1))
        self.policy_net = lasagne.layers.DenseLayer(
                policy_net, num_units=self.board_width*self.board_height,
                nonlinearity=lasagne.nonlinearities.softmax)
        value_net = lasagne.layers.Conv2DLayer(
                network, num_filters=2, filter_size=(1, 1))
        value_net = lasagne.layers.DenseLayer(value_net, num_units=64)
        self.value_net = lasagne.layers.DenseLayer(
                value_net, num_units=1,
                nonlinearity=lasagne.nonlinearities.tanh)
        self.action_probs, self.value = lasagne.layers.get_output(
                [self.policy_net, self.value_net])
        self.policy_value = theano.function([self.state_input],
                                            [self.action_probs, self.value],
                                            allow_input_downcast=True)

    def policy_value_fn(self, board):
        legal_positions = board.availables
        current_state = board.current_state()
        act_probs, value = self.policy_value(
            current_state.reshape(-1, 4, self.board_width, self.board_height)
            )
        act_probs = zip(legal_positions, act_probs.flatten()[legal_positions])
        return act_probs, value[0][0]

    def _loss_train_op(self):
        params = lasagne.layers.get_all_params(
                [self.policy_net, self.value_net], trainable=True)
        value_loss = lasagne.objectives.squared_error(
                self.winner, self.value.flatten())
        policy_loss = lasagne.objectives.categorical_crossentropy(
                self.action_probs, self.mcts_probs)
        l2_penalty = lasagne.regularization.apply_penalty(
                params, lasagne.regularization.l2)
        self.loss = self.l2_const*l2_penalty + lasagne.objectives.aggregate(
                value_loss + policy_loss, mode='mean')
        self.entropy = -T.mean(T.sum(
                self.action_probs * T.log(self.action_probs + 1e-10), axis=1))
        updates = lasagne.updates.adam(self.loss, params,
                                       learning_rate=self.learning_rate)
        self.train_step = theano.function(
            [self.state_input, self.mcts_probs, self.winner, self.learning_rate],
            [self.loss, self.entropy],
            updates=updates,
            allow_input_downcast=True
            )

    def get_policy_param(self):
        net_params = lasagne.layers.get_all_param_values(
                [self.policy_net, self.value_net])
        return net_params

    def save_model(self, model_file):
        net_params = self.get_policy_param()
        pickle.dump(net_params, open(model_file, 'wb'), protocol=2)
