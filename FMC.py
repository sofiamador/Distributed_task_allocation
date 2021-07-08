import threading


class Agent(threading.Thread):

    def __init__(self, id_):
        threading.Thread.__init__(name=id_)
        self.id_ = id_
        self.neighbours = []
        self.messages = []

    def run(self):
        self.calculate()


class FMCBuyer(Agent):

    def __init__(self, id_):
        Agent.__init__(id_)


class FMCSeller(Agent):

    def __init__(self, id_):
        Agent.__init__(id_)
