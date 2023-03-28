
import numpy as np
import cmath
from math import *
import pandas as pd
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft, fftfreq
import MagneticFieldPredictor

def k(omega:float, sigma:float) -> float:
    """ This method calculates the propagation constant for a given layer in the earth.
        @param: omega: angular frequency of the B field (rad/sec)
        @param: sigma: conductivity of that layer (Ohm*meters)^(-1)
        return: kn:    propagation constant of layer n (imaginary number) 

        Documentation: "Application Guide: Computing Geomagnetically-Induced Current in
                        the Bulk-Power System, " NERC, Dec. 2013. [Online]. Available:
                        http://www.nerc.com/comm/PC/Geomagnetic%20Disturbance%20Task
                        %20Force%20GMDTF%202013/GIC%20Application%20Guide%202
                        013-approved.pdf
    """

    mu0 = 4*np.pi * 10**(-7)
    kn = cmath.sqrt(1j * mu0 * omega * sigma)
    # print("kn: ",kn)
    return kn

def Z_final(omega:float, sigma:float) -> float:
    """ This method calculates the impedance of the final layer. 
        It is unique because there is no wave reflection at the bottom
        as there is with the other layers
        @param: omega: angular frequency of the B field (rad/sec)
        @param: sigma: conductivity of that layer (Ohm*meters)^(-1)
        return: z:     impedance of the final layer

        Documentation: "Application Guide: Computing Geomagnetically-Induced Current in
                        the Bulk-Power System, " NERC, Dec. 2013. [Online]. Available:
                        http://www.nerc.com/comm/PC/Geomagnetic%20Disturbance%20Task
                        %20Force%20GMDTF%202013/GIC%20Application%20Guide%202
                        013-approved.pdf
    """
    mu0 = 4*np.pi * 10**(-7)
    z = (1j * omega * mu0) / k(omega, sigma)
    # print("Z_final: ", z)
    return z

def r(omega:float, sigma:float, Znp1:float) -> float:
    """ This method calculates the reflection coefficient of the nth layer. 
        It depends on Z_(n+1)
        @param: omega: angular frequency of the B field (rad/sec)
        @param: sigma: conductivity of that layer (Ohm*meters)^(-1)
        @param: Znp1:  The impedance of the next layer down
        return: rn:    Reflection coefficient of the current layer

        Documentation: "Application Guide: Computing Geomagnetically-Induced Current in
                        the Bulk-Power System, " NERC, Dec. 2013. [Online]. Available:
                        http://www.nerc.com/comm/PC/Geomagnetic%20Disturbance%20Task
                        %20Force%20GMDTF%202013/GIC%20Application%20Guide%202
                        013-approved.pdf
    """
    mu0 = 4*np.pi * 10**(-7)
    # calculate propagation constant
    kn = k(omega, sigma)
    # calculate numerator of the equation 
    numerator = 1 - kn * (Znp1 / (1j * omega * mu0))
    # calculate denominator of the equation 
    denominator = 1 + kn * (Znp1 / (1j * omega * mu0))
    rn = numerator / denominator
    # print('rn: ', rn)
    return rn

def Zi(omega:float, sigma:float, rn:float, d:float) -> float:
    """ This method calculates the impedance of the nth layer. 
        @param: omega: angular frequency of the B field (rad/sec)
        @param: sigma: conductivity of that layer (Ohm*meters)^(-1)
        @param: rn:    The reflection coefficent of the current layer
        @param: d:     Thickness of the current layer (meters)
        return: Zi:    Impedance of the current layer

        Documentation: "Application Guide: Computing Geomagnetically-Induced Current in
                        the Bulk-Power System, " NERC, Dec. 2013. [Online]. Available:
                        http://www.nerc.com/comm/PC/Geomagnetic%20Disturbance%20Task
                        %20Force%20GMDTF%202013/GIC%20Application%20Guide%202
                        013-approved.pdf
    """
    mu0 = 4*np.pi * 10**(-7)

    # calculate propagation constant
    kn = k(omega, sigma)

    Zi = 1j * omega * mu0 * ((1 - rn * cmath.exp(- 2 * kn * d))/ 
                             kn*(1 + rn * cmath.exp(- 2 * kn * d)))
    # print("Zi: ", Zi)
    
    return Zi

