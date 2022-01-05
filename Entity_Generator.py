import math
import string
import random

from Simulation_Abstract import  MissionSimple, TaskSimple,  TaskGenerator, \
    PlayerSimple
# from StaticSimulation import TaskSimpleStatic, rand_id_str
from Simulation_Abstract_Components import MapHubs, PlayerGenerator, AbilitySimple
from TSG_Solver import TSGEvent, Status, TSGPlayer
import numpy as np


class SimpleTaskGenerator(TaskGenerator):
    def __init__(self, map_: MapHubs, seed, factor_initial_workload=1.15, max_importance=10, exp_lambda_parameter=2):
        """

        :param map_: object to initiate location
        :param seed: used for randomization
        :param factor_initial_workload: initial_workload = self.factor_initial_workload**task_importance
        :param max_importance: the maximum level of importance
        :param exp_lambda_parameter: used to get random gap between tasks exp(exp_lambda_parameter)
        """
        TaskGenerator.__init__(self, map_, seed)
        self.beta = exp_lambda_parameter
        self.id_task_counter = 0
        self.id_mission_counter = 0
        self.max_importance = max_importance
        self.factor_initial_workload = factor_initial_workload

    def time_gap_between_tasks(self):
        return self.rnd_numpy.exponential(scale=self.beta, size=1)[0]

    def get_task(self, tnow,flag_time_zero = False):
        """
        :rtype: TaskSimple
        """
        self.id_task_counter = self.id_task_counter + 1
        id_ = str(self.id_task_counter)
        location = self.map.generate_location()#self.map.generate_location_gauss_around_center()
        importance = (1 + math.floor(self.random.random() * self.max_importance)) * 1000
        if flag_time_zero:
            arrival_time = tnow
        else:
            arrival_time = tnow + self.time_gap_between_tasks()
        missions_list = [self.create_random_mission(task_importance=importance, arrival_time=arrival_time)]

        return TaskSimple(id_=id_, location=location, importance=importance,
                          missions_list=missions_list, arrival_time=arrival_time)

    def create_random_mission(self, task_importance: float, arrival_time: float):
        self.id_mission_counter = self.id_mission_counter + 1
        mission_id = str(self.id_mission_counter)
        initial_workload = self.factor_initial_workload ** (task_importance/1000)
        arrival_time_to_the_system = arrival_time
        max_players = min(max(self.rnd_numpy.poisson(lam=(task_importance/1500) / 2, size=1)[0], 2 ),5)

        return MissionSimple(task_importance = task_importance,mission_id= mission_id,
                             initial_workload= initial_workload, arrival_time_to_the_system= arrival_time_to_the_system, max_players=max_players)


class SimplePlayerGenerator(PlayerGenerator):
    def __init__(self, map_: MapHubs, seed, speed=1, min_productivity=0.5):
        PlayerGenerator.__init__(self, map_, seed)
        self.id_counter = 0
        self.speed = speed
        self.min_productivity = min_productivity

    def get_player(self):
        self.id_counter = self.id_counter - 1
        id_ = str(self.id_counter)
        #location = self.map.generate_location_gauss_around_center()
        location = self.map.generate_location()
        speed = self.speed
        productivity = 1#self.calc_productivity()
        return PlayerSimple(id_=id_, current_location=location, speed=speed, productivity=productivity)

    def calc_productivity(self):
        a = self.min_productivity
        b = 1
        x_min = 0
        x_max = 1

        x = self.random.random()
        x_tag = a + (((x - x_min) * (b - a)) / (x_max - x_min))
        return x_tag


class TaskSimpleStatic(TaskSimple):
    def __init__(self, id_, location, importance, missions_list, name):
        TaskSimple.__init__(self, id_, location, importance, missions_list)
        self.name = name

    def __str__(self):
        return self.name


def rand_id_str(rand):
    ans = ''.join(rand.choices(string.ascii_uppercase + string.digits, k=10))
    return ans


