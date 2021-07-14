
import threading
from enum import Enum


class Allocation_Solver():
    def __init__(self):
       pass

    def solve(self, missions_simulation, agents_simulation):
        raise  NotImplementedError


class Allocation_Solver_Distributed_V1(Allocation_Solver):
    def __init__(self, missions_simulation, agents_simulation):
        Allocation_Solver.__init__()

    def solve(self, missions_simulation, agents_simulation):
        self.create_graphs(missions_simulation, agents_simulation)
        delay_function = self.get_delay_function()

        agents_algorithm = self.create_agents_algorithm(agents_simulation)
        missions_algorithm = self.create_missions_algorithm(missions_simulation)
        self.match_agent_mission_responsibility(missions_simulation, agents_simulation)

        if missions_algorithm is not None:
            malier = Mailer(delay_function, agents_algorithm, missions_algorithm)
        else:
            mailer = Mailer(delay_function, agents_algorithm)


    def get_delay_function(self):
        return 0

    def create_graphs(self, missions_simulation, agents_simulation):
        raise NotImplementedError

    def get_agent_algorithm(self, a_simulation):
        raise NotImplementedError

    def get_mission_algorithm(self, m_simulation):
        raise NotImplementedError

    def match_agent_mission_responsibility(self, missions_simulation, agents_simulation):
        raise NotImplementedError

    def create_agents_algorithm(self, agents_simulation):
        ans = []
        for a_simulation in agents_simulation:
            ans.append(self.get_agent_algorithm(a_simulation))
        return ans


    def create_missions_algorithm(self, missions_simulation):
        ans = []
        for m_simulation in missions_simulation:
            a_algorithm = self.get_mission_algorithm(m_simulation)
            ans.append(self.get_mission_algorithm(a_algorithm))
        return ans




mailer_counter = 0
class Mailer(threading.Thread):
    def __init__(self ,delay_function, agents_algorithm ,missions_algorithm=None):
        global mailer_counter
        mailer_counter =  mailer_counte r +1
        self.id_ = mailer_counter
        self.delay_function = delay_function
        self.protocol.set_seed()


        for aa in agents_algorithm:
            aa.start()





class Agent_Algorithm(threading.Thread):
    def __init__(self ,agent_simulator):
        self.agent_simulator = agent_simulator

    def run(self) -> None:
        self.set_is_idle_to_true(  )  # TODO


print(
3)