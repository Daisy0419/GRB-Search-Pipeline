import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from scipy.ndimage import gaussian_filter
import os
import matplotlib as mpl

# COL_W = 3.33
# PAGE_W = 7.0
DPI = 300

mpl.rcParams.update({
    "font.family":      "serif",
    "font.serif":       ["Times", "Times New Roman", "DejaVu Serif"],
    "font.size":        8,
    "axes.labelsize":   8,
    "axes.titlesize":   9,
    "legend.fontsize":  7,
    "xtick.labelsize":  7,
    "ytick.labelsize":  7,
    # "axes.linewidth":   0.5,
    # "xtick.major.width": 0.4,
    # "ytick.major.width": 0.4,
    # "pdf.fonttype":     42,
    # "ps.fonttype":      42,
})


def build_binned_surface(df, value_col, n_bins=20, smooth_sigma=1.0):
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

    # ── Bin count heatmap ──
    # fig, ax = plt.subplots(figsize=(COL_W, COL_W * 0.8))
    fig, ax  = plt.subplots(figsize=(3.8, 3.3))
    masked = np.ma.masked_where(count_grid == 0, count_grid)
    im = ax.pcolormesh(src_centers, bkg_centers, masked,
                       cmap="viridis", shading="auto")
    cbar = plt.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Count per Bin", fontsize=7)
    cbar.ax.tick_params(labelsize=6)

    if n_bins <= 25:
        for bi in range(n_bins):
            for si in range(n_bins):
                c = count_grid[bi, si]
                if c > 0:
                    ax.text(src_centers[si], bkg_centers[bi], str(c),
                            ha="center", va="center", fontsize=4,
                            color="white")

    ax.set_xlabel("Source Events")
    ax.set_ylabel("Background Events")
    plt.tight_layout()
    plt.savefig("maps_per_bin.png", dpi=DPI, bbox_inches="tight",
                pad_inches=0.02)
    plt.close()

    return SRC, BKG, prob_smooth, grouped


def plot_surface_3d(SRC, BKG, prob_smooth, file, output_dir="."):
    prob_plot = np.ma.masked_invalid(prob_smooth)
    norm = plt.Normalize(0, 1)
    colors = cm.RdYlGn(norm(prob_plot))

    # fig = plt.figure(figsize=(COL_W, COL_W))
    fig = plt.figure(figsize=(3.8, 3.3))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(SRC, BKG, prob_plot,
                    facecolors=colors, alpha=0.85,
                    rstride=1, cstride=1,
                    linewidth=0.2, edgecolor="gray", shade=True)

    ax.set_xlabel("Background Events", labelpad=0)
    ax.set_ylabel("Source Events", labelpad=0)
    ax.set_zlabel("Success Probability", labelpad=-8)
    ax.set_zlim(0, 1.05)

    ax.tick_params(axis='x', pad=1, labelsize=6)
    ax.tick_params(axis='y', pad=1, labelsize=6)
    ax.tick_params(axis='z', pad=-4, labelsize=6)

    mappable = cm.ScalarMappable(norm=norm, cmap="RdYlGn")
    cbar = fig.colorbar(mappable, ax=ax, shrink=0.5, pad=0.08, aspect=20)
    cbar.set_label("Success Probability", fontsize=6)
    cbar.ax.tick_params(labelsize=5)

    ax.view_init(elev=25, azim=135)
    fig.subplots_adjust(left=0.0, right=0.78, bottom=0.0, top=1.05)
    filename = f"success_prob_surface_{file}.png"
    plt.savefig(f"{output_dir}/{filename}", dpi=DPI)
    plt.close()


def plot_wireframe_scatter(SRC, BKG, prob_smooth, grouped, file,
                           output_dir="."):
    prob_plot = np.ma.masked_invalid(prob_smooth)

    # fig = plt.figure(figsize=(COL_W, COL_W))
    fig = plt.figure(figsize=(3.8, 3.3))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_wireframe(SRC, BKG, prob_plot, color="gray", alpha=0.3,
                      rstride=1, cstride=1, linewidth=0.3)
    sc = ax.scatter(grouped["n_src"], grouped["n_bkg"], grouped["prob"],
                    c=grouped["prob"], cmap="RdYlGn",
                    s=grouped["n"] * 2 + 5, alpha=0.9,
                    edgecolors="k", linewidths=0.2,
                    vmin=0, vmax=1, zorder=5)

    ax.set_xlabel("Background Events", labelpad=0)
    ax.set_ylabel("Source Events", labelpad=0)
    ax.set_zlabel("Success Probability", labelpad=-8)
    ax.set_zlim(0, 1.05)

    ax.tick_params(axis='x', pad=1, labelsize=6)
    ax.tick_params(axis='y', pad=1, labelsize=6)
    ax.tick_params(axis='z', pad=-4, labelsize=6)

    cbar = fig.colorbar(sc, ax=ax, shrink=0.5, pad=0.08, aspect=20)
    cbar.set_label("Success Probability", fontsize=6)
    cbar.ax.tick_params(labelsize=5)

    ax.view_init(elev=25, azim=135)
    fig.subplots_adjust(left=0.0, right=0.78, bottom=0.0, top=1.05)
    filename = f"success_prob_scatter_{file}.png"
    plt.savefig(f"{output_dir}/{filename}", dpi=DPI)
    plt.close()


def plot_all_success(df, file, output_dir=".", n_bins=20, smooth_sigma=1.0):
    SRC, BKG, prob_smooth, grouped = build_binned_surface(
        df, "detected", n_bins, smooth_sigma)
    plot_surface_3d(SRC, BKG, prob_smooth, file, output_dir=output_dir)
    plot_wireframe_scatter(SRC, BKG, prob_smooth, grouped, file,
                           output_dir=output_dir)
    print(f"Success probability plots saved to {output_dir}/")


if __name__ == "__main__":
    result_dir = "verify_result/search_success_result"
    save_dir = "."
    bins_per_axes = 20
    smooth_sigma = 0.0

    tiling = "2.5x2.5_tiling"
    map_ = "utility"
    deadline = "30"
    result_csv = f"{result_dir}/{tiling}_{map_}_{deadline}.csv"
    
    df = pd.read_csv(result_csv)
    file = f"{tiling}_{map}_{deadline}"
    print(f"Loaded {len(df)} rows from {result_csv}")
    print(f"Detected: {df['detected'].sum()} / {len(df)} "
          f"({df['detected'].mean():.3f})")
    plot_all_success(df, file, save_dir, n_bins=bins_per_axes, smooth_sigma=smooth_sigma)



    # tilings = ["2.5x2.5_tiling", "5.36x4.5_tiling"]
    # maps = ["utility", "nodeadline", "gt"]
    # deadlines = [10, 20, 30, 60, 90]
    # for tiling in tilings:
    #     for map_ in maps:
    #         for deadline in deadlines:
    #             result_csv = f"{result_dir}/{tiling}_{map_}_{deadline}.csv"
    #             if not os.path.exists(result_csv):
    #                 print(f"{result_csv} does not exist")
    #                 continue
    #             df = pd.read_csv(result_csv)
    #             file = f"{tiling}_{map_}_{deadline}"
    #             print(f"Loaded {len(df)} rows from {result_csv}")
    #             print(f"Detected: {df['detected'].sum()} / {len(df)} "
    #                   f"({df['detected'].mean():.3f})")
    #             plot_all_success(df, file, save_dir,
    #                              n_bins=bins_per_axes,
    #                              smooth_sigma=smooth_sigma)