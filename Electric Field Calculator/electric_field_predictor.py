
import numpy as np
from math import *
import pandas as pd

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
    kn = np.sqrt(1j * mu0 * omega * sigma)
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

    Zi = 1j * omega * mu0 * ((1 - rn * exp(- 2 * kn * d))/ 
                             (1 + rn * exp(- 2 * kn * d)))
    return Zi

def impedance_calculator(conductivty_model:pd.DataFrame, omega:float) -> float:
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
    conductivity_vector = conductivty_model['sigma'].to_numpy(dtype=float)
    depth_vector = conductivty_model['d'].to_numpy(dtype=float)

    # begin recursive calculation of the impedance at the surface in a for loop
    length = conductivty_model.size
    # initialize final impedance value
    impedance = 0
    for i in range(length):
        # iterate from the bottom up
        j = length - 1 - i
        if i == 0: # if i == 0, we need the special case where we are at the last layer
            impedance = Z_final(omega, conductivity_vector[j])
            continue
        # recursive relation to calculate impedance at the surface
        impedance = Zi(omega, conductivity_vector[j], r(omega,conductivity_vector[j], impedance))
    
    return impedance