def impedance_calculator(conductivity_model:pd.DataFrame, omega:float) -> float:
    """ This method calculates the impedance of the earth at a given angular frequency using the 1-D layer earth model
        @param:            conductivity_model: pandas dataframe with two columns. The first column has 
                           conductivity values (Ohm * meter)^(-1) The second column has the corresponding thickness of the layer. 
                           The rows must start at the surface and go down in order
        @param: omega:     angular frequency of the magnetic field
        return: impedance: The empedance of the earth at the given frequency. This is a compex number

        Documentation: "Application Guide: Computing Geomagnetically-Induced Current in
                        the Bulk-Power System, " NERC, Dec. 2013. [Online]. Available:
                        http://www.nerc.com/comm/PC/Geomagnetic%20Disturbance%20Task
                        %20Force%20GMDTF%202013/GIC%20Application%20Guide%202
                        013-approved.pdf
    
    """
    # extract data from DataFrame into numpy arrays
    conductivity_vector = conductivity_model['sigma'].to_numpy(dtype=float)
    depth_vector = conductivity_model['d'].to_numpy(dtype=float)

    # begin recursive calculation of the impedance at the surface in a for loop
    length = conductivity_vector.size
    # initialize final impedance value
    impedance = 0
    for i in range(length):
        # iterate from the bottom up
        j = length - 1 - i
        if i == 0: # if i == 0, we need the special case where we are at the last layer
            impedance = Z_final(omega, 1/conductivity_vector[j])
            continue
        # recursive relation to calculate impedance at the surface
        impedance = Zi(omega, 1/conductivity_vector[j], r(omega,1/conductivity_vector[j], impedance), depth_vector[j])
    return impedance

def angular_frequency(array:np.array, time:np.array) -> np.array:
    """ This method computes the angular frequency at each point in the input array. 
        The output is an array of angular frequencies (rad/sec). Each element is not unique.
        The frequency is calculated by determining the number of times 
        the derivative changes from positive to negative locally.
        @param: array: array of values for which the angular frequency is needed.
        @param: time:  array of corresponding times is seconds
        return: freq:  array of corresponding angular frequencies
    """
    # initialize flags to False
    up = False

    freq = np.zeros(array.size)

    # calculate a vector that contains all of the places where the data changes direction
    direction_change_vector = np.zeros(array.size, dtype=int)
    for i in range(array.size - 1):
        temp = array[i + 1] - array[i]
        if temp > 0:
            if not up:
                direction_change_vector[i] = -1
            up = True
        elif temp < 0:
            if up:
                direction_change_vector[i] = 1
            up = False
    # sample size is the number of points to anylize before calculating the frequency
    sample_size = 4
    for i in range(0, direction_change_vector.size - sample_size, sample_size):
        num_direction_changes = 0
        for j in range(sample_size):
            if direction_change_vector[i + j] != 0:
                num_direction_changes += 1
        
        delta_t = time[i + sample_size - 1] - time[i]
        frequency = (num_direction_changes / delta_t) * 2 * np.pi
        # if frequency is zero set it to the minimum typical value
        if frequency == 0:
            frequency = 0.0001*2* np.pi
        for j in range(sample_size):
            freq[i + j] = frequency
    # calculate frequency for values missed do to larger than 1 step size
    
    num_direction_changes = 0
    for i in range(sample_size):
        if direction_change_vector[-(i + 1)] != 0:
                num_direction_changes += 1
    delta_t = time[i + sample_size - 1] - time[i]
    frequency = (num_direction_changes / delta_t) *2* np.pi
    # if frequency is zero set it to the minimum typical value
    if frequency == 0:
        frequency = 0.0001*2* np.pi
    for i in range(sample_size):
        freq[-(i + 1)] = frequency
    return freq
        


