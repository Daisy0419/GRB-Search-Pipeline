#pragma once

#include <vector>
#include <string>
#include <unordered_set>

std::vector<int> genetic_optimization_st(const std::vector<std::vector<double>>& costs, const std::vector<double>& prizes, 
                          double budget, int start_city, int end_city, std::vector<std::vector<int>> init_paths={});
