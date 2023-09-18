import math
import numpy as np
import pandas as pd

# below is hard coded dictionaries for 6 bus case
# reworking code to be based off dictionaries rather than reading csv for grid data

substation_data_6 = {1: {"lat": 33.613499, "long": -87.373673, "ground_r": 0.2},
                   2: {"lat": 34.310437, "long": -86.365765, "ground_r": 0.2},
                   3: {"lat": 33.955058, "long": -84.679354, "ground_r": 0.2}}

bus_data_6 = {1: {"sub_num": 1}, 2: {"sub_num": 1},
            3: {"sub_num": 2}, 4: {"sub_num": 2},
            5: {"sub_num": 3}, 6: {"sub_num": 3}}

branch_data_6 = {(2, 3, 1): {"has_trans": False, "resistance": 3.525,
                "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
               (4, 5, 1): {"has_trans": False, "resistance": 4.665,
                "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
               (2, 1, 1): {"has_trans": True, "resistance": None,
                "type": "gsu", "trans_w1": 0.5, "trans_w2": None, "GIC_BD": False},
               (4, 3, 1): {"has_trans": True, "resistance": None,
                "type": "auto", "trans_w1": 0.2, "trans_w2": 0.2, "GIC_BD": False},
               (5, 6, 1): {"has_trans": True, "resistance": None,
                "type": "gsu", "trans_w1": 0.5, "trans_w2": None, "GIC_BD": False}}

substation_data_20 = {1: {"lat": 33.6135, "long": -87.3737, "ground_r": 0.2},
                      2: {"lat": 34.3104, "long": -86.3658, "ground_r": 0.2},
                      3: {"lat": 33.9551, "long": -84.6794, "ground_r": 0.2},
                      4: {"lat": 33.5479, "long": -86.0746, "ground_r": 1.0},
                      5: {"lat": 32.7051, "long": -84.6634, "ground_r": 0.1},
                      6: {"lat": 33.3773, "long": -82.6188, "ground_r": 0.1},
                      7: {"lat": 34.2522, "long": -82.8363, "ground_r": 0},
                      8: {"lat": 34.1956, "long": -81.0980, "ground_r": 0.1}}

bus_data_20 = {1: {"sub_num": 1}, 2: {"sub_num": 1},
               18: {"sub_num": 2}, 17: {"sub_num": 2},
               19: {"sub_num": 2}, 16: {"sub_num": 3},
               15: {"sub_num": 3}, 3: {"sub_num": 4},
               4: {"sub_num": 4}, 20: {"sub_num": 5},
               5: {"sub_num": 5}, 6: {"sub_num": 6},
               7: {"sub_num": 6}, 8: {"sub_num": 6},
               11: {"sub_num": 7}, 12: {"sub_num": 8},
               13: {"sub_num": 8}, 14: {"sub_num": 8}}

branch_data_20 = {(2, 3, 1): {"has_trans": False, "resistance": 3.512,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (2, 17, 1): {"has_trans": False, "resistance": 3.525,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (15, 4, 1): {"has_trans": False, "resistance": 1.986,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (17, 16, 1): {"has_trans": False, "resistance": 4.665,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (4, 5, 1): {"has_trans": False, "resistance": 2.345,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (4, 5, 2): {"has_trans": False, "resistance": 2.345,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (5, 6, 1): {"has_trans": False, "resistance": 2.975,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (5, 11, 1): {"has_trans": False, "resistance": 3.509,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": True},
                  (6, 11, 1): {"has_trans": False, "resistance": 1.444,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (4, 6, 1): {"has_trans": False, "resistance": 4.666,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (15, 6, 1): {"has_trans": False, "resistance": 2.924,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (15, 6, 2): {"has_trans": False, "resistance": 2.924,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (11, 12, 1): {"has_trans": False, "resistance": 2.324,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (16, 20, 1): {"has_trans": False, "resistance": 4.049,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (17, 20, 1): {"has_trans": False, "resistance": 6.940,
                    "type": None, "trans_w1": None, "trans_w2": None, "GIC_BD": False},
                  (2, 1, 1): {"has_trans": True, "resistance": None,
                    "type": "gsu", "trans_w1": 0.1, "trans_w2": None, "GIC_BD": True},
                  (4, 3, 1): {"has_trans": True, "resistance": None,
                    "type": "gy", "trans_w1": 0.2, "trans_w2": 0.1, "GIC_BD": False},
                  (17, 18, 1): {"has_trans": True, "resistance": None,
                    "type": "gsu", "trans_w1": 0.1, "trans_w2": None, "GIC_BD": False},
                  (17, 19, 2): {"has_trans": True, "resistance": None,
                    "type": "gsu", "trans_w1": 0.1, "trans_w2": None, "GIC_BD": False},
                  (15, 16, 1): {"has_trans": True, "resistance": None,
                    "type": "auto", "trans_w1": 0.04, "trans_w2": 0.06, "GIC_BD": False},
                  (6, 7, 1): {"has_trans": True, "resistance": None,
                    "type": "gsu", "trans_w1": 0.15, "trans_w2": None, "GIC_BD": False},
                  (6, 8, 2): {"has_trans": True, "resistance": None,
                    "type": "gsu", "trans_w1": 0.15, "trans_w2": None, "GIC_BD": False},
                  (5, 20, 1): {"has_trans": True, "resistance": None,
                    "type": "gy", "trans_w1": 0.04, "trans_w2": 0.06, "GIC_BD": False},
                  (5, 20, 2): {"has_trans": True, "resistance": None,
                    "type": "gy", "trans_w1": 0.04, "trans_w2": 0.06, "GIC_BD": False},
                  (12, 13, 1): {"has_trans": True, "resistance": None,
                    "type": "gsu", "trans_w1": 0.1, "trans_w2": None, "GIC_BD": False},
                  (12, 14, 2): {"has_trans": True, "resistance": None,
                    "type": "gsu", "trans_w1": 0.1, "trans_w2": None, "GIC_BD": False},
                  (4, 3, 2): {"has_trans": True, "resistance": None,
                    "type": "auto", "trans_w1": 0.04, "trans_w2": 0.06, "GIC_BD": False},
                  (4, 3, 3): {"has_trans": True, "resistance": None,
                    "type": "gy", "trans_w1": 0.2, "trans_w2": 0.1, "GIC_BD": False},
                  (4, 3, 4): {"has_trans": True, "resistance": None,
                    "type": "auto", "trans_w1": 0.04, "trans_w2": 0.06, "GIC_BD": False},
                  (15, 16, 2): {"has_trans": True, "resistance": None,
                    "type": "auto", "trans_w1": 0.04, "trans_w2": 0.06, "GIC_BD": False}
                  }

# hard coding dataframe for 6 bus case testing, making sure it can do multiple times
E_data = {'time': [1, 2],
          'Ex':[0, 1],
          'Ey':[1, 0]}

E_data_df = pd.DataFrame(E_data)

# function to find endpoints of lines and calculate length


def list_line_data(substation_data, bus_data, branch_data):
    # creating empty lists to hold data for endpoints and then length info for input voltage calculations
    lines = []
    # using a count variable to name the lines for tracking info
    count = 0
    # for loop to loop through branch_data info
    for line, data in branch_data.items():
        # if statement to differentiate a line from a transformer
        if not data["has_trans"]:
            # gathering line tuple
            from_bus, to_bus, circuit = line
            # cross-referencing the bus info to get the lat and long of the to and from buses
            from_lat, from_long = substation_data[bus_data[from_bus]["sub_num"]]["lat"], \
            substation_data[bus_data[from_bus]["sub_num"]]["long"]
            to_lat, to_long = substation_data[bus_data[to_bus]["sub_num"]]["lat"], \
            substation_data[bus_data[to_bus]["sub_num"]]["long"]
            # increasing count
            resistance = branch_data[line]["resistance"]
            count += 1
            # appending info to empty list created before loop
            lines.append({
                "line_number": count,
                "from_bus": from_bus,
                "to_bus": to_bus,
                "circuit": circuit,
                "from_lat": from_lat,
                "from_long": from_long,
                "to_lat": to_lat,
                "to_long": to_long,
                "resistance": resistance
            })
    return lines


def list_transformer_data(branch_data):
    count = 0
    transformers = []
    for transformer, data in branch_data.items():
        if data["has_trans"]:
            count += 1
            # gathering line tuple
            W1, W2, circuit = transformer
            res_w1 = branch_data[transformer]["trans_w1"]
            res_w2 = branch_data[transformer]["trans_w2"]
            trans_type = branch_data[transformer]["type"]
            transformers.append({
                "trans_number": count,
                "W1_bus": W1,
                "W2_bus": W2,
                "circuit": circuit,
                "type": trans_type,
                "res_w1": res_w1,
                "res_w2": res_w2
            })
    return transformers


def generate_line_length(line_data):
    # variables listed below are for calculating the lengths
    phi = 0
    LN = 0
    LE = 0
    delta_long = 0
    delta_lat = 0
    line_length = []
    for info in line_data:
        phi = (info['from_lat'] + info['to_lat']) / 2
        phi = math.radians(phi)
        delta_lat = info['to_lat'] - info['from_lat']
        delta_long = info['to_long'] - info['from_long']
        line_num = info['line_number']
        resistance = info['resistance']
        LN = (111.133 - (0.56 * math.cos(phi * 2))) * delta_lat
        LE = (111.5065 - (0.1872 * math.cos(phi * 2))) * math.cos(phi) * delta_long
        line_length.append({
            "line_number": line_num,
            "LN": LN,
            "LE": LE,
            "resistance": resistance
        })

    return line_length


def input_voltage_calculation(line_length, E_data_df):
    # Copying the 'time' column
    IV_data = {'time': E_data_df['time']}

    for line in line_length:
        line_number = line['line_number']
        LN = line['LN']
        LE = line['LE']

        # Calculate the value for the corresponding line number
        IV_data[line_number] = (LE * E_data_df['Ex']) + (LN * E_data_df['Ey'])

    IV_df = pd.DataFrame(IV_data)

    return IV_df


def equivalent_current_calc(line_data, IV_df):
    EC_data = {'time': IV_df['time']}

    for line in line_data:
        line_number = line['line_number']
        resistance = line['resistance']
        indexer = line['line_number']
        EC_data[line_number] = (3 * IV_df[indexer]) / resistance

    EC_df = pd.DataFrame(EC_data)

    return EC_df


def generate_nodes(branch_data):
    nodes = set()

    for (W1_side, W2_side, circuit), data in branch_data.items():
        if data["type"] == "gsu":
            nodes.add(str(W1_side))
        elif data["type"] == "auto":
            nodes.add(str(W1_side))
            nodes.add(str(W2_side))
        elif data["type"] == "gy":
            nodes.add(str(W1_side))
            nodes.add(str(W2_side))
            nodes.add(f"between_{W1_side}_{W2_side}")
            # W1_side analogous to from_bus and W2_side analogous to to_bus
        elif data["type"] == None:
            nodes.add(str(W1_side))
            nodes.add(str(W2_side))

    return list(nodes)


def find_parallel_lines(line_list):

    parallel_lines = []

    for i in range(len(line_list)):
        j = len(line_list) - 1
        if line_list[i]["circuit"] == 1:
            parallels = []
            initial_line = line_list[i]["line_number"]
            parallels.append(initial_line)
            while j > i:
                initial_line = line_list[i]["line_number"]
                if line_list[i]["from_bus"] == line_list[j]["from_bus"] and line_list[i]["to_bus"] == line_list[j]["to_bus"] and \
                        line_list[i]["circuit"] != line_list[j]["circuit"]:
                    additional_line = line_list[j]["line_number"]
                    parallels.append(additional_line)
                j -= 1
            if len(parallels) > 1:
                parallel_lines.append({
                    "in_parallel": parallels
                })
    return parallel_lines


def find_parallel_transformers(transformer_list):

    parallel_transformers = []

    for i in range(len(transformer_list)):
        j = len(transformer_list) - 1
        if transformer_list[i]["circuit"] == 1:
            parallels = []
            initial_transformer = transformer_list[i]["trans_number"]
            parallels.append(initial_transformer)
            while j > i:
                if transformer_list[i]["type"] == "gsu":
                    if transformer_list[i]["W1_bus"] == transformer_list[j]["W1_bus"] and transformer_list[i]["circuit"] != \
                            transformer_list[j]["circuit"]:
                        additional_transformer = transformer_list[j]["trans_number"]
                        parallels.append(additional_transformer)
                if transformer_list[i]["W1_bus"] == transformer_list[j]["W1_bus"] and transformer_list[i]["W2_bus"] == \
                        transformer_list[j]["W2_bus"] \
                        and transformer_list[i]["circuit"] != transformer_list[j]["circuit"]:
                    additional_transformer = transformer_list[j]["trans_number"]
                    parallels.append(additional_transformer)
                j -= 1
            if len(parallels) > 1:
                parallel_transformers.append({
                    "in_parallel": parallels
                })
    return parallel_transformers


pd.set_option('display.max_columns', None)

line_list = list_line_data(substation_data_20, bus_data_20, branch_data_20)
# line_list_6 = list_line_data(substation_data_6, bus_data_6, branch_data_6)
# transformer_list_6 = list_transformer_data(branch_data_6)



transformer_list = list_transformer_data(branch_data_20)

line_length = generate_line_length(line_list)


IV_df = input_voltage_calculation(line_length, E_data_df)

# print(IV_df)
# print("")


EC_df = equivalent_current_calc(line_list, IV_df)
# print(EC_df)
# print("")

nodes = generate_nodes(branch_data_20)
# print(nodes)
# print(len(nodes))
# print("")

parallel_lines = find_parallel_lines(line_list)

# print(parallel_lines)
# print("")

parallel_transformers = find_parallel_transformers(transformer_list)

# print(parallel_transformers)



# start by associating line using from and to buses with substation to gather coordinates
# use function in previous version to calculate input voltage
# test with a dataframe for E field
# define nodes using substation as starting point
# create conductance matrix
