from abc import ABC

import Allocation_Solver_Abstract
import Simulation
from Allocation_Solver_Abstract import PlayerAlgorithm
from Simulation import Entity, TaskSimple, future_utility
from Allocation_Solver_Abstract import Msg,MsgTaskEntity


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



    def get_utility(self, ratio=1):
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
        self.bids = {}
        self.x_i = {} # dict {key = task, value = dict{key= mission,value = allocation}}
        self.msgs_from_tasks = {} # dict {key = task_id, value = last msg}
        self.calculate_bids_flag = False

    def reset_additional_fields(self):
        self.r_i = {}  # dict {key = task, value = dict{key= mission,value = utility}}
        self.bids = {}
        self.x_i = {}  # dict {key = task, value = dict{key= mission,value = allocation}}
        self.msgs_from_tasks = {}  # dict {key = task_id, value = last msg}
        self.calculate_bids_flag = False

        self.set_initial_r_i()
        self.set_initial_bids()
        self.set_initial_x_i()
        self.set_msgs()

    def set_msgs(self):
        for task_log in self.tasks_log:
            self.msgs_from_tasks[task_log] = None

    def set_initial_x_i(self):
        for task_log in self.tasks_log:
            self.set_single_task_in_x_i(task_log)


    def set_single_task_in_x_i(self, task_log):
        self.x_i[task_log] = {}
        for mission_log in task_log.missions:
            self.x_i[task_log][mission_log] = None

    def set_initial_r_i(self):
        for task_in_log in self.tasks_log:
            self.set_single_task_in_r_i(task_in_log)


    def set_single_task_in_r_i(self, task_in_log):
        self.r_i[task_in_log] = {}
        for mission_log in task_in_log.missions:
            util = Utility(player_entity=self.simulation_entity, mission_entity=mission_log, task_entity=task_in_log,
                           t_now=self.t_now)
            self.r_i[task_in_log][mission_log] = util


    def set_initial_bids(self):
        sum_util = self.get_sum_util()

        for task_log in self.tasks_log:
            self.bids[task_log]={}
            for mission_log in task_log.missions:
                util = self.r_i[task_log][mission_log]
                linear_util = util.get_utility()
                self.bids[task_log][mission_log] = linear_util/sum_util

    def get_sum_util(self):
        sum_util_list = []
        for task_log in self.tasks_log:
            for mission_log in task_log.missions:
                util = self.r_i[task_log][mission_log]
                linear_util = util.get_utility()
                sum_util_list.append(linear_util)

        return sum(sum_util_list)


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



    def set_receive_flag_to_true_given_msg(self, msg):
        self.calculate_bids_flag = True

    def get_current_timestamp_from_context(self, msg):
        task_id = msg.sender
        if task_id not in self.msgs_from_tasks:
            return 0
        else:
            return self.msgs_from_tasks[task_id].timestamp

    def update_message_in_context(self, msg):

        task_in_log = self.is_task_entity_new_in_log(msg.task_entity)
        task_is_new_in_log = task_in_log is None
        task_information_is_updated = task_in_log.last_time_updated<msg.task_entity.last_time_updated
        need_to_calc_bids_different = False

        if task_is_new_in_log or task_information_is_updated:
            self.set_single_task_in_x_i(task_in_log)
            self.set_single_task_in_r_i(task_in_log)
            need_to_calc_bids_different = True

            task_id = msg.sender
            self.msgs_from_tasks[task_id] = msg

            dict_missions_xi = msg.information
            task_simulation = msg.task_entity
            for mission, x_ij in dict_missions_xi:
                self.x_i[task_simulation][mission] = x_ij
                if need_to_calc_bids_different:
                    if x_ij is not None:
                        raise Exception("The task was suppose to send None")

    def is_task_entity_new_in_log(self, task_entity:Simulation.TaskSimple):
        for task_in_log in self.tasks_log:
            if task_in_log.id_==task_entity.id_:
                return task_in_log

    def get_is_going_to_compute_flag(self):
        return self.calculate_bids_flag

    def compute(self):
        sum_of_bids,sum_util_nones, w_none,w_not_none = self.calculate_sum_xij_rj()
        for task,dict in self.x_i.items():
            for mission,x_ij in dict.items():
                if x_ij is None:
                    r_ij = self.r_i[task][mission].get_utility(ratio=1)
                    self.bids[task][mission] = (r_ij/sum_util_nones)*w_none
                else:
                    r_ij_times_x_ij = self.r_i[task][mission].get_utility(ratio=x_ij)
                    self.bids[task][mission] = (r_ij_times_x_ij/sum_of_bids)*w_not_none
        self.check_bids()


    def check_bids(self):
        bids_list = []
        for task, dict in self.bids.items():
            for mission, bid in dict.items():
                bids_list.append(bid)
        bids_sum = sum(bids_list)
        if 0.98<bids_sum<1.01 == False:
            raise Exception("wrong calc of bids, should be around 1")

    def calculate_sum_xij_rj(self):
        sum_of_bids_list = []
        sum_r_ijs_none_list = []
        x_none = 0
        x_not_none = 0
        x_counter = 0
        for task,dict in self.x_i.items():
            for mission,x_ij in dict.items():
                if x_ij is None:
                    x_none+=1
                    sum_r_ijs_none_list.append(self.r_i[task][mission].get_utility(ratio=1))
                else:
                    x_not_none+=1
                    r_ij = self.r_i[task][mission]
                    sum_of_bids_list.append(r_ij.get_utility(ratio=x_ij))
                x_counter+=1

        return sum(sum_of_bids_list),sum(sum_r_ijs_none_list),x_none/x_counter,x_not_none/x_counter


    def get_list_of_msgs_to_send(self):
        ans = []
        for task,dict in self.bids.items():
            is_perfect_com = False
            if task in self.simulation_entity.tasks_responsible:
                is_perfect_com = True
            ans.append(Msg( sender=self.simulation_entity.id_, receiver = task.id_, information=dict
                            ,is_with_perfect_communication = is_perfect_com))



    def measurements_per_agent(self):
        # TODO
        print("blah")
        pass













