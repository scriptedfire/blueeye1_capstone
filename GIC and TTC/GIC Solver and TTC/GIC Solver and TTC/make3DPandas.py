import numpy as np
import pandas as pd


def get3D(min_longitude, max_longitude, min_latitude, max_latitude):
    """ This method returns a pandas dataframe indexed by time, longitude, and latitude"""
    longitude_vector = np.array([min_longitude, max_longitude])
    latitude_vector = np.array([min_latitude, max_latitude])

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
    data_dict = {"Ex": np.zeros(length), "Ey": np.zeros(length)}
    data = pd.DataFrame(data_dict, index=index)
    return data


# if __name__ == '__main__': is a way of specifying code that only runs if the file itself is run.
# This means that you can import this file without this block of code executing.
if __name__ == '__main__':

    # get empty dataframe
    data = get3D(89, 99, 45, 55)

    # example of how to access the dataframe
    time = 0
    longitude = 89
    latitude = 45
    # NOTE: pandas keys must be a string so use str()
    data.loc[(str(time), str(longitude), str(latitude)), 'Ex'] = 3.2

    # This is an example of how to populate the dataframe or traverse it
    for i in data.iterrows():
        # i is a pandas object with some metadata. It looks something like name: (10, 89, 45), dtype:float64
        # we just want the tuple so we must use i[0] in .loc instead of just i
        data.loc[i[0], "Ex"] = 3.2
        data.loc[i[0], "Ey"] = 1.2
    print(data)