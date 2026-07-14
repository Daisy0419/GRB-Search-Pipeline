# import csv
# import math
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# from pathlib import Path

# def _ensure_source_coords(df):
#     """Parse source column (dec:ra) into src_dec, src_ra."""
#     if "src_ra" not in df.columns or "src_dec" not in df.columns:
#         def _parse(s):
#             parts = str(s).split(":")
#             return float(parts[0]), float(parts[1])
#         parsed = df["source"].apply(_parse)
#         df["src_dec"] = parsed.apply(lambda x: x[0])
#         df["src_ra"] = parsed.apply(lambda x: x[1])
#     return df


# def plot_detection_vs_nsrc(df_det, output_dir="."):
#     """Detection cost vs n_src."""
#     fig, ax = plt.subplots(figsize=(8, 6))
#     sc = ax.scatter(df_det["n_src"], df_det["detection_cost"],
#                     c=df_det["n_bkg"], cmap="viridis", alpha=0.6, s=20)
#     ax.set_xlabel("n_src_events", fontsize=12)
#     ax.set_ylabel("Detection Cost (s)", fontsize=12)
#     ax.set_title("Detection Cost vs N_src", fontsize=13)
#     plt.colorbar(sc, ax=ax, label="n_bkg_events")
#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_vs_nsrc.png", dpi=150)
#     plt.close()


# def plot_detection_vs_nbkg(df_det, output_dir="."):
#     """Detection cost vs n_bkg."""
#     fig, ax = plt.subplots(figsize=(8, 6))
#     sc = ax.scatter(df_det["n_bkg"], df_det["detection_cost"],
#                     c=df_det["n_src"], cmap="plasma", alpha=0.6, s=20)
#     ax.set_xlabel("n_bkg_events", fontsize=12)
#     ax.set_ylabel("Detection Cost (s)", fontsize=12)
#     ax.set_title("Detection Cost vs N_bkg", fontsize=13)
#     plt.colorbar(sc, ax=ax, label="n_src_events")
#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_vs_nbkg.png", dpi=150)
#     plt.close()


# def plot_detection_vs_ratio(df_det, output_dir="."):
#     """Detection cost vs n_src/n_bkg ratio."""
#     n_src = df_det["n_src"].values.astype(float)
#     n_bkg = df_det["n_bkg"].values.astype(float)
#     ratio = n_src / np.maximum(n_bkg, 1.0)

#     fig, ax = plt.subplots(figsize=(8, 6))
#     sc = ax.scatter(ratio, df_det["detection_cost"],
#                     c=df_det["detection_cost"], cmap="RdYlGn_r",
#                     alpha=0.5, s=20)
#     ax.set_xlabel("n_src / n_bkg", fontsize=12)
#     ax.set_ylabel("Detection Cost (s)", fontsize=12)
#     ax.set_title("Detection Cost vs Src/Bkg Ratio", fontsize=13)
#     plt.colorbar(sc, ax=ax, label="Detection Cost (s)")
#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_vs_ratio.png", dpi=150)
#     plt.close()


# def plot_detection_scatter_combined(df_det, output_dir="."):
#     """Combining vs n_src, vs n_bkg, vs ratio."""
#     n_src = df_det["n_src"].values.astype(float)
#     n_bkg = df_det["n_bkg"].values.astype(float)
#     y = df_det["detection_cost"].values
#     ratio = n_src / np.maximum(n_bkg, 1.0)

#     fig, axes = plt.subplots(1, 3, figsize=(20, 6))

#     sc0 = axes[0].scatter(n_src, y, c=n_bkg, cmap="viridis", alpha=0.6, s=20)
#     axes[0].set_xlabel("n_src_events", fontsize=12)
#     axes[0].set_ylabel("Detection Cost (s)", fontsize=12)
#     axes[0].set_title("Detection Cost vs N_src", fontsize=13)
#     plt.colorbar(sc0, ax=axes[0], label="n_bkg_events")

