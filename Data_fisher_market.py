from Allocation_Solver_Abstract import PlayerAlgorithm, TaskAlgorithm
from Simulation import PlayerSimple


def get_specified_type_agent(agents_algorithm, type_agent):
    ans = []
    for agent in agents_algorithm:
        if isinstance(agent,type_agent):
           ans.append(agent)
    return  ans


def get_algo_task(tasks_algorithm, task_simulation):
    for t_algo in tasks_algorithm:
        if t_algo.simulation_entity.id_ == task_simulation.id_:
            return t_algo


def calculate_sum_R_X(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm,PlayerAlgorithm)
    tasks =  get_specified_type_agent(agents_algorithm,TaskAlgorithm)
    ri_xi_list = []
    ri_xi = 0
    for player in players:
        for task_simulation in player.tasks_log:
            task_algo = get_algo_task(tasks,task_simulation)
            for mission in task_simulation.missions_list:
                r_ijk_util = player.r_i[task_simulation][mission]
                r_ijk = r_ijk_util.get_utility()
                x_ijk = task_algo.x_jk[mission][player.simulation_entity.id_]
                try: ri_xi+=r_ijk*x_ijk
                except: pass
        ri_xi_list.append(ri_xi)
    return sum(ri_xi_list)

def calculate_sum_R_X_pov(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    ri_xi_list = []
    ri_xi = 0
    for player in players:
        for task in player.tasks_log:
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

def get_player_id_(player:PlayerSimple):
    return player.simulation_entity.id_


def get_single_player(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerAlgorithm)
    sorted(players, key=get_player_id_)
    if len(players)!=0:
        return players[0]


def calculate_single_R_X_player(agents_algorithm):

    single_player = get_single_player(agents_algorithm)
    tasks =  get_specified_type_agent(agents_algorithm,TaskAlgorithm)

    if single_player == None:
        return 0
    ri_xi = 0
    for task_simulation in single_player.tasks_log:
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


def get_data_fisher():
    ans = {}
    ans["Sigma RiXi"] = calculate_sum_R_X
    ans["Sigma RiXi pov"] = calculate_sum_R_X_pov
    ans["Single Sigma RiXi"] = calculate_single_R_X_player
    ans["Single Sigma RiXi pov"] = calculate_single_R_X_player_pov
    return ans

