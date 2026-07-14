"""
Fit Gen Time ~ f(n_src, n_bkg) for one or more quantile levels.

Binning: 2D percentile grid on (n_src, n_bkg).
"""

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import norm
from sklearn.metrics import r2_score

mpl.rcParams["text.usetex"] = False


# ═══════════════════════════════════════════════════════════════════════════════
# Models  (X = (n_src, n_bkg))
# ═══════════════════════════════════════════════════════════════════════════════

def power_src_bkg(X, a, b, c, d):
    n_src, n_bkg = X
    ns = np.maximum(n_src, 1.0)
    nb = np.maximum(n_bkg, 1.0)
    return a * (ns ** (-b)) * (nb ** c) + d

def linear_src_bkg(X, a, b, c):
    n_src, n_bkg = X
    ns = np.maximum(n_src, 1.0)
    return a / ns + b * n_bkg + c

def log_src_bkg(X, a, b, c, d):
    n_src, n_bkg = X
    ns = np.maximum(n_src, 1.0)
    nb = np.maximum(n_bkg, 1.0)
    return (a * np.log1p(nb / ns) +
            b * np.log1p(nb) +
            c * np.log1p(ns) + d)

def exp_ratio_bkg(X, a, b, c, d):
    n_src, n_bkg = X
    nb = np.maximum(n_bkg, 1.0)
    r = n_src / nb
    return a * np.exp(-b * r) * (nb ** c) + d

def mm_ratio_bkg(X, a, b, c, d):
    n_src, n_bkg = X
    nb = np.maximum(n_bkg, 1.0)
    r = n_src / nb
    return a * (nb ** c) / (1.0 + b * r) + d

def rational_src_bkg(X, a, b, c, d, e):
    n_src, n_bkg = X
    ns = np.maximum(n_src, 1.0)
    nb = np.maximum(n_bkg, 1.0)
    return a * (nb ** c) / np.power(ns + b, d) + e

def stretched_exp_ratio_bkg(X, a, b, k, c, d):
    n_src, n_bkg = X
    nb = np.maximum(n_bkg, 1.0)
    r = n_src / nb
    t = np.power(np.maximum(b * r, 0.0), k)
    return a * np.exp(-t) * (nb ** c) + d

def stretched_exp_src_times_bkg(X, a, b, k, c, d):
    n_src, n_bkg = X
    ns = np.maximum(n_src, 1.0)
    nb = np.maximum(n_bkg, 1.0)
    t = np.power(np.maximum(b * ns, 0.0), k)
    return a * np.exp(-t) * (nb ** c) + d

def logistic_ratio_bkg(X, a, b, r0, k, c, d):
    n_src, n_bkg = X
    nb = np.maximum(n_bkg, 1.0)
    r = n_src / nb
    x = np.clip(k * (r - r0), -60.0, 60.0)
    sig = 1.0 / (1.0 + np.exp(x))
    return a * (nb ** c) * sig + d

def softplus_gap(X, a, alpha, tau, c, d):
    n_src, n_bkg = X
    nb = np.maximum(n_bkg, 1.0)
    t = np.maximum(tau, 1e-6)
    z = np.clip((n_bkg - alpha * n_src) / t, -60.0, 60.0)
    softplus = np.log1p(np.exp(z))
    return a * softplus * (nb ** c) + d

def loglink_interaction(X, a, b, c, e, d):
    n_src, n_bkg = X
    ns = np.maximum(n_src, 1.0)
    nb = np.maximum(n_bkg, 1.0)
    Ls = np.log1p(ns)
    Lb = np.log1p(nb)
    lin = np.clip(a + b * Lb - c * Ls + e * Lb * Ls, -60.0, 60.0)
    return np.exp(lin) + d

def poly_logratio_logbkg(X, a0, a1, a2, b1, b2, d):
    n_src, n_bkg = X
    nb = np.maximum(n_bkg, 1.0)
    r = n_src / nb
    lr = np.log1p(np.maximum(r, 0.0))
    lb = np.log1p(nb)
    return a0 + a1 * lr + a2 * lr * lr + b1 * lb + b2 * lb * lb + d


