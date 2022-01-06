import abc
from abc import ABC

import math
import threading
import copy

from Simulation_Abstract_Components import Entity

debug_print_for_distribution = False
from enum import Enum

debug_fisher_market = False

from Simulation_Abstract import PlayerSimple,TaskSimple


def default_communication_disturbance(msg,entity1,entity2):
    return 0


class UnboundedBuffer():

    def __init__(self):

        self.buffer = []

        self.cond = threading.Condition(threading.RLock())

    def insert(self, list_of_msgs):

        with self.cond:
            self.buffer.append(list_of_msgs)
            self.cond.notify_all()

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

    def __init__(self, sender, receiver, information, is_with_perfect_communication):
        self.sender = sender

        self.receiver = receiver

        self.information = information

        self.msg_time = None

        self.timestamp = None

        self.is_with_perfect_communication =is_with_perfect_communication

    def set_time_of_msg(self, delay):
        self.msg_time = self.msg_time + delay

    def add_current_NCLO(self, NCLO):
        self.msg_time = NCLO

    def add_timestamp(self, timestamp):
        self.timestamp = timestamp


class MsgTaskEntity(Msg):
    def __init__(self, msg: Msg, task_entity):
        Msg.__init__(self, sender=msg.sender, receiver=msg.receiver, information=msg.information,
                     is_with_perfect_communication=msg.is_with_perfect_communication)

        self.task_entity = task_entity


mailer_counter = 0


