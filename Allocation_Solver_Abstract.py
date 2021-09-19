import threading

from enum import Enum

import Simulation


# TODO - AGENT ALGORITHM,
def default_communication_disturbance(msg):
    return 0



class UnboundedBuffer():

    def __init__(self):

        self.buffer = []

        self.cond = threading.Condition(threading.RLock())

    def insert(self, list_of_msgs):

        with self.cond:
            self.buffer.append(list_of_msgs)

    def extract(self):

        with self.cond:

            while len(self.buffer) == 0:
                self.cond.wait()

        ans = []

        for msg in self.buffer:

            if msg is None:

                return None

            else:

                ans.append(msg)

        self.buffer = []

        return ans

    def is_buffer_empty(self):

        return len(self.buffer) == 0


class Msg:

    def __init__(self, sender, receiver, information, msg_time, timestamp=0):
        self.sender = sender

        self.receiver = receiver

        self.information = information

        self.msg_time = msg_time

        self.timestamp = timestamp

    def set_time_of_msg(self, delay):
        self.msg_time = self.msg_time + delay


class MsgTaskEntity(Msg):
    def __init__(self, msg: Msg, task_entity):
        Msg.__init__(self, msg.sender, msg.receiver, msg.information, msg.msg_time, msg.timestamp)
        self.task_entity = task_entity


mailer_counter = 0


class ClockObject():
    def __init__(self):
        self.clock = 0.0
        self.lock = threading.RLock()
        self.idle_time = 0.0

    def change_clock_if_required(self, time_of_received_msg: float):
        with self.lock:
            if clock <= time_of_received_msg:
                self.idle_time = self.idle_time + (time_of_received_msg - self.clock)
                self.clock = time_of_received_msg

    def increment_clock(self, atomic_counter: int):
        with self.lock:
            self.clock = self.clock + atomic_counter

    def get_clock(self):
        with self.lock:
            return self.clock


