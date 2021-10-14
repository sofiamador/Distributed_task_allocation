import ast
import TSG_integration


def input_from_file(file_name):
    f = open(file_name, "r")
    s = f.read()
    lst = s.split("]\n")
    lst[-1] = "[" + lst[-1]
    for i in range(len(lst)):
        lst[i] = lst[i].replace("\n", "")
        lst[i] = lst[i].replace("  ", "")
        lst[i] += "]"
        lst[i] = ast.literal_eval(lst[i])
        print(lst[i])
    return lst


if __name__ == '__main__':
    file_name = "RUN1.1_input.txt"
    input_from_file(file_name)
    agent_list, event_list, allocation_list, event_params, force_type_data, discrete_params = input_from_file(file_name)
    print(agent_list)

    allocation_list_updated = TSG_integration.calcAllocations(agent_list=agent_list, event_list=event_list,
                                                              allocations_list=allocation_list,
                                                              force_type_data=force_type_data,
                                                              discrete_params=discrete_params,
                                                              event_params=event_params)
    # print(allocation_list_updated)
    # print(len(allocation_list_updated))