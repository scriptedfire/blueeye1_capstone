import numpy as np
import pandas as pd
from dateutil import parser

def get3D(min_longitude, max_longitude, min_latitude, max_latitude, time_array):
    """ This method returns a pandas dataframe indexed by time, longitude, and latitude"""
    longitude_vector = np.array([max_longitude, min_longitude])
    latitude_vector = np.array([max_latitude, min_latitude]) 

    # edit this array to customize time series
    #time_array = np.arange(0, 100, 10)
    
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
    data_dict = {"Bx":np.zeros(length), "By": np.zeros(length), "Bz": np.zeros(length)}
    data = pd.DataFrame(data_dict, index=index)
    return data

def process_intermagnet(file_name: str):
    mag_data = pd.read_csv(file_name)
    print(mag_data)
    time_array = np.zeros(mag_data.index.size)
    hour = 0
    insert_hour = ""
    insert_minute = ""
    for i in range(mag_data.index.size):
        insert_minute = f"{(i+1)%60}"
        if (i + 1) % 60 == 0:
            hour += 1
            insert_hour = f"{hour}"
        if hour < 10:
            insert_hour = f"0{hour}"
        if ((i+1)%60) < 10:
            insert_minute = f"0{(i+1)%60}"
        time_array[i] = str(parser.parse(f"2023-10-30 {insert_hour}:{insert_minute}:00 UTC").timestamp())


    # get empty dataframe
    data = get3D(21, 32, 59, 66, time_array)
    print(data)
    
    
    # This is an example of how to populate the dataframe or traverse it
    primary_count = 1
    count = 0
    for i in data.iterrows():
        # i is a panas object with some metadata. It looks something like name: (10, 89, 45), dtype:float64
        # we just want the tuple so we must use i[0] in .loc instead of just i

        data.loc[i[0], "Bx"] = float(mag_data["Bx"][count])
        data.loc[i[0], "By"] = float(mag_data["By"][count])
        data.loc[i[0], "Bz"] = float(mag_data["Bz"][count])
        
        if primary_count % 4 == 0:
            count += 1
        primary_count += 1
    return data