class Mailer(threading.Thread):

    def __init__(self, f_termination_condition, f_global_measurements,
                 f_communication_disturbance=default_communication_disturbance):
        threading.Thread.__init__(self)

        self.id_ = 0
        self.msg_box = []

        # function that returns dict=  {key: str of fields name,function of calculated fields}
        self.f_global_measurements = f_global_measurements
        # function that returns None for msg loss, or a number for NCLO delay
        self.f_communication_disturbance = f_communication_disturbance

        # function received by the user that determines when the mailer should stop iterating and kill threads
        self.f_termination_condition = f_termination_condition

        # TODO update in solver, key = agent, value = buffer  also points as an inbox for the agent
        self.agents_outboxes = {}

        # TODO update in solver, buffer also points as out box for all agents
        self.inbox = None

        # the algorithm agent created by the user will be updated in reset method
        self.agents_algorithm = []

        # mailer's clock
        self.time_mailer = ClockObject()

        self.measurements = {}

    def reset(self, agents_algorithm):
        global mailer_counter
        self.msg_box = []
        mailer_counter = mailer_counter + 1
        self.id_ = mailer_counter
        self.agents_outboxes = {}  # TODO update in allocate
        self.inbox = None  # TODO update in solver
        self.agents_algorithm = agents_algorithm
        self.time_mailer = ClockObject()
        self.measurements = {}

        for key in self.f_global_measurements.keys():
            self.measurements[key] = {}
            self.measurements[key + "_single"] = {}

    def add_out_box(self, key: str, value: UnboundedBuffer):
        self.agents_outboxes[key] = value

    def set_inbox(self, inbox_input: UnboundedBuffer):
        self.inbox = inbox_input

    def run(self) -> None:

        """

        create measurements

        iterate for the first, in constractor all agents initiate their first "synchrnoized" iteration

        iteration includes:

        -  extract msgs from inbox: where the mailer waits for msgs to be sent

        -  place messages in mailers message box with a withdrawn delay

        -  get all the messages that have delivery times smaller in comperision to the the mailers clock

        - deliver messages to the algorithm agents through their unbounded buffer



        the run continue to iterate, and creates measurements at each iteration until the given termination condition is met

        :return:

        """

        self.create_measurements()  # TODO

        self.mailer_iteration(with_update_clock_for_empty_msg_to_send=True)

        while not self.termination_condition(self.agents_algorithm):
            self.create_measurements()  # TODO

            self.self_check_if_all_idle_to_continue()

            self.mailer_iteration(with_update_clock_for_empty_msg_to_send=False)

        self.kill_agents()

    def create_measurements(self):
        current_clock = self.time_mailer.get_clock()  # TODO check if immutable

        for key, value in self.f_global_measurements.items():
            dict_of_the_measure_up_to_now = self.measurements[key]

            measure = value(self.agents_algorithm)

            dict_of_the_measure_up_to_now[current_clock] = measure

            single_agent = self.agents_algorithm[0]

            temp_list = []

            temp_list.append(single_agent)

            measure = value(temp_list)

            dict_of_the_measure_up_to_now = self.measurements[key + "_single"]

            dict_of_the_measure_up_to_now[current_clock] = measure

    def kill_agents(self):

        for out_box in self.agents_outboxes.values():
            out_box.insert(None)

    def self_check_if_all_idle_to_continue(self):

        while self.inbox.is_buffer_empty():

            are_all_idle = self.are_all_agents_idle()

            is_inbox_empty = self.inbox.is_buffer_empty()

            is_msg_box_empty = len(self.msg_box) == 0

            if are_all_idle and is_inbox_empty and not is_msg_box_empty:
                self.should_update_clock_because_no_msg_received()

                msgs_to_send = self.handle_delay()

                self.agents_recieve_msgs(msgs_to_send)

    def mailer_iteration(self, with_update_clock_for_empty_msg_to_send):

        msgs_from_inbox = self.inbox.extract()

        self.place_msgs_from_inbox_in_msgs_box(msgs_from_inbox)

        if with_update_clock_for_empty_msg_to_send:
            self.should_update_clock_because_no_msg_received()

        msgs_to_send = self.handle_delay()

        self.agents_recieve_msgs(msgs_to_send)

    def handle_delay(self):

        """

        get from inbox all msgs with msg_time lower then mailer time

        :return: msgs that will be delivered

        """

        msgs_to_send = []

        new_msg_box_list = []
        current_clock = self.time_mailer.get_clock()  # TODO check if immutable

        for msg in self.msg_box:
            if msg.msg_time <= current_clock:
                msgs_to_send.append(msg)
            else:
                new_msg_box_list.append(msg)
        self.msg_box = new_msg_box_list
        return msgs_to_send

    def place_msgs_from_inbox_in_msgs_box(self, msgs_from_inbox):

        """

        take a message from message box, and if msg is not lost, give it a delay and place it in msg_box

        uses the function recieves as input in consturctor f_communication_disturbance

        :param msgs_from_inbox: all messages taken from inbox box

        :return:

        """

        for msg in msgs_from_inbox:

            self.update_clock_upon_msg_recieved(msg)

            communication_disturbance_output = self.f_communication_disturbance(msg)

            if communication_disturbance_output is not None:
                delay = communication_disturbance_output

                msg.set_time_of_msg(delay)

                self.msg_box.append(msg)

    def update_clock_upon_msg_received(self, msg: Msg):

        """

        prior for msg entering to msg box the mailer's clock is being updated

        if the msg time is larger than

        :param msg:

        :return:

        """

        msg_time = msg.msg_time

        self.time_mailer.change_clock_if_required(msg_time)
        # current_clock = self.time_mailer.get_clock()  # TODO check if immutable
        # if current_clock <= msg_time:
        #    increment_by = msg_time-current_clock
        #    self.time_mailer.increment_clock_by(input_=increment_by)

    def agents_receive_msgs(self, msgs_to_send):

        """

        :param msgs_to_send: msgs that their delivery time is smaller then the mailer's time

        insert msgs to relevant agent's inbox

        """

        msgs_dict_by_reciever_id = self.get_receivers_by_id(msgs_to_send)

        for node_id, msgs_list in msgs_dict_by_reciever_id.items():
            node_id_inbox = self.agents_outboxes[node_id]

            node_id_inbox.insert(msgs_list)

    def get_receivers_by_id(self, msgs_to_send):

        '''

        :param msgs_to_send: msgs that are going to be sent in mailer's current iteration

        :return:  dict with key = receiver and value = list of msgs that receiver need to receive

        '''

        receivers_list = []

        for msg in msgs_to_send:
            receivers_list.append(msg.receiver)

        receivers_set = set(receivers_list)

        ans = {}

        for receiver in receivers_set:

            msgs_of_receiver = []

            for msg in msgs_to_send:
                msgs_of_receiver.append(msg)

            ans[receiver] = msgs_of_receiver

        return ans

    @staticmethod
    def msg_with_min_time(msg: Msg):

        return msg.msg_time

    def should_update_clock_because_no_msg_received(self):

        """

        update the mailers clock according to the msg with the minimum time from the mailers message box

        :return:

        """

        msg_with_min_time = min(self.msg_box, key=Mailer.msg_with_min_time)

        msg_time = msg_with_min_time.msg_time
        self.time_mailer.change_clock_if_required(msg_time)
        # current_clock = self.time_mailer.get_clock()  # TODO check if immutable
        # if msg_time > current_clock:
        #    increment_by = msg_time-current_clock
        #    self.time_mailer.increment_clock_by(input_=increment_by)

    def are_all_agents_idle(self):

        for a in self.agents_algorithm:

            if a.get_is_idle():
                return False

        return True


