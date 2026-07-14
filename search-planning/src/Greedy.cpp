#include "helplers.h"

#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>
#include <random>
#include <fstream>
#include <sstream>
#include <string>
#include <chrono>

void sortWithIndices(std::vector<double>& values, std::vector<int>& indices) {
    std::vector<std::pair<double, int>> valueIndexPairs;
    for (size_t i = 0; i < values.size(); ++i) {
        valueIndexPairs.emplace_back(values[i], i);
    }

    std::sort(valueIndexPairs.begin(), valueIndexPairs.end(),
              [](const std::pair<double, int>& a, const std::pair<double, int>& b) {
                  return a.first > b.first;
              });

    for (size_t i = 0; i < valueIndexPairs.size(); ++i) {
        values[i] = valueIndexPairs[i].first;
        indices[i] = valueIndexPairs[i].second;
    }
}

// s-t path; greedy on prize
std::vector<int> prizeGreedyPathTwoFixed(const std::vector<std::vector<double>>& costs, 
                                         const std::vector<double>& probability, 
                                         double budget, int start_tile, int end_tile) {
    std::vector<std::pair<double, int>> prize(probability.size());
    for (int i = 0; i < probability.size(); ++i) {
        prize[i] = {probability[i], i};
    }

    std::sort(prize.begin(), prize.end(),
              [](const std::pair<double, int>& a, const std::pair<double, int>& b) {
                  return a.first > b.first;
              });

    std::vector<bool> visited(probability.size(), false);
    std::vector<int> path{start_tile};
    visited[start_tile] = true;

    int current_tile = start_tile;

    for (const auto& [tile_probability, tile] : prize) {
        if (tile == current_tile || visited[tile] || tile_probability == 0.0) continue;

        double cost_to_tile = costs[current_tile][tile];
        double cost_to_end = costs[tile][end_tile];

        if (cost_to_tile + cost_to_end > budget) continue;

        budget -= cost_to_tile;
        current_tile = tile;
        path.push_back(current_tile);
        visited[tile] = true;
    }

    // Final check: is end_tile reachable?
    if (costs[current_tile][end_tile] <= budget) {
        path.push_back(end_tile);
    } else {
        std::cerr << "something went wrong in prizeGreedyPathTwoFixed\n";
        return {start_tile, end_tile};
    }

    return path;
}
