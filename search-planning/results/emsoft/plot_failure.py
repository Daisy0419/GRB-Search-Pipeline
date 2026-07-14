import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_failure_scatter(overall_csv, map_csv, output_path="failure_scatter.png"):
    """
    2D scatter of failed trials colored by failure type.
    
    - Detected=False in overall only (True in map) → deadline failure
    - Detected=False in both → map failure
    """
    df_overall = pd.read_csv(overall_csv)
    df_map = pd.read_csv(map_csv)

    # Normalize detected columns to bool
    for df in [df_overall, df_map]:
        df["detected"] = df["detected"].astype(str).str.strip().str.lower() == "true"

    # Merge on the trial identity columns
    merge_keys = ["dataset", "n_src", "n_bkg"]
    merged = df_overall.merge(df_map, on=merge_keys, suffixes=("_overall", "_map"))

    # Filter to overall failures only
    failed = merged[~merged["detected_overall"]].copy()

    # Classify failure type
    failed["failure_type"] = failed["detected_map"].map(
        {True: "Deadline Failure", False: "Map Failure"}
    )

    counts = failed["failure_type"].value_counts()
    print(counts)   

    # colors = {"Map Failure": "crimson", "Deadline Failure": "dodgerblue"}
    colors = {"Map Failure": "red", "Deadline Failure": "yellow"}

    fig, ax = plt.subplots(figsize=(10, 7))
    for ftype, group in failed.groupby("failure_type"):
        ax.scatter(group["n_src"], group["n_bkg"],
                   c=colors[ftype], label=ftype,
                   s=30, alpha=0.6, edgecolors="k", linewidths=0.3)

    # ax.set_xlabel("s (n_src_events)", fontsize=12)
    # ax.set_ylabel("b (n_bkg_events)", fontsize=12)
    ax.set_xlabel("s", fontsize=12)
    ax.set_ylabel("b", fontsize=12)
    # ax.set_title("Failed Trials by Failure Type", fontsize=13)
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    # print(f"Saved to {output_path}")


if __name__ == "__main__":
    search_success_dir = "verify_result/search_success_result"
    map_success_dir = "verify_result/map_success_result"
    tiling = "5.36x4.5_tiling"
    # tiling = "2.5x2.5_tiling"
    maps = "utility"
    deadline = 30

    tilings = ["2.5x2.5_tiling", "5.36x4.5_tiling"]
    mapss = ["utility", "nodeadline", "gt"]
    deadlines = [10, 20, 30, 60, 90]
    for tiling in tilings:
        print(tiling, ":")
        for deadline in deadlines:
        # for map_ in maps:
            print("deadline", deadline)
            for maps in mapss:
                print("maps", maps)
                search_file=f"{search_success_dir}/{tiling}_{maps}_{deadline}.csv"
                if not os.path.exists(search_file):
                    continue
                map_file=f"{map_success_dir}/full_cover_{tiling}_{maps}_{deadline}.csv"
                if not os.path.exists(map_file):
                    map_file=f"{map_success_dir}/full_cover_{tiling}_{maps}.csv"
                    if not os.path.exists(map_file):
                        print(f"{map_file} does not exist")
                        continue

                plot_failure_scatter(search_file, map_file, f"failure_{tiling}_{maps}_{deadline}.png")