from geopack import t04, gpack
import numpy as np
import pandas as pd
from math import *
from datetime import datetime,timezone
import time
from dateutil import parser
import json
from dateutil.tz import UTC

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
    for k in range(t.size() - 1):
        Wt1 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size() - 1]))
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
    for k in range(t.size() - 1):
        Wt2 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size() - 1]))
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
    for k in range(t.size() - 1):
        Ws3 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size() - 1]))
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
    for k in range(t.size() - 1):
        Wp4 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size() - 1]))
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
    for k in range(t.size() - 1):
        Wr5 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size() - 1]))
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
    for k in range(t.size() - 1):
        Wr6 += Sk(N[k], V[k], B[k], LAMB, BETA, GAMMA) * exp((R/60)*(t[k] - t[t.size() - 1]))
    normR = 60 / resolution
    Wr6 = Wr6 * (R/normR)
    return Wr6

def GPS_to_cartesian(longitude:float, latitude:float) -> list:
    """Converts gps coordiantes to geocentric cartesian coordinates in earth radii"""

    if latitude >= 0:
        phi = np.pi/2 - np.deg2rad(latitude)
    else:
        phi = -np.deg2rad(latitude) + np.pi/2
    theta = np.deg2rad(longitude)
    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)
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




parmod = [1, 1, 1, 1 ,1 ,1 ,1 ,1 ,1 ,1]
ps = 0.5 # Diplole tilt angle in radians recalc() will return this
x,y,z = 1, 1, 1

x = t04.t04(parmod,ps,x,y,z)
#print(x)


now_utc = time.time()

theta,phi = cartesian_to_GPS(1,-1,-1)
longitude = np.rad2deg(theta)
latitude = np.rad2deg(phi)
print(longitude,latitude)

x, y, z = GPS_to_cartesian(longitude, latitude)
print(x,y,z)

#print(now_utc)
gpack.recalc(now_utc)
z = gpack.geogsm(1.01, 0, 0, -1)
print(z)

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
    return df

plasma = json_plasma_to_pandas("plasma-2-hour.json")
mag = json_mag_to_pandas("mag-2-hour.json")
dst = json_dst_to_pandas("kyoto-dst.json")
recent_dst = dst["Dst"][len(dst.index) - 1]
data = pd.concat([plasma,mag])
t = parser.parse(plasma["time"][0])
print(t)
print(t.timestamp())
print(plasma)
print(mag)
print(dst)
print(mag_plasma_merge(mag,plasma))

print(recent_dst)
time_val = ["1", "2", "3", "4"]
location = [["10", "12"], ["9", "8"], ["10", "8"], ["9", "8"]]
data_dict = {"Bx":[7, 8, 9, 7, 8, 9, 7, 8, 9, 7, 8, 9], "By": [10, 11, 12, 10, 11, 12, 10, 11, 12, 10, 11, 12], "Bz": [13, 14, 15, 13, 14, 15, 13, 14, 15, 13, 14, 15]}
temp = pd.DataFrame(data_dict)
print(temp) #"longitude": [1, 2, 3], "latitude": [4, 5, 6], 

index_temp = [["1", "1", "1", "1", "2", "2", "2", "2", "3", "3", "3", "3"],
              ["10", "10", "11", "11", "12", "12", "13", "13", "14", "14", "15", "15"],
              ["16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27"]]
#tuple_index = list(zip(*index_temp))

index = pd.MultiIndex.from_arrays(index_temp, names=["time", "longitude", "latitude"])
temp2 = pd.DataFrame(data_dict, index = index)
print(temp2)

def magnetic_field_predictor(storm_data:pd.DataFrame, min_longitude:float, max_longitude: float, min_latitude:float, max_latitude:float, granularity:float) -> pd.DataFrame:
    """ Take in strom data in a pandas dataframe each column will be a different data type. The rows will be time points
    """
    longitude_vector = np.arange(min_longitude, max_longitude, granularity)
    latitude_vector = np.arange(min_latitude, max_latitude, granularity)
    time_array = storm_data["time"].to_numpy(dtype=float, copy=True)
    particle_density = storm_data["density"].to_numpy(dtype=float, copy=True)
    speed = storm_data["speed"].to_numpy(dtype=float, copy=True)
    Bxgsm = storm_data["Bx"].to_numpy(dtype=float, copy=True)
    Bygsm = storm_data["By"].to_numpy(dtype=float, copy=True)
    Bzgsm = storm_data["Bz"].to_numpy(dtype=float, copy=True)

    # build time array for pandas multindex.
    time_length = longitude_vector.size() * latitude_vector.size() * time_array.size()
    
    time_index_array = np.zeros(time_length)
    time_point = 0
    for i in range(time_length):
        if (i + 1) % longitude_vector.size() == 0:
            count += 1
        time_index_array[i] = time_array[count]

    
    #Simf = 1
    for t, time in enumerate(storm_data["time"]):
        data_dict = {"longitude": [], "latitude": [], "Bx":[], "By": [], "Bz": []}
        for i, long in enumerate(longitude_vector):
            for j, lat in enumerate(latitude_vector):
                data_dict["longitude"] = long
                data_dict["latitude"] = lat

                w1 = Wt1()

                #data_dict["Bx"], data_dict["By"], data_dict["Bz"] = 














