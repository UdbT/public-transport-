#Step1
import pandas as pd 
import os 
import shapefile
from shapely.geometry import Point # Point class
from shapely.geometry import shape # shape() is a function to convert geo objects through the interface

columns=['id', 'type_desc', 'kind_desc', 'subkind_desc', 'seat', 'weight','traveltime', 'km', 'ts1', 'lat1', 'lon1', 'ts2', 'lat2', 'lon2']
table_oddata = pd.DataFrame(columns=columns)

print("Read Shape file")
shp = shapefile.Reader(os.path.join(os.getcwd(), "thai-provinces", "tha_admbnda_adm1_rtsd_20190221.shp")) #open the shapefile
all_shapes = [shape(_shape) for _shape in shp.shapes()] # get all the polygons
all_records = shp.records()
print("Done")

def checkBangkok(row):
    # print(row)
    point = (row[1],row[0])
    for i in range(len(all_shapes)):
        boundary = all_shapes[i] # get a boundary polygon
        if Point(point).within(boundary): # make a point and see if it's in the polygon
            name = all_records[i][2] # get the second field of the corresponding record , 2 = name province
            if "Bangkok" in name :
                return True
    return False

def getProvinces(row):
    point = (row[1],row[0])
    for i in range(len(all_shapes)):
        boundary = all_shapes[i] # get a boundary polygon
        if Point(point).within(boundary): # make a point and see if it's in the polygon
            name = all_records[i][2] # get the second field of the corresponding record , 2 = name province
            return name
# ------------------- Files iteration -----------------------
files_oddata = os.listdir(os.path.join(os.getcwd(), "DA_OD"))
result_path = os.path.join(os.getcwd(), "DA_OD", "FROM-BK")
for file_oddata in files_oddata:

    if not ".csv" in file_oddata: continue

    print('-----------------')
    print(file_oddata)
    print('-----------------')

    # Add column name
    print("Read OD file")
    subtable_od = pd.read_csv(os.path.join(os.getcwd(), "DA_OD", file_oddata), sep=";", header=None, names=columns, skiprows=1)
    print("Done")

    # Fillter type รถโดยสาร
    print("Fillter bus type")
    subtable_od = subtable_od.loc[subtable_od["kind_desc"].str.contains("\u0e23\u0e16\u0e42\u0e14\u0e22\u0e2a\u0e32\u0e23.*", regex=True)]
    print("Done")

    # Get only origin row
    print("Get only origin row")
    origins = subtable_od.drop_duplicates(keep='first', subset=["id"])
    print("Done")

    print("Get only Bangkok origin row")
    origins = origins.loc[origins[["lat1","lon1"]].apply(checkBangkok, axis=1)]
    print("Done")

    id_dict = dict() # Create dict for collecting ID which begin at Bangkok
    for _id in origins["id"]:
        id_dict[_id] = 0

    print("Tag destination")
    fromBk_od = subtable_od.loc[subtable_od["id"].apply(lambda x: True if x in id_dict else False)]
    fromBk_od["destination"] = fromBk_od[["lat2", "lon2"]].apply(getProvinces, axis=1)
    fromBk_od.to_csv(os.path.join(result_path, "fromBk"+file_oddata))
    print("Done")