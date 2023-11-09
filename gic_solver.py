import math
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
# import make3DPandas # for testing only


def get_line_Efield(df_3D: pd.DataFrame, from_coords: list, to_coords: list) -> pd.DataFrame:
    """ This function takes in a multi index pandas dataframe indexed by time, longitude and latitude.
        It also requires the from coordinates and to coordinates of a TL
        @param: df_3d: the 3D pandas dataframe
        @param: from_coords: the coordinates of the from bus in degrees (longitude, latitude)
        @param: to_coords: the coordinates of the to bus in degrees (longitude, latitude)
        return: line_dict: dataframe with the time series data of the e field data for a single line
    """

    index_list = df_3D.index

    west_east = (df_3D.index[0][1], df_3D.index[2][1])
    south_north = (df_3D.index[0][2], df_3D.index[1][2])

    north_east = (south_north[1], west_east[1])
    south_east = (south_north[0], west_east[1])

    north_west = (south_north[1], west_east[0])
    south_west = (south_north[0], west_east[0])

    time_array = []
    time = 0
    for i in index_list:
        if i[0] == time:
            continue
        time = i[0]
        time_array.append(time)

    time_array = np.array(time_array)

    line_dict = {'time': time_array, 'Ex': np.zeros(time_array.size), 'Ey': np.zeros(time_array.size)}

    for i, time in enumerate(time_array):
        north_east_Efield = [df_3D.loc[(time, north_east[1], north_east[0]), 'Ex'],
                             df_3D.loc[(time, north_east[1], north_east[0]), 'Ey']]
        north_west_Efield = [df_3D.loc[(time, north_west[1], north_west[0]), 'Ex'],
                             df_3D.loc[(time, north_west[1], north_west[0]), 'Ey']]

        south_east_Efield = [df_3D.loc[(time, south_east[1], south_east[0]), 'Ex'],
                             df_3D.loc[(time, south_east[1], south_east[0]), 'Ey']]
        south_west_Efield = [df_3D.loc[(time, south_west[1], south_west[0]), 'Ex'],
                             df_3D.loc[(time, south_west[1], south_west[0]), 'Ey']]

        data_x = [[south_west_Efield[0], south_east_Efield[0]],
                  [north_west_Efield[0], north_east_Efield[0]]]
        data_y = [[south_west_Efield[1], south_east_Efield[1]],
                  [north_west_Efield[1], north_east_Efield[1]]]

        E_field_grid_x = RegularGridInterpolator((west_east, south_north), data_x)
        E_field_grid_y = RegularGridInterpolator((west_east, south_north), data_y)

        from_to_points = np.array([from_coords, to_coords])

        from_to_Efield_x = E_field_grid_x(from_to_points)
        from_to_Efield_y = E_field_grid_y(from_to_points)

        norm_x = np.mean(from_to_Efield_x)

        norm_y = np.mean(from_to_Efield_y)

        line_dict["Ex"][i] = norm_x
        line_dict["Ey"][i] = norm_y

    return pd.DataFrame(line_dict)

# below is hard coded dictionaries for 6 bus case and 20 bus case
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

# hard coded e field data for different cases
E_data_20 = {'time': [1, 2],
             'Ex': [0, 1],
             'Ey': [1, 0]}

E_data_6 = {'time': [1, 2],
            'Ex': [10, 10],
            'Ey': [0, 0]}

E_data_20N = {'time': [1, 2],
              'Ex': [0, 0],
              'Ey': [1, 10]}

E_data_20E = {'time': [1, 2],
              'Ex': [1, 1],
              'Ey': [0, 0]}

E_data_df_20 = pd.DataFrame(E_data_20)

E_data_df_6 = pd.DataFrame(E_data_6)

E_data_df_20N = pd.DataFrame(E_data_20N)

E_data_df_20E = pd.DataFrame(E_data_20E)


def list_line_data(substation_data: dict, bus_data: dict, branch_data: dict) -> list:
    """ This method takes in the grid data dictionaries and iterates through them to gather all necessary information
            for the transmission lines, e.g. coordinates, resistance, etc.
            @param: substation_data: dictionary that contains latitudes and longitudes of substations in grid
            @param: bus_data: dictionary that correlates bus numbers with substation numbers
            @param: branch_data: dictionary that holds grid information pertaining to transmission lines
            and transformers.
            return: lines: list of dictionaries containing relevant information for transmission lines in grid.
        """
    # creating empty lists to hold data for endpoints and then length info for input voltage calculations
    lines = []
    # using a count variable to name the lines for tracking info
    count = 0
    # for loop to iterate through branch_data info
    for line, data in branch_data.items():
        # if statement to differentiate a line from a transformer
        if not data["has_trans"]:
            # gathering line tuple
            from_bus, to_bus, circuit = line
            # cross-referencing the bus info to get the lat and long of the to and from buses
            # using dictionaries to gather other relevant data, e.g. resistance
            from_lat, from_long = substation_data[bus_data[from_bus]["sub_num"]]["lat"], \
                substation_data[bus_data[from_bus]["sub_num"]]["long"]
            to_lat, to_long = substation_data[bus_data[to_bus]["sub_num"]]["lat"], \
                substation_data[bus_data[to_bus]["sub_num"]]["long"]
            resistance = branch_data[line]["resistance"]
            gic_bd = branch_data[line]["GIC_BD"]
            # increasing count
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


