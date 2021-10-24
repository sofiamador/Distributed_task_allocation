import string
import random

from Simulation import MapHubs, MissionSimple, TaskSimple
# from StaticSimulation import TaskSimpleStatic, rand_id_str
from TSG_Solver import TSGEvent


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
    def __init__(self, rand: random.Random):


class SingleTaskGeneratorTSG():
    def __init__(self, rand: random.Random, map_: MapHubs, tnow =0):
        self.rand = rand
        self.tnow = tnow
        self.location = map_.generate_location_gauss_around_center()
        self.damage_level = self.rand.choice([1, 2, 3, 4, 5, 6])
        self.life_saving_potential = self.rand.choice([1, 2, 3, 4, 5])

        parameters_input = self.get_parameters_input_dict()
        parameters_dict = self.create_event_params_data_map(parameters_input)

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
                                 tnow=self.tnow)

    def get_parameters_input_dict(self):
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
    stgTSG = SingleTaskGeneratorTSG(rand=rnd, map_=mmm)
