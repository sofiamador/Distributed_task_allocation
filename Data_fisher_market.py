from Allocation_Solver_Abstract import PlayerAlgorithm, TaskAlgorithm
from Simulation_Abstract import PlayerSimple, TaskSimple, MissionSimple


###----All is using---###
def get_specified_type_agent(agents_algorithm, type_agent):
    ans = []
    for agent in agents_algorithm:
        if isinstance(agent, type_agent):
            ans.append(agent)
    return ans

def get_player_id_(player: PlayerSimple):
    return player.simulation_entity.id_


def get_task_id_(task):
    return task.simulation_entity.id_

def get_algo_task(tasks_algorithm, task_simulation):
    for t_algo in tasks_algorithm:
        if t_algo.simulation_entity.id_ == task_simulation.id_:
            return t_algo

def get_single_player(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    sorted(players, key=get_player_id_)
    if len(players) != 0:
        return players[0]

def get_single_task(agents_algorithm):
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    sorted(tasks, key=get_task_id_)
    if len(tasks) != 0:
        return tasks[0]

def init_player_task_mission_dict(players,tasks):
    ans = {}

    for player in players:
        ans[player.simulation_entity] = {}
        for task in tasks:
            ans[player.simulation_entity][task.simulation_entity] = {}

            for mission in task.simulation_entity.missions_list:
                ans[player.simulation_entity][task.simulation_entity][mission] = 0

    return ans

def get_utils_dict(players,tasks):
    ans = init_player_task_mission_dict(players,tasks)
    for player in players:
        with player.cond:
            for task, mission_dict in player.r_i.items():
                for mission, util in mission_dict.items():
                    ans[player.simulation_entity][task][mission] = util.get_utility()
    return ans

def get_allocation_dict_player_view(players,tasks):
    ans = init_player_task_mission_dict(players, tasks)
    for player in players:
        with player.cond:
            for task, mission_dict in player.x_i.items():
                for mission, x_ijk in mission_dict.items():
                    ans[player.simulation_entity][task][mission] = x_ijk
                    if x_ijk == None:
                        ans[player.simulation_entity][task][mission] = 0

    return ans

def get_player_by_id(players, player_id):
    for p in players:
        if p.simulation_entity.id_ == player_id:
            return p

def get_allocation_dict_task_view(players,tasks):
    ans = init_player_task_mission_dict(players, tasks)
    for task in tasks:
        with task.cond:
            for mission, player_id_dict in task.x_jk.items():
                for player_id, x_ijk in player_id_dict.items():
                    player = get_player_by_id(players,player_id)
                    ans[player.simulation_entity][task.simulation_entity][mission] = x_ijk
                    if x_ijk is None:
                        ans[player.simulation_entity][task.simulation_entity][mission] = 0

    return ans

def get_mission_max_req(mission:MissionSimple):
    return mission.max_players

def get_single_mission(agents_algorithm):
    task_algorithm = get_single_task(agents_algorithm)
    missions = task_algorithm.simulation_entity.missions_list
    return task_algorithm, max(missions, key=get_mission_max_req)
###----R_X---###

def calculate_sum_R_X(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    ri_xi_list = []
    ri_xi = 0
    for player in players:
        with player.cond:
            for task_simulation in player.r_i:
                task_algo = get_algo_task(tasks, task_simulation)
                for mission in task_simulation.missions_list:
                    r_ijk_util = player.r_i[task_simulation][mission]
                    r_ijk = r_ijk_util.get_utility()
                    if r_ijk!=0:

                        x_ijk = task_algo.x_jk[mission][player.simulation_entity.id_]
                        if x_ijk is None:
                            pass
                        else:
                            ri_xi += r_ijk * x_ijk



            ri_xi_list.append(ri_xi)
    return sum(ri_xi_list)

def calculate_sum_R_X_pov(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    ri_xi_list = []
    ri_xi = 0
    for player in players:
        with player.cond:
            for task in player.r_i.keys():
                for mission in task.missions_list:

                    r_ijk_util = player.r_i[task][mission]
                    r_ijk = r_ijk_util.get_utility()
                    x_ijk = player.x_i[task][mission]

                    try:
                        ri_xi += r_ijk * x_ijk
                    except:
                        pass

        ri_xi_list.append(ri_xi)
    return sum(ri_xi_list)

def calculate_single_R_X_player(agents_algorithm):
    single_player = get_single_player(agents_algorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)

    if single_player == None:
        return 0
    ri_xi = 0
    with single_player.cond:

        for task_simulation in single_player.r_i.keys():
            task_algo = get_algo_task(tasks, task_simulation)
            for mission in task_simulation.missions_list:
                r_ijk_util = single_player.r_i[task_simulation][mission]
                r_ijk = r_ijk_util.get_utility()
                x_ijk = task_algo.x_jk[mission][single_player.simulation_entity.id_]
                try:
                    ri_xi += r_ijk * x_ijk
                except:
                    pass
    return ri_xi

def calculate_single_R_X_player_pov(agents_algorithm):
    single_player = get_single_player(agents_algorithm)
    if single_player == None:
        return 0
    ri_xi = 0
    with single_player.cond:

        for task in single_player.tasks_log:
            for mission in task.missions_list:
                r_ijk_util = single_player.r_i[task][mission]
                r_ijk = r_ijk_util.get_utility()
                x_ijk = single_player.x_i[task][mission]
                try:
                    ri_xi += r_ijk * x_ijk
                except:
                    pass
    return ri_xi

###---Envy helpers---###

def calculate_envy (players,tasks,allocation_what_view):
    R_utils_dict = get_utils_dict(players, tasks)
    X_allocation_dict = allocation_what_view(players, tasks)
    players_envy_list = []
    for player_algo in players:
        with player_algo.cond:
            for other_player in players:
                if player_algo.simulation_entity.id_ != other_player.simulation_entity.id_:
                    player_utility_from_allocation_list = []
                    other_utility_from_allocation_list = []

                    for task, mission_dict in player_algo.r_i.items():
                        for mission in mission_dict.keys():
                            r_ijk = R_utils_dict[player_algo.simulation_entity][task][mission]
                            x_ijk = X_allocation_dict[player_algo.simulation_entity][task][mission]
                            x_other_jk = X_allocation_dict[other_player.simulation_entity][task][mission]

                            player_utility_from_allocation_list.append(r_ijk * x_ijk)
                            other_utility_from_allocation_list.append(r_ijk * x_other_jk)
                    player_utility_from_allocation = sum(player_utility_from_allocation_list)
                    other_utility_from_allocation = sum(other_utility_from_allocation_list)

                    if player_utility_from_allocation < other_utility_from_allocation:
                        players_envy_list.append(other_utility_from_allocation - player_utility_from_allocation)
                    else:
                        players_envy_list.append(0)
    return players_envy_list

def calculate_envy_single (single_player,players,tasks,allocation_what_view):
    R_utils_dict = get_utils_dict(players, tasks)
    X_allocation_dict = allocation_what_view(players, tasks)
    players_envy_list = []
    with single_player.cond:
        for other_player in players:
            if single_player.simulation_entity.id_ != other_player.simulation_entity.id_:
                player_utility_from_allocation_list = []
                other_utility_from_allocation_list = []

                for task, mission_dict in single_player.r_i.items():
                    for mission in mission_dict.keys():
                        r_ijk = R_utils_dict[single_player.simulation_entity][task][mission]
                        x_ijk = X_allocation_dict[single_player.simulation_entity][task][mission]
                        x_other_jk = X_allocation_dict[other_player.simulation_entity][task][mission]

                        player_utility_from_allocation_list.append(r_ijk * x_ijk)
                        other_utility_from_allocation_list.append(r_ijk * x_other_jk)
                player_utility_from_allocation = sum(player_utility_from_allocation_list)
                other_utility_from_allocation = sum(other_utility_from_allocation_list)

                if player_utility_from_allocation < other_utility_from_allocation:
                    players_envy_list.append(other_utility_from_allocation - player_utility_from_allocation)
                else:
                    players_envy_list.append(0)
    return players_envy_list

###---Envy functions---###

def calculate_sum_envy_other_player_view(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    players_envy_list = calculate_envy(players,tasks,get_allocation_dict_player_view)
    return sum(players_envy_list)
def calculate_max_envy_other_player_view(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    players_envy_list = calculate_envy(players, tasks, get_allocation_dict_player_view)
    return max(players_envy_list)

def calculate_sum_envy_other_player_view_single(agents_algorithm):
    single_player = get_single_player(agents_algorithm)
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    players_envy_list_single = calculate_envy_single(single_player,players,tasks,get_allocation_dict_player_view)
    return sum(players_envy_list_single)

def calculate_max_envy_other_player_view_single(agents_algorithm):
    single_player = get_single_player(agents_algorithm)

    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    players_envy_list_single = calculate_envy_single(single_player,players, tasks, get_allocation_dict_player_view)
    return max(players_envy_list_single)

def calculate_sum_envy_other_task_view(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    players_envy_list = calculate_envy(players,tasks,get_allocation_dict_task_view)
    return sum(players_envy_list)
def calculate_max_envy_other_task_view(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    players_envy_list = calculate_envy(players, tasks, get_allocation_dict_task_view)
    return max(players_envy_list)
def calculate_sum_envy_other_task_view_single(agents_algorithm):
    single_player = get_single_player(agents_algorithm)
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    players_envy_list_single = calculate_envy_single(single_player,players,tasks,get_allocation_dict_task_view)
    return sum(players_envy_list_single)
def calculate_max_envy_other_task_view_single(agents_algorithm):
    single_player = get_single_player(agents_algorithm)

    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    tasks = get_specified_type_agent(agents_algorithm, TaskAlgorithm)
    players_envy_list_single = calculate_envy_single(single_player,players, tasks, get_allocation_dict_task_view)
    return max(players_envy_list_single)

###---Single Task Price---

def calculate_price_single_task_view(agents_algorithm):
    task_algorithm, mission = get_single_mission(agents_algorithm)
    with task_algorithm.cond:
        return task_algorithm.price_current[mission]

def calculate_price_single_player_view(agents_algorithm):
    task_algorithm, mission = get_single_mission(agents_algorithm)
    players_algorithm = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    ans = 0
    for pa in players_algorithm:
        with pa.cond:
            if task_algorithm.simulation_entity in pa.bids:
                ans += pa.bids[task_algorithm.simulation_entity][mission]
    return ans

###--- bpb---
def calc_sum_sum_bpb(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    ans = 0
    for player in players:
        list_of_allocations = player.allocations_data
        for allocation in list_of_allocations:
            if allocation.measure_ is not None:
                ans+=allocation.measure_
    return ans

def calc_sum_max_bpb(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    ans = []
    for player in players:
        list_of_allocations = player.allocations_data
        temp_list = []
        for allocation in list_of_allocations:
            if allocation.measure_ is not None:
                temp_list.append(allocation.measure_)
        if len(temp_list)==0:
            ans.append(0)
        else:
            ans.append(max(temp_list))
    return sum(ans)

def get_data_fisher():
    ans = {}

    # ---RiXi---
    ans["Sigma RiXi"] = calculate_sum_R_X
    #ans["Sigma RiXi pov"] = calculate_sum_R_X_pov
    #ans["Single Sigma RiXi"] = calculate_single_R_X_player
    #ans["Single Sigma RiXi pov"] = calculate_single_R_X_player_pov

    # ---Envy---
    #ans["Sigma_Envy_Player View"] = calculate_sum_envy_other_player_view
    #ans["Max_Envy_Player View"] = calculate_max_envy_other_player_view
    #ans["Sigma_Envy_Task View"] = calculate_sum_envy_other_task_view
    #ans["Max_Envy_Task View"] = calculate_max_envy_other_task_view


    #ans["Single_Sigma_Envy_Player View"] = calculate_sum_envy_other_player_view_single
    #ans["Single_Max_Envy_Player View"] = calculate_max_envy_other_player_view_single
    #ans["Single_Sigma_Envy_Task View"] = calculate_sum_envy_other_task_view_single
    #ans["Single_Max_Envy_Task View"] = calculate_max_envy_other_task_view_single

    # ---Price---

    #ans["Price_Single_Mission"] = calculate_price_single_task_view
    #ans["Price_Single_Mission_Players_View"] = calculate_price_single_player_view

    # ---bpb
    #ans["Sum BPB"] = calc_sum_sum_bpb
    #ans["Max BPB"] = calc_sum_max_bpb

    return ans