def generate_line_length(line_data: list) -> list:
    """ This method uses the transmission line data contained in the line_data list to calculate the northward and
                eastward length of the transmission lines. These values and the E-field data are used to calculate
                the input voltages on the lines. Formulas used come from p. 2372 of A Test Case for the Calculation of
                Geomagnetically Induced Currents Article in IEEE Transactions on Power Delivery ·
                October 2012 DOI: 10.1109/TPWRD.2012.2206407
                @param: line_data: a list of dictionaries that contains transmission line information
                return: line_length: list of dictionaries containing transmission line lengths and other relevant data.
            """
    # empty list to hold info
    line_length = []
    for info in line_data:
        # looping through the line data list used as input
        phi = (info['from_lat'] + info['to_lat']) / 2
        phi = math.radians(phi)
        # switching from degrees to radians
        delta_lat = info['to_lat'] - info['from_lat']
        delta_long = info['to_long'] - info['from_long']
        # calculating difference in longs and lats
        line_num = info['line_number']
        line_tuple = info['tuple']
        resistance = info['resistance']
        gic_bd = info['GIC_BD']
        # pulling other relevant data
        LN = (111.133 - (0.56 * math.cos(phi * 2))) * delta_lat
        # LN is northward length, using formula from test case/study
        LE = (111.5065 - (0.1872 * math.cos(phi * 2))) * math.cos(phi) * delta_long
        # LE is eastward length
        line_length.append({
            # appending data to empty list
            "line_number": line_num,
            "tuple": line_tuple,
            "LN": LN,
            "LE": LE,
            "resistance": resistance,
            "GIC_BD": gic_bd,
            "from_coords": [info['from_long'], info['from_lat']],
            "to_coords": [info['to_long'], info['to_lat']]
        })

    return line_length


def input_voltage_calculation(line_length: list, E_data_df: pd.DataFrame) -> pd.DataFrame:
    """ This method accepts the list of a dictionary with line data in it as well as the 3D pandas dataframe with the
        e field data in it. It returns the input voltages for all time and all lines
        @param: line_length: list of dictionaries with line data
        @param: E_data_df: pandas dataframe with multindex e field data from Electric Field Calculator
        return: IV_df pandas dataframe with input voltages.
    """

    IV_data = {}
    # empty dictionary to hold input voltage data
    for line in line_length:
        line_tuple = line['tuple']
        LN = line['LN']
        LE = line['LE']

        from_coords = line["from_coords"]
        to_coords = line["to_coords"]
        # pulling coordinates from line_length list

        E_line_data_df = get_line_Efield(E_data_df, from_coords, to_coords)
        # generating E-field info for each line
        # interpolating to create uniform field for the transmission line

        line_Ex = E_line_data_df['Ex']
        line_Ey = E_line_data_df['Ey']

        # Calculate the value for the corresponding line
        IV_data[line_tuple] = (LE * line_Ex) + (LN * line_Ey)
    # add the time to the dataframe
    IV_data["time"] = E_line_data_df["time"]
    IV_df = pd.DataFrame(IV_data)

    return IV_df


def equivalent_current_calc(line_data: list, IV_df: pd.DataFrame) -> pd.DataFrame:
    """ This method accepts the list of a dictionary with line data in it as well as the 3D pandas dataframe with the
            input voltage data in it. It then calculates what the equivalent current on the transmission line would be
            based on Ohm's law (V = IR). This is used to create a Norton equivalent of the dc equivalent model
            of the inputted grid
            @param: line_data: list of dictionaries with line data generated by generate_line_length function
            @param: IV_df: pandas dataframe with input voltage for each transmission line for the time series
            return: EC_df: pandas dataframe with equivalent current for each transmission line for the time series.
        """
    # copying time data
    EC_data = {'time': IV_df['time']}

    for line in line_data:
        # looping through line data
        line_tuple = line['tuple']
        # variable for indexing DataFrame
        if line['GIC_BD']:
            # GIC_BD is a series capacitance for transmission lines
            # altered value of resistance to try to match case study reported values
            # attempt 1: modeled as high resistance, i.e. 1e6 - unsuccessful
            # attempt 2: resistance unaltered - unsuccessful
            # attempt 3: resistance doubled, current therefore halved - successful for northward only e-field
            # Doubling resistance doesn't work for eastward only e-field; cause of issue unclear
            resistance = line['resistance'] * 2
        else:
            resistance = line['resistance']
        indexer = line['tuple']
        # another variable for indexing, DataFrame was behaving strangely when just using line_tuple
        EC_data[line_tuple] = (3 * IV_df[indexer]) / resistance
        # I = V / R, adjusted from 3 phase value

    # converting to DataFrame
    EC_df = pd.DataFrame(EC_data)

    return EC_df


