import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from scipy.ndimage import gaussian_filter
import os

import matplotlib as mpl


mpl.rcParams.update({
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
})

def build_binned_surface(df, value_col, n_bins=20, smooth_sigma=1.0):
    """
    Bin data into (n_src, n_bkg) grid and compute mean of value_col per bin.

    Returns
    -------
    SRC, BKG : 2D meshgrid arrays
    prob_smooth : 2D array (smoothed, with NaN where no data)
    grouped : DataFrame with per-(n_src, n_bkg) aggregates
    """
    n_src = df["n_src"].values.astype(float)
    n_bkg = df["n_bkg"].values.astype(float)
    values = df[value_col].values.astype(float)

    src_edges = np.linspace(n_src.min(), n_src.max() + 1, n_bins + 1)
    bkg_edges = np.linspace(n_bkg.min(), n_bkg.max() + 1, n_bins + 1)
    src_centers = 0.5 * (src_edges[:-1] + src_edges[1:])
    bkg_centers = 0.5 * (bkg_edges[:-1] + bkg_edges[1:])

    prob_grid = np.full((n_bins, n_bins), np.nan)
    count_grid = np.zeros((n_bins, n_bins), dtype=int)

    src_idx = np.clip(np.digitize(n_src, src_edges) - 1, 0, n_bins - 1)
    bkg_idx = np.clip(np.digitize(n_bkg, bkg_edges) - 1, 0, n_bins - 1)

    for i in range(len(n_src)):
        si, bi = src_idx[i], bkg_idx[i]
        count_grid[bi, si] += 1
        if np.isnan(prob_grid[bi, si]):
            prob_grid[bi, si] = values[i]
        else:
            n = count_grid[bi, si]
            prob_grid[bi, si] = prob_grid[bi, si] * (n - 1) / n + values[i] / n

    # Smooth
    has_data = ~np.isnan(prob_grid)
    if smooth_sigma > 0 and has_data.sum() > 4:
        filled = prob_grid.copy()
        filled[~has_data] = 0.0
        weight = has_data.astype(float)
        smoothed_val = gaussian_filter(filled, sigma=smooth_sigma)
        smoothed_wt = gaussian_filter(weight, sigma=smooth_sigma)
        valid = smoothed_wt > 0.01
        prob_smooth = np.where(valid, smoothed_val / smoothed_wt, np.nan)
    else:
        prob_smooth = prob_grid.copy()

    SRC, BKG = np.meshgrid(src_centers, bkg_centers)

    grouped = df.groupby(["n_src", "n_bkg"]).agg(
        n=(value_col, "size"),
        prob=(value_col, "mean"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(7, 5))
    # Mask empty bins so they show as white
    masked = np.ma.masked_where(count_grid == 0, count_grid)
    im = ax.pcolormesh(src_centers, bkg_centers, masked, cmap="viridis", shading="auto")
    plt.colorbar(im, ax=ax, label="Count per bin")

    # Annotate each cell with its count (optional, useful for small n_bins)
    if n_bins <= 50:
        for bi in range(n_bins):
            for si in range(n_bins):
                c = count_grid[bi, si]
                if c > 0:
                    ax.text(src_centers[si], bkg_centers[bi], str(c),
                            ha="center", va="center", fontsize=6, color="white")

    ax.set_xlabel("n_src")
    ax.set_ylabel("n_bkg")
    ax.set_title("maps per bin")
    plt.tight_layout()
    plt.savefig("maps_per_bin.png", dpi=150)
    # plt.show()

    return SRC, BKG, prob_smooth, grouped


# Individual plot functions
def plot_surface_3d(SRC, BKG, prob_smooth, file, output_dir="."):
    """3D surface plot."""
    prob_plot = np.ma.masked_invalid(prob_smooth)
    norm = plt.Normalize(0, 1)
    colors = cm.RdYlGn(norm(prob_plot))

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(SRC, BKG, prob_plot,
                    facecolors=colors, alpha=0.85,
                    rstride=1, cstride=1,
                    linewidth=0.2, edgecolor="gray", shade=True)
    ax.set_xlabel("n_src_events", fontsize=12, labelpad=10)
    ax.set_ylabel("n_bkg_events", fontsize=12, labelpad=10)
    ax.set_zlabel("Success Probability", fontsize=12, labelpad=10)
    ax.set_zlim(0, 1.05)

    # title="Detection Success Probability Surface"
    # ax.set_title(title, fontsize=14, pad=20)

    mappable = cm.ScalarMappable(norm=norm, cmap="RdYlGn")
    cbar = fig.colorbar(mappable, ax=ax, shrink=0.6, pad=0.1)
    cbar.set_label(label="Success Probability", fontsize=11)

    ax.view_init(elev=25, azim=135)
    plt.tight_layout()
    filename=f"success_prob_surface_{file}.png", 
    plt.savefig(f"{output_dir}/{filename}", dpi=300, bbox_inches="tight")
    plt.close()



def plot_wireframe_scatter(SRC, BKG, prob_smooth, grouped, file, output_dir="."):
    """Wireframe surface with scatter overlay."""
    prob_plot = np.ma.masked_invalid(prob_smooth)

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_wireframe(SRC, BKG, prob_plot, color="gray", alpha=0.3,
                      rstride=1, cstride=1, linewidth=0.5)
    sc = ax.scatter(grouped["n_src"], grouped["n_bkg"], grouped["prob"],
                    c=grouped["prob"], cmap="RdYlGn",
                    s=grouped["n"] * 8 + 15, alpha=0.9,
                    edgecolors="k", linewidths=0.4,
                    vmin=0, vmax=1, zorder=5)
    ax.set_xlabel("n_src_events", fontsize=12, labelpad=10)
    ax.set_ylabel("n_bkg_events", fontsize=12, labelpad=10)
    ax.set_zlabel(label="Success Probability", fontsize=12, labelpad=10)
    ax.set_zlim(0, 1.05)
    # title="Success Probability: Surface + Data Points"
    # ax.set_title(title, fontsize=13, pad=20)
    cbar = fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.1)
    cbar.set_label(label="Success Probability", fontsize=11)
    ax.view_init(elev=25, azim=135)
    plt.tight_layout()
    filename=f"success_prob_scatter_{file}.png", 
    plt.savefig(f"{output_dir}/{filename}", dpi=300, bbox_inches="tight")
    plt.close()



