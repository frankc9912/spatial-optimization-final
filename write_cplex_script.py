import arcpy
import os
import math
import csv

transit_stop_shp = "C:\\Users\\MaJia\\Documents\\Spatial Op\\Final\\stops2.shp"
#parcels_shp = "final.shp"
parcels_shp = "C:\\Users\\MaJia\\Documents\\Spatial Op\\Final\\final4.shp"
#parcels_shp = os.path.join(parcels_gdb, "final3")
network_gdb = "C:\\Users\\MaJia\\Documents\\Spatial Op\\Final\\test\\test.gdb"
network_nd = os.path.join(network_gdb, "network", "network")



transit_coverage = 1320
beta = 1
n = 2
alpha_list = [0.000000009, 0.000000008, 0.000000007, 0.000000006, 0.000000005, 0.000000004, 0.000000003, 0.000000002, 0.000000001, 0.00000001, 0.0000001, 0.000001, 0.00001, 0.0001, 0.001, 0.01]
Bmax_list = [6700000, 7500000, 10000000]
Bmin = 5000000
M = 99999

try:
    # Test if the shapefile can be accessed
    if arcpy.Exists(transit_stop_shp):
        print("Shapefile found: Starting processing...")
        Ej_dict = {j: E_j for j, E_j in arcpy.da.SearchCursor(transit_stop_shp, ["stopid", "lwj"])}
        stop_geometries = {j: geom for j, geom in arcpy.da.SearchCursor(transit_stop_shp, ["stopid", "SHAPE@"])}
        print("Data loaded successfully.")
    else:
        print("Error: Shapefile does not exist at the specified path.")
except Exception as e:
    print("Failed to process shapefile: {}".format(e))

print(Ej_dict)

def calculate_network_distance(parcel_geometry, stop_geometry, network_dataset):
    arcpy.na.BuildNetwork(network_dataset)
    na_layer = arcpy.na.MakeClosestFacilityLayer(network_dataset, "ClosestFacility", "LENGTH").getOutput(0)
    sublayer_names = arcpy.na.GetNAClassNames(na_layer)
    facilities_layer_name = sublayer_names["Facilities"]
    incidents_layer_name = sublayer_names["Incidents"]
    arcpy.na.AddLocations(na_layer, facilities_layer_name, stop_geometry)
    arcpy.na.AddLocations(na_layer, incidents_layer_name, parcel_geometry)
    print(arcpy.mapping.ListLayers(na_layer, "")[1].name, arcpy.mapping.ListLayers(na_layer, "")[2].name)
    arcpy.na.Solve(na_layer)
    print(arcpy.mapping.ListLayers(na_layer, "")[4].name)
    routes_sublayer = arcpy.mapping.ListLayers(na_layer, arcpy.mapping.ListLayers(na_layer, "")[4])[0]
    cursor = arcpy.da.SearchCursor(routes_sublayer, ["Total_Length"])
    for row in cursor:
        distance = row[0]
    arcpy.Delete_management(na_layer)
    return distance

def calculate_simple_distance(parcel_geometry, stop_geometry):
    return parcel_geometry.distanceTo(stop_geometry)

#if len(arcpy.ListFields(parcels_shp, "Ai")) == 0:
    #arcpy.AddField_management(parcels_shp, "Ai", "DOUBLE")


parcel_geometry_dict = {}
Si_dict = {}
Ci_dict = {}
Ai_dict = {}
with arcpy.da.UpdateCursor(parcels_shp, ["FID", "SHAPE@", "units", "total_fee", "jobs"]) as cursor:
    for row in cursor:
        parcel_id, parcel_geometry, num_house, cost, Ai = row
        #Ai = 0
        #for stop_id, Ej in Ej_dict.items():
            #stop_geometry = stop_geometries[stop_id]
            #if calculate_simple_distance(parcel_geometry, stop_geometry) <= transit_coverage:
                #Cij = calculate_simple_distance(parcel_geometry, stop_geometry)
                #Ai += Ej * math.exp(-beta * (60*Cij/5280/10))
                #row[4] = Ai
        #cursor.updateRow(row)
        parcel_geometry_dict[parcel_id] = parcel_geometry
        Si_dict[parcel_id] = num_house
        Ci_dict[parcel_id] = cost
        Ai_dict[parcel_id] = Ai
        print(Ai_dict)

#output_csv = "C:\\Users\\MaJia\\Documents\\Spatial Op\\Final\\ai.csv"

#with open(output_csv, 'wb') as csvfile:
    #fieldnames = ['Parcel ID', 'Ai']
    #writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #writer.writeheader()
    #for parcel_id, Ai in Ai_dict.items():
        #writer.writerow({'Parcel ID': parcel_id, 'Ai': Ai})


for alpha in alpha_list:
    for Bmax in Bmax_list:
        problem_file_path = "C:\\Users\\MaJia\\Documents\\Spatial Op\\Final\\problems9\\{}_{}.txt".format(alpha, Bmax)
        I = "I"
        with open(problem_file_path, 'w') as file:
            file.write("Maximize\n")
            obj_expr = " + ".join(["{}X{}".format(alpha * n * Ai_dict[i] * Si_dict[i], i) for i in Ai_dict])
            obj_expr += " - {}{}".format((1 - alpha), I)
            file.write(obj_expr + "\n")
            file.write("\nSubject To\n")
            budget_expr = " + ".join(["{}X{}".format(Ci_dict[i], i) for i in Ai_dict])
            file.write(budget_expr + " <= {}\n".format(Bmax))
            budget_expr = " + ".join(["{}X{}".format(Ci_dict[i], i) for i in Ai_dict])
            file.write(budget_expr + " >= {}\n".format(Bmin))
            for i in Si_dict:
                for j in Si_dict:
                    if i < j:
                        file.write("+ {}X{} + {}X{} + {}X{} + {}X{} - {}{} <= {}\n".format(
                            M * Si_dict[i], i, M * Si_dict[i], j, M * Si_dict[j], i, M * Si_dict[j], j,
                            calculate_simple_distance(parcel_geometry_dict[i], parcel_geometry_dict[j]), I,
                            -Si_dict[i] - Si_dict[j] + 2 * M * Si_dict[i] + 2 * M * Si_dict[j]))
                        print(i)
            file.write(" {} >= 0\n".format(I))
            for i in Ai_dict:
                file.write("X{} >= 0\n".format(i))
            for i in Ai_dict:
                file.write("X{} <= 1\n".format(i))
            file.write("\nBinary\n")
            file.write("\n".join(["X{}".format(i) for i in Ai_dict]))
            # file.write("\n\nContinuous\n")
            # file.write("{}\n".format(I))
            file.write("\nEnd\n")

        print("CPLEX problem written to {}".format(problem_file_path))
