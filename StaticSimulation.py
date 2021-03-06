import copy
import math
import random
import matplotlib.pyplot as plt

from Allocation_Solver_Abstract import Mailer
from Allocation_Solver_Fisher import FisherAsynchronousSolver_TasksTogether, FisherAsynchronousSolver_TaskRandInit, \
    FisherCentralizedSolver
from Communication_Protocols import CommunicationProtocol, CommunicationProtocolUniform, CommunicationProtocolDefault, \
    CommunicationProtocolDistanceBaseDelayPois, CommunicationProtocolMessageLossConstant, \
    CommunicationProtocolDistanceBaseMessageLoss, CommunicationProtocolDistanceBaseDelayPoisAndLoss, \
    CommunicationProtocolMessageLossConstantAndUniform, CommunicationProtocolPois, \
    CommunicationProtocolDistanceBaseDelayExp, CommunicationProtocolExp, CommunicationProtocolExponentialDelayV1, \
    CommunicationProtocolLossDecay
from Data_fisher_market import get_data_fisher
from R_ij import calculate_rij_tsg, calculate_rij_abstract
from Entity_Generator import SingleTaskGeneratorTSG, SinglePlayerGeneratorTSG, SimpleTaskGenerator, \
    SimplePlayerGenerator
from Simulation_Abstract_Components import MapHubs, Entity, calculate_distance, MapSimple, CentralizedComputer

plt.style.use('seaborn-whitegrid')
import pandas as pd
from Simulation_Abstract import  TaskArrivalEvent, find_and_allocate_responsible_player, TaskSimple
from Allocation_Solver_Abstract import AllocationSolver
import string

number_of_tasks = None
different_reps_market_bool = None
simulation_reps = None
same_protocol_reps_number = None
which_markets = None
termination_time_constant =2000
map_width = None
map_length = None
data_jumps = None
current_ro = None
fisher_solver_distribution_level = None
util_structure_level = None
simulation_rep = None
process_debug = True
max_number_of_missions = None

def rand_id_str(rand):
    ans = ''.join(rand.choices(string.ascii_uppercase + string.digits, k=10))
    return ans

def determine_neighbor_by_map_radius(task:Entity, agent:Entity):

    #task_has_mission_with_required_skill = get_task_has_mission_with_required_skill(task,agent)
    #if not task_has_mission_with_required_skill:
    #    return False

    distance = calculate_distance(task,agent)
    radius_size = map_length/3

    ans = distance<radius_size
    return ans



class TaskArrivalEventStatic(TaskArrivalEvent):
    def __init__(self, task, players, solver: AllocationSolver):
        self.time = 0
        self.task = task
        self.players = players
        self.solver = solver

    def handle_event(self, simulation):
        self.solver.add_task_to_solver(self.task)
        simulation.solve()


def get_task_importance(task: TaskSimple):
    return task.importance


