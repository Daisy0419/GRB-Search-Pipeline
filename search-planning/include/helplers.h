#pragma once

#include <vector>

//random number generater
double random_double(double min, double max);
int random_int(int min, int max);
std::vector<int> unique_random_ints(int min, int max, int n);

//2-opt
void fix_cross(std::vector<int>& path, const std::vector<std::vector<double>>& costs);
bool fix_cross_st_path(std::vector<int>& path, const std::vector<std::vector<double>>& costs);

//compute cost of a path
double calculate_path_cost(const std::vector<int>& path, const std::vector<std::vector<double>>& costs);

void insertHighValueCheapest(std::vector<int>& path,
                                const std::vector<std::vector<double>>& cost,
                                const std::vector<double>& prize,
                                double budget,
                                double& current_cost,
                                std::vector<bool>& visited);