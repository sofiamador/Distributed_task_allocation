import enum
import random
import sys


class Status(enum.Enum):
    """
    Enum that represents the status of the agent in the simulation
    """
    IDLE = 0
    ON_MISSION = 1
    TO_MISSION = 2


class Entity:
    """
    Class that represents a basic entity in the simulation
    """

    def __init__(self, id_, location):
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
        self.last_time_updated = 0

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
        return self.id_ == other.id


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
    distance = 0
    n = min(len(entity1.location), len(entity2.location))
    for i in range(n):
        distance += (entity1.location[i] - entity2.location[i]) ** 2

    return distance ** 0.5


def are_neighbours(entity1: Entity, entity2: Entity):
    """
    The functions checks if the entities (agents) can be neighbours
    :param entity1: first entity
    :type entity1: Entity
    :param entity2: second entity
    :type entity1: Entity
    :return: bool
    """
    return True


class AbilitySimple:
    """
       Class that represents a simple ability that the missions require and the agents have
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


class PlayerSimple(Entity):
    """
    Class that represents a basic agent in the simulation
    """

    def __init__(self, id_, location, speed, status=Status.IDLE,
                 abilities=None):
        """
        :param id_: The id of the agent
        :type  id_: str
        :param location: The location of the agent
        :type location: list of float
        :param status: The status of the agent
        :type  status: Status
        :param abilities: abilities of the agent
        :type  abilities: set of AbilitySimple
        :param current_task: The current task that was allocated to agent. If the the agent is idle this field will be None.
        :type current_task: TaskSimple
        :param current_mission: The current sub-task of the agent. If the the agent is idle this field will be None.
        :type current_mission: MissionSimple

        """
        Entity.__init__(id_, location)
        if abilities is None:
            abilities = [AbilitySimple(ability_type=0)]
        self.speed = speed
        self.status = status
        self.abilities = abilities
        self.current_task = None
        self.current_mission = None
        self.tasks_responsible = []

    def update_status(self, new_status: Status, tnow: float) -> None:
        """
        Updates the status of the agent
        :param new_status:the new status of the agent
        :param tnow: the time when status of the agent is updated
        :return:None
        """
        self.status = new_status
        self.last_time_updated = tnow

    def update_location(self, location, tnow):
        """
        Updates the location of the agent
        :param location:
        :param tnow:
        :return:
        """
        self.location = location
        self.last_time_updated = tnow

    def create_neighbours_list(self, agents_list, f_are_neighbours):
        """
        creates neighbours list of agents
        :param agents_list:
        :param f_are_neighbours:
        :return:None
        """
        self.neighbours = []
        for a in agents_list:
            if self.id_ != a.id_ and f_are_neighbours(self, a):
                self.neighbours.append(a)

    def personal_utility(self, event, ability):
        """
        calculates personal utility of the agent from the event using specific ability
        :param event:
        :param ability:
        :return: personal utility
        :rtype: float
        """
        raise NotImplementedError


class MissionSimple:
    """
    Class that represents a simple mission (as a part of the event)
    """

    def __init__(self, mission_id,initial_workload,arrival_time_to_the_system, ability=[AbilitySimple(ability_type=0)],
                 min_players=1,max_players=1):
        """
        Simple mission constructor
        :param mission_id: Mission's id
        :type mission_id: str
        :param initial_workload: The required workload of the mission (in seconds)
        :type initial_workload: float
        :param arrival_time_to_the_system: The time that task (with the mission)  arrived
        :param ability:
        :param min_players:
        :param max_players:
        """

        self.mission_id = mission_id
        self.ability = ability
        self.min_players = min_players
        self.max_players = max_players
        self.initial_workload = initial_workload
        self.remaining_workload = initial_workload
        self.current_players_list = []
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
        self.current_players_list.append(new_player)

    def update_workload(self,tnow):
        delta = tnow - self.last_updated
        self.remaining_workload -= delta*len(self.current_players_list)
        if self.remaining_workload == sys.float_info.epsilon:
            self.is_done = True



class TaskSimple(Entity):
    """
    Class that represents a simple event in the simulation
    """

    def __init__(self, id_, location, importance, missions: list):
        """
        :param id_: The id of the event
        :type  id_: str
        :param location: The location of the event
        :type location: list of float
        :param importance: The importance of the event
        :type importance: int
        :param missions: the missions of the
        :param type_: The type of the event
        :type type_: int
        :param player_responsible, simulation will assign a responsible player to perform that algorithmic task
        computation and message delivery
        """
        Entity.__init__(id_, location)
        self.missions = missions
        self.player_responsible = None
        self.importance =  importance

    def event_utility(self):
        """
        Calculates the total utility of the event (sum of missions' utilities)
        :return: utility
        :rtype: float
        """
        self.sum_ = 0
        for m in self.missions:
            self.sum_ += m.mission_utility
        return self.sum_

    def create_neighbours_list(self, agents_list, f_is_agent_can_be_allocated_to_mission):
        """
        Creates 
        :param agents_list:
        :param f_is_agent_can_be_allocated_to_mission:
        :return:
        """
        for a in agents_list:
            if self.id_ != a.id_ and f_is_agent_can_be_allocated_to_mission(self, a):
                self.neighbours.append(a)


def is_agent_can_be_allocated_to_event(task: TaskSimple, agent: PlayerSimple):
    """
    Function that checks if the agent can be allocated to an task according to agent's abilities and required abilities
    to the task.
    :param task: The task that is checked.
    :type task: TaskSimple
    :param agent: The agent that is checked if it suitable for the task according to hos abilities.
    :return:
    """
    for mission in task.missions:
        if mission.ability in agent.abilities:
            return True


def amount_of_task_responsible(player):
    return len(player.tasks_responsible)


def find_responsible_agent(task: TaskSimple, players):
    distances = []
    for player in players:
        distances.append(calculate_distance(task, player))

    min_distance = min(distances)

    players_min_distances = []

    for player in players:
        if calculate_distance(task, player) == min_distance:
            players_min_distances.append(player)

    selected_player = min(players_min_distances, key=amount_of_task_responsible)
    selected_player.tasks_responsible.append(task)
    task.player_responsible = selected_player


class MapSimple:
    """
    Class that represents the map for the simulation. The events and the agents must be located using generate_location
    method. The simple map is in the shape of rectangle (with width and length parameters).
    """

    def __init__(self, number_of_centers=3, seed=1, length=9.0, width=9.0):
        """
        :param number_of_centers: number of centers in the map. Each center represents a possible base for the agent.
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
        for _ in number_of_centers:
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

    def generate_location(self):
        rand_center = self.get_center_location()
        valid_location = False
        while not valid_location:
            ans = self.generate_gauss_location(rand_center)
            if 0 < ans[0] < self.width_x and 0 < ans[1] < self.length_y:
                valid_location = True
        return True

    def generate_gauss_location(self, rand_center):
        x_center = rand_center[0]
        x_sd = self.width_x * self.sd_multiplier
        rand_x = self.rand.gauss(mu=x_center, sigma=x_sd)

        y_center = rand_center[1]
        y_sd = self.length_y * self.sd_multiplier
        rand_y = self.rand.gauss(mu=y_center, sigma=y_sd)
        return [rand_x, rand_y]


class TaskGenerator():
    def __init__(self, map_=MapSimple(seed=1), seed=1):
        """

        :param map_:
        :param seed:
        """
        self.map = map_
        self.random = random.Random(seed)

    def get_task(self):
        return NotImplementedError



class SimulationEvent():
    """
    Class that represents an event in the simulation log.
    """

    def __init__(self, time, agent=None, task=None, mission=None):
        """
        :param time:the time of the event
        :type: float
        :param agent: The relevant agent for this simulation event. Can be None(depends on extension).
        :type: AgentSimple
        :param task: The relevant event(task) to this simulation event. Can be None(depends on extension).
        :type: EventSimple
        :param mission: The relevant mission (of tasl) for this simulation event. Can be None(depends on extension).
        :type: MissionSimple
        :param task: The relevant task for this simulation event. Can be None(depends on extension).
        :type: TaskSimple
        """
        self.time = time
        self.agent = agent
        self.mission = mission
        self.task = task

    def __hash__(self):
        return hash(self.time)

    def __lt__(self, other):
        return self.time < other.time

    def handle_event(self, simulation):
        """
        Handle with the event when it arrives in the simulation
        :param simulation: the simulation where the the event appears
        :type: Simulation
        :return:
        """
        raise NotImplementedError


class TaskArrivalEvent(SimulationEvent):
    """
    Class that represent an simulation event of new Event(task) arrival.
    """

    def __init__(self, time: float, task: TaskSimple):
        """
        :param time:the time of the event
        :type: float
        :param event: The new event that arrives to simulation.
        :type: TaskSimple
        """
        SimulationEvent.__init__(time=time, task=task)

    def handle_event(self, simulation):
        find_responsible_agent()
        simulation.solver.add_task_to_solver(self.task)
        simulation.solve()
        simulation.check_new_allocation()  # TODO can be a part of the solve method in simulation
        simulation.generate_new_event()


class AgentArriveToEMissionEvent(SimulationEvent):
    """
    Class that represent an event of agent's arrival to the mission.
    """

    def __init__(self, time, agent, event, mission):
        """
        :param time:the time of the event
        :type: float
        :param agent: The relevant agent that arrives to the given mission on the given event.
        :type: AgentSimple
        :param event: The relevant event(task) that contain the given mission
        :type: EventSimple
        :param mission: The mission that the agent arrives to.
        :type: MissionSimple
        """
        SimulationEvent.__init__(time=time, event=event, mission=mission, agent=agent)

    def handle_event(self, simulation):
        simulation.create_agent_finiish_handle_mission_event()


class AgentFinishHandleMissionEvent(SimulationEvent):
    """
    Class that represent an event of: agent finishes to handle  with the mission.
    """

    def __init__(self, time, agent, event, mission):
        """
        :param time:the time of the event
        :type: float
        :param agent: The relevant agent that arrives to the given mission on the given event.
        :type: AgentSimple
        :param event: The relevant event(task) that contain the given mission
        :type: EventSimple
        :param mission: The mission that the agent arrives to.
        :type: MissionSimple
        """
        SimulationEvent.__init__(time=time, event=event, mission=mission, agent=agent)

    def handle_event(self, simulation):
        simulation.solve()
        simulation.check_new_allocation()  # TODO can be a part of the solve method in simulation


class Simulation:
    def __init__(self, name, players_list, solver, f_are_agents_neighbours, f_is_agent_can_be_allocated_to_mission,
                 events_generator, first_event, f_calculate_distance=calculate_distance):
        self.tnow = 0
        self.last_event = None
        self.name = name
        self.agent_list = players_list
        self.solver = solver
        self.solver.add_players_list()
        self.f_are_agents_neighbours = f_are_agents_neighbours
        self.f_is_agent_can_be_allocated_to_mission = f_is_agent_can_be_allocated_to_mission
        self.events_generator = events_generator
        self.f_calculate_distance = calculate_distance
        self.event_list = []
        self.diary = []

    def run_simulation(self):
        pass

    def solve(self):
        self.solver.solve(self.last_event)

    def generate_new_event(self):
        self.events_generator.get_event()
