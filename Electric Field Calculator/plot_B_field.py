import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv("data03142023-2.csv")
index_arrays = [data["time"].to_numpy(dtype=str),data["longitude"].to_numpy(),data["latitude"].to_numpy()]
print(index_arrays)
index = pd.MultiIndex.from_arrays(index_arrays, names=['time', 'longitude', 'latitude'])
print(index)
data.index = index
data.drop(axis=1, labels=['time', 'longitude', 'latitude'], inplace=True)
print(data)
print(data.groupby(level=0).size().size)
time = np.zeros(data.groupby(level=0).size().size)
Bx = np.zeros(data.groupby(level=0).size().size)
count = 0
for t, temp_df in data.groupby(level=0):
       
    time[count] = t
    
    Bx[count] = temp_df.loc[(str(time[count]), -104.5, 40.0), 'Bx']
    count += 1
print(time)
print(Bx)

plt.plot(time[1:], Bx[1:])
plt.show()