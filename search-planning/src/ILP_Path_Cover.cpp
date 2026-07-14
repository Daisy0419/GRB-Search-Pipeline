#include "ILP_Path_Cover.h"


GRBModel buildContinuousTimeModel(const ProblemInstance& inst) {
    GRBEnv env(true);
    GRBModel model(env);

    int n = inst.nTiles;
    int m = inst.nPixels;
    int start = inst.start;
    double D = inst.Deadline;
    double M = D + 1e-9;  // big-M: upper bound on schedule length

    // --- Variables ---

    // x[i] : 1 if tile i is observed
    std::vector<GRBVar> x(n);
    for (int i = 0; i < n; ++i) {
        x[i] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY,
                            "x_" + std::to_string(i));
    }

    // y[p] : 1 if pixel p is covered at least once
    std::vector<GRBVar> y(m);
    for (int p = 0; p < m; ++p) {
        y[p] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY,
                            "y_" + std::to_string(p));
    }

    // z[i][j] : 1 if we move directly from i to j
    std::vector<std::vector<GRBVar>> z(n, std::vector<GRBVar>(n));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i == j) continue;
            z[i][j] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY,
                                   "z_" + std::to_string(i) + "_" + std::to_string(j));
        }
    }

    // tau[i] : start time at tile i
    std::vector<GRBVar> tau(n);
    for (int i = 0; i < n; ++i) {
        tau[i] = model.addVar(0.0, D, 0.0, GRB_CONTINUOUS,
                              "tau_" + std::to_string(i));
    }

    model.update();

    // --- Objective: maximize sum_p prizes[p] * y[p] ---
    GRBLinExpr obj = 0.0;
    for (int p = 0; p < m; ++p) {
        obj += inst.prizes[p] * y[p];
    }
    model.setObjective(obj, GRB_MAXIMIZE);

    // --- Coverage constraints: y[p] <= sum_{i: p in coverage[i]} x[i] ---
    // Build expressions for each pixel
    std::vector<GRBLinExpr> coverExpr(m);
    for (int p = 0; p < m; ++p) coverExpr[p] = 0.0;

    for (int i = 0; i < n; ++i) {
        for (int p : inst.coverage[i]) {
            if (p < 0 || p >= m) continue; // basic safety
            coverExpr[p] += x[i];
        }
    }

    for (int p = 0; p < m; ++p) {
        model.addConstr(y[p] <= coverExpr[p],
                        "cover_once_p" + std::to_string(p));
    }

    // --- Start conditions ---
    model.addConstr(x[start] == 1, "start_visited");
    model.addConstr(tau[start] == 0.0, "start_time");

    // At most one departure from start (open path)
    {
        GRBLinExpr out = 0.0;
        for (int j = 0; j < n; ++j) {
            if (j == start) continue;
            out += z[start][j];
        }
        model.addConstr(out <= 1.0, "start_out");
    }

    // If k is visited, it has exactly one predecessor
    for (int k = 0; k < n; ++k) {
        if (k == start) continue;
        GRBLinExpr in = 0.0;
        for (int i = 0; i < n; ++i) {
            if (i == k) continue;
            in += z[i][k];
        }
        model.addConstr(in == x[k], "one_pred_" + std::to_string(k));
    }

    // Can only depart from a visited node: sum_j z[i][j] <= x[i]
    for (int i = 0; i < n; ++i) {
        GRBLinExpr out = 0.0;
        for (int j = 0; j < n; ++j) {
            if (i == j) continue;
            out += z[i][j];
        }
        model.addConstr(out <= x[i], "depart_visit_" + std::to_string(i));
    }

    // --- Continuous-time flow: tau[j] >= tau[i] + dwell_i + slew_ij - M(1 - z_ij) ---
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i == j) continue;
            double Tij = inst.dwell_times[i] + inst.slew_times[i][j];
            GRBLinExpr lhs = tau[j];
            GRBLinExpr rhs = tau[i] + Tij - M * (1.0 - z[i][j]);
            model.addConstr(lhs >= rhs,
                            "time_flow_" + std::to_string(i) + "_" + std::to_string(j));
        }
    }

    // --- Deadline: tau[i] + dwell_i <= D if x[i] = 1 ---
    for (int i = 0; i < n; ++i) {
        GRBLinExpr lhs = tau[i] + inst.dwell_times[i];
        GRBLinExpr rhs = D + M * (1.0 - x[i]);
        model.addConstr(lhs <= rhs, "deadline_" + std::to_string(i));
    }

    model.update();
    return model;
}



