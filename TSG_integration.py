# -*- coding: utf-8 -*-
import copy
# import time
import random
import uuid

from TSG_Solver import TSGPlayer, TSGMission, TSGEvent, Allocations, Status

remaining_working_time_threshold = 0.25


def are_neighbours(a, b):
    return True


def get_event_by_id(events_list, id_):
    for e in events_list:
        if e.id_ == id_:
            return e


def get_agent_by_id(agents_list, id_):
    for a in agents_list:
        if a.id_ == id_:
            return a


def create_obj_allocations(allocations_list):
    allocation_obj_lst = []
    for all in allocations_list:
        a = Allocations(allocation_id=all[0], agent_type=all[1], mission_creation_time=all[2], last_update_time=all[3],
                        mission_status=all[4], event_id=all[5], agent_id=all[6],
                        working_starting_time=all[7] / 3600, working_ending_time=all[8] / 3600)
        allocation_obj_lst.append(a)
    return allocation_obj_lst


# Agents creation functions

def create_force_type_data_map(force_type_data):
    force_data = {}
    for t in force_type_data:
        force_data[t[0]] = {"max_activity_time": t[1] / 60, "extra_hours_allowed": t[2] / 60,
                            "min_competence_time": t[3] / 60,
                            "competence_length": t[4] / 60}
    return force_data


def create_agents(agents_list, force_data_map, t_now, host_agent):
    agents_obj_list = []
    agents_id_list = []

    for t in agents_list:
        agent_id = t[0]
        agents_id_list.append(agent_id)
        type_ = t[1]
        last_update_time = t[2] / 3600
        working_hours = t[5]
        resting_hours = t[6]
        address = t[7]

        if address == host_agent:
            status = None
            is_working_extra_hours = False
            if resting_hours > 0 and working_hours > 0:
                raise Exception

            if 0 < resting_hours < force_data_map[type_]["min_competence_time"] or \
                    working_hours >= force_data_map[type_]["max_activity_time"] + force_data_map[type_][
                "extra_hours_allowed"] + remaining_working_time_threshold:
                status = Status.TOTAL_RESTING
                start_activity_time = None
                start_resting_time = t[2] / 3600 - t[6]
            elif force_data_map[type_]["min_competence_time"] <= resting_hours < force_data_map[type_][
                "competence_length"]:
                status = Status.RESTING
                start_activity_time = None
                start_resting_time = t[2] / 3600 - t[6]
            else:
                status = Status.IDLE
                start_activity_time = t[2] / 3600 - t[5]
                start_resting_time = None
                if working_hours >= force_data_map[type_]["max_activity_time"]:
                    is_working_extra_hours = True

            a = TSGPlayer(agent_id=agent_id, agent_type=type_, last_update_time=last_update_time,
                          point=[t[3], t[4]], start_activity_time=start_activity_time,
                          start_resting_time=start_resting_time,
                          max_activity_time=force_data_map[type_]["max_activity_time"],
                          extra_hours_allowed=force_data_map[type_]["extra_hours_allowed"],
                          min_competence_time=force_data_map[type_]["min_competence_time"],
                          competence_length=force_data_map[type_]["competence_length"], status=status,
                          is_working_extra_hours=is_working_extra_hours, address=address, tnow=t_now)

            agents_obj_list.append(a)
    return agents_obj_list, agents_id_list


#   events creation functions

def create_event_params_data_map(event_params):
    events_data = {}
    for t in event_params:
        events_data[(t[0], t[1], t[2])] = {"total_workload": t[3], "mission_params": {}}
        for p in t[4]:
            events_data[(t[0], t[1], t[2])]["mission_params"][p[0]] = {"max_number_of_teams": p[1],
                                                                       "workload": p[1] * p[2]}

    return events_data


def create_events(events_list, event_params_map, agent_ids_list, t_now, host_agent):
    event_obj_list = []
    for t in events_list:
        e = TSGEvent(event_id=t[0], event_type=t[1], damage_level=t[2], life_saving_potential=t[3],importance = t[4],
                     event_creation_time=t[5] / 3600, event_update_time=t[6] / 3600,
                     point=[t[7], t[8]], workload=event_params_map[(t[1], t[2], t[3])]["total_workload"],
                     mission_params=event_params_map[(t[1], t[2], t[3])]["mission_params"], tnow=t_now)
        e.player_responsible = host_agent
        e.neighbours = agent_ids_list
        event_obj_list.append(e)
    return event_obj_list


