import math
from abc import ABC



from Allocation_Solver_Abstract import PlayerAlgorithm, TaskAlgorithm, AllocationSolverTasksPlayersSemi, \
    default_communication_disturbance
from Simulation import Entity, TaskSimple, future_utility, PlayerSimple
from Allocation_Solver_Abstract import Msg,MsgTaskEntity


class Utility:
    def __init__(self, player_entity, mission_entity, task_entity, t_now, ro=1, util=-1):
        self.player_entity = player_entity
        self.mission_entity = mission_entity
        self.task_entity = task_entity
        self.t_now = t_now
        self.ro = ro
        if util == -1:
            self.linear_utility = player_entity.future_utility(mission_entity=self.mission_entity, task_entity=self.task_entity,
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

    def set_receive_flag_to_true_given_msg_after_check(self, msg):
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

        if task_is_new_in_log or task_information_is_updated:
            self.set_single_task_in_x_i(task_in_log)
            self.set_single_task_in_r_i(task_in_log)

            task_id = msg.sender
            self.msgs_from_tasks[task_id] = msg

            dict_missions_xi = msg.information
            task_simulation = msg.task_entity
            for mission, x_ij in dict_missions_xi:
                self.x_i[task_simulation][mission] = x_ij


    def is_task_entity_new_in_log(self, task_entity:TaskSimple):
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
                atomic_counter = atomic_counter + 1
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
                self.atomic_counter = self.atomic_counter + 1

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
        return ans

    def measurements_per_agent(self):
        # TODO
        print("need to complete measurements per agent in FisherPlayerASY")
        pass

    def is_identical_context(self,msg:Msg):
        sender = msg.sender
        last_msg_from_sender = self.get_last_msg_of_sender(sender)
        info_from_last_msg = last_msg_from_sender.information
        for mission_id,x_ijk in msg.information:
            if mission_id not in info_from_last_msg.keys():
                return False
            if info_from_last_msg[mission_id] != x_ijk:
                return False
        return True

    def get_last_msg_of_sender(self,sender):
        for task in self.msgs_from_tasks.keys():
            if sender == task.id_:
                return self.msgs_from_tasks[task]

    def set_receive_flag_to_false(self):
        self.calculate_bids_flag=False

class FisherTaskASY(TaskAlgorithm):
    def __init__(self, agent_simulator:TaskSimple, t_now):
        TaskAlgorithm.__init__(self, agent_simulator, t_now=t_now)
        if not isinstance(agent_simulator,TaskSimple):
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

        self.price_t_minus = 0
        self.price_current = 0
        self.price_delta = 0

    def reset_additional_fields(self):
        self.reset_potential_players_ids_list()
        self.reset_bids()
        self.reset_x_jk()
        self.reset_msgs_from_players()
        self.calculate_xjk_flag = False
        self.price_t_minus = 0
        self.price_current = 0
        self.price_delta = 0

    def reset_msgs_from_players(self):
        self.msgs_from_players = {}
        for player_id in self.potential_players_ids_list:
            self.msgs_from_players[player_id] = None

    def reset_x_jk(self):
        self.x_jk = {}
        for mission in self.simulation_entity.missions:
            self.x_jk[mission] = {}
            for n_id in self.potential_players_ids_list:
                self.x_jk[mission][n_id] = None

    def reset_bids(self):
        self.bids = {}
        for mission in self.simulation_entity.missions:
            self.bids[mission] = {}
            for n_id in self.potential_players_ids_list:
                self.bids[mission][n_id] = None

    def reset_potential_players_ids_list(self):
        self.potential_players_ids_list = []
        for neighbour in self.simulation_entity.neighbours:
            self.potential_players_ids_list.append(neighbour)

    def initiate_algorithm(self):
        self.send_msgs() # will send messages with None to all relevent players

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
        for mission,bid in msg.information:
            self.bids[mission][player_id] = bid

        self.msgs_from_players[player_id] = msg

    def get_is_going_to_compute_flag(self):
        return self.calculate_xjk_flag

    def compute(self):

        self.price_t_minus = self.price_current
        self.price_current = self.calculate_price()
        self.price_delta = math.fabs(self.price_t_minus-self.price_current)
        for mission in self.simulation_entity.missions:
            for player_id,bid in self.bids[mission].items():
                self.atomic_counter = self.atomic_counter+1
                if self.bids[mission][player_id] is not None:
                    self.x_jk[mission][player_id] = self.bids[mission][player_id]/self.price_current
                else:
                    self.x_jk[mission][player_id] = 0

    def calculate_price(self):
        ans = 0
        for mission in self.simulation_entity.missions:
            for bid in self.bids[mission].values():
                self.atomic_counter = self.atomic_counter+1
                ans = ans +bid
        return ans

    def get_list_of_msgs_to_send(self):
        ans = []
        for n_id in self.potential_players_ids_list:
            info = {}
            flag = False
            for mission in self.simulation_entity.missions:
                x_ijk = self.x_jk[mission][n_id]
                if x_ijk != 0:
                    flag = True
                info[mission] = x_ijk

            if flag:
                is_perfect_com = False
                if self.simulation_entity.player_responsible.id_ == n_id:
                    is_perfect_com = True
                msg = Msg(sender=self.simulation_entity.id_,receiver = n_id, information = info,
                          is_with_perfect_communication =is_perfect_com)
                ans.append(msg)
            return ans



    def is_identical_context(self, msg: Msg):
        sender = msg.sender
        last_msg_from_sender = self.get_last_msg_of_sender(sender)

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
        self.calculate_xjk_flag=False

    def measurements_per_agent(self):
        # TODO
        pass

class FisherAsynchronousSolver(AllocationSolverTasksPlayersSemi):
    def __init__(self, mailer=None, f_termination_condition=None, f_global_measurements=None,
                 f_communication_disturbance=default_communication_disturbance):
        AllocationSolverTasksPlayersSemi.__init__(mailer, f_termination_condition, f_global_measurements,
                                             f_communication_disturbance)

    def create_algorithm_task(self, task: TaskSimple):
        return FisherPlayerASY(agent_simulator=task,t_now = self.last_event.time)

    def create_algorithm_player(self, player:PlayerSimple):
        return FisherTaskASY(agent_simulator=player,t_now = self.last_event.time)
