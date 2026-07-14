import numpy as np
from scipy.stats import poisson
 
 
def _poisson_weights(e, lambda_b, t_m):
    """
    Truncated Poisson weights Pr(b | e, lambda_b, t_m) for b = 0..e.
    Returns
    -------
    weights : 1D array of length e+1, sums to 1.0
    """
    bs       = np.arange(e + 1, dtype=float)
    log_pmf  = poisson.logpmf(bs, mu=lambda_b * t_m)
 
    log_pmf -= log_pmf.max()                           
    weights  = np.exp(log_pmf)
    weights /= weights.sum()                   
    return weights
 
 
def compute_U(t_m, s, b, D, q,
              detection_engine, map_engine,
              smoothed=True):
    """
    Single-term utility:
        U(t_m | s, b, D) = q * P(detection_cost <= D - t_m - map_time(s,b,q) | s, b)
 
    Returns
    -------
    u : float in [0, 1]  (0 if deadline already exceeded)
    """
    if s <= 0:
        return 0.0
    if D - t_m <= 0.0: 
        return 0.0

    map_time    = map_engine.query(n_src=s, n_bkg=b, quantile=q)
    deadline_dt = D - t_m - map_time 
 
    if deadline_dt <= 0.0:
        return 0.0
 
    prob = detection_engine.query(
        deadline=deadline_dt,
        n_src=s,
        n_bkg=b,
        smoothed=smoothed,
    )
    return q * prob
 
 
def expected_U(e, D, lambda_b, t_m, q,
               detection_engine, map_engine,
               smoothed=True,
               min_weight=1e-9,
               verbose=False):
    """ 
        U_bar(t_m | e, D, lambda_b)
            = sum_{b=0}^{e} U(t_m | e-b, b, D) * Pr(b | e, lambda_b, t_m)
 
    Returns
    -------
    u_bar : float  expected utility in [0, q]
    """

    if D - t_m <= 0.0:
        if verbose:
            print(f"  D - t_m = {D - t_m:.3f} <= 0 → E[U] = 0.0")
        return 0.0
    
    weights = _poisson_weights(e, lambda_b, t_m)
 
    u_bar = 0.0
    if verbose:
        print(f"e={e}, D={D:.2f}, lambda_b={lambda_b}, t_m={t_m:.2f}, q={q}")
        print(f"{'b':>4s}  {'s':>4s}  {'weight':>8s}  {'map_t':>7s}  "
              f"{'d_left':>7s}  {'prob':>7s}  {'U':>7s}")
 
    for b, w in enumerate(weights):
        if w < min_weight:
            continue
 
        s = e - b
 
        u = compute_U(t_m, s, b, D, q,
                      detection_engine, map_engine,
                      smoothed=smoothed)
 
        u_bar += w * u
 
        if verbose:
            map_t   = map_engine.query(n_src=max(s, 0), n_bkg=b, quantile=q)
            d_left  = D - t_m - map_t
            prob    = detection_engine.query(d_left, max(s, 0), b, smoothed=smoothed) \
                      if d_left > 0 else 0.0
            print(f"  {b:>4d}  {s:>4d}  {w:>8.4f}  {map_t:>7.3f}  "
                  f"{d_left:>7.3f}  {prob:>7.4f}  {u:>7.4f}")
 
    if verbose:
        print(f"E[U] = {u_bar:.4f}")
 
    return u_bar
 

def expected_U_fast(e, D, lambda_b, t_m, q,
                    detection_engine, map_engine,
                    smoothed=True, min_weight=1e-9, verbose=False):

    if D - t_m <= 0.0:
        return 0.0

    weights = _poisson_weights(e, lambda_b, t_m)

    u_bar = 0.0
    b     = 0

    while b <= e:
        w = weights[b]
        if w < min_weight:
            b += 1
            continue

        s = max(e - b, 0)

        prob_dummy, src_bounds, bkg_bounds = \
            detection_engine.query_with_boundaries(0.0, s, b, smoothed=smoothed)

        map_t, map_src_bounds, map_bkg_bounds = \
            map_engine.query_with_boundaries(s, b, quantile=q)

        # b_end: furthest b still in the same bin pair
        b_max_det_src = int(np.floor(e - src_bounds[0])) if src_bounds[0] > 0 else e
        b_max_det_bkg = e if np.isinf(bkg_bounds[1]) else int(np.ceil(bkg_bounds[1])) - 1
        b_max_map_src = int(np.floor(e - map_src_bounds[0])) if map_src_bounds[0] > 0 else e
        b_max_map_bkg = e if np.isinf(map_bkg_bounds[1]) else int(np.ceil(map_bkg_bounds[1])) - 1
        # b_max_det_src = int(np.floor(e - src_bounds[0]))
        # b_max_det_bkg = int(np.ceil(bkg_bounds[1])) - 1
        # b_max_map_src = int(np.floor(e - map_src_bounds[0]))
        # b_max_map_bkg = int(np.ceil(map_bkg_bounds[1])) - 1
        b_end = max(min(b_max_det_src, b_max_det_bkg,
                        b_max_map_src, b_max_map_bkg, e), b)

        deadline_dt = D - t_m - map_t
        if deadline_dt > 0.0:
            prob = detection_engine.query(deadline_dt, s, b, smoothed=smoothed)
            u    = q * prob
        else:
            u = 0.0

        u_bar += float(weights[b : b_end + 1].sum()) * u
        b      = b_end + 1

    if verbose:
        print(f"E[U] = {u_bar:.4f}")

    return u_bar
    



if __name__ == "__main__":
    from success_prob_query import QueryEngine
    from mapping_time_query import MapTimeQueryEngine
    import time

    # Build engines
    t0 = time.perf_counter()
    detection_engine = QueryEngine(
        csv_path="search_result_1.34x0.9_tiling.csv",
        n_bins_per_axis=50,
        min_bin_count=10,
        bw_method="scott",
    )
    print(f"detection_engine built in {time.perf_counter() - t0:.3f}s")

    t0 = time.perf_counter()
    map_engine = MapTimeQueryEngine(
        csv_path="emsoft.csv",
        quantiles=[0.90, 0.95, 0.99],
        n_bins_per_axis=50,
        min_bin_count=10,
    )
    print(f"map_engine built in {time.perf_counter() - t0:.3f}s")

    #Parameters
    e        = 1500
    D        = 500.0
    lambda_b = 10
    t_m      = 50.0
    q        = 0.99

    #Poisson weights
    t0 = time.perf_counter()
    weights = _poisson_weights(e, lambda_b, t_m)
    print(f" poisson weights in {time.perf_counter() - t0:.6f}s  "
          f"(non-negligible terms: {(weights >= 1e-6).sum()}/{e+1})")

    #E[U]
    t0 = time.perf_counter()
    u = expected_U(e, D, lambda_b, t_m, q,
                   detection_engine, map_engine)
    total = time.perf_counter() - t0
    n_terms = (weights >= 1e-6).sum()
    print(f"\nE[U](t_m={t_m}s) = {u:.4f}")
    print(f"expected_U took {total:.4f}s  "
          f"({total/n_terms*1000:.3f}ms per term, {n_terms} terms)")
    

    t0 = time.perf_counter()
    u = expected_U_fast(e, D, lambda_b, t_m, q,
                    detection_engine, map_engine)
    total = time.perf_counter() - t0
    n_terms = (weights >= 1e-6).sum()
    print(f"\nE[U](t_m={t_m}s) = {u:.4f}")
    print(f"fast_expected_U took {total:.4f}s  "
          f"({total/n_terms*1000:.3f}ms per term, {n_terms} terms)")