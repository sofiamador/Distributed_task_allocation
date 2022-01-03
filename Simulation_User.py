import copy
import random
import pandas as pd

from Allocation_Solver_Fisher import FisherAsynchronousSolver_TasksTogether, \
    FisherAsynchronousSolver_TaskLatestArriveInit
from Communication_Protocols import CommunicationProtocolDefault
from Simulation_Abstract import Simulation
from Entity_Generator import SimpleTaskGenerator, SimplePlayerGenerator
from R_ij import calculate_rij_tsg, calculate_rij_abstract
from Simulation_Abstract_Components import MapHubs

simulations_range = range(2)
number_of_centers = 4
map_length = 10
map_width = 10
number_of_players = 10
players_speed = 10
solver_selection = 2  # 1 = all task init # 2= single latest task init
termination_time_constant = 2000
util_structure_levels = 1  # 1-calculated rij, DONT touch was relevant only for static simulation
exp_lambda_parameter = 0.5
time_per_simulation = 20
missions_information = {}
missions_information["Simulation ID"] = []
def f_termination_condition_constant_mailer_nclo(agents_algorithm, mailer,
                                                 termination_time_constant=termination_time_constant):
    if mailer.time_mailer.get_clock() < termination_time_constant:
        return False
    return True


def create_fisher_solver(communication_protocol, ro=0.9, fisher_solver_distribution_level=solver_selection,
                         util_structure_level=util_structure_levels):
    if fisher_solver_distribution_level == 1:
        return FisherAsynchronousSolver_TasksTogether(
            f_termination_condition=f_termination_condition_constant_mailer_nclo,
            f_communication_disturbance=communication_protocol.get_communication_disturbance,
            future_utility_function=calculate_rij_abstract,
            is_with_timestamp=communication_protocol.is_with_timestamp,
            ro=ro, util_structure_level=util_structure_level)

    if fisher_solver_distribution_level == 2:
        return FisherAsynchronousSolver_TaskLatestArriveInit(
            f_termination_condition=f_termination_condition_constant_mailer_nclo,
            f_communication_disturbance=communication_protocol.get_communication_disturbance,
            future_utility_function=calculate_rij_abstract,
            is_with_timestamp=communication_protocol.is_with_timestamp,
            ro=ro, util_structure_level=util_structure_level)


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
    map_ = MapHubs(seed=seed * 17 + 17, number_of_centers=number_of_centers, sd_multiplier=0.05,
                   length_y=map_length, width_x=map_width)
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


for simulation_number in simulations_range:
    print("Start Simulation Number",simulation_number)
    seed,map_,rand_ = get_initial_objects_for_simulation(simulation_number)

    tasks_generator = SimpleTaskGenerator(map_=map_, seed=seed,exp_lambda_parameter=exp_lambda_parameter )  # TaskGeneratorTSG(map_, seed, exp_lambda_parameter=2)
    player_generator = SimplePlayerGenerator(map_=map_, seed=seed,speed=players_speed)

    players_list = create_players(player_generator)
    communication_protocol = CommunicationProtocolDefault("Perfect Communication")
    solver = create_fisher_solver(communication_protocol)
    simulation_created = Simulation(name=str(simulation_number), players_list=players_list, solver=solver,
                                    tasks_generator=tasks_generator, end_time=time_per_simulation, debug_mode=True)

    add_simulation_to_extract_data(simulation_number,simulation_created.finished_tasks_list)

missions_data_frame = pd.DataFrame.from_dict(missions_information)
missions_data_frame.to_csv("first_data_frame.csv", sep=',')