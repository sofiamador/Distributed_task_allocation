import random

#matplotlib inline
import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')
import numpy as np
import pandas as pd

from Simulation import MapHubs, TaskArrivalEvent, TaskGenerator, find_responsible_agent, MissionSimple, TaskSimple, \
    AbilitySimple
from Allocation_Solver_Abstract import AllocationSolver
simulation_reps = 100


import string

def rand_id_str(rand):
    ans =  ''.join(rand.choices(string.ascii_uppercase + string.digits, k = 10))
    return ans

class TaskSimpleStatic(TaskSimple):
    def __init__(self,id_, location, importance, missions, name):
        TaskSimple.__init__(self,id_, location, importance, missions)
        self.name = name

    def __str__(self):
        return self.name

class SingleTaskStaticPoliceGenerator():
    def __init__(self,rand:random.Random,map:MapHubs):
        self.rand = rand
        self.ability_dict={}
        self.create_ability_dict()
        self.location = map.generate_location_gauss_around_center()
        self.index = self.get_random_index_according_to_p_function()
        list_of_tasks = [self.get_cat_task(),
                         self.get_bank_rubbery_task(),
                         self.get_terror_task(),
                         self.get_car_accident_easy(),
                         self.get_car_accident_hard(),
                         self.family_violence()]
        self.random_task = list_of_tasks[self.index]


    def get_cat_task(self):
        m1 = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=1800, arrival_time_to_the_system=0,
                           ability=self.ability_dict[0], max_players=2)
        m1.remaining_workload = m1.remaining_workload * self.rand.random()

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=1, missions=[m1],name="cat")

    def get_bank_rubbery_task(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600, arrival_time_to_the_system=0,
                                    ability=self.ability_dict[1], max_players=2)
        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                    arrival_time_to_the_system=0,
                                    ability=self.ability_dict[2], max_players=3)
        m_observe = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                  arrival_time_to_the_system=0,
                                  ability=self.ability_dict[3], max_players=4)
        m_gun = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5, arrival_time_to_the_system=0,
                              ability=self.ability_dict[4], max_players=3)

        missions = [m_interview, m_first_aid, m_observe, m_gun]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=8, missions=missions,name="bank_rub")

    def get_terror_task(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                    arrival_time_to_the_system=0,
                                    ability=self.ability_dict[1], max_players=3)

        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                    arrival_time_to_the_system=0,
                                    ability=self.ability_dict[2], max_players=3)

        m_observe = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                  arrival_time_to_the_system=0,
                                  ability=self.ability_dict[3], max_players=4)

        m_gun = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5, arrival_time_to_the_system=0,
                              ability=self.ability_dict[4], max_players=4)

        missions = [m_interview, m_first_aid, m_observe, m_gun]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=10, missions=missions,name="terror")

    def get_car_accident_easy(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=2700, arrival_time_to_the_system=0,
                                    ability=self.ability_dict[1], max_players=1)

        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=2700, arrival_time_to_the_system=0,
                                    ability=self.ability_dict[2], max_players=2)

        missions = [m_interview, m_first_aid]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=3, missions=missions,name="easy_car_a")

    def get_car_accident_hard(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=5400, arrival_time_to_the_system=0,
                                    ability=self.ability_dict[1], max_players=2)

        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=5400, arrival_time_to_the_system=0,
                                    ability=self.ability_dict[2], max_players=3)

        missions = [m_interview, m_first_aid]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=6, missions=missions,name="hard_car_a")

    def family_violence(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=4500, arrival_time_to_the_system=0,
                                    ability=self.ability_dict[1], max_players=2)

        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=4500, arrival_time_to_the_system=0,
                                    ability=self.ability_dict[2], max_players=1)

        missions = [m_interview, m_first_aid]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=4, missions=missions,name="family_dis")

    def create_ability_dict(self):
        self.ability_dict[0] = AbilitySimple(ability_type=0, ability_name="Basic")
        self.ability_dict[1] = AbilitySimple(ability_type=1, ability_name="Interview")
        self.ability_dict[2] = AbilitySimple(ability_type=2, ability_name="First-Aid")
        self.ability_dict[3] = AbilitySimple(ability_type=3, ability_name="Observe")
        self.ability_dict[4] = AbilitySimple(ability_type=4, ability_name="Gun")

    def get_random_index_according_to_p_function(self):
        # cat_task, 0 , 0.21
        # bank_rubbery, 1, 0.1
        # terror, 2, 0.1
        # car_accident_easy, 3 , 0.21
        # car_accident_hard, 4 , 0.17
        # family_violence, 5 , 0.21

        small_p = [0.21, 0.1, 0.1, 0.21, 0.17, 0.21]
        large_p = []
        sum_ = 0
        for i in small_p:
            sum_ = sum_+i
            large_p.append(sum_)

        if large_p[len(large_p)-1]!=1:
            raise Exception("something in the calculation is incorrect")

        p = self.rand.random()

        index  = 0
        for P in large_p:
            if p<P:
                break
            index =index+1
        return index




