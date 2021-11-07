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