def B_to_E(conductivity_model: pd.DataFrame, B:np.array, time:np.array, sign:int) -> np.array:
    """ This method performs the convolution in the frequency domain 
        to obtain the electric field from the magnetic field.
        @param: conductivity_model: dataframe of the 1-D layer Earth conductivity
        @param: B:                  array of B field direction
        @param: time:               array of corresponding time stamps
        @param: sign:               The y direction gets a negative sign. This parameter allows this to be done
        return: E:                  Electric field vector the same length as B
    """
    mu0 = 4 * np.pi * 10**(-7)
    time = np.array(time)
    H = (B * 10**(-9)) / (-mu0)
    H_fd = fft(H)
    print(H_fd)
    # get the angular frequency at each time point.
    omega = angular_frequency(B, time)
    # print(omega)
    impedance_vector = np.zeros(B.size,dtype=complex)
    for i in range(B.size):
        impedance_vector[i] = impedance_calculator(conductivity_model, omega[i])
    # print(impedance_vector)
    
    E_fd = np.multiply(impedance_vector, H_fd)
    # print(E_fd)
    E = ifft(E_fd)
    E = np.real(E) * sign
    time_step = int(np.sum(time) / time.size)

    freq = fftfreq(time.size, time_step)
    max = 0
    maxi = 0
    for i in range(freq.size):
        if max < abs(E_fd[i]):
            max = abs(E_fd[i])
            maxi = i
        # print('freq, E_fd: ', freq[i], np.absolute(E_fd[i]))
    print(maxi)
    print('max frequency: ', np.absolute(E_fd[maxi:maxi+5]))
    print(freq)
    print('E_field, time domain', E)
    
    
    E_fd[0] = 0.1
    ax1 = plt.subplot(211)
    ax1.plot(freq, np.absolute(E_fd))
    ax1.set_title('Frequency Domain Electric Field')
    plt.yscale('log')
    ax2 = plt.subplot(212)
    ax2.set_title('Frequency Domain Magnetic Field')
    H_fd[0] = 10
    ax2.plot(freq, np.absolute(H_fd))
    plt.yscale('log')
    plt.show()
    
    ax1 = plt.subplot(211)
    ax1.plot(time, E)
    ax1.set_title("Electric Field Time Domain")
    ax2 = plt.subplot(212)
    ax2.set_title("Magnetic Field Time Domain")
    ax2.plot(time, H)
    plt.show()
    
    return E

def calculate_e_field(conductivity_model:pd.DataFrame, B_field:pd.DataFrame) -> pd.DataFrame:
    """ This method is the parent function that should be called by the Application core.
        @param: conductivity_model: dataframe of the 1-D Earth conductivity
        @param: solar_storm:        solar storm data from NOAA
        return: E_field:            triple indexed pandas dataframe with electric field vector

        Documentation: "Application Guide: Computing Geomagnetically-Induced Current in
                        the Bulk-Power System, " NERC, Dec. 2013. [Online]. Available:
                        http://www.nerc.com/comm/PC/Geomagnetic%20Disturbance%20Task
                        %20Force%20GMDTF%202013/GIC%20Application%20Guide%202
                        013-approved.pdf
    """
    E_field = B_field.copy(deep=True)
    E_field.columns = ['Ex', 'Ey', 'Ez']
    
    E_field.drop(axis=1,labels='Ez',inplace=True)
    
    # extract needed longitude and latitude points from the dataframe.
    # This is necessary because the B vector needs to contain all time points.
    time_vector = B_field.index.get_level_values(0).to_numpy(dtype=float)
    longitude_vector = B_field.index.get_level_values(1).to_numpy()
    latitude_vector = B_field.index.get_level_values(2).to_numpy()
    trimmed_time_vector = []
    trimmed_longitude_vector = []
    trimmed_latitude_vector = []

    for time in time_vector:
        if time not in trimmed_time_vector:
            trimmed_time_vector.append(time)
    for long in longitude_vector:
        if long not in trimmed_longitude_vector:
            trimmed_longitude_vector.append(long)
    for lat in latitude_vector:
        if lat not in trimmed_latitude_vector:
            trimmed_latitude_vector.append(lat)
    

    # loop through all of the required points and calculate the E field then add it to the dataframe
    for long in trimmed_longitude_vector:
        for lat in trimmed_latitude_vector:
            Bx = B_field.loc[:,long,lat]['Bx'].to_numpy(copy=True)
            By = B_field.loc[:,long,lat]['By'].to_numpy(copy=True)
            Ex = B_to_E(conductivity_model, By, trimmed_time_vector, 1)
            Ey = B_to_E(conductivity_model, Bx, trimmed_time_vector, -1)
            i = 0
            # iterate through the E_field dataframe and populate the calculated E field values
            for time, time_df in E_field.groupby(level=0):
                E_field.loc[(time, long, lat), 'Ex'] = Ex[i]
                E_field.loc[(time, long, lat), 'Ey'] = Ey[i]
                i += 1
                

    print(E_field)
    return E_field