class ClockObject():
    def __init__(self):
        self.clock = 0.0
        self.lock = threading.RLock()
        self.idle_time = 0.0

    def change_clock_if_required(self, time_of_received_msg: float):
        with self.lock:
            if self.clock < time_of_received_msg:
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
                 f_communication_disturbance):
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

        # message loss due to communication protocol
        self.msg_not_delivered_loss_counter = 0

        # message loss due to timestamp policy
        self.msg_not_delivered_loss_timestamp_counter = 0

        # message sent by players regardless to communication protocol
        self.msg_sent_counter = 0

        # messages that arrive to their destination
        self.msg_received_counter = 0

        self.last_time = 0
        self.delta_time = 9999999

    def get_allocation_dictionary(self):
        pass

    def reset(self,tnow):
        global mailer_counter
        self.msg_box = []
        mailer_counter = mailer_counter + 1
        self.id_ = mailer_counter
        self.agents_outboxes = {}  # TODO update in allocate
        self.inbox = None  # TODO update in solver
        self.time_mailer = ClockObject()
        self.measurements = {}
        self.msg_not_delivered_loss_counter = 0
        self.msg_not_delivered_loss_timestamp_counter = 0
        self.msg_sent_counter = 0
        self.msg_received_counter = 0

        for key in self.f_global_measurements.keys():
            self.measurements[key] = {}
        self.measurements["Loss Counter"] = {}
        self.measurements["Loss Timestamp Counter"] = {}
        self.measurements["Message Sent Counter"] = {}
        self.measurements["Message Received Counter"] = {}

        for aa in self.agents_algorithm:
            aa.reset_fields(tnow)

        self.last_time = 0
        self.delta_time = 0
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

        self.create_measurements()

        self.mailer_iteration(with_update_clock_for_empty_msg_to_send=True)

        while not self.f_termination_condition(self.agents_algorithm, self):
            self.create_measurements()

            self.self_check_if_all_idle_to_continue()

            self.mailer_iteration(with_update_clock_for_empty_msg_to_send=False)

        self.kill_agents()

        for aa in self.agents_algorithm:
            aa.join()

    def create_measurements(self):
        current_clock = self.time_mailer.get_clock()  # TODO check if immutable

        if debug_fisher_market:
            print("******MAILER CLOCK", self.time_mailer.clock,"******")
            self.print_fisher_input()
            self.print_fisher_x()

        for measurement_name, measurement_function in self.f_global_measurements.items():

            measured_value = measurement_function(self.agents_algorithm)

            self.measurements[measurement_name][current_clock] = measured_value



        self.measurements["Loss Counter"][current_clock] = self.msg_not_delivered_loss_counter
        self.measurements["Loss Timestamp Counter"][current_clock] = self.get_counter_sum_of_timestamp_loss_msgs_from_agents()
        self.measurements["Message Sent Counter"][current_clock] = self.msg_sent_counter
        self.measurements["Message Received Counter"][current_clock] = self.get_counter_sum_msg_received_counter_from_agents()

    @staticmethod
    def get_data_keys():
        return ["Loss Counter","Loss Timestamp Counter","Message Sent Counter","Message Received Counter"]

    def get_counter_sum_of_timestamp_loss_msgs_from_agents(self):
        ans = 0
        for aa in self.agents_algorithm:
            ans+=aa.msg_not_delivered_loss_timestamp_counter
        return ans

    def get_counter_sum_msg_received_counter_from_agents(self):
        ans = 0
        for aa in self.agents_algorithm:
            ans += aa.msg_received_counter
        return ans

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

                self.agents_receive_msgs(msgs_to_send)

    def mailer_iteration(self, with_update_clock_for_empty_msg_to_send):

        #if self.all_tasks_finish():
            #print(self.time_mailer.clock)
        #print(self.time_mailer.clock)

        self.last_time = self.time_mailer.clock
        msgs_from_inbox = self.inbox.extract()

        self.place_msgs_from_inbox_in_msgs_box(msgs_from_inbox)

        if with_update_clock_for_empty_msg_to_send:
            self.should_update_clock_because_no_msg_received()

        msgs_to_send = self.handle_delay()

        self.agents_receive_msgs(msgs_to_send)

        self.delta_time = self.time_mailer.clock-self.last_time
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

        for msgs in msgs_from_inbox:
            if isinstance(msgs, list):
                for msg in msgs:
                    self.place_single_msg_from_inbox_in_msgs_box(msg)
            else:
                self.place_single_msg_from_inbox_in_msgs_box(msgs)

    def place_single_msg_from_inbox_in_msgs_box(self,msg):
        self.update_clock_upon_msg_received(msg)
        e1 = self.get_simulation_entity(msg.sender)
        e2 = self.get_simulation_entity(msg.receiver)
        communication_disturbance_output = self.f_communication_disturbance(e1,e2)
        flag = False
        self.msg_sent_counter += 1
        if msg.is_with_perfect_communication:
            self.msg_box.append(msg)
            flag = True

        if not flag and communication_disturbance_output is not None:
            delay = communication_disturbance_output
            delay = round(delay)
            msg.set_time_of_msg(delay)
            if debug_print_for_distribution:
                print(delay)
            self.msg_box.append(msg)

        if communication_disturbance_output is None:
            self.msg_not_delivered_loss_counter +=1




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
                if msg.receiver == receiver:
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

            if not a.get_is_idle():
                return False

        return True

    def print_fisher_input(self):
        print("-----R-----")

        for p in  self.agents_algorithm:
            if isinstance(p,PlayerAlgorithm):
                print()
                with p.cond:
                    #print(p.simulation_entity.id_)
                    for task, dict in p.r_i.items():
                        for mission,util in dict.items():
                            print(round(util.linear_utility,2),end=" ")

        print()
        print()

        #print("-----R dict-----")

        # for p in  self.agents_algorithm:
        #     if isinstance(p,PlayerAlgorithm):
        #         print()
        #         with p.cond:
        #             print(p.simulation_entity.id_,p.simulation_entity.abilities[0].ability_type)
        #             for task, dict in p.r_i.items():
        #                 for mission,util in dict.items():
        #                     print("Task:",task,"Mission:",mission, "r_ijk:",round(util.linear_utility,2))
        # print()
        # print()

    def print_fisher_x(self):

        print("-----X-----")




        for p in self.agents_algorithm:
            if isinstance(p, TaskAlgorithm):

                with p.cond:
                    for mission, dict in p.x_jk.items():
                        print()
                        for n_id,x in dict.items():
                            if x is None:
                                print("None", end=" ")
                            else:
                                print(round(x,4), end=" ")
        print()

    def get_simulation_entity(self, id_looking_for):
        for a in self.agents_algorithm:
            if a.simulation_entity.id_ == id_looking_for:
                return a.simulation_entity

    def all_tasks_finish(self):
        for aa in self.agents_algorithm:
            if isinstance(aa,TaskAlgorithm):
                if not aa.is_finish_phase_II:
                    return False
        return True