class SinglePlayerGeneratorTSG():
    def __init__(self, rand: random.Random, map_: MapHubs, ability_number, tnow=0, is_static_simulation=False):
        self.rand = rand
        self.tnow = tnow
        self.is_static_simulation = is_static_simulation
        self.location = map_.generate_location_gauss_around_center()
        self.selected_ability = ability_number  # self.get_selected_ability(ability_number)
        parameters_input = self.get_parameters_input_dict()
        force_data_dict = self.create_force_type_data_map(parameters_input)
        self.rnd_player = self.create_agents(force_data_dict, t_now=self.tnow)

    def create_agents(self, force_data_dict, t_now):
        agents_id_list = []
        agent_id = rand_id_str(self.rand)
        agents_id_list.append(agent_id)
        type_ = self.selected_ability
        last_update_time = self.tnow
        working_hours = 0
        resting_hours = 8
        address = "TODO"

        is_working_extra_hours = False
        if resting_hours > 0 and working_hours > 0:
            raise Exception
        if not self.is_static_simulation:
            if 0 < resting_hours < force_data_dict[type_]["min_competence_time"] or \
                    working_hours >= force_data_dict[type_]["max_activity_time"] + force_data_dict[type_][
                "extra_hours_allowed"] + 0.25:
                status = Status.TOTAL_RESTING
                start_activity_time = None
                start_resting_time = last_update_time - resting_hours
            elif force_data_dict[type_]["min_competence_time"] <= resting_hours < force_data_dict[type_][
                "competence_length"]:
                status = Status.RESTING
                start_activity_time = None
                start_resting_time = None  # TODO t[3] / 3600 - t[7]
            else:
                status = Status.IDLE
                start_activity_time = last_update_time - working_hours
                start_resting_time = None
                if working_hours >= force_data_dict[type_]["max_activity_time"]:
                    is_working_extra_hours = True
            productivity = 1
        else:
            status = Status.IDLE
            start_activity_time = t_now - self.rand.random() * force_data_dict[type_]["max_activity_time"]
            start_resting_time = None

            a = 0.6
            b = 1
            x_min = 0
            x_max = 1

            x = 1 - (t_now - start_activity_time) / force_data_dict[type_]["max_activity_time"]
            x_tag = a + (((x - x_min) * (b - a)) / (x_max - x_min))
            productivity = x_tag

            if not a <= productivity <= b:
                raise Exception("something in the calc went wrong")

        return TSGPlayer(agent_id=agent_id, agent_type=type_, last_update_time=last_update_time,
                         current_location=self.location, start_activity_time=start_activity_time,
                         start_resting_time=start_resting_time,
                         max_activity_time=force_data_dict[type_]["max_activity_time"],
                         extra_hours_allowed=force_data_dict[type_]["extra_hours_allowed"],
                         min_competence_time=force_data_dict[type_]["min_competence_time"],
                         competence_length=force_data_dict[type_]["competence_length"], status=status,
                         is_working_extra_hours=is_working_extra_hours, address=address, productivity=productivity
                         )

    def get_selected_ability(self, ability_number):
        if ability_number == 1:
            name = "SR"
        if ability_number == 8:
            name = "HQ"
        if ability_number == 4:
            name = "MED"
        return AbilitySimple(ability_type=ability_number, ability_name=name)

    def get_parameters_input_dict(self):
        return [(1, 960, 120, 360, 480), (4, 960, 120, 360, 480), (8, 480, 60, 420, 480)]

    def create_force_type_data_map(self, force_type_data):
        force_data = {}
        for t in force_type_data:
            force_data[t[0]] = {"max_activity_time": t[1] / 60, "extra_hours_allowed": t[2] / 60,
                                "min_competence_time": t[3] / 60,
                                "competence_length": t[4] / 60}
        return force_data


def get_parameters_input_dict():
    return [
        (2, 1, 1, 2, [(4, 1, 1), (1, 1, 1)]),
        (2, 2, 1, 2, [(4, 1, 1), (1, 1, 1)]),
        (2, 3, 1, 3, [(4, 1, 1), (1, 2, 1)]),
        (2, 4, 1, 14, [(4, 2, 2), (1, 4, 2), (8, 1, 2)]),
        (2, 5, 1, 21, [(4, 2, 3), (1, 4, 3), (8, 1, 3)]),
        (2, 6, 1, 30, [(4, 2, 6), (1, 3, 6)]),
        (2, 1, 2, 12, [(4, 1, 3), (1, 2, 3), (8, 1, 3)]),
        (2, 2, 2, 12, [(4, 1, 3), (1, 2, 3), (8, 1, 3)]),
        (2, 3, 2, 12, [(4, 1, 3), (1, 2, 3), (8, 1, 3)]),
        (2, 4, 2, 100, [(4, 3, 10), (1, 5, 10), (8, 2, 10)]),
        (2, 5, 2, 234, [(4, 4, 18), (1, 6, 18), (8, 3, 18)]),
        (2, 6, 2, 432, [(4, 6, 24), (1, 8, 24), (8, 4, 24)]),
        (2, 1, 3, 6, [(4, 1, 2), (1, 2, 2)]),
        (2, 2, 3, 6, [(4, 1, 2), (1, 2, 2)]),
        (2, 3, 3, 6, [(4, 1, 2), (1, 2, 2)]),
        (2, 4, 3, 24, [(4, 1, 6), (1, 3, 6)]),
        (2, 5, 3, 80, [(4, 2, 10), (1, 5, 10), (8, 1, 10)]),
        (2, 6, 3, 120, [(4, 3, 12), (1, 6, 12), (8, 1, 12)]),
        (2, 1, 4, 2, [(4, 1, 1), (1, 1, 1)]),
        (2, 2, 4, 2, [(4, 1, 1), (1, 1, 1)]),
        (2, 3, 4, 3, [(4, 2, 1), (1, 1, 1)]),
        (2, 4, 4, 4, [(4, 3, 1), (1, 1, 1)]),
        (2, 5, 4, 14, [(4, 2, 2), (1, 4, 2), (8, 1, 2)]),
        (2, 6, 4, 21, [(4, 2, 3), (1, 4, 3), (8, 1, 3)]),
        (2, 1, 5, 2, [(4, 1, 1), (1, 1, 1)]),
        (2, 2, 5, 2, [(4, 1, 1), (1, 1, 1)]),
        (2, 3, 5, 3, [(4, 1, 1), (1, 2, 1)]),
        (2, 4, 5, 4, [(4, 3, 1), (1, 1, 1)]),
        (2, 5, 5, 8, [(4, 1, 2), (1, 3, 2)]),
        (2, 6, 5, 12, [(4, 1, 3), (1, 3, 3)])
    ]


