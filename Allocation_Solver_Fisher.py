import abc
import copy
import math
import random
from abc import ABC

import Simulation_Abstract
from Allocation_Solver_Abstract import PlayerAlgorithm, TaskAlgorithm, AllocationSolverTasksPlayersSemi, \
    default_communication_disturbance, AllocationSolverTasksPlayersFullRandTaskInit, \
    AllocationSolverTasksPlayersFullLatestTaskInit
from Simulation_Abstract import Entity, TaskSimple, PlayerSimple
from Allocation_Solver_Abstract import Msg, MsgTaskEntity
from TSG_rij import calculate_rij_tsg

is_with_scheduling = True



fisher_player_debug = False
print_price_delta_debug = True
simulation_rep_received = 0

class Utility:
    def __init__(self, player_entity, mission_entity, task_entity, t_now, future_utility_function,
                 ro=0.9, util=-1):
        self.player_entity = player_entity
        self.mission_entity = mission_entity
        self.task_entity = task_entity

        self.t_now = t_now
        self.ro = ro
        if util == -1:
            self.linear_utility = future_utility_function(player_entity=self.player_entity,
                                                          mission_entity=self.mission_entity,
                                                          task_entity=self.task_entity,
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


class AllocationData():
    def __init__(self, task, mission,player_id, measure_=None,norm_xjk=None, time_player_arrives = None, max_time_received = None):
        self.task = task
        self.mission = mission
        self.player_id = player_id
        self.measure_ = measure_ #bpb
        self.time_player_arrives = time_player_arrives
        self.max_time_received = max_time_received
        self.norm_xjk = norm_xjk


class FisherPlayerASY(PlayerAlgorithm, ABC):
    def __init__(self, util_structure_level, agent_simulator, t_now, future_utility_function, is_with_timestamp, ro=0.9):
        PlayerAlgorithm.__init__(self, agent_simulator, t_now=t_now, is_with_timestamp=is_with_timestamp)
        self.ro = ro
        self.r_i = {}  # dict {key = task, value = dict{key= mission,value = utility}}
        self.bids = {}
        self.x_i = {}  # dict {key = task, value = dict{key= mission,value = allocation}}
        self.x_i_norm = {}  # dict {key = task, value = dict{key= mission,value = allocation}}
        self.msgs_from_tasks = {}  # dict {key = task_id, value = last msg}
        self.calculate_bids_flag = False
        self.future_utility_function = future_utility_function
        self.util_structure_level = util_structure_level  # 1-calculated rij, 2-random when importance determines, 3-random completely

    def reset_additional_fields(self):

        self.r_i = {}  # dict {key = task, value = dict{key= mission,value = utility}}
        self.bids = {}
        self.x_i = {}  # dict {key = task, value = dict{key= mission,value = allocation}}
        self.x_i_norm = {}
        self.msgs_from_tasks = {}  # dict {key = task_id, value = last msg}
        self.calculate_bids_flag = False

        self.set_initial_r_i()
        self.set_initial_bids()
        self.set_initial_x_i()
        self.set_msgs()
        self.more_reset_additional_fields()

    @abc.abstractmethod
    def more_reset_additional_fields(self):
        raise NotImplementedError

    def set_msgs(self):
        for task_log in self.tasks_log:
            self.msgs_from_tasks[task_log.id_] = None

    def set_initial_x_i(self):
        for task_log in self.tasks_log:
            self.set_single_task_in_x_i(task_log)

    def set_single_task_in_x_i(self, task_log):
        self.x_i[task_log] = {}
        self.x_i_norm[task_log] = {}
        for mission_log in task_log.missions_list:
            self.x_i[task_log][mission_log] = None
            self.x_i_norm[task_log][mission_log] = None

    def set_initial_r_i(self):
        for task_in_log in self.tasks_log:
            self.set_single_task_in_r_i(task_in_log)

    def set_single_task_in_r_i(self, task_in_log):

        self.r_i[task_in_log] = {}
        for mission_log in task_in_log.missions_list:
            util_value = self.get_linear_util(mission_entity=mission_log, task_entity=task_in_log)

            util = Utility(player_entity=self.simulation_entity, mission_entity=mission_log, task_entity=task_in_log,
                           t_now=self.t_now, future_utility_function=self.future_utility_function, ro=self.ro,
                           util=util_value)
            self.r_i[task_in_log][mission_log] = util

    def get_linear_util(self, mission_entity, task_entity):

        me_hash = self.simulation_entity.id_.__hash__()
        mission_hash = mission_entity.mission_id.__hash__()
        task_hash = task_entity.id_.__hash__()
        rnd_seed = simulation_rep_received * 17 + me_hash * 13 + mission_hash * 23 + task_hash * 27

        rnd = random.Random(rnd_seed)

        calculated_util = calculate_rij_tsg(player_entity=self.simulation_entity, mission_entity=mission_entity,
                                            task_entity=task_entity,
                                            t_now=self.t_now)

        if self.util_structure_level == 1:
            util = calculated_util
        if self.util_structure_level == 2:
            if calculated_util != 0:
                util = task_entity.importance * rnd.random()
            else:
                util = 0
        if self.util_structure_level == 3:
            util = rnd.random()

        return util

    def set_initial_bids(self):
        sum_util = self.get_sum_util()
        if sum_util == 0:
            return
        for task_log in self.tasks_log:
            self.bids[task_log] = {}
            for mission_log in task_log.missions_list:
                util = self.r_i[task_log][mission_log]
                linear_util = util.get_utility()
                self.bids[task_log][mission_log] = linear_util / sum_util

    def get_sum_util(self):
        sum_util_list = []
        for task_log in self.tasks_log:
            for mission_log in task_log.missions_list:
                util = self.r_i[task_log][mission_log]
                linear_util = util.get_utility()
                sum_util_list.append(linear_util)

        return sum(sum_util_list)

    def add_task_entity_to_log(self, task_entity: TaskSimple):
        super().add_task_entity_to_log(task_entity)
        for mission_entity in task_entity.missions_list:
            task_ids_in_r_i = []
            for task_key in self.r_i.keys():
                task_ids_in_r_i.append(task_key.id_)
            if task_entity.id_ not in task_ids_in_r_i:
                self.r_i[task_entity] = {}
            util_value = self.get_linear_util(task_entity=task_entity, mission_entity=mission_entity)

            self.r_i[task_entity][mission_entity] = Utility(player_entity=self.simulation_entity,
                                                            mission_entity=mission_entity,
                                                            task_entity=task_entity, t_now=self.t_now,
                                                            future_utility_function=self.future_utility_function,
                                                            util=util_value)

    def initiate_algorithm(self):
        raise Exception("only tasks initiate the algorithm")

    def set_receive_flag_to_true_given_msg_after_check(self, msg):
        self.calculate_bids_flag = True

    def get_current_timestamp_from_context(self, msg):
        task_id = msg.sender

        if task_id not in self.msgs_from_tasks or self.msgs_from_tasks[task_id] is None :
            return -1
        else:
            return self.msgs_from_tasks[task_id].timestamp

    def update_message_in_context(self, msg):
        task_simulation = self.set_information_prior_to_computation(msg)
        self.update_xij(task_simulation, msg.information[0])
        self.update_xij_norm(task_simulation, msg.information[1])
        self.update_more_information_index_2_and_above(task_simulation, msg)

    def set_information_prior_to_computation(self, msg):
        task_in_log = self.is_task_entity_new_in_log(msg.task_entity)
        if task_in_log is None:
            task_in_log = msg.task_entity

        self.set_single_task_in_x_i(task_in_log)
        self.set_single_task_in_r_i(task_in_log)

        task_id = msg.sender
        self.msgs_from_tasks[task_id] = msg

        return msg.task_entity

    def update_xij(self, task_simulation, dict_missions_xi):
        for mission, x_ij in dict_missions_xi.items():
            if x_ij is None:
                self.x_i[task_simulation][mission] = x_ij
            elif x_ij > 0.001:
                self.x_i[task_simulation][mission] = x_ij
            else:
                self.x_i[task_simulation][mission] = 0

    def update_xij_norm(self, task_simulation, dict_missions_xi_norm):
        for mission, x_ij_norm in dict_missions_xi_norm.items():
            if x_ij_norm is None:
                self.x_i_norm[task_simulation][mission] = x_ij_norm
            elif x_ij_norm > 0.001:
                self.x_i_norm[task_simulation][mission] = x_ij_norm
            else:
                self.x_i_norm[task_simulation][mission] = 0

    @abc.abstractmethod
    def update_more_information_index_2_and_above(self, task_simulation, msg):
        raise NotImplementedError

    def debug_print_received_xij(self, task_simulation, mission, x_ij):
        print("RIJ = ", self.r_i[task_simulation][mission].linear_utility)
        print("task:", task_simulation.id_, mission, "type:", mission.abilities[0].ability_type, "XIJ=", x_ij)
        print("_________")

    def is_task_entity_new_in_log(self, task_entity: TaskSimple):
        for task_in_log in self.tasks_log:
            if task_in_log.id_ == task_entity.id_:
                return task_in_log

    def get_is_going_to_compute_flag(self):
        return self.calculate_bids_flag

    def compute(self):
        self.compute_player_market()
        self.compute_schedule()

    def compute_player_market(self):
        sum_of_bids, sum_util_nones, w_none, w_not_none = self.calculate_sum_xij_rj()
        atomic_counter = 0
        for task, dict in self.x_i.items():
            self.bids[task] = {}
            for mission, x_ij in dict.items():
                if x_ij is None:
                    r_ij = self.r_i[task][mission].get_utility(ratio=1)
                    if sum_util_nones == 0:
                        self.bids[task][mission] = 0
                    else:
                        self.bids[task][mission] = (r_ij / sum_util_nones) * w_none
                else:
                    if sum_of_bids == 0:
                        self.bids[task][mission] = 0
                    else:
                        r_ij_times_x_ij = self.r_i[task][mission].get_utility(ratio=x_ij)
                        self.bids[task][mission] = (r_ij_times_x_ij / sum_of_bids) * w_not_none
                atomic_counter = atomic_counter + 1
        self.check_bids()

    def check_bids(self):
        bids_list = []
        for task, dict in self.bids.items():
            for mission, bid in dict.items():
                bids_list.append(bid)
        bids_sum = sum(bids_list)
        if 0.98 < bids_sum < 1.01 == False:
            raise Exception("wrong calc of bids, should be around 1")

    def calculate_sum_xij_rj(self):
        sum_of_bids_list = []
        sum_r_ijs_none_list = []
        x_none = 0
        x_not_none = 0
        x_counter = 0
        for task, dict in self.x_i.items():
            for mission, x_ij in dict.items():
                if x_ij is None:
                    x_none += 1
                    sum_r_ijs_none_list.append(self.r_i[task][mission].get_utility(ratio=1))
                else:
                    x_not_none += 1
                    r_ij = self.r_i[task][mission]
                    sum_of_bids_list.append(r_ij.get_utility(ratio=x_ij))
                # self.atomic_counter = self.atomic_counter + 1

                x_counter += 1

        return sum(sum_of_bids_list), sum(sum_r_ijs_none_list), x_none / x_counter, x_not_none / x_counter

    @abc.abstractmethod
    def compute_schedule(self):
        raise NotImplementedError

    def get_list_of_msgs_to_send(self):
        ans = []
        for task, dict in self.bids.items():
            information_to_send = [dict]
            additional_info = self.list_of_info_to_send_beside_bids(task)
            if additional_info is not None:
                information_to_send = information_to_send + additional_info

            is_perfect_com = False
            if task in self.simulation_entity.tasks_responsible:
                is_perfect_com = True
            ans.append(Msg(sender=self.simulation_entity.id_, receiver=task.id_, information=information_to_send
                           , is_with_perfect_communication=is_perfect_com))
        return ans

    @abc.abstractmethod
    def list_of_info_to_send_beside_bids(self, task:TaskSimple) -> []:
        raise NotImplementedError

    def measurements_per_agent(self):
        # TODO
        print("need to complete measurements per agent in FisherPlayerASY")
        pass

    def is_identical_context(self, msg: Msg):
        sender = msg.sender
        last_msg_from_sender = self.get_last_msg_of_sender(sender)
        if last_msg_from_sender is None:
            return False

        info_from_last_msg = last_msg_from_sender.information[0]

        for mission_id, x_ijk in msg.information[0].items():
            if mission_id not in info_from_last_msg.keys():
                return False
            if info_from_last_msg[mission_id] is None:
                return False
            if info_from_last_msg[mission_id] != x_ijk:
                return False

        return True

    def get_last_msg_of_sender(self, sender):
        for task in self.msgs_from_tasks.keys():
            if sender == task:
                return self.msgs_from_tasks[task]

    def set_receive_flag_to_false(self):
        self.calculate_bids_flag = False

def get_allocation_measure(allo:AllocationData):
    return allo.measure_

class FisherPlayerASY_TSG_greedy_Schedual(FisherPlayerASY):
    def __init__(self, util_structure_level, agent_simulator, t_now, future_utility_function, is_with_timestamp, ro=0.9):
        FisherPlayerASY.__init__(self,util_structure_level = util_structure_level, agent_simulator=agent_simulator,
                                 t_now=t_now, future_utility_function=future_utility_function,
                                 is_with_timestamp=is_with_timestamp, ro=ro)
        self.allocations_data = []
        self.allocation_data_dict = {}



    def more_reset_additional_fields(self):
        self.allocations_data = []
        self.allocation_data_dict = {}

    def update_more_information_index_2_and_above(self, task_simulation, msg):
        if is_with_scheduling:

            max_time_dict = msg.information[2]
            if task_simulation not in self.allocation_data_dict:
                self.allocation_data_dict[task_simulation] = {}
                for mission in task_simulation.missions_list:
                    self.allocation_data_dict[task_simulation][mission] = AllocationData(task=task_simulation,
                                                                                         mission=mission,
                                                                                         player_id=self.simulation_entity.id_,
                                                                                           )
            allos_of_task = self.allocation_data_dict[task_simulation]
            for mission, max_time in max_time_dict.items():
                allos_of_task[mission].max_time_received = max_time

        else:
            pass

    def compute_schedule(self):
        if is_with_scheduling:

            time_to_tasks = self.get_time_of_task()
            bang_per_buck_dict = self.get_bang_per_buck_dict(time_to_tasks)  # task = {mission:bpb}
            self.insert_bpb_dict_to_allocation_data(bang_per_buck_dict)
            self.allocations_data = sorted(self.allocations_data, key= get_allocation_measure, reverse=True)
            self.measure_arrival_time()
            only_allocated_missions = self.get_only_allocated_missions()
            allocation_list = self.exam_switch(only_allocated_missions)
            self.update_schedule_for_simulation_player(allocation_list)
        else:
            pass
    def update_schedule_for_simulation_player(self, allocation_list):
        self.simulation_entity.schedule = []  # [(task,mission,time)]
        for allo in allocation_list:
            task = allo.task
            mission = allo.mission
            time_ = (mission.remaining_workload*allo.norm_xjk) / self.simulation_entity.productivity
            tuple_ = (task, mission, time_)
            self.simulation_entity.schedule.append(tuple_)  # [(task,mission,time)]

    def exam_switch(self,only_allo_missions):


        if len(only_allo_missions)>0:
            top_measure_allocation = only_allo_missions[0]

            max_time_received = top_measure_allocation.max_time_received

            if max_time_received is not None:
                for i in range(1,len(only_allo_missions)):
                    other_mission_allocation = only_allo_missions[i]
                    time_it_will_take = self.get_time_it_takes_to_go_to_other_mission(top_measure_allocation,other_mission_allocation)
                    if max_time_received>time_it_will_take:
                        only_allo_missions[0], only_allo_missions[i] = only_allo_missions[i], only_allo_missions[0]
                        break
        return only_allo_missions


    def get_time_it_takes_to_go_to_other_mission(self,top_measure_allocation,other_mission_allocation):
        current_location = self.simulation_entity.location
        player_speed = self.simulation_entity.speed
        top_measure_task_location = top_measure_allocation.task.location

        location_task = other_mission_allocation.task.location

        ####---------travel time from current location
        distance_to_task = Simulation_Abstract.calculate_distance_input_location(location_task, current_location)
        absolute_time_to_task = distance_to_task / player_speed
        time_player_arrives = absolute_time_to_task

        ###----------workload time
        remaining_workload = other_mission_allocation.mission.remaining_workload
        productivity = self.simulation_entity.productivity
        time_at_mission = other_mission_allocation.norm_xjk * remaining_workload / productivity

        ###----------travel time to top location
        distance_from_other_task_to_top = Simulation_Abstract.calculate_distance_input_location(location_task,
                                                                                                top_measure_task_location)
        absolute_time_to_task_from_other_task_to_top = distance_from_other_task_to_top / player_speed

        ###----------
        return time_player_arrives + time_at_mission + absolute_time_to_task_from_other_task_to_top


    def insert_bpb_dict_to_allocation_data(self, bang_per_buck_dict):
        for task,dict_ in bang_per_buck_dict.items():
            for mission, bpb_measure in dict_.items():
                current_allocation_data_in_memory = self.get_allocation_data(task, mission)
                if current_allocation_data_in_memory is None :
                    allo_temp = AllocationData(task=task, mission=mission, player_id=self.simulation_entity.id_,
                                               measure_=bpb_measure,norm_xjk=self.x_i_norm[task][mission])
                    self.allocations_data.append(allo_temp)

                    if allo_temp.task not in self.allocation_data_dict.keys() :
                        self.allocation_data_dict[allo_temp.task] = {}
                    self.allocation_data_dict[allo_temp.task][allo_temp.mission] = allo_temp

                else:
                    current_allocation_data_in_memory.measure_ = bpb_measure
                    current_allocation_data_in_memory.norm_xjk = self.x_i_norm[task][mission]
                    current_allocation_data_in_memory.time_player_arrives = None

    def get_allocation_data(self, task, mission):
        for allo in self.allocations_data:
            first_cond = allo.task.id_ == task.id_
            second_cond = allo.mission.mission_id == mission.mission_id
            if first_cond and second_cond:
                return allo
        return None


    def get_time_of_task(self):
        ans = {}

        for task in self.x_i_norm.keys():
            distance_to_task = Simulation_Abstract.calculate_distance(self.simulation_entity, task)
            arrival_time = distance_to_task / self.simulation_entity.speed
            ans[task] = arrival_time
        return ans

    def get_bang_per_buck_dict(self, time_to_tasks):
        bang_per_buck = {}
        for task, dict_ in self.x_i_norm.items():
            bang_per_buck[task] = {}
            time_to_task = time_to_tasks[task]
            for mission, allocation in dict_.items():

                r_ijk = self.r_i[task][mission].get_utility(1)
                x_ijk = allocation

                if x_ijk is None or x_ijk == 0:
                    bang_per_buck[task][mission] = 0
                else:
                    numerator = r_ijk * x_ijk

                    remaining_workload = mission.remaining_workload
                    productivity = self.simulation_entity.productivity
                    time_at_mission = allocation * (remaining_workload / productivity)
                    denominator = time_to_task + time_at_mission
                    bang_per_buck[task][mission] = numerator / denominator
        return bang_per_buck


    def list_of_info_to_send_beside_bids(self, task:TaskSimple) -> []:
        if is_with_scheduling:
            dict_= self.allocation_data_dict[task]
            ans = {}
            for mission,allo in dict_.items():
                ans[mission]=allo.time_player_arrives

            return [ans]

        else:
            pass

    def measure_arrival_time(self):
        current_time = 0
        player_speed = self.simulation_entity.speed
        current_location = self.simulation_entity.location
        for allocation in self.allocations_data:
            location_task = allocation.task.location
            if allocation.measure_ == 0:
                allocation.time_player_arrives = None
            else:
                distance_to_task = Simulation_Abstract.calculate_distance_input_location(location_task,current_location)
                absolute_time_to_task = distance_to_task/player_speed

                ####---------
                time_player_arrives = current_time+ absolute_time_to_task
                allocation.time_player_arrives = time_player_arrives

                ###----------
                current_time = self.update_current_time(allocation,current_time,absolute_time_to_task)
                current_location = location_task

    def update_current_time(self,allocation,current_time,absolute_time_to_task):
        remaining_workload = allocation.mission.remaining_workload
        productivity = self.simulation_entity.productivity
        time_at_mission = allocation.norm_xjk * remaining_workload / productivity
        return current_time + absolute_time_to_task + time_at_mission

    def get_only_allocated_missions(self):
        only_allo_missions = []
        for allo in self.allocations_data:
            if allo.measure_ > 0:
                only_allo_missions.append(allo)
        only_allo_missions = sorted(only_allo_missions, key=get_allocation_measure, reverse=True)
        return only_allo_missions




class FisherTaskASY(TaskAlgorithm):
    def __init__(self, agent_simulator: TaskSimple, t_now, is_with_timestamp, counter_of_converges=2, Threshold=0.001):
        TaskAlgorithm.__init__(self, simulation_entity = agent_simulator, t_now=t_now, is_with_timestamp=is_with_timestamp)
        if not isinstance(agent_simulator, TaskSimple):
            raise Exception("wrong type of simulation entity")
        self.Threshold = Threshold
        self.counter_of_converges = counter_of_converges
        self.counter_of_converges_dict = {}
        self.is_finish_phase_II = False
        self.potential_players_ids_list = []
        self.reset_potential_players_ids_list()
        self.bids = {}
        self.missions_converged = {}
        self.reset_bids()
        self.x_jk = {}
        self.x_jk_normal = {}
        self.reset_x_jk()
        self.msgs_from_players = {}
        self.reset_msgs_from_players()
        self.calculate_xjk_flag = False
        self.price_t_minus = {}
        self.price_current = {}
        self.price_delta = {}

        for mission in self.simulation_entity.missions_list:
            self.price_t_minus[mission] = 9999999
            self.price_current[mission] = 0
            self.price_delta[mission] = 9999999
            self.counter_of_converges_dict[mission] = self.counter_of_converges

    def reset_additional_fields(self):
        self.is_finish_phase_II = False
        self.reset_potential_players_ids_list()
        self.reset_bids()
        self.reset_x_jk()
        self.reset_msgs_from_players()
        self.calculate_xjk_flag = False
        for mission in self.simulation_entity.missions_list:
            self.price_t_minus[mission] = 9999999
            self.price_current[mission] = 0
            self.price_delta[mission] = 9999999
            self.counter_of_converges_dict[mission] = self.counter_of_converges
        self.more_reset_additional_fields()

    @abc.abstractmethod
    def more_reset_additional_fields(self):
        raise NotImplementedError


    def reset_msgs_from_players(self):
        self.msgs_from_players = {}
        for player_id in self.potential_players_ids_list:
            self.msgs_from_players[player_id] = None

    def reset_x_jk(self):
        self.x_jk = {}
        self.x_jk_normal = {}
        for mission in self.simulation_entity.missions_list:
            self.x_jk[mission] = {}
            self.x_jk_normal[mission] = {}
            for n_id in self.potential_players_ids_list:
                self.x_jk[mission][n_id] = None
                self.x_jk_normal[mission][n_id] = None

    def reset_bids(self):
        self.bids = {}
        for mission in self.simulation_entity.missions_list:
            self.bids[mission] = {}
            for n_id in self.potential_players_ids_list:
                self.bids[mission][n_id] = None

    def reset_potential_players_ids_list(self):
        self.potential_players_ids_list = []
        for neighbour in self.simulation_entity.neighbours:
            self.potential_players_ids_list.append(neighbour)

    def initiate_algorithm(self):
        self.send_msgs()  # will send messages with None to all relevent players

    def set_receive_flag_to_true_given_msg_after_check(self, msg):
        self.calculate_xjk_flag = True

    def get_current_timestamp_from_context(self, msg):
        player_id = msg.sender
        try:
            if self.msgs_from_players[player_id] is None:
                return 0
            else:
                return self.msgs_from_players[player_id].timestamp
        except:
            return 0

    def update_message_in_context(self, msg):
        player_id = msg.sender
        self.msgs_from_players[player_id] = msg
        self.update_bids_info(bids_dict = msg.information[0], player_id=player_id)
        self.update_more_information_index_1_and_above(player_id =player_id, msg=msg)

    @abc.abstractmethod
    def update_more_information_index_1_and_above(self,player_id , msg):
        raise NotImplementedError

    def update_bids_info(self, bids_dict,player_id):
        for mission, bid in bids_dict.items():
            if mission not in self.bids:
                self.bids[mission] = {}
            self.bids[mission][player_id] = bid

    def get_is_going_to_compute_flag(self):
        return self.calculate_xjk_flag

    def compute(self):

        self.price_t_minus = self.price_current
        self.price_current = self.calculate_price()
        self.check_converges_market()
        flag = False
        if self.task_phase_I_over():
            self.is_finish_phase_II = True
            flag = True
        self.compute_allocation()
        self.compute_normalize_allocation()

        self.compute_schedule()
        if flag:
            return True
        return False

    @abc.abstractmethod
    def compute_schedule(self):
        raise NotImplementedError



    def compute_normalize_allocation(self):
        # self.check_if_x_jk_per_mission_is_one()
        dict_non_zero_allocation = self.dict_non_zero_allocation()
        for mission, dict_ in dict_non_zero_allocation.items():

            if mission.max_players == 1:
                self.normalize_allocation_if_no_coop(dict_, mission)
            else:
                amount_of_allocated_agents = len(dict_non_zero_allocation[mission])
                if amount_of_allocated_agents > mission.max_players:
                    self.spread_allocation_to_max_amount(dict_non_zero_allocation[mission], mission.max_players,
                                                         mission)
                else:
                    self.copy_current_xij_to_normalized(mission)

    def compute_allocation(self):
        for mission in self.simulation_entity.missions_list:
            for player_id, bid in self.bids[mission].items():
                self.atomic_counter = self.atomic_counter + 1
                if self.bids[mission][player_id] is not None and self.price_current[mission] != 0:
                    self.x_jk[mission][player_id] = bid / self.price_current[mission]
                else:
                    self.x_jk[mission][player_id] = None

    def check_converges_market(self):
        for mission in self.simulation_entity.missions_list:
                current_price = self.price_current[mission]
                t_minus_price = self.price_t_minus[mission]
                self.price_delta[mission] = math.fabs(t_minus_price - current_price)
                if self.price_delta[mission] != 0:
                    self.update_converges_conditions(mission)



    def update_converges_conditions(self, mission):

        if self.price_delta[mission] < self.Threshold:
            self.counter_of_converges_dict[mission] = self.counter_of_converges_dict[mission] - 1
        else:
            self.counter_of_converges_dict[mission] = self.counter_of_converges

    def check_if_x_jk_per_mission_is_one(self):
        ans = {}
        for mission in self.simulation_entity.missions_list:
            ans[mission] = 0
        for mission in self.simulation_entity.missions_list:
            for player_id, bid in self.bids[mission].items():
                if self.bids[mission][player_id] is not None and self.price_current[mission] != 0:
                    ans[mission] = ans[mission] + self.x_jk[mission][player_id]
                else:
                    pass
        for mission, sum_x_jk in ans.items():
            if not 0.999 < sum_x_jk <= 1.001:
                if sum_x_jk != 0:
                    raise Exception("mistake in calculating x_jk for task", self.simulation_entity)

    def calculate_price(self):
        ans = {}
        for mission in self.simulation_entity.missions_list:
            for bid in self.bids[mission].values():
                # self.atomic_counter = self.atomic_counter+1

                if bid is None:
                    bid = 0
                temp_price = 0
                if mission in ans.keys():
                    temp_price = ans[mission]
                ans[mission] = temp_price + bid
        return ans

    def get_list_of_msgs_to_send(self):
        ans = []
        for n_id in self.potential_players_ids_list:
            xij_market = {}
            xij_normal = {}
            flag = False
            for mission in self.simulation_entity.missions_list:
                x_ijk = self.x_jk[mission][n_id]
                xij_normal_val = self.x_jk_normal[mission][n_id]
                if x_ijk != 0:
                    flag = True
                xij_market[mission] = x_ijk
                xij_normal[mission] = xij_normal_val
            
            information_to_send = [xij_market, xij_normal]
            addition_to_info = self.list_of_info_to_send_beside_allocation(n_id)
            if addition_to_info is not None:
                information_to_send = information_to_send + addition_to_info

            if flag:
                is_perfect_com = False
                if self.simulation_entity.player_responsible.id_ == n_id:
                    is_perfect_com = True
                msg = Msg(sender=self.simulation_entity.id_, receiver=n_id, information=information_to_send,
                          is_with_perfect_communication=is_perfect_com)
                ans.append(msg)
        return ans

    def is_identical_context(self, msg: Msg):
        sender = msg.sender
        last_msg_from_sender = self.get_last_msg_of_sender(sender)
        if last_msg_from_sender is None:
            return False
        info_from_last_msg = last_msg_from_sender.information[0]

        for mission_id, x_ijk in msg.information[0].items():
            if mission_id not in info_from_last_msg.keys():
                return False
            if info_from_last_msg[mission_id] != x_ijk:
                return False
        return True

    def get_last_msg_of_sender(self, sender):
        for task in self.msgs_from_players.keys():
            if sender == task:
                return self.msgs_from_players[task]

    def set_receive_flag_to_false(self):
        self.calculate_xjk_flag = False

    def measurements_per_agent(self):
        # TODO
        pass

    def task_phase_I_over(self):
        for mission, counter in self.counter_of_converges_dict.items():
            if counter > 0:
                if not self.allocation_all_zero(mission) and not self.allocation_single_one(mission):
                    return False

        return True

    def allocation_all_zero(self, mission):
        if len(self.x_jk[mission].keys()) == 0:
            return False
        for player_id, xjk in self.x_jk[mission].items():
            if xjk != 0:
                return False
        return True

    def allocation_single_one(self, mission):
        for player_id, xjk in self.x_jk[mission].items():
            if xjk == 1:
                return True
        return False

    def dict_non_zero_allocation(self):
        ans = {}
        for mission, dict in self.x_jk.items():
            temp_ans = {}
            for player_id, allocation in dict.items():
                if allocation != 0 and allocation is not None:
                    temp_ans[player_id] = allocation
            ans[mission] = temp_ans

        return ans

    def normalize_allocation_if_no_coop(self, dict_, mission):
        top_allocation_player_id = None
        if len(dict_) != 0:
            top_allocation_player_id = max(dict_, key=dict_.get)

        if top_allocation_player_id is not None:
            for player_id in self.x_jk_normal[mission].keys():
                if player_id == top_allocation_player_id:
                    self.x_jk_normal[mission][player_id] = 1
                else:
                    self.x_jk_normal[mission][player_id] = 0
        else:
            for player_id in self.x_jk_normal[mission].keys():
                self.x_jk_normal[mission][player_id] = 0

    def copy_current_xij_to_normalized(self, mission):

        for player_id in self.x_jk_normal[mission].keys():
            if self.x_jk[mission][player_id] != 0 or self.x_jk[mission][player_id] is not None:
                self.x_jk_normal[mission][player_id] = self.x_jk[mission][player_id]
            else:
                self.x_jk_normal[mission][player_id] = 0

    def spread_allocation_to_max_amount(self, dict_, max_players, mission):
        to_be_allocated = self.get_dict_of_allocated_players(dict_, max_players)
        normalized_allocated_players = self.get_normalized_allocated_players(to_be_allocated)

        for id_ in self.x_jk_normal[mission].keys():
            if id_ in normalized_allocated_players.keys():
                self.x_jk_normal[mission][id_] = normalized_allocated_players[id_]
            else:
                self.x_jk_normal[mission][id_] = 0

    def get_dict_of_allocated_players(self, dict_, max_players):
        to_be_allocated = copy.deepcopy(dict_)
        while len(to_be_allocated) != max_players:
            lowest_allocation_player_id = min(to_be_allocated, key=to_be_allocated.get)
            del to_be_allocated[lowest_allocation_player_id]
        return to_be_allocated

    def get_normalized_allocated_players(self, to_be_allocated):
        ans = {}
        sum_of_values = sum(to_be_allocated.values())
        for id_, non_norm_xijk in to_be_allocated.items():
            ans[id_] = non_norm_xijk / sum_of_values
        return ans

    @abc.abstractmethod
    def list_of_info_to_send_beside_allocation(self,player_id:str):
        raise NotImplementedError

class FisherTaskASY_TSG_greedy_Schedual(FisherTaskASY,ABC):
    def __init__(self, agent_simulator: TaskSimple, t_now, is_with_timestamp, counter_of_converges=2, Threshold=0.001):

        TaskAlgorithm.__init__(self, agent_simulator, t_now=t_now, is_with_timestamp=is_with_timestamp)
        if not isinstance(agent_simulator, TaskSimple):
            raise Exception("wrong type of simulation entity")
        self.Threshold = Threshold
        self.counter_of_converges = counter_of_converges
        self.counter_of_converges_dict = {}

        self.is_finish_phase_II = False

        self.potential_players_ids_list = []
        self.reset_potential_players_ids_list()

        self.bids = {}
        self.missions_converged = {}

        self.reset_bids()

        self.x_jk = {}
        self.x_jk_normal = {}

        self.reset_x_jk()

        self.msgs_from_players = {}
        self.reset_msgs_from_players()

        self.calculate_xjk_flag = False
        self.price_t_minus = {}
        self.price_current = {}
        self.price_delta = {}
        for mission in self.simulation_entity.missions_list:
            self.price_t_minus[mission] = 9999999
            self.price_current[mission] = 0
            self.price_delta[mission] = 9999999
            self.counter_of_converges_dict[mission] = self.counter_of_converges
        FisherTaskASY.__init__(self, agent_simulator=agent_simulator, t_now=t_now, is_with_timestamp=is_with_timestamp, counter_of_converges=2, Threshold=0.001)
        self.max_time_per_mission = {}
        self.player_greedy_arrive_dict = {}
        self.reset_mission_per_allocation_list()

    def reset_mission_per_allocation_list(self):
        for mission in self.simulation_entity.missions_list:
            self.player_greedy_arrive_dict[mission] ={}
            self.max_time_per_mission[mission] = None

    def more_reset_additional_fields(self):

        self.reset_mission_per_allocation_list()


    def update_more_information_index_1_and_above(self, player_id, msg):
        if is_with_scheduling:

            allocations_dict = msg.information[1]
            player_id_sender = msg.sender
            for mission,time_arrive in allocations_dict.items():
                self.player_greedy_arrive_dict[mission][player_id_sender] = time_arrive
        else:
            pass



    def compute_schedule(self):
        if is_with_scheduling:
            self.compute_max_time_per_mission()
        else:
            pass

    def compute_max_time_per_mission(self):
        for mission in self.simulation_entity.missions_list:
            arrives_per_mission = []
            arrive_time_dict = self.player_greedy_arrive_dict[mission]
            for time_ in arrive_time_dict.values():
                if time_ is not None:
                    arrives_per_mission.append(time_)
            if len(arrives_per_mission) == 0:
                self.max_time_per_mission[mission] = None
            else:
                self.max_time_per_mission[mission] = max(arrives_per_mission)


    def list_of_info_to_send_beside_allocation(self,player_id:str) -> []:
        if is_with_scheduling:
            return [self.max_time_per_mission]
        else:
            pass



# self.task = task
# self.mission = mission
# self.player_id = player_id
# self.measure_ = measure_  # bpb
# self.time_player_arrives = None
# self.max_time_received = None
# self.norm_xjk = norm_xjk


class FisherAsynchronousSolver_TasksTogether(AllocationSolverTasksPlayersSemi):
    def __init__(self, util_structure_level, mailer=None, f_termination_condition=None, f_global_measurements={},
                 f_communication_disturbance=default_communication_disturbance, future_utility_function=None,
                 is_with_timestamp=True, ro=0.9, simulation_rep=0):
        AllocationSolverTasksPlayersSemi.__init__(self, mailer, f_termination_condition, f_global_measurements,
                                                  f_communication_disturbance)
        simulation_rep_received = simulation_rep
        self.util_structure_level = util_structure_level
        self.ro = ro
        self.future_utility_function = future_utility_function
        self.is_with_timestamp = is_with_timestamp

    def create_algorithm_task(self, task: TaskSimple):
        return FisherTaskASY_TSG_greedy_Schedual(agent_simulator=task, t_now=self.tnow, is_with_timestamp=self.is_with_timestamp)

    def create_algorithm_player(self, player: PlayerSimple):
        return FisherPlayerASY_TSG_greedy_Schedual(util_structure_level=self.util_structure_level,
                                                   agent_simulator=player, t_now=self.tnow,
                                                   future_utility_function=self.future_utility_function,
                                                   is_with_timestamp=self.is_with_timestamp, ro=self.ro)


class FisherAsynchronousSolver_TaskRandInit(AllocationSolverTasksPlayersFullRandTaskInit):
    def __init__(self, util_structure_level, mailer=None, f_termination_condition=None, f_global_measurements={},
                 f_communication_disturbance=default_communication_disturbance, future_utility_function=None,
                 is_with_timestamp=True, ro=0.9, simulation_rep=0):
        AllocationSolverTasksPlayersFullRandTaskInit.__init__(self, mailer, f_termination_condition,
                                                              f_global_measurements,
                                                              f_communication_disturbance)
        simulation_rep_received = simulation_rep
        self.util_structure_level = util_structure_level
        self.ro = ro
        self.future_utility_function = future_utility_function
        self.is_with_timestamp = is_with_timestamp

    def create_algorithm_task(self, task: TaskSimple):
        return FisherTaskASY_TSG_greedy_Schedual(agent_simulator=task, t_now=self.tnow, is_with_timestamp=self.is_with_timestamp)

    def create_algorithm_player(self, player: PlayerSimple):
        return FisherPlayerASY_TSG_greedy_Schedual(util_structure_level=self.util_structure_level,
                                                   agent_simulator=player, t_now=self.tnow,
                                                   future_utility_function=self.future_utility_function,
                                                   is_with_timestamp=self.is_with_timestamp, ro=self.ro)


class FisherAsynchronousSolver_TaskLatestArriveInit(AllocationSolverTasksPlayersFullRandTaskInit):
    def __init__(self, util_structure_level, mailer=None, f_termination_condition=None, f_global_measurements={},
                 f_communication_disturbance=default_communication_disturbance, future_utility_function=None,
                 is_with_timestamp=True, ro=0.9, simulation_rep=0):
        AllocationSolverTasksPlayersFullLatestTaskInit.__init__(self, mailer, f_termination_condition,
                                                                f_global_measurements,
                                                                f_communication_disturbance)
        simulation_rep_received = simulation_rep
        self.util_structure_level = util_structure_level
        self.ro = ro
        self.future_utility_function = future_utility_function
        self.is_with_timestamp = is_with_timestamp

    def create_algorithm_task(self, task: TaskSimple):
        return FisherTaskASY_TSG_greedy_Schedual(agent_simulator=task, t_now=self.tnow, is_with_timestamp=self.is_with_timestamp)

    def create_algorithm_player(self, player: PlayerSimple):
        return FisherPlayerASY_TSG_greedy_Schedual(util_structure_level=self.util_structure_level,
                                                   agent_simulator=player, t_now=self.tnow,
                                                   future_utility_function=self.future_utility_function,
                                                   is_with_timestamp=self.is_with_timestamp, ro=self.ro)
