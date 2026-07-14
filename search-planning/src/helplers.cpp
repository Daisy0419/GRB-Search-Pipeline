
#include <iostream>
#include <random>
#include <algorithm>

#include "helplers.h"

// Random double in [min, max)
double random_double(double min, double max) {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(min, max);
    return dis(gen);
}

// Random integer in [min, max] 
int random_int(int min, int max) {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(min, max);
    return dis(gen);
}

// n unique integers sampled without replacement from [min, max]
std::vector<int> unique_random_ints(int min, int max, int n) {
    if (n > (max - min + 1)) {
        throw std::invalid_argument("Cannot generate more unique numbers than the range size.");
    }
    std::vector<int> numbers(max - min + 1);
    std::iota(numbers.begin(), numbers.end(), min);

    static std::random_device rd;
    static std::mt19937 gen(rd());
    std::shuffle(numbers.begin(), numbers.end(), gen);

    return std::vector<int>(numbers.begin(), numbers.begin() + n);
}


// 2-opt, checks all valid pairs of edges in the path
void fix_cross(std::vector<int>& path, const std::vector<std::vector<double>>& costs) {
    if (costs.empty() || costs.size() != costs[0].size()) {
        throw std::invalid_argument("Cost matrix must be non-empty and square.");
    }
    if (path.size() > costs.size()) {
        throw std::invalid_argument("Path contains nodes outside cost matrix bounds.");
    }
    if (path.size() < 4) { // at least 4 nodes
        return;  
    }

    for (size_t i = 1; i < path.size() - 2; ++i) {
        for (size_t j = i + 1; j < path.size() - 2; ++j) {
            int a = path[i - 1]; 
            int b = path[i];   
            int c = path[j];    
            int d = path[j + 1]; 

            double original_cost = costs[a][b] + costs[c][d];
            double uncrossed_cost = costs[a][c] + costs[b][d];

            if (uncrossed_cost < original_cost - 1e-9) {
                std::reverse(path.begin() + i, path.begin() + j + 1);
            }
        }
    }
}

// 2-opt, ensures that the path remains a valid open path from fixed start to fixed end
bool fix_cross_st_path(std::vector<int>& path, const std::vector<std::vector<double>>& costs) {
    bool is_improved = false;
    if (costs.empty() || costs.size() != costs[0].size()) {
        throw std::invalid_argument("Cost matrix must be non-empty and square.");
    }
    if (path.size() > costs.size()) {
        std::cout << "path.size(): " << path.size() << " costs.size() " << costs.size();
        throw std::invalid_argument("Path contains nodes outside cost matrix bounds.");
    }
    if (path.size() < 4) {
        return is_improved;
    }

    

    // Avoid modifying edges adjacent to start (s) or end (t)
    for (size_t i = 1; i < path.size() - 2; ++i) {
        for (size_t j = i + 1; j < path.size() - 1; ++j) {
            int a = path[i - 1];
            int b = path[i];
            int c = path[j];
            int d = path[j + 1];

            if (i == 1 && j + 1 == path.size() - 1) continue; // affect both s and t
            if (i == 1 && a == path[0]) continue;             // affects s
            if (j + 1 == path.size() - 1 && d == path.back()) continue; // affects t

            double original_cost = costs[a][b] + costs[c][d];
            double uncrossed_cost = costs[a][c] + costs[b][d];

            if (uncrossed_cost < original_cost - 1e-12) {
                std::reverse(path.begin() + i, path.begin() + j + 1);
                is_improved = true;
            }
        }
    }
    return is_improved;
}



// compute total cost of a given path
double calculate_path_cost(const std::vector<int>& path, const std::vector<std::vector<double>>& costs) {
    double total_cost = 0.0;
    for (size_t i = 1; i < path.size(); ++i) {
        total_cost += costs[path[i - 1]][path[i]];
    }
    return total_cost;
}


// // Insert nodes with highest possible value in cheapest position until budget exhausts
// void insertHighValueCheapest(std::vector<int>& path,
//                                 const std::vector<std::vector<double>>& cost,
//                                 const std::vector<double>& prize,
//                                 double budget,
//                                 double& current_cost,
//                                 std::vector<bool>& visited) {
//     const int n = static_cast<int>(cost.size());

//     // Build candidate list ordered by decreasing prize
//     std::vector<int> cand;
//     cand.reserve(n);
//     for (int v = 0; v < n; ++v)
//         if (!visited[v] && v != path.front() && v != path.back())
//             cand.push_back(v);

//     std::sort(cand.begin(), cand.end(),
//               [&](int a, int b){ return prize[a] > prize[b]; });

//     // Try each node repeatedly until no more insertions possible
//     bool progress = true;
//     while (progress) {
//         progress = false;

//         for (int idx = 0; idx < static_cast<int>(cand.size()); ++idx) {
//             int node = cand[idx];
//             if (visited[node]) continue; 

//             // Find cheapest insertion position
//             double best_extra = std::numeric_limits<double>::infinity();
//             std::size_t best_pos = 0;

//             for (std::size_t j = 0; j < path.size() - 1; ++j) {
//                 double extra = cost[path[j]][node] +
//                                cost[node][path[j+1]] -
//                                cost[path[j]][path[j+1]];
//                 if (extra < best_extra) {
//                     best_extra = extra;
//                     best_pos = j + 1;
//                 }
//             }

//             if (current_cost + best_extra <= budget + 1e-12) {
//                 path.insert(path.begin() + best_pos, node);
//                 current_cost += best_extra;
//                 visited[node] = true;
//                 progress = true;
//             }
//         }
//     }
// }