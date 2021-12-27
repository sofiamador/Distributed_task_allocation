import enum
import random
import sys
import abc
from abc import ABC
from datetime import time
import numpy as np

from typing import List

global solver_debug


class Status(enum.Enum):
    """
    Enum that represents the status of the player in the simulation
    """
    IDLE = 0
    ON_MISSION = 1
    TO_MISSION = 2


class Entity:
    """
    Class that represents a basic entity in the simulation
    """

    def __init__(self, id_, location, last_time_updated=0):
        """
        :param id_: The id of the entity
        :type  id_: str
        :param location: The location of the entity. A list of of coordination.
        :type location: list of floats
        :param last_time_updated:

        """
        self.id_ = id_
        self.location = location
        self.neighbours = []
        self.last_time_updated = last_time_updated

    def update_time(self, tnow):
        if tnow >= self.last_time_updated:
            self.last_time_updated = tnow
        else:
            raise Exception("last time updated is higher than tnow")

    def create_neighbours_list(self, entities_list: list, f_are_neighbours):
        """
        Method that populates the neighbours list of the entity. It accepts list of potential neighbours
        and a function that returns whether a pair of entities are neighbours
        :param entities_list: List of entities that are potential neighbours
        :type entities_list: list ot Entity
        :param f_are_neighbours: Function that receives 2 entities and return true if they can be neighbours
        :type f_are_neighbours: function
        :return: None
        """
        raise NotImplementedError

    def __hash__(self):
        return hash(self.id_)

    def __eq__(self, other):
        return self.id_ == other.id_

    def __str__(self):
        return str(self.id_)


def calculate_distance_input_location(location1, location2):
    """
    Calculates the distance between two entities. Each entity must have a location property.
    :param location1:first location
    :type location1: list
    :param location2:second location
    :type location2: list
    :return: Euclidean distance between two entities
    :rtype: float
    """

    distance = 0
    n = min(len(location1), len(location2))
    for i in range(n):
        distance += (location1[i] - location2[i]) ** 2

    return distance ** 0.5


def calculate_distance(entity1: Entity, entity2: Entity):
    """
    Calculates the distance between two entities. Each entity must have a location property.
    :param entity1:first entity
    :type entity1: Entity
    :param entity2:second entity
    :type entity1: Entity
    :return: Euclidean distance between two entities
    :rtype: float
    """
    location1 = entity1.location
    location2 = entity2.location
    return calculate_distance_input_location(location1, location2)


def are_neighbours(entity1: Entity, entity2: Entity):
    """
    The functions checks if the entities (players) can be neighbours
    :param entity1: first entity
    :type entity1: Entity
    :param entity2: second entity
    :type entity1: Entity
    :return: bool
    """
    return True


def is_player_can_be_allocated_to_task(task, player):
    """
    Function that checks if the player can be allocated to an task according to player's abilities and required abilities
    to the task.
    :param task: The task that is checked.
    :type task: TaskSimple
    :param player: The player that is checked if it suitable for the task according to hos abilities.
    :return:
    """
    #for mission in task.missions_list:
    #    for ability in mission.abilities:
    #        if ability in player.abilities:
    #            return True
    return True


class AbilitySimple:
    """
       Class that represents a simple ability that the missions require and the players have
    """

    def __init__(self, ability_type, ability_name=None):
        """
        :param ability_type: The type of the ability
        :type ability_type: int
        :param ability_name: The name of the ability. If the name is not given it will be set to the type of the ability
        (casted to str) 
        :type ability_name: str
        """

        self.ability_type = ability_type
        self.ability_name = ability_name
        if self.ability_name is None:
            self.ability_name = str(ability_type)

    def __hash__(self):
        return hash(self.ability_type)

    def __eq__(self, other):
        return self.ability_type == other.ability_type

    def __str__(self):
        return self.ability_name

    def get_ability_type(self):
        return self.ability_type


class MissionMetrics:

    def __init__(self):
        pass