def generate_nodes_and_network(branch_data: dict, bus_data: dict, substation_data: dict) -> dict:
    """ This method takes in the grid data dictionaries and uses the information to locate all nodes within the grid.
                These nodes are used for nodal analysis method to ultimately calculate current in windings and lines
                @param: substation_data: dictionary that contains latitudes and longitudes of substations in grid
                @param: bus_data: dictionary that correlates bus numbers with substation numbers
                @param: branch_data: dictionary that holds grid information pertaining to transmission lines
                and transformers.
                return: nodes: dictionary containing bus numbers as keys. Values associated with keys are the information
                for the transformers, transmission lines, and/or substation connected to the bus. All resistances corrected
                from 3 phase.
            """
    # empty list to hold node info
    nodes = {}

    for element, data in branch_data.items():
        # looping through branch data that contains
        W1_side, W2_side, circuit = element
        # breaking down tuple into its components
        substation_tuple = (
            "sub_num", str(bus_data[W1_side]['sub_num']), substation_data[bus_data[W1_side]['sub_num']]['ground_r'])
        # using bus_data and substation_data to pull info on substations not contained in branch_data
        if data["type"] == "gsu":
            # logic for placing a gsu type transformer
            # all resistances, except for substations, corrected from three-phase
            # gsu will be combination of delta and wye connection
            # delta connection will have 'None' for resistance
            # using if and elif statements to check which side has the delta connection
            if branch_data[element]['trans_w2'] is None:
                try:
                    if branch_data[element]['GIC_BD']:
                        # if it has a GIC blocking device, resistance modeled as extremely high
                        # only on gsu
                        nodes[W1_side].append(
                            (element, branch_data[element]['type'], (branch_data[element]['trans_w1'] / 3) + 1e6))
                    else:
                        nodes[W1_side].append(
                            (element, branch_data[element]['type'], branch_data[element]['trans_w1'] / 3))
                except KeyError:
                    # try except used to avoid KeyError issue when placing info in nodes dictionary
                    if branch_data[element]['GIC_BD']:
                        nodes[W1_side] = [
                            (element, branch_data[element]['type'], (branch_data[element]['trans_w1'] / 3) + 1e6)]
                    else:
                        nodes[W1_side] = [(element, branch_data[element]['type'], branch_data[element]['trans_w1'] / 3)]
                try:
                    # connecting corresponding substation to node
                    if substation_tuple not in nodes[W1_side]:
                        nodes[W1_side].append(substation_tuple)
                except Exception as e:
                    print("Error:", e)
            elif branch_data[element]['trans_w1'] is None:
                # same process as above, just switched from W1_side to W2_side and from 'trans_w1' to 'trans_w2'
                try:
                    if branch_data[element]['GIC_BD']:
                        # if it has a GIC blocking device, resistance modeled as extremely high
                        # only on gsu
                        nodes[W2_side].append(
                            (element, branch_data[element]['type'], (branch_data[element]['trans_w2'] / 3) + 1e6))
                    else:
                        nodes[W2_side].append(
                            (element, branch_data[element]['type'], branch_data[element]['trans_w2'] / 3))
                except KeyError:
                    if branch_data[element]['GIC_BD']:
                        # if it has a GIC blocking device, resistance modeled as extremely high
                        # only on gsu
                        nodes[W2_side] = [
                            (element, branch_data[element]['type'], (branch_data[element]['trans_w2'] / 3) + 1e6)]
                        # gsu only connected on W1 side
                    else:
                        nodes[W2_side] = [(element, branch_data[element]['type'], branch_data[element]['trans_w2'] / 3)]
                try:
                    # connecting corresponding substation to node
                    if substation_tuple not in nodes[W2_side]:
                        nodes[W2_side].append(substation_tuple)
                except Exception as e:
                    print("Error:", e)
        elif data["type"] == "auto":
            # similar logic for placing an autotransformer, which has two elements
            # W2 is common for auto
            # W1 is series
            # series component connect at W1 and W2 side
            try:
                nodes[W1_side].append(
                    (element, branch_data[element]['type'] + " series", branch_data[element]['trans_w1'] / 3))
            except KeyError:
                nodes[W1_side] = [
                    (element, branch_data[element]['type'] + " series", branch_data[element]['trans_w1'] / 3)]
            try:
                nodes[W2_side].append(
                    (element, branch_data[element]['type'] + " common", branch_data[element]['trans_w2'] / 3))
                nodes[W2_side].append(
                    (element, branch_data[element]['type'] + " series", branch_data[element]['trans_w1'] / 3))
            except KeyError:
                nodes[W2_side] = [
                    (element, branch_data[element]['type'] + " common", branch_data[element]['trans_w2'] / 3)]
                nodes[W2_side].append(
                    (element, branch_data[element]['type'] + " series", branch_data[element]['trans_w1'] / 3))
            try:
                # placing connected substation
                # connected to auto common, i.e. W2_side
                # and statement used for case where an auto and gy are in parallel
                if substation_tuple not in nodes[W2_side] and substation_tuple not in nodes[
                    f"between_{W1_side}_{W2_side}"]:
                    nodes[W2_side].append(substation_tuple)
            except KeyError:
                nodes[W2_side].append(substation_tuple)
        elif data["type"] == "gy":
            # similar process as above
            # W1 is HV of gy
            # W2 is LV of gy
            try:
                nodes[W1_side].append(
                    (element, branch_data[element]['type'] + " HV", branch_data[element]['trans_w1'] / 3))
            except KeyError:
                nodes[W1_side] = [(element, branch_data[element]['type'] + " HV", branch_data[element]['trans_w1'] / 3)]
            try:
                nodes[W2_side].append(
                    (element, branch_data[element]['type'] + " LV", branch_data[element]['trans_w2'] / 3))
            except KeyError:
                nodes[W2_side] = [(element, branch_data[element]['type'] + " LV", branch_data[element]['trans_w2'] / 3)]
            # statements that follow are for special case created by gy
            # must account for a third node that the W1 and W2 elements are both connected to
            # substation is connected to this third node rather than being directly connected like with auto or gsu
            try:
                nodes[f"between_{W1_side}_{W2_side}"].append(
                    (element, branch_data[element]['type'] + " HV", branch_data[element]['trans_w1'] / 3))
                nodes[f"between_{W1_side}_{W2_side}"].append(
                    (element, branch_data[element]['type'] + " LV", branch_data[element]['trans_w2'] / 3))
            except KeyError:
                nodes[f"between_{W1_side}_{W2_side}"] = [
                    (element, branch_data[element]['type'] + " HV", branch_data[element]['trans_w1'] / 3)]
                nodes[f"between_{W1_side}_{W2_side}"].append(
                    (element, branch_data[element]['type'] + " LV", branch_data[element]['trans_w2'] / 3))
            try:
                if substation_tuple not in nodes[f"between_{W1_side}_{W2_side}"]:
                    nodes[f"between_{W1_side}_{W2_side}"].append(substation_tuple)
                # if statement to pull substation info from W2_side so that it isn't counted twice
                if substation_tuple in nodes[W2_side]:
                    nodes[W2_side].remove(substation_tuple)
            except Exception as e:
                print("Error:", e)
        elif not data["has_trans"]:
            # this process is used for identifying nodes/buses transmission lines are connected to
            # transmission line is accounted for at from and to buses
            try:
                nodes[W1_side].append((element, "line", branch_data[element]['resistance'] / 3))
            except KeyError:
                nodes[W1_side] = [(element, "line", branch_data[element]['resistance'] / 3)]
            try:
                nodes[W2_side].append((element, "line", branch_data[element]['resistance'] / 3))
            except KeyError:
                nodes[W2_side] = [(element, "line", branch_data[element]['resistance'] / 3)]

    # method to account for when gys and autos are in parallel
    auto_and_gy = []
    # empty list to hold auto common information
    for key, list in nodes.items():
        # iterating through nodes dictionary generated in code above
        has_auto = False
        has_gy = False
        # creating flags for identifying parallel gy and auto condition
        for tuple, type, resistance in list:
            try:
                if branch_data[tuple]['type'] == "auto":
                    has_auto = True
                    # first flag set
                    if type == "auto common":
                        auto_and_gy.append((tuple, type, resistance))
                        # appending typical info associated with a node to empty list
                elif branch_data[tuple]['type'] == "gy":
                    has_gy = True
                    # setting second flag
            except Exception:
                pass
        if has_auto and has_gy:
            # executes if both flags set
            for item in auto_and_gy:
                tup, typ, res = item
                if item not in nodes[f"between_{tup[0]}_{tup[1]}"]:
                    # associating auto common with special case node
                    nodes[f"between_{tup[0]}_{tup[1]}"].append(item)
        else:
            auto_and_gy = []
            # emptying list if both flags aren't set
    return nodes


