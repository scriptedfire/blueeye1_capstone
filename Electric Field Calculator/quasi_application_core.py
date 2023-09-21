
import ElectricFieldPredictor
import time
from datetime import datetime
import NOAASolarStormDataMiner
from dateutil import parser
import pandas as pd
start = time.time()
# current_time = time.localtime()
current_time = datetime.utcnow() # time.gmtime()
current_time = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
print(current_time)

FILE_Path = r"C:\\Users\\steph\\GitHub\\blueeye1_capstone\\Electric Field Calculator"
# set begin date to pass to NOAA date miner
begin = current_time #"2023-09-16 00:00:00 UTC"
file = open('log_file.txt','a')
#print(parser.parse(begin).timestamp())
storm_data, valid_check = NOAASolarStormDataMiner.data_scraper(begin, file, FILE_Path)
print('\n',"              Solar Storm Data\n")
print("Data is bad: ", valid_check, '\n')
print(storm_data, flush=True)

print('\n')
#print("storm data time = ", time.time() - start)
res_data = pd.read_csv('data\piedmont conductivity.csv')

data = ElectricFieldPredictor.ElectricFieldCalculator(res_data, storm_data, -109, -102, 37, 41, file)
print('\n',"              Electric Field Data\n")
print(data, flush=True)

print("total runtime = ", time.time() - start)