class SimulationStatic():
    def __init__(self, rep_number, solver: AllocationSolver, map_length, map_width,players_required_ratio=0.5,
                  tasks_per_center=3, number_of_centers=3,players_absolute_number = 2):
        self.players_required_ratio = players_required_ratio
        self.players_absolute_number=players_absolute_number
        self.rand = random.Random(rep_number * 17)

        self.seed_number = rep_number
        self.solver = solver
        self.map = MapHubs(seed=self.seed_number * 1717, number_of_centers=number_of_centers, sd_multiplier=0.1,
                           length_y=map_length, width_x=map_width)
        self.task_generator = SimpleTaskGenerator(map_=self.map, seed=self.seed_number,max_number_of_missions=max_number_of_missions)
        self.tasks_per_center = tasks_per_center

        self.tasks = []
        self.create_tasks()

        self.players = []
        self.players_generator = SimplePlayerGenerator(map_=self.map, seed=self.seed_number,max_number_of_abilities = max_number_of_missions)
        self.create_players_given_ratio()
        #self.draw_map() # show map of tasks location for debug

    def add_solver(self, solver: AllocationSolver):
        self.solver = solver
        for task in self.tasks:
            find_and_allocate_responsible_player(task=task, players=self.players)

        if fisher_solver_distribution_level == 3:

            for player in self.players:
                solver.centralized_computer.update_player_simulation(player)
            #solver.centralized_computer.players_simulation=self.players
            for task in self.tasks:
                solver.centralized_computer.update_task_simulation(task)

                find_and_allocate_responsible_player(task=task, players=self.players)

            #solver.centralized_computer.tasks_simulation=self.tasks

        else:


            for player in self.players:
                self.solver.add_player_to_solver(player)

            for task in self.tasks:
                self.solver.add_task_to_solver(task)

    def create_tasks(self):
        total_number_of_tasks = number_of_tasks#self.tasks_per_center * len(self.map.centers_location)
        for _ in range(total_number_of_tasks):
            task = self.task_generator.get_task(0,True)#SingleTaskGeneratorTSG(rand=self.rand, map_=self.map).random_task
            self.tasks.append(task)


    def draw_map(self):
        x = []
        y = []
        importance = []
        name = []
        type_ = []

        for t in self.tasks:
            x.append(t.location[0])
            y.append(t.location[1])
            type_.append("task")

        for cent in self.map.centers_location:
            x.append(cent[0])
            y.append(cent[1])
            type_.append("center")

        for player in self.players:
            x.append(player.location[0])
            y.append(player.location[1])
            type_.append("player")

        df = pd.DataFrame(dict(x=x, y=y, type_=type_))

        fig, ax = plt.subplots()

        colors = {'center': 'red', 'task': 'blue', 'player': 'green'}

        ax.scatter(df['x'], df['y'], c=df['type_'].map(colors))

        # plt.scatter(x, y, color='black')
        plt.xlim(0, self.map.width)
        plt.ylim(0, self.map.length)
        plt.show()

    def create_players_given_ratio(self):
        number_players_required = self.get_number_of_tasks_required()
        if self.players_absolute_number is not None:
            number_of_players = players_absolute_number
        else:
            number_of_players = math.floor(self.players_required_ratio * number_players_required)

        for _ in range(number_of_players):
            self.players.append(self.players_generator.get_player())
        #self.tasks = sorted(self.tasks, key=get_task_importance, reverse=True)
        #self.create_players(number_of_players)
        self.set_tasks_neighbors()

    def set_tasks_neighbors(self):
        ids_ = []
        for player in self.players:
            ids_.append(player)
        for task in self.tasks:
            task.create_neighbours_list(ids_)

    def create_players(self, number_of_players, dict_input={1: 14, 4: 6, 8: 1}):
        dict_copy = copy.deepcopy(dict_input)
        while number_of_players != 0:

            if self.all_values_are_zero(dict_copy.values()):
                dict_copy = copy.deepcopy(dict_input)
            else:
                for k, v in dict_copy.items():
                    if v != 0:
                        player = SimplePlayerGenerator(rand=self.rand, map_=self.map, ability_number=k,
                                                          is_static_simulation=True).rnd_player
                        self.players.append(player)
                        dict_copy[k] = v - 1
                        number_of_players -= 1
                        if number_of_players == 0:
                            break

    def all_values_are_zero(self, values):
        for v in values:
            if v != 0:
                return False
        return True

    def get_number_of_tasks_required(self):
        ans = 0
        for task in self.tasks:
            for mission in task.missions_list:
                ans += mission.max_players
        return ans

def centralized_constant_clock(current_clock,agents_algorithm = None):
    if current_clock < termination_time_constant:
        return False
    return True

def f_termination_condition_constant_mailer_nclo(agents_algorithm, mailer,
                                                 termination_time_constant=termination_time_constant):
    if mailer.time_mailer.get_clock() < termination_time_constant:
        return False
    return True


def find_relevant_measure_from_dict(nclo, data_map_of_measure):
    while nclo != 0:
        if nclo in data_map_of_measure.keys():
            return data_map_of_measure[nclo]
        else:
            nclo = nclo - 1
    return 0

