import copy
import random

from Allocation_Solver_Fisher import FisherAsynchronousSolver_TasksTogether, \
    FisherAsynchronousSolver_TaskLatestArriveInit
from Communication_Protocols import CommunicationProtocolDefault
from Simulation_Abstract import Simulation, MapHubs
from TaskStaticGenerator import TaskGeneratorTSG, SinglePlayerGeneratorTSG
from TSG_rij import calculate_rij_tsg

simulations_range = range(100)
number_of_centers = 4
map_length = 90
map_width = 90
number_of_players = 21
solver_selection = 2 #1 = all task init # 2= single latest task init
termination_time_constant =5000
util_structure_levels = 1 # 1-calculated rij, DONT touch was relevant only for static simulation

def f_termination_condition_constant_mailer_nclo(agents_algorithm, mailer,
                                                 termination_time_constant=termination_time_constant):
    if mailer.time_mailer.get_clock() < termination_time_constant:
        return False
    return True

def create_fisher_solver(communication_protocol,ro=0.9, fisher_solver_distribution_level = solver_selection,
                         util_structure_level = util_structure_levels):

    if fisher_solver_distribution_level == 1:
        return FisherAsynchronousSolver_TasksTogether(
        f_termination_condition=f_termination_condition_constant_mailer_nclo,
        f_communication_disturbance=communication_protocol.get_communication_disturbance,
        future_utility_function=calculate_rij_tsg,
        is_with_timestamp=communication_protocol.is_with_timestamp,
        ro=ro,util_structure_level = util_structure_level)

    if fisher_solver_distribution_level == 2:
        return   FisherAsynchronousSolver_TaskLatestArriveInit(
        f_termination_condition=f_termination_condition_constant_mailer_nclo,
        f_communication_disturbance=communication_protocol.get_communication_disturbance,
        future_utility_function=calculate_rij_tsg,
        is_with_timestamp=communication_protocol.is_with_timestamp,
        ro=ro,util_structure_level = util_structure_level)


#(self, util_structure_level,mailer=None, f_termination_condition=None, f_global_measurements=None,
 #                f_communication_disturbance=default_communication_disturbance, future_utility_function=None,
  #               is_with_timestamp = True, ro = 1,simulation_rep=0):


def all_values_are_zero(values):
    for v in values:
        if v != 0:
            return False
    return True


def create_players(rand_,map_, number_of_players_ = number_of_players , dict_input={1: 14, 4: 6, 8: 1}):
    dict_copy = copy.deepcopy(dict_input)
    players = []
    while number_of_players_ != 0:

        if all_values_are_zero(dict_copy.values()):
            dict_copy = copy.deepcopy(dict_input)
        else:
            for k, v in dict_copy.items():
                if v != 0:
                    player = SinglePlayerGeneratorTSG(rand=rand_, map_=map_, ability_number=k,
                                                      is_static_simulation=True).rnd_player
                    players.append(player)
                    dict_copy[k] = v - 1
                    number_of_players_ -= 1
                    if number_of_players_ == 0:
                        break
    return players


for simulation_number in simulations_range:
    seed = simulation_number
    map_ = MapHubs(seed=seed * 17+17, number_of_centers=number_of_centers, sd_multiplier=0.05,
                       length_y=map_length, width_x=map_width)
    rand_ = random.Random(seed*17+1910)

    tasks_generator = TaskGeneratorTSG(map_, seed, exp_lambda_parameter=2)
    communication_protocol = CommunicationProtocolDefault("Perfect Communication")
    solver = create_fisher_solver(communication_protocol)
    players_list = create_players(rand_,map_)
    name = str(simulation_number)

    simulation_created =  Simulation(name = name, players_list=players_list, solver= solver, tasks_generator=tasks_generator,end_time = 1000,debug_mode=True)