class AgentAlgorithm(threading.Thread):
    """
    list of abstract methods:
    initialize_algorithm
    --> how does the agent begins algorithm prior to the start() of the thread

    set_receive_flag_to_true_given_msg(msgs):
    --> given msgs received is agent going to compute in this iteration

    get_is_going_to_compute_flag()
    --> return the flag which determins if computation is going to occur

    update_message_in_context(msg)
    --> save msgs in agents context

    compute
    -->  use updated context to compute agents statues and

    get_list_of_msgs
    -->  create and return list of msgs

    get_list_of_msgs
    --> returns list of msgs that needs to be sent

    set_receive_flag_to_false
    --> after computation occurs set the flag back to false

    measurements_per_agent
    --> returns dict with key: str of measure, value: the calculated measure
    """

    def __init__(self, simulation_entity, is_with_timestamp=False):

        threading.Thread.__init__(self)
        self.neighbours_ids_list = {}
        self.is_with_timestamp = is_with_timestamp  # is agent using timestamp when msgs are received
        self.timestamp_counter = 0  # every msg sent the timestamp counter increases by one (see run method)
        self.simulation_entity = simulation_entity  # all the information regarding the simulation entity
        self.atomic_counter = 0  # counter changes every computation
        self.NCLO = ClockObject()  # an instance of an object with
        self.idle_time = 0
        self.is_idle = True
        self.cond = threading.Condition(threading.RLock())  # TODO update in solver
        self.inbox = None  # DONE TODO update in solver
        self.outbox = None
        self.sent_initial_information_flag = False

    def update_cond_for_responsible(self, condition_input:threading.Condition):
        self.cond = condition_input

    def add_neighbour_id(self, id_: str):
        if self.id_ not in self.neighbours_ids_list:
            self.neighbours_ids_list.append(id_)

    def add_task_entity(self, task_entity: Simulation.TaskSimple):
        pass

    def set_inbox(self, inbox_input: UnboundedBuffer):
        self.inbox = inbox_input

    def set_outbox(self, outbox_input: UnboundedBuffer):
        self.outbox = outbox_input

    def set_clock_object_for_responsible(self, clock_object_input):
        self.NCLO = clock_object_input


    def initiate_algorithm(self):
        """
        before thread starts the action in this method will occur
        :return:
        """
        raise NotImplementedError

    def measurements_per_agent(self):
        """
        NotImplementedError
        :return: dict with key: str of measure, value: the calculated measure
        """
        raise NotImplementedError

    # ---------------------- receive_msgs ----------------------

    def receive_msgs(self, msgs: []):

        for msg in msgs:

            if self.is_with_timestamp:

                current_timestamp_from_context = self.get_current_timestamp_from_context(msg)

                if msg.timestamp > current_timestamp_from_context:
                    self.update_message_in_context(msg)
                    self.set_receive_flag_to_true_given_msg(msg)
            else:
                self.update_message_in_context(msg)
                self.set_receive_flag_to_true_given_msg(msg)

        self.update_agent_time(msgs)

    def set_receive_flag_to_true_given_msg(self, msg):

        """
        given msgs received is agent going to compute in this iteration?
        set the relevant computation flag
        :param msg:
        :return:
        """

        raise NotImplementedError

    def get_current_timestamp_from_context(self, msg):

        """
        :param msg: use it to extract the current timestamp from the receiver
        :return: the timestamp from the msg
        """

        return -1

    def update_message_in_context(self, msg):

        '''
        :param msg: msg to update in agents memory
        :return:
        '''

        raise NotImplementedError

    # ---------------------- receive_msgs ----------------------

    def update_agent_time(self, msgs):

        """
        :param msgs: list of msgs received simultaneously
        """
        max_time = self.get_max_time_of_msgs(msgs)
        self.NCLO.change_clock_if_required(max_time)

        # if self.NCLO <= max_time:
        #    self.idle_time = self.idle_time + (max_time - self.NCLO)
        #    self.NCLO = max_time

    def get_max_time_of_msgs(self, msgs):
        max_time = 0
        for msg in msgs:
            time_msg = msg.msg_time
            if time_msg > max_time:
                max_time = time_msg

        return max_time

    # ---------------------- reaction_to_msgs ----------------------

    def reaction_to_msgs(self):

        with self.cond:
            self.atomic_counter = 0
            if self.get_is_going_to_compute_flag() is True:
                self.compute()  # atomic counter must change
                self.timestamp_counter = self.timestamp_counter + 1
                self.NCLO.increment_clock(atomic_counter=self.atomic_counter)
                self.send_msgs()
                self.set_receive_flag_to_false()

    def get_is_going_to_compute_flag(self):
        """
        :return: the flag which determines if computation is going to occur
        """
        raise NotImplementedError

    def compute(self):
        """
       After the context was updated by messages received, computation takes place
       using the new information and preparation on context to be sent takes place
        """
        raise NotImplementedError

    def send_msgs(self):
        msgs = self.get_list_of_msgs()
        self.outbox.insert(msgs)

    def get_list_of_msgs_to_send(self):
        """
        create and return list of msgs to send
        """
        raise NotImplementedError

    def set_receive_flag_to_false(self):
        """
        after computation occurs set the flag back to false
        :return:
        """
        raise NotImplementedError

    def run(self) -> None:

        while True:

            self.set_idle_to_true()

            msgs = self.inbox.extract()  # TODO when finish mailer

            self.set_idle_to_false()

            if msgs is None:
                break

            self.receive_msgs(msgs)
            self.reaction_to_msgs()

    def set_idle_to_true(self):

        with self.cond:
            self.is_idle = True

            self.cond.notify_all()

    def set_idle_to_false(self):

        with self.cond:
            self.is_idle = False

    def get_is_idle(self):

        with self.cond:
            while not self.is_idle:
                self.cond.wait()
            return self.is_idle


