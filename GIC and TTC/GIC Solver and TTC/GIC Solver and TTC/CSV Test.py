import pandas as pd
import numpy as np
sub_file_path = "/Users/madelineburrows/Desktop/ECEN 403/Substation Data.csv"
sub_df = pd.read_csv(sub_file_path)

def read_csv_to_numpy(filename):
    # read the CSV file using Pandas
    df = pd.read_csv(filename)

    # convert the DataFrame to a NumPy array
    np_array = df.to_numpy()

    # return the NumPy array
    return np_array

line_array = read_csv_to_numpy("/Users/madelineburrows/Desktop/ECEN 403/Line Data.csv")
sub_array = sub_df.to_numpy()


long_from = 0
long_to = 0
lat_from = 0
lat_to = 0
data = np.zeros((np.shape(line_array)[0],5))
for i in range(np.shape(line_array)[0]):
    for j in range(np.shape(sub_array)[0]):
        if sub_array[j][4] == line_array[i][1] or sub_array[j][5] == line_array[i][1]:
            long_from = sub_array[j][2]
            lat_from = sub_array[j][1]
        if sub_array[j][4] == line_array[i][2] or sub_array[j][5] == line_array[i][2]:
            long_to = sub_array[j][2]
            lat_to = sub_array[j][1]
    data[i][0] = line_array[i][0]
    data[i][1] = long_from
    data[i][2] = lat_from
    data[i][3] = long_to
    data[i][4] = lat_to

print(data)








