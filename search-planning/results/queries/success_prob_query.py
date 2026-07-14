"""
Per-bin empirical + KDE-smoothed success CDF for detection cost.
--------
1. Load CSV, filter detected rows
2. Build per-bin KDE CDFs once
3. Query at runtime:  success_prob_query(deadline, n_src, n_bkg)
"""

"""
Usage
-----
1. Build empirical + KDE CDFs for all bin once
    engine = QueryEngine("some_result.csv") 

2. Query as needed after 
    prob   = engine.query(deadline=20, n_src=200, n_bkg=900)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.interpolate import interp1d


# Manage Single bin, KDE precomputed at build time
class BinCDF:
    """
    Empirical and KDE-smoothed CDF for one (n_src, n_bkg) bin.

    KDE CDF is fully precomputed as an interp1d on construction,
    so every kde_cdf(tau) call is a single O(log n) lookup.
    """

    def __init__(self, costs, bw_method="scott"):
        self.costs           = np.sort(costs)
        self.n               = len(costs)
        self._kde            = None
        self._kde_cdf_interp = None

        # Empirical CDF (left-continuous step function)
        xs = np.concatenate([[0.0], self.costs])
        ys = np.concatenate([[0.0], np.arange(1, self.n + 1) / self.n])
        self._ecdf = interp1d(xs, ys, kind="previous",
                              bounds_error=False, fill_value=(0.0, 1.0))

        # KDE + precomputed CDF interpolant
        if self.n >= 5:
            try:
                self._kde = gaussian_kde(self.costs, bw_method=bw_method)
                self._build_kde_cdf_interp()
            except Exception:
                self._kde = None

    def _build_kde_cdf_interp(self):
        std = self.costs.std() if self.costs.std() > 0 else 1.0
        lo  = max(0.0, self.costs[0] - 3 * self._kde.factor * std)
        hi  = self.costs[-1] * 1.5 + 1.0
        xs  = np.linspace(lo, hi, 2000)
        pdf = self._kde(xs)

        cdf_vals = np.concatenate([[0.0], np.cumsum(pdf) * (xs[1] - xs[0])])
        cdf_vals /= cdf_vals[-1]
        xs_ext   = np.concatenate([[0.0], xs])

        self._kde_cdf_interp = interp1d(xs_ext, cdf_vals,
                                        bounds_error=False,
                                        fill_value=(0.0, 1.0))

    def ecdf(self, tau):
        """Empirical CDF/U(tau)."""
        return float(self._ecdf(tau))

    def kde_cdf(self, tau):
        """KDE-smoothed CDF/U(tau)."""
        if self._kde_cdf_interp is None:
            return self.ecdf(tau)
        return float(self._kde_cdf_interp(tau))

    def quantile(self, p, smoothed=True):
        """Return tau such that U(tau) = p."""
        if smoothed and self._kde_cdf_interp is not None:
            xs  = np.linspace(0.0, self.costs[-1] * 2.0 + 1.0, 5000)
            cdf = self._kde_cdf_interp(xs)
            idx = np.clip(np.searchsorted(cdf, p), 0, len(xs) - 1)
            return float(xs[idx])
        return float(np.quantile(self.costs, p))

    def plot(self, ax, tau_budget=None, smoothed=True, label=None):
        xs     = np.linspace(0.0, self.costs[-1] * 1.15, 500)
        ys_emp = np.array([self.ecdf(x) for x in xs])
        ax.step(xs, ys_emp, where="post", color="steelblue",
                lw=1.2, alpha=0.7, label="Empirical")

        if smoothed and self._kde_cdf_interp is not None:
            ax.plot(xs, self._kde_cdf_interp(xs),
                    color="tomato", lw=1.5, label="KDE")

        if tau_budget is not None:
            p_emp = self.ecdf(tau_budget)
            ax.axvline(tau_budget, color="k", lw=0.8, ls="--")
            ax.axhline(p_emp,      color="k", lw=0.5, ls=":")
            ax.scatter([tau_budget], [p_emp], color="k", s=25, zorder=5)

        if label:
            ax.set_title(label, fontsize=7)
        ax.set_ylim(-0.02, 1.05)
        ax.tick_params(labelsize=6)



# QueryEngine
class QueryEngine:
    """
    Build once from a CSV, query many times.
        engine = QueryEngine("detection_analysis.csv")
        prob   = engine.query(deadline=20, n_src=200, n_bkg=900)
    """

    def __init__(self, csv_path, n_bins_per_axis=20,
                 min_bin_count=5, bw_method="scott"):
        """
        Load CSV, filter detected maps, build all per-bin KDE CDFs.
        Parameters
        ----------
        csv_path        : path to detection_analysis.csv
        n_bins_per_axis : grid resolution along each axis
        min_bin_count   : bins with fewer samples are skipped
        bw_method       : KDE bandwidth — 'scott', 'silverman', or float
        """
        df     = pd.read_csv(csv_path)
        df_det = df[df["detected"] == True].copy()

        print(f"Loaded {len(df):,} rows,  {len(df_det):,} detected "
              f"({100 * len(df_det) / len(df):.1f}%)")
        print(f"  n_src : [{df_det['n_src'].min():.0f}, {df_det['n_src'].max():.0f}]")
        print(f"  n_bkg : [{df_det['n_bkg'].min():.0f}, {df_det['n_bkg'].max():.0f}]")
        print(f"  cost  : [{df_det['detection_cost'].min():.3f}, "
              f"{df_det['detection_cost'].max():.3f}] s")

        n_src = df_det["n_src"].values.astype(float)
        n_bkg = df_det["n_bkg"].values.astype(float)
        cost  = df_det["detection_cost"].values.astype(float)

        self.src_edges = np.linspace(n_src.min(), n_src.max(), n_bins_per_axis + 1)
        self.bkg_edges = np.linspace(n_bkg.min(), n_bkg.max(), n_bins_per_axis + 1)

        src_idx = np.digitize(n_src, self.src_edges[1:-1])
        bkg_idx = np.digitize(n_bkg, self.bkg_edges[1:-1])

        self._bin_cdfs = {}
        self._bin_meta = {}
        n_sb = len(self.src_edges) - 1
        n_bb = len(self.bkg_edges) - 1

        for si in range(n_sb):
            for bi in range(n_bb):
                mask = (src_idx == si) & (bkg_idx == bi)
                if mask.sum() < min_bin_count:
                    # print(f"Small bin with events: {mask.sum()}")
                    continue
                self._bin_cdfs[(si, bi)] = BinCDF(cost[mask], bw_method=bw_method)
                self._bin_meta[(si, bi)] = dict(
                    src_center=0.5 * (self.src_edges[si] + self.src_edges[si + 1]),
                    bkg_center=0.5 * (self.bkg_edges[bi] + self.bkg_edges[bi + 1]),
                    n=int(mask.sum()),
                )

        # print(f"Built CDFs for {len(self._bin_cdfs)} / {n_sb * n_bb} bins")
        print(f"Built CDFs for {len(self._bin_cdfs)} bins")

    #Internal bin lookup
    def _resolve(self, n_src, n_bkg):
        """Map a query point to (si, bi)."""
        ns = np.clip(n_src, self.src_edges[0], self.src_edges[-1])
        nb = np.clip(n_bkg, self.bkg_edges[0], self.bkg_edges[-1])
        si = int(np.clip(np.digitize(ns, self.src_edges[1:-1]),
                         0, len(self.src_edges) - 2))
        bi = int(np.clip(np.digitize(nb, self.bkg_edges[1:-1]),
                         0, len(self.bkg_edges) - 2))
        return si, bi


    def _get_bin(self, n_src, n_bkg, fallback=None):
        """
        Return (key, BinCDF, meta).

        Parameters
        ----------
        fallback : 'nearest' — use closest populated bin (default)
                'error'   — raise KeyError if exact bin is not populated
                None      — return (None, None, None) if not found
        """
        si, bi = self._resolve(n_src, n_bkg)
        key    = (si, bi)

        if key in self._bin_cdfs:
            return key, self._bin_cdfs[key], self._bin_meta[key]

        # Exact bin not populated
        if fallback == "error":
            src_c = 0.5 * (self.src_edges[si] + self.src_edges[si + 1])
            bkg_c = 0.5 * (self.bkg_edges[bi] + self.bkg_edges[bi + 1])
            raise KeyError(
                f"No populated bin for n_src={n_src}, n_bkg={n_bkg}. "
                f"Mapped to bin ({si},{bi}) centered at "
                f"(src≈{src_c:.0f}, bkg≈{bkg_c:.0f}) which has fewer than "
                f"min_bin_count samples. "
                f"Try reducing min_bin_count or use fallback='nearest'.")

        if fallback == "nearest":
            key = min(self._bin_cdfs,
                    key=lambda k: (k[0] - si) ** 2 + (k[1] - bi) ** 2)
            return key, self._bin_cdfs[key], self._bin_meta[key]

        return None, None, None

    # query interface
    def query(self, deadline, n_src, n_bkg, smoothed=True, fallback=None, verbose=False):
        """
        P(detection_cost <= deadline | n_src, n_bkg).

        Parameters
        ----------
        deadline : float  time budget in seconds
        n_src    : float  source pixel count
        n_bkg    : float  background pixel count
        smoothed : bool   KDE CDF (True) or empirical step (False)
        verbose  : bool   print matched bin info

        Returns
        -------
        prob : float in [0, 1]
        """
        key, cdf, info = self._get_bin(n_src, n_bkg, fallback=fallback)
        if key is None:
            return None
        
        if verbose:
            print(f"  [query] bin {key}  "
                  f"src_center≈{info['src_center']:.0f}  "
                  f"bkg_center≈{info['bkg_center']:.0f}  "
                  f"n={info['n']}")
        return cdf.kde_cdf(deadline) if smoothed else cdf.ecdf(deadline)

    def batch_query(self, queries, smoothed=True, fallback=None):
        """
        Parameters
        ----------
        queries  : array-like (N, 3) columns [deadline, n_src, n_bkg]
                or DataFrame with those column names
        smoothed : bool
        fallback : 'nearest' — use closest populated bin
                'error'   — raise KeyError on first missing bin
                None      — fill prob/bin info with None for missing bins

        Returns
        -------
        DataFrame: deadline, n_src, n_bkg, prob,
                bin_src_center, bin_bkg_center, bin_n, bin_found
        """
        if isinstance(queries, pd.DataFrame):
            rows = queries[["deadline", "n_src", "n_bkg"]].values
        else:
            rows = np.asarray(queries)

        records = []
        for deadline, ns, nb in rows:
            key, cdf, info = self._get_bin(ns, nb, fallback=fallback)

            if key is None:
                records.append(dict(
                    deadline=deadline, n_src=ns, n_bkg=nb,
                    prob=None,
                    bin_src_center=None,
                    bin_bkg_center=None,
                    bin_n=None,
                    bin_found=False,
                ))
                continue

            prob = cdf.kde_cdf(deadline) if smoothed else cdf.ecdf(deadline)
            records.append(dict(
                deadline=deadline, n_src=ns, n_bkg=nb,
                prob=prob,
                bin_src_center=info["src_center"],
                bin_bkg_center=info["bkg_center"],
                bin_n=info["n"],
                bin_found=True,
            ))

        df = pd.DataFrame(records)

        n_missing = (~df["bin_found"]).sum()
        if n_missing > 0:
            print(f"  [batch_query] WARNING: {n_missing}/{len(df)} rows "
                f"had no populated bin (prob=None)")

        return df

    def plot_query(self, deadline, n_src, n_bkg,
                   smoothed=True, output_path=None):
        """Plot the CDF of the matched bin with the query point."""
        key, cdf, info = self._get_bin(n_src, n_bkg)
        prob  = cdf.kde_cdf(deadline) if smoothed else cdf.ecdf(deadline)
        p_emp = cdf.ecdf(deadline)
        p_kde = cdf.kde_cdf(deadline)
        bw_str = (f"KDE bw factor={cdf._kde.factor:.3f}"
                  if cdf._kde is not None else "KDE unavailable")

        fig, ax = plt.subplots(figsize=(8, 5))
        cdf.plot(ax, tau_budget=deadline, smoothed=smoothed)

        ax.annotate(f"empirical: {p_emp:.4f}", xy=(deadline, p_emp),
                    xytext=(deadline * 1.05, p_emp - 0.08),
                    fontsize=8, color="steelblue",
                    arrowprops=dict(arrowstyle="->", color="steelblue", lw=0.8))
        if smoothed and cdf._kde is not None:
            ax.annotate(f"KDE: {p_kde:.4f}", xy=(deadline, p_kde),
                        xytext=(deadline * 1.05, p_kde + 0.05),
                        fontsize=8, color="tomato",
                        arrowprops=dict(arrowstyle="->", color="tomato", lw=0.8))

        ax.set_xlabel("Detection cost (s)", fontsize=11)
        ax.set_ylabel("F(τ)", fontsize=11)
        ax.set_title(
            f"Query: deadline={deadline:.2f}s,  n_src={n_src:.0f},  "
            f"n_bkg={n_bkg:.0f}\n"
            f"Matched bin {key}: src≈{info['src_center']:.0f},  "
            f"bkg≈{info['bkg_center']:.0f},  n={info['n']}\n"
            f"{bw_str}  :  P(cost ≤ deadline) = {prob:.4f}",
            fontsize=9)
        ax.legend(fontsize=9)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()
        else:
            plt.show()

        return prob


if __name__ == "__main__":

    # use examples
    # from detection_cdf_query import QueryEngine
    # tiling="1.34x0.9_tiling"
    tiling="5.36x4.5_tiling"
    result_csv = f"search_result_{tiling}.csv"

    engine = QueryEngine(
        csv_path=result_csv,
        n_bins_per_axis=20,
        min_bin_count=5,
        bw_method="scott",
    )

    # Single query
    deadline, n_src, n_bkg = 20, 200, 500
    prob = engine.query(deadline, n_src, n_bkg)
    if prob is None:
        print(f"\nP(cost <= {deadline:.2f}s | n_src={n_src}, n_bkg={n_bkg}) = N/A "
            f"(no bin found for this query point)")
    else:
        print(f"\nP(cost <= {deadline:.2f}s | n_src={n_src}, n_bkg={n_bkg}) = {prob:.4f}")

    # for diagnose
    engine.plot_query(deadline, n_src, n_bkg, output_path="det_cdf_query.png")
    print("Saved: det_cdf_query.png")


    # Batch query
    print("\nBatch query:")
    queries = pd.DataFrame([
        {"deadline": 2.5, "n_src": 350, "n_bkg":  900},
        {"deadline": 1.0, "n_src": 200, "n_bkg":  5000},
        {"deadline": 3.0, "n_src": 600, "n_bkg": 1200},
        {"deadline": 5.0, "n_src": 400, "n_bkg":  800},
    ])
    print(engine.batch_query(queries).to_string(index=False))

