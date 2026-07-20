import subprocess
import os
import pandas as pd

def run(executable, dataset, tiling, source_tile, w_max, w_acc, dwell_time, is_deepslow=0):
    print(f"\nRunning ./ts with dataset={dataset}, tiling={tiling}, source_tile={source_tile}, w_max={w_max}, w_acc={w_acc}, dwell_time={dwell_time}, is_deepslow={is_deepslow}")
    cmd = [executable, dataset, tiling, str(source_tile), str(w_max), str(w_acc), str(dwell_time), str(is_deepslow)]
    try:
        # result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # output = result.stdout
        # print(output)
        result = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print(result.stdout)
        print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error message: {e.stderr}")


def getFiles(folder_path):
    skymaps = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".h5"):
            skymap = os.path.splitext(filename)[0]
            skymaps.append(skymap)
    return skymaps

def getTileFiles(folder_path):
    tilefiles = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            tilefiles.append(filename)
    return tilefiles


if __name__ == "__main__":
    EXECUTABLE = "../build/ts"
    map_path = "/shared/training/longlow_maps"
    # map_path = "/home/daisy/GRB_Search_pipeline_workstation/data/ADAPT_maps_new/emsoft_maps_short"
    tile_path = "../data/tilings"
    source_tile_dir = "../data/source_tile_longlow_train"  
    

    result_file = "out.csv"
    skymaps = getFiles(map_path)
    tilefiles = getTileFiles(tile_path)

    w_max = 10
    w_acc = 10
    dwell_time = 5
    is_deepslow = 0

    for tiling_file in tilefiles:
        tiling_path = os.path.join(tile_path, tiling_file)
        tiling = os.path.splitext(tiling_file)[0]
        source_tile_csv = os.path.join(source_tile_dir, f"source_tiles_{tiling}.csv")
        source_tile_lookup = pd.read_csv(source_tile_csv).set_index("map")

        for skymap in skymaps:
            source_tile = source_tile_lookup.loc[f"{skymap}.h5", "RightTile"]
            dataset = os.path.join(map_path, f"{skymap}.h5")
            print(f"dataset: {dataset}")
            run(EXECUTABLE, dataset, tiling_path, source_tile,
                w_max, w_acc, dwell_time, is_deepslow)

        new_result_name = f"longlow_{tiling}.csv"
        os.rename(result_file, new_result_name)



    EXECUTABLE = "../build/ts"
    # map_path = "/shared/training/longlow_maps"
    map_path = "/home/daisy/GRB_Search_pipeline_workstation/data/ADAPT_maps_new/emsoft_maps_short"
    tile_path = "../data/tilings"
    source_tile_dir = "../data/source_tile_short_train"  
    

    result_file = "out.csv"
    skymaps = getFiles(map_path)
    tilefiles = getTileFiles(tile_path)

    w_max = 10
    w_acc = 10
    dwell_time = 5
    is_deepslow = 0

    for tiling_file in tilefiles:
        tiling_path = os.path.join(tile_path, tiling_file)
        tiling = os.path.splitext(tiling_file)[0]
        source_tile_csv = os.path.join(source_tile_dir, f"source_tiles_{tiling}.csv")
        source_tile_lookup = pd.read_csv(source_tile_csv).set_index("map")

        for skymap in skymaps:
            source_tile = source_tile_lookup.loc[f"{skymap}.h5", "RightTile"]
            dataset = os.path.join(map_path, f"{skymap}.h5")
            print(f"dataset: {dataset}")
            run(EXECUTABLE, dataset, tiling_path, source_tile,
                w_max, w_acc, dwell_time, is_deepslow)

        new_result_name = f"short_{tiling}.csv"
        os.rename(result_file, new_result_name)

# if __name__ == "__main__":
#     EXECUTABLE = "../build/ts" 
#     map_path = "../data/ADAPT_maps_new/test"
#     tile_path = "../data/tilings"
#     source_tile_path = "../data/source_tile"

#     result_file = "out.csv"
#     time_file = "time.csv"
#     skymaps=getFiles(map_path)
#     tilefiles=getTileFiles(tile_path)

#     w_max = 10
#     w_acc = 10
#     dwell_time = 5
#     is_deepslow = 0
    
#     for tiling_file in tilefiles:
#         tiling_path = os.path.join(tile_path, tiling_file)
#         tiling = os.path.splitext(tiling_file)[0]
#         source_tile_path = os.path.join(source_tile_path, f"source_tiles_{tiling}.csv")
#         source_tile_lookup = pd.read_csv(source_tile_path).set_index("map")
#         for skymap in skymaps:
#             source_tile = source_tile_lookup.loc[f"{skymap}.h5", "RightTile"]
#             dataset = os.path.join(map_path, f"{skymap}.h5")
#             print(f"dataset: {dataset}")
#             run(EXECUTABLE, dataset, tiling_path, source_tile, w_max, w_acc, dwell_time, is_deepslow)
        
#         new_result_name = f"{tiling}.csv"
#         # new_time_name = f"runtime_{tiling}.csv"
#         os.rename(result_file, new_result_name)
#         # os.rename(time_file, new_time_name)
    
#     # is_deepslow=1
#     # for skymap in skymaps:
#     #     dataset = os.path.join(data_path, f"{skymap}.txt")
#     #     print(f"dataset: {dataset}")
#     #     run(dataset, budgets, w_max, w_acc, dwell_time, is_deepslow)
#     #     # run(budgets, num_routes, dataset)
#     #     new_name = f"2axes_{skymap}.csv"
#     #     os.rename(default_name, new_name)