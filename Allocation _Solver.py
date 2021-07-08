

import threading
from enum import Enum

class Enum_Mailer(Enum):
    Central_Task_Awareness = 1
    Chain_Task_Awareness = 2

class Enum_Algorithm(Enum):
    FMC_TA_distributed = 1

class Algorithm_Info():
    def __init__(self, is_distributed, algo_enum, graph_creator):
        self.algo_enum = algo_enum
        self.is_distributed = is_distributed
        if self.is_distributed:
            self.graph_creator_function = graph_creator


class Allocation_Solver():
    def __init__(self,missions_simulation, agents_simulation, algorithm_info):
       pass


class Allocation_Solver_Distributed(Allocation_Solver):
    def __init__(self, missions_simulation, agents_simulation, algorithm_info, mailer_type):
        Allocation_Solver.__init__(missions_simulation,agents_simulation,algorithm_info)

        self.missions_algorithm = None
        self.create_missions_algorithm(missions_simulation, algorithm_info.algo_enum)

        self.agents_algorithm = None
        self.create_agents_algorithm(agents_simulation,  algorithm_info.algo_enum)

        algorithm_info.graph_creator_function(self.missions_algorithm,self.agents_algorithm)  # creates neighborhood

        self.mailer = None
        self.create_mailer(mailer_type)

    def create_missions_algorithm(self, missions_simulation, algo_enum):
        for m_simulation in missions_simulation:
            m_algorithm = None
            if algo_enum == algo_enum.FMC_TA_distributed:
                m_algorithm = Mission_FMC_TA_DISTRIBUTED(m_simulation) # TODO create class Mission_FMC_TA_DISTRIBUTED
            self.missions_algorithm.append(m_algorithm)

    def create_agents_algorithm(self, agents_simulation, algo_enum):
        for a_simulation in agents_simulation:
            a_algorithm = None
            if algo_enum == algo_enum.FMC_TA_distributed:
                a_algorithm = Agent_FMC_TA_DISTRIBUTED(a_simulation)  # TODO create class Agent_FMC_TA_DISTRIBUTED
            self.agents_algorithm .append(a_algorithm)

    def create_mailer(self,mailer_type):
        if mailer_type == Enum_Mailer.Central_Task_Awareness:
            self.mailer = MailerCental() # TODO create class MailerCental
        if mailer_type == Enum_Mailer.Chain_Task_Awareness:
            self.mailer = MailerChain() # TODO create class MailerChain



class Agent_Algorithm(threading.Thread):
    def __init__(self,agent_simulator):
        self.agent_simulator = agent_simulator

    def run(self) -> None:
        self.set_is_idle_to_true()#TODO




mailer_counter = 0
class Mailer(threading.Thread):
    def __init__(self):
        global mailer_counter
        mailer_counter =  mailer_counter+1
        self.id_ = mailer_counter
        #self.protocol = protocol # delay and msg loss
        self.protocol.set_seed()

