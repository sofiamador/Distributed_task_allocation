import math
import random

import Simulation


class CommunicationProtocol:
    def __init__(self,is_with_timestamp,name):

        self.name = name
        self.is_with_timestamp = is_with_timestamp
        self.rnd  = None

    def __str__(self):
        return self.name

    def set_seed(self,seed):
        self.rnd = random.Random(seed)

    def get_communication_disturbance(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        return 0

class CommunicationProtocolUniform(CommunicationProtocol):
    def __init__(self,is_with_timestamp,name,UB):
        CommunicationProtocol.__init__(self,is_with_timestamp,name)
        self.UB = UB

    def get_communication_disturbance(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        if self.UB == 0:
            return 0
        return self.rnd.uniform(0, self.UB)

class CommunicationProtocolDistanceBase(CommunicationProtocol):
    def __init__(self, is_with_timestamp, name, length,width):
        CommunicationProtocol.__init__(self, is_with_timestamp, name)
        self.max_distance = math.sqrt(length**2+width**2)

    def get_communication_disturbance(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        pass

    def calculate_ratio(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        l1,l2 = self.get_who_is_who_location(entity1,entity2)

        delta_x_square = (l1[0]-l2[0])**2
        delta_y_square = (l1[1]-l2[1])**2
        quad_distance = math.sqrt(delta_x_square+delta_y_square)
        return  quad_distance/self.max_distance

    def get_who_is_who_location(self, entity1, entity2):
        if isinstance(entity1, Simulation.PlayerSimple) and isinstance(entity2, Simulation.PlayerSimple):
            return entity1.location,entity2.location
        if isinstance(entity1, Simulation.TaskSimple) and isinstance(entity2, Simulation.PlayerSimple):
            l1 = self.get_location_of_responsible_player(entity1)
            return l1,entity2.location

        if isinstance(entity1, Simulation.PlayerSimple) and isinstance(entity2, Simulation.TaskSimple):
            l2 = self.get_location_of_responsible_player(entity2)
            return entity1.location, l2

        if isinstance(entity1, Simulation.TaskSimple) and isinstance(entity2, Simulation.TaskSimple):
            l1 = self.get_location_of_responsible_player(entity1)
            l2 = self.get_location_of_responsible_player(entity2)
            return l1, l2

    def get_location_of_responsible_player(self, entity:Simulation.TaskSimple):
        if isinstance(entity, Simulation.TaskSimple):
            return entity.player_responsible.location
        else:
            raise Exception("only tasks have responsible players")


class CommunicationProtocolDistanceBaseDelayPois(CommunicationProtocolDistanceBase):
    def __init__(self, is_with_timestamp, name, length,width,param):
        CommunicationProtocolDistanceBase.__init__(self, is_with_timestamp, name,length,width)
        self.param = param

    def get_communication_disturbance(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        ratio = self.calculate_ratio(self, entity1, entity2)
        #TODO

class CommunicationProtocolDistanceBaseMessageLoss(CommunicationProtocolDistanceBase):
    def __init__(self, is_with_timestamp, name, length,width,param):
        CommunicationProtocolDistanceBase.__init__(self, is_with_timestamp, name,length,width)
        self.param = param

    def get_communication_disturbance(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        P = self.calculate_ratio(self, entity1, entity2)
        p = self.rnd.random()
        if(p<P):
            return None
        else:
            return 0


class CommunicationProtocolDistanceBaseDelayPoisAndLoss(CommunicationProtocolDistanceBase):
    def __init__(self, is_with_timestamp, name, length,width,param):
        CommunicationProtocolDistanceBase.__init__(self, is_with_timestamp, name,length,width)
        self.param = param

    def get_communication_disturbance(self, entity1: Simulation.Entity, entity2: Simulation.Entity):
        P = self.calculate_ratio(self, entity1, entity2)
        p = self.rnd.random()
        if (p < P):
            return None
        else:
            return #TODO