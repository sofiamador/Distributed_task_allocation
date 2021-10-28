import math

from TSG_Solver import TSGPlayer, TSGMission, TSGEvent, late_finish_coefficient, interruption_coefficient


def calc_ratio_utility_for_current_mission(task_entity,mission_entity,player_entity:TSGPlayer):
    current_sar_size = task_entity.get_mission(
        1).get_number_of_agents_allocated_to_mission()  # TODO get number allocated not on mission
    ans = 0
    if player_entity.abilities[0].ability_type == 1:
        if current_sar_size == 0:
            raise Exception()
        elif current_sar_size == 1:
            for m in task_entity.missions_list:
                if m.abilities[0].ability_type != 1:
                    ans += m.teams_ratio
        else:
            for m in task_entity.missions_list:
                if m.abilities[0].ability_type != 1:
                    current_team_size_non_sar = m.get_number_of_agents_allocated_to_mission()
                    if current_team_size_non_sar > 0:  # current_sar_size > 1 and current_ems_size > 0:
                        opt_ratio = m.teams_ratio
                        ans += abs(opt_ratio - (current_team_size_non_sar / current_sar_size - 1)) - abs(
                            opt_ratio - (current_team_size_non_sar / (current_sar_size)))
    else:
        if current_sar_size == 0:
            return -mission_entity.teams_ratio
        else:
            current_team_size_non_sar = mission_entity.get_number_of_agents_allocated_to_mission()
            opt_ratio = mission_entity.teams_ratio
            return abs(opt_ratio - (current_team_size_non_sar - 1 / current_sar_size)) - abs(
                opt_ratio - current_team_size_non_sar / current_sar_size)
    return ans


def calc_distance_penalty(task_entity:TSGEvent,player_entity:TSGPlayer,tnow):

    delta_x = task_entity.location[0]-player_entity.location[0]
    delta_y = task_entity.location[1]-player_entity.location[1]
    quad_distance = math.sqrt(delta_x**2+delta_y**2)
    travel_time = player_entity.speed/quad_distance #speed in km/hr?

    arrive_now = task_entity.calculate_penalty_for_late_arrival(time_of_first_arrival=tnow,
                                                               update_late_arrival_indicator=False)

    arrive_after_travel = task_entity.calculate_penalty_for_late_arrival(time_of_first_arrival=tnow+travel_time,
                                                                         update_late_arrival_indicator=False)

    return 1 - (arrive_now - arrive_after_travel)

def calc_shift_time_worth_ratio(player_entity:TSGPlayer,mission_entity:TSGMission,tnow):
    if player_entity.did_agent_start_overtime:
        if player_entity.current_mission is not None:
            if player_entity.current_mission.mission_id != mission_entity.mission_id:
                return 0

    remaining_time_until_end_of_shift, remaining_overtime = player_entity.shift_and_overtime_hours_worth(tnow)

    remaining_worth = (remaining_time_until_end_of_shift + remaining_overtime)

    shift_hours_potential, overtime_hours_potential = player_entity.shift_and_overtime_potential_hours_worth()
    potential_worth = shift_hours_potential + overtime_hours_potential

    return remaining_worth / potential_worth

def calc_ratio_utility_for_other_missions(task_entity:TSGEvent,mission_entity:TSGMission):
    current_sar_size = task_entity.get_mission(1).get_number_of_agents_allocated_to_mission()
    ans = 0
    if mission_entity.abilities[0].ability_type == 1:
        if current_sar_size == 0:
            for m in task_entity.missions_list:
                if m.abilities[0].ability_type != 1:
                    ans += m.teams_ratio
        if current_sar_size > 0:
            for m in task_entity.missions_list:
                if m.abilities[0].ability_type != 1:
                    current_team_size_non_sar = m.get_number_of_agents_allocated_to_mission()
                    if current_team_size_non_sar > 0:
                        opt_ratio = m.teams_ratio
                        ans += abs(opt_ratio - (current_team_size_non_sar / current_sar_size)) - abs(
                            opt_ratio - (current_team_size_non_sar / (current_sar_size + 1)))
    else:
        current_team_size_non_sar = mission_entity.get_number_of_agents_allocated_to_mission()
        if current_sar_size == 0:
            return 0
        elif current_team_size_non_sar == 0 and current_sar_size > 0:
            return mission_entity.teams_ratio
        else:
            opt_ratio = mission_entity.teams_ratio
            return abs(opt_ratio - (current_team_size_non_sar / current_sar_size)) - abs(
                opt_ratio - (current_team_size_non_sar + 1) / current_sar_size)
    return ans

def calc_interruption_penalty(player_entity:TSGPlayer):
    if player_entity.current_mission is None:
        return 0
    return player_entity.current_mission.expected_survival_interruption_decrease()

def calc_late_finish(player_entity:TSGPlayer):
    if player_entity.current_mission is None:
        return 0

    return player_entity.agent.current_mission.expected_survival_late_finish_decrease()

def calculate_rij_tsg(player_entity :TSGPlayer, mission_entity:TSGMission, task_entity:TSGEvent,
                                                 t_now=0):
    flag = False
    player_abilities_numbers = []
    mission_abilities_numbers = []

    for ability in player_entity.abilities: player_abilities_numbers.append(ability.get_ability_type())
    for ability in mission_entity.abilities: mission_abilities_numbers.append(ability.get_ability_type())

    for player_ability_number in player_abilities_numbers:

        if player_ability_number in mission_abilities_numbers:
           flag = True

    if not flag:
        return 0

    max_util = task_entity.initial_score
    late_arrival_indicator = task_entity.penalty_for_late_arrival  # [0,1]
    distance_penalty = calc_distance_penalty(task_entity=task_entity,player_entity=player_entity,tnow=t_now)  # [0,1]
    productivity = player_entity.productivity  # [0,1] # TODO integration phase 2

    shift_time_ratio = calc_shift_time_worth_ratio(player_entity,mission_entity,t_now)  # TODO cannot be larger then 1
    if shift_time_ratio == 0:
        return 0

    if shift_time_ratio > 1.001 or shift_time_ratio < 0:
        raise ValueError

    w_ratio_penalty = task_entity.ro_coefficient
    if w_ratio_penalty is None:
        w_ratio_penalty = task_entity.initial_ro_coefficient

    if player_entity.current_mission is not None and player_entity.current_mission.mission_id == mission_entity.mission_id:
        ratio_utility = calc_ratio_utility_for_current_mission(task_entity=task_entity,mission_entity=mission_entity,player_entity=player_entity)
    else:
        ratio_utility = calc_ratio_utility_for_other_missions(task_entity=task_entity,mission_entity=mission_entity)  # [0,1]

    if player_entity.current_mission is not None and not mission_entity.is_passed_optimal_workload:
        interruption_penalty = calc_interruption_penalty(player_entity=player_entity)
    else:
        interruption_penalty = 0

    w_late_penalty = late_finish_coefficient
    late_penalty = calc_late_finish(player_entity=player_entity)
    w_interruption_penalty = interruption_coefficient

    abandonment_penalty = w_late_penalty * late_penalty + w_interruption_penalty * interruption_penalty

    ans = max_util * late_arrival_indicator * distance_penalty * productivity * shift_time_ratio + (
            w_ratio_penalty * ratio_utility) - abandonment_penalty

    if ans < 10:
        ans = 10

    return ans
