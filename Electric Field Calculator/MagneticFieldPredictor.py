from geopack import t04, gpack
import numpy as np
import pandas as pd
from math import *
from datetime import datetime
import time
from dateutil import parser
from dateutil.tz import UTC
import ppigrf
start = time.time()

""" 
    Author: Stephen Hurt
    email: stephenhurt99@tamu.edu
    This script implements a predictive model of the earth's magnetic field 
    described in the documentation below and papers referenced therein. This paper is hereafter refered to as [1]
    documentation
        [1] N. A. Tsyganenko and M. I. Sitnov, Modeling the dynamics of the inner magnetosphere during
            strong geomagnetic storms, J. Geophys. Res., v. 110 (A3), A03208, doi: 10.1029/2004JA010798, 2005."""


def Pdyn(rhoP: float, velocity: float) -> float:
    """ This function calculates the solar wind dynamic pressure given the particle density, and solar wind speed
        @param: rhoP: particle density in 1/cm^3
        @param: velocity: solar wind speed in km/s
        return: dynamicPressure_nP (nP)
        Notes:
        Calculating solar wind dynamic pressure
        Pdyn = rho * V^2
        rho == mass density
        V == wind velocity
        The solar wind is approximately 95% protons (H + ) , 4% alpha particles ( H e + + ) and 1% minor ions, of which carbon, nitrogen, oxygen, neon, magnesium, silicon and iron are the most abundant.
        solar wind mass == 0.95 * 1.6726e-27kg + 0.04 * 6.6447e-27kg + 0.01*4.664e-26kg = 2.3212e-27

        solar wind speed units: km/s
        desnity units = 1/cm^3
        rho = density * (solar wind mass)
    """
    SOLAR_WIND_MASS = 2.3212 * 10 ** -27 #kg

    speed_ms = velocity * 1000 # m/s
    rho_m3 = rhoP * 100 **3 # 1/m^3
    rho = rho_m3 * SOLAR_WIND_MASS # mass desnsity of the solar wind

    dynamicPressure = rho * (speed_ms ** 2) # Pascals

    dynamicPressure_nP = dynamicPressure * 10 ** 9 # nano Pascals
    return dynamicPressure_nP


def Sk(N: float, V: float, B : float, lamb: float, beta: float, gamma: float) -> float:
    """ This function is a subroutine of the Wi functions. It calculates a subfunction of the sum computed in each function.
        @param: N: solar wind density
        @param: V: solar wind speed
        @param: B: magnitude of the southward component of the IMF
        @param: lamb: fitting parameter
        @param: beta: fitting parameter
        @param: gamma: fitting parameter
        :return scalar solution 
        
    """
    s = ((N/5.0)**lamb) * ((V/400.0)**beta) * ((1.16 * B/5.0)**gamma)
    
    return s

