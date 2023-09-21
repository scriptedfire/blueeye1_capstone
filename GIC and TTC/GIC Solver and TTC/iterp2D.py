import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
import random

def get3D(min_longitude, max_longitude, min_latitude, max_latitude):
    """ This method returns a pandas dataframe indexed by time, longitude, and latitude"""
    longitude_vector = np.array([max_longitude, min_longitude])
    latitude_vector = np.array([max_latitude, min_latitude]) 

    # edit this array to customize time series
    time_array = np.arange(0, 100, 10)
    
    # build time, longitude, and latitude array for pandas multindex.
    length = longitude_vector.size * latitude_vector.size * time_array.size
    
    # build index 
    time_index_array = np.empty([1, length], dtype=object)[0]
    longitude_index_array = np.empty([1, length], dtype=object)[0]
    latitude_index_array = np.empty([1, length], dtype=object)[0]
    time_point = 0
    longitude_point = 0
    
    for i in range(length):
        # time should be same value up until the length of the longitude vector
        # reset longitude vector to 0 every time we reach the end of the latitude vector
        if ((i) % (latitude_vector.size)) == 0:
            if i != 0:
                
                longitude_point += 1
        if ((i) % (longitude_vector.size * latitude_vector.size)) == 0:
            if i != 0:
                time_point += 1
                longitude_point = 0
        
        time_index_array[i] = str(time_array[time_point])
        
        longitude_index_array[i] = str(longitude_vector[longitude_point])
        # repeatedly copy the longitude and latitude points to the index array
        latitude_index_array[i] = str(latitude_vector[i % latitude_vector.size])
    

    index = [time_index_array, longitude_index_array, latitude_index_array]
    
    index = pd.MultiIndex.from_arrays(index, names=["time", "longitude", "latitude"])
    data_dict = {"Ex":np.zeros(length), "Ey": np.zeros(length)}
    data = pd.DataFrame(data_dict, index=index)
    return data

substation_data = {1 : {"lat" : 33.613499, "long" : -87.373673, "ground_r" : 0.2},
                   2 : {"lat" : 34.310437, "long" : -86.365765, "ground_r" : 0.2},
                   3 : {"lat" : 33.955058, "long" : -84.679354, "ground_r" : 0.2},}

bus_data = {1 : {"sub_num" : 1}, 2 : {"sub_num" : 1},
            3 : {"sub_num" : 2}, 4 : {"sub_num" : 2},
            5 : {"sub_num" : 3}, 6 : {"sub_num" : 3}}

branch_data = {(2, 3, 1) : {"has_trans" : False, "resistance" : 3.525,
                            "type" : None, "trans_w1" : None, "trans_w2" : None},
                (4, 5, 1) : {"has_trans" : False, "resistance" : 4.665,
                                "type" : None, "trans_w1" : None, "trans_w2" : None},
                (1, 2, 1) : {"has_trans" : True, "resistance" : None,
                                "type" : "gsu", "trans_w1" : 0.5, "trans_w2" : None},
                (3, 4, 1) : {"has_trans" : True, "resistance" : None,
                            "type" : "auto", "trans_w1" : 0.2, "trans_w2" : 0.2},
                (5, 6, 1) : {"has_trans" : True, "resistance" : None,
                            "type" : "gsu", "trans_w1" : 0.5, "trans_w2" : None}}

line_dict = {'time': [0, 10, 20, 30], 'Ex':[], 'Ey': []}

def get_line_Efield(df_3D: pd.DataFrame, from_coords: list, to_coords: list) -> dict:

    index_list = df_3D.index
    north_east = (df_3D.index[0][1], df_3D.index[0][2])
    south_east  = (df_3D.index[0][1], df_3D.index[1][2])

    north_west = (df_3D.index[2][1], df_3D.index[2][2])
    south_west = (df_3D.index[2][1], df_3D.index[3][2])

    west_east = (df_3D.index[2][1], df_3D.index[0][1])
    south_north = (df_3D.index[1][2], df_3D.index[0][2])

    print(south_north)
    print(west_east)
    print(north_west, north_east)
    print(south_west, south_east)

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
        north_east_Efield = [df_3D.loc[(time, north_east[0], north_east[1]), 'Ex'], df_3D.loc[(time, north_east[0], north_east[1]), 'Ey']]
        north_west_Efield = [df_3D.loc[(time, north_west[0], north_west[1]), 'Ex'], df_3D.loc[(time, north_west[0], north_west[1]), 'Ey']]

        south_east_Efield = [df_3D.loc[(time, south_east[0], south_east[1]), 'Ex'], df_3D.loc[(time, south_east[0], south_east[1]), 'Ey']]
        south_west_Efield = [df_3D.loc[(time, south_west[0], south_west[1]), 'Ex'], df_3D.loc[(time, south_west[0], south_west[1]), 'Ey']]
        
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

        print(norm_x, norm_y)

        line_dict["Ex"][i] = norm_x    
        line_dict["Ey"][i] = norm_y 

    return line_dict


