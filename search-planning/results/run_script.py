import subprocess
import os

def run(executable, dataset, tiling, budgets, w_max, w_acc, dwell_time, is_deepslow=0):
    for budget in budgets:
        print(f"\nRunning ./ts with dataset={dataset}, tiling={tiling}, budget={budget}, w_max={w_max}, w_acc={w_acc}, dwell_time={dwell_time}, is_deepslow={is_deepslow}")
        cmd = [executable, dataset, tiling, str(budget), str(w_max), str(w_acc), str(dwell_time), str(is_deepslow)]
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
    map_path = "../data/ADAPT_maps_new/emsoft_maps_new"
    tile_path = "../data/tilings"

    result_file = "out.csv"
    time_file = "time.csv"
    skymaps=getFiles(map_path)
    tilefiles=getTileFiles(tile_path)
    budgets = [10000]
    # budgets = [30, 40, 50, 60, 70, 80, 90]
    w_max = 10
    w_acc = 10
    dwell_time = 5
    is_deepslow = 0

    
    for tiling_ in tilefiles:
        tiling = os.path.join(tile_path, tiling_)
        for skymap in skymaps:
            dataset = os.path.join(map_path, f"{skymap}.h5")
            print(f"dataset: {dataset}")
            run(EXECUTABLE, dataset, tiling, budgets, w_max, w_acc, dwell_time, is_deepslow)
            # run(budgets, num_routes, dataset)
            # new_name = f"geodesic_{skymap}.csv"
            # tile = os.path.splitext(tiling_)[0]
            # new_result_name = f"{tile}_{skymap}.csv"
            # new_time_name = f"runtime_{tile}_{skymap}.csv"
            # os.rename(result_file, new_result_name)
            # os.rename(time_file, new_time_name)
        tile = os.path.splitext(tiling_)[0]
        new_result_name = f"{tile}.csv"
        new_time_name = f"runtime_{tile}.csv"
        os.rename(result_file, new_result_name)
        os.rename(time_file, new_time_name)
    
    # is_deepslow=1
    # for skymap in skymaps:
    #     dataset = os.path.join(data_path, f"{skymap}.txt")
    #     print(f"dataset: {dataset}")
    #     run(dataset, budgets, w_max, w_acc, dwell_time, is_deepslow)
    #     # run(budgets, num_routes, dataset)
    #     new_name = f"2axes_{skymap}.csv"
    #     os.rename(default_name, new_name)