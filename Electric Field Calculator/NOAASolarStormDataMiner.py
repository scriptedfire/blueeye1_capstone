
import urllib.request
import json
import pandas as pd
import os
from dateutil import parser
import numpy as np
import time

start = time.time()

# Author: Stephen Hurt
# email:  stephenhurt99@tamu.edu
# This script pulls solar storm data from NOAA for the past seven days and outputs the data in a pandas dataframe.
# It also outputs the data in a .csv file

# https://services.swpc.noaa.gov/products/geospace/propagated-solar-wind.json

URL_STORM_DATA = r"https://services.swpc.noaa.gov/products/geospace/propagated-solar-wind.json"

URL_DST = r"https://services.swpc.noaa.gov/json/geospace/geospace_dst_7_day.json"

FILE_Path = r"C:\\Users\\steph\\GitHub\\blueeye1_capstone\\Electric Field Calculator"

def json_dst_to_pandas(json_object:object) -> pd.DataFrame:
    "json object of dst data to a pndas dataframe for NOAA geospace_dst file"
    #json_object = open(filename)
    #plasma_data = json.load(json_object)
    
    data_dict = {"time":[], "Dst":[]}

    for i, dict in enumerate(json_object):
        
        data_dict["time"].append(dict["time_tag"])
        data_dict["Dst"].append(dict["dst"])
    return pd.DataFrame(data_dict, columns=["time", "Dst"])

def json_storm_data_to_pandas(storm_data:object) -> pd.DataFrame:
    """convert json file of predicted storm data to pandas dataframe"""
    
    #storm_data = json.load(json_object)
    
    data_dict = {"time":[],"speed":[], "density":[], "Vx":[], "Vy":[], "Vz":[], "Bx":[], "By": [], "Bz":[]}

    for i, array in enumerate(storm_data):
        if i == 0:
            continue
        data_dict["time"].append(array[11])
        data_dict["speed"].append(array[1])
        data_dict["density"].append(array[2])
        data_dict["Bx"].append(array[4])
        data_dict["By"].append(array[5])
        data_dict["Bz"].append(array[6])
        data_dict["Vx"].append(array[8])
        data_dict["Vy"].append(array[9])
        data_dict["Vz"].append(array[10])
    
    return pd.DataFrame(data_dict, columns=["time","speed", "density", "Vx", "Vy", "Vz", "Bx", "By", "Bz"])

def storm_data_to_csv(df:pd.DataFrame, file_path) -> None:
    """convert dataframe of predicted storm data to csv"""
    
    start_time = str(parser.parse(df["time"].iloc[0]))
    end_time = str(parser.parse(df["time"].iloc[-1]))
    start_time = start_time[:10] + '-' + start_time[11:13] + start_time[14:16] + start_time[17:]
    end_time = end_time[:10] + '-' + end_time[11:13] + end_time[14:16] + end_time[17:]
    

    file_name = 'Predicted_storm_data_' + start_time + '_' + end_time + '.csv'

    file_path = file_path + os.path.sep + file_name
    
    df.to_csv(file_path)
    return None

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
        
        if parser.parse(row['time']).timestamp() < parser.parse(data['time'].iloc[0]).timestamp():# parser.parse(data['time'].iloc[0]).timestamp():
            dst.drop(dst.index[i - j], inplace=True)
            j += 1
        elif parser.parse(row['time']).timestamp() > parser.parse(data['time'].iloc[-1]).timestamp(): #parser.parse(data['time'].iloc[-1]).timestamp():
            
            dst.drop(dst.index[i - j], inplace=True)
            j += 1
    dst.reset_index(inplace=True)
    dst_array = np.zeros(data.index.size)
    time_slot = 0
    
    for i, row in data.iterrows():
        
        if parser.parse(row['time']).timestamp() > parser.parse(dst['time'].iloc[time_slot]).timestamp(): # parser.parse(row['time']).timestamp()
                        time_slot += 1
        # if the storm data extends past known dst data, use the most recent
        if time_slot >= dst["Dst"].index.size:
            time_slot = dst["Dst"].index.size - 1
        dst_array[i] = dst['Dst'].iloc[time_slot]

    data['dst'] = dst_array
    return data



def data_scraper(start_date:str, file_path:str = None) -> pd.DataFrame:
    """This is the function that will be called to run the data scraper
        @param: start_date: beggining date and time for which data is requested in UTC. 
        Must be more recent than 7 days and before the most distant prediction
        @param: file_path: folder where the scraped data can be saved in a csv file
        return: pandas data from with the storm data including the dst index.
    """
    start_date = parser.parse(start_date).timestamp()
    count = 0
    max_attempts = 1000
    error = 'no error'
    while count < max_attempts:
        try:
            r_storm_data = urllib.request.urlopen(URL_STORM_DATA)
            r_dst_index = urllib.request.urlopen(URL_DST)
            break
        except Exception as e:
             error = str(e) + f" maximum, {max_attempts}, attemps exceeded when requesting data from NOAA"
             count += 1
    if count >= max_attempts:
         return error
    storm_data = json.load(r_storm_data)
    dst = json.load(r_dst_index)
    dst_df = json_dst_to_pandas(dst)
    storm_data_df = json_storm_data_to_pandas(storm_data)
    
    data = storm_data_dst_merge(storm_data_df, dst_df)
    j = 0
    
    for i, row in data.iterrows():
        current_time = parser.parse(row['time']).timestamp()
        if current_time < start_date:
            data.drop(data.index[i - j], inplace=True)
            j += 1
    data.reset_index(inplace=True)
    data.drop(data.columns[0], axis=1, inplace=True)

    # create file with the data if a file path is given
    if file_path:
        storm_data_to_csv(data, file_path)
    
    return data
begin = "2023-03-15 00:02:00"
print(data_scraper(begin, FILE_Path))

finish = time.time()

print("runtime = ", finish - start)