MODELS = {
    "power_src_bkg":               (power_src_bkg,               [1e4, 0.5, 0.5, 10],                 "a/src^b * bkg^c + d"),
    "linear_src_bkg":              (linear_src_bkg,              [1e4, 0.01, 10],                     "a/src + b*bkg + c"),
    "log_src_bkg":                 (log_src_bkg,                 [50, 10, -10, 10],                   "a*ln(1+bkg/src)+b*ln(1+bkg)+c*ln(1+src)+d"),
    "exp_ratio_bkg":               (exp_ratio_bkg,               [100, 1, 0.1, 10],                   "a*exp(-b*src/bkg)*bkg^c + d"),
    "mm_ratio_bkg":                (mm_ratio_bkg,                [500.0, 1.0, 0.5, 10.0],             "a*bkg^c / (1+b*src/bkg) + d"),
    "rational_src_bkg":            (rational_src_bkg,            [1e5, 10.0, 0.5, 1.0, 10.0],         "a*bkg^c / (src+b)^d + e"),
    "stretched_exp_ratio_bkg":     (stretched_exp_ratio_bkg,     [500.0, 1.0, 0.7, 0.5, 10.0],        "a*exp(-(b*r)^k)*bkg^c + d"),
    "stretched_exp_src_times_bkg": (stretched_exp_src_times_bkg, [500.0, 1e-2, 0.7, 0.5, 10.0],       "a*exp(-(b*src)^k)*bkg^c + d"),
    "logistic_ratio_bkg":          (logistic_ratio_bkg,          [500.0, 1.0, 0.5, 5.0, 0.5, 10.0],   "a*bkg^c*sig(k*(r-r0)) + d"),
    "softplus_gap":                (softplus_gap,                [50.0, 2.0, 50.0, 0.0, 10.0],        "a*sp((bkg-alpha*src)/tau)*bkg^c + d"),
    "loglink_interaction":         (loglink_interaction,         [3.0, 0.5, 0.5, 0.0, 0.0],           "exp(a+b*lnB-c*lnS+e*lnB*lnS)+d"),
    "poly_logratio_logbkg":        (poly_logratio_logbkg,        [10.0, -200.0, 50.0, 30.0, 5.0, 0.0],"a0+a1*lnR+a2*lnR^2+b1*lnB+b2*lnB^2+d"),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Binning helper
# ═══════════════════════════════════════════════════════════════════════════════

def _bin_stats_2d(n_src, n_bkg, cost, n_bins_per_axis, quantiles):
    """Bin on a 2D percentile grid of (n_src, n_bkg).

    Parameters
    ----------
    quantiles : list[float]

    Returns
    -------
    binned    : dict[f"q{int(q*100)}"] -> {X, y, counts}
    src_edges, bkg_edges
    """
    # src_edges = np.unique(np.percentile(n_src, np.linspace(0, 100, n_bins_per_axis + 1)))
    # bkg_edges = np.unique(np.percentile(n_bkg, np.linspace(0, 100, n_bins_per_axis + 1)))
    src_edges = np.linspace(n_src.min(), n_src.max(), n_bins_per_axis + 1)
    bkg_edges = np.linspace(n_bkg.min(), n_bkg.max(), n_bins_per_axis + 1)


    src_idx = np.digitize(n_src, src_edges[1:-1])
    bkg_idx = np.digitize(n_bkg, bkg_edges[1:-1])

    qkeys   = [f"q{int(q * 100)}" for q in quantiles]
    targets = {k: [] for k in qkeys}
    bin_src, bin_bkg, bin_counts = [], [], []

    for si in range(len(src_edges) - 1):
        for bi in range(len(bkg_edges) - 1):
            mask = (src_idx == si) & (bkg_idx == bi)
            if mask.sum() < 2:
                continue
            c = cost[mask]
            bin_src.append(0.5 * (src_edges[si] + src_edges[si + 1]))
            bin_bkg.append(0.5 * (bkg_edges[bi] + bkg_edges[bi + 1]))
            bin_counts.append(mask.sum())
            for q, k in zip(quantiles, qkeys):
                targets[k].append(np.percentile(c, q * 100))

    bin_src    = np.array(bin_src,    dtype=float)
    bin_bkg    = np.array(bin_bkg,    dtype=float)
    bin_counts = np.array(bin_counts, dtype=int)
    X_bin      = (bin_src, bin_bkg)

    binned = {k: dict(X=X_bin, y=np.array(targets[k], dtype=float), counts=bin_counts)
              for k in qkeys}
    return binned, src_edges, bkg_edges


# ═══════════════════════════════════════════════════════════════════════════════
# Bin count heatmap
# ═══════════════════════════════════════════════════════════════════════════════

def plot_bin_counts_heatmap(binned, src_edges, bkg_edges, title="Samples per bin"):
    any_target       = next(iter(binned.values()))
    bin_src, bin_bkg = any_target["X"]
    counts           = any_target["counts"]

    src_centers = 0.5 * (src_edges[:-1] + src_edges[1:])
    bkg_centers = 0.5 * (bkg_edges[:-1] + bkg_edges[1:])

    grid = np.full((len(bkg_centers), len(src_centers)), np.nan)
    for s, b, n in zip(bin_src, bin_bkg, counts):
        si = int(np.argmin(np.abs(src_centers - s)))
        bi = int(np.argmin(np.abs(bkg_centers - b)))
        grid[bi, si] = n

    masked = np.ma.masked_where(np.isnan(grid), grid)

    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.pcolormesh(src_edges, bkg_edges, masked, cmap="viridis", shading="auto")
    plt.colorbar(im, ax=ax, label="Count per bin")

    for s, b, n in zip(bin_src, bin_bkg, counts):
        ax.text(s, b, str(int(n)), ha="center", va="center",
                fontsize=6, color="white")

    ax.set_xlabel("n_src")
    ax.set_ylabel("n_bkg")
    ax.set_title(title)
    plt.tight_layout()
    plt.show()


# ═══════════════════════════════════════════════════════════════════════════════
# Fitting helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _fit_models_to_target(X_bin, y_bin, sigma=None):
    results = {}
    for name, (func, p0, formula) in MODELS.items():
        try:
            popt, _ = curve_fit(func, X_bin, y_bin, p0=p0, maxfev=100000,
                                sigma=sigma, absolute_sigma=False)
            y_pred = func(X_bin, *popt)
            r2     = r2_score(y_bin, y_pred)
            rmse   = float(np.sqrt(np.mean((y_bin - y_pred) ** 2)))
            mae    = float(np.mean(np.abs(y_bin - y_pred)))
            n_p    = len(popt)
            n_d    = len(y_bin)
            adj_r2 = 1 - (1 - r2) * (n_d - 1) / max(n_d - n_p - 1, 1)
            results[name] = dict(params=popt, r2=r2, adj_r2=adj_r2, rmse=rmse,
                                 mae=mae, n_params=n_p, func=func, formula=formula)
        except Exception as e:
            results[name] = None
            print(f"    {name:30s}: FAILED ({e})")
    return {k: v for k, v in results.items() if v is not None}


def _print_table(valid, label):
    sorted_names = sorted(valid, key=lambda k: -valid[k]["r2"])
    print(f"\n  ── {label} ──")
    print(f"  {'Model':30s} {'Formula':46s} {'R2':>8s} {'RMSE':>8s} {'MAE':>8s}")
    print(f"  {'-'*96}")
    for name in sorted_names:
        r = valid[name]
        print(f"  {name:30s} {r['formula'][:46]:46s} "
              f"{r['r2']:>8.4f} {r['rmse']:>8.2f} {r['mae']:>8.2f}")
    best = sorted_names[0]
    r    = valid[best]
    print(f"  Best: {best}  R2={r['r2']:.4f}")
    ps = ", ".join(f"{v:.6f}" for v in r["params"])
    print(f"  Params: [{ps}]")
    return sorted_names


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

def fit_quantiles(df_det, output_dir=".", n_bins_per_axis=20,
                  quantiles=(0.50, 0.75, 0.90, 0.95, 0.99),
                  min_bin_count=25):
    """Fit parametric models to multiple quantile levels of Gen Time.

    Parameters
    ----------
    quantiles : sequence of float, e.g. [0.90, 0.95, 0.99]
    """
    quantiles = sorted(quantiles)
    qkeys     = [f"q{int(q * 100)}" for q in quantiles]

    n_src = df_det["n_src"].values.astype(float)
    n_bkg = df_det["n_bkg"].values.astype(float)
    cost  = df_det["mapping_time"].values.astype(float)

    print(f"Quantile fitting on {len(cost)} raw points")
    print(f"  n_src:     [{n_src.min():.0f}, {n_src.max():.0f}]")
    print(f"  n_bkg:     [{n_bkg.min():.0f}, {n_bkg.max():.0f}]")
    print(f"  cost:      [{cost.min():.2f}, {cost.max():.2f}]")
    print(f"  quantiles: {quantiles}")
    print(f"  min_bin_count: {min_bin_count}")

    # ── Bin ──────────────────────────────────────────────────────────────────
    binned, src_edges, bkg_edges = _bin_stats_2d(
        n_src, n_bkg, cost, n_bins_per_axis, quantiles)

    # ── Filter sparse bins ───────────────────────────────────────────────────
    mask       = next(iter(binned.values()))["counts"] >= min_bin_count
    n_filtered = (~mask).sum()
    print(f"  Dropping {n_filtered} bins with <{min_bin_count} samples")
    for k in qkeys:
        b = binned[k]
        binned[k] = dict(
            X=(b["X"][0][mask], b["X"][1][mask]),
            y=b["y"][mask],
            counts=b["counts"][mask],
        )

    plot_bin_counts_heatmap(binned, src_edges, bkg_edges)
    print(f"  Bins after filter: {mask.sum()}")

    # ── Fit ──────────────────────────────────────────────────────────────────
    all_results = {}
    all_sorted  = {}

    for q, k in zip(quantiles, qkeys):
        X_bin  = binned[k]["X"]
        y_bin  = binned[k]["y"]
        counts = binned[k]["counts"]
        sigma  = 1.0 / np.sqrt(np.maximum(counts, 1))
        label  = f"Quantile p={q}"

        print(f"\n{'='*100}")
        print(f"Target: {label}   ({len(y_bin)} bins, "
              f"y in [{y_bin.min():.2f}, {y_bin.max():.2f}])")

        valid        = _fit_models_to_target(X_bin, y_bin, sigma=sigma)
        sorted_names = _print_table(valid, label)
        all_results[k] = valid
        all_sorted[k]  = sorted_names

    # ═════════════════════════════════════════════════════════════════════════
    # Plots
    # ═════════════════════════════════════════════════════════════════════════

    ratio_raw = n_src / np.maximum(n_bkg, 1.0)
    cmap      = plt.cm.plasma
    colors    = {k: cmap(i / max(len(qkeys) - 1, 1)) for i, k in enumerate(qkeys)}

    # ── Fig 1: R² comparison ─────────────────────────────────────────────────
    ncols = min(len(qkeys), 4)
    nrows = int(np.ceil(len(qkeys) / ncols))
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(5 * ncols, max(5, len(MODELS) * 0.4) * nrows),
                             squeeze=False)
    axes_flat = axes.flatten()

    for i, (q, k) in enumerate(zip(quantiles, qkeys)):
        ax         = axes_flat[i]
        valid      = all_results[k]
        snames     = all_sorted[k]
        names_plot = snames[::-1]
        r2_vals    = [valid[n]["r2"] for n in names_plot]

        bars = ax.barh(names_plot, r2_vals, color=colors[k], edgecolor="k",
                       linewidth=0.5, alpha=0.85)
        ax.set_xlabel("R²", fontsize=10)
        ax.set_title(f"Quantile p={q}", fontsize=11, fontweight="bold")
        for bar, r2v in zip(bars, r2_vals):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                    f"{r2v:.4f}", va="center", fontsize=7)

    for j in range(len(qkeys), len(axes_flat)):
        axes_flat[j].set_visible(False)

    plt.suptitle("Model R² — Gen Time Quantile Fits", fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/map_quantile_r2_comparison.png",
                dpi=150, bbox_inches="tight")
    plt.close()

    # ── Fig 2: Best-model 3D surface per quantile ────────────────────────────
    n_grid   = 60
    src_grid = np.linspace(max(n_src.min(), 1), n_src.max(), n_grid)
    bkg_grid = np.linspace(max(n_bkg.min(), 1), n_bkg.max(), n_grid)
    SRC_G, BKG_G = np.meshgrid(src_grid, bkg_grid)
    X_grid = (SRC_G.ravel(), BKG_G.ravel())

    ncols = min(len(qkeys), 3)
    nrows = int(np.ceil(len(qkeys) / ncols))
    fig   = plt.figure(figsize=(7 * ncols, 6 * nrows))

    for i, (q, k) in enumerate(zip(quantiles, qkeys)):
        ax        = fig.add_subplot(nrows, ncols, i + 1, projection="3d")
        valid     = all_results[k]
        best_name = all_sorted[k][0]
        r         = valid[best_name]

        Z_pred = r["func"](X_grid, *r["params"]).reshape(SRC_G.shape)
        ax.plot_surface(SRC_G, BKG_G, Z_pred, alpha=0.45, cmap="coolwarm",
                        edgecolor="none", rstride=3, cstride=3)

        X_bin = binned[k]["X"]
        y_bin = binned[k]["y"]
        ax.scatter(X_bin[0], X_bin[1], y_bin, s=25, color="black",
                   edgecolors="white", linewidths=0.4, zorder=10, depthshade=True)

        ax.set_xlabel("n_src", fontsize=8, labelpad=2)
        ax.set_ylabel("n_bkg", fontsize=8, labelpad=2)
        ax.set_zlabel("time (s)", fontsize=8, labelpad=2)
        ax.set_title(f"p={q}\n{best_name}  R²={r['r2']:.4f}", fontsize=9)
        ax.tick_params(labelsize=6)
        ax.view_init(elev=25, azim=-50)

    plt.suptitle("Best-model 3D surfaces — Gen Time Quantiles", fontsize=14, y=1.01)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/map_quantile_3d_best.png", dpi=150, bbox_inches="tight")
    plt.close()

    # ── Fig 3: Overlay — raw + best-model curves for all quantiles ───────────
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.scatter(ratio_raw, cost, alpha=0.06, s=5, color="grey", label="raw data")

    ratio_smooth   = np.linspace(ratio_raw.min(), ratio_raw.max(), 300)
    median_bkg_val = float(np.median(n_bkg))
    X_smooth = (ratio_smooth * median_bkg_val,
                np.full_like(ratio_smooth, median_bkg_val))

    for q, k in zip(quantiles, qkeys):
        valid     = all_results[k]
        best_name = all_sorted[k][0]
        r         = valid[best_name]
        color     = colors[k]

        X_bin     = binned[k]["X"]
        y_bin     = binned[k]["y"]
        bin_ratio = X_bin[0] / np.maximum(X_bin[1], 1.0)

        ax.scatter(bin_ratio, y_bin, s=30, color=color, edgecolors="k",
                   linewidths=0.4, zorder=5, alpha=0.7)
        y_smooth = r["func"](X_smooth, *r["params"])
        ax.plot(ratio_smooth, y_smooth, color=color, lw=2.0, alpha=0.9,
                label=f"p={q}: {best_name} (R²={r['r2']:.4f})")

    ax.set_xlabel("n_src / n_bkg", fontsize=13)
    ax.set_ylabel("Gen Time (s)", fontsize=13)
    ax.set_title("Gen Time — Quantile Fits Overlay", fontsize=14)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/map_quantile_overlay.png", dpi=150, bbox_inches="tight")
    plt.close()

    # ── Fig 4: Pred vs target — best model per quantile ──────────────────────
    ncols = min(len(qkeys), 4)
    nrows = int(np.ceil(len(qkeys) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4.5 * nrows),
                             squeeze=False)
    axes_flat = axes.flatten()

    for i, (q, k) in enumerate(zip(quantiles, qkeys)):
        ax        = axes_flat[i]
        valid     = all_results[k]
        best_name = all_sorted[k][0]
        r         = valid[best_name]
        X_bin     = binned[k]["X"]
        y_bin     = binned[k]["y"]
        counts    = binned[k]["counts"]
        y_pred    = r["func"](X_bin, *r["params"])

        ax.scatter(y_bin, y_pred, s=counts * 2, alpha=0.7, c=colors[k],
                   edgecolors="k", linewidths=0.3)
        lims = [0, max(y_bin.max(), y_pred.max()) * 1.1]
        ax.plot(lims, lims, "k--", lw=1)
        ax.set_xlim(lims); ax.set_ylim(lims)
        ax.set_xlabel("Binned Target (s)", fontsize=9)
        ax.set_ylabel("Predicted (s)", fontsize=9)
        ax.set_title(f"p={q}: {best_name}\nR²={r['r2']:.4f}", fontsize=9)
        ax.tick_params(labelsize=8)

    for j in range(len(qkeys), len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle("Pred vs Binned Target — Gen Time Quantiles\n(dot size ∝ bin count)",
                 fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/map_quantile_predvs.png", dpi=150, bbox_inches="tight")
    plt.close()

    # ── Fig 5: Residuals — best model per quantile ───────────────────────────
    ncols = min(len(qkeys), 4)
    nrows = int(np.ceil(len(qkeys) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows),
                             squeeze=False)
    axes_flat = axes.flatten()

    for i, (q, k) in enumerate(zip(quantiles, qkeys)):
        ax        = axes_flat[i]
        valid     = all_results[k]
        best_name = all_sorted[k][0]
        r         = valid[best_name]
        X_bin     = binned[k]["X"]
        y_bin     = binned[k]["y"]
        y_pred    = r["func"](X_bin, *r["params"])
        resid     = y_bin - y_pred
        bin_ratio = X_bin[0] / np.maximum(X_bin[1], 1.0)

        ax.scatter(bin_ratio, resid, s=30, color=colors[k],
                   edgecolors="k", linewidths=0.3)
        ax.axhline(0, color="black", lw=0.5)
        ax.set_xlabel("n_src / n_bkg", fontsize=9)
        ax.set_ylabel("Residual (s)", fontsize=9)
        ax.set_title(f"p={q}: {best_name}\nR²={r['r2']:.4f}", fontsize=9)
        ax.tick_params(labelsize=8)

    for j in range(len(qkeys), len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle("Residuals — Gen Time Quantile Fits", fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/map_quantile_residuals.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"\nPlots saved to {output_dir}/")
    return all_results, all_sorted


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fit Gen Time to multiple quantile levels",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--csv",             default="emsoft-stats.csv")
    parser.add_argument("--output",          default=".")
    parser.add_argument("--n-bins-per-axis", type=int,   default=20)
    parser.add_argument("--quantiles",       type=float, nargs="+",
                        default=[0.90, 0.95, 0.99],
                        help="One or more quantile levels, e.g. --quantiles 0.90 0.95 0.99")
    parser.add_argument("--min-bin-count",   type=int,   default=25)
    args = parser.parse_args()

    df_det = pd.read_csv(args.csv)

    if len(df_det) == 0:
        print("No data.")
        raise SystemExit(1)

    fit_quantiles(
        df_det,
        output_dir=args.output,
        n_bins_per_axis=args.n_bins_per_axis,
        quantiles=args.quantiles,
        min_bin_count=args.min_bin_count,
    )