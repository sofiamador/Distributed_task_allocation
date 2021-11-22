import math
from abc import ABC

from Allocation_Solver_Abstract import PlayerAlgorithm, TaskAlgorithm, AllocationSolverTasksPlayersSemi, \
    default_communication_disturbance
from Simulation import Entity, TaskSimple, PlayerSimple
from Allocation_Solver_Abstract import Msg, MsgTaskEntity

fisher_player_debug = False


class Utility:
    def __init__(self, player_entity, mission_entity, task_entity, t_now, future_utility_function, ro=1, util=-1):
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


class FisherPlayerASY(PlayerAlgorithm):
    def __init__(self, agent_simulator, t_now, future_utility_function, is_with_timestamp,ro = 1):
        PlayerAlgorithm.__init__(self, agent_simulator, t_now=t_now, is_with_timestamp=is_with_timestamp)
        self.ro = ro
        self.r_i = {}  # dict {key = task, value = dict{key= mission,value = utility}}
        self.bids = {}
        self.x_i = {}  # dict {key = task, value = dict{key= mission,value = allocation}}
        self.msgs_from_tasks = {}  # dict {key = task_id, value = last msg}
        self.calculate_bids_flag = False
        self.future_utility_function = future_utility_function

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
        for mission_log in task_log.missions_list:
            self.x_i[task_log][mission_log] = None

    def set_initial_r_i(self):
        for task_in_log in self.tasks_log:
            self.set_single_task_in_r_i(task_in_log)

    def set_single_task_in_r_i(self, task_in_log):

        self.r_i[task_in_log] = {}
        for mission_log in task_in_log.missions_list:
            util = Utility(player_entity=self.simulation_entity, mission_entity=mission_log, task_entity=task_in_log,
                           t_now=self.t_now, future_utility_function=self.future_utility_function,ro=self.ro)
            self.r_i[task_in_log][mission_log] = util

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
            self.r_i[task_entity][mission_entity] = Utility(player_entity=self.simulation_entity,
                                                            mission_entity=mission_entity,
                                                            task_entity=task_entity, t_now=self.t_now,
                                                            future_utility_function=self.future_utility_function)

    def initiate_algorithm(self):
        raise Exception("only tasks initiate the algorithm")

    def set_receive_flag_to_true_given_msg_after_check(self, msg):
        self.calculate_bids_flag = True

    def get_current_timestamp_from_context(self, msg):
        task_id = msg.sender
        if task_id not in self.msgs_from_tasks:
            return -1
        else:
            return self.msgs_from_tasks[task_id].timestamp

    def update_message_in_context(self, msg):
        task_in_log = self.is_task_entity_new_in_log(msg.task_entity)
        task_is_new_in_log = False
        if task_in_log is None:
            task_in_log = msg.task_entity
        #      task_is_new_in_log = True
        # else:
        #     task_information_is_updated = task_in_log.last_time_updated < msg.task_entity.last_time_updated
        #
        # if task_is_new_in_log or task_information_is_updated:

        self.set_single_task_in_x_i(task_in_log)
        self.set_single_task_in_r_i(task_in_log)

        task_id = msg.sender
        self.msgs_from_tasks[task_id] = msg

        dict_missions_xi = msg.information
        task_simulation = msg.task_entity
        for mission, x_ij in dict_missions_xi.items():
            if x_ij is None:
                self.x_i[task_simulation][mission] = x_ij
            elif x_ij > 0.001:
                self.x_i[task_simulation][mission] = x_ij
            else:
                self.x_i[task_simulation][mission] = 0

            if fisher_player_debug and self.simulation_entity.id_ == "QDPV68R5J2":
                self.debug_print_received_xij(task_simulation, mission, x_ij)

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

    def get_list_of_msgs_to_send(self):
        ans = []
        for task, dict in self.bids.items():
            is_perfect_com = False
            if task in self.simulation_entity.tasks_responsible:
                is_perfect_com = True
            ans.append(Msg(sender=self.simulation_entity.id_, receiver=task.id_, information=dict
                           , is_with_perfect_communication=is_perfect_com))
        return ans

    def measurements_per_agent(self):
        # TODO
        print("need to complete measurements per agent in FisherPlayerASY")
        pass

    def is_identical_context(self, msg: Msg):
        sender = msg.sender
        last_msg_from_sender = self.get_last_msg_of_sender(sender)
        if last_msg_from_sender is None:
            return False

        info_from_last_msg = last_msg_from_sender.information

        for mission_id, x_ijk in msg.information:
            if mission_id not in info_from_last_msg.keys():
                return False
            if info_from_last_msg[mission_id] != x_ijk:
                return False
        return True

    def get_last_msg_of_sender(self, sender):
        for task in self.msgs_from_tasks.keys():
            if sender == task.id_:
                return self.msgs_from_tasks[task]

    def set_receive_flag_to_false(self):
        self.calculate_bids_flag = False


class PhaseTwoPlayer(PlayerAlgorithm):
    def __init__(self, agent_simulator, t_now, future_utility_function, is_with_timestamp, ro=1):
        PlayerAlgorithm.__init__(self, agent_simulator, t_now=t_now, is_with_timestamp=is_with_timestamp)
        self.fisher_entity = FisherPlayerASY(agent_simulator, t_now, future_utility_function, is_with_timestamp,ro)
        self.is_phase_2 = False



