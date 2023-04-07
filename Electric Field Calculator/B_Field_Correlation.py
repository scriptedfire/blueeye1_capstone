
import pandas as pd
from dateutil import parser
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import MagneticFieldPredictor
import time


start = time.time()

def storm_data_dst_merge(data:pd.DataFrame, dst:pd.DataFrame) -> pd.DataFrame:
    """ This function merges the storm data with the dst. 
        This is complicated by the fact that dst data is much lower in granularity
        @param: data: storm data
        @param: dst: dataframe of dst indecies with time stamps
        return: merged dataframe
    """
   
    j = 0
    # loop through the dst data frame and delete the times that are outside of the storm time
    data = data.loc[data['time'] > dst['time'].iloc[0]]
    data = data.loc[data['time'] < dst['time'].iloc[-1]]
    for i, row in data.iterrows():
        
        if row['time'] < dst['time'].iloc[0]:
            data.drop(data.index[i - j], inplace=True)
            j += 1
        elif row['time'] > dst['time'].iloc[-1]: 
            
            dst.drop(dst.index[i - j], inplace=True)
            j += 1
    data.reset_index(inplace=True)
    dst_array = np.zeros(data.index.size)
    time_slot = 0
    
    # FIXME: see if this loop can be avoided with a conditional slice
    for i, row in data.iterrows():
        
        if row['time'] > dst['time'].iloc[time_slot]: # parser.parse(row['time']).timestamp()
                        time_slot += 1
        # if the storm data extends past known dst data, use the most recent
        if time_slot >= dst["dst"].index.size:
            time_slot = dst["dst"].index.size - 1
        dst_array[i] = dst['dst'].iloc[time_slot]

    data['dst'] = dst_array
    return data


def mean(array):
    N = array.size
    avg = 0
    for i in range(N):
        avg += array[i]
    avg = avg / N
    return avg

def var(array: np.array):
    N = array.size

    # compute average
    avg = 0
    for i in range(N):
        avg += array[i]
    avg = avg / N
    var = 0
    for i in range(N):
        var += (array[i] - avg) ** 2
    var = var / N
    return var

intermagnet = pd.read_csv("intermagnetBOU20150622-25.csv")
synthetic_file = "Predicted_B_Field_OMNI_2015.csv"
#synthetic = pd.read_csv(synthetic_file)
data = pd.read_csv("OMNI_data_2015_clean_with_dst.csv")

data.reset_index(inplace=True)
print(data)
synthetic = MagneticFieldPredictor.magnetic_field_predictor(data, -105, -104, 40, 41, 0.5)
synthetic.to_csv(synthetic_file)
print(synthetic)
print("calculation time = ", time.time() - start)

end_time = "2023-03-16 23:59:59 UTC"

# data.drop('Unnamed: 0',axis=1, inplace=True)
# print(data)
intermagnet.reset_index(inplace=True)
intermagnet.drop('DOY',axis=1, inplace=True)
intermagnet.drop('BOUG',axis=1, inplace=True)
intermagnet.drop('Unnamed: 6',axis=1, inplace=True)
print(intermagnet)

end_time = parser.parse(end_time).timestamp()

#synthetic = synthetic[synthetic['time'] < end_time]
synthetic = synthetic[~(synthetic == 0).any(axis=1)]
synthetic.reset_index(inplace=True)
print(synthetic)


for t, df in intermagnet.iterrows():
    intermagnet['DATE TIME'].iloc[intermagnet.index[t]] = parser.parse(str(df['DATE TIME']) + 'UTC').timestamp()

intermagnet.drop('index', axis=1, inplace=True)
print(intermagnet)

time_intermagnet = intermagnet['DATE TIME'].to_numpy(copy=True, dtype=float)

time_synthetic = synthetic['time'].to_numpy(copy=True, dtype=float)

if time_intermagnet.size > time_synthetic.size:
    length = time_synthetic.size

else:
    length = time_intermagnet.size


vector_synthetic_xi = [] # np.zeros(time_synthetic.size)# synthetic['Bx'].to_numpy(copy=True, dtype=float)
vector_synthetic_yi = [] # np.zeros(time_synthetic.size)# ssynthetic['By'].to_numpy(copy=True, dtype=float)
vector_synthetic_zi = [] # np.zeros(time_synthetic.size)# ssynthetic['Bz'].to_numpy(copy=True, dtype=float)
time_synthetic = [] # np.zeros(time_synthetic.size)
vector_synthetic_x = np.zeros(length)
vector_synthetic_y = np.zeros(length)
vector_synthetic_z = np.zeros(length)

count = 0

for i, df in synthetic.iterrows():
     if float(df['longitude']) == -104.5 and float(df['latitude']) == 40.5:
          vector_synthetic_xi.append(float(df['Bx']))
          vector_synthetic_yi.append(float(df['By']))
          vector_synthetic_zi.append(float(df['Bz']))
          time_synthetic.append(float(df['time']))
          count += 1

time_synthetic = np.array(time_synthetic)

if time_intermagnet.size > time_synthetic.size:
    length = time_synthetic.size

else:
    length = time_intermagnet.size


#print(vector_synthetic_xi)
#print(time_intermagnet)

for i in range(length):
    for j in range(length):
        if (time_synthetic[j] > (time_intermagnet[i] - 30)) and (time_synthetic[j] < (time_intermagnet[i] + 30)):
            vector_synthetic_x[i] = vector_synthetic_xi[j]
            vector_synthetic_y[i] = vector_synthetic_yi[j]
            vector_synthetic_z[i] = vector_synthetic_zi[j]
            
            
            break