def plot_all_success(df, file, output_dir=".", n_bins=20, smooth_sigma=1.0):
    """Generate all success probability plots."""
    SRC, BKG, prob_smooth, grouped = build_binned_surface(
        df, "detected", n_bins, smooth_sigma)

    plot_surface_3d(SRC, BKG, prob_smooth, file, output_dir=output_dir)
    plot_wireframe_scatter(SRC, BKG, prob_smooth, grouped, file, output_dir=output_dir)

    print(f"Success probability plots saved to {output_dir}/")





if __name__ == "__main__":
    result_dir = "verify_result/search_success_result"
    save_dir = "."
    bins_per_axes = 20
    smooth_sigma = 0.0


    # tiling = "2.5x2.5_tiling"
    # map = "utility"
    # dealine = "10"

    # result_csv = "2.5x2.5_tiling_utility_90.csv"
    
    # df = pd.read_csv(result_csv)
    # file = f"{tiling}_{map}_{dealine}"
    # print(f"Loaded {len(df)} rows from {result_csv}")
    # print(f"Detected: {df['detected'].sum()} / {len(df)} "
    #       f"({df['detected'].mean():.3f})")
    # plot_all_success(df, file, save_dir, n_bins=bins_per_axes, smooth_sigma=smooth_sigma)



    tilings = ["2.5x2.5_tiling", "5.36x4.5_tiling"]
    maps = ["utility", "nodeadline", "gt"]
    deadlines = [10, 20, 30, 60, 90]
    for tiling in tilings:
        for map_ in maps:
            for deadline in deadlines:
                result_csv = f"{result_dir}/{tiling}_{map_}_{deadline}.csv"
                if not os.path.exists(result_csv): 
                    print(f"{result_csv} does not exist")
                    continue
                df = pd.read_csv(result_csv)
                file = f"{tiling}_{map}_{deadline}"
                print(f"Loaded {len(df)} rows from {result_csv}")
                print(f"Detected: {df['detected'].sum()} / {len(df)} "
                    f"({df['detected'].mean():.3f})")

                plot_all_success(df, file, save_dir, n_bins=bins_per_axes, smooth_sigma=smooth_sigma)