class FisherTaskASY(TaskAlgorithm):
    def __init__(self, agent_simulator: TaskSimple, t_now, is_with_timestamp):
        TaskAlgorithm.__init__(self, agent_simulator, t_now=t_now,is_with_timestamp=is_with_timestamp)
        if not isinstance(agent_simulator, TaskSimple):
            raise Exception("wrong type of simulation entity")

        self.potential_players_ids_list = []
        self.reset_potential_players_ids_list()

        self.bids = {}
        self.reset_bids()

        self.x_jk = {}
        self.reset_x_jk()

        self.msgs_from_players = {}
        self.reset_msgs_from_players()

        self.calculate_xjk_flag = False
        self.price_t_minus = {}
        self.price_current = {}
        self.price_delta = {}
        for mission in self.simulation_entity.missions_list:
            self.price_t_minus[mission] = 0
            self.price_current[mission] = 0
            self.price_delta[mission] = 0

    def reset_additional_fields(self):
        self.reset_potential_players_ids_list()
        self.reset_bids()
        self.reset_x_jk()
        self.reset_msgs_from_players()
        self.calculate_xjk_flag = False
        for mission in self.simulation_entity.missions_list:
            self.price_t_minus[mission] = 0
            self.price_current[mission] = 0
            self.price_delta[mission] = 0

    def reset_msgs_from_players(self):
        self.msgs_from_players = {}
        for player_id in self.potential_players_ids_list:
            self.msgs_from_players[player_id] = None

    def reset_x_jk(self):
        self.x_jk = {}
        for mission in self.simulation_entity.missions_list:
            self.x_jk[mission] = {}
            for n_id in self.potential_players_ids_list:
                self.x_jk[mission][n_id] = None

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
        if self.msgs_from_players[player_id] is None:
            return 0
        else:
            return self.msgs_from_players[player_id].timestamp

    def update_message_in_context(self, msg):
        player_id = msg.sender
        for mission, bid in msg.information.items():
            if mission not in self.bids:
                self.bids[mission] = {}
            self.bids[mission][player_id] = bid

        self.msgs_from_players[player_id] = msg

    def get_is_going_to_compute_flag(self):
        return self.calculate_xjk_flag

    def compute(self):

        self.price_t_minus = self.price_current
        self.price_current = self.calculate_price()
        for mission in self.simulation_entity.missions_list:
            self.price_delta[mission] = math.fabs(self.price_t_minus[mission] - self.price_current[mission])
        for mission in self.simulation_entity.missions_list:
            for player_id, bid in self.bids[mission].items():
                self.atomic_counter = self.atomic_counter + 1
                if self.bids[mission][player_id] is not None and self.price_current[mission] != 0:
                    self.x_jk[mission][player_id] = bid / self.price_current[mission]
                else:
                    self.x_jk[mission][player_id] = None
        self.check_if_x_jk_per_mission_is_one()
        #print(self.x_jk)

    def check_if_x_jk_per_mission_is_one(self):
        ans = {}
        for mission in self.simulation_entity.missions_list:
            ans[mission] = 0
        for mission in self.simulation_entity.missions_list:
            for player_id, bid in self.bids[mission].items():
                self.atomic_counter = self.atomic_counter + 1
                if self.bids[mission][player_id] is not None and self.price_current[mission] != 0:
                    ans[mission] = ans[mission]+ self.x_jk[mission][player_id]
                else:
                    pass
        for mission, sum_x_jk in ans.items():
            if  not 0.999<sum_x_jk <= 1.001:
                if sum_x_jk!=0:
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
            info = {}
            flag = False
            for mission in self.simulation_entity.missions_list:
                x_ijk = self.x_jk[mission][n_id]
                if x_ijk != 0:
                    flag = True
                info[mission] = x_ijk

            if flag:
                is_perfect_com = False
                if self.simulation_entity.player_responsible.id_ == n_id:
                    is_perfect_com = True
                msg = Msg(sender=self.simulation_entity.id_, receiver=n_id, information=info,
                          is_with_perfect_communication=is_perfect_com)
                ans.append(msg)
        return ans

    def is_identical_context(self, msg: Msg):
        sender = msg.sender
        last_msg_from_sender = self.get_last_msg_of_sender(sender)
        if last_msg_from_sender is None:
            return False
        info_from_last_msg = last_msg_from_sender.information

        for mission_id, x_ijk in msg.information.items():
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


class FisherAsynchronousSolver(AllocationSolverTasksPlayersSemi):
    def __init__(self, mailer=None, f_termination_condition=None, f_global_measurements=None,
                 f_communication_disturbance=default_communication_disturbance, future_utility_function=None,
                 is_with_timestamp = True, ro = 1):
        AllocationSolverTasksPlayersSemi.__init__(self, mailer, f_termination_condition, f_global_measurements,
                                                  f_communication_disturbance)
        self.ro = ro
        self.future_utility_function = future_utility_function
        self.is_with_timestamp = is_with_timestamp

    def create_algorithm_task(self, task: TaskSimple):
        return FisherTaskASY(agent_simulator=task, t_now=self.tnow,is_with_timestamp = self.is_with_timestamp)

    def create_algorithm_player(self, player: PlayerSimple):
        return FisherPlayerASY(agent_simulator=player, t_now=self.tnow,
                               future_utility_function=self.future_utility_function,is_with_timestamp = self.is_with_timestamp, ro = self.ro)