def update_agents_status_and_missions_workload(agents_obj_list, events_obj_list, allocation_list_, t_now):
    mission = None
    for a in allocation_list_:
        agent = get_agent_by_id(agents_list=agents_obj_list, id_=a.agent_id)
        event = get_event_by_id(events_list=events_obj_list, id_=a.event_id)
        mission = event.get_mission(a.agent_type)
        work_done = 0
        if a.working_starting_time <= t_now <= a.working_ending_time:
            if a.agent_type != agent.agent_type:
                raise Exception
            agent.current_mission = mission
            if agent.status != Status.TOTAL_RESTING:
                agent.status = Status.HANDLING_WITH_A_MISSION
            mission.players_allocated_to_the_mission.append(agent)
            mission.players_allocated_to_the_mission.append(agent)
            work_done = t_now - a.working_starting_time
        elif t_now > a.working_ending_time:
            work_done = a.working_ending_time - a.working_starting_time
        mission.remaining_workload -= work_done
    return


def solve(agent_obj_list, event_obj_list, t_now):
    allocations = []
    for i in range(len(agent_obj_list)):
        agent = agent_obj_list[i]
        event = event_obj_list[i % len(event_obj_list)]
        a = Allocations(allocation_id=uuid.uuid1(), agent_type=agent.abilities[0].ability_type,
                        mission_creation_time=t_now,
                        last_update_time=t_now, mission_status=1, event_id=event.id_,
                        agent_id=agent.id_, working_starting_time=t_now,
                        working_ending_time=t_now + 3600 * random.random())
        for m in event.missions_list:
            if m.abilities[0] == agent.abilities[0]:
                m.add_player(agent,t_now)

        allocations.append(a)
    return allocations
    # FMC_algorithm = SolveFisher(agents_=agent_obj_list, events_=event_obj_list, time_now_=t_now)
    # return FMC_algorithm.first_allocations


def merge_new_and_prev_allocations(new_obj_allocations, old_obj_alloctions):
    for a in new_obj_allocations:
        for old_a in old_obj_alloctions:
            if a == old_a:
                a.allocation_id = old_a.allocation_id
                a.initial_workload = old_a.initial_workload


def create_list_of_tuples_allocations(new_obj_allocations):
    allocations_list = []
    for a in new_obj_allocations:
        tup = (
            a.allocation_id, a.agent_type, a.mission_creation_time * 3600, a.working_ending_time * 3600,
            a.mission_status,
            a.event_id,
            a.agent_id, a.working_starting_time * 3600, a.working_ending_time * 3600)
        allocations_list.append(copy.deepcopy(tup))
    return allocations_list


def calcAllocations(*args, **kwargs):
    # try:
    return calcAllocationsInternal(*args, **kwargs)
    # except Exception as e:
    #    f = open("error.txt","r")
    #    f.write(e)


def print_allocations(event_obj_list):
    for e in event_obj_list:
        print(e.id_, "importance", e.importance)
        for m in e.missions_list:
            agent_l = "{"
            for a in m.players_allocated_to_the_mission:
                agent_l += a.__str__() + ", "
            agent_l += "}"
            print("workload", m.remaining_workload, "max teams", m.max_players, "type", m.abilities[0].ability_type,
                  agent_l)
    print()
    print()


def calcAllocationsInternal(host_agent, agent_list, event_list, allocations_list, event_params, force_type_data,
                            discrete_params):
    # t_now = time.time()/3600
    t_now = event_list[-1][6] / 3600
    # agents creation#
    force_data_map = create_force_type_data_map(force_type_data)  # ok
    agents_obj_list, agent_ids_list = create_agents(agent_list, force_data_map, t_now, host_agent)  # ok

    # mission creation#
    event_params_map = create_event_params_data_map(event_params)  # ok
    event_obj_list = create_events(event_list, event_params_map, agent_ids_list=agent_ids_list, t_now=t_now,
                                   host_agent=host_agent)  # ok

    # update the host agent
    h = get_agent_by_id(agents_obj_list, host_agent)
    # if h is None:
    #     h =  TSGPlayer(agent_id=agent_id, agent_type=type_, last_update_time=last_update_time,
    #                       point=[t[3], t[4]], start_activity_time=start_activity_time,
    #                       start_resting_time=start_resting_time,
    #                       max_activity_time=force_data_map[type_]["max_activity_time"],
    #                       extra_hours_allowed=force_data_map[type_]["extra_hours_allowed"],
    #                       min_competence_time=force_data_map[type_]["min_competence_time"],
    #                       competence_length=force_data_map[type_]["competence_length"], status=status,
    #                       is_working_extra_hours=is_working_extra_hours, address=address, tnow=t_now)
    h.neighbours = agents_obj_list
    h.tasks_responsible = event_obj_list

    #  update missions and agents
    allocation_obj_list = create_obj_allocations(allocations_list)  # ok

    update_agents_status_and_missions_workload(agents_obj_list=agents_obj_list, events_obj_list=event_obj_list,
                                               allocation_list_=allocation_obj_list,
                                               t_now=t_now)
    print_allocations(event_obj_list)
    new_obj_allocations = solve(agents_obj_list, event_obj_list, t_now)
    merge_new_and_prev_allocations(new_obj_allocations=new_obj_allocations, old_obj_alloctions=allocation_obj_list)
    print_allocations(event_obj_list)
    return create_list_of_tuples_allocations(new_obj_allocations)