def nodal_indexer(nodes: dict) -> dict:
    """ This is a simple function that iterates through the node dictionary and associates each key in the nodes
                dictionary with a value that can be used for indexing when creating matrices later in process.
                @param: nodes: dictionary containing bus numbers as keys. Values associated with keys are the information
                for the transformers, transmission lines, and/or substation connected to the bus. All resistances corrected
                from 3 phase.
                return: nodal_index: dictionary with indexable values associated with keys from nodes dictionary
            """
    # creating empty dictionary to hold indexing numbers
    nodal_index = {}
    # indexing variable, starts from 0 and is increased by one in for loop
    i = 0
    for key, value in nodes.items():
        nodal_index[key] = i
        i += 1
    return nodal_index


def reverse_map_nodes(nodes: dict, nodal_index: dict, branch_data: dict) -> dict:
    """ This function takes in the nodes dictionary, nodal_index dictionary and branch data dictionaries, and then
                    returns a new dictionary that has reorganized the nodes dictionary to have indexable keys and
                    also contains total resistance values associated with the mapped elements.
                    @param: nodes: dictionary containing bus numbers as keys. Values associated with keys are the
                    information for the transformers, transmission lines, and/or substation connected to the bus.
                    All resistances corrected from 3 phase.
                    @param: nodal_index: dictionary that holds indexable values associated with keys from nodes
                    dictionary
                    @param: branch_data: dictionary that holds grid information pertaining to transmission lines
                    and transformers.
                    return: grouped_dict: dictionary that has reorganized the nodes dictionary to have indexable keys
                    and also contains total resistance values associated with the mapped elements.
                """
    reverse_mapping = {}
    # Iterate through the keys and values of the nodes dictionary
    for key, value_list in nodes.items():
        for value_tuple in value_list:
            # Check if the value_tuple is already in the reverse_mapping
            if value_tuple in reverse_mapping:
                # If it is, append the current key to the list of associated keys
                reverse_mapping[value_tuple].append(key)
            else:
                # If it's not, create a new list with the current key
                reverse_mapping[value_tuple] = [key]

    for name, connections in reverse_mapping.items():
        if name[0] in branch_data:
            if name[1] == 'auto series':
                if name[0][0] != connections[0]:
                    temp = connections[0]
                    connections[0] = connections[1]
                    connections[1] = temp

    for same_name, new_connects in reverse_mapping.items():
        for i in range(len(new_connects)):
            new_connects[i] = nodal_index[new_connects[i]]

    grouped_dict = {}  # new dictionary that was created because original method was deleting items

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
        # values looks like: (tuple, type, resistance)
        # lists that are used for case of parallel elements
        # also identifying if a substation is connected at node
        # this data is necessary for calculating the total resistance at a node
        para = []
        sub_connect = []
        if len(values) > 1:
            # check to see if multiple elements associated with key
            for i in range(len(values)):
                # looping through elements
                if values[i][0] in branch_data:  # check to see if it's a transformer or transmission line
                    para.append(values[i][2])
                    # appending resistance value to parallel items list
                else:
                    sub_connect.append(values[i][2])
                    # substation data not contained in branch_data dictionary
                    # adding substation resistance to sub_connect list
            if len(para) > 1 and len(sub_connect) == 1:
                # checking if transformers in parallel are connect to a substation
                equiv_res = parallel_resistance_calculator(para)
                # using to calculate equivalent resistance of parallel items
                total_res = equiv_res + sub_connect[0]
                grouped_dict[key].append(("total resistance", total_res, equiv_res))
                # appending equivalent resistance for use later in calculating current
            elif len(para) > 1 and len(sub_connect) == 0:
                # case where transformers or transmission lines are in parallel
                total_res = parallel_resistance_calculator(para)
                grouped_dict[key].append(("total resistance", total_res, "parallel elements"))
            elif len(para) == 1 and len(sub_connect) == 1:
                # case where a single transformer (gsu) is connected to a substation
                total_res = para[0] + sub_connect[0]
                grouped_dict[key].append(("total resistance", total_res, "transformer to sub"))
        else:
            # case in which only 1 element is associated with key
            # this case is typical of a substation connected to gy special case node
            total_res = values[0][2]
            grouped_dict[key].append(("total resistance", total_res))

    return grouped_dict


