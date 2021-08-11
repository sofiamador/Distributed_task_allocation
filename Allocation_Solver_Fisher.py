import Allocation_Solver_Abstract

class AllocationSolverDistributedFisher(Allocation_Solver_Abstract.AllocationSolverDistributed):
    def __init__(self, mailer=None):
        Allocation_Solver_Abstract.AllocationSolverDistributed.__init__(missions_simulation, agents_simulation, mailer)

    def solve(self, missions_simulation, agents_simulation, mailer=None) -> {}:
        self.missions_simulation = missions_simulation
        self.agents_simulation = agents_simulation
        self.mailer = mailer
        self.allocate()


a = AllocationSolverDistributedFisher([], [], [])
