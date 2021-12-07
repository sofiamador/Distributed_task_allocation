from Simulation_Abstract import Simulation, MapHubs
from TaskStaticGenerator import TaskGeneratorTSG


simulations_range = range(100)
number_of_centers = 4
map_length = 90
map_width = 90


for simulation_number in simulations_range:
    seed = simulation_number
    map_ = MapHubs(seed=seed * 1717, number_of_centers=number_of_centers, sd_multiplier=0.05,
                       length_y=map_length, width_x=map_width)

    tasks_generator = TaskGeneratorTSG(map_, seed)
    solver = None
    players_list = None
    name = None




    simulation_created =  Simulation(name, players_list, solver, tasks_generator)