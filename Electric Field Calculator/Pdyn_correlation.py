import MagneticFieldPredictor
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


data = pd.read_csv('OMNI_data_2015_clean_with_dst.csv')

length = data.index.size

synthetic_pdyn = np.zeros(length)

real_pdyn = data['Pdyn'].to_numpy()

for i, df in data.iterrows():

    synthetic_pdyn[i] = MagneticFieldPredictor.Pdyn(float(df['density']), float(df['speed']))

print(synthetic_pdyn)
print(real_pdyn)

var_synthetic = np.var(synthetic_pdyn)
var_real = np.var(real_pdyn)

covariance = np.cov(synthetic_pdyn, real_pdyn)[0][1]

rho = covariance / np.sqrt(var_synthetic  * var_real)


print(rho)

time = data['time'].to_numpy()

plt.figure()
plt.plot(time, synthetic_pdyn, label= 'synthetic')
plt.plot(time, real_pdyn, label= 'real')
plt.legend()
plt.show()