
import numpy as np
import cmath
from math import *
import pandas as pd
from scipy.fft import fft, ifft, fftfreq
import MagneticFieldPredictor

def k(f:float, sigma:float) -> float:
    """ This method calculates the propagation constant for a given layer in the earth.
        @param: f: frequency of the B field (Hz)
        @param: sigma: conductivity of that layer (Ohm*meters)^(-1)
        return: kn:    propagation constant of layer n (imaginary number) 

        Documentation:  D. H. Boteler, R. J. Pirjola and L. Marti, "Analytic Calculation of 
                        Geoelectric Fields Due to Geomagnetic Disturbances: A Test Case," 
                        in IEEE Access, vol. 7, pp. 147029-147037, 2019, doi: 10.1109/ACCESS.2019.2945530.
    """
    mu0 = 4*np.pi * 10**(-7)
    kn = cmath.sqrt(2j * np.pi * mu0 * f * sigma)
        
    return kn

def K_final(f:float, sigma:float) -> complex:
    """ This method calculates the final layer of the earth response transfer function.
        @param: f: frequency of the B field (Hz)
        @param: sigma: conductivity of that layer (Ohm*meters)^(-1)
        return: k: Earth response of final layer (imaginary number) 

        Documentation:  D. H. Boteler, R. J. Pirjola and L. Marti, "Analytic Calculation of 
                        Geoelectric Fields Due to Geomagnetic Disturbances: A Test Case," 
                        in IEEE Access, vol. 7, pp. 147029-147037, 2019, doi: 10.1109/ACCESS.2019.2945530.
    """
    mu0 = 4*np.pi * 10**(-7)
    k = cmath.sqrt(2j * np.pi * f / (mu0 * sigma))
    return k

def K_n(K_np1:complex, kn:complex, f:float, d:float) -> complex:
    """ This method calculates the nth layer of the earth response transfer function.
        @param: K_np1: n + 1 layer of the Earth repsonse transfer function
        @param: kn propagation constant of the nth layer
        @param: f: frequency of the B field (Hz)
        @param: d: thickness of that layer meters
        return: kn: Earth response of final layer

        Documentation:  D. H. Boteler, R. J. Pirjola and L. Marti, "Analytic Calculation of 
                        Geoelectric Fields Due to Geomagnetic Disturbances: A Test Case," 
                        in IEEE Access, vol. 7, pp. 147029-147037, 2019, doi: 10.1109/ACCESS.2019.2945530.
    """           
    eta_n = 2j * np.pi * f / kn
    numerator = K_np1 * (1 + cmath.exp(-2 * kn * d)) + eta_n * (1 - cmath.exp(-2 * kn * d))
    denomenator = K_np1 * (1 - cmath.exp(-2 * kn * d)) + eta_n * (1 + cmath.exp(-2 * kn * d))
    Kn = eta_n * numerator / denomenator
    return Kn

def k_f(impedance_data:pd.DataFrame, f:float) -> complex:
    """ This function computes the earth response for a given frequency and 1-D layer Earth model
        @param: impedance_data: pandas dataframe with the impedance of the layer and the thickness of each layer
                                impedance in Ohm*meters, thickness in meters.
        @param: f: frequency to evaluate the transfer function (Hz)
        return: ki: Earth response at that frequency
    """
    impedance = impedance_data['sigma'].to_numpy(dtype=float)
    depth = impedance_data['d'].to_numpy(dtype=float)
    ki = 0
    for i in range(impedance.size):
        if i == 0:
            ki = K_final(f, 1/impedance[-1])
            continue
        ki = K_n(ki, k(f, 1/impedance[impedance.size - 1 - i]), f, depth[impedance.size - 1 - i])
    return ki


