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
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


fromBk_folder = os.path.join(os.getcwd(), "DA_OD", "FROM-BK")
result_path = os.path.join(os.getcwd(), "DA_OD", "Paths")
for fromBk_file in os.listdir(fromBk_folder):
    fromBk_data = pd.read_csv(os.path.join(fromBk_folder, fromBk_file))

    path_dict = dict()
    for index, row in fromBk_data.iterrows():
        if row["id"] in path_dict:
            path_dict[row["id"]].append(row["destination"])
        else:
            path_dict[row["id"]] = ["Bangkok"]
            path_dict[row["id"]].append(row["destination"])

    for prov, path in path_dict.items():
        path_dict[prov] = listUniqify(path)

    with open(os.path.join(result_path, "paths_"+fromBk_file.split("_")[2][:-4] + ".json"), 'w') as fp:
        json.dump(path_dict, fp)
