import subprocess
import os
import pandas as pd
import re
import csv

"parse mapping and waiting time"

def parse_map_filename(filename):
    """Extract polar angle, azimuth, and transient_id from a map filename."""
    m = re.match(
        r'.*_p(\d+)-(\d+)_a(\d+)-(\d+)_(\d+)_map\.h5',
        filename
    )
    if not m:
        return None
    
    p_int, p_frac, a_int, a_frac, tid = m.groups()
    polar = float(f"{p_int}.{p_frac}")
    azimuth = float(f"{a_int}.{a_frac}")
    transient_id = int(tid)
    
    return polar, azimuth, transient_id

def make_key(alt, az, tid):
    """Round to 1 decimal place for matching."""
    return (round(alt, 1), round(az, 1), tid)

def build_map_index(map_dir):
    index = {}
    for fname in os.listdir(map_dir):
        if not fname.endswith('_map.h5'):
            continue
        parsed = parse_map_filename(fname)
        if parsed is None:
            continue
        polar, azimuth, tid = parsed
        altitude = 90.0 - polar
        key = make_key(altitude, azimuth, tid)
        index[key] = os.path.join(map_dir, fname)
    return index

def match_csv_to_maps(csv_path, map_dir):
    """For each CSV row, find the corresponding map file and extract times.
    
    Returns a list of dicts with keys:
        map_file, transient_id, wait_time, mapping_time,
        and the full row for anything else you need.
    """
    index = build_map_index(map_dir)
    
    results = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            alt = float(row['alt'])
            az = float(row['az'])
            tid = int(row['transient_id'])
            wait_time = float(row['wait_time'])
            mapping_time = float(row['mapping_time'])

            key = make_key(alt, az, tid)
            map_file = index.get(key, None)
            
            if map_file is None:
                print(f"WARNING: no map file found for alt={alt}, az={az}, "
                      f"transient_id={tid} (key={key})")

            if map_file is None:
                # Nearest-match fallback
                best_key = min(
                    (k for k in index if k[2] == tid),
                    key=lambda k: (k[0] - alt)**2 + (k[1] - az)**2,
                    default=None
                )
                if best_key is not None:
                    map_file = index[best_key]
                    print(f"  Fuzzy matched: csv=({alt},{az}) -> file key=({best_key[0]},{best_key[1]})")
                        
            results.append({
                'map_file': map_file,
                'transient_id': tid,
                'wait_time': wait_time,
                'mapping_time': mapping_time,
                # 'row': row, 
            })
    
    return results


def run(executable, dataset, tiling, source_tile, w_max, w_acc, deadline, is_deepslow=0):
    print(f"\nRunning ./ts with dataset={dataset}, tiling={tiling}, source_tile={source_tile}, w_max={w_max}, w_acc={w_acc}, deadline={deadline}, is_deepslow={is_deepslow}")
    cmd = [executable, dataset, tiling, str(source_tile), str(w_max), str(w_acc), str(deadline), str(is_deepslow)]
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
    map_path_ = "/shared/valid_tests/5.36x4.5/emsoft_maps"
    map_stats_ = "/shared/valid_tests/5.36x4.5/emsoft_stats"
    tile_path = "../data/tilings"
    source_tile_dir = "../data/source_tile_short"  


    result_file = "out.csv"
    tilefiles = getTileFiles(tile_path)


    w_max = 10
    w_acc = 10
    # deadline = 30 
    is_deepslow = 0


    # # After building time_lookup from match_csv_to_maps results
    # time_results = match_csv_to_maps(map_stats, map_path)

    # # Check 1: Multiple CSV rows mapping to the same file (many-to-one)
    # file_to_rows = {}
    # for r in time_results:
    #     f = r['map_file']
    #     if f is not None:
    #         file_to_rows.setdefault(f, []).append(r['transient_id'])

    # print("=== Files matched by multiple CSV rows ===")
    # for f, tids in file_to_rows.items():
    #     if len(tids) > 1:
    #         print(f"  {os.path.basename(f)} <- transient_ids {tids}")

    # # Check 2: Multiple files matching the same CSV row (one-to-many)
    # # This would show up as duplicate keys in build_map_index
    # def build_map_index_checked(map_dir):
    #     index = {}
    #     collisions = {}
    #     for fname in os.listdir(map_dir):
    #         if not fname.endswith('_map.h5'):
    #             continue
    #         parsed = parse_map_filename(fname)
    #         if parsed is None:
    #             continue
    #         polar, azimuth, tid = parsed
    #         altitude = 90.0 - polar
    #         key = make_key(altitude, azimuth, tid)
    #         if key in index:
    #             collisions.setdefault(key, [index[key]]).append(os.path.join(map_dir, fname))
    #         index[key] = os.path.join(map_dir, fname)
        
    #     if collisions:
    #         print("=== Keys with multiple map files (index collisions) ===")
    #         for k, files in collisions.items():
    #             print(f"  key={k}:")
    #             for f in files:
    #                 print(f"    {os.path.basename(f)}")
    #     else:
    #         print("No index collisions (all keys unique)")
        
    #     return index

    # # Check 3: Unmatched in both directions
    # matched_files = set(r['map_file'] for r in time_results if r['map_file'])
    # all_map_files = set(
    #     os.path.join(map_path, f) for f in os.listdir(map_path) if f.endswith('_map.h5')
    # )
    # unmatched_csv = [r for r in time_results if r['map_file'] is None]
    # unmatched_files = all_map_files - matched_files

    # print(f"\n=== Summary ===")
    # print(f"CSV rows: {len(time_results)}, matched: {len(time_results) - len(unmatched_csv)}, unmatched: {len(unmatched_csv)}")
    # print(f"Map files: {len(all_map_files)}, matched: {len(matched_files)}, unmatched: {len(unmatched_files)}")

    # map_types = ['gt', 'nodeadline']
    deadlines = [40]

    for deadline in deadlines:
        map_path = f"{map_path_}_{deadline}"
        map_stats = f"{map_stats_}_{deadline}.csv"
        skymaps = getFiles(map_path)
        


        # Build a lookup: map_file -> {wait_time, mapping_time, ...}
        time_results = match_csv_to_maps(map_stats, map_path)
        time_lookup = {}
        for r in time_results:
            if r['map_file'] is not None:
                # Key by the basename so we can match against skymap names
                basename = os.path.splitext(os.path.basename(r['map_file']))[0]
                time_lookup[basename] = r

        

        for tiling_file in tilefiles:
            tiling_path = os.path.join(tile_path, tiling_file)
            tiling = os.path.splitext(tiling_file)[0]
            source_tile_csv = os.path.join(source_tile_dir, f"source_tiles_{tiling}.csv")
            source_tile_lookup = pd.read_csv(source_tile_csv).set_index("map")

            for skymap in skymaps:
                source_tile = source_tile_lookup.loc[f"{skymap}.h5", "RightTile"]
                dataset = os.path.join(map_path, f"{skymap}.h5")

                if skymap not in time_lookup:
                    print(f"WARNING: no time info for {skymap}, skipping")
                    continue

                info = time_lookup[skymap]
                mapping_time = info['mapping_time']
                waiting_time = info['wait_time']
                remain_time = max(deadline - mapping_time - waiting_time, 0.0)

                print(f"dataset: {dataset}, remain_time: {remain_time:.3f}")
                run(EXECUTABLE, dataset, tiling_path, source_tile,
                    w_max, w_acc, remain_time, is_deepslow)

            new_result_name = f"{tiling}_utility_{deadline}.csv"
            os.rename(result_file, new_result_name)

