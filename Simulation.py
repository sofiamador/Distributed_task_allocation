import enum, numpy
import random


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

    def __init__(self, id_, location, name, type_):
        """
        :param id_: The id of the entity
        :type  id_: str
        :param location: The location of the entity. A list of of coordination.
        :type location: list of floats
        :param name: The name of the entity
        :type name: str
        :param type_: The type of the entity
        :type type_: int
        """
        self.id_ = id_
        self.location = location
        self.name = name
        self.type_ = type_
        self.neighbours = []

    def create_neighbours_list(self, entities_list, f_are_neighbours):
        """
        Method that populates the neighbours list of the entity. It accepts list of potential neighbours
        ana a function that returns whether a pair of entities are neighbours
        :param entities_list:
        :param f_are_neighbours:
        :return: None
        """
        raise NotImplementedError


def calculate_distance(entity1: Entity, entity2: Entity):
    """
    Calculates the distance between two entities. Each entity must have a location property.
    :param entity1:first entity
    :param entity2:second entity
    :return: Euclidean distance between two entities
    :rtype: float
    """
    distance = 0
    n = min(len(entity1.location, len(entity2.location)))
    for i in range(n):
        distance += (entity1.location[i] - entity2.location[i]) ** 2

    return distance ** 0.5


def are_neighbours(entity1: Entity, entity2: Entity):
    """
    The functions checks if the entities (agents) can be neighbours
    :param entity1: first entity
    :param entity2: second entity
    :return: bool
    """
    return True


class AbilitySimple:
    """
       Class that represents a simple ability that the missions require and the agents have
    """

    def __init__(self, ability_name, max_amount, min_amount=1):
        """
       :param ability_name
       :type ability_name: str
       :param max_amount: maximum amount of required ability
       :type max_amount:float
       :param min_amount: minimum amount of required ability
       :type min_amount:float
        """
        self.ability_name = ability_name
        self.max_amount = max_amount
        self.min_amount = min_amount

    def __hash__(self):
        return hash(self.ability_name)

    def __eq__(self, other):
        return self.ability_name == other.ability_name


class AgentSimple(Entity):
    """
    Class that represents a basic agent in the simulation
    """

    def __init__(self, id_, location, speed, name=None, type_=1, status=Status.IDLE,
                 abilities={AbilitySimple("basic", 1)}):
        """
        :param id_: The id of the agent
        :type  id_: str
        :param location: The location of the agent
        :type location: list of float
        :param name: The name of the agent
        :param type_: The type of the agent
        :type type_: int
        :param status: The status of the agent
        :type  status: Status
        :param abilities: abilities of the agent
        :type  abilities: set of AbilitySimple
        """
        Entity.__init__(id_, location, name, type_)
        self.speed = speed
        if name is None:
            self.name = id
        self.status = status
        self.abilities = abilities

        self.allocated_mission = None
        self.last_time_updated = 0

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

    def __init__(self, mission_id, ability=AbilitySimple("basic", 1), type_=1):
        """
        Simple mission constructor
        :param mission_id:
        :type mission_id: str
        :param ability: The required ability for the mission
        :type ability: AbilitySimple
        :param type_: the type of the mission
        :type type_: int
        """
        self.mission_id = mission_id
        self.ability = ability
        self.type_ = type_

    def mission_utility(self):
        """
        The utility for handling the mission
        :return:
        """
        raise NotImplementedError


class EventSimple(Entity):
    """
    Class that represents a simple event in the simulation
    """

    def __init__(self, id_, location, name, missions: list, type_=1):
        """
        :param id_: The id of the event
        :type  id_: str
        :param location: The location of the event
        :type location: list of float
        :param name: The name of the event
        :type name: str
        :param missions: the missions of the
        :param type_: The type of the event
        :type type_: int
        """
        Entity.__init__(id_, location, name, type_)
        if name is None:
            self.name = id
        self.missions = missions
        self.type_ = type_

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


def is_agent_can_be_allocated_to_event(event: EventSimple, agent: AgentSimple):
    for mission in event.missions:
        if mission.ability in agent.abilities:
            return True


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
            self.centers_location.append(self.geneate_location())

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


class Simulation:
    def __init__(self, name, agents_list, solver, f_are_agents_neighbours, f_is_agent_can_be_allocated_to_mission,
                 events_generator, first_event, f_calculate_distance=calculate_distance):
        self.name = name
        self.agent_list = agents_list
        self.solver = solver
        self.f_are_agents_neighbours = f_are_agents_neighbours
        self.f_is_agent_can_be_allocated_to_mission = f_is_agent_can_be_allocated_to_mission
        self.events_generator = events_generator
        self.f_calculate_distance = calculate_distance
        self.event_list = []
        self.diary = []

    def run_simulation(self):
        pass

    def solve(self):
        self.solver.solve(self.agent_list, self.event_list)
