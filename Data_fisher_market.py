from Simulation import PlayerSimple


def get_specified_type_agent(agents_algorithm, type_agent):
    ans = []
    for agent in agents_algorithm:
        if isinstance(agent,type_agent):
           ans.append(agent)
    return  ans

def calculate_sum_R_X(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm,PlayerSimple)
    ri_xi_list = []
    ri_xi = 0
    for player in players:
        for task in player.tasks_log:
            for mission in task.missions:
                r_ijk_util = player.r_i[task][mission]
                r_ijk = r_ijk_util.get_utility()
                x_ijk = task.x_jk[mission][player.id_]
                ri_xi+=r_ijk*x_ijk
        ri_xi_list.append(ri_xi)
    return sum(ri_xi_list)

def calculate_sum_R_X_pov(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerSimple)
    ri_xi_list = []
    ri_xi = 0
    for player in players:
        for task in player.tasks_log:
            for mission in task.missions:
                r_ijk_util = player.r_i[task][mission]
                r_ijk = r_ijk_util.get_utility()
                x_ijk = player.x_i[task][mission]
                ri_xi += r_ijk * x_ijk
        ri_xi_list.append(ri_xi)
    return sum(ri_xi_list)

def get_player_id_(player:PlayerSimple):
    return player.id_


def get_single_player(agents_algorithm):
    players = get_specified_type_agent(agents_algorithm, PlayerSimple)
    sorted(players, key=get_player_id_)
    return players[0]

def calculate_single_R_X_player(agents_algorithm):

    single_player = get_single_player(agents_algorithm)
    ri_xi = 0
    for task in single_player.self.tasks_log:
        for mission in task.missions:
            r_ijk_util = single_player.r_i[task][mission]
            r_ijk = r_ijk_util.get_utility()
            x_ijk = task.x_jk[mission][single_player.id_]
            ri_xi += r_ijk * x_ijk
    return ri_xi


def calculate_single_R_X_player_pov(agents_algorithm):
    single_player = get_single_player(agents_algorithm)
    ri_xi = 0
    for task in single_player.self.tasks_log:
        for mission in task.missions:
            r_ijk_util = single_player.r_i[task][mission]
            r_ijk = r_ijk_util.get_utility()
            x_ijk = single_player.x_i[task][mission]
            ri_xi += r_ijk * x_ijk
    return ri_xi


def get_data_fisher():
    ans = {}
    ans["Sigma RiXi"] = calculate_sum_R_X
    ans["Sigma RiXi pov"] = calculate_sum_R_X_pov
    ans["Single Sigma RiXi"] = calculate_single_R_X_player
    ans["Single Sigma RiXi pov"] = calculate_single_R_X_player_pov
    return ans