class PlayerSimple(Entity):
    """
    Class that represents a basic player in the simulation
    """

    def __init__(self, id_, current_location, speed, status=Status.IDLE,
                 abilities=None, tnow=0, base_location=None, productivity=1):
        """
        :param id_: The id of the player
        :type  id_: str
        :param current_location: The location of the player
        :type current_location: list of float
        :param status: The status of the player
        :type  status: Status
        :param abilities: abilities of the player
        :type  abilities: set of AbilitySimple
        :param current_task: The current task that was allocated to player. If the the player is idle this field will be None.
        :type current_task: TaskSimple
        :param current_mission: The current sub-task of the player. If the the player is idle this field will be None.
        :type current_mission: MissionSimple

        """
        Entity.__init__(self, id_, current_location, tnow)
        if abilities is None:
            abilities = [AbilitySimple(ability_type=0)]
        self.speed = speed
        self.status = status
        self.abilities = abilities
        self.current_task = None
        self.current_mission = None
        self.tasks_responsible = []
        self.neighbours = []
        self.base_location = base_location
        self.productivity = productivity
        self.schedule = []  # [(task,mission,time)]

    def update_status(self, new_status: Status, tnow: float) -> None:
        """
        Updates the status of the player
        :param new_status:the new status of the player
        :param tnow: the time when status of the player is updated
        :return:None
        """
        self.status = new_status
        self.update_time(tnow)

    def update_location(self, location, tnow):
        """
        Updates the location of the player
        :param location:
        :param tnow:
        :return:
        """
        self.location = location
        self.update_time(tnow)

    def create_neighbours_list(self, players_list, f_are_neighbours=are_neighbours):
        """
        creates neighbours list of players
        :param players_list:
        :param f_are_neighbours:
        :return:None
        """
        for p in players_list:
            if self.id_ != p.id_ and f_are_neighbours(self, p):
                self.neighbours.append(p)

    def calculate_relative_location(self, tnow):
        if self.status == Status.TO_MISSION:
            travel_time = calculate_distance(self, self.current_task) / self.speed
            time_delta = tnow - self.last_time_updated
            ratio_of_the_time = time_delta / travel_time
            for i in range(len(self.location)):
                self.location[i] = self.location[i] + (
                            self.current_task.location[i] - self.location[i]) * ratio_of_the_time
            self.update_time(tnow)


class MissionSimple:
    """
    Class that represents a simple mission (as a part of the task)
    """

    def __init__(self, mission_id, initial_workload, arrival_time_to_the_system,
                 abilities=(AbilitySimple(ability_type=0)),
                 min_players=1, max_players=1):
        """
        Simple mission constructor
        :param mission_id: Mission's id
        :type mission_id: str
        :param initial_workload: The required workload of the mission (in seconds)
        :type initial_workload: float
        :param arrival_time_to_the_system: The time that task (with the mission)  arrived
        :param abilities:
        :param min_players:
        :param max_players:
        """

        self.mission_id = mission_id
        self.abilities = abilities
        self.min_players = min_players
        self.max_players = max_players
        self.initial_workload = initial_workload
        self.remaining_workload = initial_workload
        self.players_allocated_to_the_mission = []
        self.players_handling_with_the_mission = []
        self.is_done = False
        self.arrival_time_to_the_system = arrival_time_to_the_system
        self.last_updated = arrival_time_to_the_system

    def update_workload(self, tnow):
        delta = tnow - self.last_updated
        self.workload_updating(delta)
        if self.remaining_workload < 0.05:
            self.is_done = True

        self.last_updated = tnow

    def workload_updating(self, delta):
        productivity = 0
        for p in self.players_handling_with_the_mission:
            productivity += p.productivity
        self.remaining_workload -= delta * productivity
        if self.remaining_workload < -0.01:
            raise Exception("Negative workload to mission" + str(self.mission_id))

    def add_allocated_player(self, player):
        if player in self.players_allocated_to_the_mission:
            raise Exception("Double allocation of the same player to one mission: player " + str(player.id_))
        self.players_allocated_to_the_mission.append(player)

    def add_handling_player(self, player):
        if player in self.players_handling_with_the_mission:
            raise Exception("Double handling of the the same player to one mission" + str(self.mission_id))
        self.players_handling_with_the_mission.append(player)

    def remove_allocated_player(self, player):
        if player not in self.players_allocated_to_the_mission:
            raise Exception("Allocated player is not exist in the mission" + str(self.mission_id))
        self.players_allocated_to_the_mission.remove(player)

    def remove_handling_player(self, player):
        if player.status == Status.ON_MISSION:
            if player not in self.players_handling_with_the_mission:
                raise Exception("Allocated player is not exist in the mission")
            self.players_handling_with_the_mission.remove(player)
        self.remove_allocated_player(player)

    def __hash__(self):
        return hash(self.mission_id)

    def __eq__(self, other):
        return self.mission_id == other.mission_id

    def __str__(self):
        return str(self.mission_id)


