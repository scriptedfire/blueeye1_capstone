import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv("20230315.csv")
index_arrays = [data["time"].to_numpy(dtype=str),data["longitude"].to_numpy(),data["latitude"].to_numpy()]

index = pd.MultiIndex.from_arrays(index_arrays, names=['time', 'longitude', 'latitude'])

data.index = index
data.drop(axis=1, labels=['time', 'longitude', 'latitude'], inplace=True)

time = np.zeros(data.groupby(level=0).size().size)
Bx = np.zeros(data.groupby(level=0).size().size)

time2 = np.zeros(int(data.groupby(level=0).size().size / 5)+1)
Bx2 = np.zeros(int(data.groupby(level=0).size().size / 5)+1)
count = 0
count2 = 0
for t, temp_df in data.groupby(level=0):
    if count == 0:
        temp = float(t)
    time[count] = t
    # print(temp_df.loc[(str(time[count]), -105.0, 40.0), 'Bz'])
    Bx[count] = temp_df.loc[(str(time[count]), -105.0, 40.0), 'Bx']
    time[count] = (float(t) - temp) / 3600
    if count % 5 == 0:
        time2[count2] = t

        Bx2[count2] = temp_df.loc[(str(time2[count2]), -105.0, 40.0), 'Bx']
        time2[count2] = (float(t) - temp) / 3600
        count2 += 1
    count += 1

fig, axs = plt.subplots(2)

axs[0].plot(time[1:], Bx[1:])
axs[1].plot(time2[1:], Bx2[1:])
plt.show()