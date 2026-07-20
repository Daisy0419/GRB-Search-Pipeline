import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


df = pd.read_csv("GCP_result/runtime_1.34x0.9_tiling.csv")

heuristic = "gcp"


df["budget"] = pd.to_numeric(df["budget"], errors="coerce")
df["num_tiles"] = pd.to_numeric(df["num_tiles"], errors="coerce")
df["elapsed_ms"] = pd.to_numeric(df["elapsed_ms"], errors="coerce")

# 1) Histogram of num_tiles 
ds_tiles = (
    df[["dataset", "num_tiles"]]
    .dropna()
    .drop_duplicates(subset=["dataset"]) 
)

plt.figure()
plt.hist(ds_tiles["num_tiles"], bins="auto")
# plt.hist(ds_tiles["num_tiles"], bins=10)
plt.xlabel("num_tiles (unique per dataset)")
plt.ylabel("Number of datasets")
plt.title("Histogram of num_tiles (each dataset counted once)")
plt.tight_layout()
plt.show()


# 2) Distribution of num_tiles 
vals = ds_tiles["num_tiles"].dropna().values
mean_val = np.mean(vals)

plt.figure()
plt.violinplot(vals, showmeans=False, showmedians=True, showextrema=True)
plt.boxplot(vals, vert=True, widths=0.15, showfliers=True)

plt.scatter([1], [mean_val], marker="D", s=60, label=f"Mean = {mean_val:.2f}")

plt.ylabel("num_tiles (unique per dataset)")
plt.title("num_tiles distribution (violin + box overlay)")
plt.legend()
plt.tight_layout()
plt.show()



# 3) Stage runtimes
# heuristic = "Annealing"
labels_order = ["init", "mapping", heuristic, "total"] 
df2 = df[df["label"].isin(labels_order)].dropna(subset=["dataset", "budget", "num_tiles", "elapsed_ms"]).copy()

# (A) Pivot so each (dataset, budget, num_tiles) becomes one row with columns for each stage
wide = (
    df2.pivot_table(
        index=["dataset", "budget", "num_tiles"],
        columns="label",
        values="elapsed_ms",
        aggfunc="mean",  
    )
    .reset_index()
)

# If any stage missing, drop those rows
required = ["init", "mapping", heuristic, "total"]
wide = wide.dropna(subset=required)

# (B)end-to-end total
wide["end2end"] = wide["init"] + wide["mapping"] + wide[heuristic] + wide["total"]

# (C) Convert back to long format for easy plotting
long = wide.melt(
    id_vars=["dataset", "budget", "num_tiles"],
    value_vars=["init", "mapping", heuristic, "total", "end2end"],
    var_name="stage",
    value_name="ms",
)

# (D) Aggregate across datasets for the same (num_tiles, budget, stage)
# Use mean
agg = (
    long.groupby(["num_tiles", "budget", "stage"], as_index=False)["ms"]
        .mean()
)

# runtime vs num_tiles, one curve per budget (for each stage)
stages_to_plot = ["mapping", heuristic, "end2end"]

for stage in stages_to_plot:
    sub = agg[agg["stage"] == stage].copy()
    if sub.empty:
        continue

    plt.figure()
    for b, g in sub.groupby("budget"):
        g = g.sort_values("num_tiles")
        plt.plot(g["num_tiles"], g["ms"], marker="o", label=f"budget={b:g}")

    plt.xlabel("num_tiles")
    plt.ylabel("time (ms)")
    title_name = "end2end" if stage == "end2end_ms" else stage
    plt.title(f"{title_name} time vs num_tiles (grouped by budget)")
    plt.legend()
    plt.tight_layout()
    plt.show()



def model_n2(n, e, f):
    n = np.asarray(n, dtype=float)
    return e * (n**2) + f

def model_n3(n, c, d):
    n = np.asarray(n, dtype=float)
    return c * (n**3) + d

def model_n3logn(n, a, b):
    n = np.asarray(n, dtype=float)
    return a * (n**3) * np.log(n) + b

def r2_score(y, yhat):
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan



stages_to_fit = ["mapping", heuristic, "end2end"] 

for stage in stages_to_fit:
    sub = long[long["stage"] == stage].dropna(subset=["num_tiles", "ms"]).copy()
    if sub.empty:
        print(f"[skip] stage '{stage}' not found. Available:", sorted(long["stage"].unique()))
        continue

    x = sub["num_tiles"].to_numpy(dtype=float)
    y = sub["ms"].to_numpy(dtype=float)

    #n>1 for log(n)
    mask = x > 1
    x, y = x[mask], y[mask]

    order = np.argsort(x)
    x, y = x[order], y[order]

    eps = 1e-12
    guess_e = np.median(y / (x**2 + eps))
    guess_c = np.median(y / (x**3 + eps))
    guess_a = np.median(y / ((x**3) * np.log(x) + eps))
    guess_f = np.median(y)
    guess_d = np.median(y)
    guess_b = np.median(y)

    # Fit n^2
    popt_2, _ = curve_fit(model_n2, x, y, p0=[guess_e, guess_f], maxfev=20000)
    yhat_2 = model_n2(x, *popt_2)
    r2_2 = r2_score(y, yhat_2)

    # Fit n^3
    popt_3, _ = curve_fit(model_n3, x, y, p0=[guess_c, guess_d], maxfev=20000)
    yhat_3 = model_n3(x, *popt_3)
    r2_3 = r2_score(y, yhat_3)

    # Fit n^3 log n
    popt_3l, _ = curve_fit(model_n3logn, x, y, p0=[guess_a, guess_b], maxfev=20000)
    yhat_3l = model_n3logn(x, *popt_3l)
    r2_3l = r2_score(y, yhat_3l)

    e, f = popt_2
    c, d = popt_3
    a, b = popt_3l

    print(f"\n=== Stage: {stage} ===")
    print(f"Fit (n^2):          t(n) = {e:.6g} * n^2 + {f:.6g}            [R^2={r2_2:.4f}]")
    print(f"Fit (n^3):          t(n) = {c:.6g} * n^3 + {d:.6g}            [R^2={r2_3:.4f}]")
    print(f"Fit (n^3 log n):    t(n) = {a:.6g} * n^3 * log(n) + {b:.6g}   [R^2={r2_3l:.4f}]")

    plt.figure()
    plt.scatter(x, y, s=18, alpha=0.7, label="data")

    xg = np.linspace(x.min(), x.max(), 300)
    plt.plot(xg, model_n2(xg, *popt_2), label="fit: n^2")
    plt.plot(xg, model_n3(xg, *popt_3), label="fit: n^3")
    plt.plot(xg, model_n3logn(xg, *popt_3l), label="fit: n^3 log n")

    plt.xlabel("num_tiles (n)")
    plt.ylabel("time (ms)")
    plt.title(f"{stage}: scatter + fitted curves")
    plt.legend()
    plt.tight_layout()
    plt.show()