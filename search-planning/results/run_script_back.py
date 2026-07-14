import subprocess
import os

def run(dataset, budgets, w_max, w_acc, dwell_time, is_deepslow=0):
    for budget in budgets:
        print(f"\nRunning ./ts with dataset={dataset}, budget={budget}, w_max={w_max}, w_acc={w_acc}, dwell_time={dwell_time}, is_deepslow={is_deepslow}")
        cmd = [EXECUTABLE, dataset, str(budget), str(w_max), str(w_acc), str(dwell_time), str(is_deepslow)]
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
        if filename.endswith(".txt"):
            skymap = os.path.splitext(filename)[0]
            skymaps.append(skymap)
    return skymaps

if __name__ == "__main__":
    EXECUTABLE = "../build/ts" 
    data_path = "../data/GRB_maps/txt_files"

    result_file = "out.csv"
    time_file = "time.csv"
    skymaps=getFiles(data_path)
    budgets = [30, 60, 90, 120, 150, 180, 210]
    # budgets = [30]
    w_max = 30
    w_acc = 30
    dwell_time = 5
    is_deepslow = 0

    

    for skymap in skymaps:
        dataset = os.path.join(data_path, f"{skymap}.txt")
        print(f"dataset: {dataset}")
        run(dataset, budgets, w_max, w_acc, dwell_time, is_deepslow)
        # run(budgets, num_routes, dataset)
        # new_name = f"geodesic_{skymap}.csv"
        new_result_name = f"{skymap}.csv"
        new_time_name = f"runtime_{skymap}.csv"
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