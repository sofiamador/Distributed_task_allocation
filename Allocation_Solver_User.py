import Allocation_Solver_Abstract


class Allocation_Solver_FMC_TA_distributed(Allocation_Solver_Abstract.Allocation_Solver_Distributed_V1):
    def __init__(self):
        ttt = self.get_delay_function()
        print(ttt)

    def create_graphs(self, missions_simulation, agents_simulation):
        raise NotImplementedError

    def get_agent_algorithm(self, a_simulation):
        raise NotImplementedError

    def get_mission_algorithm(self, m_simulation):
        raise NotImplementedError

    def get_delay_function(self):
        return 0