class AgentAlgorithm(threading.Thread, ABC):
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

    def __init__(self, simulation_entity:Entity, t_now, is_with_timestamp=True):

        threading.Thread.__init__(self)
        self.t_now = t_now
        self.neighbours_ids_list = []
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
        self.msg_not_delivered_loss_timestamp_counter = 0
        self.msg_received_counter = 0

    def reset_fields(self,t_now):
        self.t_now = t_now
        self.neighbours_ids_list = []
        self.timestamp_counter = 0  # every msg sent the timestamp counter increases by one (see run method)
        self.atomic_counter = 0  # counter changes every computation
        self.NCLO = ClockObject()  # an instance of an object with
        self.idle_time = 0
        self.is_idle = True
        self.cond = threading.Condition(threading.RLock())
        self.inbox = None  # DONE
        self.outbox = None
        self.reset_additional_fields()
        self.msg_not_delivered_loss_timestamp_counter = 0
        self.msg_received_counter = 0


    def update_cond_for_responsible(self, condition_input: threading.Condition):
        self.cond = condition_input

    def add_neighbour_id(self, id_: str):
        if self.simulation_entity.id_ not in self.neighbours_ids_list:
            self.neighbours_ids_list.append(id_)

    def remove_neighbour_id(self, id_: str):
        if self.simulation_entity.id_ in self.neighbours_ids_list:
            self.neighbours_ids_list.remove(id_)

    def add_task_entity(self, task_entity: TaskSimple):
        pass

    def set_inbox(self, inbox_input: UnboundedBuffer):
        self.inbox = inbox_input

    def set_outbox(self, outbox_input: UnboundedBuffer):
        self.outbox = outbox_input

    def set_clock_object_for_responsible(self, clock_object_input):
        self.NCLO = clock_object_input




    @abc.abstractmethod
    def initiate_algorithm(self):
        """
        before thread starts the action in this method will occur
        :return:
        """
        raise NotImplementedError

    @abc.abstractmethod
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
                    self.set_receive_flag_to_true_given_msg(msg)
                    self.update_message_in_context(msg)
                    self.msg_received_counter += 1

                else:
                    self.msg_not_delivered_loss_timestamp_counter += 1
            else:
                self.set_receive_flag_to_true_given_msg(msg)
                self.update_message_in_context(msg)
                self.msg_received_counter += 1

        self.update_agent_time(msgs)

    @abc.abstractmethod
    def set_receive_flag_to_true_given_msg(self, msg):

        """
        given msgs received is agent going to compute in this iteration?
        set the relevant computation flag
        :param msg:
        :return:
        """

        raise NotImplementedError

    @abc.abstractmethod
    def get_current_timestamp_from_context(self, msg):

        """
        :param msg: use it to extract the current timestamp from the receiver
        :return: the timestamp from the msg
        """

        raise NotImplementedError

    @abc.abstractmethod
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

    @abc.abstractmethod
    def get_is_going_to_compute_flag(self):
        """
        :return: the flag which determines if computation is going to occur
        """
        raise NotImplementedError

    @abc.abstractmethod
    def compute(self):
        """
       After the context was updated by messages received, computation takes place
       using the new information and preparation on context to be sent takes place
        """
        raise NotImplementedError

    def send_msgs(self):
        msgs = self.get_list_of_msgs_to_send()
        for msg in msgs:
            msg.add_current_NCLO(self.NCLO.clock)
            msg.add_timestamp(self.timestamp_counter)
            msg.is_with_perfect_communication = self.check_if_msg_should_have_perfect_communication(msg)
        self.outbox.insert(msgs)

    def check_if_msg_should_have_perfect_communication(self):
        """
        if both agent "sit" on the same computer them true
        :return: bool
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_list_of_msgs_to_send(self):
        """
        create and return list of msgs to send
        """
        raise NotImplementedError

    @abc.abstractmethod
    def set_receive_flag_to_false(self):
        """
        after computation occurs set the flag back to false
        :return:
        """
        raise NotImplementedError

    def run(self) -> None:


        while True:

            self.set_idle_to_true()

            msgs_list = self.inbox.extract()  # TODO when finish mailer

            with self.cond:
                if msgs_list is None:
                    break

                msgs = []
                for msg_list in msgs_list:
                    for msg in msg_list:
                        msgs.append(msg)
                self.set_idle_to_false()
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

    @abc.abstractmethod
    def reset_additional_fields(self):
        raise NotImplementedError

class AgentAlgorithmTaskPlayers(AgentAlgorithm):
    def __init__(self, simulation_entity: Entity, t_now, is_with_timestamp=False):
        AgentAlgorithm.__init__(self, simulation_entity=simulation_entity, t_now=t_now,
                                is_with_timestamp=is_with_timestamp)
        self.ttt=simulation_entity

    #def __eq__(self, other):
        #return self.simulation_entity.id_ == other.simulation_entity.id_

    #def __hash__(self):
        #return 0#self.simulation_entity.id_.__hash__()


    def set_receive_flag_to_true_given_msg(self, msg:Msg):

        sender_id = msg.sender
        list_of_ids_under_responsibility = self.get_list_of_ids_under_responsibility()
        if sender_id in list_of_ids_under_responsibility:
            if self.is_identical_context(msg):
                return
            else:
                self.set_receive_flag_to_true_given_msg_after_check(msg)
        else:
            self.set_receive_flag_to_true_given_msg_after_check(msg)

    @abc.abstractmethod
    def set_receive_flag_to_true_given_msg_after_check(self,msg):
        raise NotImplementedError

    @abc.abstractmethod
    def is_identical_context(self, msg:Msg):
        raise NotImplementedError



    @abc.abstractmethod
    def get_list_of_ids_under_responsibility(self):
        raise NotImplementedError

class PlayerAlgorithm(AgentAlgorithmTaskPlayers):
    def __init__(self, simulation_entity:PlayerSimple, t_now, is_with_timestamp=True):
        AgentAlgorithm.__init__(self, simulation_entity=simulation_entity, t_now=t_now,
                                is_with_timestamp=is_with_timestamp)

        self.tasks_responsible_ids = []
        for task_responsible in simulation_entity.tasks_responsible:
            self.tasks_responsible_ids.append(task_responsible.id_)
        self.tasks_log = []
        self.additional_tasks_in_log = []

        if self.simulation_entity.current_task is not None:
            self.tasks_log.append(self.simulation_entity.current_task)




    def check_if_msg_should_have_perfect_communication(self,msg:Msg):
        ids_ = []
        for t in self.tasks_log:
            ids_.append(t.id_)

        if msg.receiver in ids_:
            return True
        return False

    def get_list_of_ids_under_responsibility(self):
        return self.tasks_responsible_ids


    def add_task_entity_to_log(self, task_entity: TaskSimple):
        if task_entity.id_ not in self.neighbours_ids_list:
            self.add_neighbour_id(task_entity.id_)
        self.tasks_log.append(task_entity)

    def remove_task_from_log(self, task_entity: TaskSimple):
        if task_entity.id_ in self.neighbours_ids_list:
            self.remove_neighbour_id(task_entity.id_)
            for task_in_log in self.tasks_log:
                if task_in_log.id_ == task_entity.id_:
                    self.tasks_log.remove(task_in_log)
                    break

    def receive_msgs(self, msgs: []):
        super().receive_msgs(msgs)
        for msg in msgs:

            #if msg.task_entity not in self.tasks_log :
            for task_in_log in self.tasks_log:
                if task_in_log.id_ == msg.task_entity.id_:
                    self.tasks_log.remove(task_in_log)
                    break

            self.tasks_log.append(msg.task_entity)
            self.additional_tasks_in_log.append(msg.task_entity)
            self.add_neighbour_id(msg.task_entity.id_)
        else:
            for task_in_log in self.tasks_log:
                if task_in_log==msg.task_entity:
                    if task_in_log.last_time_updated<msg.task_entity.last_time_updated:
                        self.tasks_log.remove(task_in_log)
                        self.tasks_log.append(msg.task_entity)
                        #print(msg.task_entity+"is updated, Allocation_Solver_Abstract")


    def send_msgs(self):
        super().send_msgs()
        self.additional_tasks_in_log = []

    def update_log_with_task(self,task_input:TaskSimple):
        for task_in_log in self.tasks_log:
            if task_input.id_ == task_in_log.id_:
                self.tasks_log.remove(task_in_log)
                self.tasks_log.append(copy.copy(task_input))

class TaskAlgorithm(AgentAlgorithmTaskPlayers):
    def __init__(self, simulation_entity:TaskSimple, t_now, is_with_timestamp=False):
        AgentAlgorithmTaskPlayers.__init__(self, simulation_entity=simulation_entity, t_now=t_now,
                                is_with_timestamp=is_with_timestamp)



    def check_if_msg_should_have_perfect_communication(self,msg:Msg):
        if self.simulation_entity.player_responsible is not None:
            if msg.receiver== self.simulation_entity.player_responsible.id_:
                return True
        return False


    def get_list_of_ids_under_responsibility(self):
        ans = []
        ans.append(self.simulation_entity.player_responsible.id_)
        return ans

    def send_msgs(self):
        ans = []

        msgs = self.get_list_of_msgs_to_send()
        for msg in msgs:
            temp_msg = MsgTaskEntity(msg, copy.copy(self.simulation_entity))
            temp_msg.add_current_NCLO(self.NCLO.clock)
            temp_msg.add_timestamp(self.timestamp_counter)
            temp_msg.is_with_perfect_communication = self.check_if_msg_should_have_perfect_communication(msg)
            ans.append(temp_msg)
            self.outbox.insert(temp_msg)



class AllocationSolver:
    
    def __init__(self, tasks_simulation=[], players_simulation=[]):
        self.centralized_computer = None
        self.agents_algorithm = []

        self.tasks_simulation = []
        for task in tasks_simulation:
            self.add_task_to_solver(task)
            
        self.players_simulation = []
        for player in players_simulation:
            self.add_player_to_solver(player)
        self.tnow = 0


    def add_tasks_list(self,tasks_simulation):
        for task in tasks_simulation:
            self.add_task_to_solver(task)

    def add_players_list(self, players_simulation):
        for player in players_simulation:
            self.add_player_to_solver(player)

    def solve(self, tnow, centralized_computer = None ) -> {}:
        self.tnow = tnow
        self.centralized_computer = centralized_computer
        return self.allocate()

    @abc.abstractmethod
    def add_player_to_solver(self, player: PlayerSimple):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_player_from_solver(self, player: PlayerSimple):
        raise NotImplementedError

    @abc.abstractmethod
    def add_task_to_solver(self, task: TaskSimple):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_task_from_solver(self, task: TaskSimple):
        raise NotImplementedError

    @abc.abstractmethod
    def allocate(self):
        """
        Use missions and agents to allocate an agent to mission
        :returns dictionary with key = agent and value = mission
        """
        raise NotImplementedError


class CentralComputer:
    pass





class AllocationSolverCentralized(AllocationSolver):
    def __init__(self, centralized_computer:CentralComputer,f_termination_condition):
        AllocationSolver.__init__(self,centralized_computer)
        self.centralized_computer = centralized_computer
        self.f_termination_condition = f_termination_condition


    def reset_centralized_computer_info(self):
        self.agents_algorithm = []

        tasks = self.centralized_computer.tasks
        for tt in tasks:
            task_copy = copy.copy(tt)
            self.tasks_simulation.append(task_copy)
            self.add_task_to_solver()

        players = self.centralized_computer.players
        for pp in players:
            player_copy = copy.copy(pp)
            self.players_simulation.append(player_copy)
            self.add_player_to_solver()


    def solve(self, tnow, centralized_computer=None) -> {}:
        self.tnow = tnow
        self.centralized_computer = centralized_computer
        self.reset_centralized_computer_info()
        self.initialize_centralistic_algorithm()
        return self.allocate()

    def allocate(self):
        while(self.f_termination_condition(self.agents_algorithm)):
            pass
            #TODO

    @abc.abstractmethod
    def initialize_centralistic_algorithm(self):
        raise NotImplementedError

    def add_player_to_solver(self, player: PlayerSimple):
        pass

    def remove_player_from_solver(self, player: PlayerSimple):
        pass

    def add_task_to_solver(self, task: TaskSimple):
        pass

    def remove_task_from_solver(self, task: TaskSimple):
        pass




class AllocationSolverDistributed(AllocationSolver):

    def __init__(self,  f_termination_condition=None, f_global_measurements=None,
                 f_communication_disturbance=default_communication_disturbance):
        """
        :param mailer: entity that simulates message delivery (given protocol) between agents
        :param f_termination_condition: function received by the user that determines when the mailer should stop
        :param f_global_measurements: function that returns dictionary=  {key: str of fields name,function of calculated fields
        :param f_communication_disturbance: function that returns None for msg loss, or a number for NCLO delay
        """
        AllocationSolver.__init__(self)
        self.f_termination_condition =f_termination_condition
        self.f_global_measurements =f_global_measurements
        self.f_communication_disturbance =f_communication_disturbance


        self.mailer = None
        self.imply_mailer( )

    def get_measurements(self):
        return self.mailer.measurements


    def solve(self, tnow, centralized_computer=None) -> {}:
        self.tnow = tnow
        self.centralized_computer = centralized_computer

        self.agents_algorithm = []
        self.players_algorithm = []
        self.tasks_algorithm = []

        self.imply_mailer()
        for pp in self.players_simulation:
            self.what_solver_does_when_player_is_added(pp)

        for tt in self.tasks_simulation:
            self.what_solver_does_when_task_is_added(tt)


        return self.allocate()

    def add_player_to_solver(self, player: PlayerSimple):
        self.players_simulation.append(player)
        #self.what_solver_does_when_player_is_added(player)

    def remove_player_from_solver(self, player: PlayerSimple):
        self.players_simulation.remove(player)
        self.what_solver_does_when_player_is_removed(player)

    def add_task_to_solver(self, task: TaskSimple):
        self.tasks_simulation.append(task)
        #self.what_solver_does_when_task_is_added(task)

    def remove_task_from_solver(self, task: TaskSimple):
        self.tasks_simulation.remove(task)
        self.what_solver_does_when_task_is_removed(task)

    @abc.abstractmethod
    def what_solver_does_when_player_is_added(self, player: PlayerSimple):
        raise NotImplementedError

    @abc.abstractmethod
    def what_solver_does_when_task_is_added(self, task: TaskSimple):
        raise NotImplementedError

    @abc.abstractmethod
    def what_solver_does_when_player_is_removed(self, player: PlayerSimple):
        raise NotImplementedError

    @abc.abstractmethod
    def what_solver_does_when_task_is_removed(self, task: TaskSimple):
        raise NotImplementedError

    def imply_mailer(self ):
        """
        if mailer is received in constructor then use it,
        otherwise use f_termination_condition,f_global_measurements, f_communication_disturbance  to create Mailer
        :param mailer: entity that simulates message delivery (given protocol) between agents
        :param f_termination_condition: function received by the user that determines when the mailer should stop
        :param f_global_measurements: function that returns dictionary=  {key: str of fields name,function of calculated fields
        :param f_communication_disturbance: function that returns None for msg loss, or a number for NCLO delay
        :return: None
        """

        if self.f_termination_condition is not None and self.f_global_measurements is not None:
            self.mailer = Mailer(self.f_termination_condition, self.f_global_measurements, self.f_communication_disturbance)
        else:
            raise Exception(
                "Cannot create mailer instance without: dictionary of measurments with function and a termination condition")

    def get_algorithm_agent_by_entity(self, entity_input: Entity):
        """
        :param entity_input:
        :return: the algorithm agent that contains the simulation entity
        """
        for agent_algo in self.agents_algorithm:
            if agent_algo.simulation_entity == entity_input:
                return agent_algo
        raise Exception("algorithm agent does not exists")

    def what_solver_does_when_player_is_added(self, player:PlayerSimple):
        algorithm_player = self.create_algorithm_player(player)
        self.agents_algorithm.append(algorithm_player)


    def what_solver_does_when_player_is_removed(self, player:PlayerSimple):
        player_algo = self.get_algorithm_agent_by_entity(player)
        self.agents_algorithm.remove(player_algo)

    @abc.abstractmethod
    def create_algorithm_player(self, player:PlayerSimple):
        raise NotImplementedError


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
        #self.agents_algorithm = self.create_agents_algorithm()
        self.reset_algorithm_agents()
        self.mailer.reset(self.tnow)
        self.connect_entities()
        self.agents_initialize()
        self.start_all_threads()
        self.mailer.start()
        self.mailer.join()
        #return self.mailer.get_allocation_dictionary()  # TODO



    def reset_algorithm_agents(self):
        for aa in self.agents_algorithm:
            aa.reset_fields(self.tnow)

    def start_all_threads(self):
        for aa in self.agents_algorithm:
            aa.start()

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
            self.mailer.add_out_box(aa.simulation_entity.id_, agent_inbox)
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

    def __init__(self,  f_termination_condition=None, f_global_measurements=None,
                 f_communication_disturbance=default_communication_disturbance):
        AllocationSolverDistributed.__init__(self, f_termination_condition, f_global_measurements,
                                             f_communication_disturbance)
        self.tasks_algorithm = []
        self.players_algorithm = []

    def get_player_entity(self,player_id):
        for player_entity in self.players_simulation:
            if player_entity.id_ == player_id:
                return player_entity

        raise Exception("how come the id does not exists? you have a mistake")

    def get_players_entity(self,neighbors_id):
        ans = []
        for player_id in neighbors_id:
            ans.append(self.get_player_entity(player_id))
        return ans

    def neighbors_by_skill(self,task):
        ans = {}
        neighbors_ids = task.neighbours
        neighbors_entities = self.get_players_entity(neighbors_ids)
        missions = task.missions_list
        for mission in missions:
            for ability in mission.abilities:
                ans[ability] = []
        ids_to_remove = []
        for neighbor_entity in neighbors_entities:
            for ability in neighbor_entity.abilities:
                if ability not in ans.keys():
                    ids_to_remove.append(neighbor_entity.id_)
                else:
                    ans[ability].append(neighbor_entity)

        updated_neighbors_list = []
        for player_id in task.neighbours:
            if player_id not in ids_to_remove:
                updated_neighbors_list.append(player_id)

        task.neighbours = updated_neighbors_list
        return ans

    def what_solver_does_when_player_is_added(self, player: PlayerSimple):
        algorithm_player = self.create_algorithm_player(player)
        self.agents_algorithm.append(algorithm_player)
        self.players_algorithm.append(algorithm_player)
        self.mailer.agents_algorithm.append(algorithm_player)

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

    def what_solver_does_when_task_is_added(self, task: TaskSimple):
        task_algorithm = self.create_algorithm_task(task)
        self.agents_algorithm.append(task_algorithm)
        self.tasks_algorithm.append(task_algorithm)
        self.mailer.agents_algorithm.append(task_algorithm)
        player_sim_responsible = task.player_responsible
        player_algorithm = self.get_algorithm_agent_by_entity(player_sim_responsible)

        AllocationSolverTasksPlayersSemi.connect_condition(player_algorithm, task_algorithm)
        AllocationSolverTasksPlayersSemi.update_player_log(player_algorithm, task_algorithm)
        AllocationSolverTasksPlayersSemi.connect_clock_object(player_algorithm, task_algorithm)

    def what_solver_does_when_player_is_removed(self, player: PlayerSimple):
        player_algorithm = self.get_algorithm_agent_by_entity(player)
        self.agents_algorithm.remove(player_algorithm)
        self.players_algorithm.remove(player_algorithm)

    def what_solver_does_when_task_is_removed(self, task: TaskSimple):
        task_algorithm = self.get_algorithm_agent_by_entity(task)
        self.agents_algorithm.remove(task_algorithm)
        self.tasks_algorithm.remove(task_algorithm)
        self.remove_task_from_players_log(task)

    def remove_task_from_players_log(self, task: TaskSimple):
        for player_algo in self.players_algorithm:
            player_algo.remove_task_from_log(task)

    @abc.abstractmethod
    def create_algorithm_task(self, task: TaskSimple):
        raise NotImplementedError

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
                current_task_updated = self.get_updated_entity_copy_of_current_task(current_task)
                player_algorithm.update_log_with_task(current_task_updated)

    def get_updated_entity_copy_of_current_task(self, current_task:TaskSimple):
        for task_algo in self.tasks_algorithm:
            if task_algo.simulation_entity.id_ == current_task.id_:
                return task_algo.simulation_entity

    def connect_neighbors(self):
        """
        implement method
        simulate_players_and_tasks_representation: take care of all connections due to player responsible for a task
        connect_players_to_tasks: update the neighbours list at the task entites. The player entity is already updated
        :return:
        """
        self.update_log_of_players_current_task()
        self.connect_players_to_tasks()

    def connect_players_to_tasks(self):
        for task_sim in self.tasks_simulation:
            tasks_neighbours = task_sim.neighbours
            task_algorithm = self.get_algorithm_agent_by_entity(task_sim)
            for player_sim_id in tasks_neighbours:
                task_algorithm.add_neighbour_id(player_sim_id)

    def agents_initialize(self):
        for task_algo in self.tasks_algorithm:
            task_algo.initiate_algorithm()


def task_by_id(task_algo:TaskAlgorithm):
    return task_algo.simulation_entity.id_

class AllocationSolverTasksPlayersFullRandTaskInit(AllocationSolverTasksPlayersSemi):
    def __init__(self, mailer=None, f_termination_condition=None, f_global_measurements=None,
                 f_communication_disturbance=default_communication_disturbance):
        AllocationSolverTasksPlayersSemi.__init__(self,mailer, f_termination_condition, f_global_measurements,
                                             f_communication_disturbance)

    def agents_initialize(self):
        max_task = max(self.tasks_algorithm,key = task_by_id)
        max_task.initiate_algorithm()


def get_task_arrival_time(task_entity:TaskSimple):
    return task_entity.arrival_time

class AllocationSolverTasksPlayersFullLatestTaskInit(AllocationSolverTasksPlayersSemi):
    def __init__(self, mailer=None, f_termination_condition=None, f_global_measurements=None,
                 f_communication_disturbance=default_communication_disturbance):
        AllocationSolverTasksPlayersSemi.__init__(self, f_termination_condition, f_global_measurements,
                                             f_communication_disturbance)

    def agents_initialize(self):
        task_entities = []
        for task_algo in self.tasks_algorithm:
            task_entities.append(task_algo.simulation_entity)

        max_task = max(task_entities,key = get_task_arrival_time)
        max_task.initiate_algorithm()