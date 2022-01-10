import copy
import random
import pandas as pd

from Allocation_Solver_Abstract import TaskAlgorithm
from Allocation_Solver_Fisher import FisherAsynchronousSolver_TasksTogether, \
    FisherAsynchronousSolver_TaskLatestArriveInit, FisherTaskASY, FisherCentralizedSolver
from Communication_Protocols import CommunicationProtocolDefault, CommunicationProtocolExponentialDelayV1, \
    CommunicationProtocolLossDecay
from Simulation_Abstract import Simulation
from Entity_Generator import SimpleTaskGenerator, SimplePlayerGenerator
from R_ij import calculate_rij_tsg, calculate_rij_abstract
from Simulation_Abstract_Components import MapHubs, Entity, calculate_distance, calculate_distance_input_location, \
    MapSimple, CentralizedComputer
is_with_message_loss = True
is_perfect_communication = True
simulations_range = range(1)
number_of_centers = 10
map_length = 10
map_width = 10
number_of_players = 50
players_speed = 5
solver_selection = 3  # 1 = all task init # 2= single latest task init
termination_time_constant = 10000
util_structure_levels = 1  # 1-calculated rij, DONT touch was relevant only for static simulation
exp_lambda_parameters = [0.2]#0.1,0.2,0.25,0.5,0.75,1,1.5,2,2.5,3,3.5,4,4.5,5
time_per_simulation = 10
number_of_initial_tasks = 10
max_number_of_abilities = 1

neighbor_radius_parameter = 3 # neighbor if distance<(map_size/neighbor_radius_parameter)
missions_information = {}
missions_information["Simulation ID"] = []

def get_task_has_mission_with_required_skill(task,agent):
    abilities_in_task = []
    for mission in task.missions_list:
        for ability in mission.abilities:
            abilities_in_task.append(ability)

    for player_ability in agent.abilities:
        if player_ability in abilities_in_task:
            return True
    return False


def determine_neighbor_by_map_radius(task:Entity, agent:Entity):

    #task_has_mission_with_required_skill = get_task_has_mission_with_required_skill(task,agent)
    #if not task_has_mission_with_required_skill:
    #    return False

    distance = calculate_distance(task,agent)
    radius_size = map_length/neighbor_radius_parameter

    ans = distance<radius_size
    ans = True
    return ans

def f_termination_condition_constant_mailer_nclo(agents_algorithm, mailer,
                                                 termination_time_constant=termination_time_constant):
    if mailer.time_mailer.get_clock() < termination_time_constant:
        return False
    return True




def get_have_at_list_one_task_that_converged(tasks):
    for task in tasks:

        if task.is_finish_phase_II:
            return True
    return False



def get_tasks_that_were_out_of_the_market(tasks):
    ans = []
    for task in tasks:
        for msg in task.msgs_from_players.values():
            if msg is not None:
                break
        ans.append(task)
    return ans


def  f_termination_condition_all_tasks_converged_central(current_time,agents_algorithm):
    # TODO take care of only 1 task in system
    if current_time > termination_time_constant:
        return True

    tasks = []
    players = []
    for agent in agents_algorithm:
        if isinstance(agent, FisherTaskASY):
            tasks.append(agent)
        else:
            players.append(agent)

    #
    for task in tasks:
        if not task.is_finish_phase_II and current_time < termination_time_constant:
            return False

    return True


def f_termination_condition_all_tasks_converged(agents_algorithm, mailer,
                                                 termination_time_constant=termination_time_constant):
    # TODO take care of only 1 task in system
    if mailer.time_mailer.get_clock() > termination_time_constant:
        return True

    tasks = []
    players = []
    for agent in agents_algorithm:
        if isinstance(agent,FisherTaskASY):
            tasks.append(agent)
        else:
            players.append(agent)

    #have_at_list_one_task_that_converged = get_have_at_list_one_task_that_converged(tasks)
    #tasks_that_were_out_of_the_market = get_tasks_that_were_out_of_the_market(tasks,players)
    #if have_at_list_one_task_that_converged and len(tasks_that_were_out_of_the_market)>0:
        #for  task in tasks_that_were_out_of_the_market:
            #task.is_finish_phase_II = True
    #if len(tasks)>=2:
    for task in tasks:
        if not task.is_finish_phase_II and mailer.time_mailer.get_clock() < termination_time_constant:
           return False

    return True





def create_fisher_solver(communication_protocol,
                         centralized_computer ,
                         ro=0.9, fisher_solver_distribution_level=solver_selection,
                         util_structure_level=util_structure_levels ):
    if fisher_solver_distribution_level == 1:
        return FisherAsynchronousSolver_TasksTogether(
            f_termination_condition=f_termination_condition_all_tasks_converged,
            f_communication_disturbance=communication_protocol.get_communication_disturbance,
            future_utility_function=calculate_rij_abstract,
            is_with_timestamp=communication_protocol.is_with_timestamp,
            ro=ro, util_structure_level=util_structure_level)

    if fisher_solver_distribution_level == 2:
        return FisherAsynchronousSolver_TaskLatestArriveInit(
            f_termination_condition=f_termination_condition_all_tasks_converged,
            f_communication_disturbance=communication_protocol.get_communication_disturbance,
            future_utility_function=calculate_rij_abstract,
            is_with_timestamp=communication_protocol.is_with_timestamp,
            ro=ro, util_structure_level=util_structure_level)

    if fisher_solver_distribution_level == 3:


        return FisherCentralizedSolver( centralized_computer=centralized_computer,
                                        f_termination_condition=f_termination_condition_all_tasks_converged_central,
        future_utility_function=calculate_rij_abstract,
        is_with_timestamp=None,
        ro=ro, util_structure_level =util_structure_level)