def get_data_prior_statistic(data_,market_number):
    data_keys = []
    data_keys_t = get_data_fisher().keys()
    for k in data_keys_t:
        data_keys.append(k)

    #mailer_keys = Mailer.get_data_keys()
    #for k in mailer_keys:
    #    data_keys.append(k)

    data_prior_statistic = {}
    flag=False
    for measure_name in data_keys:
        data_prior_statistic[measure_name] = {}
        for nclo in range(0, termination_time_constant, data_jumps):
            data_prior_statistic[measure_name][nclo] = []
            range_measure = None
            if different_reps_market_bool:
                range_measure = len(simulation_reps)
            else:
                range_measure = same_protocol_reps_number
                if isinstance(communication_protocol,  CommunicationProtocolDefault):
                    flag = True

            if not flag:
                for rep in simulation_reps:
                    data_of_rep = data_[rep]
                    data_map_of_measure = data_of_rep[measure_name]
                    the_measure = find_relevant_measure_from_dict(nclo, data_map_of_measure)
                    data_prior_statistic[measure_name][nclo].append(the_measure)
            else:
                data_of_rep = data_[market_number]
                data_map_of_measure = data_of_rep[measure_name]
                the_measure = find_relevant_measure_from_dict(nclo, data_map_of_measure)
                data_prior_statistic[measure_name][nclo].append(the_measure)

    return data_prior_statistic


def calc_avg(data_prior_statistic):
    data_keys = get_data_fisher().keys()
    ans = {}
    for key in data_keys:
        ans[key] = {}
        data_per_nclo = data_prior_statistic[key]
        for nclo, measure_list in data_per_nclo.items():
            ans[key][nclo] = sum(measure_list) / len(measure_list)
    return ans


def organize_data_to_dict(data_prior_statistic):
    ans = {}

    for title, nclo_dict in data_prior_statistic.items():
        nclo_list = []
        for nclo, single_measure in nclo_dict.items():
            nclo_list.append(nclo)
        ans["NCLO"] = nclo_list
        break

    for title, nclo_dict in data_prior_statistic.items():
        measure_list = []
        for nclo, single_measure in nclo_dict.items():
            measure_list.append(single_measure)
        ans[title] = measure_list

    return ans


def organize_data_to_dict_for_avg(data_avg):
    ans = {}

    for title, nclo_dict in data_avg.items():
        nclo_list = []
        for nclo, single_measure in nclo_dict.items():
            nclo_list.append(nclo)
        ans["NCLO"] = nclo_list
        break

    for title, nclo_dict in data_avg.items():
        measure_list = []
        for nclo, single_measure in nclo_dict.items():
            measure_list.append(single_measure)
        ans[title] = measure_list

    return ans

def get_data_last(data_):
    ans = {}
    for measure_name,nclo_dict in data_.items():
        max_nclo = max(nclo_dict.keys())
        ans[measure_name] = nclo_dict[max_nclo]
    return ans


def create_data_statistics(data_,market_number):
    # data_prior_statistic = get_data_prior_statistic(data_)
    # return organize_data_to_dict(data_prior_statistic)

    data_prior_statistic = get_data_prior_statistic(data_,market_number)
    data_avg = calc_avg(data_prior_statistic)
    ans1 = organize_data_to_dict_for_avg(data_avg)
    ans2 = get_data_last(data_prior_statistic)

    return ans1,ans2


def create_data_communication(amount_of_lines):
    protocol_name_list = []
    timestamp_list = []

    for _ in range(amount_of_lines):
        protocol_name_list.append(communication_protocol.name)
        if communication_protocol.is_with_timestamp:
            timestamp_list.append("TS")
        else:
            timestamp_list.append("No_TS")

    ans = {}
    ans["Communication Protocol"] = protocol_name_list
    ans["timestamp"] = timestamp_list
    return ans


