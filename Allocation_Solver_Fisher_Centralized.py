import copy

from Allocation_Solver_Abstract import AllocationSolver
from Simulation import TaskSimple, PlayerSimple


class FisherCentralizedImplementation:
    def __init__(self, utilities):
        self.NCLO = 0
        self.counter = 0
        self.change = 0
        self.THRESHOLD = 1E-8

        self.nofGoods = len(utilities[0])
        self.nofAgents = len(utilities)
        self.utilities_ = [[None for _ in range(self.nofGoods)] for _ in
                           range(self.nofAgents)]  # utilities of buyers over the goods

        self.bids = [[0 for _ in range(self.nofGoods)] for _ in range(self.nofAgents)]  # buyers bids over the goods
        self.prices = [0 for _ in range(self.nofGoods)]  # prices of the goods in the market
        valuation_sums = [0 for _ in range(self.nofAgents)]
        for i in range(self.nofAgents):
            for j in range(self.nofGoods):
                if utilities[i][j] is not None:
                    self.utilities_[i][j] = utilities[i][j]
                    valuation_sums[i] += utilities[i][j].getUtility(1)
                    NCLO = NCLO+1
            for j in range(self.nofGoods):
                if utilities[i][j] is not None:
                    self.bids[i][j] = utilities[i][j].getUtility(1) / valuation_sums[i]
                    NCLO = NCLO+1

        self.generateAllocations()

    # generates allocation according to current bids and prices
    def generateAllocations(self):
        self.calculate_prices()
        self.calculate_x_ij()

    def calculate_x_ij(self):
        self.change = 0
        for i in range(self.nofAgents):
            for j in range(self.nofGoods):
                if self.prices[j] != 0:
                    self.change += abs(((self.bids[i][j] / self.prices[j]) - self.utilities_[i][j].xij))
                    if self.bids[i][j] / self.prices[j] > 1E-10:
                        self.utilities_[i][j].xij = self.bids[i][j] / self.prices[j]
                        self.NCLO = self.NCLO + 1

        # self.print()

    def calculate_prices_initial(self):
        for j in range(self.nofGoods):
            self.prices[j] = 0
            for i in range(self.nofAgents):
                NCLO = NCLO + 1
                self.prices[j] += self.bids[i][j]

    def print_xij(self):
        print()
        print("------Matrix X------")

        for i in range(self.nofAgents):
            print()
            for j in range(self.nofGoods):
                if j == 0:
                    print("Agent id_", self.utilities_[i][j].agent.agent_id_, end=":  ")

                if self.utilities_[i][j].xij is not None and self.utilities_[i][j].xij > 0.0000001:
                    if self.utilities_[i][j].xij > 0.99:
                        print("1.00000", end="\t")
                    if self.utilities_[i][j].xij == 0:
                        print("0.00000", end="\t")
                    else:
                        print(round(self.utilities_[i][j].xij, ndigits=5), end="\t")
                else:
                    print("0.00000", end="\t")
        print()

    def iterate(self):
        utilities = [[0 for _ in range(self.nofGoods)] for _ in
                     range(self.nofAgents)]
        # calculate current utilities and sum the utility for each agent
        utilitySum = [0 for _ in range(self.nofAgents)]
        self.calculate_sum_r_i(utilities,utilitySum)
        self.calculate_bids(utilities,utilitySum)

        self.generateAllocations()

    def calculate_sum_r_i(self, utilities, utilitySum):

        for i in range(self.nofAgents):
            for j in range(self.nofGoods):
                if self.utilities_[i][j].xij is not None:
                    utilities[i][j] = self.utilities_[i][j].getUtility(self.utilities_[i][j].xij)
                    utilitySum[i] += utilities[i][j]
                    self.NCLO += 1

    def calculate_bids(self,utilities,utilitySum):
        for i in range(self.nofAgents):
            for j in range(self.nofGoods):
                calc_bid = utilities[i][j] / utilitySum[i]
                self.NCLO+=1
                flag = False
                if calc_bid < 0.0001:
                    self.bids[i][j] = 0
                    flag = True
                if calc_bid > 0.9999:
                    self.bids[i][j] = 1
                    flag = True
                if not flag:
                    self.bids[i][j] = calc_bid


    # algorithm

    def algorithm(self):
        self.iterate()
        while self.isStable() is False:
            self.iterate()
        self.fix_xij()
        return

    def isStable(self):
        self.counter = self.counter + 1
        if self.counter > 5000:
            return True
        # print("change", self.change)
        return self.change < self.THRESHOLD

    def fix_xij(self):
        for i in range(len(self.utilities_)):
            for j in range(len(self.utilities_[i])):
                util = self.utilities_[i][j]
                if util.xij<0.05:
                    util.xij = 0


class AllocationSolverFisherCentralized (AllocationSolver):
    def __init__(self, tasks_simulation=[], players_simulation=[]):
        AllocationSolver.__init__(tasks_simulation,players_simulation)

        self.dict_ptmu = {}

    def allocate(self):
        self.reset_dict()

    def reset_dict(self):
        for player in self.players_simulation:
            self.dict_ptmu = {}
            for task in self.tasks_simulation:
                self.dict_ptmu[task] = {}
                for mission in task.missions:

    def add_player_to_solver(self, player: PlayerSimple):
        self.players_simulation.append(player)
        self.what_solver_does_when_player_is_added(player)

    def remove_player_from_solver(self, player: PlayerSimple):
        self.players_simulation.remove(player)
        self.what_solver_does_when_player_is_removed(player)

    def add_task_to_solver(self, task: TaskSimple):
        self.tasks_simulation.append(task)
        self.what_solver_does_when_task_is_added(task)

    def remove_task_from_solver(self, task: TaskSimple):
        self.tasks_simulation.remove(task)
        self.what_solver_does_when_task_is_removed(task)




