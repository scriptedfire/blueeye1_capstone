import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# author: Kevin Masters
# email: kmmasters@tamu.edu
# this script calculates the heat up in the structural elements of transformers (tie bars)
# this script models the heat up of 42 transformer models
# the information for these models and the equation used for the calculations are described
# in the EPRI papers, the pdf versions of which are contained within the same folder as this script
# after calculating the heat up, this script then generates a warning if the transformer will hit a critical temperature
# the heat up data and the warnings are outputted as csv files

# critical data:
# gic flow
# Transformer type/data
# need to know windings, metallic parts oil
# move from this to XFMR thermal model
# get hot spot temperature

# Transformer thermal model equation
# define (2 tau / delta t) as alpha, tau is thermal time constant, delta t is change in time
# y(k+1) = (K / (1 + alpha))*(x(k) + x(k+1)) - ((1 - alpha)/(1 + alpha))*y(k)
# y(k + 1) = hot spot rise
# x(k) = past input temp
# x(k+1) = current temp
# K = steady-state temperature / input gic current
# K is dependant upon transformer model

# Total hotspot temperature must also account for top oil temperature
# THS = theta_TO + y(k +1)
# theta_TO = top oil temperature

# to validate, compare plots with EPRI plots

# Prior to integration, will use local csv file for GIC data
# Format of GIC data: time, Amps
# to validate against EPRI models file will be time variable and go from 10A, 20A, 40A, 50A, 100A, 200A over 6 hours

# creating a function to put pertinent data from csv files into arrays which are used for the calculations
# same function from GIC Solver


def csv_to_array(filename):

    df = pd.read_csv(filename)
    # reading in the csv file using pandas
    # putting this into a dataframe

    array = df.to_numpy()
    # converting the dataframe to a numpy array

    # returning the numpy array
    return array

def log_message(message):
    # function to create a log file
    log_file = 'TTC_log.txt'
    with open(log_file, 'a') as file:
        file.write(message + '\n')

def hs_temp_rise_calculation(Iss, Tss, tau, GIC_data):
    # this function is the crux of this program
    # Iss is the steady state current value, e.g. 10A, 20A, etc.
    # Tss is the steady state temperature
    # Tss is different for each transformer model
    # tau is different for the different tie bar designs
    # y(k) = (1 / (1 + (2tau/deltat)) * (x(k-1) + x(k)) - ((1 - (2tau/deltat)) / (1 + (2tau/deltat))) * y(k-1)
    # reformatting heat rise equation for simpler coding in python
    # original equation y(k+1) = (K / (1 + alpha))*(x(k) + x(k+1)) - ((1 - alpha)/(1 + alpha))*y(k)
    # define (2 tau / delta t) as alpha, tau is thermal time constant, delta t is change in time
    # the K value is taken care of through the np.interpolation
    # must use interpolation function in numpy

    Current = np.zeros(np.shape(GIC_data)[0])
    # creating an array to hold only the current values from the GIC_data array
    # will use this for interpolation
    # this interpolation eliminates the variable K, but is also very necessary for when the current inputted isn't
    # exactly the same as what the EPRI study uses
    # for example, the interpolation function will be able to find the steady state temperature for an input of 8A

    for i in range(np.shape(GIC_data)[0]):
        Current[i] = GIC_data[i][1]
        # using a for loop to fill the empty array with the current values in the GIC_data array
    x = np.interp(Current, Iss, Tss)
    # creating a new array that interpolates the currents with the steady state current and steady state temp
    y = np.zeros((np.shape(GIC_data)[0], 2))
    # creating an array of zeros to hold the heat up info
    # can be assumed that y(0) = 0 with the EPRI models
    # this assumption/code may need to be updated after integration
    # format of array: time, heat up in Kelvin
    for i in range(1, np.shape(GIC_data)[0]):
        # since the equation is a difference equation and assumes y(0) = 0, starting from index 1
        # this helps avoid indexing out of range
        # for loop is used to cycle through the current inputs
        delta_time = GIC_data[i][0] - GIC_data[i - 1][0]
        # defining delta_time as the difference between time at i and time at i - 1
        # delta_time with the EPRI model is always 1 min, but this will be important after integration
        y[i][1] = ((1 / (1 + ((2 * tau) / delta_time))) * (x[i - 1] + x[i])) - (
                    (1 - ((2 * tau) / delta_time)) / (1 + ((2 * tau) / delta_time)) * y[i - 1][1])
        # finding the heat up using previously discussed equation
        # storing in array
        y[i][0] = GIC_data[i][0]
        # storing the corresponding timestamp
        # returning array
    return y