# (self, util_structure_level,mailer=None, f_termination_condition=None, f_global_measurements=None,
#                f_communication_disturbance=default_communication_disturbance, future_utility_function=None,
#               is_with_timestamp = True, ro = 1,simulation_rep=0):


def all_values_are_zero(values):
    for v in values:
        if v != 0:
            return False
    return True


def get_initial_objects_for_simulation(simulation_number):
    seed = simulation_number
    map_ = MapSimple(number_of_centers=number_of_centers,seed=simulation_number)#MapHubs( number_of_centers=number_of_centers, seed=simulation_number,
                    #length_y=map_length, width_x=map_width, sd_multiplier=0.5)


    rand_ = random.Random(seed * 17 + 1910)
    return seed,map_,rand_

def create_players(player_generator):
    ans = []
    for _ in range(number_of_players):
        ans.append(player_generator.get_player())
    return ans

def add_simulation_to_extract_data(simulation_number,finished_tasks):

    for task in finished_tasks:
        for mission in task.done_missions:
            missions_information["Simulation ID"].append(simulation_number)
            mission_dict = mission.measurements.get_mission_measurements_dict()
            for k,v in mission_dict.items():
                if k not in missions_information.keys():
                    missions_information[k] = []
                missions_information[k].append(v)

for exp_lambda_parameter in exp_lambda_parameters:
    for simulation_number in simulations_range:
        print("Start Simulation Number",simulation_number)
        seed,map_,rand_ = get_initial_objects_for_simulation(simulation_number)

        tasks_generator = SimpleTaskGenerator(max_number_of_missions = max_number_of_abilities,map_=map_, seed=seed,exp_lambda_parameter=exp_lambda_parameter )  # TaskGeneratorTSG(map_, seed, exp_lambda_parameter=2)
        player_generator = SimplePlayerGenerator(max_number_of_abilities = max_number_of_abilities,map_=map_, seed=seed,speed=players_speed)

        players_list = create_players(player_generator)

        if is_with_message_loss:
            communication_protocol_for_simulator = CommunicationProtocolLossDecay(3)
            communication_protocol_for_solver = CommunicationProtocolLossDecay(3)

        else:
            communication_protocol_for_simulator = CommunicationProtocolExponentialDelayV1(2)
            communication_protocol_for_solver = CommunicationProtocolExponentialDelayV1(2)

        if is_perfect_communication:
            communication_protocol_for_simulator = CommunicationProtocolDefault("defult")
            communication_protocol_for_solver =CommunicationProtocolDefault("defult")


        communication_protocol_for_solver.set_seed(simulation_number)
        communication_protocol_for_simulator.set_seed(simulation_number*17)

        centralized_computer = CentralizedComputer(map_.get_the_center_of_the_map_location())
        solver = create_fisher_solver(communication_protocol_for_solver,centralized_computer =centralized_computer)


        if solver_selection == 3:
            is_centalized = True
        else:
            is_centalized = False


        simulation_created = Simulation(name=str(simulation_number), players_list=players_list, solver=solver,
                                        tasks_generator=tasks_generator, end_time=time_per_simulation, debug_mode=True,
                                        f_is_player_can_be_allocated_to_task=determine_neighbor_by_map_radius,number_of_initial_tasks = number_of_initial_tasks
                                        ,f_generate_message_delay = communication_protocol_for_simulator.get_communication_disturbance,is_centralized= is_centalized,
                                        center_of_map= map_.get_the_center_of_the_map_location())

        add_simulation_to_extract_data(simulation_number,simulation_created.finished_tasks_list)
        if simulation_number % 5 ==0:
            missions_data_frame = pd.DataFrame.from_dict(missions_information)
            if is_with_message_loss:
                missions_data_frame.to_csv("solver_+"+str(solver_selection)+"_distributed_rate_"+str(exp_lambda_parameter)+"_message_loss_reps_"+str(simulation_number)+".csv", sep=',')
            else:
                missions_data_frame.to_csv("solver_+"+str(solver_selection)+"_distributed_rate_"+str(exp_lambda_parameter)+"_message_delay_"+str(simulation_number)+".csv", sep=',')

    missions_data_frame = pd.DataFrame.from_dict(missions_information)
    if is_with_message_loss:
        missions_data_frame.to_csv("solver_+" + str(solver_selection) + "_distributed_rate_" + str(
            exp_lambda_parameter) + "_message_loss_reps_" + str(simulation_number) + ".csv", sep=',')
    else:
        missions_data_frame.to_csv("solver_+" + str(solver_selection) + "_distributed_rate_" + str(
            exp_lambda_parameter) + "_message_delay_" + str(simulation_number) + ".csv", sep=',')

