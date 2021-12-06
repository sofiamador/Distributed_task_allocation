import copy
import random

from Simulation import Simulation, MapHubs
from TaskStaticGenerator import TaskGeneratorTSG, SinglePlayerGeneratorTSG

simulations_range = range(100)
number_of_centers = 4
map_length = 90
map_width = 90
number_of_players = 21*1.5


def all_values_are_zero(values):
    for v in values:
        if v != 0:
            return False
    return True

def create_players( rand_,map_,number_of_players=number_of_players, dict_input={1: 14, 4: 6, 8: 1}):
    ans = []
    dict_copy = copy.deepcopy(dict_input)
    while number_of_players != 0:
        if all_values_are_zero(dict_copy.values()):
            dict_copy = copy.deepcopy(dict_input)
        else:
            for k, v in dict_copy.items():
                if v != 0:
                    player = SinglePlayerGeneratorTSG(rand=rand_, map_=map_, ability_number=k,
                                                      is_static_simulation=True).rnd_player
                    ans.append((player))
                    dict_copy[k] = v - 1
                    number_of_players -= 1
                    if number_of_players == 0:
                        break
        return  ans

for simulation_number in simulations_range:
    seed = simulation_number
    rand_ =  random.Random(seed)

    map_ = MapHubs(seed=seed * 1717, number_of_centers=number_of_centers, sd_multiplier=0.05,
                       length_y=map_length, width_x=map_width)

    tasks_generator = TaskGeneratorTSG(map_, seed)

    solver = None #TODO
    players_list = create_players(rand_,map_)
    name = None #TODO

    simulation_created =  Simulation(name, players_list, solver, tasks_generator)