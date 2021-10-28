import copy
import math
import random
import matplotlib.pyplot as plt

from Allocation_Solver_Fisher import FisherAsynchronousSolver
from Data_fisher_market import get_data_fisher
from TSG_rij import calculate_rij_tsg
from TaskStaticGenerator import SingleTaskStaticPoliceGenerator, SingleTaskGeneratorTSG, SinglePlayerGeneratorTSG

plt.style.use('seaborn-whitegrid')
import numpy as np
import pandas as pd
from Simulation import MapHubs, TaskArrivalEvent, TaskGenerator, find_responsible_agent, MissionSimple, TaskSimple, \
    AbilitySimple, PlayerSimple, Status
from Allocation_Solver_Abstract import AllocationSolver, default_communication_disturbance

simulation_reps = 100
termination_time_constant = 1000

import string


def rand_id_str(rand):
    ans = ''.join(rand.choices(string.ascii_uppercase + string.digits, k=10))
    return ans




def create_ability_dict(ability_dict):
    ability_dict[0] = AbilitySimple(ability_type=0, ability_name="Basic")
    ability_dict[1] = AbilitySimple(ability_type=1, ability_name="Interview")
    ability_dict[2] = AbilitySimple(ability_type=2, ability_name="First-Aid")
    ability_dict[3] = AbilitySimple(ability_type=3, ability_name="Observe")
    ability_dict[4] = AbilitySimple(ability_type=4, ability_name="Gun")
    return ability_dict




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
    def __init__(self, rep_number, solver: AllocationSolver, players_required_ratio=0.5,
                 create_ability_dict=create_ability_dict):
        self.create_ability_dict = create_ability_dict
        self.players_required_ratio = players_required_ratio
        self.rand = random.Random(rep_number * 17)
        self.seed_number = rep_number
        self.solver = solver
        self.map = MapHubs(seed=self.seed_number * 1717, number_of_centers=1, sd_multiplier=0.05, length_y=90,width_x=90)
        self.tasks_per_center = 2

        self.tasks = []
        self.create_tasks()

        self.players = []
        self.create_players_given_ratio()
        #self.draw_map() # show map of tasks location for debug


    def add_solver (self,solver:AllocationSolver):
        self.solver = solver

        for task in self.tasks:
            find_responsible_agent(task = task, players = self.players)

        for player in self.players:
            self.solver.add_player_to_solver(player)

        for task in self.tasks:
            self.solver.add_task_to_solver(task)

        self.solver.solve(0)

    def create_tasks(self):
        total_number_of_tasks = self.tasks_per_center * len(self.map.centers_location)
        for _ in range(total_number_of_tasks):
            task = SingleTaskGeneratorTSG(rand= self.rand, map_=self.map).random_task
            self.tasks.append(task)


            #SingleTaskStaticPoliceGenerator(rand=self.rand, map=self.map,
                   #                                create_ability_dict=self.create_ability_dict).random_task


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

        colors = {'center': 'red', 'task': 'blue','player':'green'}

        ax.scatter(df['x'], df['y'], c=df['type_'].map(colors))

        # plt.scatter(x, y, color='black')
        plt.xlim(0, self.map.width)
        plt.ylim(0, self.map.length)
        plt.show()

    def create_players_given_ratio(self):
        number_players_required = self.get_number_of_tasks_required()
        number_of_players = math.floor(self.players_required_ratio * number_players_required)
        self.tasks = sorted(self.tasks, key=get_task_importance, reverse=True)
        self.create_players(number_of_players)
        self.set_tasks_neighbors()

    def set_tasks_neighbors(self):
        ids_ = []
        for player in self.players:
            ids_.append(player.id_)
        for task in self.tasks:
            task.create_neighbours_list(ids_)
    def create_players(self,number_of_players,dict_input = {1:14,4:6,8:1}):
        dict_copy = copy.deepcopy(dict_input)
        while number_of_players!=0:

            if self.all_values_are_zero(dict_copy.values()):
                dict_copy = copy.deepcopy(dict_input)
            else:
                for k,v in dict_copy.items():
                    if v!=0:
                        player = SinglePlayerGeneratorTSG( rand = self.rand , map_=self.map, ability_number = k,is_static_simulation=True).rnd_player
                        self.players.append(player)
                        dict_copy[k]=v-1
                        number_of_players-=1
                        if number_of_players==0:
                            break
    def all_values_are_zero(self,values):
        for v in values:
            if v!=0:
                return False
        return True

    def get_number_of_tasks_required(self):
        ans = 0
        for task in self.tasks:
            for mission in task.missions_list:
                ans += mission.max_players
        return ans




def f_termination_condition_constant_mailer_nclo(agents_algorithm, mailer,
                                                 termination_time_constant_input=termination_time_constant):
    if mailer.time_mailer.get_clock() < termination_time_constant_input:
        return False
    return True


if __name__ == '__main__':



    for i in range(simulation_reps):
        ss = SimulationStatic(rep_number=i, solver=None)
        fisher_solver = FisherAsynchronousSolver(f_termination_condition=f_termination_condition_constant_mailer_nclo,
                                                 f_global_measurements=get_data_fisher(),
                                                 f_communication_disturbance=default_communication_disturbance,
                                                 future_utility_function=calculate_rij_tsg)

        ss.add_solver(fisher_solver)
        fisher_solver.solve()
        print(3)