def parallel_resistance_calculator(parallel: list) -> float:
    """ This function calculates the equivalent resistance for resistances that are in parallel. It takes in a list
                    which contains the resistance values, and outputs a float value of the equivalent resistance.
                    @param: parallel: list containing resistance values of elements in parallel
                    return: r_equiv: calculated float value of the equivalent resistance
                """
    inverse_res = 0
    # calculation of equivalent resistance formula:
    # r_equiv^-1 = (r_1^-1 + r_2^-1 +...+ r_n^-1)
    for i in range(len(parallel)):
        # looping through values in list
        inverse_res += (1 / parallel[i])
        # summing resistances^-1

    r_equiv = 1 / inverse_res

    return r_equiv


def node_voltage_calculator(cond_mat: np.ndarray, ic_mat: np.ndarray) -> np.ndarray:
    """ This function calculates the nodal voltage matrix. It uses the conduction and current vector matrices to calculate
                       this values
                       @param: cond_mat: numpy array that contains the inverted conductance matrix data
                       @param: ic_mat: numpy array that contains the current vector data
                       return: node_volt_mat: a numpy array that contains the bus/nodal voltages
                   """

    node_volt_mat = np.matmul(cond_mat, ic_mat)
    # multiplying inverted conductance matrix with current vector

    # returning array
    return node_volt_mat