def transformer_thermal_capacity_t(GIC_array:np.array, types: str) -> [pd.DataFrame, pd.DataFrame]:
    # using local csv files to validate subsystem
    # after integration, this data will come from the application core

    
    # this array holds the data on the current flowing into the transformer
    # format of array: time, current (A)
    # this array follows what was inputted for the EPRI study: 10, 20, 40, 50, 100, 200 (A) each for 60 min

    # focusing on structural models as these are much more likely to overheat
    # the EPRI study tests 2 tie bar designs for 42 different transformer models
    # all 42 transformers and both tie bar designs can be modeled using this code for a total of 84 models
    # EPRI defines two design types with different tau values
    # design 1 tau = 4 min
    # design 2 tau = 8 min
    # for total heat assume ambient temp is 40 degrees Celsius
    # Assume top oil temp is constant

    # Design1_array = csv_to_array("EPRI Tie Bar Design 1 SS Values.csv")

    # this array holds the steady state temperatures, in Kelvin, for the design 1 tie bar transformers
    # the steady state temperatures (Tss) correspond to the above stated dc current levels
    # the heat up to steady state temperature is non-linear
    # format of array: transformer name, 0A Tss (always 0), 10A Tss, 20A Tss, 40A Tss, 50A Tss, 100A Tss, 200A Tss

    Design2_array = csv_to_array("EPRI Tie Bar Design 2 SS Values.csv")
    # this array holds essentially the same information as Design1_Array, but this is for tie bar design 2
    # the design 2 steady state temperatures are generally much higher than design 1
    # design 2 is much more likely to overheat than design 1

    Top_oil_array = csv_to_array("Transformer Top Oil Temp.csv")
    # this array holds the top oil temperature for the 42 different transformers
    # the EPRI study listed 90 degrees Celsius as the top oil temp for every transformer
    # this array is somewhat unnecessary to validate against EPRI heat up models, but will be needed for ECEN 404

    for i in range(np.shape(Top_oil_array)[0]):
        # for loop to convert from Celcius to Kelvin
        # temp rise temp is in K. Making top oil temp match units
        Top_oil_array[i][1] = Top_oil_array[i][1] + 273.15


    # validation criteria for modeling: 1. steady-state values of temperature for respective DC level
    # 2. trend of the thermal behavior response
    # validate against EPRI models

    # Iss array holds the steady state DC currents from EPRI models
    EPRI_Iss = np.array([0, 10, 20, 40, 50, 100, 200])

    # defining the tau values for the two tie bar designs
    # design 1 has a tau of 4 min, and design 2 has a tau of 8 min
    tau_1 = 4
    tau_2 = 8

    # the temperature limit before damage for structural elements of a transformer is 200 C/473.15 K
    # using the temperature limit in Kelvin to match heat up units
    temperature_limit = 473.15

    # will create a 3d array to hold all the transformer heat up data

    # creating an empty dictionary to store the heatup arrays
    heatup_dict = {}
    warning_dict = {}

    if types.lower() == 'auto':
        trans_num = 10
    else:
        trans_num = 23