class TaskSimple(Entity):
    """
    Class that represents a simple task in the simulation
    """

    def __init__(self, id_, location, importance, missions_list: list, arrival_time=0):
        """
        :param id_: The id of the task
        :type  id_: str
        :param location: The location of the task
        :type location: list of float
        :param importance: The importance of the task
        :type importance: int
        :param missions_list: the missions of the
        :param type_: The type of the task
        :type type_: int
        :param player_responsible, simulation will assign a responsible player to perform that algorithmic task
        computation and message delivery
        """
        Entity.__init__(self, id_, location, arrival_time)
        self.missions_list = missions_list
        self.player_responsible = None
        self.importance = importance
        self.arrival_time = arrival_time
        self.done_missions = []
        self.is_done = False

    def create_neighbours_list(self, players_list,
                               f_is_player_can_be_allocated_to_mission=is_player_can_be_allocated_to_task):
        """
        Creates 
        :param players_list:
        :param f_is_player_can_be_allocated_to_mission:
        :return:
        """
        for a in players_list:
            if f_is_player_can_be_allocated_to_mission(self, a):
                self.neighbours.append(a.id_)

    def update_workload_for_missions(self, tnow):

        for m in self.missions_list:
            m.update_workload(tnow)
        self.update_time(tnow)

    def mission_finished(self, mission):
        self.missions_list.remove(mission)
        self.done_missions.append(mission)
        if len(self.missions_list) == 0:
            self.is_done = True


def amount_of_task_responsible(player):
    return len(player.tasks_responsible)


def find_and_allocate_responsible_player(task: TaskSimple, players):
    distances = []
    for player in players:
        # for mission in task.missions_list:
        #     for ability in mission.abilities:
        #         if ability in player.abilities:
        distances.append(calculate_distance(task, player))

    min_distance = min(distances)

    players_min_distances = []

    for player in players:
        if calculate_distance(task, player) == min_distance:
            # for mission in task.missions_list:
            #     for ability in mission.abilities:
            #         if ability in player.abilities:
            players_min_distances.append(player)

    selected_player = min(players_min_distances, key=amount_of_task_responsible)
    selected_player.tasks_responsible.append(task)
    task.player_responsible = selected_player


class MapSimple:
    """
    Class that represents the map for the simulation. The tasks and the players must be located using generate_location
    method. The simple map is in the shape of rectangle (with width and length parameters).
    """

    def __init__(self, number_of_centers=3, seed=1, length=9.0, width=9.0):
        """
        :param number_of_centers: number of centers in the map. Each center represents a possible base for the player.
        :type: int
        :param seed: seed for random object
        :type: int
        :param length: The length of the map
        :type: float
        :param width: The length of the map
        :type: float
        """
        self.length = length
        self.width = width
        self.rand = random.Random(seed)
        self.centers_location = []
        for _ in range(number_of_centers):
            self.centers_location.append(self.generate_location())

    def generate_location(self):
        """
        :return: random location on the map
        :rtype: list of float
        """
        x1 = self.rand.random()
        x2 = self.rand.random()
        return [self.width * x1, self.length * x2]

    def get_center_location(self):
        return self.rand.choice(self.centers_location)


