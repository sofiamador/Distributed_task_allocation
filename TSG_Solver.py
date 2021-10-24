import enum
import uuid

from Simulation import MissionSimple, TaskSimple, AbilitySimple, PlayerSimple

import math

# --------------- Parameters ---------------

initial_score_multiplier = 1
interruption_coefficient = 300
late_finish_coefficient = interruption_coefficient
penalty_team_ratio_weight = 200
ro_for_fisher = 0.9
remaining_working_time_threshold = 0.25
distance_penalty = 1
time_of_abandonment = 0.55


class Status(enum.Enum):
    IDLE = 0
    TOTAL_RESTING = 1  # can be disturbed
    RESTING = 2
    HANDLING_WITH_A_MISSION = 6


def calculate_how_many_time_intervals_in_hours(time):
    time_in_minutes = time * 60
    reminder = time_in_minutes % 30
    time_in_minutes = time_in_minutes - reminder
    time_interval = math.floor(time_in_minutes / 30)
    return time_interval


def transform_time_to_RPM_time_interval(time):
    time_in_minutes = time
    reminder = time_in_minutes % 30
    time_in_minutes = time_in_minutes - reminder
    time_interval = math.floor(time_in_minutes / 30)
    if time_interval < 1:
        time_interval = 1
    if time_interval > 12:
        time_interval = 12

    return time_interval


