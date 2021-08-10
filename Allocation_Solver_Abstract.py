import threading
from enum import Enum
import Simulation

# TODO - AGENT ALGORITHM,

class AllocationSolver():
    def __init__(self):
        self.missions_simulation = None
        self.agents_simulation = None
        self.mailer = None

    def solve(self, missions_simulation, agents_simulation, mailer=None) -> {}:
        self.missions_simulation = missions_simulation
        self.agents_simulation = agents_simulation
        self.mailer = mailer
        self.allocate()

    def allocate(self):
        """
        Use missions and agents to allocate an agent to mission
        :returns dictionary with key = agent and value = mission
        """
        raise NotImplementedError


class AllocationSolverDistributed(AllocationSolver):
    def __init__(self, missions_simulation, agents_simulation, mailer=None):

        AllocationSolver.__init__(missions_simulation, agents_simulation, mailer)

    def allocate(self):
        """
        distributed version step recommendation using mailer
        """
        self.agents_algorithm = self.create_agents_algorithm()
        self.create_graphs()
        self.mailer.update_fields()
        self.mailer.start()

    def create_graphs(self):
        raise NotImplementedError

    def create_agents_algorithm(self):
        raise NotImplementedError



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

mailer_counter = 0


def default_communication_disturbance(msg):
    return 0


class Mailer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.id_ = 0
        self.msg_box = []

        # function that returns dict=  {key: str of fields name,function of calculated fields}
        self.f_global_measurements = None
        # function that returns None for msg loss, or a number for NCLO delay
        self.f_communication_disturbance = None

        # function received by the user that determines when the mailer should stop iterating and kill threads
        self.f_termination_condition = None

        # TODO update in solver, key = agent, value = buffer  also points as an inbox for the agent
        self.agents_outboxes = {}

        # TODO update in solver, buffer also points as out box for all agents
        self.inbox = None

        # the algorithm agent created by the user
        self.agents_algorithm = []

        # mailer's clock
        self.time_mailer = 0

        self.measurements = {}

    def update_fields(self, agents_algorithm, f_termination_condition, f_global_measurements,
                      f_communication_disturbance=default_communication_disturbance):
        """
        :param agents_algorithm: the algorithm agent created by the user
        :param f_termination_condition: function received by the user that determines when the mailer should stop
                iterating and kills threads, input: list of algorithm agents, output: boolean (is run over)
        :param f_global_measurements:  function that returns dict=  {key: str of fields name,function of calculated fields},
        each function receieves list of algorithm agents
        :param f_communication_disturbance: function that returns None for msg loss, or a number for NCLO delay

        initiates all agents, their actions before the run
        :return:
        """

        global mailer_counter
        self.msg_box = []
        mailer_counter = mailer_counter + 1
        self.id_ = mailer_counter
        self.f_communication_disturbance = f_communication_disturbance
        self.agents_outboxes = {}  # TODO update in allocate
        self.inbox = None  # TODO update in solver
        self.agents_algorithm = agents_algorithm
        self.time_mailer = 0
        self.f_termination_condition = f_termination_condition
        self.f_global_measurements = f_global_measurements
        self.measurements = {}

        for key in f_global_measurements.keys():
            self.measurements[key] = {}
            self.measurements[key + "_single"] = {}

       # for key in f_agent_measurements.keys():
        #    self.measurements[key + "_avg"] = {}
         #   self.measurements[key + "_min"] = {}
          #  self.measurements[key + "_max"] = {}
           # self.measurements[key + "_single"] = {}

        for aa in agents_algorithm:
            aa.initialize_algorithm()

    def add_out_box(self, key: Simulation.Entity, value: UnboundedBuffer):
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
        for key, value in self.f_global_measurements.items():
            dict_of_the_measure_up_to_now = self.measurements[key]
            measure = value(self.agents_algorithm)
            dict_of_the_measure_up_to_now[self.time_mailer] = measure

            single_agent = self.agents_algorithm[0]
            temp_list = []
            temp_list.append(single_agent)
            measure = value(temp_list)
            dict_of_the_measure_up_to_now = self.measurements[key+"_single"]
            dict_of_the_measure_up_to_now[self.time_mailer] = measure


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
        for msg in self.msg_box:
            if msg.msg_time <= self.time_mailer:
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

    def update_clock_upon_msg_recieved(self, msg: Msg):
        """
        prior for msg entering to msg box the mailer's clock is being updated
        if the msg time is larger than
        :param msg:
        :return:
        """

        msg_time = msg.msg_time
        if self.time_mailer <= msg_time:
            self.time_mailer = msg_time

    def agents_recieve_msgs(self, msgs_to_send):
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
        if msg_time > self.time_mailer:
            self.time_mailer = msg_time

    def are_all_agents_idle(self):
        for a in self.agents_algorithm:
            if a.get_is_idle():
                return False
        return True


class Agent_Algorithm(threading.Thread):
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
        threading.Thread.__init__()
        self.is_with_timestamp = is_with_timestamp
        self.timestamp_counter = 0
        self.neighbors_ids = []
        self.simulation_entity = simulation_entity
        self.atomic_counter = 0
        self.NCLO = 0
        self.idle_time = 0
        self.is_idle = True
        self.cond = None  # TODO update in solver
        self.inbox = None  # TODO update in solver
        self.outbox = None  # TODO update in solver

    def set_inbox(self, inbox_input: UnboundedBuffer):
        self.inbox = inbox_input

    def set_outbox(self, outbox_input: UnboundedBuffer):
        self.outbox = outbox_input

    def set_cond(self, cond_input):
        self.cond = cond_input

    def add_neighbor_id(self, neighbor_id: str):
        self.neighbors_ids.append(neighbor_id)

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
        raise NotImplementedError

    # ---------------------- receive_msgs ----------------------

    def update_agent_time(self, msgs):
        """

        :param msgs: list of msgs received simultaneously

        """
        max_time = self.get_max_time_of_msgs(msgs)
        with self.cond:
            if self.NCLO <= max_time:
                self.idle_time = self.idle_time + (max_time - self.NCLO)
                self.NCLO = max_time

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
                self.NCLO = self.NCLO + self.atomic_counter
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

    def get_list_of_msgs(self):
        """
         raise NotImplementedError
        create and return list of msgs
        """
        raise NotImplementedError

    def set_receive_flag_to_false(self):
        """
        raise NotImplementedError
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
            while self.is_idle == False:
                self.cond.wait()
            return self.is_idle

    def initialize_algorithm(self):
        raise NotImplementedError