class PlayerAlgorithm(AgentAlgorithm):
    def __init__(self, simulation_entity, is_with_timestamp=False):
        AgentAlgorithm.__init__(self, simulation_entity, is_with_timestamp=is_with_timestamp)
        self.task_logs = []
        self.additional_tasks_in_log = []

    def add_task_entity_to_log(self, task_entity: Simulation.TaskSimple):
        if task_entity.id_ not in self.neighbours_ids_list:
            self.add_neighbour_id(task_entity.id_)
        self.task_logs.append(task_entity)

    def receive_msgs(self, msgs: []):
        super().receive_msgs(msgs)
        for msg in msgs:
            if msg.task_entity not in task_logs:
                self.task_logs.append(msg.task_entity)
                self.additional_tasks_in_log.append(msg.task_entity)
                self.add_neighbour_id(msg.task_entity.id_)

    def send_msgs(self):
        super().send_msgs()
        self.additional_tasks_in_log = []


class TaskAlgorithm(AgentAlgorithm):
    def __init__(self, simulation_entity, is_with_timestamp=False):
        AgentAlgorithm.__init__(self, simulation_entity, is_with_timestamp=is_with_timestamp)

    def send_msgs(self):
        msgs = self.get_list_of_msgs()
        ans = []
        for msg in msgs:
            ans.append(MsgTaskEntity(msg, self.simulation_entity))
        msgs = ans
        self.outbox.insert(msgs)


class AllocationSolver():
    def __init__(self,t_now):
        self.tasks_simulation = []
        self.players_simulation = []
        self.last_event = None

    def solve(self, tasks_simulation=[], players_simulation=[],last_event=None) -> {}:
        self.tasks_simulation = tasks_simulation
        self.players_simulation = players_simulation
        self.last_event = last_event
        return self.allocate()

    def allocate(self):
        """
        Use missions and agents to allocate an agent to mission
        :returns dictionary with key = agent and value = mission
        """
        raise NotImplementedError


