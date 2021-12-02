import abc
import math
import random
from abc import ABC

import Simulation

import numpy as np

debug_print_for_distribution = False
class CommunicationProtocol(ABC):
    def __init__(self, is_with_timestamp, name):

        self.name = name
        self.is_with_timestamp = is_with_timestamp
        self.rnd = None
        self.rnd_numpy = None

    def __str__(self):
        return self.name

    def set_seed(self, seed):
        self.rnd = random.Random(seed)
        self.rnd_numpy = np.random.default_rng(seed=seed)

    def get_communication_disturbance(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        if isinstance(entity1, Simulation.TaskSimple) and isinstance(entity2, Simulation.PlayerSimple):
            if entity1.player_responsible.id_ == entity2.id_:
                return 0

        if isinstance(entity2, Simulation.TaskSimple) and isinstance(entity1, Simulation.PlayerSimple):
            if entity2.player_responsible.id_ == entity1.id_:
                return 0

        return self.get_communication_disturbance_by_protocol(entity1, entity2)

    @abc.abstractmethod
    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        raise NotImplementedError


class CommunicationProtocolDefault(CommunicationProtocol):
    def __init__(self, name, is_with_timestamp=False):
        CommunicationProtocol.__init__(self, is_with_timestamp, name)

    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        return 0


class CommunicationProtocolUniform(CommunicationProtocol):
    def __init__(self, is_with_timestamp, name, UB):
        CommunicationProtocol.__init__(self, is_with_timestamp, name)
        self.UB = UB

    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        if self.UB == 0:
            return 0
        return self.rnd.uniform(0, self.UB)

class CommunicationProtocolPois(CommunicationProtocol):
    def __init__(self, is_with_timestamp, name, lambda_):
        CommunicationProtocol.__init__(self, is_with_timestamp, name)
        self.lambda_ = lambda_

    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        if self.lambda_ == 0:
            return 0

        delay = self.rnd_numpy.poisson(self.lambda_)
        if debug_print_for_distribution:
            print(delay)
        return delay


class CommunicationProtocolExp(CommunicationProtocol):
    def __init__(self, is_with_timestamp, name, lambda_):
        CommunicationProtocol.__init__(self, is_with_timestamp, name)
        self.lambda_ = lambda_

    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        if self.lambda_ == 0:
            return 0

        delay = self.rnd_numpy.exponential(scale=self.lambda_, size=1)[0]
        if debug_print_for_distribution:
            print(delay)
        return delay


class CommunicationProtocolDistanceBase(CommunicationProtocol, ABC):
    def __init__(self, is_with_timestamp, name, length, width):
        CommunicationProtocol.__init__(self, is_with_timestamp, name)
        self.max_distance = math.sqrt(length ** 2 + width ** 2)

    def calculate_ratio(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        l1, l2 = self.get_who_is_who_location(entity1, entity2)

        delta_x_square = (l1[0] - l2[0]) ** 2
        delta_y_square = (l1[1] - l2[1]) ** 2
        quad_distance = math.sqrt(delta_x_square + delta_y_square)
        return quad_distance / self.max_distance

    def get_who_is_who_location(self, entity1, entity2):
        if isinstance(entity1, Simulation.PlayerSimple) and isinstance(entity2, Simulation.PlayerSimple):
            return entity1.location, entity2.location

        if isinstance(entity1, Simulation.TaskSimple) and isinstance(entity2, Simulation.PlayerSimple):
            if entity1.player_responsible.id_ == entity2.id_:
                return 0

            l1 = self.get_location_of_responsible_player(entity1)
            return l1, entity2.location

        if isinstance(entity1, Simulation.PlayerSimple) and isinstance(entity2, Simulation.TaskSimple):
            if entity2.player_responsible.id_ == entity1.id_:
                return 0

            l2 = self.get_location_of_responsible_player(entity2)
            return entity1.location, l2

        if isinstance(entity1, Simulation.TaskSimple) and isinstance(entity2, Simulation.TaskSimple):
            l1 = self.get_location_of_responsible_player(entity1)
            l2 = self.get_location_of_responsible_player(entity2)
            return l1, l2

    def get_location_of_responsible_player(self, entity: Simulation.TaskSimple):
        if isinstance(entity, Simulation.TaskSimple):
            return entity.player_responsible.location
        else:
            raise Exception("only tasks have responsible players")


class CommunicationProtocolDistanceBaseDelayPois(CommunicationProtocolDistanceBase):
    def __init__(self, is_with_timestamp, name, length, width, constant_):
        CommunicationProtocolDistanceBase.__init__(self, is_with_timestamp, name, length, width)
        self.constant_ = constant_

    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        ratio = self.calculate_ratio(entity1, entity2)
        param = ratio * self.constant_
        delay = self.rnd_numpy.poisson(param, 1)[0]
        if debug_print_for_distribution:
            print(delay)
        return delay


class CommunicationProtocolDistanceBaseDelayExp(CommunicationProtocolDistanceBase):
    def __init__(self, is_with_timestamp, name, length, width, constant_):
        CommunicationProtocolDistanceBase.__init__(self, is_with_timestamp, name, length, width)
        self.constant_ = constant_

    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        ratio = self.calculate_ratio(entity1, entity2)
        param = ratio * self.constant_
        #delay = self.rnd_numpy.poisson(param, 1)[0]
        delay = self.rnd_numpy.exponential(scale=param, size=1)[0]
        if debug_print_for_distribution:
            print(delay)
        return delay


class CommunicationProtocolDistanceBaseMessageLoss(CommunicationProtocolDistanceBase):
    def __init__(self, is_with_timestamp, name, length, width,distance_loss_ratio):
        CommunicationProtocolDistanceBase.__init__(self, is_with_timestamp, name, length, width)
        self.max_distance = self.max_distance*distance_loss_ratio



    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        P = self.calculate_ratio(entity1, entity2)
        p = self.rnd.random()
        if debug_print_for_distribution:
            if p < P:
                print(1)
            else:
                print(0)

        if p < P:
            return None
        else:
            return 0


class CommunicationProtocolDistanceBaseDelayPoisAndLoss(CommunicationProtocolDistanceBase):
    def __init__(self, is_with_timestamp, name, length, width, constant_):
        CommunicationProtocolDistanceBase.__init__(self, is_with_timestamp, name, length, width)
        self.constant_ = constant_

    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        ratio = self.calculate_ratio(entity1, entity2)
        p = self.rnd.random()
        if p < ratio:
            return None
        else:
            param = ratio * self.constant_
            return self.rnd_numpy.poisson(param, 1)[0]


class CommunicationProtocolMessageLossConstant(CommunicationProtocol):
    def __init__(self, name, is_with_timestamp, p_loss):
        CommunicationProtocol.__init__(self, is_with_timestamp, name)
        self.p_loss = p_loss

    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        p = self.rnd.random()
        if p < self.p_loss:
            return None
        else:
            return 0


class CommunicationProtocolMessageLossConstantAndUniform(CommunicationProtocol):
    def __init__(self, name, is_with_timestamp, p_loss,UB):
        CommunicationProtocol.__init__(self, is_with_timestamp, name)
        self.p_loss = p_loss
        self.UB = UB

    def get_communication_disturbance_by_protocol(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        p = self.rnd.random()
        if p < self.p_loss:
            return None
        else:
            return self.rnd.uniform(0, self.UB)
