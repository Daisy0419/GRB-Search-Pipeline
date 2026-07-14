import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from pathlib import Path

# -----------------------------
# Paper-friendly sizing/styling
# -----------------------------
# Good defaults for ACM/EMSOFT-style 2-column papers.
COLUMN_W = 3.35   # single column width (in)
FULL_W   = 7.00   # full width across two columns (in)
SMALL_H  = 2.35
WIDE_H   = 2.25

mpl.rcParams.update({
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.2,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def _prep_output_dir(output_dir: str | Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _style_ax(ax, xlabel, ylabel="Mapping time (s)", *, xscale=None, yscale=None):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if xscale:
        ax.set_xscale(xscale)
    if yscale:
        ax.set_yscale(yscale)
    ax.grid(True, linewidth=0.4, alpha=0.25)
    ax.tick_params(direction="in")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _save(fig, stem: str, output_dir: str | Path):
    output_dir = _prep_output_dir(output_dir)
    fig.savefig(output_dir / f"{stem}.pdf")
    fig.savefig(output_dir / f"{stem}.png", dpi=400)
    plt.close(fig)


def _scatter_with_cbar(ax, x, y, c, cmap, cbar_label, *, marker_size=12):
    # rasterized=True keeps vector PDFs small while preserving text as vector.
    sc = ax.scatter(
        x, y,
        c=c,
        cmap=cmap,
        s=marker_size,
        alpha=0.65,
        linewidths=0,
        rasterized=True,
    )
    cbar = plt.colorbar(sc, ax=ax, orientation="horizontal", pad=0.18, fraction=0.10)
    cbar.set_label(cbar_label)
    cbar.ax.tick_params(labelsize=7)
    return sc


def _running_median(ax, x, y, n_bins=12):
    """Overlay a simple binned median trend line for readability in print."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    finite = np.isfinite(x) & np.isfinite(y)
    x = x[finite]
    y = y[finite]
    if len(x) < 8:
        return

    edges = np.linspace(x.min(), x.max(), n_bins + 1)
    mids, meds = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (x >= lo) & (x < hi) if hi < edges[-1] else (x >= lo) & (x <= hi)
        if mask.sum() >= 3:
            mids.append((lo + hi) / 2)
            meds.append(np.median(y[mask]))

    if len(mids) >= 2:
        ax.plot(mids, meds, marker="o", markersize=2.5)


# -----------------------------
# Single-column figures
# -----------------------------
def plot_time_vs_nsrc(df, output_dir="."):
    fig, ax = plt.subplots(figsize=(COLUMN_W, SMALL_H), constrained_layout=True)
    _scatter_with_cbar(
        ax,
        df["n_src"],
        df["mapping_time"],
        df["n_bkg"],
        "viridis",
        r"$n_{\mathrm{bkg}}$",
    )
    _running_median(ax, df["n_src"], df["mapping_time"])
    _style_ax(ax, r"$n_{\mathrm{src}}$")
    _save(fig, "time_vs_nsrc_emsoft", output_dir)


def plot_time_vs_nbkg(df, output_dir="."):
    fig, ax = plt.subplots(figsize=(COLUMN_W, SMALL_H), constrained_layout=True)
    _scatter_with_cbar(
        ax,
        df["n_bkg"],
        df["mapping_time"],
        df["n_src"],
        "plasma",
        r"$n_{\mathrm{src}}$",
    )
    _running_median(ax, df["n_bkg"], df["mapping_time"])
    _style_ax(ax, r"$n_{\mathrm{bkg}}$")
    _save(fig, "time_vs_nbkg_emsoft", output_dir)


def plot_time_vs_ratio(df, output_dir="."):
    n_src = df["n_src"].to_numpy(dtype=float)
    n_bkg = df["n_bkg"].to_numpy(dtype=float)
    ratio = n_src / np.maximum(n_bkg, 1.0)
    total_events = n_src + n_bkg

    fig, ax = plt.subplots(figsize=(COLUMN_W, SMALL_H), constrained_layout=True)
    _scatter_with_cbar(
        ax,
        ratio,
        df["mapping_time"],
        total_events,
        "cividis",
        r"$n_{\mathrm{src}} + n_{\mathrm{bkg}}$",
    )
    _running_median(ax, ratio, df["mapping_time"])
    _style_ax(ax, r"$n_{\mathrm{src}}/n_{\mathrm{bkg}}$")
    _save(fig, "time_vs_ratio_emsoft", output_dir)


# -----------------------------
# Full-width figure for paper
# -----------------------------
def plot_time_scatter_combined(df, output_dir="."):
    n_src = df["n_src"].to_numpy(dtype=float)
    n_bkg = df["n_bkg"].to_numpy(dtype=float)
    y = df["mapping_time"].to_numpy(dtype=float)
    ratio = n_src / np.maximum(n_bkg, 1.0)

    fig, axes = plt.subplots(
        1, 3,
        figsize=(FULL_W, WIDE_H),
        sharey=True,
        constrained_layout=True,
    )

    for ax, x, xlabel in [
        (axes[0], n_src, r"$n_{\mathrm{src}}$"),
        (axes[1], n_bkg, r"$n_{\mathrm{bkg}}$"),
        (axes[2], ratio, r"$n_{\mathrm{src}}/n_{\mathrm{bkg}}$"),
    ]:
        ax.scatter(x, y, s=10, alpha=0.5, linewidths=0, rasterized=True)
        _running_median(ax, x, y)
        _style_ax(ax, xlabel, ylabel="Mapping time (s)" if ax is axes[0] else "")

    _save(fig, "time_scatter_combined_emsoft", output_dir)


# -----------------------------
# Optional replacement for 3D plot
# -----------------------------
def plot_time_hexbin(df, output_dir="."):
    """
    Better than 3D for a paper: easier to read in print and at column width.
    Shows density in (n_src, n_bkg) and colors bins by mean mapping time.
    """
    fig, ax = plt.subplots(figsize=(COLUMN_W, 2.6), constrained_layout=True)
    hb = ax.hexbin(
        df["n_src"],
        df["n_bkg"],
        C=df["mapping_time"],
        reduce_C_function=np.mean,
        gridsize=18,
        mincnt=1,
        linewidths=0.2,
        rasterized=True,
    )
    cbar = plt.colorbar(hb, ax=ax, orientation="horizontal", pad=0.18, fraction=0.10)
    cbar.set_label("Mean mapping time (s)")
    _style_ax(ax, r"$n_{\mathrm{src}}$", r"$n_{\mathrm{bkg}}$")
    _save(fig, "time_hexbin_emsoft", output_dir)


def plot_all_scatter(df, output_dir="."):
    plot_time_vs_nsrc(df, output_dir)
    plot_time_vs_nbkg(df, output_dir)
    plot_time_vs_ratio(df, output_dir)
    plot_time_scatter_combined(df, output_dir)
    plot_time_hexbin(df, output_dir)
    print(f"Saved paper-ready figures to {Path(output_dir).resolve()}")


if __name__ == "__main__":
    results_csv = "emsoft-stats.csv"
    output_dir = "."

    df = pd.read_csv(results_csv)
    plot_all_scatter(df, output_dir)
