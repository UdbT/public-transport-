## Step 3
# Province counting
import os
import json
import pandas as pd
from collections import Counter

province_count = Counter()
fromBk_folder = os.path.join(os.getcwd(), "DA_OD", "FROM-BK")
for fromBk_file in os.listdir(fromBk_folder):
    print(fromBk_file)
    fromBk = pd.read_csv(os.path.join(fromBk_folder, fromBk_file))
    fromBk = fromBk.drop_duplicates(keep='first', subset=['id', 'destination'])
    province_count_tmp = fromBk.groupby("destination").size().astype(int)
    province_count = province_count + Counter(dict(province_count_tmp))

for key in province_count:
    province_count[key] = int(province_count[key])

with open(os.path.join(os.getcwd(), "province-count.json"), 'w') as fp:
    json.dump(province_count, fp)