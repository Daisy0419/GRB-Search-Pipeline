import csv
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def plot_time_vs_nsrc(df_det, output_dir="."):
    """Generation time vs n_src, colored by n_bkg."""
    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(df_det["n_src"], df_det["time"],
                    c=df_det["n_bkg"], cmap="viridis", alpha=0.6, s=20)
    ax.set_xlabel("n_src_events", fontsize=12)
    ax.set_ylabel("Generation Time (s)", fontsize=12)
    ax.set_title("Generation Time vs N_src", fontsize=13)
    plt.colorbar(sc, ax=ax, label="n_bkg_events")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/time_vs_nsrc.png", dpi=150)
    plt.close()


def plot_time_vs_nbkg(df_det, output_dir="."):
    """Generation time vs n_bkg, colored by n_src."""
    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(df_det["n_bkg"], df_det["time"],
                    c=df_det["n_src"], cmap="plasma", alpha=0.6, s=20)
    ax.set_xlabel("n_bkg_events", fontsize=12)
    ax.set_ylabel("Generation Time (s)", fontsize=12)
    ax.set_title("Generation Time vs N_bkg", fontsize=13)
    plt.colorbar(sc, ax=ax, label="n_src_events")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/time_vs_nbkg.png", dpi=150)
    plt.close()


def plot_time_vs_ratio(df_det, output_dir="."):
    """Generation time vs n_src/n_bkg ratio, colored by detection cost."""
    n_src = df_det["n_src"].values.astype(float)
    n_bkg = df_det["n_bkg"].values.astype(float)
    ratio = n_src / np.maximum(n_bkg, 1.0)

    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(ratio, df_det["time"],
                    c=df_det["time"], cmap="RdYlGn_r",
                    alpha=0.5, s=20)
    ax.set_xlabel("n_src / n_bkg", fontsize=12)
    ax.set_ylabel("Generation Time (s)", fontsize=12)
    ax.set_title("Generation Time vs Src/Bkg Ratio", fontsize=13)
    plt.colorbar(sc, ax=ax, label="Generation Time (s)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/time_vs_ratio.png", dpi=150)
    plt.close()


def plot_time_scatter_combined(df_det, output_dir="."):
    """Combined 1x3 scatter: vs n_src, vs n_bkg, vs ratio."""
    n_src = df_det["n_src"].values.astype(float)
    n_bkg = df_det["n_bkg"].values.astype(float)
    y = df_det["time"].values
    ratio = n_src / np.maximum(n_bkg, 1.0)

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))

    sc0 = axes[0].scatter(n_src, y, c=n_bkg, cmap="viridis", alpha=0.6, s=20)
    axes[0].set_xlabel("n_src_events", fontsize=12)
    axes[0].set_ylabel("Generation Time (s)", fontsize=12)
    axes[0].set_title("Generation Time vs N_src", fontsize=13)
    plt.colorbar(sc0, ax=axes[0], label="n_bkg_events")

    sc1 = axes[1].scatter(n_bkg, y, c=n_src, cmap="plasma", alpha=0.6, s=20)
    axes[1].set_xlabel("n_bkg_events", fontsize=12)
    axes[1].set_ylabel("Generation Time (s)", fontsize=12)
    axes[1].set_title("Generation Time vs N_bkg", fontsize=13)
    plt.colorbar(sc1, ax=axes[1], label="n_src_events")

    sc2 = axes[2].scatter(ratio, y, c=y, cmap="RdYlGn_r", alpha=0.5, s=20)
    axes[2].set_xlabel("n_src / n_bkg", fontsize=12)
    axes[2].set_ylabel("Generation Time (s)", fontsize=12)
    axes[2].set_title("Generation Time vs Src/Bkg Ratio", fontsize=13)
    plt.colorbar(sc2, ax=axes[2], label="Generation Time (s)")

    plt.tight_layout()
    plt.savefig(f"{output_dir}/time_scatter_combined.png", dpi=150)
    plt.close()


def plot_time_3d(df_det, output_dir="."):
    """3D scatter: n_src, n_bkg, time."""
    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")
    sc = ax.scatter(df_det["n_src"], df_det["n_bkg"], df_det["time"],
                    c=df_det["time"], cmap="RdYlGn_r",
                    s=20, alpha=0.6, edgecolors="k", linewidths=0.2)
    ax.set_xlabel("n_src_events", fontsize=11, labelpad=10)
    ax.set_ylabel("n_bkg_events", fontsize=11, labelpad=10)
    ax.set_zlabel("Generation Time (s)", fontsize=11, labelpad=10)
    ax.set_title("Generation Time vs (N_src, N_bkg)", fontsize=13, pad=20)
    fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.1, label="Generation Time (s)")
    ax.view_init(elev=25, azim=135)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/time_3d.png", dpi=150, bbox_inches="tight")
    plt.close()

def plot_time_3d_multiview(df_det, output_dir="."):
    """3D scatter: n_src, n_bkg, time — shown from multiple viewing angles."""
    from mpl_toolkits.mplot3d import Axes3D

    views = [
        (25, 135,  "Front-left"),
        (25, -50,  "Front-right"),
        (25, 45,   "Back-right"),
        (25, 225,  "Back-left"),
        (70, 135,  "Top-down (angled)"),
        (5,  135,  "Near-horizontal"),
    ]

    nrows, ncols = 2, 3
    fig = plt.figure(figsize=(8 * ncols, 7 * nrows))

    for i, (elev, azim, label) in enumerate(views):
        ax = fig.add_subplot(nrows, ncols, i + 1, projection="3d")
        sc = ax.scatter(df_det["n_src"], df_det["n_bkg"], df_det["time"],
                        c=df_det["time"], cmap="RdYlGn_r",
                        s=20, alpha=0.6, edgecolors="k", linewidths=0.2)
        ax.set_xlabel("n_src_events", fontsize=10, labelpad=8)
        ax.set_ylabel("n_bkg_events", fontsize=10, labelpad=8)
        ax.set_zlabel("Gen Time (s)", fontsize=10, labelpad=8)
        ax.set_title(f"{label}\n(elev={elev}°, azim={azim}°)", fontsize=11)
        ax.view_init(elev=elev, azim=azim)
        ax.tick_params(labelsize=8)

    # fig.colorbar(sc, ax=fig.axes, shrink=0.4, pad=0.08,
    #              label="Generation Time (s)", location="bottom")
    fig.suptitle("Generation Time vs (N_src, N_bkg) — Multiple Views",
                 fontsize=14, y=1.01)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/time_3d_multiview.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_all_scatter(df_det, output_dir="."):
    plot_time_vs_nsrc(df_det, output_dir)
    plot_time_vs_nbkg(df_det, output_dir)
    plot_time_vs_ratio(df_det, output_dir)
    # plot_time_scatter_combined(df_det, output_dir)
    # plot_time_3d(df_det, output_dir)
    plot_time_3d_multiview(df_det, output_dir)
    print(f"All scatter plots saved to {output_dir}/")


if __name__ == "__main__":

    results_csv = f"emsoft.csv"
    output_dir = "."

    df = pd.read_csv(results_csv)
    plot_all_scatter(df, output_dir)