def create_fisher_solver(simulation_rep,map:MapSimple,communication_protocol,ro=0.9):
    if fisher_solver_distribution_level == 1:

        return FisherAsynchronousSolver_TasksTogether(
        f_termination_condition=f_termination_condition_constant_mailer_nclo,
        f_global_measurements=get_data_fisher(),
        f_communication_disturbance=communication_protocol.get_communication_disturbance,
        future_utility_function=calculate_rij_abstract,
        is_with_timestamp=communication_protocol.is_with_timestamp,
        ro=ro,util_structure_level = util_structure_level)

    if fisher_solver_distribution_level == 2:
        return FisherAsynchronousSolver_TaskRandInit(
         f_termination_condition=f_termination_condition_constant_mailer_nclo,
         f_global_measurements=get_data_fisher(),
         f_communication_disturbance=communication_protocol.get_communication_disturbance,
         future_utility_function=calculate_rij_abstract,
         is_with_timestamp=communication_protocol.is_with_timestamp,
         ro=ro, util_structure_level =util_structure_level)

    if fisher_solver_distribution_level == 3:
        centralized_computer = CentralizedComputer(location=map.get_the_center_of_the_map_location())

        return FisherCentralizedSolver( centralized_computer=centralized_computer,f_termination_condition=centralized_constant_clock,
        f_global_measurements=get_data_fisher(),
        future_utility_function=calculate_rij_abstract,
        is_with_timestamp=None,
        ro=ro, util_structure_level =util_structure_level)




def create_data_simulation(amount_of_lines, players_required_ratio, tasks_per_center, number_of_centers, algo_name):
    algo_name_list = []
    players_required_ratio_list = []
    tasks_per_center_list = []
    number_of_centers_list = []

    for _ in range(amount_of_lines):
        algo_name_list.append(algo_name)
        players_required_ratio_list.append(players_required_ratio)
        tasks_per_center_list.append(tasks_per_center)
        number_of_centers_list.append(number_of_centers)
    ans = {}
    ans["Algorithm"] = algo_name_list
    ans["Players Required Ratio"] = players_required_ratio_list
    ans["Tasks Per Center"] = tasks_per_center_list
    ans["Number Of Centers"] = number_of_centers_list
    return ans

def get_num_reps(ans2):
    for k, v in ans2.items():
        return len(v)


def create_data_market_number(amount_of_lines1, market_number):
    ans = {}
    temp_list  = []
    if market_number is not None:
        for _ in range(amount_of_lines1):
            temp_list.append(market_number)

    if market_number is not None:
        ans["Market_number"] = temp_list
    return ans


def create_type_solver(amount_of_lines1, type_solver):
    ans = {}
    temp_list = []
    if type_solver is not None:

        if type_solver == 1:
            name_solver = "semi distributed"
        if type_solver == 2:
            name_solver = "full distributed"
        if type_solver == 3:
            name_solver = "centralized"

        for _ in range(amount_of_lines1):
            temp_list.append(name_solver)

    if type_solver is not None:
        ans["Type_Solver"] = temp_list
    return ans


def create_type_util(amount_of_lines, util_structure_level):
    ans = {}
    temp_list = []
    if util_structure_level is not None:

        if util_structure_level == 1:
            name_util = "Structure Util"
        if util_structure_level == 2:
            name_util = "Semi Structure Util"
        if util_structure_level == 3:
            name_util = "rnd Util"

        for _ in range(amount_of_lines):
            temp_list.append(name_util)

    if util_structure_level is not None:
        ans["util_structure_level"] = temp_list
    return ans


