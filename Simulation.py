import enum


class Status(enum.Enum):
    IDLE = 0
    ON_MISSION = 1
    TO_MISSION = 2

print("hello world")
class Entity():
    def __init__(self, id_, location, name, type_):
        self.id_ = id_
        self.location = location
        self.name = name
        self.type_ = type_
        self.neighbours = []

    def create_neighbours_list(self, entities_list, f_are_neighbours):
        raise NotImplementedError


def calculate_distance(entity1: Entity, entity2: Entity):
    distance = 0
    n = min(len(entity1.location, len(entity2.location)))
    for i in range(n):
        distance += (entity1.location[i] - entity2.location[i]) ** 2

    return distance ** 0.5


def are_are_neighbours(entity1: Entity, entity2: Entity):
    return True


class SimpleAgent(Entity):
    def __init__(self, id_, location: list, speed: int, name=None, type_=1, status=Status.IDLE):
        Entity.__init__(id_, location, name, type_)
        self.speed = speed
        if name is None:
            self.name = id
        self.status = status
        self.allocated_mission = None
        self.last_time_updated = 0

    def update_status(self, new_status, tnow):
        self.status = new_status
        self.last_time_updated = tnow

    def create_neighbours_list(self, agents_list, f_are_neighbours):
        for a in agents_list:
            if self.id_ != a.id_ and f_are_neighbours(self, a):
                self.neighbours.append(a)


class SimpleMission(Entity):
    def __init__(self, id_, location, name, type_=1):
        Entity.__init__(id_, location, name, type_)
        if name is None:
            self.name = id

    def final_utility(self):
        raise NotImplementedError

    def potential_utility(self, agent: SimpleAgent):
        raise NotImplementedError


class Simulation:
    def __init__(self, name, agents_list, solver, f_are_agents_neighbours, f_is_agent_can_be_allocated_to_mission,
                 mission_generator, f_calculate_distance=calculate_distance):
        self.name = name
        self.agent_list = agents_list