def Wt1(t : np.array, N : np.array, V : np.array, B : np.array) -> float:
    """ This method computes a component of the scalar coefficient 
        of the first component of the tail B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        return: Wt1: W parameter described in [1]  
    """
    resolution = (t[-1] - t[0]) / t.size
    if resolution == 0:
        resolution = 1
    # fitting constants from [1]
    r = 0.383403
    gamma = 0.916555
    beta = 0.846509
    lamb = 0.394732
    # initialize W and compute the numerical integral over t
    Wt1 = 0
    for k in range(t.size - 1):
        Wt1 += Sk(N[k], V[k], B[k], lamb, beta, gamma) * exp((r/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wt1 = Wt1 * (r/normR)
    return Wt1

def Wt2(t : np.array, N : np.array, V : np.array, B : np.array) -> float:
    """ This method computes a component of the scalar coefficient 
        of the second component of the tail B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        return: Wt2: W parameter described in [1]   
    """
    resolution = (t[-1] - t[0]) / t.size
    if resolution == 0:
        resolution = 1
    # fitting constants from [1]
    r = 0.648176
    gamma = 0.898772
    beta = 0.180725
    lamb = 0.550920
    # initialize W and comput the numerical integral over t
    Wt2 = 0
    for k in range(t.size - 1):
        Wt2 += Sk(N[k], V[k], B[k], lamb, beta, gamma) * exp((r/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wt2 = Wt2 * (r/normR)
    return Wt2


def Ws3(t : np.array, N : np.array, V : np.array, B : np.array) -> float:
    """ This method computes a component of the scalar coefficient 
        of the symetric ring current B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        return: Ws3: W parameter described in [1]   
    """
    resolution = (t[-1] - t[0]) / t.size
    if resolution == 0:
        resolution = 1
    # fitting constants from [1]
    r = 0.318752E-01 
    gamma = 1.29123
    beta = 2.26596
    lamb = 0.387365
    # initialize W and comput the numerical integral over t
    Ws3 = 0
    for k in range(t.size - 1):
        Ws3 += Sk(N[k], V[k], B[k], lamb, beta, gamma) * exp((r/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Ws3 = Ws3 * (r/normR)
    return Ws3

def Wp4(t : np.array, N : np.array, V : np.array, B : np.array) -> float:
    """ This method computes a component of the scalar coefficient 
        of the first component of the tail B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        return: Wp4: W parameter described in [1]   
    """
    resolution = (t[-1] - t[0]) / t.size
    if resolution == 0:
        resolution = 1
    # fitting constants from [1]
    r = 0.581168
    gamma = 1.33199
    beta = 1.28211
    lamb = 0.436819
    # initialize W and comput the numerical integral over t
    Wp4 = 0
    for k in range(t.size - 1):
        Wp4 += Sk(N[k], V[k], B[k], lamb, beta, gamma) * exp((r/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wp4 = Wp4 * (r/normR)
    return Wp4


def Wr5(t : np.array, N : np.array, V : np.array, B : np.array) -> float:
    """ This method computes a component of the scalar coefficient 
        of the first component of the Birkeland Current B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        return: Wr5: W parameter described in [1]   
    """
    resolution = (t[-1] - t[0]) / t.size
    if resolution == 0:
        resolution = 1
    # fitting constants from [1]
    R5 = 1.15070
    GAMMA5 = 0.699074
    BETA5 = 1.62290
    LAMB5 = 0.405553
    # initialize W and comput the numerical integral over t
    Wr5 = 0
    for k in range(t.size - 1):
        Wr5 += Sk(N[k], V[k], B[k], LAMB5, BETA5, GAMMA5) * exp((R5/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wr5 = Wr5 * (R5/normR)
    return Wr5

def Wr6(t : np.array, N : np.array, V : np.array, B : np.array) -> float:
    """ This method computes a component of the scalar coefficient 
        of the second component of the Birkeland Current B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        return: Wr6: W parameter described in [1]   
    """
    resolution = (t[-1] - t[0]) / t.size
    if resolution == 0:
        resolution = 1
    # fitting constants from [1]
    R6 = 0.843004
    GAMMA6 = 0.537116
    BETA6 = 2.42297
    LAMB6 = 1.26131
    # initialize W and comput the numerical integral over t
    Wr6 = 0
    for k in range(t.size - 1):
        Wr6 += Sk(N[k], V[k], B[k], LAMB6, BETA6, GAMMA6) * exp((R6/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wr6 = Wr6 * (R6/normR)
    return Wr6

def GPS_to_cartesian(longitude:float, latitude:float, elevation:float = 0) -> list:
    """ Converts gps coordiantes to geocentric cartesian coordinates in earth radii
        elevations assumed to be in feet
        @param: longitude: longitude expressed in degrees with East being positive
        @param: latitude: latitude in degree with North Being positive
        @param: elevation: altitude above sea level (feet)
        return: x, y, z: the geo cartesian coordinates
    """
    Re  = 2.093e+7 # feet
    rho = 1 + elevation/Re

    if latitude >= 0:
        phi = np.pi/2 - np.deg2rad(latitude)
    else:
        phi = -np.deg2rad(latitude) + np.pi/2
    theta = np.deg2rad(longitude)
    
    x = rho * np.sin(phi) * np.cos(theta)
    y = rho * np.sin(phi) * np.sin(theta)
    z = rho * np.cos(phi)
    return x, y, z

def cartesian_to_GPS(x:float, y:float, z:float) -> list:
    """ Converts geocentric cartesian coordinates to gps coordinates
        This function calls the west and south direction negative
        @param: x, y, z: the geo cartesian coordinates
        return: longitude, latitude: units are degrees and North and East are positive
    """

    rho = np.sqrt(x**2 + y**2 + z**2)

    # Use the sign of the individual parameters to determine what the value should be.
    if rho == 0:
        phi = 0
    else:
        # use cartesian to polar transform equation
        phi = np.arccos(z/rho)
        # subtract form pi/2 to correct for the fact that the equator is 0 degrees
        phi = np.pi/2 - phi
    # handle the special case when the cartesian to polar transform would have division by 0
    if x == 0:
        if y < 0:
            theta = -np.pi / 2
        elif y == 0:
            theta = 0
        else:
            theta = np.pi / 2
    # use cartesian to polar transform
    else:
        theta = np.arctan(y/x)
        # correct for sign
        if x < 0:
            if y < 0:
                theta = theta - np.pi
            else:
                theta = theta + np.pi
            
    longitude = theta
    latitude = phi
    return longitude, latitude

def geo_to_enu(x:float, y:float, z:float, longitude:float, latitude:float):
    """ This function is a coordinate transform from geocentric coordinates to enu coordinates
        @param: x, x coordinate in geocentric coordinates
        @param: y, y coordinate in geocentric coordinates
        @param: z, z coordinate in geocentric coordinates
        @param: longitude: longitude in degrees
        @param: latitude: latitude in degrees
        return: e, n, u: coordinates in enu
        documentation: https://gssc.esa.int/navipedia/index.php/Transformations_between_ECEF_and_ENU_coordinates
    """ 
    lamb = np.deg2rad(longitude)
    phi = np.deg2rad(latitude)
    T = [[-np.sin(lamb),                np.cos(lamb),                         0],
         [-np.cos(lamb) * np.sin(phi), -np.sin(lamb) * np.sin(phi), np.cos(phi)],
         [ -np.cos(lamb) * np.cos(phi),  -np.sin(lamb) * np.cos(phi), -np.sin(phi)]]
    T_matrix = np.array(T)
    
    Bgeo = np.array([x, y, z])
    
    e, n, u = np.matmul(T_matrix, Bgeo)
    return e, n, u

def calculateSouthBField(Bxgsm: np.array, Bygsm: np.array, Bzgsm:np.array) -> np.array:
    """ This function return an array of the magnitude of the southward components of the interplanetary magnetic field (IMF)
        @param: Bxgsm: x component of the IMF in gsm coordinates
        @param: Bygsm: y component of the IMF in gsm coordinates
        @param: Bzgsm: z component of the IMF in gsm coordinates
        return: southern component of the IMF relative to the dipole
    """
    Bsouth = np.zeros(Bxgsm.size)
    for i in range(Bxgsm.size):
        Bgeo = gpack.geogsm(Bxgsm[i], Bygsm[i], Bzgsm[i], -1)
        Bgeo = gpack.geomag(Bgeo[0], Bgeo[1], Bgeo[2], 2)
        if Bgeo[2] > 0:
            Bsouth[i] = 0
        else:
            Bsouth[i] = abs(Bgeo[2])
    return Bsouth


def calculateBField(t: np.array, N: np.array, V: np.array, Bxgsm: np.array, Bygsm: np.array, Bzgsm: np.array, Vxgsm:float, Vygsm:float, Vzgsm:float, longitudeCBF: float, latitudeCBF: float, dst: float) -> list:
    """ This function calculates and returns the magnetic field vector at a given time point which is the last time point in the t array
        
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: Bxgsm: x component of the interplanetary magnetic field (IMF) in gsm coordinates
        @param: Bygsm: y component of the interplanetary magnetic field (IMF) in gsm coordinates
        @param: Bzgsm: z component of the interplanetary magnetic field (IMF) in gsm coordinates
        @param: Vxgsm: x component of the solar wind in gsm coordinates
        @param: Vygsm: y component of the solar wind in gsm coordinates
        @param: Vzgsm: z component of the solar wind in gsm coordinates
        @param: longitudeCBF: float of the longitude where the B field is being evaluated
        @param: latitudeCBF: float of the latitude where the B field is being evaluated
        @param: dst: most recent dst index in nT
        return: Bxgeo, Bygeo, Bzgeo predicted magnetic field vector
    """
    gpack.recalc(t[-1])
    Vxgse, Vygse, Vzgse = gpack.gsmgse(Vxgsm, Vygsm, Vzgsm, 1) 
    psi = gpack.recalc(t[-1], Vxgse, Vygse, Vzgse)
    
    B = calculateSouthBField(Bxgsm, Bygsm, Bzgsm)
    
    # update current time to be the last time in the series
    
    x, y, z = GPS_to_cartesian(longitudeCBF, latitudeCBF, 5318)

    # convert geo cartesian coordinates to gsm cartesian coordinates
    xgsm, ygsm, zgsm = gpack.geogsm(x, y, z, 1)
    
    W1 = Wt1(t, N, V, B)
    W2 = Wt2(t, N, V, B)
    W3 = Ws3(t, N, V, B)
    W4 = Wp4(t, N, V, B)
    W5 = Wr5(t, N, V, B)
    W6 = Wr6(t, N, V, B)
    
    speed = V[-1]
    pdyn = Pdyn(N[-1], speed)
    
    parmod = [pdyn, dst, Bygsm[-1], Bzgsm[-1], W1, W2, W3, W4, W5, W6]
    
    Bxgsm, Bygsm, Bzgsm = t04.t04(parmod, psi, xgsm, ygsm, zgsm)
    
    
    Bxgeo, Bygeo, Bzgeo = gpack.geogsm(Bxgsm, Bygsm, Bzgsm, -1) #gpack.geogsm(Bxdipole, Bydipole, Bzdipole, -1)
    # e = east component (y)
    # n = north component (x)
    # u = upward component (z)
    h = 0
    
    Be, Bn, Bu = ppigrf.igrf(longitudeCBF, latitudeCBF, h, datetime.fromtimestamp(t[-1]))
    e, n, u = geo_to_enu(Bxgeo, Bygeo, Bzgeo, longitudeCBF, latitudeCBF)
    
    return n + Bn, e + Be, u + Bu



def magnetic_field_predictor(storm_data:pd.DataFrame, min_longitude:float, max_longitude: float, min_latitude:float, max_latitude:float) -> pd.DataFrame:
    """ Take in strom data in a pandas dataframe each column will be a different data type. The rows will be time points
        @param: storm_data: Multiindex pandas dataframe. First index is a time point, 
        second is longitude, third is latitude. The columns are the solar storm data
        @param: min_longitude: minimum longitude in degrees
        @param: max_longitude: maximum longitude in degrees
        @param: min_latitude: minimum latitude in degrees
        @param: max_latitude: maximum latitude in degrees
        @param: granularity: the step size between GPS coordinates. This parameter has a strong effect on computation time.
        The above five parameters form a grid where the magnetic field vector will be calculated for each time point
        return: pandas dataframe with the total magnetic field vector (nT) at each time (sec) and location long, lat (degrees)
    """
    longitude_vector = np.array([min_longitude, max_longitude]) # np.arange(min_longitude, max_longitude, granularity)
    latitude_vector = np.array([min_latitude, max_latitude]) # np.arange(min_latitude, max_latitude, granularity)
    time_array = storm_data["time"].to_numpy(copy=True)
    
    
    particle_density = storm_data["density"].to_numpy(dtype=float, copy=True)
    speed = storm_data["speed"].to_numpy(dtype=float, copy=True)
    Bxgsm = storm_data["Bx"].to_numpy(dtype=float, copy=True)
    Bygsm = storm_data["By"].to_numpy(dtype=float, copy=True)
    Bzgsm = storm_data["Bz"].to_numpy(dtype=float, copy=True)
    Vxgsm = storm_data["Vx"].to_numpy(dtype=float, copy=True)
    Vygsm = storm_data["Vy"].to_numpy(dtype=float, copy=True)
    Vzgsm = storm_data["Vz"].to_numpy(dtype=float, copy=True)
    dst_array = storm_data['dst'].to_numpy(dtype=float, copy=True)
    # build time, longitude, and latitude array for pandas multindex.
    length = longitude_vector.size * latitude_vector.size * time_array.size
    
    # build index 
    time_index_array = np.empty([1, length], dtype=object)[0]
    longitude_index_array = np.empty([1, length], dtype=object)[0]
    latitude_index_array = np.empty([1, length], dtype=object)[0]
    time_point = 0
    longitude_point = 0
    
    for i in range(length):
        # time should be same value up until the length of the longitude vector
        # reset longitude vector to 0 every time we reach the end of the latitude vector
        if ((i) % (latitude_vector.size)) == 0:
            if i != 0:
                
                longitude_point += 1
        if ((i) % (longitude_vector.size * latitude_vector.size)) == 0:
            if i != 0:
                time_point += 1
                longitude_point = 0
        
        time_index_array[i] = str(time_array[time_point])
        
        longitude_index_array[i] = str(longitude_vector[longitude_point])
        # repeatedly copy the longitude and latitude points to the index array
        latitude_index_array[i] = str(latitude_vector[i % latitude_vector.size])
    

    index = [time_index_array, longitude_index_array, latitude_index_array]
    
    index = pd.MultiIndex.from_arrays(index, names=["time", "longitude", "latitude"])
    data_dict = {"Bx":np.zeros(length), "By": np.zeros(length), "Bz": np.zeros(length)}
    data = pd.DataFrame(data_dict, index=index)
    # data is a triple indexed pandas dataframe with magnetic field vectors zeroed
    data.dropna(inplace=True)
    

    time_array_minutes = np.zeros(time_array.size)
    for i in range(time_array.size):
        time_array_minutes[i] = time_array[i] / 60
    
    for t in range(1, time_array_minutes.size):
        dst = dst_array[t-1]
        
        for long in range(longitude_vector.size):
            for lat in range(latitude_vector.size):
                # The W functions integrate to the current time point so the array should stop with the current time
                
                Bx, By, Bz = calculateBField(time_array_minutes[:t], particle_density[:t], speed[:t], Bxgsm[:t], Bygsm[:t], Bzgsm[:t], Vxgsm[t-1], Vygsm[t-1], Vzgsm[t-1], longitude_vector[long], latitude_vector[lat], dst)
                
                data.loc[(str(time_array[t]), str(longitude_vector[long]), str(latitude_vector[lat])), 'Bx'] = Bx
                data.loc[(str(time_array[t]), str(longitude_vector[long]), str(latitude_vector[lat])), 'By'] = By
                data.loc[(str(time_array[t]), str(longitude_vector[long]), str(latitude_vector[lat])), 'Bz'] = Bz
                
    data = data.loc[(data!=0).any(axis=1)]
    return data