def B_to_E(conductivity_model: pd.DataFrame, B:np.array, time:np.array, sign:int) -> np.array:
    """ This method performs the convolution in the frequency domain 
        to obtain the electric field from the magnetic field.
        @param: conductivity_model: dataframe of the 1-D layer Earth resistivity
        @param: B:                  array of B field direction
        @param: time:               array of corresponding time stamps
        @param: sign:               The y direction gets a negative sign. This parameter allows this to be done
        return: E:                  Electric field vector the same length as B
    """
    
    
    # interpolate B field to be spaced by 60 seconds
    #############################################
    # Comment these 3 lines out to test with Electric_field_calculator_test_bench.py
    #x_array_B_field = np.arange(time[0], time[time.size - 1], 60)
    #
    #B = np.interp(x_array_B_field, time, B)
    #
    #time = x_array_B_field

    ###########################################
    
    
    B_fd = fft(B*10**(-9))
    
    
    time_step = 60
    time_step = time[1] - time[0]
    freq = fftfreq(time.size, time_step)
    
    impedance_vector = np.zeros(B.size, dtype=complex)
    # DC is not meaningful, make this frequency very very low
    freq[0] = 0.000001
    for i in range(B.size):
        impedance_vector[i] = k_f(conductivity_model, freq[i])
    
    E_fd = np.zeros(B_fd.size, dtype=complex)

    for w in range(freq.size):
        E_fd[w] = impedance_vector[w] * B_fd[w] 
    
    E = ifft(E_fd)

    E = np.real(E) * sign * 1000 # multiply by sign and 1000 to get it in V/km in the correct direction
    
    # Remove as much aliasing as possible
    if E.size >= 60:
        for i in range(60):
            E[i] = E[60]
            E[E.size - i- 1] = E[E.size - 1 - 60]
    
    
    return E

def calculate_e_field(conductivity_model:pd.DataFrame, B_field:pd.DataFrame) -> pd.DataFrame:
    """ This method builds the pandas data frame of E field values.
        @param: conductivity_model: dataframe of the 1-D Earth conductivity
        @param: solar_storm:        solar storm data from NOAA
        return: E_field:            triple indexed pandas dataframe with electric field vector

        Documentation:  D. H. Boteler, R. J. Pirjola and L. Marti, "Analytic Calculation of 
                        Geoelectric Fields Due to Geomagnetic Disturbances: A Test Case," 
                        in IEEE Access, vol. 7, pp. 147029-147037, 2019, doi: 10.1109/ACCESS.2019.2945530.
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
    trimmed_time_vector = np.array(trimmed_time_vector)

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
                   
    return E_field

def ElectricFieldCalculator(resistivity_data:pd.DataFrame, storm_data:pd.DataFrame, min_longitude:float, max_longitude:float, min_latitude:float, max_latitude:float, log_queue:object) -> pd.DataFrame:
    """ This method is the parent function that should be called by the Application core.
        @param: resistivity_data: dataframe of the 1-D Earth conductivity
        @param: solar_storm:        solar storm data from NOAA
        @param: min_longitude: minimum longitude in degrees
        @param: max_longitude: maximum longitude in degrees
        @param: min_latitude: minimum latitude in degrees
        @param: max_latitude: maximum latitude in degrees
        @param: log_queue: queue object to send log messages through
        The above five parameters form a grid where the electric field vector will be calculated for each time point
        
        return: E_field: triple indexed pandas dataframe with electric field vector

        Documentation:  D. H. Boteler, R. J. Pirjola and L. Marti, "Analytic Calculation of 
                        Geoelectric Fields Due to Geomagnetic Disturbances: A Test Case," 
                        in IEEE Access, vol. 7, pp. 147029-147037, 2019, doi: 10.1109/ACCESS.2019.2945530.
    """
    log_queue.put("Calcaulating magnetic field...\n")
    try:
        B_field_data = MagneticFieldPredictor.magnetic_field_predictor(storm_data, min_longitude, max_longitude, min_latitude, max_latitude)
    except Exception as e:
        e = str(e)
        log_queue.put('An Unexpected error occured when attempting to predict the magnetic field\n')
        log_queue.put(e)
        log_queue.put('\n')
        return e
    print('\n',"              Magnetic Field Data\n")
    print(B_field_data, flush=True)
    print('\n')
    log_queue.put("Magnetic field calculation complete.\nCalculating electric field from predicted magnetic field...\n")
    try:
        E_Field = calculate_e_field(resistivity_data, B_field_data)
    except Exception as e:
        e = str(e)
        log_queue.put('An Unexpected error occured when attempting to calculate the electric field\n')
        log_queue.put(e)
        log_queue.put('\n')
        return e
    
    log_queue.put("Electric Field Calculation complete.\n")
    return E_Field