def ic_mat_generator_gic_df(nodal_index: dict, EC_df: pd.DataFrame,
                            reverse_mapping: dict, cond_mat: np.ndarray, branch_data: dict) -> pd.DataFrame:
    """ This method takes in the indexing information, the equivalent current time series data, the mapped elements of
                    the grid, the conductance matrix, and the branch data in order to generate the current vector matrix.
                    This matrix is then used as an input to the node_voltage_calculator function within this function,
                    which is subsequently used as an input for the gic_value_calculator function within this function.
                    @param: nodal_index: dictionary that contains information on index of nodes. Determines size of array
                    @param: EC_df: Pandas DataFrame that holds the time series equivalent current for each transmission line
                    @param: reverse_mapping: dictionary that holds data regarding nodes which each grid element is connected to
                    @param: cond_mat: numpy array that holds the conductance matrix data. This matrix is static
                    @param: branch_data: dictionary that holds grid information pertaining to transmission lines
                    and transformers.
                    return: gic_df: a Pandas DataFrame that holds gic values for lines and transformers.
                """

    branch_data_calc = branch_data
    # creating a copy of the branch_data dictionary to avoid alterations to original
    # used as an input to gic_value_calculator function called within this function
    gic_data = {}
    # empty dictionary to hold gic data, will be converted to a pandas DataFrame
    ic_matrix = np.zeros((len(nodal_index), 1))
    # creating an array of zeros of with size n x 1 where n is the number of nodes in given system
    tl_nodes = {}
    # empty dictionary to hold transmission line dictionary held in reverse_mapping dictionary
    for keys, values in reverse_mapping.items():
        # for loop to copy data from reverse mapping into tl_nodes
        for i in range(len(values)):
            if values[i][1] == "line":
                # confirming that a line was found
                try:
                    tl_nodes[keys].append((values[i], None))
                    # None is included for formatting when including the current value in next for loop
                except KeyError:
                    tl_nodes[keys] = [(values[i], None)]

    for index, row in EC_df.iterrows():
        # looping through equivalent current DataFrame
        for key, value_list in tl_nodes.items():
            updated_value_list = []
            # a blank list to hold the updated information
            # using this to avoid overwrites
            for item in value_list:
                toop = item[0][0]
                if toop in row.index:
                    column_value = row[toop]
                    # grabbing the current value
                    updated_item = (item[0], column_value)
                    # variable that holds line data and current on line for that time
                    updated_value_list.append(updated_item)
                else:
                    updated_value_list.append(item)
            tl_nodes[key] = updated_value_list
            # updating tl_nodes

        for key, value in tl_nodes.items():
            # loop must be done within looping through DataFrame
            indexer = list(key)
            for i in range(len(value)):
                current = value[i][1]
                # from bus gets -, to bus gets +
                ic_matrix[indexer[0]] -= current
                ic_matrix[indexer[1]] += current
        bus_voltage = node_voltage_calculator(cond_mat, ic_matrix)
        # calculating bus voltages
        ic_matrix = np.zeros((len(nodal_index), 1))
        # clearing ic_matrix
        gics = gic_value_calculator(reverse_mapping, tl_nodes, bus_voltage, branch_data_calc)
        # calculating gics

        # logic below is used to fill in data in gic_data dictionary which is then converted to a DataFrame
        if len(gic_data) == 0:
            gic_data['time'] = [EC_df.loc[index][0]]
            for marker, info in gics.items():
                gic_data[marker] = [info]
        elif len(gic_data) > 0:
            gic_data['time'].append(EC_df.loc[index][0])
            for marker, info in gics.items():
                gic_data[marker].append(info)
        ic_matrix = np.zeros((len(nodal_index), 1))
        # clearing ic_matrix again
    gic_df = pd.DataFrame(gic_data)
    return gic_df


def cond_mat_generator(nodal_index: dict, reverse_map: dict) -> np.ndarray:
    """ This function generates the conductance matrix for the given grid, then inverts it for use in later calculation.
                        It takes in the nodal index information to generate a nxn matrix where n is the number of nodes
                        in the system. The reverse_map dictionary contains the resistance/conductance data and
                        information regarding where each element in the grid is connected.
                          @param: nodal_index: dictionary that holds data regarding the number of nodes in grid
                          @param: reverse_map: dictionary that holds data regarding where each grid element is connected
                          and total resistance of elements that share the same key.
                          return: inv_cond_mat: a numpy array of the inverted conductance matrix for a grid. This matrix
                          is static.
                      """

    conductance_matrix = np.zeros((len(nodal_index), len(nodal_index)))
    # creating an nxn matrix filled with zeros

    for key, values in reverse_map.items():
        indexer = list(key)
        if len(values) > 1:
            # this if statement should always be true, might be able to remove
            conductance = 0
            # variable to hold conductance data
            for i in range(len(values)):
                if values[i][0] == "total resistance":
                    conductance = 1 / values[i][1]
                    # conductance is total_resistance^-1
            if len(indexer) == 1:  # For keys with a single index, e.g., (1,)
                conductance_matrix[indexer[0]][indexer[0]] += conductance
                # adding conductance to matrix at correct index
            elif len(indexer) == 2:  # For keys with two indices, e.g., (1, 2)
                # adding conductance
                conductance_matrix[indexer[0]][indexer[0]] += conductance
                conductance_matrix[indexer[1]][indexer[1]] += conductance
                # adding negative of conductance to diagonal elements
                conductance_matrix[indexer[0]][indexer[1]] -= conductance
                conductance_matrix[indexer[1]][indexer[0]] -= conductance

    inv_cond_mat = np.linalg.inv(conductance_matrix)
    return inv_cond_mat