class MapHubs(MapSimple):
    def __init__(self, number_of_centers=3, seed=1, length_y=9.0, width_x=9.0, sd_multiplier=0.5):
        MapSimple.__init__(self, number_of_centers, seed, length_y, width_x)
        self.sd_multiplier = sd_multiplier

    def generate_location_gauss_around_center(self):
        rand_center = self.get_center_location()
        valid_location = False
        while not valid_location:
            ans = self.generate_gauss_location(rand_center)
            if 0 < ans[0] < self.width and 0 < ans[1] < self.length:
                valid_location = True
        return ans

    def generate_gauss_location(self, rand_center):
        x_center = rand_center[0]
        x_sd = self.width * self.sd_multiplier
        rand_x = self.rand.gauss(mu=x_center, sigma=x_sd)

        y_center = rand_center[1]
        y_sd = self.length * self.sd_multiplier
        rand_y = self.rand.gauss(mu=y_center, sigma=y_sd)
        return [rand_x, rand_y]

class PlayerGenerator(ABC):
    def __init__(self, map_=MapSimple(seed=1), seed=1):
        """

        :param map_:
        :param seed:
        """
        self.map = map_
        self.random = random.Random(seed)

    @abc.abstractmethod
    def get_player(self):
        """
        :rtype: TaskSimple
        """
        return NotImplementedError



class TaskGenerator(ABC):
    def __init__(self, map_=MapSimple(seed=1), seed=1):
        """

        :param map_:
        :param seed:
        """
        self.map = map_
        self.random = random.Random(seed)
        self.rnd_numpy = np.random.default_rng(seed=seed)

    @abc.abstractmethod
    def get_task(self, tnow):
        """
        :rtype: TaskSimple
        """
        return NotImplementedError

    @abc.abstractmethod
    def time_gap_between_tasks(self):
        return NotImplementedError


class SimulationEvent:
    """
    Class that represents an event in the simulation log.
    """

    def __init__(self, time_, player=None, task=None, mission=None):
        """
        :param time_:the time of the event
        :type: float
        :param player: The relevant player for this simulation event. Can be None(depends on extension).
        :type: PlayerSimple
        :param task: The relevant task(task) to this simulation event. Can be None(depends on extension).
        :type: TaskSimple
        :param mission: The relevant mission (of task) for this simulation event. Can be None(depends on extension).
        :type: MissionSimple

        """
        self.time = time_
        self.player = player
        self.mission = mission
        self.task = task

    def __hash__(self):
        return hash(self.time)

    def __lt__(self, other):
        return self.time < other.time

    def handle_event(self, simulation):
        """
        Handle with the task when it arrives in the simulation
        :param simulation: the simulation where the the task appears
        :type: Simulation
        :return:
        """
        raise NotImplementedError

    def __str__(self):
        return "time:" + str(self.time) + "\tevent type:" + str(type(self)) + "\tplayer:" + str(
            self.player) + "\ttask:" + str(
            self.task) + "\tmission:" + str(self.mission)


class EndSimulationEvent(SimulationEvent):
    def handle_event(self, simulation):
        pass

    def __init__(self, time_: float):
        """
        :param time_:the time of the event (Simulation completion time)
        :type: float
        """
        SimulationEvent.__init__(self, time_=time_)


class TaskArrivalEvent(SimulationEvent):
    """
    Class that represent an simulation event of new task arrival.
    """

    def __init__(self, time_: float, task: TaskSimple):
        """
        :param time_:the time of the event
        :type: float
        :param task: The new task that arrives to simulation.
        :type: TaskSimple
        """
        SimulationEvent.__init__(self, time_=time_, task=task)

    def handle_event(self, simulation):
        find_and_allocate_responsible_player(task=self.task, players=simulation.players_list)
        simulation.tasks_list.append(self.task)
        simulation.solver.add_task_to_solver(self.task)
        simulation.solve()
        simulation.generate_new_task_to_diary()


