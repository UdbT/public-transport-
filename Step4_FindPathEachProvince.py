## Step 4
# Find path from Bangkok to each province
import os
import json
import pandas as pd

def listUniqify(seq, idfun=None): 
   # order preserving
   if idfun is None:
       def idfun(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = idfun(item)
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result
   
#open provinces file
read_province = pd.read_csv(os.path.join(os.getcwd(), "thai-provinces", "thai-provinces_point.csv"))
provinces = list(read_province["province_EN"])

# Initialize province dict
pathToProv_dict = dict()
for province in provinces:
    pathToProv_dict[province] = dict()

paths_folder = os.path.join(os.getcwd(), "DA_OD", "Paths")
for path_file in os.listdir(paths_folder):
    print(path_file)
    with open(os.path.join(paths_folder, path_file), 'r') as fp:
        paths = json.load(fp)
    for index, value in paths.items():
        id_path = listUniqify(value)
        for province in provinces:
            if "Bangkok" in province: continue
            try:
                for passed_province in id_path[:id_path.index(province)+1]:
                    # print(passed_province)
                    if "NaN" in passed_province : continue

                    if passed_province in pathToProv_dict[province]:
                        pathToProv_dict[province][passed_province] += 1
                    else:
                        pathToProv_dict[province][passed_province] = 1
            except:
                pass

with open("province-paths.json", 'w') as fp:
    json.dump(pathToProv_dict, fp)