class Casualty(object):
    """ class that for RPM calculation"""

    # ##-------------------Constructor-------------------------------------------------------------------------##

    def __init__(self, initial_RPM):
        # ##---------------Decrease parameters before threshold--------------------------------------------------##

        self.initialRPM = initial_RPM
        self.RPM_survival_care_time_df = None
        self.initialize_survival_table()
        self.initialSurvivalProbability = self.get_updated_survival_probability(updated_RPM=initial_RPM)
        self.initialCartTime = self.get_updated_care_time(updated_RPM=initial_RPM)
        self.RPM_before_threshold = None
        self.survival_probability_before_threshold = None
        self.care_time_before_threshold = None
        self.RPMdf = None
        self.initialize_RPM_table()

        # ##---------------Decrease parameters before threshold--------------------------------------------------##

        self.RPM_after_threshold = None
        self.survival_probability_after_threshold = None
        self.probability_decrease_after_threshold = 0.03

        # ##---------------Debug methods-------------------------------------------------------------------------##

        self.printDebug = False

    # ##-----------------------Penalty Methods----------------------------------------------------------------##

    def calculate_penalty(self):
        RPM_decrease = self.initialRPM - self.RPM_before_threshold
        survival_decrease = self.initialSurvivalProbability - self.survival_probability_before_threshold
        care_time_increase = self.care_time_before_threshold - self.initialCartTime
        penalty = [RPM_decrease, survival_decrease, care_time_increase]
        return penalty

    # ##-----------------------Setters----------------------------------------------------------------##

    def get_updated_rpm(self, time_interval, initialRPM):
        row = initialRPM
        col = transform_time_to_RPM_time_interval(time=time_interval)
        updated_RPM = self.RPMdf[row][col]
        return updated_RPM

    def get_updated_survival_probability(self, updated_RPM):
        updated_survival_probability = self.RPM_survival_care_time_df[updated_RPM]
        return updated_survival_probability

    def get_updated_care_time(self, updated_RPM):
        updated_care_time = self.RPM_survival_care_time_df[updated_RPM]
        return updated_care_time

    def get_RPM_from_table(self, row, col):
        returned_RPM = self.RPMdf[row][col]
        return returned_RPM

    def get_updated_rpm_in_intervals_in_hours(self, time_interval, initialRPM):
        row = initialRPM
        col = calculate_how_many_time_intervals_in_hours(time=time_interval)

        if col >= 12:
            col = 11

        updated_RPM = self.RPMdf[row][col]
        return updated_RPM

    def get_updated_survival_in_interval_hours_after_optimal_threshold(self, time_interval, optimal_threshold_survival,
                                                                       probability_decrease_after_threshold):
        number_of_intervals = calculate_how_many_time_intervals_in_hours(time=time_interval)
        current_survival = optimal_threshold_survival - (number_of_intervals * probability_decrease_after_threshold)
        return current_survival

    def get_minimal_survival_probability(self, initial_RPM):
        row = initial_RPM
        col = 11
        minimal_RPM = self.RPMdf[row][col]
        minimal_survival_probability = self.RPM_survival_care_time_df[minimal_RPM]
        return minimal_survival_probability

    def initialize_RPM_table(self):
        RPM_table = {}
        RPM_table[0] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        RPM_table[1] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        RPM_table[2] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        RPM_table[3] = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        RPM_table[4] = [2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        RPM_table[5] = [3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        RPM_table[6] = [4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        RPM_table[7] = [6, 5, 4, 3, 2, 1, 0, 0, 0, 0, 0, 0]
        RPM_table[8] = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0, 0, 0]
        RPM_table[9] = [9, 8, 8, 7, 6, 5, 4, 3, 2, 1, 0, 0]
        RPM_table[10] = [10, 9, 9, 8, 8, 7, 6, 6, 5, 5, 4, 4]
        RPM_table[11] = [11, 11, 10, 10, 9, 8, 8, 7, 7, 6, 6, 5]
        RPM_table[12] = [12, 12, 11, 11, 10, 10, 10, 10, 9, 9, 8, 8]
        self.RPMdf = RPM_table

    def initialize_survival_table(self):
        survival_table = {0: 0.052, 1: 0.089, 2: 0.15, 3: 0.23, 4: 0.35, 5: 0.49, 6: 0.63, 7: 0.75, 8: 0.84, 9: 0.9,
                          10: 0.94, 11: 0.97, 12: 0.98}
        self.RPM_survival_care_time_df = survival_table


class TSGMission(MissionSimple):

    def mission_utility(self):
        pass

    # ##-----------------------------Constructor---------------------------------##

    def __init__(self, agent_type, event_id, mission_id, required_workload, max_number_of_teams,
                 importance, initial_RPM, damage_level_threshold, ratio, mission_creation_time):
        MissionSimple.__init__(self, mission_id=mission_id, initial_workload=required_workload,
                               arrival_time_to_the_system=mission_creation_time,
                               abilities=[AbilitySimple(ability_type=agent_type)],
                               min_players=1, max_players=max_number_of_teams)

        self.event_id = event_id
        self.mission_importance = importance
        self.damage_level_threshold = damage_level_threshold
        self.initial_RPM = initial_RPM
        self.teams_ratio = ratio
        self.workload_done = 0
        self.players_allocated_to_the_mission = []

        self.casualty = Casualty(initial_RPM=self.initial_RPM)
        self.optimal_threshold = self.calculate_optimal_threshold()  # Update for each mission = 0
        self.optimal_threshold_time, self.optimal_threshold_RPM, \
        self.optimal_threshold_survival = self.calculate_optimal_threshold_time_RPM_survival()
        self.current_survival = self.casualty.get_updated_survival_probability(updated_RPM=initial_RPM)

        self.is_passed_optimal_workload = False

        # ##-----------------------------Late Finish Variables----------------------------------------##

        self.probability_decrease_after_threshold = 0.03
        self.optimal_finish = self.initial_workload  # Update for each mission = 0

    # ##------------------------------Methods for strings and equal---------------------------------##
    def __eq__(self, other):
        if type(other) is TSGMission:
            return self.abilities.ability_type == other.agent_type and self.event_id == other.event_id
        return False

    def __hash__(self):
        return self.mission_id.__hash__()

    def __str__(self):
        return "Mission id: " + str(self.mission_id) + ", max agents: " + str(self.max_players)

        # f"Event id:{self.event_id}, required workload:{self.required_workload}," \
        #   f" remaining workload:{self.remaining_workload}" \
        #   f", max agents {self.max_number_of_teams}.\n"

    # def update_remaining_workload(self, time_now, event_last_update_time): #TODO in phase 2 integration
    #
    #     interval_time = time_now - event_last_update_time
    #     if interval_time > 0 and self.mission_ended is False:
    #         for agent in self.agent_on_the_mission:
    #
    #             workload_reduced_by_agent = agent.mission_workload_to_reduce(interval_time=interval_time)
    #             self.remaining_workload = self.remaining_workload - workload_reduced_by_agent
    #             self.workload_done = self.workload_done + workload_reduced_by_agent
    #             if self.remaining_workload <= 0:
    #                 self.mission_ended = True

    def get_number_of_agents_allocated_to_mission(self):
        if self.players_allocated_to_the_mission is None:
            return 0
        return len(self.players_allocated_to_the_mission)

    def evaluate_optimal_threshold_survival_for_number_of_agents(self, number_of_agents, workload_done):

        # Case 1 - We passed the optimal workload and there is not penalty of interruption.
        if self.is_passed_optimal_workload is True:
            return 0

        # Case 2 - The method got 1 agent or 0 agent and will return the survival as if there are no agent from this
        # point of time.
        if number_of_agents <= 0:
            max_penalty = self.casualty.get_minimal_survival_probability(initial_RPM=self.initial_RPM)
            return max_penalty

        # Case 3 - Calculate for the number of agents.
        else:
            remaining_workload_until_threshold = self.optimal_threshold - workload_done
            workload_for_each_agent = remaining_workload_until_threshold / number_of_agents
            time_until_optimal_threshold = workload_for_each_agent
            updated_RPM = self.casualty.get_updated_rpm_in_intervals_in_hours(
                time_interval=time_until_optimal_threshold, initialRPM=self.initial_RPM)
            survival_probability = self.casualty.get_updated_survival_probability(updated_RPM=updated_RPM)
            return survival_probability

    # ##-----------------------------------Fisher-Market Clearing Methods------------------------------##
    def expected_survival_interruption_decrease(self):
        # Phase 1 - Get the number of agents and remaining workload.
        number_of_agents = len(self.players_allocated_to_the_mission)

        # Phase 2 - Get the current_survival and survival at the optimal threshold time
        optimal_threshold_survival = self.optimal_threshold_survival

        # Phase 3 - Calculate the penalty for interruption
        survival_interruption_minus_one_agent = self.evaluate_optimal_threshold_survival_for_number_of_agents(
            number_of_agents=number_of_agents - 1, workload_done=self.initial_workload - self.remaining_workload)
        penalty_for_interruption = optimal_threshold_survival - survival_interruption_minus_one_agent

        return penalty_for_interruption

    def expected_survival_late_finish_decrease(self):

        penalty_for_late_finish = 0

        # Phase 1 - Get the number of agents and remaining workload.
        number_of_agents = len(self.players_allocated_to_the_mission)
        remaining_workload = self.remaining_workload
        workload_done = self.workload_done

        # Phase 2 - Get the current_survival and survival at the optimal threshold time
        current_survival = self.current_survival

        # Phase 3 - Calculate the penalty for late finish
        survival_finish_minus_one_agent = self.evaluate_optimal_finish_survival_for_number_of_agents(
            number_of_agents=number_of_agents - 1, remaining_workload=remaining_workload, workload_done=workload_done)
        penalty_for_late_finish = current_survival - survival_finish_minus_one_agent

        return penalty_for_late_finish

        # Will perform an optimal evaluation of the finish survival probability for a constant number of agents.

    def evaluate_optimal_finish_survival_for_number_of_agents(self, number_of_agents, remaining_workload,
                                                              workload_done):

        # Case 1 - The method got 1 agent or 0 agent and will return the survival as if there are no agent from this point of time.
        if number_of_agents <= 0:
            max_penalty = self.casualty.get_minimal_survival_probability(initial_RPM=self.initial_RPM)
            return max_penalty

        # Case 2 - Did not passed the optimal threshold.
        if not self.is_passed_optimal_workload:

            optimal_threshold_survival = self.evaluate_optimal_threshold_survival_for_number_of_agents(
                number_of_agents=number_of_agents, workload_done=workload_done)
            workload_until_optimal_finish = self.initial_workload - self.optimal_threshold
            workload_per_agent = workload_until_optimal_finish / number_of_agents
            time_to_finish = workload_per_agent
            survival_at_optimal_finish = self.casualty.get_updated_survival_in_interval_hours_after_optimal_threshold(
                time_interval=time_to_finish, optimal_threshold_survival=optimal_threshold_survival,
                probability_decrease_after_threshold=self.probability_decrease_after_threshold)

        # Case 3 - We passed the optimal threshold
        else:

            current_survival = self.current_survival
            workload_per_agent = remaining_workload / number_of_agents
            time_to_finish = workload_per_agent
            survival_at_optimal_finish = self.casualty.get_updated_survival_in_interval_hours_after_optimal_threshold(
                time_interval=time_to_finish, optimal_threshold_survival=current_survival,
                probability_decrease_after_threshold=self.probability_decrease_after_threshold)

        if survival_at_optimal_finish < 0.052:
            survival_at_optimal_finish = 0.052

        return survival_at_optimal_finish

    def calculate_optimal_threshold_time_RPM_survival(self):

        working_time_for_each_agent = self.optimal_threshold / self.max_players
        optimal_threshold_time = working_time_for_each_agent + self.initial_workload
        optimal_threshold_RPM = self.casualty.get_updated_rpm_in_intervals_in_hours(
            time_interval=working_time_for_each_agent, initialRPM=self.initial_RPM)
        optimal_threshold_survival = self.casualty.get_updated_survival_probability(
            updated_RPM=optimal_threshold_RPM)

        return optimal_threshold_time, optimal_threshold_RPM, optimal_threshold_survival

    def calculate_optimal_threshold(self):
        optimal_threshold = self.initial_workload * self.damage_level_threshold  # Gets the required_workload and multiply by a agreed percentage.
        return optimal_threshold  # Store as threshold.


class TSGEvent(TaskSimple):
    def __init__(self, event_id, event_type, damage_level, life_saving_potential,
                 event_creation_time, event_update_time, point, workload, mission_params, tnow):

        # ##------------------------Parameters received from TSG during simulation run-------------------------##
        TaskSimple.__init__(self, id_=event_id, location=point, importance=1, missions_list=[], tnow=event_update_time)

        self.initialRPM = 12
        self.event_type = event_type
        self.damage_level = damage_level
        self.life_saving_potential = life_saving_potential
        self.initial_score = 0
        self.critical_time = None
        self.set_initial_score_and_importance()
        self.event_creation_time = event_creation_time
        self.event_workload = workload
        self.mission_params = mission_params
        self.agents_on_site = []
        self.set_initial_RPM_according_to_life_saving_potential()
        self.triage_classification = self.importance
        self.damage_level_threshold = self.set_damage_level_threshold()

        for ty in mission_params:
            ratio = mission_params[ty]["max_number_of_teams"] / mission_params[1]["max_number_of_teams"]
            m = TSGMission(agent_type=ty, event_id=event_id, mission_id=str(uuid.uuid1()).upper(),
                           required_workload=mission_params[ty]["workload"],
                           max_number_of_teams=mission_params[ty]["max_number_of_teams"],
                           importance=self.importance, initial_RPM=self.initialRPM,
                           damage_level_threshold=self.damage_level_threshold, ratio=ratio,
                           mission_creation_time=self.event_creation_time)
            self.missions_list.append(m)

        # ##-----------------------------Parameters that updates during simulation---------------------------------##
        # TODO in phase 2 integration
        self.first_agent_arrival_time = None  # The time that first agent arrived to the mission

        # ##----------------------------------Measurements Parameters-------------------------------------------##

        self.event_ended = False
        self.penalty_for_late_arrival = 1
        self.optimal_time = 0.5
        if self.first_agent_arrival_time is not None:
            self.calculate_penalty_for_late_arrival(self.first_agent_arrival_time)
        self.initial_ro_coefficient = penalty_team_ratio_weight
        self.ro_coefficient = self.initialize_ro_coefficient()

    # Determine the threshold damage level according to the damage level.
    def set_damage_level_threshold(self):
        damage_level = self.damage_level
        damage_level_threshold = 1
        if damage_level == 1:
            damage_level_threshold = 1
        elif damage_level == 2:
            damage_level_threshold = 0.1
        elif damage_level == 3:
            damage_level_threshold = 0.3
        elif damage_level == 4:
            damage_level_threshold = 0.5
        elif damage_level == 5:
            damage_level_threshold = 0.7

        return damage_level_threshold

    def set_initial_RPM_according_to_life_saving_potential(self):
        initial_RPM = 12
        if self.life_saving_potential == 1:  # For unknown.
            initial_RPM = 12

        elif self.life_saving_potential == 2:  # For high.
            initial_RPM = 11

        elif self.life_saving_potential == 3:  # For medium.
            initial_RPM = 8

        elif self.life_saving_potential == 4:  # For low.
            initial_RPM = 6

        elif self.life_saving_potential == 5:  # For zero.
            initial_RPM = 3
        self.initialRPM = initial_RPM
        # ##------------------------------Methods for equality, strings and prints---------------------------------##

    def __eq__(self, other):
        if type(other) is TSGEvent:
            return self.event_id == other.event_id
        return False

    def __str__(self):
        return f"Event id:{self.event_id}, creation time: {self.event_creation_time}, " \
               f"importance: {self.event_importance}, event location:{self.point}.\n"

    # ##------------------------------Getters--------------------------------------------------##

    def get_mission(self, agent_type):
        for m in self.missions_list:
            if m.agent_type == agent_type:
                return m

    def check_if_missions_workload_ended(self):
        for mission in self.missions_list:
            if mission.is_done is False:
                return False
        self.event_ended = True  # Mark the event has ended.
        return True

    def set_initial_score_and_importance(self):
        if self.life_saving_potential == 1:
            lsp = 0
        elif self.life_saving_potential == 2:
            lsp = 4
        elif self.life_saving_potential == 3:
            lsp = 3
        elif self.life_saving_potential == 4:
            lsp = 2
        elif self.life_saving_potential == 5:
            lsp = 1

        score = (self.damage_level - 1) * lsp + 1
        if score - 1 > 10:
            self.critical_time = 1
            self.importance = 3
        elif score - 1 > 4:
            self.critical_time = 1.5
            self.importance = 2
        else:
            self.critical_time = 2.5
            self.importance = 1
        score *= (self.importance * 100)
        self.initial_score = score

    # penalty for late arrival
    def calculate_penalty_for_late_arrival(self, time_of_first_arrival, update_late_arrival_indicator=True):
        penalty = 0
        if time_of_first_arrival <= self.optimal_time + self.event_creation_time:  # Case 1 - Time of first arrival < Optimal time
            penalty = self.calculate_according_to_phi_one(time_of_first_arrival=time_of_first_arrival,
                                                          flag=update_late_arrival_indicator)

        elif time_of_first_arrival > self.optimal_time + self.event_creation_time and (
                time_of_first_arrival < self.critical_time + self.event_creation_time):  # Case 2 - Time of first arrival > Optimal time and < Critical Time
            penalty = self.calculate_according_to_phi_two(time_of_first_arrival=time_of_first_arrival,
                                                          flag=update_late_arrival_indicator)

        elif time_of_first_arrival > self.critical_time + self.event_creation_time:
            penalty = self.calculate_according_to_phi_three(
                update_late_arrival_indicator)  # Case 3 - Time of first arrival > Optimal time

        if update_late_arrival_indicator:
            self.penalty_for_late_arrival = penalty

        return penalty

    def calculate_according_to_phi_one(self, time_of_first_arrival, flag):

        point_a = (1, 0)  # Insert the first point - Assuming this is a linear function.
        point_b = (0.95, self.optimal_time)  # Insert the second point - Assuming this is a linear function.
        slope = (point_a[0] - point_b[0]) / (point_a[1] - point_b[1])  # Slope calculation.
        n = point_a[0] - (slope * point_a[1])  # Complete the n in y = mx + n linear function.
        time_of_first_arrival = time_of_first_arrival - self.event_creation_time
        penalty = slope * time_of_first_arrival + n
        if flag is True:
            self.penalty_for_late_arrival = penalty
        return penalty

    def calculate_according_to_phi_two(self, time_of_first_arrival, flag):

        point_a = (0.95, self.optimal_time)  # Insert the first point - Assuming this is a linear function.
        point_b = (0.1, self.critical_time)  # Insert the second point - Assuming this is a linear function.
        slope = (point_a[0] - point_b[0]) / (point_a[1] - point_b[1])  # Slope calculation.
        n = point_a[0] - (slope * point_a[1])  # Complete the n in y = mx + n linear function.
        time_of_first_arrival = time_of_first_arrival - self.event_creation_time
        penalty = slope * time_of_first_arrival + n
        if flag is True:
            self.penalty_for_late_arrival = penalty
        return penalty

    def calculate_according_to_phi_three(self, flag):

        penalty = 0.1
        if flag is True:
            self.penalty_for_late_arrival = penalty
        return penalty

    def initialize_ro_coefficient(self):

        return self.initial_ro_coefficient * self.importance


class TSGPlayer(PlayerSimple):
    """ Class that represents an agent"""

    def __init__(self, agent_id, agent_type, last_update_time, point, start_activity_time,
                 start_resting_time, max_activity_time, extra_hours_allowed, min_competence_time, competence_length,
                 is_working_extra_hours, address, status=Status.IDLE, tnow=0):

        # ##------------------------Parameters received from TSG during simulation run-------------------------##

        PlayerSimple.__init__(self, id_=agent_id, location=point, speed=50, status=Status.IDLE,
                              abilities=[AbilitySimple(ability_type=agent_type)], tnow=tnow)
        self.start_activity_time = start_activity_time
        self.start_resting_time = start_resting_time
        self.max_activity_time = max_activity_time
        self.extra_hours_allowed = extra_hours_allowed
        self.min_competence_time = min_competence_time
        self.competence_length = competence_length

        self.overtime_worth = 0.5
        self.status = status
        self.is_working_extra_hours = is_working_extra_hours

        # ##-----------------------------Parameters that updates during simulation---------------------------------##

        self.start_min_resting_time = None
        self.productivity = 1
        self.scheduled_missions = []
        self.current_mission = None
        self.did_agent_start_overtime = False
        self.address = address

    # ##------------------------Methods for change status--------------------------------------------##

    def check_if_agent_is_idle(self):
        if self.status is Status.IDLE:
            return 1
        else:
            return 0

    def check_if_agent_is_resting(self):

        if self.status is Status.RESTING or self.status is Status.RETRO:

            return True

        else:
            return False

    def check_if_agent_is_allocated_to_mission(self):

        if self.status in [Status.HANDLING_WITH_A_MISSION, Status.ON_THE_WAY_TO_THE_MISSION,
                           Status.WORKING_EXTRA_HOURS]:
            return True
        else:
            return False

    def check_if_agent_is_on_the_way_to_mission(self):

        if self.status is Status.ON_THE_WAY_TO_THE_MISSION:
            return 1
        else:
            return 0

    # Returns True if the team is ready to activity
    def can_be_active(self, tnow):
        if tnow - self.start_resting_time > self.min_competence_time:
            return True
        return False

    # ##------------------------Method for time calculations----------------------------------------##

    def time_left_until_end_of_shift(self, Tnow):
        time_left = Tnow - self.start_activity_time
        if time_left < 0:
            print(self.agent_id_, "Logic Error - Time left until end of shift is negative")
        return time_left

    # ##------------------------------Update productivity methods---------------------------------##

    def update_productivity_for_allocation_calculations(self, time_now):

        productivity_after_disturbance = self.update_productivity_after_rest_disturbance(time_now=time_now)
        self.productivity = productivity_after_disturbance
        self.start_activity_time = time_now

    def update_productivity_after_rest_disturbance(self, time_now):

        resting_time_prior_disturbance = time_now - self.start_min_resting_time + self.min_competence_time

        point_a = (6, 0.1)  # Insert the first point - Assuming this is a linear function.
        point_b = (8, 1)  # Insert the second point - Assuming this is a linear function.
        slope = (point_a[1] - point_b[1]) / (point_a[0] - point_b[0])  # Slope calculation.
        n = point_a[1] - (slope * point_a[0])  # Complete the n in y = mx + n linear function.
        productivity_after_disturbance = slope * resting_time_prior_disturbance + n
        return productivity_after_disturbance

    # ##------------------------STR and Equality-------------------------##

    def get_agent_type(self):
        return self.agent_type

    def __eq__(self, other):
        if type(other) is type(TSGPlayer):
            return self.id_ == other.id_
        return False

    def __str__(self):
        return str(self.id_)

        # ##-----------------------------Time calculations Methods---------------------------------##

    def shift_and_overtime_hours_worth(self, time_now):

        hours_worth = self.agent_shift_hours_worth(time_now=time_now)
        overtime_worth = self.agent_overtime_hours_worth(time_now=time_now)

        return hours_worth, overtime_worth

    def shift_and_overtime_hours_left(self, time_now):

        remaining_time_until_end_of_shift = self.calculate_remaining_working_hours_in_shift(time_now=time_now)
        remaining_overtime = self.calculate_remaining_overtime(time_now=time_now)
        return remaining_time_until_end_of_shift, remaining_overtime

    def calculate_remaining_working_hours_in_shift(self, time_now):

        if self.status is Status.RESTING:

            agent_shift_time = self.max_activity_time  # Get the agent duration for the shift.
            agent_remaining_time_until_end_of_shift = agent_shift_time  # Calculate the remaining time during the shift.
            return agent_remaining_time_until_end_of_shift

        else:

            agent_starting_time = self.start_activity_time  # Get the agent start activity time.
            agent_shift_time = self.max_activity_time  # Get the agent duration for the shift.
            agent_remaining_time_until_end_of_shift = agent_starting_time + agent_shift_time - time_now  # Calculate the remaining time during the shift.
            if agent_remaining_time_until_end_of_shift <= 0:  # In case the agent is in its overtime.
                return 0

            return agent_remaining_time_until_end_of_shift

    def calculate_remaining_overtime(self, time_now):

        if self.status is Status.RESTING:

            agent_over_time = self.extra_hours_allowed
            return agent_over_time

        else:

            start_time = self.start_activity_time
            agent_shift_time = self.max_activity_time
            extra_hours_allowed = self.extra_hours_allowed

            remaining_overtime = start_time + agent_shift_time + extra_hours_allowed - time_now

        if remaining_overtime > extra_hours_allowed:  # if the agent is not in overtime yet, will return overtime allowed.

            return extra_hours_allowed

        else:

            return remaining_overtime

    def agent_shift_hours_worth(self, time_now):

        remaining_time_until_end_of_shift = self.calculate_remaining_working_hours_in_shift(time_now=time_now)
        shift_hours_worth = remaining_time_until_end_of_shift * self.productivity
        return shift_hours_worth

    def agent_overtime_hours_worth(self, time_now):

        remaining_time_until_overtime_end = self.calculate_remaining_overtime(time_now=time_now)
        overtime_worth = remaining_time_until_overtime_end * self.productivity * self.overtime_worth
        return overtime_worth

    def mission_workload_to_reduce(self, interval_time):

        workload_reduced_by_agent = 0

        if self.status is Status.HANDLING_WITH_A_MISSION:  # If is handling the mission and not in overtime

            workload_reduced_by_agent = interval_time * self.productivity

        elif self.status is Status.WORKING_EXTRE_HOURS:

            workload_reduced_by_agent = interval_time * self.productivity * self.overtime_worth

        return workload_reduced_by_agent

    def agent_overtime_hours_worth_with_time_interval(self, time_for_overtime):

        overtime_worth = time_for_overtime * self.productivity * self.overtime_worth
        return overtime_worth

    def agent_shift_hours_worth_with_time_interval(self, time_for_shift):

        shift_hours_worth = time_for_shift * self.productivity
        return shift_hours_worth

    def transform_hours_worth_to_shift_time(self, time_interval):

        shift_time = time_interval / self.productivity

        return shift_time

    def transform_overtime_worth_to_overtime_time(self, time_interval):

        overtime_time = time_interval / (self.productivity * self.overtime_worth)

        return overtime_time

    def shift_and_overtime_potential_hours_worth(self):

        shift_hours_potential = self.max_activity_time * self.productivity
        overtime_hours_potential = self.extra_hours_allowed * self.productivity * self.overtime_worth

        return shift_hours_potential, overtime_hours_potential

    def shift_and_overtime_hours_future_worth(self, event, begin_simulation_time):

        event_point = event.point
        travel_time = self.travel_time(a=self.point, b=event_point)
        time_left_for_shift_worth = 0
        overtime_worth = 0

        if begin_simulation_time + travel_time <= self.start_activity_time + self.max_activity_time:

            time_left_for_shift = self.start_activity_time + self.max_activity_time - begin_simulation_time - travel_time
            time_left_for_shift_worth = time_left_for_shift * self.productivity
            overtime_worth = self.extra_hours_allowed * self.productivity * self.overtime_worth
            return time_left_for_shift_worth, overtime_worth

        else:

            time_left_for_shift_worth = None
            overtime_worth = None
            return time_left_for_shift_worth, overtime_worth

    # When agent starts overtime.
    def change_agent_status_to_overtime(self, time_now):
        self.status = Status.WORKING_EXTRA_HOURS
        self.did_agent_start_overtime = True


class Allocations(object):

    # ##-----------------------------Constructor---------------------------------##

    def __init__(self, allocation_id, agent_type, mission_creation_time, last_update_time, mission_status, event_id,
                 agent_id, working_starting_time, working_ending_time):
        self.allocation_id = allocation_id
        self.agent_type = agent_type
        self.mission_creation_time = mission_creation_time
        self.last_update_time = last_update_time
        self.mission_status = mission_status
        self.event_id = event_id
        self.agent_id = agent_id
        self.working_starting_time = working_starting_time
        self.working_ending_time = working_ending_time

    def __eq__(self, other):
        return self.event_id == other.event_id and self.agent_id == other.agent_id