def gic_value_calculator(reverse_map: dict, tl_nodes: dict, nodal_volt_mat: np.ndarray, branch_data: dict) -> dict:
    """ This function calculates the gics in transmission lines and transformer windings. It takes the mapped nodes from
                            the reverse_map dictionary and the tl_nodes dictionaries to grab resistance/conductance values.
                            The branch_data dictionary is similarly used for resistance values. The function then uses
                            basic nodal analysis techniques using the nodal voltages in the nodal_volt_mat array and
                            resistance/conductance values to calculate the current in a grid element.
                              @param: reverse_map: dictionary that holds data regarding where each grid element is connected
                              and total resistance of elements that share the same key.
                              @param: tl_nodes: dictionary that holds transmission line data regarding connected nodes
                              and resistance values.
                              @param: nodal_volt_mat: numpy array with nodal voltages. Can be indexed using reverse_map
                              and tl_nodes dictionaries
                              @param: branch_data: dictionary containing data for transformers and transmission lines.
                              Used to get resistance values transformers
                              return: gic_data: dictionary that holds gic info for transmission lines and transformers
                              in the grid. This dictionary is converted to a Pandas DataFrame in
                              the ic_mat_generator_gic_df function when this function is called within it.
                          """
    gic_info = {}
    gic_data = {}
    # two dictionaries being used
    # gic_info holds all the initial data
    # gic_data gets a copy of this, but also the calculated value of effective gics for auto and gy transformers
    for key, values in reverse_map.items():
        gics = 0
        key_list = list(key)
        try:
            if reverse_map[key][0][1] != "line":
                # disregarding keys with transmission lines in this loop
                for j in range(len(values)):
                    # elements connected to 1 bus
                    if values[j][0] == "total resistance" and len(key_list) == 1:
                        if len(values) == 2:
                            # if len(values) == 2, only a sub connected
                            pass
                        elif len(values) == 3:
                            # sub and a transformer
                            gics = float((1 / values[j][1]) * nodal_volt_mat[key_list[0]])
                            # gics are (1 / total res value) * nodal voltage
                            gic_info[str(reverse_map[key][0][0])] = (gics / 3)
                            # creating key of the transformer's tuple
                        elif len(values) > 3:
                            # case where multiple transformers and sub connected
                            # could be gsu or auto common
                            divided_voltage = float((values[j][2] / values[j][1]) * nodal_volt_mat[key_list[0]])
                            # finding amount of voltage loss over transformers
                            for k in range(len(values)):
                                try:
                                    if values[k][0] in branch_data:
                                        # this check also weeds out substations
                                        if branch_data[values[k][0]]['type'] == "gsu":
                                            if branch_data[values[k][0]]['trans_w1'] is not None:
                                                gics = (1 / branch_data[values[k][0]]['trans_w1']) * divided_voltage
                                                gic_info[str(reverse_map[key][k][0])] = gics
                                            elif branch_data[values[k][0]]['trans_w2'] is not None:
                                                gics = (1 / branch_data[values[k][0]]['trans_w2']) * divided_voltage
                                                gic_info[str(reverse_map[key][k][0])] = gics
                                        elif branch_data[values[k][0]]['type'] == "auto":
                                            gics = (1 / branch_data[values[k][0]]['trans_w2']) * divided_voltage
                                            try:
                                                gic_info[str(reverse_map[key][k][0])].append(gics)
                                            except KeyError:
                                                gic_info[str(reverse_map[key][k][0])] = [gics]
                                except KeyError:
                                    pass
                    # elements connected to 2 buses
                    elif values[j][0] == "total resistance" and len(key_list) == 2:
                        nodal_dif = float(nodal_volt_mat[key_list[0]] - nodal_volt_mat[key_list[1]])
                        for z in range(len(values)):
                            if reverse_map[key][z][1] == "auto series":
                                gics = (1 / branch_data[values[z][0]]['trans_w1']) * nodal_dif
                                # adjusting for effective gic
                                gics = gics * (branch_data[values[z][0]]['trans_w1'] / (
                                        branch_data[values[z][0]]['trans_w1'] + branch_data[values[z][0]][
                                    'trans_w2']))
                                try:
                                    gic_info[str(reverse_map[key][z][0])].append(gics)
                                except KeyError:
                                    gic_info[str(reverse_map[key][z][0])] = [gics]
                            elif reverse_map[key][z][1] == "auto common":
                                gics = (1 / branch_data[values[z][0]]['trans_w2']) * nodal_dif
                                # adjustment for effective gics
                                gics = gics * (branch_data[values[z][0]]['trans_w2'] / (
                                        branch_data[values[z][0]]['trans_w1'] + branch_data[values[z][0]]['trans_w2']))
                                try:
                                    gic_info[str(reverse_map[key][z][0])].append(gics)
                                except KeyError:
                                    gic_info[str(reverse_map[key][z][0])] = [gics]
                            elif reverse_map[key][z][1] == "gy LV":
                                gics = (1 / branch_data[values[z][0]]['trans_w2']) * nodal_dif
                                # adjustment for effective gics
                                gics = gics * (branch_data[values[z][0]]['trans_w2'] / branch_data[values[z][0]][
                                    'trans_w1'])
                                try:
                                    gic_info[str(reverse_map[key][z][0])].append(gics)
                                except KeyError:
                                    gic_info[str(reverse_map[key][z][0])] = [gics]
                            elif reverse_map[key][z][1] == "gy HV":
                                gics = (1 / branch_data[values[z][0]]['trans_w1']) * nodal_dif
                                # no adjustment for effective gic needed for HV
                                try:
                                    gic_info[str(reverse_map[key][z][0])].append(gics)
                                except KeyError:
                                    gic_info[str(reverse_map[key][z][0])] = [gics]
        except KeyError:
            pass

        for keys, value in tl_nodes.items():
            gics = 0
            key_list2 = list(keys)
            try:
                if len(value) == 1:
                    # print(float((value[0][1])))
                    # print(float(1 / (value[0][0][2])))
                    # print(nodal_volt_mat[key_list2[0]])
                    # print(nodal_volt_mat[key_list2[1]])
                    # print(float((nodal_volt_mat[key_list2[0]] - nodal_volt_mat[key_list2[1]])))
                    # gics = float((value[0][1])) + float(
                    #     ((value[0][0][2]) * (nodal_volt_mat[key_list2[0]] - nodal_volt_mat[key_list2[1]])))
                    base_current = float((value[0][1]))
                    admittance = float(1 / (value[0][0][2]))
                    volt_dif = float(nodal_volt_mat[key_list2[0]] - nodal_volt_mat[key_list2[1]])
                    gics = base_current + (admittance * volt_dif)
                    # gics = equivalent current for line + (voltage difference * resistance^-1)
                    gic_info[value[0][0][0]] = (gics / 3)
                    # adjusted for phase
                elif len(value) > 1:
                    for p in range(len(value)):
                        base_current = float((value[p][1]))
                        admittance = float(1 / (value[p][0][2]))
                        volt_dif = float(nodal_volt_mat[key_list2[0]] - nodal_volt_mat[key_list2[1]])
                        gics = base_current + (admittance * volt_dif)
                        gic_info[value[p][0][0]] = (gics / 3)
            except IndexError:
                pass

    for name, info in gic_info.items():
        # copying over info from gic_info to gic_data
        if isinstance(info, list):
            # if there's a list, must calculate effective gic
            # this is just an addition of the values
            # quantity already altered in prior step to be ready for simple addition
            gic_data[name] = sum(info)
        else:
            gic_data[name] = info

    return gic_data


