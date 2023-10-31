
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def rho(array1:np.array, array2:np.array):
     
    var1 = np.var(array1)
    var2 = np.var(array2)
    cov = np.cov(array1,array2)[0][1]

    return cov/np.sqrt(var1 * var2)


synthetic = pd.read_csv("B_field_prediction_2015_tsgk_test.csv")

vector_intermagnet_x = synthetic['Bxts'].to_numpy(dtype=float)
vector_intermagnet_y = synthetic['Byts'].to_numpy(dtype=float)
vector_intermagnet_z = synthetic['Bzts'].to_numpy(dtype=float)



vector_synthetic_x = synthetic['Bx_syn'].to_numpy(dtype=float)
vector_synthetic_y = synthetic['By_syn'].to_numpy(dtype=float)
vector_synthetic_z = synthetic['Bz_syn'].to_numpy(dtype=float)

w1_syn = synthetic['w1'].to_numpy(dtype=float)
w1_tsg = synthetic['p5'].to_numpy(dtype=float)

w2_syn = synthetic['w2'].to_numpy(dtype=float)
w2_tsg = synthetic['p6'].to_numpy(dtype=float)

w3_syn = synthetic['w3'].to_numpy(dtype=float)
w3_tsg = synthetic['p7'].to_numpy(dtype=float)

w4_syn = synthetic['w4'].to_numpy(dtype=float)
w4_tsg = synthetic['p8'].to_numpy(dtype=float)

w5_syn = synthetic['w5'].to_numpy(dtype=float)
w5_tsg = synthetic['p9'].to_numpy(dtype=float)

w6_syn = synthetic['w6'].to_numpy(dtype=float)
w6_tsg = synthetic['p10'].to_numpy(dtype=float)


max4_syn = 0
max4_syni = 0
max4_tsg = 0
max4_tsgi = 0
for i in range(w4_syn.size):
    if w4_syn[i] > max4_syn:
        max4_syn = w4_syn[i]
        max4_syni = i
    if w4_tsg[i] > max4_tsg:
        max4_tsg = w4_tsg[i]
        max4_tsgi = i



dst_used = synthetic['dst'].to_numpy(dtype=float)
dst_tsg = synthetic['p2'].to_numpy(dtype=float)

pdyn_syn = synthetic['pressure'].to_numpy(dtype=float)
pdyn_tsg = synthetic['p1'].to_numpy(dtype=float)

bygsm_syn = synthetic['BYGSM'].to_numpy(dtype=float)
bygsm_tsg = synthetic['p3'].to_numpy(dtype=float)

bzgsm_syn = synthetic['BZGSM'].to_numpy(dtype=float)
bzgsm_tsg = synthetic['p4'].to_numpy(dtype=float)

time = synthetic['time'].to_numpy(dtype=float)


var_intermagnet_x =  np.var(vector_intermagnet_x)

var_intermagnet_y = np.var(vector_intermagnet_y)

var_intermagnet_z = np.var(vector_intermagnet_z)

var_synthetic_x = np.var(vector_synthetic_x)

var_synthetic_y = np.var(vector_synthetic_y)

var_synthetic_z = np.var(vector_synthetic_z)

print("Correlation coefficient pdyn: ", rho(pdyn_syn, pdyn_tsg))
print("Correlation coefficient dst: ", rho(dst_used, dst_tsg))
print("Correlation coefficient W1: ", rho(w1_syn, w1_tsg))
print("Correlation coefficient W2: ", rho(w2_syn, w2_tsg))
print("Correlation coefficient W3: ", rho(w3_syn, w3_tsg))
print("Correlation coefficient W4: ", rho(w4_syn, w4_tsg))
print("Correlation coefficient W5: ", rho(w5_syn, w5_tsg))
print("Correlation coefficient W6: ", rho(w6_syn, w6_tsg))

def mean(array):
    N = array.size
    avg = 0
    for i in range(N):
        avg += array[i]
    avg = avg / N
    return avg


cov_x = np.cov(vector_intermagnet_x, vector_synthetic_x)[0][1]

cov_y = np.cov(vector_intermagnet_y, vector_synthetic_y)[0][1]

