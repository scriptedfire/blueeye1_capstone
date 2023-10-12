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


E_data_20 = {'time': [1, 2],
          'Ex': [0, 1],
          'Ey': [1, 0]}

E_data_6 = {'time': [1, 2],
          'Ex': [10, 10],
          'Ey': [0, 0]}

E_data_df_20 = pd.DataFrame(E_data_20)

E_data_df_6 = pd.DataFrame(E_data_6)
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
            gic_bd = branch_data[line]["GIC_BD"]
            count += 1
            # appending info to empty list created before loop
            lines.append({
                "line_number": count,
                "tuple": (from_bus, to_bus, circuit),
                "from_bus": from_bus,
                "to_bus": to_bus,
                "circuit": circuit,
                "from_lat": from_lat,
                "from_long": from_long,
                "to_lat": to_lat,
                "to_long": to_long,
                "resistance": resistance,
                "GIC_BD": gic_bd
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
            gic_bd = branch_data[transformer]["GIC_BD"]
            transformers.append({
                "trans_number": count,
                "W1_bus": W1,
                "W2_bus": W2,
                "circuit": circuit,
                "type": trans_type,
                "res_w1": res_w1,
                "res_w2": res_w2,
                "GIC_BD": gic_bd
            })
    return transformers
# list_transformer_data may be moot


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
        line_tuple = info['tuple']
        resistance = info['resistance']
        gic_bd = info['GIC_BD']
        LN = (111.133 - (0.56 * math.cos(phi * 2))) * delta_lat
        LE = (111.5065 - (0.1872 * math.cos(phi * 2))) * math.cos(phi) * delta_long
        line_length.append({
            "line_number": line_num,
            "tuple": line_tuple,
            "LN": LN,
            "LE": LE,
            "resistance": resistance,
            "GIC_BD": gic_bd
        })

    return line_length


def input_voltage_calculation(line_length, E_data_df):
    # Copying the 'time' column
    IV_data = {'time': E_data_df['time']}

    for line in line_length:
        line_tuple = line['tuple']
        LN = line['LN']
        LE = line['LE']

        # Calculate the value for the corresponding line number
        IV_data[line_tuple] = (LE * E_data_df['Ex']) + (LN * E_data_df['Ey'])

    IV_df = pd.DataFrame(IV_data)

    return IV_df


def equivalent_current_calc(line_data, IV_df):
    EC_data = {'time': IV_df['time']}

    for line in line_data:
        line_tuple = line['tuple']
        if line['GIC_BD']:
            resistance = line['resistance'] + 1e6
        else:
            resistance = line['resistance']
        indexer = line['tuple']
        EC_data[line_tuple] = (3 * IV_df[indexer]) / resistance

    EC_df = pd.DataFrame(EC_data)

    return EC_df


def generate_nodes_and_network(branch_data, bus_data, substation_data):
    nodes = {}

    for element, data in branch_data.items():
        W1_side, W2_side, circuit = element
        substation_tuple = ("sub_num", bus_data[W1_side]['sub_num'], substation_data[bus_data[W1_side]['sub_num']]['ground_r'])
        if data["type"] == "gsu":
            try:
                nodes[W1_side].append((element, branch_data[element]['type'], branch_data[element]['trans_w1']/3))
            except KeyError:
                nodes[W1_side] = [(element, branch_data[element]['type'], branch_data[element]['trans_w1']/3)]
            try:
                if substation_tuple not in nodes[W1_side]:
                    nodes[W1_side].append(substation_tuple)
            except Exception as e:
                print("Error:", e)
        elif data["type"] == "auto":
            # W2 is common for auto
            # W1 is series
            try:
                nodes[W1_side].append((element, branch_data[element]['type']+" series", branch_data[element]['trans_w1']/3))
            except KeyError:
                nodes[W1_side] = [(element, branch_data[element]['type']+" series", branch_data[element]['trans_w1']/3)]
            try:
                nodes[W2_side].append((element, branch_data[element]['type']+" common", branch_data[element]['trans_w2']/3))
                nodes[W2_side].append((element, branch_data[element]['type']+" series", branch_data[element]['trans_w1']/3))
            except KeyError:
                nodes[W2_side] = [(element, branch_data[element]['type']+" common", branch_data[element]['trans_w2']/3)]
                nodes[W2_side].append((element, branch_data[element]['type']+" series", branch_data[element]['trans_w1']/3))
            try:
                if substation_tuple not in nodes[W2_side] and substation_tuple not in nodes[f"between_{W1_side}_{W2_side}"]:
                    nodes[W2_side].append(substation_tuple)
            except KeyError:
                nodes[W2_side].append(substation_tuple)
        elif data["type"] == "gy":
            # W1 is HV
            # W2 is LV
            try:
                nodes[W1_side].append((element, branch_data[element]['type']+" HV", branch_data[element]['trans_w1']/3))
            except KeyError:
                nodes[W1_side] = [(element, branch_data[element]['type']+" HV", branch_data[element]['trans_w1']/3)]
            try:
                nodes[W2_side].append((element, branch_data[element]['type']+" LV", branch_data[element]['trans_w2']/3))
            except KeyError:
                nodes[W2_side] = [(element, branch_data[element]['type']+" LV", branch_data[element]['trans_w2']/3)]
            try:
                nodes[f"between_{W1_side}_{W2_side}"].append((element, branch_data[element]['type']+" HV", branch_data[element]['trans_w1']/3))
                nodes[f"between_{W1_side}_{W2_side}"].append((element, branch_data[element]['type']+" LV", branch_data[element]['trans_w2']/3))
            except KeyError:
                nodes[f"between_{W1_side}_{W2_side}"] = [(element, branch_data[element]['type']+" HV", branch_data[element]['trans_w1']/3)]
                nodes[f"between_{W1_side}_{W2_side}"].append((element, branch_data[element]['type']+" LV", branch_data[element]['trans_w2']/3))
            try:
                if substation_tuple not in nodes[f"between_{W1_side}_{W2_side}"]:
                    nodes[f"between_{W1_side}_{W2_side}"].append(substation_tuple)
                if substation_tuple in nodes[W2_side]:
                    nodes[W2_side].remove(substation_tuple)
            except Exception as e:
                print("Error:", e)
        elif not data["has_trans"]:
            try:
                nodes[W1_side].append((element, "line", branch_data[element]['resistance']/3))
            except KeyError:
                nodes[W1_side] = [(element, "line", branch_data[element]['resistance']/3)]
            try:
                nodes[W2_side].append((element, "line", branch_data[element]['resistance']/3))
            except KeyError:
                nodes[W2_side] = [(element, "line", branch_data[element]['resistance']/3)]

    auto_and_gy = []
    for key, list in nodes.items():
        has_auto = False
        has_gy = False
        for tuple, type, resistance in list:
            try:
                if branch_data[tuple]['type'] == "auto":
                    has_auto = True
                    if type == "auto common":
                        auto_and_gy.append((tuple, type, resistance))
                elif branch_data[tuple]['type'] == "gy":
                    has_gy = True
            except Exception:
                pass
        if has_auto and has_gy:
            for item in auto_and_gy:
                tup, typ, res = item
                if item not in nodes[f"between_{tup[0]}_{tup[1]}"]:
                    nodes[f"between_{tup[0]}_{tup[1]}"].append(item)
        else:
            auto_and_gy = []

    return nodes


def nodal_indexer(nodes):
    nodal_index = {}
    a = 0
    for key, value in nodes.items():
        nodal_index[key] = a
        a += 1
    return nodal_index


def reverse_map_nodes(nodes, nodal_index, branch_data):
    reverse_mapping = {}
    # Iterate through the keys and values of the input dictionary
    for key, value_list in nodes.items():
        for value_tuple in value_list:
            # Check if the value_tuple is already in the reverse_mapping
            if value_tuple in reverse_mapping:
                # If it is, append the current key to the list of associated keys
                reverse_mapping[value_tuple].append(nodal_index[key])
            else:
                # If it's not, create a new list with the current key
                reverse_mapping[value_tuple] = [nodal_index[key]]

    grouped_dict = {}

    for key, value in reverse_mapping.items():
        # Convert the value list to a tuple to make it hashable
        value_tuple = tuple(value)

        # Check if the value tuple is already a key in the grouped_dict
        if value_tuple in grouped_dict:
            # If it is, append the current key to the list of keys for that value
            grouped_dict[value_tuple].append(list(key))
        else:
            # If not, create a new list with the current key as the first element
            grouped_dict[value_tuple] = [list(key)]

    for key, values in grouped_dict.items():
        para = []
        sub_connect = []
        total_res = 0
        if len(values) > 1:
            for i in range(len(values)):
                if values[i][0] in branch_data:
                    para.append(values[i][2])
                else:
                    sub_connect.append(values[i][2])
            if len(para) > 1 and len(sub_connect) == 1:
                equiv_res = parallel_resistance_calculator(para)
                total_res = equiv_res + sub_connect[0]
                grouped_dict[key].append(("total resistance", total_res, equiv_res))
            elif len(para) > 1 and len(sub_connect) == 0:
                total_res = parallel_resistance_calculator(para)
                grouped_dict[key].append(("total resistance", total_res, "parallel transformers"))
            elif len(para) == 1 and len(sub_connect) == 1:
                total_res = para[0] + sub_connect[0]
                grouped_dict[key].append(("total resistance", total_res, "transformer to sub"))
        else:
            total_res = values[0][2]
            grouped_dict[key].append(("total resistance", total_res))

    return grouped_dict


def parallel_resistance_calculator(parallel):
    inverse_res = 0
    for i in range(len(parallel)):
        inverse_res += (1/parallel[i])

    r_equiv = 1 / inverse_res

    return r_equiv


def node_voltage_calculator(cond_mat, ic_mat):
    # this function uses matrix multiplication to find the nodal voltages
    # taking the inverse of the conductance matrix
    inv_cond_mat = np.linalg.inv(cond_mat)

    node_volt_mat = np.matmul(inv_cond_mat, ic_mat)
    # returning array
    return node_volt_mat


def ic_mat_generator_gic_df(nodal_index, EC_df, reverse_mapping, cond_mat):
    gic_data = {}
    ic_matrix = np.zeros((len(nodal_index), 1))
    tl_nodes = {}
    for keys, values in reverse_mapping.items():
        for i in range(len(values)):
            if values[i][1] == "line":
                try:
                    tl_nodes[keys].append((values[i], None))
                except KeyError:
                    tl_nodes[keys] = [(values[i], None)]

    for index, row in EC_df.iterrows():
        for key, value_list in tl_nodes.items():
            updated_value_list = []
            for item in value_list:
                toop = item[0][0]
                if toop in row.index:
                    column_value = row[toop]
                    updated_item = (item[0], column_value)
                    updated_value_list.append(updated_item)
                else:
                    updated_value_list.append(item)
            tl_nodes[key] = updated_value_list

        for key, values in tl_nodes.items():
            indexer = list(key)
            for i in range(len(values)):
                current = values[i][1]
                ic_matrix[indexer[0]] += current
                ic_matrix[indexer[1]] -= current
        bus_voltage = node_voltage_calculator(cond_mat, ic_matrix)
        gics = gic_value_calculator(reverse_mapping, tl_nodes, bus_voltage)
        if len(gic_data) == 0:
            gic_data['time'] = [EC_df.loc[index][0]]
            for marker, info in gics.items():
                gic_data[marker] = [info]
        elif len(gic_data) > 0:
            gic_data['time'].append(EC_df.loc[index][0])
            for marker, info in gics.items():
                gic_data[marker].append(info)
        ic_matrix = np.zeros((len(nodal_index), 1))
    gic_df = pd.DataFrame(gic_data)
    return gic_df


def cond_mat_generator(nodal_index, reverse_map):
    conductance_matrix = np.zeros((len(nodal_index), len(nodal_index)))

    for key, values in reverse_map.items():
        indexer = list(key)
        if len(values) > 1:
            conductance = 0
            for i in range(len(values)):
                if values[i][0] == "total resistance":
                    conductance = 1 / values[i][1]
            if len(indexer) == 1:  # For keys with a single index, e.g., (1,)
                conductance_matrix[indexer[0]][indexer[0]] += conductance
            elif len(indexer) == 2:  # For keys with two indices, e.g., (1, 2)
                conductance_matrix[indexer[0]][indexer[0]] += conductance
                conductance_matrix[indexer[1]][indexer[1]] += conductance
                conductance_matrix[indexer[0]][indexer[1]] -= conductance
                conductance_matrix[indexer[1]][indexer[0]] -= conductance

    return conductance_matrix


def gic_value_calculator(reverse_map, tl_nodes, nodal_volt_mat):
    gic_data = {}
    for key, values in reverse_map.items():
        gics = 0
        key_list = list(key)
        try:
            if reverse_map[key][0][1] != "line":
                for j in range(len(values)):
                    if values[j][0] == "total resistance" and len(key_list) == 1:
                        gics = float((1 / values[j][1]) * nodal_volt_mat[key_list[0]])
                        gic_data[str(reverse_map[key][0][0]) + " " + reverse_map[key][0][1]] = [gics]
                    elif values[j][0] == "total resistance" and len(key_list) == 2:
                        gics = float((1 / values[j][1]) * (nodal_volt_mat[key_list[0]] - nodal_volt_mat[key_list[1]]))
                        gic_data[str(reverse_map[key][0][0]) + " " + reverse_map[key][0][1]] = [gics]
        except KeyError:
            pass
        for keys, value in tl_nodes.items():
            gics = 0
            key_list2 = list(keys)
            try:
                gics = (-1*value[0][1]) + float(((1 / value[0][0][2]) * (nodal_volt_mat[key_list2[0]] - nodal_volt_mat[key_list2[1]])))
                gic_data[value[0][0][0]] = [gics]
            except IndexError as e:
                print(e)
                print(keys)

    return gic_data


if __name__ == '__main__':

    pd.set_option('display.max_columns', None)

    # line_list = list_line_data(substation_data_20, bus_data_20, branch_data_20)

    line_list_6 = list_line_data(substation_data_6, bus_data_6, branch_data_6)

    # line_length = generate_line_length(line_list)

    line_length_6 = generate_line_length(line_list_6)

    # IV_df = input_voltage_calculation(line_length, E_data_df_20)
    IV_df_6 = input_voltage_calculation(line_length_6, E_data_df_6)


    # EC_df = equivalent_current_calc(line_length, IV_df)

    EC_df_6 = equivalent_current_calc(line_length_6, IV_df_6)


    # nodes = generate_nodes_and_network(branch_data_20, bus_data_20, substation_data_20)
    nodes_6 = generate_nodes_and_network(branch_data_6, bus_data_6, substation_data_6)


    # nodal_index = nodal_indexer(nodes)
    # reverse_mapping = reverse_map_nodes(nodes, nodal_index, branch_data_20)


    nodal_index_6 = nodal_indexer(nodes_6)
    reverse_mapping_6 = reverse_map_nodes(nodes_6, nodal_index_6, branch_data_6)


    cond_mat_6 = cond_mat_generator(nodal_index_6, reverse_mapping_6)

    # cond_mat_20 = cond_mat_generator(nodal_index, reverse_mapping)

    gic_df = ic_mat_generator_gic_df(nodal_index_6, EC_df_6, reverse_mapping_6, cond_mat_6)
    print(gic_df)