def get_data_single_output_dict(data_,market_number = None,type_solver = None):
    ans_avg,ans_last = create_data_statistics(data_, market_number)
    amount_of_lines1 = len(ans_avg["NCLO"])
    if fisher_solver_distribution_level!=3:
        data_communication1 = create_data_communication(amount_of_lines1)
    else:
        data_communication1 ={}
    data_simulation1 = create_data_simulation(amount_of_lines1, players_required_ratio, tasks_per_center,
                                             number_of_centers, algo_name)
    data_market_number1 = create_data_market_number(amount_of_lines1,market_number)
    type_solver1 = create_type_solver(amount_of_lines1,type_solver)
    type_util1 = create_type_util(amount_of_lines1,util_structure_level)



    amount_of_lines2 = get_num_reps(ans_last)

    if fisher_solver_distribution_level != 3:
        data_communication2 = create_data_communication(amount_of_lines2)
    else:
        data_communication2 = {}

    #data_communication2 = create_data_communication(amount_of_lines2)
    data_simulation2 = create_data_simulation(amount_of_lines2, players_required_ratio, tasks_per_center,
                                              number_of_centers, algo_name)
    data_market_number2 = create_data_market_number(amount_of_lines2,market_number)
    type_solver2 = create_type_solver(amount_of_lines2,type_solver)
    type_util2 = create_type_util(amount_of_lines2,util_structure_level)

    data_output1 = {}
    data_output2 = {}


    for k, v in type_util1.items():
        data_output1[k] = v

    for k, v in type_util2.items():
        data_output2[k] = v

    for k, v in type_solver1.items():
        data_output1[k] = v

    for k, v in type_solver2.items():
        data_output2[k] = v


    for k, v in data_market_number1.items():
        data_output1[k] = v

    for k, v in data_simulation1.items():
        data_output1[k] = v

    for k, v in data_communication1.items():
        data_output1[k] = v

    for k, v in ans_avg.items():
        data_output1[k] = v

    for k, v in data_simulation2.items():
        data_output2[k] = v

    for k, v in data_communication2.items():
        data_output2[k] = v

    for k, v in ans_last.items():
        data_output2[k] = v

    for k, v in data_market_number2.items():
        data_output2[k] = v

    return data_output1,data_output2


def create_communication_protocols(is_with_timestamp,perfect_communication,alpha_for_delay,alpha_for_loss,ubs):
                                   #,ubs, constants_for_distances_pois, constants_for_distances_and_loss, p_losses,distance_loss_ratios,p_loss_and_ubs,poises,constants_for_distances_exp,exps):
    ans = []

    # for p_ub in p_loss_and_ubs:
    #     p = p_ub[0]
    #     ub = p_ub[1]
    #     name = "U(0," + str(ub) + "),p_loss"+str(p)
    #     ans.append(CommunicationProtocolMessageLossConstantAndUniform(name=name, is_with_timestamp=is_with_timestamp, p_loss=p,UB=ub))
    #
    # for pois in poises:
    #     name = "pois(" + str(pois) + ")"
    #     ans.append(CommunicationProtocolPois(name=name, is_with_timestamp=is_with_timestamp, lambda_ = pois))
    #
    # for exp in exps:
    #     name = "exp(" + str(exp) + ")"
    #     ans.append(CommunicationProtocolExp(name=name, is_with_timestamp=is_with_timestamp, lambda_=exp))
    #
    #
    for ub in ubs:
        name = "U(0," + str(ub) + ")"
        ans.append(CommunicationProtocolUniform(name=name, is_with_timestamp=is_with_timestamp, UB=ub))
    #
    #
    # for constant_ in constants_for_distances_pois:
    #     name = "Pois(Dij_x" + str(constant_) + ")"
    #     ans.append(CommunicationProtocolDistanceBaseDelayPois(is_with_timestamp=is_with_timestamp, name=name, length=map_length, width=map_width, constant_=constant_))
    #
    #
    # for constant_ in constants_for_distances_exp:
    #     name = "Exp(Dij_x" + str(constant_) + ")"
    #     ans.append(CommunicationProtocolDistanceBaseDelayExp(is_with_timestamp=is_with_timestamp, name=name,
    #                                                           length=map_length, width=map_width, constant_=constant_))
    #
    # for constant_ in constants_for_distances_and_loss:
    #     name = "Pois(Dij_x" + str(constant_) + ") + Distance Loss"
    #     ans.append(CommunicationProtocolDistanceBaseDelayPoisAndLoss(is_with_timestamp=is_with_timestamp, name=name, length=map_length,width=map_width, constant_=constant_))
    #
    # for p_loss in p_losses:
    #     name = "p loss = " + str(p_loss)
    #     ans.append(CommunicationProtocolMessageLossConstant(name=name, is_with_timestamp=False, p_loss=p_loss))

    #
    # for distance_loss_ratio in distance_loss_ratios:
    #     name = "Distance Loss "+str(distance_loss_ratio)
    #
    #     ans.append(CommunicationProtocolDistanceBaseMessageLoss(name=name, is_with_timestamp=False,length=map_length,
    #                                                               width=map_width,distance_loss_ratio=distance_loss_ratio))

    for alpha in alpha_for_delay:
        ans.append(CommunicationProtocolExponentialDelayV1(alpha = alpha,is_with_timestamp=is_with_timestamp))

    for alpha in alpha_for_loss:
        ans.append(CommunicationProtocolLossDecay(alpha, is_with_timestamp=is_with_timestamp,name="distance^alpha"))
    if perfect_communication:
        ans.append(CommunicationProtocolDefault(name="Perfect Communication"))

    return ans


