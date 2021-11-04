def default_communication_disturbance(entity1,entity2):
    return 0


class CommunicationProtocol:
    def __init__(self,is_with_timestamp,communication_function,name):
        self.communication_function = communication_function
        self.name = name
        self.is_with_timestamp = is_with_timestamp
    def __str__(self):
        return self.name