if __name__ == '__main__':
    data = get3D(10,20,45, 55)
    
    for i in data.iterrows():
        # i is a panas object with some metadata. It looks something like name: (10, 89, 45), dtype:float64
        # we just want the tuple so we must use i[0] in .loc instead of just i
        if (int(i[0][1]) == 20):
            data.loc[i[0], "Ex"] = random.uniform(-10.0, 10.0) # 3 * (int(i[0][0]) + 1)# random.uniform(-10.0, 10.0)
            data.loc[i[0], "Ey"] = random.uniform(-10.0, 10.0) # 4 * (int(i[0][0]) + 1)# random.uniform(-10.0, 10.0)
        else:
            data.loc[i[0], "Ex"] = random.uniform(-10.0, 10.0) # -1 * (int(i[0][0]) + 1)# random.uniform(-10.0, 10.0)
            data.loc[i[0], "Ey"] = random.uniform(-10.0, 10.0) # 1 * (int(i[0][0]) + 1) # random.uniform(-10.0, 10.0)
    print(data)
    line_e_field = get_line_Efield(data, (15, 50), (15, 50)) # get_line_Efield(data, (12, 48), (18, 52))
    print()
    for i in range(10):
        print("Ex, Ey: (", round(data.loc[(str(i*10), '10', '55')][0], 2), round(data.loc[(str(i*10), '10', '55')][1], 2), ")",\
              "_________________________________", "(", round(data.loc[(str(i*10), '20', '55')][0], 2), round(data.loc[(str(i*10), '20', '55')][1], 2), ")")
        print("                      |                                 |")
        print("                      |                                 |")
        print("                      |                                 |")
        print("                      |                                 |")
        print("                      |                                 |")
        print("                      |               *                 |")
        print("                      |              ({} {})         |".format(round(line_e_field['Ex'][i], 1), round(line_e_field['Ey'][i], 1)))
        print("                      |                                 |")
        print("                      |                                 |")
        print("                      |                                 |")
        print("                      |                                 |")
        print("Ex, Ey: (", round(data.loc[(str(i*10), '10', '45')][0], 2), round(data.loc[(str(i*10), '10', '45')][1], 2), ")",\
              "_________________________________", "(", round(data.loc[(str(i*10), '20', '45')][0], 2), round(data.loc[(str(i*10), '20', '45')][1], 2), ")")
        print("\n")

        norm_x_north = (data.loc[(str(i*10), '10', '55')][0] + data.loc[(str(i*10), '20', '55')][0]) # / 2.0
        norm_y_north = (data.loc[(str(i*10), '20', '55')][1] + data.loc[(str(i*10), '10', '55')][1]) # / 2.0

        norm_x_south = (data.loc[(str(i*10), '10', '45')][0] + data.loc[(str(i*10), '20', '45')][0]) # / 2.0
        norm_y_south = (data.loc[(str(i*10), '10', '45')][1] + data.loc[(str(i*10), '20', '45')][1]) # / 2.0

        x = (norm_x_north + norm_x_south) / 4.0

        y = (norm_y_north + norm_y_south) / 4.0

        error = 1e-15
        if abs(line_e_field['Ex'][i] - x) < error and abs(line_e_field['Ey'][i] - y) < error:
            print("Accurate interpolation within {}\n".format(error))
        else:
            print(abs(line_e_field['Ex'][i] - x))
            print(abs(line_e_field['Ey'][i] - y))
            raise RuntimeError