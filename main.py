import threading,time

import random


class Msg():
    def __init__(self,sender_id,receiver_id,information):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.information = information

class UnboundedBufferForMagadExtract():

    def __init__(self,sleeping_time = 1):
        self.buffer = []
        self.cond = threading.Condition(threading.RLock())
        self.sleeping_time = sleeping_time

    def insert(self, list_of_msgs):
        with self.cond:
            self.buffer.append(list_of_msgs)

    def extract(self):
        with self.cond:
            if len(self.buffer) == 0:
                time.sleep(self.sleeping_time)
            ans = []

            for msg in self.buffer:
                if msg is None:
                    return None
                ans.append(msg)
            return ans


class UnboundedBufferForCloudExtract():

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


class Cloud(threading.Thread):
    def __init__(self, inbox:UnboundedBufferForCloudExtract,outboxes, termination_counter = 50):
        threading.Thread.__init__(self)
        self.outboxes = outboxes
        self.inbox = inbox
        self.termination_counter = termination_counter
        self.counter = 0


    def run(self) -> None:
        while self.counter<self.termination_counter:
            self.counter = self.counter+1
            msgs_received_lists = self.inbox.extract()
            for msg_list in msgs_received_lists:
                for msg in msg_list:
                    receiver = msg.receiver_id
                    outbox = self.outboxes[receiver]
                    outbox.insert(msg)

        for id_,outbox in self.outboxes.items():
            outbox.insert(None)



class Magad(threading.Thread):
    def __init__(self, id_,neighbors_ids,outbox:UnboundedBufferForCloudExtract,inbox:UnboundedBufferForMagadExtract,max_time_computation = 3):
        threading.Thread.__init__(self)
        self.id_ = id_
        self.outbox = outbox
        self.inbox = inbox
        self.neighbors_ids = neighbors_ids
        self.rand = random.Random(id_)
        self.max_time_computation = max_time_computation
        self.counter = 0

    def run(self) -> None:
        msgs = self.create_msgs()

        while True:
            self.outbox.insert(msgs)
            msgs_received = self.inbox.extract()
            for msg in msgs_received:
                print("received: "+msg.information)
            msgs = self.create_msgs()

    def create_msgs(self):
        ans = []
        time.sleep(self.rand.random()*self.max_time_computation)
        for n_id in self.neighbors_ids:
            msg = Msg(sender_id=self.id_,receiver_id=n_id,information="msg from "+str(self.id_)+ " to "+str(n_id))
            ans.append(msg)
        return ans


def create_magads(amount_of_magads, outbox_magad_inbox_cloud, inbox_per_magad,magad_max_computation_time):
    magads = []
    for id_ in range(amount_of_magads):
        neighbor_ids = []
        for n_id in range(amount_of_magads):
            if n_id!=id_:
                neighbor_ids.append(n_id)
        inbox = inbox_per_magad[id_]
        magad = Magad(id_=id_,outbox =outbox_magad_inbox_cloud ,inbox= inbox,max_time_computation = magad_max_computation_time,neighbors_ids=neighbor_ids)
        magads.append(magad)
    return magads

if __name__ == '__main__':
    amount_of_magads = 2
    magad_max_computation_time = 5
    sleeping_time_for_msg_check = 1
    cloud_termination_limit = 50
    #------------
    outbox_magad_inbox_cloud = UnboundedBufferForCloudExtract()
    inbox_per_magad = {}
    for id_ in range(amount_of_magads):
        inbox_per_magad[id_] = UnboundedBufferForMagadExtract(sleeping_time= sleeping_time_for_msg_check)
    #------------
    magads = create_magads(amount_of_magads,outbox_magad_inbox_cloud,inbox_per_magad,magad_max_computation_time)
    cloud = Cloud(inbox=outbox_magad_inbox_cloud,outboxes=inbox_per_magad , termination_counter = 50)

    cloud.start()
    for magad in magads:
        magad.start()