#    for i in range(np.shape(Design1_array)[0]):
#        # looping through all the design 1 transformer models
#        key = 'T{}, design {}'.format(i + 1, 1)
#        # creating a key based on the loop index and design number
#        try:
#            # calling function to calculate heat up
#            # using try catch to pick up errors
#            Y = hs_temp_rise_calculation(EPRI_Iss, Design1_array[i][1:8].astype(np.float32), tau_1, GIC_array)
#            log_message('Calculating heat up for ' + Design1_array[i][0] + ' Design 1')
#        except Exception as e:
#            log_message('An unexpected error occurred when calculating heat up: ' + str(e))
#        # specifying Tss from function as Design1_array[i][1:8].astype(np.float32)
#        # excluding [i][0] because that's the transformer number, not Tss data
#        # converting to floats, encountered errors when not designating the type as float32
#        # using the
#        # generating heat up array for transformer at i, e.g. T1, T2, T3, etc.
#        heatup_dict[key] = Y
#        # adding array to the dictionary with the key
#        # looping through array to see if it hits critical temperature
#        log_message('Checking if critical temperature reached for ' + Design1_array[i][0] + ' Design 1')
#        for j in range(np.shape(Y)[0]):
#            bad_temp = False
#            # creating a flag
#            if Y[j][1] + Top_oil_array[i][1] >= temperature_limit:
#                # checking if temp rise heats up to critical temperature
#                bad_temp = True
#                # setting flag true
#                warning = "WARNING: TEMPERATURE LIMIT FOR {} TIE BAR WILL BE REACHED IN {} MINUTES".format(
#                    Design1_array[i][0], Y[j][0].astype(int))
#                # creating warning variable that contains the transformer model number and the time it will hit crit
#                if key not in warning_dict:
#                    warning_dict[key] = [warning]
#                else:
#                    warning_dict[key].append(warning)
#                break
#        if not bad_temp:
#            safe = "TEMPERATURE FOR {} TIE BAR WITHIN ACCEPTABLE RANGE".format(Design1_array[i][0])
#            if key not in warning_dict:
#                warning_dict[key] = [safe]
#            else:
#                warning_dict[key].append(safe)

    # this loop does the same thing as the one above, but for the design 2 models
    # for i in range(np.shape(Design2_array)[0]):

    key = 'T{}, design {}'.format(trans_num + 1, 2)
    try:
        Y = hs_temp_rise_calculation(EPRI_Iss, Design2_array[trans_num][1:8].astype(np.float32), tau_2, GIC_array)
        log_message('Calculating heat up for ' + Design2_array[trans_num][0] + ' Design 2')
    except Exception as e:
        log_message('An unexpected error occurred when calculating heat up: ' + str(e))
    heatup_dict[key] = Y
    log_message('Checking if critical temperature reached for ' + Design2_array[trans_num][0] + ' Design 2')
    for j in range(np.shape(Y)[0]):
        # bad_temp = False
        if Y[j][1] + Top_oil_array[trans_num][1] >= temperature_limit:
            return Y[j][0].astype(int)
    return None
            # bad_temp = True
            # warning = "WARNING: TEMPERATURE LIMIT FOR {} TIE BAR WILL BE REACHED IN {} MINUTES".format(
            #     Design2_array[trans_num][0], Y[j][0].astype(int))
            # if key not in warning_dict:
            #     warning_dict[key] = [warning]
            # else:
            #     warning_dict[key].append(warning)
            # break
    # if not bad_temp:
    #     safe = "TEMPERATURE FOR {} TIE BAR WITHIN ACCEPTABLE RANGE".format(Design2_array[i][0])
    #     if key not in warning_dict:
    #         warning_dict[key] = [safe]
    #     else:
    #         warning_dict[key].append(safe)


    # Converting each 2D array in the dictionary to a dataframe
    # dfs = []
    # # creating an empty list to hold the resulting dataframes
    # for key in heatup_dict:
    #     # looping through each key in the dictionary
    #     arr = heatup_dict[key]
    #     # getting the 2D array associated with the key
    #     # reshaping the array to a 2D shape with columns matching the original array
    #     df = pd.DataFrame(arr.reshape(-1, arr.shape[-1]))
    #     # creating new column names for the dataframe based on the original key
    #     # time for column 0, temp rise for column 2
    #     df.columns = [f'{key}_time', f'{key}_temp_rise']
    #     dfs.append(df)
    #     # appending the resulting dataframe to the list
# 
    # total_heatup = pd.concat(dfs, axis=1)
    # # concatenating the list of dataframes into a single dataframe along the columns (axis=1) dimension
# 
    # # exporting as a csv
    # total_heatup.to_csv('total_heatup.csv', index=False)
    # log_message('Exporting heat up data')
# 
    # # creating lists for the keys and values from the warning dictionary
    # # using these to have better formatting with the exported csv
    # keys_list = list(warning_dict.keys())
    # values_list = list(warning_dict.values())
# 
    # # creating a dataframe from the keys and values in the warning dictionary
    # warning_df = pd.DataFrame({'Transformer': keys_list, 'Warning': values_list})
    # # exporting as a csv
    # warning_df.to_csv('warnings_generated.csv', index=False)
    # log_message('Exporting warning data')
# 
    # return warning_df

def make_gic_time(time: np.array, gics:np.array) -> np.array:
    
    time_gic = np.zeros((time.size, 2))
    for i in range(time.size):
        time_gic[i][0] = time[i]
        time_gic[i][1] = gics[i]
    return time_gic


def transformer_thermal_capacity(branch_data:dict) -> dict:
    
    
    for branch in branch_data:
        transformer = branch_data[branch]
        if not transformer["has_trans"]:
            continue
        gic_time = make_gic_time(branch_data[branch]['time'], branch_data[branch]['GICs'])
        branch_data[branch]['warning_time'] = transformer_thermal_capacity_t(gic_time, branch_data[branch]['type'])

    return branch_data

if __name__ == '__main__':
    gic_time = csv_to_array("TTC GIC Data.csv")
    gic_array = np.zeros(gic_time.shape[0])
    time_array = np.zeros(gic_time.shape[0])
    for i in range(gic_time.shape[0]):
        gic_array[i] = gic_time[i][1]
        time_array[i] = gic_time[i][0]
    

    branch_data = {}
    branch_data[(1, 2, 1)] = {"has_trans" : True, 'type': 'GSU', 'time': time_array, 'GICs': gic_array, 'warning_time': None}
    print(transformer_thermal_capacity(branch_data))