class PlayerArriveToEMissionEvent(SimulationEvent):
    """
    Class that represent an event of player's arrival to the mission.
    """

    def __init__(self, time_, player, task, mission):
        """
        :param time_:the time of the event
        :type: float
        :param player: The relevant player that arrives to the given mission on the given task.
        :type: PlayerSimple
        :param task: The relevant task that contain the given mission
        :type: TaskSimple
        :param mission: The mission that the player arrives to.
        :type: MissionSimple
        """
        SimulationEvent.__init__(self, time_=time_, task=task, mission=mission, player=player)

    def handle_event(self, simulation):
        self.mission.add_handling_player(self.player)
        simulation.generate_agent_finish_handle_mission_event(mission=self.mission, player=self.player, task=self.task)


class PlayerFinishHandleMissionEvent(SimulationEvent):
    """
    Class that represent an event of player finished to handle  with the mission.
    """

    def __init__(self, time_, player, task, mission):
        """
        :param time:the time of the event
        :type: float
        :param player: The relevant player that arrives to the given mission on the given task.
        :type: PlayerSimple
        :param task: The relevant task that contain the given mission
        :type: TaskSimple
        :param mission: The mission that the player arrives to.
        :type: MissionSimple
        """
        SimulationEvent.__init__(self, time_=time_, task=task, mission=mission, player=player)

    def handle_event(self, simulation):
        self.mission.remove_handling_player(player=self.player)
        if len(self.player.schedule) >= 1:
            simulation.generate_player_arrives_to_mission_event(player=self.player)
        else:
            self.player.update_status(Status.IDLE, self.time)
            self.player.current_mission = None
            self.player.current_task = None

        if self.mission.is_done:
            print("mission ended:", self.task.id_)
            self.task.mission_finished(self.mission)
            # TODO check palyers on the event
            if self.task.is_done:
                simulation.handle_task_ended(self.task)
                print("task ended:", self.task.id_)




