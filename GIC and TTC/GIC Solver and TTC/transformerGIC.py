import pandas as pd

branch_data = {}
branch_data[(1, 2, 1)] = {"has_trans" : True, 'type': 'GSU', 'time': [], 'GICs':[], 'temp': 50, 'warning_time': 126}
branch_data[(1, 4)] = {"has_trans" : True, 'type': 'GSU', 'time': [], 'GICs':[]}

bus_data = {}
bus_data[1] = {"sub_num" : 1}

sub_data = {}
sub_data[1] = {"grounding_resistance" : None}

for branch in branch_data:
    print(branch_data[branch])
