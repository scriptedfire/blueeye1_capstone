import ElectricFieldPredictor
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.fft import fft, fftfreq

""" This code uses the following paper to validate ElectricFieldCalculator.py

        Documentation:  D. H. Boteler, R. J. Pirjola and L. Marti, "Analytic Calculation of 
                        Geoelectric Fields Due to Geomagnetic Disturbances: A Test Case," 
                        in IEEE Access, vol. 7, pp. 147029-147037, 2019, doi: 10.1109/ACCESS.2019.2945530.
"""

quebec_res = pd.read_csv('Quebec_1D_model.csv') 
time = np.arange(0,43200,0.5)

mu0 = 4 * np.pi * 10**(-7)



# the data in the following arrays are taken from the tables in the documentation above
A_m = [200, 90, 30, 17, 8, 3.5, 1]
phi_m = np.array([10, 20, 30, 40, 50, 60, 70], dtype=float)*np.pi/180.0
f_m = [0.00009259, 0.00020833, 0.00047619, 0.00111111, 0.00238095, 0.00555555, 0.025]
B = np.zeros(time.size)

E_m = np.array([43.76735, 40.32326, 26.04161, 26.16634, 20.74819, 16.31864, 9.60469])*10**(-3)
phi_m2 = np.array([87.15, 93.76, 97.19, 102.08, 110.58, 114.97, 114.38])*np.pi/180.0

E = np.zeros(time.size)
k = np.zeros(7)
k_phi = np.zeros(7)


# calculate the earth response using the ElectricFieldCalculator and compare with the results in the paper
for i in range(7):
    k_i = ElectricFieldPredictor.k_f(quebec_res, f_m[i])
    k[i] = abs(k_i) * 10**(-3)
    k_phi[i] = np.arctan2(k_i.imag,k_i.real) * 180/np.pi

K_mag_expected = [0.2188, 0.4480, 0.8681, 1.5392, 2.5935, 4.6625, 9.6047]
K_phase_expected = [77.15, 73.76, 67.17, 62.08, 60.58, 54.97, 44.38]

# test Earth transfer function
num_failed_mag = 0
num_failed_phase = 0
for i in range(7):
    if k[i] < K_mag_expected[i] - K_mag_expected[i]*0.01 or k[i] > K_mag_expected[i] + K_mag_expected[i]*0.01:
        num_failed_mag += 1
        print(f'Earth Response magnitude Incorrect! Expected: {K_mag_expected[i]}, got {k[i]}')
    if k_phi[i] < K_phase_expected[i] - K_phase_expected[i]*0.01 or k_phi[i] > K_phase_expected[i] + K_phase_expected[i]*0.01:
        num_failed_phase += 1
        print(f'Earth Response phase Incorrect! Expected: {K_phase_expected[i]}, got {k_phi[i]}')

if num_failed_mag == 0:
    print("All Earth Response magnitude tests pass")
else:
    print(f'{num_failed_mag} Earth response magnitude tests failed')

if num_failed_phase == 0:
    print("All Earth Response phase tests pass")
else:
    print(f'{num_failed_phase} Earth response phase tests failed')

# generate synthetic electric and magnetic fields in the paper
for t in range(time.size):
    for m in range(7):
        B[t] += A_m[m] * np.sin(2*np.pi*f_m[m]*time[t] + phi_m[m])
        E[t] += E_m[m] * np.sin(2*np.pi*f_m[m]*time[t] + phi_m2[m])

# calculate e field from the synthetic magnetic field and compare with the synthetic magnetic field
my_E_field = ElectricFieldPredictor.B_to_E(quebec_res, B, time, 1)

plt.subplot(3,1,1)
plt.plot(time, B, label='Magnetic Field Test Data')
plt.legend()
plt.ylabel('Magnetic Field (nT)')
plt.xlabel('time (s)')

plt.subplot(3,1,2)
plt.plot(time, E, label='Electric Field Comparison Data')
plt.legend()
plt.ylabel('Electric Field (V/km)')
plt.xlabel('time (s)')
plt.subplot(3,1,3)
plt.plot(time, my_E_field, label='Electric Field Calculated Data')

plt.ylabel('Electric Field (V/km)')
plt.xlabel('time (s)')
plt.legend()
plt.subplots_adjust(left=0.15,
                    bottom=0.1,
                    right=0.9,
                    top=0.95,
                    hspace=0.6)
plt.show()

# calculate correlation coefficient of the actual and expected electric fields
rho = np.cov(E,my_E_field)[0][1]/np.sqrt(np.var(E)*np.var(my_E_field))
print("Electric Field Correlation Coefficient", rho)


