
import pandas as pd
from dateutil import parser
import numpy as np
import matplotlib.pyplot as plt
# file = open('bou20230316pmin.min', 'r')
# 
# f = file.readlines()
# with open("intermagnetBOU20230316.csv", 'w') as csv:
#     beginWrite = False
#     for line in f:
#         line = line.split()
#         line[0] = line[0] + ' ' + line[1]
#         line = line[:1] + line[2:]
#         
#         if line[0] == '# www.intermagnet.org':
#             beginWrite = True
#         if beginWrite:
#             for element in line:
#                 csv.write(element)
#                 csv.write(',')
#             csv.write('\n')
# 


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

intermagnet = pd.read_csv("intermagnetBOU20230316.csv")
synthetic_file = "Predicted_B_Field_20230316.csv"
synthetic = pd.read_csv(synthetic_file)
print(synthetic)
end_time = "2023-03-14 23:59:59"

intermagnet.drop('Unnamed: 6',axis=1, inplace=True)
intermagnet.drop('DOY',axis=1, inplace=True)
intermagnet.drop('BOUF',axis=1, inplace=True)

end_time = parser.parse(end_time).timestamp()

#synthetic = synthetic[synthetic['time'] < end_time]
synthetic = synthetic[~(synthetic == 0).any(axis=1)]
print(synthetic)

for t, df in intermagnet.iterrows():
    intermagnet['DATE TIME'].iloc[intermagnet.index[t]] = parser.parse(df['DATE TIME']).timestamp()
print(intermagnet)

time_intermagnet = intermagnet['DATE TIME'].to_numpy(copy=True, dtype=float)

time_synthetic = synthetic['time'].to_numpy(copy=True, dtype=float)

if time_intermagnet.size > time_synthetic.size:
    length = time_synthetic.size

else:
    length = time_intermagnet.size


vector_synthetic_xi = synthetic['Bx'].to_numpy(copy=True, dtype=float)
vector_synthetic_yi = synthetic['By'].to_numpy(copy=True, dtype=float)
vector_synthetic_zi = synthetic['Bz'].to_numpy(copy=True, dtype=float)

vector_synthetic_x = np.zeros(length)
vector_synthetic_y = np.zeros(length)
vector_synthetic_z = np.zeros(length)

for i in range(length):
    for j in range(length):
        if (time_synthetic[j] > (time_intermagnet[i] - 30)) and (time_synthetic[j] < (time_intermagnet[i] + 30)):
            vector_synthetic_x[i] = vector_synthetic_xi[j]
            vector_synthetic_y[i] = vector_synthetic_yi[j]
            vector_synthetic_z[i] = vector_synthetic_zi[j]
            
            break
        
vector_intermagnet_x = intermagnet['BOUX'].to_numpy(copy=True, dtype=float)
vector_intermagnet_y = intermagnet['BOUY'].to_numpy(copy=True, dtype=float)
vector_intermagnet_z = intermagnet['BOUZ'].to_numpy(copy=True, dtype=float)

jx = 0
jy = 0
jz = 0
time_x = time_intermagnet
time_y = time_intermagnet
time_z = time_intermagnet
for i in range(length):
    if vector_synthetic_x[i - jx] == 0:
        vector_synthetic_x = np.delete(vector_synthetic_x, i - jx, None)
        vector_intermagnet_x = np.delete(vector_intermagnet_x, i - jx, None)
        time_x = np.delete(time_x, i - jx, None)
        jx += 1
    if vector_synthetic_y[i - jy] == 0:
        vector_synthetic_y = np.delete(vector_synthetic_y, i - jy, None)
        vector_intermagnet_y = np.delete(vector_intermagnet_y, i - jy, None)
        time_y = np.delete(time_y, i - jy, None)
        jy += 1
    if vector_synthetic_z[i - jz] == 0:
        vector_synthetic_z = np.delete(vector_synthetic_z, i - jz, None)
        vector_intermagnet_z = np.delete(vector_intermagnet_z, i - jz, None)
        time_z = np.delete(time_z, i - jz, None)
        jz += 1


print(np.min(vector_intermagnet_x))
print(np.max(vector_intermagnet_x))
print(np.max(vector_intermagnet_x) - np.min(vector_intermagnet_x))

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
# plt.scatter(vector_intermagnet_x, vector_synthetic_x)
plt.show()

plt.plot(time_y, vector_intermagnet_y, label= 'intermagnet y')
plt.plot(time_y, vector_synthetic_y, label= 'synthetic y')
plt.legend()
# plt.scatter(vector_intermagnet_x, vector_synthetic_x)
plt.show()

plt.plot(time_z, vector_intermagnet_z, label= 'intermagnet z')
plt.plot(time_z, vector_synthetic_z, label= 'synthetic z')
plt.legend()
# plt.scatter(vector_intermagnet_x, vector_synthetic_x)
plt.show()