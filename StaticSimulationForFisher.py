import Allocation_Solver_Abstract

from Simulation import MapHubs, TaskArrivalEvent, TaskGenerator, find_responsible_agent
from Allocation_Solver_Abstract import AllocationSolver

simulation_reps = 100


# maps = create_maps()
# tasks_per_scenario = create_tasks_per_scenario(maps)
# players_per_scenario = create_tasks_per_scenario(tasks_per_scenario)
# new_task_events_per_scenario = create_new_task_events_per_scenario(maps)

class TaskArrivalEventStatic(TaskArrivalEvent):
    def __init__(self, task, players, solver: AllocationSolver):
        self.time = 0
        self.task = task
        self.players = players
        self.solver = solver

    def handle_event(self, simulation):
        find_responsible_agent(task=self.task, agents_list=self.players)
        self.solver.add_task_to_solver(self.task)
        simulation.solve()


class AllocationStaticGenerator:
    """
    create tasks and players and responsible players
    """
    # TODO


class SimulationStatic():
    def __init__(self, rep_number, solver: AllocationSolver, players_required_ratio):
        self.seed_number = rep_number
        self.solver = solver

        # FOR MAP
        number_of_centers = 3
        tasks_per_center = 2
        length_y = 9.0
        width_x = 9.0
        sd_multiplier = 0.5
        # ---------------

        # FOR Task Generator
        abilities = None  # TODO
        max_amount_of_missions = None  # TODO
        mission_class = None  # TODO

        self.map = MapHubs(number_of_centers=number_of_centers, seed=self.seed_number,
                           length_y=length_y, width_x=width_x, sd_multiplier=sd_multiplier)

        self.task_generator = TaskGenerator(map=self.map, seed=self.seed_number, abilities=abilities,
                                            max_amount_of_missions=max_amount_of_missions,
                                            mission_class=mission_class)  # get_next_task

        allocation_generator = AllocationStaticGenerator(seed=self.seed_number, map=self.map,
                                                         task_generator=self.task_generator,
                                                         tasks_per_center=tasks_per_center,
                                                         players_required_ratio=players_required_ratio)

        self.tasks = allocation_generator.tasks
        self.players = allocation_generator.players

        self.solver.add_tasks_list(self.tasks)
        self.solver.add_players_list(self.players)
        self.task_arrive_event = self.create_task_arrival_event()

    def create_task_arrival_event(self):
        task_new = self.task_generator.get_next_task()
        TaskArrivalEventStatic()
