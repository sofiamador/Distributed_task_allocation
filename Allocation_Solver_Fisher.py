from abc import ABC

from Allocation_Solver_Abstract import PlayerAlgorithm
from Simulation import Entity, TaskSimple, future_utility


class Utility:
    def __init__(self, player_entity, mission_entity, task_entity, t_now, ro=1, util=-1):
        self.player_entity = player_entity
        self.mission_entity = mission_entity
        self.task_entity = task_entity
        self.t_now = t_now
        self.ro = ro
        if util == -1:
            self.linear_utility = future_utility(player_entity=self.player_entity,
                                                 mission_entity=self.mission_entity, task_entity=self.task_entity,
                                                 t_now=self.t_now)
        else:
            self.linear_utility = util

    def get_linear_utility(self):
        return self.linear_utility

    def get_utilility(self, ratio=1):
        return (ratio * self.linear_utility) ** self.ro


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


class FisherPlayerASY(PlayerAlgorithm):
    def __init__(self, agent_simulator, t_now):
        PlayerAlgorithm.__init__(self, agent_simulator, t_now=t_now)
        self.r_i = {} # dict {key = task, value = dict{key= mission,value = utility}}
        self.x_i = {} # dict {key = task, value = dict{key= mission,value = allocation}}
        self.msgs = {} # dict {key = task_id, value = last msg}
        self.calculate_bids_flag = False


    def add_task_entity_to_log(self, task_entity: TaskSimple):
        super().add_task_entity_to_log(task_entity)
        for mission_entity in task_entity.missions:
            if task_entity not in self.r_i:
                self.r_i[task_entity] = {}
            self.r_i[task_entity][mission_entity] = Utility(player_entity=self.simulation_entity,
                                                            mission_entity=mission_entity,
                                                            task_entity=task_entity, t_now=self.t_now)

    def initiate_algorithm(self):
        raise Exception("only tasks initiate the algorithm")

    def measurements_per_agent(self):
        # TODO
        print("blah")

        pass

    def reset_additional_fields(self):
        # TODO
        pass

    def set_receive_flag_to_true_given_msg(self, msg):
        self.calculate_bids_flag = True

    def get_current_timestamp_from_context(self, msg):
        task_id = msg.sender
        if task_id not in self.msgs:
            return 0
        else:
            return self.msgs[task_id].timestamp

    def update_message_in_context(self, msg):
        task_id = msg.sender
        self.msgs[task_id] = msg
        dict_missions_xi = msg.information
        for mission, x_ij in dict_missions_xi:
            self.x_i[mission] = x_ij

    def get_is_going_to_compute_flag(self):
        return self.calculate_bids_flag

    def compute(self):
        # TODO
        pass

    def get_list_of_msgs_to_send(self):
        # TODO
        pass