def ElectricFieldCalculator(resistivity_data:pd.DataFrame, storm_data:pd.DataFrame, min_longitude:float, max_longitude:float, min_latitude:float, max_latitude:float, granularity:int) -> pd.DataFrame:
    """ This method is the parent function that should be called by the Application core.
        @param: resistivity_data: dataframe of the 1-D Earth conductivity
        @param: solar_storm:        solar storm data from NOAA
        @param: min_longitude: minimum longitude in degrees
        @param: max_longitude: maximum longitude in degrees
        @param: min_latitude: minimum latitude in degrees
        @param: max_latitude: maximum latitude in degrees
        @param: granularity: the step size between GPS coordinates. This parameter has a strong effect on computation time.
        The above five parameters form a grid where the electric field vector will be calculated for each time point
        
        return: E_field:            triple indexed pandas dataframe with electric field vector

        Documentation: "Application Guide: Computing Geomagnetically-Induced Current in
                        the Bulk-Power System, " NERC, Dec. 2013. [Online]. Available:
                        http://www.nerc.com/comm/PC/Geomagnetic%20Disturbance%20Task
                        %20Force%20GMDTF%202013/GIC%20Application%20Guide%202
                        013-approved.pdf
    """
    B_field_data = MagneticFieldPredictor.magnetic_field_predictor(storm_data, min_longitude, max_longitude, min_latitude, max_latitude, granularity)
    E_Field = calculate_e_field(resistivity_data, B_field_data)
    return E_Field

if __name__ == '__main__':
    # data = pd.read_csv('conductivity_model_test_data.csv')
    res_data = pd.read_csv('data\piedmont conductivity.csv')

    omega_b = 2 * np.pi * 1

    mag_data = pd.read_csv("data\\20230315.csv")
    index_arrays = [mag_data["time"].to_numpy(dtype=str),mag_data["longitude"].to_numpy(),mag_data["latitude"].to_numpy()]

    index = pd.MultiIndex.from_arrays(index_arrays, names=['time', 'longitude', 'latitude'])

    mag_data.index = index

    mag_data.drop(axis=1,labels=['time', 'longitude', 'latitude'],inplace=True)
    mag_data = mag_data[(mag_data != 0).any(axis=1)]


    calculate_e_field(res_data, mag_data)

    
    print(impedance_calculator(res_data, omega_b))

    w = [0.00001,0.0001,0.001,0.01,0.1,1]

    z = [0,0,0,0,0,0]

    for i in range(len(w)):
        z[i] = abs(impedance_calculator(res_data, w[i]*2*np.pi))

    plt.figure()
    plt.xscale('log')

    plt.plot(w,z,scalex='log', scaley='log')
    plt.grid()
    plt.show()