def additions_to_names(file_name1,file_name2, fisher_solver_distribution_level, communication_protocol):
    if fisher_solver_distribution_level == 1:
        file_name1 = file_name1 + "_semi_dist"
        file_name2 = file_name2 + "_semi_dist"
    if fisher_solver_distribution_level == 2:
        file_name1 = file_name1 + "_fully_dist"
        file_name2 = file_name2 + "_fully_dist"

    if util_structure_level ==1:
        file_name1 = file_name1 + "_structure_util"
        file_name2 = file_name2 + "_structure_util"

    if util_structure_level ==2:
        file_name1 = file_name1 + "_semi_structure_util"
        file_name2 = file_name2 + "_semi_structure_util"

    if util_structure_level ==3:
        file_name1 = file_name1 + "_rnd_util"
        file_name2 = file_name2 + "_rnd_util"

    if fisher_solver_distribution_level !=3:
        if communication_protocol.is_with_timestamp:
            file_name1 = file_name1 + "_TS.csv"
            file_name2 = file_name2 + "_TS.csv"
        else:
            file_name1 = file_name1 + "_no_TS.csv"
            file_name2 = file_name2 + "_no_TS.csv"

    else:
        file_name1 = file_name1 + ".csv"
        file_name2 = file_name2 + ".csv"

    return file_name1,file_name2

def run_different_markets(ro,communication_protocol=None):
    data_ = {}
    for i in simulation_reps:#range(simulation_reps):
        simulation_rep = i
        if process_debug:
            print(i)

        scenario = SimulationStatic(rep_number=i, solver=None, map_length=map_length, map_width=map_width,
                              players_required_ratio=players_required_ratio
                              , tasks_per_center=tasks_per_center,  number_of_centers=number_of_centers,players_absolute_number =players_absolute_number)
        if communication_protocol is not None:
            communication_protocol.set_seed(i)

        fisher_solver = create_fisher_solver(communication_protocol=communication_protocol, map=scenario.map,
                                             ro=ro,simulation_rep = simulation_rep)
        scenario.add_solver(fisher_solver)
        if fisher_solver_distribution_level == 3:
            fisher_solver.solve(tnow = 0)

        else:
            fisher_solver.solve(tnow = 0)
        data_[i]= fisher_solver.get_measurements()

    data_single_output_dict1, data_single_output_dict2 = get_data_single_output_dict(data_, type_solver = fisher_solver_distribution_level)

    data_frame1 = pd.DataFrame.from_dict(data_single_output_dict1)

    if fisher_solver_distribution_level!=3:
        file_name1 = "AVG_reps_" + str(simulation_reps) + "_" + algo_name + "_ro_" + str(current_ro) + "_ratio_" + str(
            players_required_ratio) + "_" + communication_protocol.name+ "_termination_"+str(termination_time_constant)

    else:
        file_name1 = "AVG_reps_central" + str(simulation_reps) + "_" + algo_name + "_ro_" + str(current_ro) + "_ratio_" + str(
            players_required_ratio)  + "_termination_" + str(
            termination_time_constant)

    data_frame2 = pd.DataFrame.from_dict(data_single_output_dict2)

    if fisher_solver_distribution_level!=3:

        file_name2 = "Last_reps_" + str(simulation_reps) + "_" + algo_name + "_ro_" + str(
            current_ro) + "_ratio_" + str(players_required_ratio) + "_" + communication_protocol.name+ "_termination_"+str(termination_time_constant)

    else:
        file_name2 = "Last_reps_central" + str(simulation_reps) + "_" + algo_name + "_ro_" + str(
            current_ro) + "_ratio_" + str(
            players_required_ratio)  + "_termination_" + str(
            termination_time_constant)

    file_name1,file_name2 = additions_to_names ( file_name1,file_name2,fisher_solver_distribution_level,communication_protocol)

    data_frame1.to_csv(file_name1, sep=',')
    data_frame2.to_csv(file_name2, sep=',')

    data_output_list_avg.append(data_frame1)
    data_output_list_last.append(data_frame2)