def create_event_params_data_map(event_params):
    events_data = {}
    for t in event_params:
        events_data[(t[0], t[1], t[2])] = {"total_workload": t[3], "mission_params": {}}
        for p in t[4]:
            events_data[(t[0], t[1], t[2])]["mission_params"][p[0]] = {"max_number_of_teams": p[1],
                                                                       "workload": p[1] * p[2]}

    return events_data


def get_relevant_key_and_value(parameters_dict, damage_level, life_saving_potential):
    for key, value in parameters_dict.items():
        if key[1] == damage_level and key[2] == life_saving_potential:
            return key, value


class TaskGeneratorTSG(TaskGenerator):
    def __init__(self, map_, seed, exp_lambda_parameter=2):
        """

        :param map_:
        :param seed:
        """
        TaskGenerator.__init__(self, map_, seed)
        self.rnd_numpy = np.random.default_rng(seed=seed)

        self.lambda_ = exp_lambda_parameter

    def time_gap_between_tasks(self):
        return self.rnd_numpy.exponential(scale=self.lambda_, size=1)[0]

    def get_task(self, tnow):
        """
        :rtype: TaskSimple
        """
        location = self.map.generate_location_gauss_around_center()
        damage_level = self.random.choice([1, 2, 3, 4, 5, 6])
        life_saving_potential = self.random.choice([1, 2, 3, 4, 5])
        parameters_input = get_parameters_input_dict()
        parameters_dict = create_event_params_data_map(parameters_input)
        key, value = get_relevant_key_and_value(parameters_dict, damage_level, life_saving_potential)

        random_task = TSGEvent(event_id=rand_id_str(self.random),
                               event_type=2,
                               damage_level=damage_level,
                               life_saving_potential=life_saving_potential,
                               event_creation_time=tnow + self.time_gap_between_tasks(),
                               event_update_time=tnow,
                               point=location,
                               workload=value["total_workload"],
                               mission_params=value["mission_params"],
                               importance=None)
        return random_task


class SingleTaskGeneratorTSG():
    def __init__(self, rand: random.Random, map_: MapHubs, tnow=0):
        self.rand = rand
        self.tnow = tnow
        self.location = map_.generate_location_gauss_around_center()
        self.damage_level = self.rand.choice([1, 2, 3, 4, 5, 6])
        self.life_saving_potential = self.rand.choice([1, 2, 3, 4, 5])

        parameters_input = get_parameters_input_dict()
        parameters_dict = create_event_params_data_map(parameters_input)

        key, value = self.get_relevant_key_and_value(parameters_dict)
        self.random_task = TSGEvent(event_id=rand_id_str(self.rand),
                                    event_type=2,
                                    damage_level=self.damage_level,
                                    life_saving_potential=self.life_saving_potential,
                                    event_creation_time=self.tnow,
                                    event_update_time=self.tnow,
                                    point=self.location,
                                    workload=value["total_workload"],
                                    mission_params=value["mission_params"],
                                    importance=None)

    def create_event_params_data_map(self, event_params):
        events_data = {}
        for t in event_params:
            events_data[(t[0], t[1], t[2])] = {"total_workload": t[3], "mission_params": {}}
            for p in t[4]:
                events_data[(t[0], t[1], t[2])]["mission_params"][p[0]] = {"max_number_of_teams": p[1],
                                                                           "workload": p[1] * p[2]}

        return events_data

    def get_relevant_key_and_value(self, parameters_dict):
        for key, value in parameters_dict.items():
            if key[1] == self.damage_level and key[2] == self.life_saving_potential:
                return key, value