GRBModel buildMTZModel(const ProblemInstance& inst) {
    GRBEnv env(true);
    GRBModel model(env);

    int n = inst.nTiles;
    int m = inst.nPixels;
    int start = inst.start;
    double D = inst.Deadline;

    // --- Variables ---

    // x[i] : visited tile
    std::vector<GRBVar> x(n);
    for (int i = 0; i < n; ++i) {
        x[i] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY,
                            "x_" + std::to_string(i));
    }

    // y[p] : pixel covered at least once
    std::vector<GRBVar> y(m);
    for (int p = 0; p < m; ++p) {
        y[p] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY,
                            "y_" + std::to_string(p));
    }

    // z[i][j] : travel arc
    std::vector<std::vector<GRBVar>> z(n, std::vector<GRBVar>(n));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i == j) continue;
            z[i][j] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY,
                                   "z_" + std::to_string(i) + "_" + std::to_string(j));
        }
    }

    // MTZ order variables u[i] in [0, n]
    std::vector<GRBVar> u(n);
    for (int i = 0; i < n; ++i) {
        u[i] = model.addVar(0.0, n, 0.0, GRB_CONTINUOUS,
                            "u_" + std::to_string(i));
    }

    model.update();

    // --- Objective ---
    GRBLinExpr obj = 0.0;
    for (int p = 0; p < m; ++p) {
        obj += inst.prizes[p] * y[p];
    }
    model.setObjective(obj, GRB_MAXIMIZE);

    // --- Coverage: y[p] <= sum_{i: p in coverage[i]} x[i] ---
    std::vector<GRBLinExpr> coverExpr(m);
    for (int p = 0; p < m; ++p) coverExpr[p] = 0.0;

    for (int i = 0; i < n; ++i) {
        for (int p : inst.coverage[i]) {
            if (p < 0 || p >= m) continue;
            coverExpr[p] += x[i];
        }
    }

    for (int p = 0; p < m; ++p) {
        model.addConstr(y[p] <= coverExpr[p],
                        "cover_once_p" + std::to_string(p));
    }

    // --- Budget constraint: sum(s_ij z_ij) + sum(T_i x_i) <= D ---
    {
        GRBLinExpr totalTime = 0.0;
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                if (i == j) continue;
                totalTime += inst.slew_times[i][j] * z[i][j];
            }
        }
        for (int i = 0; i < n; ++i) {
            totalTime += inst.dwell_times[i] * x[i];
        }
        model.addConstr(totalTime <= D, "budget");
    }

    // --- Path + start structure ---
    model.addConstr(x[start] == 1, "start_visited");

    // At most one departure from start
    {
        GRBLinExpr out = 0.0;
        for (int j = 0; j < n; ++j) {
            if (j == start) continue;
            out += z[start][j];
        }
        model.addConstr(out <= 1.0, "start_out");
    }

    // Incoming arcs bounded by visitation (at most one predecessor)
    for (int k = 0; k < n; ++k) {
        if (k == start) continue;
        GRBLinExpr in = 0.0;
        for (int i = 0; i < n; ++i) {
            if (i == k) continue;
            in += z[i][k];
        }
        model.addConstr(in <= x[k], "in_le_visit_" + std::to_string(k));
    }

    // Can only depart from visited node
    for (int i = 0; i < n; ++i) {
        GRBLinExpr out = 0.0;
        for (int j = 0; j < n; ++j) {
            if (i == j) continue;
            out += z[i][j];
        }
        model.addConstr(out <= x[i], "depart_visit_" + std::to_string(i));
    }

    // --- MTZ subtour elimination ---
    // u[start] = 0
    model.addConstr(u[start] == 0.0, "u_start");

    // Bounds: u[i] tied to x[i]; if not visited, u[i] = 0 is allowed.
    for (int i = 0; i < n; ++i) {
        if (i == start) continue;
        model.addConstr(u[i] <= n * x[i], "u_ub_" + std::to_string(i));
        model.addConstr(u[i] >= x[i],     "u_lb_" + std::to_string(i));
    }

    // If z[i][j] = 1, then u[j] >= u[i] + 1 (mod big-M relaxation)
    double Mmtz = n + 1.0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i == j) continue;
            GRBLinExpr lhs = u[j];
            GRBLinExpr rhs = u[i] + 1.0 - Mmtz * (1.0 - z[i][j]);
            model.addConstr(lhs >= rhs,
                            "mtz_" + std::to_string(i) + "_" + std::to_string(j));
        }
    }

    model.update();
    return model;
}




std::vector<int> gurobiPathCover(const std::vector<std::vector<double>>& slew_times,
                                const std::vector<double>& dwell_times,
                                const std::vector<double>& pixel_probs,
                                const std::vector<std::vector<int>>& member_pixels,
                                int start, int end, double Budget,
                                double mipGap, double timeLimit,
                                const std::vector<int>& initialPath) {

        ProblemInstance inst(
            start,
            Budget,
            pixel_probs,
            dwell_times,
            slew_times,
            member_pixels
        );


}