def run_same_market_diff_communication_experiment(communication_protocol,ro):
    data_ = {}
    for market_number in which_markets:


        if isinstance(communication_protocol,CommunicationProtocolDefault):
            scenario = SimulationStatic(rep_number=market_number, solver=None, map_length=map_length,
                                        map_width=map_width,
                                        players_required_ratio=players_required_ratio
                                        , tasks_per_center=tasks_per_center, number_of_centers=number_of_centers)

            fisher_solver = create_fisher_solver(communication_protocol=communication_protocol, map = scenario.map, ro=ro, fisher_solver_distribution_level =fisher_solver_distribution_level)
            scenario.add_solver(fisher_solver)
            fisher_solver.solve()
            data_[market_number] = fisher_solver.get_measurements()

        else:
            for i in range(same_protocol_reps_number):
                scenario = SimulationStatic(rep_number=market_number, solver=None, map_length=map_length,
                                            map_width=map_width,
                                            players_required_ratio=players_required_ratio
                                            , tasks_per_center=tasks_per_center, number_of_centers=number_of_centers)

                if process_debug:
                    print(i)

                communication_protocol.set_seed(i)

                fisher_solver = create_fisher_solver(communication_protocol=communication_protocol, map=scenario.map,
                                                     ro=ro)


                scenario.add_solver(fisher_solver)
                fisher_solver.solve()
                data_[i] = fisher_solver.get_measurements()

        data_single_output_dict1, data_single_output_dict2 = get_data_single_output_dict(data_,
                                                                                         type_solver=fisher_solver_distribution_level)

        data_frame1 = pd.DataFrame.from_dict(data_single_output_dict1)
        file_name1 = "AVG_same_market_" + str(market_number) +  "_reps_" + str(same_protocol_reps_number) + "_" + algo_name + "_ro_" + str(current_ro) + "_ratio_" + str(
            players_required_ratio) + "_" + communication_protocol.name + "_termination_"+str(termination_time_constant)

        data_frame2 = pd.DataFrame.from_dict(data_single_output_dict2)
        file_name2 = "Last_same_market_" + str(market_number) +  "_reps_" + str(same_protocol_reps_number) + "_" + algo_name + "_ro_" + str(current_ro) + "_ratio_" + str(
            players_required_ratio) + "_" + communication_protocol.name+ "_termination_"+str(termination_time_constant)

        file_name1, file_name2 = additions_to_names(file_name1, file_name2, fisher_solver_distribution_level,
                                                    communication_protocol)

        data_frame1.to_csv(file_name1, sep=',')
        data_frame2.to_csv(file_name2, sep=',')

        data_output_list_avg.append(data_frame1)
        data_output_list_last.append(data_frame2)


