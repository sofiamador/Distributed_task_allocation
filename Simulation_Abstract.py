import enum
import random
import sys
from datetime import time

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
        :param type_: The type of the entity
        :type type_: int
        :param last_time_updated:

        """
        self.id_ = id_
        self.location = location
        self.neighbours = []
        self.last_time_updated = last_time_updated

    def update_time(self, tnow):
        if tnow >= self.last_time_updated:
            self.last_time_updated = tnow

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
    distance = 0
    n = min(location1, location2)
    for i in range(n):
        distance += (location1[i] - location2[i]) ** 2

    return distance ** 0.5

def calculate_distance_input_location(location1, location2):
    """
    Calculates the distance between two entities. Each entity must have a location property.
    :param entity1:first entity
    :type entity1: Entity
    :param entity2:second entity
    :type entity1: Entity
    :return: Euclidean distance between two entities
    :rtype: float
    """

    distance = 0
    n = min(location1, location2)
    for i in range(n):
        distance += (location1[i] - location2[i]) ** 2

    return distance ** 0.5


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
    for mission in task.missions_list:
        for ability in mission.abilities:
            if ability in player.abilities:
                return True
    return False


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

    def update_status(self, new_status: Status, tnow: float) -> None:
        """
        Updates the status of the player
        :param new_status:the new status of the player
        :param tnow: the time when status of the player is updated
        :return:None
        """
        self.status = new_status
        self.last_time_updated = tnow

    def update_location(self, location, tnow):
        """
        Updates the location of the player
        :param location:
        :param tnow:
        :return:
        """
        self.location = location
        self.last_time_updated = tnow

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


class MissionSimple:
    """
    Class that represents a simple mission (as a part of the task)
    """

    def __init__(self, mission_id, initial_workload, arrival_time_to_the_system,
                 abilities=[AbilitySimple(ability_type=0)],
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

    def mission_utility(self):
        """
        The utility for handling the mission
        :return:
        """
        raise NotImplementedError

    def add_player(self, new_player, tnow):
        self.update_workload(tnow)
        self.players_allocated_to_the_mission.append(new_player)

    def remove_player(self, new_player, tnow):
        self.update_workload(tnow)
        self.players_allocated_to_the_mission.remove(new_player)

    def remove_all_players(self, tnow):
        self.update_workload(tnow)
        self.players_allocated_to_the_mission.clear()

    def update_workload(self, tnow):
        delta = tnow - self.last_updated
        self.workload_updating(delta)
        if self.remaining_workload == sys.float_info.epsilon:
            self.is_done = True
        self.last_updated = tnow

    def workload_updating(self, delta):
        self.remaining_workload -= delta * len(self.players_handling_with_the_mission)

    def __hash__(self):
        return hash(self.mission_id)

    def __eq__(self, other):
        return self.mission_id == other.mission_id


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

    def task_utility(self):
        """
        Calculates the total utility of the task (sum of missions' utilities)
        :return: utility
        :rtype: float
        """
        sum_ = 0
        for m in self.missions_list:
            sum_ += m.mission_utility
        return sum_

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

    def mission_finished(self, mission):
        self.missions_list.remove(mission)
        self.done_missions.append(mission)


def amount_of_task_responsible(player):
    return len(player.tasks_responsible)


def find_and_allocate_responsible_player(task: TaskSimple, players):
    distances = []
    for player in players:
        for mission in task.missions_list:
            for ability in mission.abilities:
                if ability in player.abilities:
                    distances.append(calculate_distance(task, player))

    min_distance = min(distances)

    players_min_distances = []

    for player in players:
        if calculate_distance(task, player) == min_distance:
            for mission in task.missions_list:
                for ability in mission.abilities:
                    if ability in player.abilities:
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


class TaskGenerator:
    def __init__(self, map_=MapSimple(seed=1), seed=1):
        """

        :param map_:
        :param seed:
        """
        self.map = map_
        self.random = random.Random(seed)

    def get_task(self, tnow):
        """
        :rtype: TaskSimple
        """
        return NotImplementedError


class SimulationEvent:
    """
    Class that represents an event in the simulation log.
    """

    def __init__(self, time, player=None, task=None, mission=None):
        """
        :param time:the time of the event
        :type: float
        :param player: The relevant player for this simulation event. Can be None(depends on extension).
        :type: PlayerSimple
        :param task: The relevant task(task) to this simulation event. Can be None(depends on extension).
        :type: TaskSimple
        :param mission: The relevant mission (of task) for this simulation event. Can be None(depends on extension).
        :type: MissionSimple

        """
        self.time = time
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


class TaskArrivalEvent(SimulationEvent):
    """
    Class that represent an simulation event of new task arrival.
    """

    def __init__(self, time: float, task: TaskSimple):
        """
        :param time:the time of the event
        :type: float
        :param task: The new task that arrives to simulation.
        :type: TaskSimple
        """
        SimulationEvent.__init__(self, time=time, task=task)

    def handle_event(self, simulation):
        find_and_allocate_responsible_player(task=self.task, players=simulation.players_list)
        simulation.solver.add_task_to_solver(self.task)
        simulation.solve()
        simulation.generate_new_task_to_diary()


class PlayerArriveToEMissionEvent(SimulationEvent):
    """
    Class that represent an event of player's arrival to the mission.
    """

    def __init__(self, time, player, task, mission):
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
        SimulationEvent.__init__(time=time, task=task, mission=mission, player=player)

    def handle_event(self, simulation):
        self.player.status = Status.ON_MISSION
        self.player.location = self.task.location
        self.mission.players_handling_with_the_mission.append(self.player)
        simulation.generate_finish_handle_mission_event(mission=self.mission, player=self.player)


class FinishHandleMissionEvent(SimulationEvent):
    """
    Class that represent an event of: player finishes to handle  with the mission.
    """

    def __init__(self, time, task, mission):
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
        SimulationEvent.__init__(time=time, task=task, mission=mission)

    def handle_event(self, simulation):
        for p in self.mission.players_handling_with_the_mission:
            p.current_mission = None
        self.mission.is_done = True
        self.task.mission_finished(self.mission)
        simulation.solve()


class PlayerFinishHandleMissionEvent(SimulationEvent):
    """
    Class that represent an event of: player finishes to handle  with the mission.
    """

    def __init__(self, time, player, task, mission):
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
        SimulationEvent.__init__(time=time, task=task, mission=mission, player=player)

    def handle_event(self, simulation):
        simulation.solve()


class Simulation:
    def __init__(self, name: str, players_list: list, solver, tasks_generator, f_are_players_neighbours=are_neighbours,
                 f_is_player_can_be_allocated_to_task=is_player_can_be_allocated_to_task,
                 f_calculate_distance=calculate_distance):
        """

        :param name: The name of simulation
        :param players_list: The list of the players(players) that are participate
        :param solver: The algorithm that solve the task allocation problem
        :param f_are_players_neighbours: functions that checks if the players are player
        :param f_is_player_can_be_allocated_to_task: The function checks if the player can be allocated to mission
        :param tasks_generator:
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

        self.f_is_player_can_be_allocated_to_mission = f_is_player_can_be_allocated_to_task
        self.tasks_generator = tasks_generator
        self.f_calculate_distance = f_calculate_distance
        self.generate_new_task_to_diary()
        self.new_allocation = None
        self.tasks_list = []

    def run_simulation(self):
        while not self.diary:
            self.diary = sorted(self.diary, key=lambda event: event.time)
            self.last_event = self.diary.pop(0)
            self.prev_time = self.tnow
            self.tnow = self.last_event.time
            self.update_workload()
            self.last_event.handle_event(self)

    def solve(self):

        self.new_allocation: dict = self.solver.solve(self.tnow)  # {player:[(task,mission,time)]}
        self.check_new_allocation()

    def generate_new_task_to_diary(self):
        task: TaskSimple = self.tasks_generator.get_task(self.tnow)
        task.create_neighbours_list(players_list=self.players_list,
                                    f_is_player_can_be_allocated_to_mission=self.f_is_player_can_be_allocated_to_mission)
        event = TaskArrivalEvent(task=task, time=task.arrival_time)
        self.diary.append(event)

    def check_new_allocation(self):
        for player, missions in self.new_allocation:
            if player.current_mission is None:  # The agent doesn't have a current mission
                if len(missions) == 0:  # The agent doesn't have a new allocation
                    player.status = Status.IDLE
                else:  # The agent has a new allocation
                    self.generate_player_arrives_to_mission_event(player=player, task=missions[0], mission=missions[1])

            else:  # The player has a current allocation
                if len(missions) == 0:  # Player doesn't have a new allocation
                    player.status = Status.IDLE
                    # TODO sent to the base
                else:  # The player has a new allocation
                    if missions[1] == player.current_mission:  # The current allocation is similar to old allocation
                        pass
                    else:  # The player abandons his current event to a new allocation
                        self.handle_abandonment_event(player=player, task=missions[0], mission=missions[1])

    def update_workload(self):
        for e in self.tasks_list:
            e.update_workload_for_missions(self.tnow)

    def generate_player_arrives_to_mission_event(self, player, task, mission):

        player.status = Status.TO_MISSION
        player.current_mission = mission
        player.current_task = task
        mission.players_allocated_to_the_mission.append(player)
        travel_time = self.f_calculate_distance(player, task) / player.speed
        self.diary.append(PlayerArriveToEMissionEvent(time=self.tnow + travel_time, task=task, mission=mission,
                                                      player=player))

    def handle_abandonment_event(self, player: PlayerSimple, task: TaskSimple, mission: MissionSimple):
        player.current_mission.players_allocated_to_the_mission.remove(player)
        player.current_mission.players_handling_with_the_mission.remove(player)
        self.generate_player_arrives_to_mission_event(player=player, task=task, mission=mission)
        self.generate_finish_handle_mission_event(mission=mission)

    def generate_finish_handle_mission_event(self, mission: MissionSimple):
        for ev in self.diary:
            if type(ev) == FinishHandleMissionEvent and ev.mission.mission_id == mission.mission_id:
                self.diary.remove(ev)
        productivity_sum = 0
        for p in mission.players_handling_with_the_mission:
            productivity_sum += p.productivity
        time_to_end_mission = mission.remaining_workload / productivity_sum
        event = FinishHandleMissionEvent(mission=mission, time=self.tnow + time_to_end_mission)
        self.diary.append(event)
