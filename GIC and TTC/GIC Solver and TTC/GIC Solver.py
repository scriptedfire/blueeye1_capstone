import math
import numpy as np
import pandas as pd


# Critical data for gic calculation:
# 1. Electric field: magnitude, direction
# 2. Substation data: latitude, longitude, grounding resistance
# 3. Transmission line data: from bus, to bus, voltage (Kv-LL), Length, Resistance
# 4. Transformer data: Type (GSU, GY-GY-D, GY-GY, auto), Winding resistance (HV and LV), Bus info for end and finish

# Solve for input voltage on transmission line
# V = EnLn + EeLe; En = Northward E, Ee = Eastward E, Ln = Northward length, Le = eastward length
# need to know formatting of data, put into an array using numpy

# Ln = (111.133 - 0.56cos(2*phi))*(delta_latitude)
# delta_lat = absolute difference between latitudes
# phi = (LatA + LatB) / 2
# convert phi to radians using math
# Le = (111.5065 - 0.1872cos(2*phi))*cos(phi)*delta_long
# delta_long = absolute difference between longitudes

# need to create admittance matrix
# nodal analysis with dc models
# I_dc = V(n,m) / R_eff (V(n,m) is from line connecting bus m to n)
# G = network conductance matrix
# V = (G^-1)*I_dc

#test to confirm correct voltage

latitude_a = 60
latitude_b = 50
longitude_a = 70
longitude_b = 75