if __name__ == '__main__':
    fisher_solver_distribution_levels = [2]#[3,2,1]#[1,2] # 1 = semi distributed, 2 = one task distributed, 3 =centralistic
    util_structure_levels = [1]#[1,3]#[1,2,3] # 1-calculated rij, 2-random when importance determines, 3-random completely

    different_reps_market_bool = True
    same_protocol_reps_number = 100
    which_markets = [0,1,2,3]
    simulation_reps = range(100)
    players_absolute_numbers = [2]
    players_required_ratios = []
    tasks_per_center = 1
    number_of_centers = 2
    number_of_tasks =2
    data_jumps = 1
    map_width = 1
    map_length = 1
    algo_name = "FMC_ASY"
    ros = [0.9]
    is_with_timestamp = True #False #False #True
    perfect_communication = False #True  #False
    max_number_of_missions = 1
    alpha_for_delay = []#[0.25,0.5,0.75,1,1.25,1.5,1.75,2,2.25,2.5,2.75,3]
    alpha_for_loss = []#[10,9,8,7,6,5,4,3,2,1]
    ubs = [50,100,150,200,250]#[250,500,750,1000]  # [1000,2000,2500,3000]#[100,250,500, 750][4000,5000,7500,10000]
    #p_losses = []  # [0.1,0.2,0.3,0.4,0.5,0.6,0.7]
    #p_loss_and_ubs = []  # [[0.25,1000]]
    #constants_for_distances_pois = []  # [1000,2000,2500,3000]#[100,250,500, 750][4000,5000,7500,10000]
    #constants_for_distances_and_loss = []  # [500, 1000, 5000]
    #distance_loss_ratios = []  # [1,0.5,0.4,0.3,0.2,0.1]#[0.9,0.8,0.7,0.6]
    #poises = []# [1000,2000,2500,3000]#[100,250,500, 750][4000,5000,7500,10000]

    #constants_for_distances_exp = []# [1000,2000,2500,3000]#[100,250,500, 750][4000,5000,7500,10000]
    #exps=[]# [1000,2000,2500,3000]#[100,250,500, 750][4000,5000,7500,10000]
    communication_protocols = create_communication_protocols(is_with_timestamp,perfect_communication,alpha_for_delay,alpha_for_loss,ubs)

                                                             #ubs, constants_for_distances_pois, constants_for_distances_and_loss, p_losses,distance_loss_ratios,p_loss_and_ubs,poises,constants_for_distances_exp,exps)

    data_output_list_avg = []
    data_output_list_last = []

    for fisher_solver in fisher_solver_distribution_levels:
        fisher_solver_distribution_level = fisher_solver
        for util_structure in util_structure_levels:
            util_structure_level = util_structure

            if len(players_absolute_numbers) == 0:
                players_absolute_number = None

                for players_required_ratio in players_required_ratios:
                    for ro in ros:
                        current_ro = ro
                        if fisher_solver == 3:
                            run_different_markets(ro)
                        else:
                            for communication_protocol in communication_protocols:
                                if process_debug:
                                    print("players_required_ratios =", players_required_ratio, ";", "communication protocol =",
                                          communication_protocol.name)
                                run_different_markets( ro,communication_protocol = communication_protocol,)

            else:
                    for players_absolute_number in players_absolute_numbers:
                        players_required_ratio = None
                        for ro in ros:
                            current_ro = ro
                            if fisher_solver == 3:
                                run_different_markets(ro)
                            else:
                                for communication_protocol in communication_protocols:
                                    if process_debug:
                                        print("players_absolute_number =", players_absolute_number, ";",
                                              "communication protocol =",
                                              communication_protocol.name)
                                    run_different_markets(ro, communication_protocol=communication_protocol, )
                            #if different_reps_market_bool:

                            #else:
                            #    run_same_market_diff_communication_experiment(communication_protocol,ro)


        #data_output1 = pd.concat(data_output_list_avg)
        #data_output2 = pd.concat(data_output_list_last)

        #data_output1.to_csv("avg_"+algo_name + ".csv", sep=',')
        #data_output2.to_csv("last_"+algo_name + ".csv", sep=',')