class AllocationSolverDistributed(AllocationSolver):

    def __init__(self, mailer=None, f_termination_condition=None, f_global_measurements=None,
                 f_communication_disturbance=default_communication_disturbance):
        """

        :param mailer: entity that simulates message delivery (given protocol) between agents
        :param f_termination_condition: function received by the user that determines when the mailer should stop
        :param f_global_measurements: function that returns dictionary=  {key: str of fields name,function of calculated fields
        :param f_communication_disturbance: function that returns None for msg loss, or a number for NCLO delay

        """
        """ 
        """

        AllocationSolver.__init__(self)
        self.agents_algorithm = []
        self.mailer = None
        self.imply_mailer(mailer=mailer, f_termination_condition=f_termination_condition,
                          f_global_measurements=f_global_measurements,
                          f_communication_disturbance=f_communication_disturbance)

    def imply_mailer(self, mailer, f_termination_condition, f_global_measurements, f_communication_disturbance):
        """
        if mailer is received in constructor then use it,
        otherwise use f_termination_condition,f_global_measurements, f_communication_disturbance  to create Mailer
        :param mailer: entity that simulates message delivery (given protocol) between agents
        :param f_termination_condition: function received by the user that determines when the mailer should stop
        :param f_global_measurements: function that returns dictionary=  {key: str of fields name,function of calculated fields
        :param f_communication_disturbance: function that returns None for msg loss, or a number for NCLO delay
        :return: None
        """
        if mailer is None:
            if f_termination_conditionis is not None and f_global_measurements is not None:
                self.mailer = Mailer(f_termination_condition, f_global_measurements, f_communication_disturbance)
            else:
                raise Exception(
                    "Cannot create mailer instance without: dictionary of measurments with function and a termination condition")
        else:
            self.mailer = mailer

    def allocate(self):
        """
        all recommended steps for allocation:
        1. agents_algorithm: create agent algorithm to determine the processes of message received, computation and delivery
        2. connect_entities:
            2.1. connect message boxes of mailer
            2.2. connect neighbours: all necessary connections prior to initiation of the the threads
        3. agents_initialize
        4. mailer.reset(): mailer sets its fields prior to the start() of the threads
        5. mailer.start(): create and start thread
        6. mailer.join(): need mailer to die before finish its allocation process
        :return the allocation at the end of the allocation
        """
        self.agents_algorithm = self.create_agents_algorithm()
        self.connect_entities()
        self.agents_initialize()
        self.mailer.reset(self.agents_algorithm)
        self.mailer.start()
        self.mailer.join()
        return self.mailer.get_allocation_dictionary()  # TODO

    def create_agents_algorithm(self):
        """
        create agent algorithm with the specified implemented
        methods according to the abstract agent class
        :return: list of algorithm agents
        """
        raise NotImplementedError

    def agents_initialize(self):
        """
        determine which of the algorithm agents initializes its algorithmic process
        :return:
        """
        raise NotImplementedError

    def connect_entities(self):
        """
            2.1. connect message boxes of mailer and the algorithm agents so messages will go through mailer
            2.2. connect neighbours: all necessary connections prior to initiation of the the threads
        """
        self.set_msg_boxes()
        self.connect_neighbors()

    def set_msg_boxes(self):
        """
        set the message boxes so they will point to the same object
        mailer's inbox is the outbox of all agents
        agent's outbox is one of the inboxes of the mailers
        """
        mailer_inbox = UnboundedBuffer()
        self.mailer.set_inbox(mailer_inbox)
        for aa in self.agents_algorithm:
            aa.set_outbox(mailer_inbox)
            agent_inbox = UnboundedBuffer()
            self.mailer.add_out_box(aa.id_, agent_inbox)
            aa.set_inbox(agent_inbox)

    def connect_neighbors(self):
        """
        create all connections between agents according to selected algorithm
        """
        raise NotImplementedError