#     sc1 = axes[1].scatter(n_bkg, y, c=n_src, cmap="plasma", alpha=0.6, s=20)
#     axes[1].set_xlabel("n_bkg_events", fontsize=12)
#     axes[1].set_ylabel("Detection Cost (s)", fontsize=12)
#     axes[1].set_title("Detection Cost vs N_bkg", fontsize=13)
#     plt.colorbar(sc1, ax=axes[1], label="n_src_events")

#     sc2 = axes[2].scatter(ratio, y, c=y, cmap="RdYlGn_r", alpha=0.5, s=20)
#     axes[2].set_xlabel("n_src / n_bkg", fontsize=12)
#     axes[2].set_ylabel("Detection Cost (s)", fontsize=12)
#     axes[2].set_title("Detection Cost vs Src/Bkg Ratio", fontsize=13)
#     plt.colorbar(sc2, ax=axes[2], label="Detection Cost (s)")

#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_scatter_combined.png", dpi=150)
#     plt.close()


# def plot_detection_vs_sum_tiles(df_det, output_dir="."):
#     """Detection cost vs sum_tiles."""
#     n_src = df_det["n_src"].values.astype(float)
#     n_bkg = df_det["n_bkg"].values.astype(float)
#     ratio = n_src / np.maximum(n_bkg, 1.0)

#     fig, ax = plt.subplots(figsize=(8, 6))
#     sc = ax.scatter(df_det["sum_tiles"], df_det["detection_cost"],
#                     c=ratio, cmap="plasma", alpha=0.5, s=20)
#     ax.set_xlabel("SumTiles", fontsize=12)
#     ax.set_ylabel("Detection Cost (s)", fontsize=12)
#     ax.set_title("Detection Cost vs SumTiles", fontsize=13)
#     plt.colorbar(sc, ax=ax, label="n_src / n_bkg")
#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_vs_sumtiles.png", dpi=150)
#     plt.close()


# def plot_detection_vs_src_ra(df_det, output_dir="."):
#     """Detection cost vs source RA."""
#     df_det = _ensure_source_coords(df_det)
#     n_src = df_det["n_src"].values.astype(float)
#     n_bkg = df_det["n_bkg"].values.astype(float)
#     ratio = n_src / np.maximum(n_bkg, 1.0)

#     fig, ax = plt.subplots(figsize=(8, 6))
#     sc = ax.scatter(df_det["src_ra"], df_det["detection_cost"],
#                     c=ratio, cmap="plasma", alpha=0.5, s=20)
#     ax.set_xlabel("Source RA (deg)", fontsize=12)
#     ax.set_ylabel("Detection Cost (s)", fontsize=12)
#     ax.set_title("Detection Cost vs Source RA", fontsize=13)
#     plt.colorbar(sc, ax=ax, label="n_src / n_bkg")
#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_vs_src_ra.png", dpi=150)
#     plt.close()


# def plot_detection_vs_src_dec(df_det, output_dir="."):
#     """Detection cost vs source Dec."""
#     df_det = _ensure_source_coords(df_det)
#     n_src = df_det["n_src"].values.astype(float)
#     n_bkg = df_det["n_bkg"].values.astype(float)
#     ratio = n_src / np.maximum(n_bkg, 1.0)

#     fig, ax = plt.subplots(figsize=(8, 6))
#     sc = ax.scatter(df_det["src_dec"], df_det["detection_cost"],
#                     c=ratio, cmap="plasma", alpha=0.5, s=20)
#     ax.set_xlabel("Source Dec (deg)", fontsize=12)
#     ax.set_ylabel("Detection Cost (s)", fontsize=12)
#     ax.set_title("Detection Cost vs Source Dec", fontsize=13)
#     plt.colorbar(sc, ax=ax, label="n_src / n_bkg")
#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_vs_src_dec.png", dpi=150)
#     plt.close()


# def plot_detection_vs_src_radec_combined(df_det, output_dir="."):
#     """Detection cost vs RA and Dec side by side."""
#     df_det = _ensure_source_coords(df_det)
#     y = df_det["detection_cost"].values

#     fig, axes = plt.subplots(1, 2, figsize=(16, 6))

