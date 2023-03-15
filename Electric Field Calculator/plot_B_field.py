import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv("data03142023-5.csv")
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
    time[count] = (float(t)  - 1678788960) / 3600
    count += 1
print(time)
print(Bx)
with open("plot_file.csv", 'w') as f:
    f.write('time, Bx,\n')
    for i in range(time.size):
        f.write(str(time[i]))
        f.write(',')
        f.write(str(Bx[i]))
        f.write(',\n')
plt.plot(time[1:], Bx[1:])
plt.show()