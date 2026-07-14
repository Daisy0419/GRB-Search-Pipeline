import csv
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib as mpl


mpl.rcParams.update({
    "font.family":      "serif",
    "font.serif":       ["Times", "Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
})


def plot_time_3d(df_det, output_dir="."):
    from mpl_toolkits.mplot3d import Axes3D

    # fig = plt.figure(figsize=(5, 4.5))
    fig = plt.figure(figsize=(3.8, 3.3))
    ax = fig.add_subplot(111, projection="3d")
    sc = ax.scatter(df_det["n_bkg"], df_det["n_src"], df_det["mapping_time"],
                    c=df_det["mapping_time"], cmap="RdYlGn_r",
                    s=3, alpha=0.6, edgecolors="k", linewidths=0.2)

    ax.set_xlabel("Background Events, b", labelpad=0)
    ax.set_ylabel("Source Events, s", labelpad=0)
    ax.set_zlabel("Map Generation Time (s)", labelpad=-8)

    ax.tick_params(axis='x', pad=1)
    ax.tick_params(axis='y', pad=1)
    ax.tick_params(axis='z', pad=-5)

    ax.view_init(elev=25, azim=135)

    # Give more room on the right for the z-label
    fig.subplots_adjust(left=0.0, right=0.92, bottom=0.0, top=1.1)
    # fig.subplots_adjust(left=0.0, right=0.78, bottom=0.0, top=1.05)
    # plt.savefig(f"{output_dir}/time_3d.png", dpi=300, bbox_inches="tight")
    plt.savefig(f"{output_dir}/mapping_time.png", dpi=300)
    # plt.savefig(f"{output_dir}/time_3d.png", dpi=300,
    #         bbox_inches="tight", pad_inches=0.2)
    plt.close()



if __name__ == "__main__":

    results_csv = f"emsoft-stats.csv"
    output_dir = "."

    df = pd.read_csv(results_csv)
    plot_time_3d(df, output_dir)