class Simulation:
    def __init__(self, name: str, players_list: list, solver, tasks_generator: TaskGenerator, end_time: float,
                 f_are_players_neighbours=are_neighbours,
                 f_is_player_can_be_allocated_to_task=is_player_can_be_allocated_to_task,
                 f_calculate_distance=calculate_distance, debug_mode=False):
        """
        :param name: The name of simulation
        :param players_list: The list of the players(players) that are participate
        :param solver: The algorithm that solve the task allocation problem
        :param tasks_generator: Task generator
        :param end_time: Simulation completion time
        :param f_are_players_neighbours: functions that checks if the players are player
        :param f_is_player_can_be_allocated_to_task: The function checks if the player can be allocated to mission
        :param f_calculate_distance: calculate the distance
        """
        self.tnow = 0
        self.prev_time = 0
        self.last_event = None
        self.name = name
        self.diary = []
        # players initialization
        self.players_list = players_list
        self.solver = solver
        self.solver.add_players_list(players_list)
        self.f_are_players_neighbours = f_are_players_neighbours
        # tasks initialization
        self.f_is_player_can_be_allocated_to_mission = f_is_player_can_be_allocated_to_task
        self.tasks_generator = tasks_generator
        self.f_calculate_distance = f_calculate_distance
        self.generate_new_task_to_diary()
        self.tasks_list = []
        self.finished_tasks_list = []
        self.diary.append(EndSimulationEvent(time_=end_time))
        self.debug_mode = debug_mode
        self.solver_counter = 0
        self.run_simulation()

    def run_simulation(self):
        while True:
            self.diary = sorted(self.diary, key=lambda event: event.time)
            self.last_event = self.diary.pop(0)
            if self.debug_mode:
                print(self.last_event)
            if type(self.last_event) == EndSimulationEvent:
                break
            self.prev_time = self.tnow
            self.tnow = self.last_event.time
            self.update_workload()
            self.last_event.handle_event(self)

    def solve(self):
        self.solver_counter = self.solver_counter + 1
        if self.debug_mode:
            print("SOLVER STARTS:", self.solver_counter)
        self.update_locations_of_players()
        self.solver.solve(self.tnow)
        self.check_new_allocation()

    def check_new_allocation(self):
        for player in self.players_list:
            if player.current_mission is None:  # The agent doesn't have a current mission
                if len(player.schedule) == 0:  # The agent doesn't have a new allocation
                    player.update_status(Status.IDLE, self.tnow)
                else:  # The agent has a new allocation
                    self.generate_player_arrives_to_mission_event(player=player)

            else:  # The player has a current allocation
                if len(player.schedule) == 0:  # Player doesn't have a new allocation (only the old one)
                    self.handle_abandonment_event(player=player)
                    player.update_status(Status.IDLE, self.tnow)
                else:  # The player has a new allocation
                    if player.schedule[0][1] == player.current_mission:
                        if player.status == Status.ON_MISSION:
                            player.schedule.pop(0)
                        # The current allocation is similar to old allocation
                        pass
                    else:  # The player abandons his current event to a new allocation
                        self.handle_abandonment_event(player=player)
                        self.generate_player_arrives_to_mission_event(player=player)

    def update_workload(self):
        for t in self.tasks_list:
            t.update_workload_for_missions(self.tnow)

    def update_locations_of_players(self):
        for player in self.players_list:
            player.calculate_relative_location(self.tnow)

    def handle_abandonment_event(self, player: PlayerSimple):
        player.current_mission.remove_handling_player(player)
        player.current_mission = None
        player.current_task = None
        if player.status == Status.ON_MISSION:
            self.remove_player_finish_handle_mission_event_from_diary(player)
        else:
            self.remove_player_arrive_to_mission_event_from_diary(player)

        # self.generate_finish_handle_mission_event(mission=mission)

    def remove_player_finish_handle_mission_event_from_diary(self, player: PlayerSimple):
        for ev in self.diary:
            if type(ev) == PlayerFinishHandleMissionEvent and ev.player.id_ == player.id_:
                self.diary.remove(ev)

    def remove_player_arrive_to_mission_event_from_diary(self, player: PlayerSimple):
        for ev in self.diary:
            if type(ev) == PlayerArriveToEMissionEvent and ev.player.id_ == player.id_:
                self.diary.remove(ev)

    def handle_task_ended(self, task):
        self.finished_tasks_list.append(task)
        #task.task_utiliy() #TODO sofi had a mistake
        self.tasks_list.remove(task)

    def generate_new_task_to_diary(self):
        """
        The method generates new task from task generator, creates neighbour list for the task and add TaskArrivalEvent
        to the diary.
        """
        task: TaskSimple = self.tasks_generator.get_task(self.tnow)
        task.create_neighbours_list(players_list=self.players_list,
                                    f_is_player_can_be_allocated_to_mission=
                                    self.f_is_player_can_be_allocated_to_mission)
        event = TaskArrivalEvent(task=task, time_=task.arrival_time)
        self.diary.append(event)

    def generate_player_arrives_to_mission_event(self, player):
        player.update_status(Status.TO_MISSION, self.tnow)
        next_task = player.schedule[0][0]
        next_mission = player.schedule[0][1]
        player.current_mission = next_mission
        player.current_task = next_task
        next_mission.add_allocated_player(player)
        travel_time = self.f_calculate_distance(player, next_task) / player.speed
        self.diary.append(
            PlayerArriveToEMissionEvent(time_=self.tnow + travel_time, task=next_task, mission=next_mission,
                                        player=player))

    def generate_agent_finish_handle_mission_event(self, player: PlayerSimple, mission: MissionSimple,
                                                   task: TaskSimple):
        player.update_status(Status.ON_MISSION, self.tnow)
        player.update_location(task.location, self.tnow)

        duration = player.schedule[0][2]
        player.schedule.pop(0)
        self.diary.append(
            PlayerFinishHandleMissionEvent(player=player, time_=self.tnow + duration, mission=mission, task=task))