def gic_computation(substation_data: dict, bus_data: dict, branch_data: dict, E_data_df: pd.DataFrame) -> pd.DataFrame:
    """ This method takes in the grid data dictionaries and the E-field DataFrame, and outputs a Pandas DataFrame
                the calculated GICs in the transmission lines and transformers for the inputted grid. This function
                is essentially a singular function that executes all the previously defined functions in the order
                necessary to ultimately calculate GIC values. Singular function is able to be called easier by
                application core.
                @param: substation_data: dictionary that contains latitudes and longitudes of substations in grid
                @param: bus_data: dictionary that correlates bus numbers with substation numbers
                @param: branch_data: dictionary that holds grid information pertaining to transmission lines
                and transformers.
                @param: E_data_df: Pandas DataFrame that holds time series E-field data
                return: gic_df: Pandas DataFrame that holds time series GIC values for lines and transformers
            """
    line_list = list_line_data(substation_data, bus_data, branch_data)
    line_length = generate_line_length(line_list)
    IV_df = input_voltage_calculation(line_length, E_data_df)
    EC_df = equivalent_current_calc(line_length, IV_df)
    nodes = generate_nodes_and_network(branch_data, bus_data, substation_data)
    nodal_index = nodal_indexer(nodes)
    reverse_mapping = reverse_map_nodes(nodes, nodal_index, branch_data)
    cond_mat = cond_mat_generator(nodal_index, reverse_mapping)
    gic_df = ic_mat_generator_gic_df(nodal_index, EC_df, reverse_mapping, cond_mat, branch_data)

    return gic_df


if __name__ == '__main__':

    pd.set_option('display.max_columns', None)

    # line_list = list_line_data(substation_data_20, bus_data_20, branch_data_20)

    # line_length_20 = generate_line_length(line_list)

    # IV_df_20 = input_voltage_calculation(line_length_20, E_data_df_20N)

    # EC_df_20 = equivalent_current_calc(line_length_20, IV_df_20)

    # nodes_20 = generate_nodes_and_network(branch_data_20, bus_data_20, substation_data_20)

    # nodal_index = nodal_indexer(nodes_20)

    # reverse_mapping = reverse_map_nodes(nodes_20, nodal_index, branch_data_20)

    # cond_mat_20 = cond_mat_generator(nodal_index, reverse_mapping)

    # bus to index [2, 3, 17, 15, 4, 16, 5, 6, 11, 12, 20, 4/3, 5/20]
    # north [-12.39, 20.04, 25.05, 30.09, 20.33, 29.37, -29.01, -7.16, 60.57, 7.11, -29.04, 19.98, -27.908]
    # east [-190.04, -125.10, -41.01, -24.39, -125.97, -22.99, -7.26, 44.32, -40.47, 15.67, -6.13, -124.58, -6.546]


    # get empty dataframe
    # data = make3DPandas.get3D(-88, -80, 32, 35)
    #
    # # example of how to access the dataframe
    # # time = 0
    # # longitude = 89
    # # latitude = 45
    # # # NOTE: pandas keys must be a string so use str()
    # # data.loc[(str(time), str(longitude), str(latitude)), 'Ex'] = 1
    #
    # # This is an example of how to populate the dataframe or traverse it
    # for i in data.iterrows():
    #     # i is a pandas object with some metadata. It looks something like name: (10, 89, 45), dtype:float64
    #     # we just want the tuple, so we must use i[0] in .loc instead of just i
    #     data.loc[i[0], "Ex"] = 0
    #     data.loc[i[0], "Ey"] = 1
    #
    #
    # gic_df_20N = gic_computation(substation_data_20, bus_data_20, branch_data_20, data)

    # print(gic_df_20N)