#maps = create_maps()
#tasks_per_scenario = create_tasks_per_scenario(maps)
#players_per_scenario = create_tasks_per_scenario(tasks_per_scenario)
#new_task_events_per_scenario = create_new_task_events_per_scenario(maps)

class TaskArrivalEventStatic(TaskArrivalEvent):
    def __init__(self,task,players,solver:AllocationSolver):
        self.time = 0
        self.task=task
        self.players = players
        self.solver = solver

    def handle_event(self, simulation):
        find_responsible_agent(task = self.task,agents_list =self.players)
        self.solver.add_task_to_solver(self.task)
        simulation.solve()


class AllocationStaticGenerator:
    """
    create tasks and players and responsible players
    """
    #TODO


class SimulationStatic():
    def __init__(self, rep_number = 99,solver: AllocationSolver = None, players_required_ratio = 1):

        self.rand = random.Random(rep_number*17)

        self.seed_number = rep_number
        self.solver = solver

        # FOR MAP
        #---------------
        self.map = MapHubs(seed=self.seed_number*1717, number_of_centers=5,sd_multiplier=0.05)
        self.tasks_per_center = 3

        self.tasks = []
        self.create_tasks()

        self.draw_tasks()

        #allocation_generator = AllocationStaticGenerator()
        #self.tasks = allocation_generator.tasks
        #self.players = allocation_generator.players
        #self.solver.add_tasks_list(self.tasks)
        #self.solver.add_players_list(self.players)
        #self.task_arrive_event =  self.create_task_arrival_event()

    def create_task_arrival_event(self):
        task_new = self.task_generator.get_next_task()
        TaskArrivalEventStatic()

    def create_tasks(self):
        total_number_of_tasks = self.tasks_per_center *len(self.map.centers_location)
        for _ in range(total_number_of_tasks):
            task = SingleTaskStaticPoliceGenerator(rand=self.rand,map=self.map).random_task
            self.tasks.append(task)

    def draw_tasks(self):
        x = []
        y = []
        importance =[]
        name = []
        type_ = []

        for t in self.tasks:
            x.append(t.location[0])
            y.append(t.location[1])
            #importance.append(t.importance)
            name.append(t.name)
            type_.append("task")

        for cent in self.map.centers_location:
            x.append(cent[0])
            y.append(cent[1])
            # importance.append(t.importance)
            name.append("center")
            type_.append("center")

        df = pd.DataFrame(dict(x=x, y=y, type_=type_,name=name))

        fig, ax = plt.subplots()

        colors = {'center': 'red', 'task': 'blue'}

        ax.scatter(df['x'], df['y'], c=df['type_'].map(colors))

        #plt.scatter(x, y, color='black')
        plt.xlim(0, self.map.width)
        plt.ylim(0, self.map.length)
        plt.show()


if __name__ == '__main__':
    ss = SimulationStatic(rep_number=50)