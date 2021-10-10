import random

import Allocation_Solver_Abstract

from Simulation import MapHubs, TaskArrivalEvent, TaskGenerator, find_responsible_agent, MissionSimple, TaskSimple, \
    AbilitySimple
from Allocation_Solver_Abstract import AllocationSolver
simulation_reps = 100


import string


def create_ability_dict():

    ability_dict = {}
    ability_dict[0] =  AbilitySimple( ability_type=0, ability_name="Basic")
    ability_dict[1] =  AbilitySimple( ability_type=1, ability_name="Interview")
    ability_dict[2] =  AbilitySimple( ability_type=2, ability_name="First-Aid")
    ability_dict[3] =  AbilitySimple( ability_type=3, ability_name="Observe")
    ability_dict[4] =  AbilitySimple( ability_type=4, ability_name="Gun")

    return ability_dict


def rand_id_str(rand):
    ans =  ''.join(rand.choices(string.ascii_uppercase + string.digits, k = 10))
    return ans

def get_cat_task(rand:random.Random, location, ability_dict = create_ability_dict()):


    m1 = MissionSimple(mission_id=rand_id_str(rand),initial_workload =1800, arrival_time_to_the_system=0,
                       ability=ability_dict[0],max_players=2)
    m1.remaining_workload = m1.remaining_workload * rand.random()

    return TaskSimple(id_=rand_id_str(rand),location=location,importance=1,missions=[m1])

def get_bank_rubbery_task(rand:random.Random, location, ability_dict = create_ability_dict()):

    m_interview = MissionSimple(mission_id=rand_id_str(rand), initial_workload=3600, arrival_time_to_the_system=0,
                       ability=ability_dict[1], max_players=2)
    m_first_aid = MissionSimple(mission_id=rand_id_str(rand), initial_workload=3600*1.5, arrival_time_to_the_system=0,
                                ability=ability_dict[2], max_players=3)
    m_observe = MissionSimple(mission_id=rand_id_str(rand), initial_workload=3600 * 1.5, arrival_time_to_the_system=0,
                                ability=ability_dict[3], max_players=4)
    m_gun = MissionSimple(mission_id=rand_id_str(rand), initial_workload=3600 * 1.5, arrival_time_to_the_system=0,
                              ability=ability_dict[4], max_players=3)

    missions = [m_interview,m_first_aid,m_observe,m_gun]


    return TaskSimple(id_=rand_id_str(rand),location=location,importance=8,missions=missions)

def get_terror_task(rand:random.Random, location, ability_dict = create_ability_dict()):

    m_interview = MissionSimple(mission_id=rand_id_str(rand), initial_workload=3600*1.5, arrival_time_to_the_system=0,
                       ability=ability_dict[1], max_players=3)

    m_first_aid = MissionSimple(mission_id=rand_id_str(rand), initial_workload=3600*1.5, arrival_time_to_the_system=0,
                                ability=ability_dict[2], max_players=3)

    m_observe = MissionSimple(mission_id=rand_id_str(rand), initial_workload=3600 * 1.5, arrival_time_to_the_system=0,
                                ability=ability_dict[3], max_players=4)

    m_gun = MissionSimple(mission_id=rand_id_str(rand), initial_workload=3600 * 1.5, arrival_time_to_the_system=0,
                              ability=ability_dict[4], max_players=4)

    missions = [m_interview,m_first_aid,m_observe,m_gun]


    return TaskSimple(id_=rand_id_str(rand),location=location,importance=10,missions=missions)

def get_car_accident_easy (rand: random.Random, location, ability_dict=create_ability_dict()):

    m_interview = MissionSimple(mission_id=rand_id_str(rand), initial_workload=2700, arrival_time_to_the_system=0,
                                ability=ability_dict[1], max_players=1)

    m_first_aid = MissionSimple(mission_id=rand_id_str(rand), initial_workload=2700, arrival_time_to_the_system=0,
                                ability=ability_dict[2], max_players=2)


    missions = [m_interview, m_first_aid]

    return TaskSimple(id_=rand_id_str(rand), location=location, importance=3, missions=missions)

def get_car_accident_hard (rand: random.Random, location, ability_dict=create_ability_dict()):

    m_interview = MissionSimple(mission_id=rand_id_str(rand), initial_workload=5400, arrival_time_to_the_system=0,
                                ability=ability_dict[1], max_players=2)

    m_first_aid = MissionSimple(mission_id=rand_id_str(rand), initial_workload=5400, arrival_time_to_the_system=0,
                                ability=ability_dict[2], max_players=3)


    missions = [m_interview, m_first_aid]

    return TaskSimple(id_=rand_id_str(rand), location=location, importance=6, missions=missions)

def family_violence  (rand: random.Random, location, ability_dict=create_ability_dict()):

    m_interview = MissionSimple(mission_id=rand_id_str(rand), initial_workload=4500, arrival_time_to_the_system=0,
                                ability=ability_dict[1], max_players=2)

    m_first_aid = MissionSimple(mission_id=rand_id_str(rand), initial_workload=4500, arrival_time_to_the_system=0,
                                ability=ability_dict[2], max_players=1)


    missions = [m_interview, m_first_aid]

    return TaskSimple(id_=rand_id_str(rand), location=location, importance=4, missions=missions)


def get_random_task_out_of_list(list_of_tasks,rand):
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

    if large_p[len(large_p-1)]!=1:
        raise Exception("something in the calculation is incorrect")

    p = rand.random()

    index  = 0
    for P in large_p:
        if p<P:
            return list_of_tasks[index]
        index =index+1


def get_random_task(rand:random.Random,map:MapHubs):

    location = map.generate_location()

    list_of_tasks = [get_cat_task(location,rand),
                     get_bank_rubbery_task(location,rand),
                     get_terror_task(location,rand),
                     get_car_accident_easy(location,rand),
                     get_car_accident_hard(location,rand),
                     family_violence(location,rand)]

    return  get_random_task_out_of_list(list_of_tasks,rand)













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
    def __init__(self, rep_number,solver: AllocationSolver, players_required_ratio):
        self.seed_number = rep_number
        self.solver = solver

        # FOR MAP
        number_of_centers = 3
        length_y = 9.0
        width_x = 9.0
        sd_multiplier = 0.5
        #---------------



        self.map = MapHubs(number_of_centers=number_of_centers, seed=self.seed_number,
                                 length_y=length_y, width_x=width_x, sd_multiplier=sd_multiplier)
        tasks_per_center = 2

        self.task_generator = StaticTaskGenerator(map_ = self.map,seed = self.seed_number, task_list=) #get_next_task
        allocation_generator = AllocationStaticGenerator()
        self.tasks = allocation_generator.tasks
        self.players = allocation_generator.players
        self.solver.add_tasks_list(self.tasks)
        self.solver.add_players_list(self.players)
        self.task_arrive_event =  self.create_task_arrival_event()

    def create_task_arrival_event(self):
        task_new = self.task_generator.get_next_task()
        TaskArrivalEventStatic()