#     sc0 = axes[0].scatter(df_det["src_ra"], y, c=y, cmap="RdYlGn_r",
#                           alpha=0.5, s=20, edgecolors="k", linewidths=0.2)
#     axes[0].set_xlabel("Source RA (deg)", fontsize=12)
#     axes[0].set_ylabel("Detection Cost (s)", fontsize=12)
#     axes[0].set_title("Detection Cost vs Source RA", fontsize=13)
#     plt.colorbar(sc0, ax=axes[0], label="Detection Cost (s)")

#     sc1 = axes[1].scatter(df_det["src_dec"], y, c=y, cmap="RdYlGn_r",
#                           alpha=0.5, s=20, edgecolors="k", linewidths=0.2)
#     axes[1].set_xlabel("Source Dec (deg)", fontsize=12)
#     axes[1].set_ylabel("Detection Cost (s)", fontsize=12)
#     axes[1].set_title("Detection Cost vs Source Dec", fontsize=13)
#     plt.colorbar(sc1, ax=axes[1], label="Detection Cost (s)")

#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_vs_src_radec.png", dpi=150)
#     plt.close()


# def plot_detection_3d(df_det, output_dir="."):
#     """3D scatter: n_src, n_bkg, detection_cost."""
#     fig = plt.figure(figsize=(12, 9))
#     ax = fig.add_subplot(111, projection="3d")
#     sc = ax.scatter(df_det["n_src"], df_det["n_bkg"], df_det["detection_cost"],
#                     c=df_det["detection_cost"], cmap="RdYlGn_r",
#                     s=20, alpha=0.6, edgecolors="k", linewidths=0.2)
#     ax.set_xlabel("n_src_events", fontsize=11, labelpad=10)
#     ax.set_ylabel("n_bkg_events", fontsize=11, labelpad=10)
#     ax.set_zlabel("Detection Cost (s)", fontsize=11, labelpad=10)
#     ax.set_title("Detection Cost vs (N_src, N_bkg)", fontsize=13, pad=20)
#     fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.1, label="Detection Cost (s)")
#     ax.view_init(elev=25, azim=135)
#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_3d.png", dpi=150, bbox_inches="tight")
#     plt.close()


# def plot_detection_3d_multiview(df_det, output_dir="."):
#     """3D scatter from multiple viewing angles."""
#     views = [
#         (25, 135,  "Front-left"),
#         (25, -50,  "Front-right"),
#         (25, 45,   "Back-right"),
#         (25, 225,  "Back-left"),
#         (70, 135,  "Top-down (angled)"),
#         (5,  135,  "Near-horizontal"),
#     ]

#     nrows, ncols = 2, 3
#     fig = plt.figure(figsize=(8 * ncols, 7 * nrows))

#     for i, (elev, azim, label) in enumerate(views):
#         ax = fig.add_subplot(nrows, ncols, i + 1, projection="3d")
#         sc = ax.scatter(df_det["n_src"], df_det["n_bkg"], df_det["detection_cost"],
#                         c=df_det["detection_cost"], cmap="RdYlGn_r",
#                         s=20, alpha=0.6, edgecolors="k", linewidths=0.2)
#         ax.set_xlabel("n_src_events", fontsize=10, labelpad=8)
#         ax.set_ylabel("n_bkg_events", fontsize=10, labelpad=8)
#         ax.set_zlabel("Detection Cost (s)", fontsize=10, labelpad=8)
#         ax.set_title(f"{label}\n(elev={elev}, azim={azim})", fontsize=11)
#         ax.view_init(elev=elev, azim=azim)
#         ax.tick_params(labelsize=8)

#     fig.suptitle("Detection Cost vs (N_src, N_bkg) - Multiple Views",
#                  fontsize=14, y=1.01)
#     plt.tight_layout()
#     plt.savefig(f"{output_dir}/detection_3d_multiview.png", dpi=150, bbox_inches="tight")
#     plt.close()


