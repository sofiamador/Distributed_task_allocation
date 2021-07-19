import threading
from enum import Enum


# TODO - AGENT ALGORITHM,

class Allocation_Solver():
    def __init__(self, missions_simulation, agents_simulation):
        self.missions_simulation = missions_simulation
        self.agents_simulation = agents_simulation

    def solve(self) -> {}:
        """
        Use missions and agents to allocate an agent to mission
        :returns dictionary with key = agent and value = mission
        """
        raise NotImplementedError


class Allocation_Solver_Distributed(Allocation_Solver):
    def __init__(self, missions_simulation, agents_simulation):
        Allocation_Solver.__init__(missions_simulation, agents_simulation)

    def solve(self):
        """
        distributed version step recommendation using mailer
        """
        delay_function = self.get_delay_function()
        agents_algorithm = self.create_agents_algorithm()
        self.create_graphs()
        malier = Mailer(delay_function, agents_algorithm)

    def get_delay_function(self):
        return 0

    #
    def create_graphs(self):
        raise NotImplementedError

    def create_agents_algorithm(self):
        raise NotImplementedError

    def get_mission_algorithm(self, m_simulation):
        raise NotImplementedError


class Allocation_Solver_Distributed_v2(Allocation_Solver_Distributed):

    def solve(self):
        """
        distributed version step recommendation using mailer
        """
        delay_function = self.get_delay_function()
        agents_algorithm = self.create_agents_algorithm()
        self.create_graphs()
        self.match_agent_mission_responsibility()
        malier = Mailer(delay_function, agents_algorithm)

    def match_agent_mission_responsibility(self):
        raise NotImplementedError


mailer_counter = 0


class Mailer(threading.Thread):
    def __init__(self, f_delay, agents_algorithm):
        threading.Thread.__init__()
        global mailer_counter
        mailer_counter = mailer_counter + 1
        self.id_ = mailer_counter
        self.delay_function = f_delay
        self.protocol.set_seed()

        for aa in agents_algorithm:
            aa.start()


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

    send_msgs
    --> send to neighbors the changed statues

    set_receive_flag_to_false
    --> after computation occurs set the flag back to false

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
        self.cond = threading.Condition(threading.RLock())


    def set_cond(self, cond_input):
        self.cond = cond_input

    def add_neighbor_id(self, neighbor_id: str):
        self.neighbors_ids.append(neighbor_id)

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
        raise NotImplementedError




    def compute(self):
        """
	    After the context was updated by messages received, computation takes place
	    using the new information and preparation on context to be sent takes place
        """
        raise NotImplementedError


    def send_msgs(self):
        """
        send information after computation
        """
        raise NotImplementedError


    def set_receive_flag_to_false(self):
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




class Msg:
    def __init__(self, sender, receiver, information, msg_time, timestamp=0):
        self.sender = sender
        self.receiver = receiver
        self.information = information
        self.msg_time = msg_time
        self.timestamp = timestamp
