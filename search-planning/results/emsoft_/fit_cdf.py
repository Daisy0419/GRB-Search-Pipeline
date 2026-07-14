"""
Per-bin empirical (and KDE-smoothed) success CDF for detection cost.

For each bin B of (n_src, n_bkg) we estimate

    F_B(tau) = #{i in B : cost_i <= tau} / #{i in B}

and optionally smooth via kernel density estimation (KDE).

Primary query interface
-----------------------
    prob, key, info = query_success_prob(
        bin_cdfs, bin_meta, src_edges, bkg_edges,
        tau=2.5, n_src=350, n_bkg=900)

    => P(detection_cost <= tau | n_src, n_bkg)

Outputs
-------
- Heatmap of F_B(tau) at a chosen deadline tau
- Grid of per-bin CDF curves (empirical + KDE)
- Heatmap of budget required to achieve a target success probability p
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.interpolate import interp1d


# ═══════════════════════════════════════════════════════════════════════════════
# Core: single-bin CDF
# ═══════════════════════════════════════════════════════════════════════════════

# class BinCDF:
#     def __init__(self, costs, bw_method="scott"):
#         self.costs     = np.sort(costs)
#         self.n         = len(costs)
#         self.bw_method = bw_method
#         self._kde      = None
#         self._kde_cdf_interp = None  # cached interpolant

#         # Empirical CDF
#         xs = np.concatenate([[0.0], self.costs])
#         ys = np.concatenate([[0.0], np.arange(1, self.n + 1) / self.n])
#         self._ecdf = interp1d(xs, ys, kind="previous",
#                               bounds_error=False, fill_value=(0.0, 1.0))

#         # KDE + precomputed CDF interpolant
#         if self.n >= 5:
#             try:
#                 self._kde = gaussian_kde(self.costs, bw_method=bw_method)
#                 self._build_kde_cdf_interp()
#             except Exception:
#                 self._kde = None

#     def _build_kde_cdf_interp(self):
#         """Precompute KDE CDF on a fine grid and store as an interpolant."""
#         lo  = max(0.0, self.costs[0] - 3 * self._kde.factor * self.costs.std())
#         hi  = self.costs[-1] * 1.5 + 1.0   # generous upper bound
#         xs  = np.linspace(lo, hi, 2000)
#         pdf = self._kde(xs)
#         cdf_vals = np.concatenate([[0.0], np.cumsum(pdf) * (xs[1] - xs[0])])
#         cdf_vals /= cdf_vals[-1]
#         xs_ext = np.concatenate([[0.0], xs])
#         self._kde_cdf_interp = interp1d(
#             xs_ext, cdf_vals,
#             bounds_error=False, fill_value=(0.0, 1.0))

#     def kde_cdf(self, tau):
#         """KDE-smoothed CDF — O(1) lookup via cached interpolant."""
#         if self._kde_cdf_interp is None:
#             return self.ecdf(tau)
#         return float(self._kde_cdf_interp(tau))

#     def quantile(self, p, smoothed=False):
#         """Return tau such that F_B(tau) = p."""
#         if smoothed and self._kde_cdf_interp is not None:
#             # Invert the cached interpolant directly
#             hi  = self.costs[-1] * 2.0 + 1.0
#             xs  = np.linspace(0.0, hi, 5000)
#             cdf = self._kde_cdf_interp(xs)
#             idx = np.clip(np.searchsorted(cdf, p), 0, len(xs) - 1)
#             return float(xs[idx])
#         return float(np.quantile(self.costs, p))
    


class BinCDF:
    """Empirical and KDE-smoothed CDF for one (n_src, n_bkg) bin."""

    def __init__(self, costs, bw_method="scott"):
        """
        Parameters
        ----------
        costs     : 1D array of observed costs in this bin
        bw_method : KDE bandwidth selector — 'scott', 'silverman', or a float
        """
        self.costs     = np.sort(costs)
        self.n         = len(costs)
        self.bw_method = bw_method
        self._kde      = None

        # Empirical CDF (left-continuous step function)
        xs = np.concatenate([[0.0], self.costs])
        ys = np.concatenate([[0.0], np.arange(1, self.n + 1) / self.n])
        self._ecdf = interp1d(xs, ys, kind="previous",
                              bounds_error=False, fill_value=(0.0, 1.0))

        # KDE (only if enough points)
        if self.n >= 5:
            try:
                self._kde = gaussian_kde(self.costs, bw_method=bw_method)
            except Exception:
                self._kde = None

    def ecdf(self, tau):
        """Empirical CDF: F_B(tau)."""
        return float(self._ecdf(tau))

    def kde_cdf(self, tau):
        """KDE-smoothed CDF. Falls back to empirical if KDE unavailable."""
        if self._kde is None:
            return self.ecdf(tau)
        lo       = max(0.0, self.costs[0] - 3 * self._kde.factor * self.costs.std())
        hi       = max(float(tau), self.costs[-1] * 1.1)
        xs       = np.linspace(lo, hi, 2000)
        pdf      = self._kde(xs)
        cdf_vals = np.concatenate([[0.0], np.cumsum(pdf) * (xs[1] - xs[0])])
        cdf_vals /= cdf_vals[-1]
        xs_ext   = np.concatenate([[0.0], xs])
        f = interp1d(xs_ext, cdf_vals, bounds_error=False, fill_value=(0.0, 1.0))
        return float(f(tau))

    def quantile(self, p, smoothed=False):
        """Return tau such that F_B(tau) = p."""
        if smoothed and self._kde is not None:
            hi  = self.costs[-1] * 2.0 + 1.0
            xs  = np.linspace(0.0, hi, 5000)
            cdf = np.array([self.kde_cdf(x) for x in xs])
            idx = np.clip(np.searchsorted(cdf, p), 0, len(xs) - 1)
            return float(xs[idx])
        return float(np.quantile(self.costs, p))

    def plot(self, ax, tau_budget=None, smoothed=True, label=None):
        """Plot empirical (and optionally KDE) CDF on ax."""
        xs     = np.linspace(0.0, self.costs[-1] * 1.15, 500)
        ys_emp = np.array([self.ecdf(x) for x in xs])
        ax.step(xs, ys_emp, where="post", color="steelblue",
                lw=1.2, alpha=0.7, label="Empirical")

        if smoothed and self._kde is not None:
            ys_kde = np.array([self.kde_cdf(x) for x in xs])
            ax.plot(xs, ys_kde, color="tomato", lw=1.5, label="KDE")

        if tau_budget is not None:
            p_emp = self.ecdf(tau_budget)
            ax.axvline(tau_budget, color="k", lw=0.8, ls="--")
            ax.axhline(p_emp,      color="k", lw=0.5, ls=":")
            ax.scatter([tau_budget], [p_emp], color="k", s=25, zorder=5)

        if label:
            ax.set_title(label, fontsize=7)
        ax.set_ylim(-0.02, 1.05)
        ax.tick_params(labelsize=6)


# ═══════════════════════════════════════════════════════════════════════════════
# Build all per-bin CDFs
# ═══════════════════════════════════════════════════════════════════════════════

def build_bin_cdfs(n_src, n_bkg, cost, n_bins_per_axis,
                   min_bin_count=10, bw_method="scott"):
    """
    Bin (n_src, n_bkg) on a 2D equal-width grid and build a BinCDF per cell.

    Returns
    -------
    bin_cdfs  : dict[(si, bi)] -> BinCDF
    src_edges : 1D array, shape (n_bins_per_axis+1,)
    bkg_edges : 1D array, shape (n_bins_per_axis+1,)
    bin_meta  : dict[(si, bi)] -> {src_center, bkg_center, n}
    """
    src_edges = np.linspace(n_src.min(), n_src.max(), n_bins_per_axis + 1)
    bkg_edges = np.linspace(n_bkg.min(), n_bkg.max(), n_bins_per_axis + 1)

    src_idx = np.digitize(n_src, src_edges[1:-1])
    bkg_idx = np.digitize(n_bkg, bkg_edges[1:-1])

    bin_cdfs = {}
    bin_meta = {}

    for si in range(len(src_edges) - 1):
        for bi in range(len(bkg_edges) - 1):
            mask = (src_idx == si) & (bkg_idx == bi)
            if mask.sum() < min_bin_count:
                continue
            c = cost[mask]
            bin_cdfs[(si, bi)] = BinCDF(c, bw_method=bw_method)
            bin_meta[(si, bi)] = dict(
                src_center=0.5 * (src_edges[si] + src_edges[si + 1]),
                bkg_center=0.5 * (bkg_edges[bi] + bkg_edges[bi + 1]),
                n=int(mask.sum()),
            )

    return bin_cdfs, src_edges, bkg_edges, bin_meta


# ═══════════════════════════════════════════════════════════════════════════════
# Query interface
# ═══════════════════════════════════════════════════════════════════════════════

def _resolve_bin(n_src, n_bkg, src_edges, bkg_edges):
    """Return (si, bi) for a query point, clipped to grid extent."""
    n_src_c = np.clip(n_src, src_edges[0], src_edges[-1])
    n_bkg_c = np.clip(n_bkg, bkg_edges[0], bkg_edges[-1])
    si = int(np.clip(np.digitize(n_src_c, src_edges[1:-1]),
                     0, len(src_edges) - 2))
    bi = int(np.clip(np.digitize(n_bkg_c, bkg_edges[1:-1]),
                     0, len(bkg_edges) - 2))
    return si, bi


def query_success_prob(bin_cdfs, bin_meta, src_edges, bkg_edges,
                       tau, n_src, n_bkg,
                       smoothed=True, fallback="nearest", verbose=False):
    """
    Return P(detection_cost <= tau | n_src, n_bkg).

    Parameters
    ----------
    tau      : float — time budget / deadline
    n_src    : float — query source pixel count
    n_bkg    : float — query background pixel count
    smoothed : bool  — use KDE CDF (True) or empirical step function (False)
    fallback : 'nearest' — if the exact bin was filtered out (too few samples),
               use the nearest populated bin by bin-index Euclidean distance.
               Pass None to return (None, None, None) instead.
    verbose  : bool  — print matched bin and any fallback warning

    Returns
    -------
    prob     : float in [0, 1], or None if no bin available
    bin_key  : (si, bi) tuple of the matched bin
    bin_info : dict with keys src_center, bkg_center, n
    """
    si, bi  = _resolve_bin(n_src, n_bkg, src_edges, bkg_edges)
    key     = (si, bi)
    exact   = key in bin_cdfs
    used_fb = False

    if not exact:
        if fallback == "nearest" and bin_cdfs:
            key     = min(bin_cdfs.keys(),
                          key=lambda k: (k[0] - si) ** 2 + (k[1] - bi) ** 2)
            used_fb = True
        else:
            return None, None, None

    if verbose:
        info = bin_meta[key]
        if used_fb:
            print(f"  [query] WARNING: exact bin ({si},{bi}) filtered "
                  f"(too few samples) — nearest bin {key} used "
                  f"(src≈{info['src_center']:.0f}, "
                  f"bkg≈{info['bkg_center']:.0f}, n={info['n']})")
        else:
            print(f"  [query] bin {key}  "
                  f"src≈{info['src_center']:.0f}  "
                  f"bkg≈{info['bkg_center']:.0f}  "
                  f"n={info['n']}")

    cdf  = bin_cdfs[key]
    prob = cdf.kde_cdf(tau) if smoothed else cdf.ecdf(tau)
    return prob, key, bin_meta[key]


def batch_query(bin_cdfs, bin_meta, src_edges, bkg_edges,
                queries, smoothed=True, fallback="nearest"):
    """
    Query P(cost <= tau | n_src, n_bkg) for multiple (tau, n_src, n_bkg) rows.

    Parameters
    ----------
    queries : array-like of shape (N, 3) with columns [tau, n_src, n_bkg],
              or a DataFrame with those column names.

    Returns
    -------
    DataFrame with columns:
        tau, n_src, n_bkg, prob,
        bin_si, bin_bi, bin_src_center, bin_bkg_center, bin_n, fallback_used
    """
    if isinstance(queries, pd.DataFrame):
        rows = queries[["tau", "n_src", "n_bkg"]].values
    else:
        rows = np.asarray(queries)

    records = []
    for tau, ns, nb in rows:
        prob, key, info = query_success_prob(
            bin_cdfs, bin_meta, src_edges, bkg_edges,
            tau=tau, n_src=ns, n_bkg=nb,
            smoothed=smoothed, fallback=fallback)

        exact_si, exact_bi = _resolve_bin(ns, nb, src_edges, bkg_edges)
        fb = (key != (exact_si, exact_bi)) if key is not None else True

        records.append(dict(
            tau=tau, n_src=ns, n_bkg=nb,
            prob=prob,
            bin_si=key[0]              if key  else None,
            bin_bi=key[1]              if key  else None,
            bin_src_center=info["src_center"] if info else None,
            bin_bkg_center=info["bkg_center"] if info else None,
            bin_n=info["n"]            if info else None,
            fallback_used=fb,
        ))

    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════════════════
# Plotting utilities
# ═══════════════════════════════════════════════════════════════════════════════

def plot_cdf_heatmap(bin_cdfs, bin_meta, src_edges, bkg_edges,
                     tau_budget, smoothed=True,
                     title=None, output_path=None):
    """Heatmap of F_B(tau_budget) — success probability per bin."""
    n_src_bins = len(src_edges) - 1
    n_bkg_bins = len(bkg_edges) - 1

    grid = np.full((n_bkg_bins, n_src_bins), np.nan)
    for (si, bi), cdf in bin_cdfs.items():
        grid[bi, si] = cdf.kde_cdf(tau_budget) if smoothed else cdf.ecdf(tau_budget)

    masked = np.ma.masked_where(np.isnan(grid), grid)

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.pcolormesh(src_edges, bkg_edges, masked,
                       cmap="RdYlGn", vmin=0, vmax=1, shading="auto")
    plt.colorbar(im, ax=ax, label=f"P(cost ≤ {tau_budget:.2f} s)")

    for (si, bi), meta in bin_meta.items():
        val = bin_cdfs[(si, bi)].kde_cdf(tau_budget) if smoothed \
              else bin_cdfs[(si, bi)].ecdf(tau_budget)
        ax.text(meta["src_center"], meta["bkg_center"],
                f"{val:.2f}\nn={meta['n']}",
                ha="center", va="center", fontsize=5.5, color="black")

    ax.set_xlabel("n_src")
    ax.set_ylabel("n_bkg")
    ax.set_title(title or
                 f"P(detection cost ≤ {tau_budget:.2f} s) per bin"
                 f"  ({'KDE' if smoothed else 'empirical'})")
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_cdf_grid(bin_cdfs, bin_meta, src_edges, bkg_edges,
                  tau_budget=None, smoothed=True,
                  max_panels=40, output_path=None):
    """Spatially-arranged grid of per-bin CDF curves."""
    n_src_bins = len(src_edges) - 1
    n_bkg_bins = len(bkg_edges) - 1

    stride  = max(1, int(np.ceil(np.sqrt(n_src_bins * n_bkg_bins / max_panels))))
    si_vals = list(range(0, n_src_bins, stride))
    bi_vals = list(range(0, n_bkg_bins, stride))

    nrows, ncols = len(bi_vals), len(si_vals)
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(2.2 * ncols, 2.0 * nrows),
                             squeeze=False)

    for row, bi in enumerate(bi_vals[::-1]):
        for col, si in enumerate(si_vals):
            ax = axes[row][col]
            if (si, bi) in bin_cdfs:
                meta  = bin_meta[(si, bi)]
                label = (f"src≈{meta['src_center']:.0f}\n"
                         f"bkg≈{meta['bkg_center']:.0f}  n={meta['n']}")
                bin_cdfs[(si, bi)].plot(ax, tau_budget=tau_budget,
                                        smoothed=smoothed, label=label)
            else:
                ax.set_visible(False)

    for ax in axes[-1]:
        ax.set_xlabel("cost (s)", fontsize=6)
    for row_axes in axes:
        row_axes[0].set_ylabel("F(τ)", fontsize=6)

    fig.suptitle(
        "Per-bin empirical CDFs" +
        (f"  [deadline τ={tau_budget:.2f}s marked]" if tau_budget else ""),
        fontsize=11, y=1.01)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_quantile_heatmap(bin_cdfs, bin_meta, src_edges, bkg_edges,
                          p=0.95, smoothed=True, output_path=None):
    """Heatmap of tau needed to achieve success probability p per bin."""
    n_src_bins = len(src_edges) - 1
    n_bkg_bins = len(bkg_edges) - 1

    grid = np.full((n_bkg_bins, n_src_bins), np.nan)
    for (si, bi), cdf in bin_cdfs.items():
        grid[bi, si] = cdf.quantile(p, smoothed=smoothed)

    masked = np.ma.masked_where(np.isnan(grid), grid)

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.pcolormesh(src_edges, bkg_edges, masked,
                       cmap="viridis_r", shading="auto")
    plt.colorbar(im, ax=ax, label=f"τ needed for P(cost≤τ) = {p}")

    for (si, bi), meta in bin_meta.items():
        q = bin_cdfs[(si, bi)].quantile(p, smoothed=smoothed)
        ax.text(meta["src_center"], meta["bkg_center"],
                f"{q:.1f}s",
                ha="center", va="center", fontsize=5.5, color="white")

    ax.set_xlabel("n_src")
    ax.set_ylabel("n_bkg")
    ax.set_title(f"Budget required for p={p} success probability per bin"
                 f"  ({'KDE' if smoothed else 'empirical'})")
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_query_on_cdf(bin_cdfs, bin_meta, src_edges, bkg_edges,
                      tau, n_src, n_bkg, smoothed=True, output_path=None):
    """
    Plot the CDF of the matched bin with the query (tau, prob) highlighted.
    Useful for inspecting a single prediction.
    """
    prob, key, info = query_success_prob(
        bin_cdfs, bin_meta, src_edges, bkg_edges,
        tau=tau, n_src=n_src, n_bkg=n_bkg,
        smoothed=smoothed, verbose=True)

    if prob is None:
        print("No bin found for this query.")
        return None

    fig, ax = plt.subplots(figsize=(7, 4))
    bin_cdfs[key].plot(ax, tau_budget=tau, smoothed=smoothed)

    ax.set_xlabel("Detection cost (s)", fontsize=11)
    ax.set_ylabel("F(τ)", fontsize=11)
    ax.set_title(
        f"Query: τ={tau:.2f}s,  n_src={n_src:.0f},  n_bkg={n_bkg:.0f}\n"
        f"Matched bin {key}: src≈{info['src_center']:.0f}, "
        f"bkg≈{info['bkg_center']:.0f},  n={info['n']}\n"
        f"P(cost ≤ τ) = {prob:.4f}",
        fontsize=10)
    ax.legend(fontsize=9)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()

    return prob


def build_bin_value_grid(n_src, n_bkg, values, src_edges, bkg_edges,
                          aggfunc=np.mean):
    """
    Aggregate a per-row scalar (e.g. sum_tiles) into the same 2D bin grid.

    Parameters
    ----------
    values   : 1D array aligned with n_src / n_bkg
    aggfunc  : e.g. np.mean, np.median, np.std

    Returns
    -------
    grid     : 2D array (n_bkg_bins, n_src_bins), NaN where no data
    counts   : 2D int array of sample counts per bin
    """
    n_src_bins = len(src_edges) - 1
    n_bkg_bins = len(bkg_edges) - 1

    src_idx = np.clip(np.digitize(n_src, src_edges[1:-1]), 0, n_src_bins - 1)
    bkg_idx = np.clip(np.digitize(n_bkg, bkg_edges[1:-1]), 0, n_bkg_bins - 1)

    grid   = np.full((n_bkg_bins, n_src_bins), np.nan)
    counts = np.zeros((n_bkg_bins, n_src_bins), dtype=int)

    for si in range(n_src_bins):
        for bi in range(n_bkg_bins):
            mask = (src_idx == si) & (bkg_idx == bi)
            if mask.sum() == 0:
                continue
            grid[bi, si]   = aggfunc(values[mask])
            counts[bi, si] = mask.sum()

    return grid, counts


def plot_value_heatmap(n_src, n_bkg, values, src_edges, bkg_edges,
                       aggfunc=np.mean, aggname="mean",
                       col_label="sum_tiles", cmap="plasma",
                       output_path=None):
    """
    Heatmap of aggfunc(values) per (n_src, n_bkg) bin.

    Parameters
    ----------
    values   : 1D array of the column to aggregate (e.g. df["sum_tiles"].values)
    aggfunc  : np.mean, np.median, np.std, np.max, etc.
    aggname  : string label for the aggregation, used in title/colorbar
    col_label: column name for axis labels
    """
    grid, counts = build_bin_value_grid(
        n_src, n_bkg, values, src_edges, bkg_edges, aggfunc=aggfunc)

    masked = np.ma.masked_where(np.isnan(grid), grid)

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.pcolormesh(src_edges, bkg_edges, masked, cmap=cmap, shading="auto")
    plt.colorbar(im, ax=ax, label=f"{aggname}({col_label})")

    src_centers = 0.5 * (src_edges[:-1] + src_edges[1:])
    bkg_centers = 0.5 * (bkg_edges[:-1] + bkg_edges[1:])

    for bi in range(len(bkg_centers)):
        for si in range(len(src_centers)):
            v = grid[bi, si]
            n = counts[bi, si]
            if np.isnan(v) or n == 0:
                continue
            ax.text(src_centers[si], bkg_centers[bi],
                    f"{v:.1f}\nn={n}",
                    ha="center", va="center", fontsize=5.5, color="white")

    ax.set_xlabel("n_src")
    ax.set_ylabel("n_bkg")
    ax.set_title(f"{aggname}({col_label}) per (n_src, n_bkg) bin")
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()

# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

def run_bin_cdfs(df_det, output_dir=".", n_bins_per_axis=20,
                 min_bin_count=10, bw_method="scott",
                 tau_budget=None, quantile_p=0.95):
    """
    Build per-bin CDFs and save all diagnostic plots.

    Parameters
    ----------
    df_det         : DataFrame with columns n_src, n_bkg, detection_cost
    tau_budget     : deadline for success-probability heatmap;
                     defaults to 90th percentile of all costs
    quantile_p     : probability level for budget-required heatmap

    Returns
    -------
    bin_cdfs, bin_meta, src_edges, bkg_edges
    """
    n_src = df_det["n_src"].values.astype(float)
    n_bkg = df_det["n_bkg"].values.astype(float)
    cost  = df_det["detection_cost"].values.astype(float)

    if tau_budget is None:
        tau_budget = float(np.percentile(cost, 90))

    print(f"Building per-bin CDFs on {len(cost)} points")
    print(f"  n_src:         [{n_src.min():.0f}, {n_src.max():.0f}]")
    print(f"  n_bkg:         [{n_bkg.min():.0f}, {n_bkg.max():.0f}]")
    print(f"  cost:          [{cost.min():.2f}, {cost.max():.2f}]")
    print(f"  tau_budget:    {tau_budget:.2f}")
    print(f"  quantile_p:    {quantile_p}")
    print(f"  min_bin_count: {min_bin_count}")
    print(f"  bw_method:     {bw_method}")

    bin_cdfs, src_edges, bkg_edges, bin_meta = build_bin_cdfs(
        n_src, n_bkg, cost, n_bins_per_axis,
        min_bin_count=min_bin_count, bw_method=bw_method)

    print(f"  Populated bins: {len(bin_cdfs)}")

    plot_cdf_heatmap(
        bin_cdfs, bin_meta, src_edges, bkg_edges,
        tau_budget=tau_budget, smoothed=True,
        output_path=f"{output_dir}/det_cdf_success_prob_heatmap.png")
    print("  Saved: det_cdf_success_prob_heatmap.png")

    plot_cdf_grid(
        bin_cdfs, bin_meta, src_edges, bkg_edges,
        tau_budget=tau_budget, smoothed=True,
        output_path=f"{output_dir}/det_cdf_curves_grid.png")
    print("  Saved: det_cdf_curves_grid.png")

    # Fig 4: mean sum_tiles per bin
    sum_tiles = df_det["sum_tiles"].values.astype(float)

    plot_value_heatmap(
        n_src, n_bkg, sum_tiles, src_edges, bkg_edges,
        aggfunc=np.mean, aggname="mean", col_label="sum_tiles",
        output_path=f"{output_dir}/det_sum_tiles_mean_heatmap.png")

    plot_value_heatmap(
        n_src, n_bkg, sum_tiles, src_edges, bkg_edges,
        aggfunc=np.median, aggname="median", col_label="sum_tiles",
        output_path=f"{output_dir}/det_sum_tiles_median_heatmap.png")

    # plot_quantile_heatmap(
    #     bin_cdfs, bin_meta, src_edges, bkg_edges,
    #     p=quantile_p, smoothed=True,
    #     output_path=f"{output_dir}/det_cdf_budget_required_heatmap.png")
    # print("  Saved: det_cdf_budget_required_heatmap.png")

    return bin_cdfs, bin_meta, src_edges, bkg_edges



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Per-bin empirical CDF of detection cost",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--csv",             default="5.36x4.5_tiling.csv")
    parser.add_argument("--output",          default=".")
    parser.add_argument("--n-bins-per-axis", type=int,   default=20)
    parser.add_argument("--min-bin-count",   type=int,   default=25)
    parser.add_argument("--bw-method",       default="scott",
                        help="KDE bandwidth: 'scott', 'silverman', or a float")
    parser.add_argument("--tau-budget",      type=float, default=None,
                        help="Deadline for success-prob heatmap "
                             "(default: 90th percentile of costs)")
    parser.add_argument("--quantile-p",      type=float, default=0.95)
    # Single-query mode
    parser.add_argument("--query-tau",       type=float, default=None,
                        help="Query a single deadline after building CDFs")
    parser.add_argument("--query-n-src",     type=float, default=None)
    parser.add_argument("--query-n-bkg",     type=float, default=None)
    args = parser.parse_args()

    df     = pd.read_csv(args.csv)
    df_det = df[df["detected"] == True].copy()
    print(f"Loaded {len(df)} rows, {len(df_det)} detected\n")

    if len(df_det) == 0:
        print("No detections.")
        raise SystemExit(1)

    bin_cdfs, bin_meta, src_edges, bkg_edges = run_bin_cdfs(
        df_det,
        output_dir=args.output,
        n_bins_per_axis=args.n_bins_per_axis,
        min_bin_count=args.min_bin_count,
        bw_method=args.bw_method,
        tau_budget=args.tau_budget,
        quantile_p=args.quantile_p,
    )

    # Optional single-query from CLI
    if args.query_tau is not None:
        if args.query_n_src is None or args.query_n_bkg is None:
            print("ERROR: --query-tau requires --query-n-src and --query-n-bkg")
            raise SystemExit(1)

        prob, key, info = query_success_prob(
            bin_cdfs, bin_meta, src_edges, bkg_edges,
            tau=args.query_tau,
            n_src=args.query_n_src,
            n_bkg=args.query_n_bkg,
            smoothed=True,
            verbose=True,
        )
        print(f"\nQuery result:")
        print(f"  P(cost <= {args.query_tau:.2f}s | "
              f"n_src={args.query_n_src:.0f}, n_bkg={args.query_n_bkg:.0f})"
              f" = {prob:.4f}")
        print(f"  Matched bin {key}: "
              f"src≈{info['src_center']:.0f}, "
              f"bkg≈{info['bkg_center']:.0f}, "
              f"n={info['n']}")

        plot_query_on_cdf(
            bin_cdfs, bin_meta, src_edges, bkg_edges,
            tau=args.query_tau,
            n_src=args.query_n_src,
            n_bkg=args.query_n_bkg,
            smoothed=True,
            output_path=f"{args.output}/det_cdf_query.png",
        )
        print("  Saved: det_cdf_query.png")