
from Allocation_Solver_Abstract import PlayerAlgorithm
from Simulation import Entity, TaskSimple


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


class FisherPlayer(PlayerAlgorithm):
    def __init__(self, agent_simulator):
        PlayerAlgorithm.__init__(self, agent_simulator)
        r_i = {}

    def add_task_entity_to_log(self, task_entity: TaskSimple):
        super().add_task_entity_to_log(task_entity)
        rij #STOPPED HERE NEED TO CALCULATE RIJ WHEN RECIEVE TASK ENTITY TO LOG
    def initiate_algorithm(self):
        #TODO
        pass

    def measurements_per_agent(self):
        # TODO
        pass

    def set_receive_flag_to_true_given_msg(self, msg):
        # TODO
        pass

    def get_current_timestamp_from_context(self, msg):
        # TODO
        pass

    def update_message_in_context(self, msg):
        # TODO
        pass

    def get_current_timestamp_from_context(self, msg):
        # TODO
        pass

    def update_message_in_context(self, msg):
        # TODO
        pass

    def get_is_going_to_compute_flag(self):
        # TODO
        pass

    def compute(self):
        # TODO
        pass

    def get_list_of_msgs(self):
        # TODO
        pass

    def set_receive_flag_to_false(self):
        # TODO
        pass


class FisherTaskPhaseI(AgentAlgorithm):
    def __init__(self, tasks_simulator):
        AgentAlgorithm.__init(self, tasks_simulator)

    def measurements_per_agent(self):
        # TODO

        """
        NotImplementedError
        :return: dict with key: str of measure, value: the calculated measure
        """

        raise NotImplementedError

    def set_receive_flag_to_true_given_msg(self, msg):
        # TODO
        """
        given msgs received is agent going to compute in this iteration?
        set the relevant computation flag
        :param msg:
        :return:

        """

        raise NotImplementedError

    def get_current_timestamp_from_context(self, msg):
        # TODO
        """
        :param msg: use it to extract the current timestamp from the receiver
        :return: the timestamp from the msg

        """

        return -1

    def update_message_in_context(self, msg):
        # TODO
        '''
        :param msg: msg to update in agents memory
        :return:
        '''

        raise NotImplementedError

    def get_is_going_to_compute_flag(self):
        # TODO
        """
        :return: the flag which determines if computation is going to occur
        """
        raise NotImplementedError

    def compute(self):
        # TODO
        """
       After the context was updated by messages received, computation takes place
       using the new information and preparation on context to be sent takes place
        """
        raise NotImplementedError

    def get_list_of_msgs(self):
        # TODO
        """
        create and return list of msgs
        """
        raise NotImplementedError

    def set_receive_flag_to_false(self):
        # TODO
        """
        after computation occurs set the flag back to false
        :return:
        """
        raise NotImplementedError



class AllocationSolverDistributedFisher(AllocationSolverDistributed):
    def __init__(self, mailer=None):
        AllocationSolverDistributed.__init__(self, mailer)
        


    def create_agents_algorithm(self):
        ans = []
        for agent_sim in self.agents_simulation:
            agent_algo = FisherPlayerPhaseI(agent_sim)
            ans.append(agent_algo)
            self.algorithm_players.append(agent_algo)

        for task_sim in self.tasks_simulation:
            task_algo = FisherTaskPhaseI(task_sim)
            ans.append(task_algo)
            self.algorithm_tasks.append(task_algo)

    def connect_task_agent_timeObject(self):
        for agent_algo


    # def create_graphs(self):
    #     for e in self.algorithm_tasks:
    #         list_of_agents_that_can_be_allocated = e.neighbours
    #         for ap in self.algorithm_players:
    #             agent_simulation = ap.simulation_entity
    #             if agent_simulation in list_of_agents_that_can_be_allocated:
    #                 e.add_neighbour_id(agent_simulation.id_)
    #                 ap.add_neighbour_id(e.id_)
    #                 ap.add_to_event_domain(e)
        #dict_event_player_responsibility = self.distribute_agents_responsibilities_on_agents()

    # def distribute_agents_responsibilities_on_agents(self):
    #     ans = {}
    #     for e in self.events_simulation:
    #         agent_min_distance_to_event = self.get_agent_min_distance_to_event(event=e)
    #         algorithm_players_at_min_distance = self.get_algorithm_players_at_min_distance(agent_min_distance_to_event=agent_min_distance_to_event, event=e)
    #         single_player_with_smallest_responsibilities= self.get_single_player_with_smallest_responsibilities(ans, algorithm_players_at_min_distance)
    #     return ans

    # def get_single_player_with_smallest_responsibilities(self,dict_of_respons , algorithm_players):
    #    selected_ap = None
    #    min_reprs = 0
    #    flag = False
    #
    #    for ap in algorithm_players:
    #        if not flag:
    #            flag = True
    #            selected_ap = ap
    #             see
    #
    # def get_algorithm_players_at_min_distance(self,agent_min_distance_to_event,event ):
    #     ans = []
    #     for ap in self.algorithm_players:
    #         if calculate_distance(event, ap.simulation_entity) == agent_min_distance_to_event:
    #             ans.append(ap)
    #     return  ans
    #
    # def get_agent_min_distance_to_event(self, event):
    #     list_of_distances = []
    #     for pa in self.algorithm_players:
    #         list_of_distances = list_of_distances + calculate_distance(event, pa.simulation_entity)
    #     return min(list_of_distances)