cov_z = np.cov(vector_intermagnet_z, vector_synthetic_z)[0][1]



rho_x = cov_x / np.sqrt(var_intermagnet_x * var_synthetic_x)

print('Correlation coefficient X direction: ', rho_x)



rho_y = cov_y / np.sqrt(var_intermagnet_y * var_synthetic_y)

print('Correlation coefficient Y direction: ', rho_y)



rho_z = cov_z / np.sqrt(var_intermagnet_z * var_synthetic_z)

# uncomment to see each waveform offset removed

# avg_intermagnet_x = mean(vector_intermagnet_x)
# avg_synthetic_x = mean(vector_synthetic_x)
# 
# for i in range(vector_intermagnet_x.size):
#     vector_synthetic_x[i] -= avg_synthetic_x
#     vector_intermagnet_x[i] -= avg_intermagnet_x
# 
# avg_intermagnet_y = mean(vector_intermagnet_y)
# avg_synthetic_y = mean(vector_synthetic_y)
# 
# for i in range(vector_intermagnet_y.size):
#     vector_synthetic_y[i] -= avg_synthetic_y
#     vector_intermagnet_y[i] -= avg_intermagnet_y
# 
# avg_intermagnet_z = mean(vector_intermagnet_z)
# avg_synthetic_z = mean(vector_synthetic_z)
# 
# for i in range(vector_intermagnet_z.size):
#     vector_synthetic_z[i] -= avg_synthetic_z
#     vector_intermagnet_z[i] -= avg_intermagnet_z
# 
print('Correlation coefficient Z direction: ', rho_z)

plt.plot(time, pdyn_tsg, label= 'tsg pdyn')
plt.plot(time, pdyn_syn, label= 'synthetic pdyn')
plt.xlabel('Time (s)')
plt.ylabel('Pressure (nP)')
plt.legend()
# 
plt.show()
# 
plt.plot(time, dst_tsg, label= 'tsg dst')
plt.plot(time, dst_used, label= 'synthetic dst')
plt.xlabel('Time (s)')
plt.ylabel('dst (nT)')
plt.legend()
# 
plt.show()
# 


plt.plot(time, w1_tsg, label= 'tsg w1')
plt.plot(time, w1_syn, label= 'synthetic w1')
plt.xlabel('Time (s)')
plt.legend()

plt.show()

plt.plot(time, w2_tsg, label= 'tsg w2')
plt.plot(time, w2_syn, label= 'synthetic w2')
plt.xlabel('Time (s)')
plt.legend()

plt.show()

plt.plot(time, w3_tsg, label= 'tsg w3')
plt.plot(time, w3_syn, label= 'synthetic w3')
plt.xlabel('Time (s)')
plt.legend()

plt.show()

plt.plot(time, w4_tsg, label= 'tsg w4')
plt.plot(time, w4_syn, label= 'synthetic w4')
plt.xlabel('Time (s)')
plt.legend()

plt.show()

plt.plot(time, w5_tsg, label= 'tsg w5')
plt.plot(time, w5_syn, label= 'synthetic w5')
plt.xlabel('Time (s)')
plt.legend()

plt.show()

plt.plot(time, w6_tsg, label= 'tsg w6')
plt.plot(time, w6_syn, label= 'synthetic w6')
plt.xlabel('Time (s)')
plt.legend()

plt.show()


plt.plot(time, vector_intermagnet_x, label= 'tsg x')
plt.plot(time, vector_synthetic_x, label= 'synthetic x')
plt.xlabel('Time (s)')
plt.ylabel('Magnetic Field (nT)')
plt.legend()

plt.show()

plt.plot(time, vector_intermagnet_y, label= 'tsg y')
plt.plot(time, vector_synthetic_y, label= 'synthetic y')
plt.xlabel('Time (s)')
plt.ylabel('Magnetic Field (nT)')
plt.legend()

plt.show()

plt.plot(time, vector_intermagnet_z, label= 'tsg z')
plt.plot(time, vector_synthetic_z, label= 'synthetic z')
plt.xlabel('Time (s)')
plt.ylabel('Magnetic Field (nT)')
plt.legend()

plt.show()