class SingleTaskStaticPoliceGenerator():
    def __init__(self, create_ability_dict, rand: random.Random, map: MapHubs,
                 small_p=[0.21, 0.1, 0.1, 0.21, 0.17, 0.21]):
        self.rand = rand
        self.ability_dict = {}
        create_ability_dict(self.ability_dict)
        self.location = map.generate_location_gauss_around_center()
        self.small_p = small_p
        list_of_tasks = [self.get_cat_task(),
                         self.get_bank_rubbery_task(),
                         self.get_terror_task(),
                         self.get_car_accident_easy(),
                         self.get_car_accident_hard(),
                         self.family_violence()]

        self.random_task = rand.choices(list_of_tasks, weights=small_p, k=1)[0]

    def get_cat_task(self):
        m1 = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=1800, arrival_time_to_the_system=0,
                           abilities=self.ability_dict[0], max_players=2)
        m1.remaining_workload = m1.remaining_workload * self.rand.random()

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=1, missions_list=[m1],
                                name="cat")

    def get_bank_rubbery_task(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[1], max_players=2)
        m_interview.remaining_workload = m_interview.remaining_workload * self.rand.random()

        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[2], max_players=3)
        m_first_aid.remaining_workload = m_first_aid.remaining_workload * self.rand.random()

        m_observe = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                  arrival_time_to_the_system=0,
                                  abilities=self.ability_dict[3], max_players=4)
        m_observe.remaining_workload = m_observe.remaining_workload * self.rand.random()

        m_gun = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                              arrival_time_to_the_system=0,
                              abilities=self.ability_dict[4], max_players=3)
        m_gun.remaining_workload = m_gun.remaining_workload * self.rand.random()

        missions = [m_interview, m_first_aid, m_observe, m_gun]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=8,
                                missions_list=missions,
                                name="bank_rub")

    def get_terror_task(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[1], max_players=3)
        m_interview.remaining_workload = m_interview.remaining_workload * self.rand.random()

        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[2], max_players=3)
        m_first_aid.remaining_workload = m_first_aid.remaining_workload * self.rand.random()

        m_observe = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                                  arrival_time_to_the_system=0,
                                  abilities=self.ability_dict[3], max_players=4)
        m_observe.remaining_workload = m_observe.remaining_workload * self.rand.random()

        m_gun = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=3600 * 1.5,
                              arrival_time_to_the_system=0,
                              abilities=self.ability_dict[4], max_players=4)
        m_gun.remaining_workload = m_gun.remaining_workload * self.rand.random()

        missions = [m_interview, m_first_aid, m_observe, m_gun]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=10,
                                missions_list=missions,
                                name="terror")

    def get_car_accident_easy(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=2700,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[1], max_players=1)
        m_interview.remaining_workload = m_interview.remaining_workload * self.rand.random()

        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=2700,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[2], max_players=2)
        m_first_aid.remaining_workload = m_first_aid.remaining_workload * self.rand.random()

        missions = [m_interview, m_first_aid]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=3,
                                missions_list=missions,
                                name="easy_car_a")

    def get_car_accident_hard(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=5400,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[1], max_players=2)
        m_interview.remaining_workload = m_interview.remaining_workload * self.rand.random()

        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=5400,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[2], max_players=3)
        m_first_aid.remaining_workload = m_first_aid.remaining_workload * self.rand.random()

        missions = [m_interview, m_first_aid]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=6,
                                missions_list=missions,
                                name="hard_car_a")

    def family_violence(self):
        m_interview = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=4500,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[1], max_players=2)
        m_interview.remaining_workload = m_interview.remaining_workload * self.rand.random()

        m_first_aid = MissionSimple(mission_id=rand_id_str(self.rand), initial_workload=4500,
                                    arrival_time_to_the_system=0,
                                    abilities=self.ability_dict[2], max_players=1)
        m_first_aid.remaining_workload = m_first_aid.remaining_workload * self.rand.random()

        missions = [m_interview, m_first_aid]

        return TaskSimpleStatic(id_=rand_id_str(self.rand), location=self.location, importance=4,
                                missions_list=missions,
                                name="family_dis")


if __name__ == '__main__':
    rnd = random.Random(1)
    mmm = MapHubs(number_of_centers=3, seed=1, length_y=9.0, width_x=9.0, sd_multiplier=0.5)
    generator_ = SimpleTaskGenerator(map_=mmm, seed=1, factor_initial_workload=1.15, max_importance=10,
                                     exp_lambda_parameter=2)
    tasks = []

    player_generator = SimplePlayerGenerator(map_=mmm, seed=1)
    for _ in range(10):
        tasks.append(generator_.get_task(0))

    players = []
    for _ in range(10):
        players.append(player_generator.get_player())

