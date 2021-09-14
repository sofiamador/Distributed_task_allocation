from Simulation import MissionSimple, TaskSimple, AbilitySimple

import math


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


class TSGMissionSimple(MissionSimple):

    # ##-----------------------------Constructor---------------------------------##

    def __init__(self, agent_type, event_id, mission_id, required_workload, max_number_of_teams,
                 importance, initial_RPM, damage_level_threshold, ratio, mission_creation_time):
        MissionSimple.__init__(self, mission_id,
                               ability=AbilitySimple(ability_name=agent_type, max_amount=max_number_of_teams),
                               type_=agent_type)

        self.mission_creation_time = mission_creation_time
        self.agent_type = agent_type
        self.event_id = event_id
        self.mission_id = mission_id
        self.required_workload = required_workload
        self.max_number_of_teams = max_number_of_teams
        self.mission_importance = importance
        self.damage_level_threshold = damage_level_threshold
        self.agent_on_the_mission = []
        self.mission_ended = False
        self.initial_RPM = initial_RPM
        self.teams_ratio = ratio
        self.remaining_workload = self.required_workload
        self.workload_done = 0
        self.agents_allocated_to_the_mission = []

        self.casualty = Casualty(initial_RPM=self.initial_RPM)
        self.optimal_threshold = self.calculate_optimal_threshold()  # Update for each mission = 0
        self.optimal_threshold_time, self.optimal_threshold_RPM, \
        self.optimal_threshold_survival = self.calculate_optimal_threshold_time_RPM_survival()
        self.current_survival = self.casualty.get_updated_survival_probability(updated_RPM=initial_RPM)

        self.is_passed_optimal_workload = False

        # ##-----------------------------Late Finish Variables----------------------------------------##

        self.probability_decrease_after_threshold = 0.03
        self.optimal_finish = self.required_workload  # Update for each mission = 0

    # ##------------------------------Methods for strings and equal---------------------------------##
    def __eq__(self, other):
        if type(other) is Mission:
            return self.agent_type == other.agent_type and self.event_id == other.event_id
        return False

    def __hash__(self):
        return self.mission_id.__hash__()

    def __str__(self):
        return "Mission id: " + str(self.mission_id) + ", max agents: " + str(self.max_number_of_teams)

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
        if self.agents_allocated_to_the_mission is None:
            return 0
        return len(self.agents_allocated_to_the_mission)

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
        number_of_agents = len(self.agent_on_the_mission)

        # Phase 2 - Get the current_survival and survival at the optimal threshold time
        optimal_threshold_survival = self.optimal_threshold_survival

        # Phase 3 - Calculate the penalty for interruption
        survival_interruption_minus_one_agent = self.evaluate_optimal_threshold_survival_for_number_of_agents(
            number_of_agents=number_of_agents - 1, workload_done=self.required_workload - self.remaining_workload)
        penalty_for_interruption = optimal_threshold_survival - survival_interruption_minus_one_agent

        return penalty_for_interruption

    def expected_survival_late_finish_decrease(self):

        penalty_for_late_finish = 0

        # Phase 1 - Get the number of agents and remaining workload.
        number_of_agents = len(self.agent_on_the_mission)
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
            workload_until_optimal_finish = self.required_workload - self.optimal_threshold
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

        working_time_for_each_agent = self.optimal_threshold / self.max_number_of_teams
        optimal_threshold_time = working_time_for_each_agent + self.mission_creation_time
        optimal_threshold_RPM = self.casualty.get_updated_rpm_in_intervals_in_hours(
            time_interval=working_time_for_each_agent, initialRPM=self.initial_RPM)
        optimal_threshold_survival = self.casualty.get_updated_survival_probability(
            updated_RPM=optimal_threshold_RPM)

        return optimal_threshold_time, optimal_threshold_RPM, optimal_threshold_survival

    def calculate_optimal_threshold(self):
        optimal_threshold = self.required_workload * self.damage_level_threshold  # Gets the required_workload and multiply by a agreed percentage.
        return optimal_threshold  # Store as threshold.