class AllocationSolverTasksPlayersSemi(AllocationSolverDistributed):
    """
    solver were the tasks are also algorithm agents
    """

    def __init__(self, mailer=None, f_termination_condition=None, f_global_measurements=None,
                 f_communication_disturbance=default_communication_disturbance):
        AllocationSolverDistributed.__init__(mailer, f_termination_condition, f_global_measurements,
                                             f_communication_disturbance)
        self.tasks_algorithm = []
        self.players_algorithm = []

    def create_agents_algorithm(self):
        """
        create abstract task_algorithms and abstract player_algorithms list
        :return: combined list of task and player algorithm
        """
        ans = []
        for task in self.tasks_simulation:
            t_task_algorithm = TaskAlgorithm(task)
            self.tasks_algorithm.append(t_task_algorithm)
            ans.append(t_task_algorithm)
        for player in self.players_simulation:
            t_player_algorithm = TaskAlgorithm(player)
            self.tasks_algorithm.append(t_player_algorithm)
            ans.append(t_player_algorithm)
        return ans

    @staticmethod
    def connect_condition(player_algo: PlayerAlgorithm, task_algo: TaskAlgorithm):
        """
        have the same condition for both input algorithms entity
       :param player_algo:
       :param task_algo:
       :return:
       """
        cond = threading.Condition(threading.RLock())
        player_algo.update_cond_for_responsible(cond)
        task_algo.update_cond_for_responsible(cond)

    @staticmethod
    def update_player_log(player_algo: PlayerAlgorithm, task_algo: TaskAlgorithm):
        """
        add task to player's log because player is responsible for it, the players is aware of the task's information
        in the discussed scenario
        :param player_algo:
        :param task_algo:
        :return:
        """
        player_algo.add_task_entity_to_log(task_algo.simulation_entity)

    @staticmethod
    def connect_clock_object(player_algo: PlayerAlgorithm, task_algo: TaskAlgorithm):
        """
        have the same clock for both input algorithm entity
        :param player_algo:
        :param task_algo:
        :return:
        """
        clock_obj = ClockObject()
        player_algo.set_clock_object_for_responsible(clock_obj)
        task_algo.set_clock_object_for_responsible(clock_obj)

    def get_algorithm_agent_by_entity(self, entity_input: Simulation.Entity):
        """
        :param entity_input:
        :return: the algorithm agent that contains the simulation entity
        """
        for agent_algo in self.agents_algorithm:
            if agent_algo.simulation_entity == entity_input:
                return agent_algo
        raise Exception("algorithm agent does not exists")

    def connect_responsible_player_and_agent(self, what_to_connect):
        """
        :param what_to_connect: function with the input of player and task, while using a method of one of the entities
        """
        for player_sim in self.players_simulation:
            player_algorithm = self.get_algorithm_agent_by_entity(player_sim)
            tasks_of_player_simulation = player_sim.tasks_responsible
            for task_sim in tasks_of_player_simulation:
                task_algorithm = self.get_algorithm_agent_by_entity(task_sim)
                what_to_connect(player_algorithm, task_algorithm)

    def update_log_of_players_current_task(self):
        """
        the specified scenario suggests that players are aware of the current information of the tasks they are currently at
        this method updates the relative information at the players log
        :return:
        """
        for player_sim in self.players_simulation:
            player_algorithm = self.get_algorithm_agent_by_entity(player_sim)
            current_task = player_sim.current_task
            if current_task is not None:
                for task_sim in tasks_of_player_simulation:
                    player_algorithm.add_task_entity_to_log(task_sim)

    def connect_neighbors(self):
        """
        implement method
        simulate_players_and_tasks_representation: take care of all connections due to player responsible for a task
        connect_players_to_tasks: update the neighbours list at the task entites. The player entity is already updated
        :return:
        """
        self.simulate_players_and_tasks_representation()
        self.update_log_of_players_current_task()
        self.connect_players_to_tasks()

    def simulate_players_and_tasks_representation(self):
        self.connect_responsible_player_and_agent(AllocationSolverTasksPlayersSemi.connect_condition)
        self.connect_responsible_player_and_agent(AllocationSolverTasksPlayersSemi.update_player_log)
        self.connect_responsible_player_and_agent(AllocationSolverTasksPlayersSemi.connect_clock_object)

    def connect_players_to_tasks(self):
        for task_sim in self.tasks_simulation:
            tasks_neighbours = task_sim.neighbours
            task_algorithm = self.get_algorithm_agent_by_entity(task_sim)
            for player_sim in tasks_neighbours:
                task_algorithm.add_neighbour_id(player_sim.id_)

    def agents_initialize(self):
        for task_algo in self.tasks_algorithm:
            task_algo.initiate_algorithm()

