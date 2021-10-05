import Allocation_Solver_Abstract
from Simulation import MapHubs
from Allocation_Solver_Abstract import AllocationSolver
simulation_reps = 100



#maps = create_maps()
#tasks_per_scenario = create_tasks_per_scenario(maps)
#players_per_scenario = create_tasks_per_scenario(tasks_per_scenario)
#new_task_events_per_scenario = create_new_task_events_per_scenario(maps)

class SimulationStatic():
    def __init__(self, solver: AllocationSolver, rep_number, players_required_ratio,
                 number_of_centers = 3, tasks_per_center = 2,
                 length_y=9.0, width_x=9.0, sd_multiplier=0.5):

        map = MapHubs(number_of_centers=number_of_centers, seed=rep_number,
                                 length_y=length_y, width_x=width_x, sd_multiplier=sd_multiplier)

        self.solver = solver

        allocation_generator = Allocation_Generator(seed = rep_number,map = map,tasks_per_center = tasks_per_center,)

        tasks = allocation_generator.tasks
        players = allocation_generator.players
        task_arrive_event
        self.solver.add_tasks_list(tasks)
        self.solver.add_players_list(players)