# def plot_all_scatter(df_det, output_dir="."):
#     plot_detection_vs_nsrc(df_det, output_dir)
#     plot_detection_vs_nbkg(df_det, output_dir)
#     plot_detection_vs_ratio(df_det, output_dir)
#     # plot_detection_scatter_combined(df_det, output_dir)
#     plot_detection_vs_sum_tiles(df_det, output_dir)
#     plot_detection_vs_src_ra(df_det, output_dir)
#     plot_detection_vs_src_dec(df_det, output_dir)
#     # plot_detection_vs_src_radec_combined(df_det, output_dir)
#     # plot_detection_3d(df_det, output_dir)
#     plot_detection_3d_multiview(df_det, output_dir)
#     print(f"All scatter plots saved to {output_dir}/")


# if __name__ == "__main__":
#     tiling = "5.36x4.5_tiling"
#     results_csv = f"{tiling}.csv"
#     output_dir = "."

#     df = pd.read_csv(results_csv)
#     df_det = df[df["detected"]].copy()
#     if len(df_det) == 0:
#         print("No detections found.")
#         exit(1)

#     print(f"\nDetected rows: {len(df_det)}")
#     print(f"  detection_cost: min={df_det['detection_cost'].min():.2f}  "
#           f"max={df_det['detection_cost'].max():.2f}  "
#           f"mean={df_det['detection_cost'].mean():.2f}")
#     print(f"  n_src: [{df_det['n_src'].min()}, {df_det['n_src'].max()}]")
#     print(f"  n_bkg: [{df_det['n_bkg'].min()}, {df_det['n_bkg'].max()}]")
#     print(f"  sum_tiles: [{df_det['sum_tiles'].min()}, {df_det['sum_tiles'].max()}]")

#     plot_all_scatter(df_det, output_dir)



import csv
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib as mpl


mpl.rcParams.update({
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
    # Swap x and y so s ends up on the right, b on the left
    sc = ax.scatter(df_det["n_bkg"], df_det["n_src"], df_det["runtime"],
                    c=df_det["runtime"], cmap="RdYlGn_r",
                    s=8, alpha=0.6, edgecolors="k", linewidths=0.2)

    ax.set_xlabel("Source Events, s", labelpad=0)
    ax.set_ylabel("Background Events, b", labelpad=0)
    ax.set_zlabel("Search Planning Time (s)", labelpad=0)

    ax.tick_params(axis='x', pad=1)
    ax.tick_params(axis='y', pad=1)
    ax.tick_params(axis='z', pad=0)

    ax.view_init(elev=25, azim=135)

    # Give more room on the right for the z-label
    fig.subplots_adjust(left=0.0, right=0.87, bottom=-0.05, top=1.1)
    # fig.subplots_adjust(left=0.0, right=0.78, bottom=0.0, top=1.05)
    # plt.savefig(f"{output_dir}/time_3d.png", dpi=300, bbox_inches="tight")
    plt.savefig(f"{output_dir}/search_planning_time.png", dpi=300)
    # plt.savefig(f"{output_dir}/time_3d.png", dpi=300,
    #         bbox_inches="tight", pad_inches=0.2)
    plt.close()



if __name__ == "__main__":
    tiling = "5.36x4.5_tiling"
    # tiling = "2.5x2.5_tiling"
    results_csv = f"{tiling}.csv"
    output_dir = "."

    df = pd.read_csv(results_csv)
    df_det = df[df["detected"]].copy()
    if len(df_det) == 0:
        print("No detections found.")
        exit(1)

    print(f"\nDetected rows: {len(df_det)}")
    print(f"  detection_cost: min={df_det['detection_cost'].min():.2f}  "
          f"max={df_det['detection_cost'].max():.2f}  "
          f"mean={df_det['detection_cost'].mean():.2f}")
    print(f"  n_src: [{df_det['n_src'].min()}, {df_det['n_src'].max()}]")
    print(f"  n_bkg: [{df_det['n_bkg'].min()}, {df_det['n_bkg'].max()}]")
    print(f"  sum_tiles: [{df_det['sum_tiles'].min()}, {df_det['sum_tiles'].max()}]")

    plot_time_3d(df_det, output_dir)