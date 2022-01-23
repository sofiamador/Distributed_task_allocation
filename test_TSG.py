import ast
import TSG_integration


def input_from_file(file_name):
    f = open(file_name, "r")
    s = f.read()
    # lst = s.split("]\n")
    lst = s.split("\n")
    print(lst[0])
    # lst[-1] = "[" + lst[-1]
    for i in range(1, len(lst)):
        # lst[i] = lst[i].replace("\n", "")
        # lst[i] = lst[i].replace("  ", "")
        # lst[i] += "]"
        lst[i] = ast.literal_eval(lst[i])
        print(lst[i])
    #lst[-1] = lst[-1][0]
    return lst


def test_TSG(file_name):
    host_name, agent_list, event_list, allocation_list, event_params, force_type_data, discrete_params = input_from_file(
        file_name)

    allocation_list_updated = TSG_integration.calcAllocations(host_agent=host_name, agent_list=agent_list,
                                                              event_list=event_list,
                                                              allocations_list=allocation_list,
                                                              force_type_data=force_type_data,
                                                              discrete_params=discrete_params,
                                                              event_params=event_params)
    print(allocation_list_updated)
    print(len(allocation_list_updated))


import threading

# x = threading.Thread(target=test_TSG, args="input.txt")
# x.start()
# y = threading.Thread(target=test_TSG, args=("RUN1.7_input.txt", "צוות_חילוץ_7"))
# y.start()
test_TSG("input.txt")
