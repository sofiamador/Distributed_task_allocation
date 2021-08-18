from Allocation_Solver_Abstract import AllocationSolverDistributed
from Allocation_Solver_Abstract import AgentAlgorithm


def calculate_distance(entity1: Entity, entity2: Entity):
    """
    Calculates the distance between two entities. Each entity must have a location property.
    :param entity1:first entity
    :param entity2:second entity
    :return: Euclidean distance between two entities
    :rtype: float
    """
    distance = 0
    n = min(len(entity1.location, len(entity2.location)))
    for i in range(n):
        distance += (entity1.location[i] - entity2.location[i]) ** 2
    return distance ** 0.5


class FisherPlayerPhaseI(AgentAlgorithm):
    def __init__(self, agent_simulator):
        AgentAlgorithm.__init(self, agent_simulator)


class FisherMissionPhaseI(AgentAlgorithm):
    def __init__(self, events_simulator):
        AgentAlgorithm.__init(self, events_simulator)


class AllocationSolverDistributedFisher(AllocationSolverDistributed):
    def __init__(self, mailer=None):
        AllocationSolverDistributed.__init__(self, mailer)
        self.algorithm_players = []
        self.algorithm_events = []

    def create_graphs(self):
        self.connect_agents()
        dict_event_player_responsibility = self.distribute_agents_responsibilities_on_agents()

    def distribute_agents_responsibilities_on_agents(self):
        ans = {}
        for e in self.events_simulation:
            agent_min_distance_to_event = self.get_agent_min_distance_to_event(event=e)
            algorithm_players_at_min_distance = self.get_algorithm_players_at_min_distance(agent_min_distance_to_event=agent_min_distance_to_event, event=e)
            single_player_with_smallest_responsibilities= self.get_single_player_with_smallest_responsibilities(ans, algorithm_players_at_min_distance)
        return ans

    def get_single_player_with_smallest_responsibilities(self,dict_of_respons , algorithm_players):
       selected_ap = None
       min_reprs = 0
       flag = False

       for ap in algorithm_players:
           if not flag:
               flag = True
               selected_ap = ap
                see

    def get_algorithm_players_at_min_distance(self,agent_min_distance_to_event,event ):
        ans = []
        for ap in self.algorithm_players:
            if calculate_distance(event, ap.simulation_entity) == agent_min_distance_to_event:
                ans.append(ap)
        return  ans

    def get_agent_min_distance_to_event(self, event):
        list_of_distances = []
        for pa in self.algorithm_players:
            list_of_distances = list_of_distances + calculate_distance(event, pa.simulation_entity)
        return min(list_of_distances)

    def connect_agents(self):
        for e in self.events_simulation:
            list_of_agents_that_can_be_allocated = e.neighbours
            for ap in self.algorithm_players:
                agent_simulation = ap.simulation_entity
                if agent_simulation in list_of_agents_that_can_be_allocated:
                    e.add_neighbour_id(agent_simulation.id_)
                    ap.add_neighbour_id(e.id_)
                    ap.add_to_event_domain(e)

    def create_agents_algorithm(self):
        ans = []
        for agent_sim in self.agents_simulation:
            agent_algo = FisherPlayerPhaseI(agent_sim)
            ans.append(agent_algo)
            self.algorithm_players.append(agent_algo)

        for events_sim in self.events_simulation:
            event_algo = FisherMissionPhaseI(events_sim)
            ans.append(event_algo)
            self.algorithm_events.append(event_algo)