#print(time_synthetic)
# print(vector_synthetic_x)

vector_intermagnet_x = intermagnet['BOUX'].to_numpy(copy=True, dtype=float)
vector_intermagnet_y = intermagnet['BOUY'].to_numpy(copy=True, dtype=float)
vector_intermagnet_z = intermagnet['BOUZ'].to_numpy(copy=True, dtype=float)

# print(vector_intermagnet_x)

jx = 0
jy = 0
jz = 0
time_x = time_intermagnet
time_y = time_intermagnet
time_z = time_intermagnet



for i in range(length):
    if vector_synthetic_x[i - jx] == 0.0:
        vector_synthetic_x = np.delete(vector_synthetic_x, i - jx, None)
        vector_intermagnet_x = np.delete(vector_intermagnet_x, i - jx, None)
        time_x = np.delete(time_x, i - jx, None)
        jx += 1
    if vector_synthetic_y[i - jy] == 0.0:
        vector_synthetic_y = np.delete(vector_synthetic_y, i - jy, None)
        vector_intermagnet_y = np.delete(vector_intermagnet_y, i - jy, None)
        time_y = np.delete(time_y, i - jy, None)
        jy += 1
    if vector_synthetic_z[i - jz] == 0.0:
        vector_synthetic_z = np.delete(vector_synthetic_z, i - jz, None)
        vector_intermagnet_z = np.delete(vector_intermagnet_z, i - jz, None)
        time_z = np.delete(time_z, i - jz, None)
        jz += 1

# repeat to eliminate trailing zeros

jx = 0
jy = 0
jz = 0


for i in range(time_x.size):
    if vector_synthetic_x[i - jx] == 0.0:
        vector_synthetic_x = np.delete(vector_synthetic_x, i - jx, None)
        vector_intermagnet_x = np.delete(vector_intermagnet_x, i - jx, None)
        time_x = np.delete(time_x, i - jx, None)
        jx += 1
    if vector_synthetic_y[i - jy] == 0.0:
        vector_synthetic_y = np.delete(vector_synthetic_y, i - jy, None)
        vector_intermagnet_y = np.delete(vector_intermagnet_y, i - jy, None)
        time_y = np.delete(time_y, i - jy, None)
        jy += 1
    if vector_synthetic_z[i - jz] == 0.0:
        vector_synthetic_z = np.delete(vector_synthetic_z, i - jz, None)
        vector_intermagnet_z = np.delete(vector_intermagnet_z, i - jz, None)
        time_z = np.delete(time_z, i - jz, None)
        jz += 1




var_intermagnet_x =  np.var(vector_intermagnet_x)

var_intermagnet_y = np.var(vector_intermagnet_y)

var_intermagnet_z = np.var(vector_intermagnet_z)

var_synthetic_x = np.var(vector_synthetic_x)

var_synthetic_y = np.var(vector_synthetic_y)

var_synthetic_z = np.var(vector_synthetic_z)




cov_x = np.cov(vector_intermagnet_x, vector_synthetic_x)[0][1]

cov_y = np.cov(vector_intermagnet_y, vector_synthetic_y)[0][1]

cov_z = np.cov(vector_intermagnet_z, vector_synthetic_z)[0][1]

print(var_intermagnet_x, var_synthetic_x, cov_x)

rho_x = cov_x / np.sqrt(var_intermagnet_x * var_synthetic_x)

print('rho_x = ', rho_x)

print(var_intermagnet_y, var_synthetic_y, cov_y)

rho_y = cov_y / np.sqrt(var_intermagnet_y * var_synthetic_y)

print('rho_y = ', rho_y)


print(var_intermagnet_z, var_synthetic_z, cov_z)

rho_z = cov_z / np.sqrt(var_intermagnet_z * var_synthetic_z)

avg_intermagnet_x = mean(vector_intermagnet_x)
avg_synthetic_x = mean(vector_synthetic_x)

for i in range(vector_intermagnet_x.size):
    vector_synthetic_x[i] -= avg_synthetic_x
    vector_intermagnet_x[i] -= avg_intermagnet_x

avg_intermagnet_y = mean(vector_intermagnet_y)
avg_synthetic_y = mean(vector_synthetic_y)

for i in range(vector_intermagnet_y.size):
    vector_synthetic_y[i] -= avg_synthetic_y
    vector_intermagnet_y[i] -= avg_intermagnet_y

avg_intermagnet_z = mean(vector_intermagnet_z)
avg_synthetic_z = mean(vector_synthetic_z)

for i in range(vector_intermagnet_z.size):
    vector_synthetic_z[i] -= avg_synthetic_z
    vector_intermagnet_z[i] -= avg_intermagnet_z

print('rho_z = ', rho_z)


plt.plot(time_x, vector_intermagnet_x, label= 'intermagnet x')
plt.plot(time_x, vector_synthetic_x, label= 'synthetic x')
plt.legend()

plt.show()

plt.plot(time_y, vector_intermagnet_y, label= 'intermagnet y')
plt.plot(time_y, vector_synthetic_y, label= 'synthetic y')
plt.legend()

plt.show()

plt.plot(time_z, vector_intermagnet_z, label= 'intermagnet z')
plt.plot(time_z, vector_synthetic_z, label= 'synthetic z')
plt.legend()

plt.show()