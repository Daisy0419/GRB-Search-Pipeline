#pragma once
#include <vector>

void sortWithIndices(std::vector<double>& values, std::vector<int>& indices);

// greedy algorithm wrapper
std::vector<int> prizeGreedyPathTwoFixed(const std::vector<std::vector<double>>& costs, 
                                         const std::vector<double>& probability, 
                                         double budget, int start_tile, int end_tile);