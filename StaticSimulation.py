import math
import random
import matplotlib.pyplot as plt

from Allocation_Solver_Fisher import FisherAsynchronousSolver
from Data_fisher_market import get_data_fisher
from TaskStaticGenerator import SingleTaskStaticPoliceGenerator, SingleTaskGeneratorTSG

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
    def __init__(self, rep_number, solver: AllocationSolver, players_required_ratio=1.5,
                 create_ability_dict=create_ability_dict):
        self.create_ability_dict = create_ability_dict
        self.players_required_ratio = players_required_ratio
        self.rand = random.Random(rep_number * 17)
        self.seed_number = rep_number
        self.solver = solver
        self.map = MapHubs(seed=self.seed_number * 1717, number_of_centers=3, sd_multiplier=0.05)
        self.tasks_per_center = 3

        self.tasks = []
        self.create_tasks()
        self.draw_tasks() # show map of tasks location for debug

        self.players = []
        self.create_players_and_allocations()


    def add_solver (self,solver:AllocationSolver):
        self.solver = solver
        task_arrive = SingleTaskStaticPoliceGenerator(rand=self.rand, map=self.map,
                                                      create_ability_dict=self.create_ability_dict).random_task
        self.tasks.append(task_arrive)
        for task in self.tasks:
            find_responsible_agent(task = task, players = self.players)

        for player in self.players:
            self.solver.add_player_to_solver(player)

        self.solver.add_task_to_solver(task_arrive)
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


    def draw_tasks(self):
        x = []
        y = []
        importance = []
        name = []
        type_ = []

        for t in self.tasks:
            x.append(t.location[0])
            y.append(t.location[1])
            # importance.append(t.importance)
            #name.append(t.name)
            type_.append("task")

        for cent in self.map.centers_location:
            x.append(cent[0])
            y.append(cent[1])
            # importance.append(t.importance)
            #name.append("center")
            type_.append("center")

        df = pd.DataFrame(dict(x=x, y=y, type_=type_))

        fig, ax = plt.subplots()

        colors = {'center': 'red', 'task': 'blue'}

        ax.scatter(df['x'], df['y'], c=df['type_'].map(colors))

        # plt.scatter(x, y, color='black')
        plt.xlim(0, self.map.width)
        plt.ylim(0, self.map.length)
        plt.show()

    def create_players_and_allocations(self):
        number_players_required = self.get_number_of_tasks_required()
        number_of_players = math.floor(self.players_required_ratio * number_players_required)
        self.tasks = sorted(self.tasks, key=get_task_importance, reverse=True)
        self.create_allocation_dict_greedy(number_of_players)
        if number_of_players>len(self.players):
            self.allocate_extra_agents_to_centers(number_of_players)
        self.add_abilities_to_players()

    def allocate_extra_agents_to_centers(self,number_of_players):
        amount_players_left = number_of_players-len(self.players)
        centers = self.map.centers_location
        while amount_players_left>0:
            for center in centers:
                if amount_players_left>0: return
                amount_players_left=-1

    def add_abilities_to_players(self):
        abilities_dict = create_ability_dict({})
        abilities_list = []
        for ability in abilities_dict.values():
            abilities_list.append(ability)

        for player in self.players:
            abilities_selected = self.rand.choices(abilities_list, k=2)
            abilities_to_add = []
            for ability in abilities_selected:
                if not ability in player.abilities:
                    abilities_to_add.append(ability)
            for ability in abilities_to_add:
                player.abilities.append(ability)
            if not AbilitySimple(0, "Basic") in player.abilities:
                player.abilities.append(AbilitySimple(0, "Basic"))

    def get_number_of_tasks_required(self):
        ans = 0
        for task in self.tasks:
            for mission in task.missions_list:
                ans += mission.max_players
        return ans

    def create_allocation_dict_greedy(self, number_of_players):
        allocation = {}
        for task in self.tasks:
            allocation[task] = {}
            for mission in task.missions_list:
                allocation[task][mission] = []

        for task, dic_m_list in allocation.items():
            task_location = task.location
            for mission, m_list in dic_m_list.items():
                ability = mission.abilities
                max_players = mission.max_players
                while number_of_players != 0 and max_players != 0:
                    player = PlayerSimple(id_=rand_id_str(self.rand), location=task_location,
                                          speed=0.013889, status=Status.ON_MISSION, abilities=[ability])
                    self.players.append(player)
                    m_list.append(player)
                    player.current_mission = mission
                    player.current_task = task
                    mission.players_allocated_to_the_mission.append(player)
                    number_of_players -= 1
                    max_players -= 1
        return allocation


def f_termination_condition_constant_mailer_nclo(agents_algorithm, mailer,
                                                 termination_time_constant_input=termination_time_constant):
    if mailer.time_mailer.get_clock() < termination_time_constant_input:
        return False
    return True


if __name__ == '__main__':

    fisher_solver = FisherAsynchronousSolver(f_termination_condition=f_termination_condition_constant_mailer_nclo,
                                             f_global_measurements=get_data_fisher,
                                             f_communication_disturbance=default_communication_disturbance)

    for i in range(simulation_reps):
        ss = SimulationStatic(rep_number=i, solver=None)


        ss.add_solver( fisher_solver)
        fisher_solver.solve()
        print(3)
