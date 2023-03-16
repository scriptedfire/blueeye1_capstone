from geopack import t04, gpack
import numpy as np
from numpy.linalg import inv
import pandas as pd
from math import *
from datetime import datetime,timezone
import time
from dateutil import parser
import json
from dateutil.tz import UTC

start = time.time()

""" 
    Author: Stephen Hurt
    email: stephenhurt99@tamu.edu
    This script implements a predictive model of the earth's magnetic field 
    described in the documentation below and papers referenced therein. This paper is hereafter refered to as [1]
    documentation
        [1] N. A. Tsyganenko and M. I. Sitnov, Modeling the dynamics of the inner magnetosphere during
            strong geomagnetic storms, J. Geophys. Res., v. 110 (A3), A03208, doi: 10.1029/2004JA010798, 2005."""

"""Notes:
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

def Pdyn(rhoP: float, velocity: float) -> float:
    """ This function calculates the solar wind dynamic pressure given the particle density, and solar wind speed
        @param: rhoP: particle density in 1/cm^3
        @param: velocity: solar wind speed in km/s
        return: dynamicPressure_nP
    """
    SOLAR_WIND_MASS = 2.3212 * 10 ** -27 #kg

    speed_ms = velocity * 1000 # m/s
    rho_m3 = rhoP * 100 **3 # 1/m^3
    rho = rho_m3 * SOLAR_WIND_MASS # mass desnsity of the solar wind

    dynamicPressure = rho * (speed_ms ** 2) # Pascals

    dynamicPressure_nP = dynamicPressure * 10 ** 9 # nano Pascals
    return dynamicPressure_nP


def Sk(N: float, V: float, B : float, lamb: float, beta: float, gamma: float) -> float:
    """This function is a subroutine of the Wi functions. It calculates a subfunciton of the sum computed in each function.
        @param: N: solar wind density
        @param: V: solar wind speed
        @param: B: magnitude of the southward component of the IMF
        @param: lamb: fitting parameter
        @param: beta: fitting parameter
        @param: gamma: fitting parameter
        :return scalar solution 
        
    """
    S = (N/5)**lamb
    S = S * (V/400)**beta
    S = S * (B/5)**gamma
    return S

def Wt1(t : np.array, N : np.array, V : np.array, B : np.array, resolution = 5) -> float:
    """ This method computes a component of the scalar coefficient 
        of the first component of the tail B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        @param: resolution: this is the resolution of the data passed in. i. e the time between measurements. The default is 5 minutes as in [1]
          
    """

    # fitting constants from [1]
    R = 0.39 
    GAMMA = 0.87
    BETA = 0.8
    LAMB = 0.39
    # initialize W and comput the numerical integral over t
    Wt1 = 0
    for k in range(t.size - 1):
        Wt1 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wt1 = Wt1 * (R/normR)
    return Wt1

def Wt2(t : np.array, N : np.array, V : np.array, B : np.array, resolution = 5) -> float:
    """ This method computes a component of the scalar coefficient 
        of the second component of the tail B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        @param: resolution: this is the resolution of the data passed in. i. e the time between measurements. The default is 5 minutes as in [1]
          
    """

    # fitting constants from [1]
    R = 0.7 
    GAMMA = 0.67
    BETA = 0.18
    LAMB = 0.46
    # initialize W and comput the numerical integral over t
    Wt2 = 0
    for k in range(t.size - 1):
        Wt2 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wt2 = Wt2 * (R/normR)
    return Wt2


def Ws3(t : np.array, N : np.array, V : np.array, B : np.array, resolution = 5) -> float:
    """ This method computes a component of the scalar coefficient 
        of the symetric ring current B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        @param: resolution: this is the resolution of the data passed in. i. e the time between measurements. The default is 5 minutes as in [1]
          
    """

    # fitting constants from [1]
    R = 0.031 
    GAMMA = 1.32
    BETA = 2.32
    LAMB = 0.39
    # initialize W and comput the numerical integral over t
    Ws3 = 0
    for k in range(t.size - 1):
        Ws3 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Ws3 = Ws3 * (R/normR)
    return Ws3

def Wp4(t : np.array, N : np.array, V : np.array, B : np.array, resolution = 5) -> float:
    """ This method computes a component of the scalar coefficient 
        of the first component of the tail B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        @param: resolution: this is the resolution of the data passed in. i. e the time between measurements. The default is 5 minutes as in [1]
          
    """

    # fitting constants from [1]
    R = 0.58 
    GAMMA = 1.29
    BETA = 1.25
    LAMB = 0.42
    # initialize W and comput the numerical integral over t
    Wp4 = 0
    for k in range(t.size - 1):
        Wp4 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wp4 = Wp4 * (R/normR)
    return Wp4


def Wr5(t : np.array, N : np.array, V : np.array, B : np.array, resolution = 5) -> float:
    """ This method computes a component of the scalar coefficient 
        of the first component of the Birkeland Current B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        @param: resolution: this is the resolution of the data passed in. i. e the time between measurements. The default is 5 minutes as in [1]
          
    """

    # fitting constants from [1]
    R = 1.15
    GAMMA = 0.69
    BETA = 1.6
    LAMB = 0.41
    # initialize W and comput the numerical integral over t
    Wr5 = 0
    for k in range(t.size - 1):
        Wr5 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wr5 = Wr5 * (R/normR)
    return Wr5

def Wr6(t : np.array, N : np.array, V : np.array, B : np.array, resolution = 5) -> float:
    """ This method computes a component of the scalar coefficient 
        of the second component of the Birkeland Current B field of Eqaution 5 in [1]
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        @param: resolution: this is the resolution of the data passed in. i. e the time between measurements. The default is 5 minutes as in [1]
          
    """

    # fitting constants from [1]
    R = 0.88
    GAMMA = 0.53
    BETA = 2.4
    LAMB = 1.29
    # initialize W and comput the numerical integral over t
    Wr6 = 0
    for k in range(t.size - 1):
        Wr6 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size - 1]))
    normR = 60 / resolution
    Wr6 = Wr6 * (R/normR)
    return Wr6

def GPS_to_cartesian(longitude:float, latitude:float, elevation:float = 0) -> list:
    """Converts gps coordiantes to geocentric cartesian coordinates in earth radii
        elevations assumed to be in feet
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
        This function calls the west and south direction negative"""

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
    #print(T_matrix)
    e, n, u = np.matmul(T_matrix, Bgeo)
    return e, n, u

def calculateSouthBField(Bxgsm: np.array, Bygsm: np.array, Bzgsm:np.array, theta:float, srasn:float, sdec:float) -> np.array:
    """ This function return an array of the magnitude of the southward components of the interplanetary magnetic field (IMF)
        @param: Bxgsm: x component of the IMF in gsm coordinates
        @param: Bygsm: y component of the IMF in gsm coordinates
        @param: Bzgsm: z component of the IMF in gsm coordinates
        @param: theta: Greenwhich Mean Sidereal time.
        @param: srasn: right ascension of the sun (radians)
        @param: sdec: declination of the sun (radians)
        return: southern component of the IMF relative to the dipole
    """
    Bsouth = np.zeros(Bxgsm.size)
    for i in range(Bxgsm.size):
        Bgeo = gpack.geogsm(Bxgsm[i], Bygsm[i], Bzgsm[i], -1)
        Bgeo = gpack.geomag(Bgeo[0], Bgeo[1], Bgeo[2], 2)
        Bsouth[i] = abs(Bgeo[2])
    return Bsouth


def json_plasma_to_pandas(filename:str) -> pd.DataFrame:

    json_object = open(filename)
    plasma_data = json.load(json_object)
    
    data_dict = {"time":[], "density":[], "speed": []}

    for i, array in enumerate(plasma_data):
        if i == 0:
            continue
        data_dict["time"].append(array[0])
        data_dict["density"].append(array[1])
        data_dict["speed"].append(array[2])
    return pd.DataFrame(data_dict, columns=["time", "density", "speed"])


def json_mag_to_pandas(filename:str) -> pd.DataFrame:

    json_object = open(filename)
    plasma_data = json.load(json_object)
    
    data_dict = {"time":[], "Bx":[], "By": [], "Bz":[]}

    for i, array in enumerate(plasma_data):
        if i == 0:
            continue
        data_dict["time"].append(array[0])
        data_dict["Bx"].append(array[1])
        data_dict["By"].append(array[2])
        data_dict["Bz"].append(array[3])
    return pd.DataFrame(data_dict, columns=["time", "Bx", "By", "Bz"])

def json_dst_to_pandas(filename:str) -> pd.DataFrame:

    json_object = open(filename)
    plasma_data = json.load(json_object)
    
    data_dict = {"time":[], "Dst":[]}

    for i, array in enumerate(plasma_data):
        if i == 0:
            continue
        data_dict["time"].append(array[0])
        data_dict["Dst"].append(array[1])
    return pd.DataFrame(data_dict, columns=["time", "Dst"])

def mag_plasma_merge(mag:pd.DataFrame, plasma:pd.DataFrame) -> pd.DataFrame:
    to_mag = mag["time"][0]
    to_plasma = plasma["time"][0]

    to_mag = parser.parse(to_mag).timestamp()
    to_plasma = parser.parse(to_plasma).timestamp()

    # correct misalignment in time stamps
    if to_mag < to_plasma:
        difference = (to_plasma - to_mag) / 60
        difference = int(round(difference, 0))
        plasma.index += difference
    else:
        difference = (to_mag - to_plasma) / 60
        difference = int(round(difference, 0))
        mag.index += difference
    df = mag
    df["density"] = plasma["density"]
    df["speed"] = plasma["speed"]
    # return data frame and erase missing data
    
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df

def storm_data_dst_merge(data:pd.DataFrame, dst:pd.DataFrame) -> pd.DataFrame:
    """ This function merges the storm data with the dst. 
        This is complicated by the fact that dst data is much lower in granularity
        @param: data: storm data
        @param: dst: dataframe of dst indecies with time stamps
        return: merged dataframe
    """
   
    j = 0
    # loop through the dst data frame and delete the times that are outside of the storm time
    for i, row in dst.iterrows():
        
        if parser.parse(row['time']).timestamp() < data['time'].iloc[0]:# parser.parse(data['time'].iloc[0]).timestamp():
            dst.drop(dst.index[i - j], inplace=True)
            j += 1
        elif parser.parse(row['time']).timestamp() > data['time'].iloc[-1]: #parser.parse(data['time'].iloc[-1]).timestamp():
            
            dst.drop(dst.index[i - j], inplace=True)
            j += 1
    dst.reset_index(inplace=True)
    dst_array = np.zeros(data.index.size)
    time_slot = 0
    
    for i, row in data.iterrows():
        
        if row['time'] + 3600 > parser.parse(dst['time'].iloc[time_slot]).timestamp(): # parser.parse(row['time']).timestamp()
                        time_slot += 1
        # if the storm data extends past known dst data, use the most recent
        if time_slot >= dst["Dst"].index.size:
            time_slot = dst["Dst"].index.size - 1
        dst_array[i] = dst['Dst'].iloc[time_slot]

    data['dst'] = dst_array
    return data



def calculateBField(t: np.array, N: np.array, V: np.array, Bxgsm: np.array, Bygsm: np.array, Bzgsm: np.array, longitudeCBF: float, latitudeCBF: float, dst: float, resolution = 5) -> list:
    """ This function calculates and returns the magnetic field vector at a given time point which is the last time point in the t array
        
        @param: t: numpy array of time points where the first value is at the beginning of a solar storm
        @param: N: numpy array that is the same length as t that has the solar wind density corresponding to the time point in t
        @param: V: numpy array that is the same length as t that has the solar wind speed corresponding to the time point in t
        @param: B: numpy array that is the same length as t that has the southward component of the IMF corresponding to the time point in t
        @param: Bxgsm: x component of the interplanetary magnetic field (IMF) in gsm coordinates
        @param: Bygsm: y component of the interplanetary magnetic field (IMF) in gsm coordinates
        @param: Bzgsm: z component of the interplanetary magnetic field (IMF) in gsm coordinates
        @param: longitude: float of the longitude where the B field is being evaluated
        @param: latitude: float of the longitude where the B field is being evaluated
        @param: dst: most recent dst index in nT
        @param: resolution: this is the resolution of the data passed in. i. e the time between measurements. The default is 5 minutes as in [1]
        return: Bxgeo, Bygeo, Bzgeo predicted magnetic field vector
    """
    psi = gpack.recalc(t[-1], V[-1])
    gst, slong, srasn, sdec, obliq = gpack.sun(t[-1])
    B = calculateSouthBField(Bxgsm, Bygsm, Bzgsm, gst, srasn, sdec)
    
    # update current time to be the last time in the series
    
    x, y, z = GPS_to_cartesian(longitudeCBF, latitudeCBF, 5318)

    # convert geo cartesian coordinates to gsm cartesian coordinates
    xgsm, ygsm, zgsm = gpack.geogsm(x, y, z, 1)
    W1 = Wt1(t, N, V, B, resolution)
    W2 = Wt2(t, N, V, B, resolution)
    W3 = Ws3(t, N, V, B, resolution)
    W4 = Wp4(t, N, V, B, resolution)
    W5 = Wr5(t, N, V, B, resolution)
    W6 = Wr6(t, N, V, B, resolution)
    
    speed = V[-1]
    pdyn = Pdyn(N[-1], speed)
    parmod = [pdyn, dst, Bygsm[-1], Bzgsm[-1], W1, W2, W3, W4, W5, W6]
    
    Bxgsm, Bygsm, Bzgsm = t04.t04(parmod, psi, xgsm, ygsm, zgsm)
    
    Bxdipole, Bydipole, Bzdipole = gpack.dip(xgsm, ygsm, zgsm)
    
    Bxgeo, Bygeo, Bzgeo = gpack.geogsm(Bxdipole + Bxgsm, Bydipole + Bygsm, Bzdipole + Bzgsm, -1) #gpack.geogsm(Bxdipole, Bydipole, Bzdipole, -1)
    # e = east component (y)
    # n = north component (x)
    # u = upward component (z)
    e, n, u = geo_to_enu(Bxgeo, Bygeo, Bzgeo, longitudeCBF, latitudeCBF)
    print("e, n, u ",e, n, u)
    print("Bxgeo, Bygeo, Bzgeo ",Bxgeo, Bygeo, Bzgeo)
    print(longitudeCBF, latitudeCBF)
    return n, e, u

def impact_time_shift(storm_data_real_time: pd.DataFrame) -> pd.DataFrame:
    """ This function takes in a pandas dataframe of real time storm data and 
        shifts the time values to the expected time when it hits Earth. 
        This assumes the data is being retrieved form 1500000 kilometers away
        @param: storm_data_real_time: pandas dataframe with real time solar data
        return: storm_data: time shifted to the conditions on earth at impact
    """ 
    distance = 1500000 #km
    storm_data = storm_data_real_time.copy(True)
    time_array = np.zeros(storm_data.index.size, dtype=object)
    
    for i, time_df in storm_data.groupby(level=0):
        # add the time it will take for the storm to hit and add to the list
        
        time_array[i] =  round(parser.parse(time_df['time'].iloc[0]).timestamp() + distance / float(time_df['speed']), 1)
        
    
    storm_data['time'] = time_array
    storm_data.sort_values('time', inplace=True)
    return storm_data

def magnetic_field_predictor(storm_data:pd.DataFrame, min_longitude:float, max_longitude: float, min_latitude:float, max_latitude:float, granularity:float) -> pd.DataFrame:
    """ Take in strom data in a pandas dataframe each column will be a different data type. The rows will be time points
        @param: storm_data: Multiindex pandas dataframe. First index is a time point, 
        second is longitude, third is latitude. The columns are the components of the IMF
        @param: min_longitude: minimum longitude in degrees
        @param: max_longitude: maximum longitude in degrees
        @param: min_latitude: minimum latitude in degrees
        @param: max_latitude: maximum latitude in degrees
        @param: granularity: the step size between GPS coordinates. This parameter has a strong effect on computation time.
        The above five parameters form a grid where the magnetic field vector will be calculated for each time point
        return: pandas dataframe with the total magnetic field vector at each time and location
    """
    #storm_data = impact_time_shift(storm_data_real_time)
    longitude_vector = np.arange(min_longitude, max_longitude, granularity)
    latitude_vector = np.arange(min_latitude, max_latitude, granularity)
    time_array = storm_data["time"].to_numpy(copy=True)
    
    # time_array = np.zeros(time_array_str.size)
    #for i in range(time_array.size):
    #    time_point = parser.parse(time_array_str[i])
    #    time_array[i] = time_point.timestamp()
    particle_density = storm_data["density"].to_numpy(dtype=float, copy=True)
    speed = storm_data["speed"].to_numpy(dtype=float, copy=True)
    Bxgsm = storm_data["Bx"].to_numpy(dtype=float, copy=True)
    Bygsm = storm_data["By"].to_numpy(dtype=float, copy=True)
    Bzgsm = storm_data["Bz"].to_numpy(dtype=float, copy=True)
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
    
    resolution = time_array_minutes[1] - time_array_minutes[0]

    for t in range(1, time_array_minutes.size):
        dst = dst_array[t]
        
        for long in range(longitude_vector.size):
            for lat in range(latitude_vector.size):
                # The W functions integrate to the current time point so the array should stop with the current time
                
                Bx, By, Bz = calculateBField(time_array_minutes[:t], particle_density[:t], speed[:t], Bxgsm[:t], Bygsm[:t], Bzgsm[:t], longitude_vector[long], latitude_vector[lat], dst, resolution)
                
                data.loc[(str(time_array[t]), str(longitude_vector[long]), str(latitude_vector[lat])), 'Bx'] = Bx
                data.loc[(str(time_array[t]), str(longitude_vector[long]), str(latitude_vector[lat])), 'By'] = By
                data.loc[(str(time_array[t]), str(longitude_vector[long]), str(latitude_vector[lat])), 'Bz'] = Bz
               

    return data

# test geogsm
long = -105
lat = 80


print(geo_to_enu(-5687.808696521344, -5704.456296717376, 29950.32399670261, long, lat))

#xgeo, ygeo, zgeo = GPS_to_cartesian(long, lat)
#print(xgeo, ygeo, zgeo)
#utc = '03/16/2023  04:12:00 UTC'
#utc = parser.parse(utc).timestamp()
#print(utc)
#gpack.recalc(utc)
#
#xgsm, ygsm, zgsm = gpack.geogsm(xgeo, ygeo, zgeo, 1)
#print(xgsm, ygsm, zgsm)

plasma = json_plasma_to_pandas("plasma-1-day_test.json")
mag = json_mag_to_pandas("mag-1-day_test.json")
dst = json_dst_to_pandas("kyoto-dst-0314.json")
recent_dst = float(dst["Dst"][len(dst.index) - 1])

storm_data = mag_plasma_merge(mag, plasma)

storm_data_with_offset = impact_time_shift(storm_data)


storm_data_with_dst = storm_data_dst_merge(storm_data_with_offset, dst)


low_gran_storm_data = storm_data_with_dst.copy(True)
j = 0
for i in range(storm_data_with_dst.index.size):
    if i% 5 != 0:
        low_gran_storm_data.drop(low_gran_storm_data.index[i - j], inplace=True)
        j += 1

low_gran_storm_data.reset_index(inplace=True)



data = magnetic_field_predictor(low_gran_storm_data, -105, -104, 40, 41, 0.5)

print(data)

data.to_csv("data03142023_low_res_enu.csv")

finish = time.time()

print("runtime = ", finish - start)

