
import ElectricFieldPredictor
import time
import NOAASolarStormDataMiner
from dateutil import parser
import pandas as pd
start = time.time()

FILE_Path = r"C:\\Users\\steph\\GitHub\\blueeye1_capstone\\Electric Field Calculator"
begin = "2023-04-26 00:00:00 UTC"
file = open('log_file.txt','a')
#print(parser.parse(begin).timestamp())
storm_data = NOAASolarStormDataMiner.data_scraper(begin, file, FILE_Path)
print('\n',"              Solar Storm Data\n")

print(storm_data, flush=True)

print('\n')
#print("storm data time = ", time.time() - start)
res_data = pd.read_csv('data\piedmont conductivity.csv')

data = ElectricFieldPredictor.ElectricFieldCalculator(res_data, storm_data, -105, -104, 41, 42, 0.5, file)
print('\n',"              Electric Field Data\n")
print(data, flush=True)

print("total runtime = ", time.time() - start)
