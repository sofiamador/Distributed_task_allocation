from Simulation_Abstract_Components import TaskSimple, find_and_allocate_responsible_player, Status, TaskGenerator, \
    calculate_distance, are_neighbours, is_player_can_be_allocated_to_task, PlayerSimple, MissionSimple


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
        simulation.generate_agent_finish_handle_mission_event(player=self.player)


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
                simulation.solver.remove_task_from_solver(self.task)


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
        self.remove_player_finish_handle_mission_event_from_diary()
        self.remove_player_arrive_to_mission_event_from_diary()
        self.clean_tasks_form_agents()
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
                else:  # The player has a new allocation (missions in schedule)
                    if player.schedule[0][1] == player.current_mission: # The players remains in his current mission
                        player.current_mission.players_allocated_to_the_mission.append(player)
                        if player.status == Status.ON_MISSION: # If the has already arrived to the mission
                            player.current_mission.players_allocated_to_the_mission.append(player)
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
        player.current_mission = None
        player.current_task = None
        # self.generate_finish_handle_mission_event(mission=mission)

    def handle_task_ended(self, task):
        self.finished_tasks_list.append(task)
        #task.task_utiliy() #TODO sofi had a mistake
        self.tasks_list.remove(task)

    def remove_player_finish_handle_mission_event_from_diary(self):
        for ev in self.diary:
            if type(ev) == PlayerFinishHandleMissionEvent:
                self.diary.remove(ev)

    def remove_player_arrive_to_mission_event_from_diary(self):
        for ev in self.diary:
            if type(ev) == PlayerArriveToEMissionEvent:
                self.diary.remove(ev)

    def clean_tasks_form_agents(self):
        for t in self.tasks_list:
            for m in t.missions_list:
                m.players_allocated_to_the_mission.clear()
                m.players_handling_with_the_mission.clear()

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

    def generate_agent_finish_handle_mission_event(self, player: PlayerSimple):
        mission = player.current_mission
        task = player.current_task
        player.update_status(Status.ON_MISSION, self.tnow)
        player.update_location(task.location, self.tnow)

        duration = player.schedule[0][2]
        player.schedule.pop(0)
        self.diary.append(
            PlayerFinishHandleMissionEvent(player=player, time_=self.tnow + duration, mission=mission, task=task))


