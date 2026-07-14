#include "AntColony.h"
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
#include <omp.h>

AntColony::AntColony(std::vector<std::vector<double>> costs, std::vector<double> prize_) {
    distances = costs;
    prizes = prize_;
    // for(auto p : prizes) {
    //     std::cout << p << " " ;
    // }
    // std::cout << " end print prize" << std::endl;

    NUM_CITIES = costs.size();
    NUM_ANTS = 2 * NUM_CITIES;

    initialize_heuristic();
    pheromones.resize(NUM_CITIES, std::vector<double>(NUM_CITIES, 0.5));
    // initialize_pheromones();
}

void AntColony::initialize_pheromones() {
    pheromones.resize(NUM_CITIES, std::vector<double>(NUM_CITIES));
    for (int i = 0; i < NUM_CITIES; i++) {
        for (int j = 0; j < NUM_CITIES; j++) {
            pheromones[i][j] = i != j ? prizes[j] * 5 / distances[i][j] + 0.5 : 0.0;
        }
    }
}

void AntColony::initialize_heuristic() {
    heuristic.resize(NUM_CITIES, std::vector<double>(NUM_CITIES));
    for (int i = 0; i < NUM_CITIES; i++) {
        for (int j = 0; j < NUM_CITIES; j++) {
            heuristic[i][j] = std::pow(prizes[j] * 5, GAMMA) * 
                               std::pow(1.0 / distances[i][j], BETA);
            // std::cout << "prizes: " << prizes[j] << " costs: " << distances[i][j] 
            // << heuristic[i][j] << std::endl;
        }
    }
}


// std::pair<int, double> AntColony::choose_next_city(int current_city,
//                                                    const std::vector<bool>& visited_set,
//                                                    double budget) {
//     std::vector<double> probabilities(NUM_CITIES, 0.0);
//     double sum = 0.0;

//     // Precompute candidates
//     std::vector<int> candidates;
//     candidates.reserve(NUM_CITIES);

//     for (int j = 0; j < NUM_CITIES; j++) {
//         if (!visited_set[j] && distances[current_city][j] <= budget) {
//             double heuristic = std::pow(pheromones[current_city][j], ALPHA) *
//                                std::pow(prizes[j] * 5, GAMMA) *
//                                std::pow(1.0 / distances[current_city][j], BETA);
//             probabilities[j] = heuristic;
//             sum += heuristic;
//             candidates.push_back(j);
//         }
//     }

//     if (sum == 0.0) return {-1, 0.0}; // No valid moves

//     // Normalize probabilities
//     for (int j : candidates) {
//         probabilities[j] /= sum;
//     }

//     // Select next city
//     double rand_prob = random_double(0.0, 1.0);
//     double cumulative = 0.0;
//     for (int j : candidates) {
//         cumulative += probabilities[j];
//         if (rand_prob <= cumulative) {
//             return {j, distances[current_city][j]};
//         }
//     }

//     return {-1, 0.0};
// }

std::pair<int, double> AntColony::choose_next_city(int current_city,
                                                   const std::vector<bool>& visited_set,
                                                   double budget) {
    double sum = 0.0;
    std::vector<std::pair<int, double>> candidates; 

    // Single pass to compute sum and collect candidates
    for (int j = 0; j < NUM_CITIES; j++) {
        if (!visited_set[j] && distances[current_city][j] <= budget && distances[current_city][j] > 0.0) {
            double prob = std::pow(pheromones[current_city][j], ALPHA) * heuristic[current_city][j];
            if (prob > 0.0) {
                sum += prob;
                candidates.emplace_back(j, prob);
            }
        }
    }

    // if (candidates.empty()) {
    //     return {-1, 0.0};
    // }

    if (candidates.empty()) {
        // std::cout << "No candidates for current_city=" << current_city 
        //         << ", budget=" << budget << std::endl;
        // for (int j = 0; j < NUM_CITIES; j++) {
        //     if (!visited_set[j]) {
        //         std::cout << "  j=" << j << ", distance=" << distances[current_city][j] 
        //                 << ", pheromone=" << pheromones[current_city][j] 
        //                 << ", heuristic=" << heuristic[current_city][j] << std::endl;
        //     }
        // }
        return {-1, 0.0};
    }

    // Roulette wheel selection in one pass
    double rand_prob = random_double(0.0, sum);
    double cumulative = 0.0;
    for (const auto& [city, prob] : candidates) {
        cumulative += prob;
        if (rand_prob <= cumulative) {
            return {city, distances[current_city][city]};
        }
    }

    // Fallback (should rarely happen due to sum check)
    return {candidates.back().first, distances[current_city][candidates.back().first]};
}

std::vector<int> AntColony::ant_tour(double budget, int start_city) {
    std::vector<int> visited;
    std::vector<bool> visited_set(NUM_CITIES, false);
    
    visited.push_back(start_city);
    visited_set[start_city] = true;

    int current_city = start_city;
    double remaining_budget = budget;

    while (remaining_budget > 0) {
        auto [next_city, cost] = choose_next_city(current_city, visited_set, remaining_budget);
        if (next_city == -1) break;

        visited.push_back(next_city);
        visited_set[next_city] = true;

        current_city = next_city;
        remaining_budget -= cost;
    }
    // std::cout << "find tour: " << visited.size() << std::endl;
    // std::cout << "remaining_budget: " << remaining_budget << std::endl;

    return visited;
}

double AntColony::simulate_ants(std::vector<int>& best_tour, double &best_prize, 
                                double initial_budget, int start_city) {
    // double best_prize = 0;
    std::vector<std::vector<int>> visited(NUM_ANTS);

    // Simulate each ant's tour
    #pragma omp parallel for schedule(dynamic, 5)
    for (int ant = 0; ant < NUM_ANTS; ant++) {
        visited[ant] = ant_tour(initial_budget, start_city);
    }

    //fix-cross(2 opt)
    #pragma omp parallel for schedule(dynamic, 5)
    for (size_t ant = 0; ant < visited.size(); ant++) {
        fix_cross(visited[ant], distances);
    }

    // Evaporate pheromones
    #pragma omp parallel for collapse(2)
    for (int i = 0; i < NUM_CITIES; i++) {
        for (int j = 0; j < NUM_CITIES; j++) {
            pheromones[i][j] *= (1.0 - EVAPORATION_RATE);
        }
    }

    // Update pheromones
    #pragma omp parallel for schedule(dynamic, 5)
    for (int ant = 0; ant < NUM_ANTS; ant++) {
        if (visited[ant].size() < 2) continue;

        double tour_cost = 0.0;
        double tour_prize = prizes[visited[ant].back()];
        for (size_t i = 0; i < visited[ant].size() - 1; i++) {
            tour_cost += distances[visited[ant][i]][visited[ant][i + 1]];
            tour_prize += prizes[visited[ant][i]];

        }
        // double tour_prize = 0;
        // for (int city : visited[ant]) {
        //     tour_prize += prizes[city];
        // }
        #pragma omp critical
        if (tour_prize > best_prize) {
            best_prize = tour_prize;
            best_tour = visited[ant];
            // std::cout << "New best prize found: " << best_prize << ", cost: " << tour_cost << std::endl;
        }

        double contribution = Q * tour_prize / tour_cost;
        for (size_t i = 0; i < visited[ant].size() - 1; i++) {
            #pragma omp atomic
            pheromones[visited[ant][i]][visited[ant][i + 1]] += contribution;
        }
    }

    return best_prize;
}

std::vector<int> AntColony::ant_colony_optimization(double budget, int start_city) {
    std::vector<int> best_tour;
    double best_prize = 0;

    for (int iteration = 0; iteration < MAX_ITERATIONS; iteration++) {
        double prize = simulate_ants(best_tour, best_prize, budget, start_city);
        // std::cout << "best_prize: " << best_prize << std::endl;
        // std::cout << "budget: " << budget << std::endl;
        // best_prize = std::max(best_prize, prize);
    }
    return best_tour;

}



std::pair<int, double> AntColony::choose_next_city(int current_city, int end_city,
                                                   const std::vector<bool>& visited_set,
                                                   double budget) {
    double sum = 0.0;
    std::vector<std::pair<int, double>> candidates; 

    // Single pass to compute sum and collect candidates
    for (int j = 0; j < NUM_CITIES; j++) {
        if (!visited_set[j] && distances[current_city][j] + distances[j][end_city] <= budget) {
            double prob = std::pow(pheromones[current_city][j], ALPHA) * heuristic[current_city][j];
            if (prob > 0.0) {
                sum += prob;
                candidates.emplace_back(j, prob);
            }
        }
    }

    if (candidates.empty()) {
        return {-1, 0.0};
    }

    // Roulette wheel selection in one pass
    double rand_prob = random_double(0.0, sum);
    double cumulative = 0.0;
    for (const auto& [city, prob] : candidates) {
        cumulative += prob;
        if (rand_prob <= cumulative) {
            return {city, distances[current_city][city]};
        }
    }

    return {candidates.back().first, distances[current_city][candidates.back().first]};
}


std::vector<int> AntColony::ant_tour(double budget, int start_city, int end_city) {
    std::vector<int> visited;
    std::vector<bool> visited_set(NUM_CITIES, false);
    
    visited.push_back(start_city);
    visited_set[start_city] = true;
    visited_set[end_city] = true;

    int current_city = start_city;
    double remaining_budget = budget;

    while (remaining_budget > 0) {
        auto [next_city, cost] = choose_next_city(current_city, end_city, visited_set, remaining_budget);
        if (next_city == -1) break;

        visited.push_back(next_city);
        visited_set[next_city] = true;

        current_city = next_city;
        remaining_budget -= cost;
    }

    if (distances[current_city][end_city] <= remaining_budget) {
        visited.push_back(end_city);
        visited_set[end_city] = true;
    } else {
        std::cerr << "not enough budget to go end city\n";
        visited.push_back(end_city);  
    }

    // visited.push_back(end_city);
    // visited_set[end_city] = true;   
    // std::cout << "find tour: " << visited.size() << std::endl;
    // std::cout << "remaining_budget: " << remaining_budget << std::endl;
    return visited;
}

double AntColony::simulate_ants(std::vector<int>& best_tour, double &best_prize, 
                                double initial_budget, int start_city, int end_city) {
    // double best_prize = 0;
    std::vector<std::vector<int>> visited(NUM_ANTS);

    // Simulate each ant's tour
    #pragma omp parallel for schedule(dynamic, 5)
    for (int ant = 0; ant < NUM_ANTS; ant++) {
        visited[ant] = ant_tour(initial_budget, start_city, end_city);
    }

    //fix-cross(2 opt)
    #pragma omp parallel for schedule(dynamic, 5)
    for (size_t ant = 0; ant < visited.size(); ant++) {
        fix_cross(visited[ant], distances);
    }

    // Evaporate pheromones
    #pragma omp parallel for collapse(2)
    for (int i = 0; i < NUM_CITIES; i++) {
        for (int j = 0; j < NUM_CITIES; j++) {
            pheromones[i][j] *= (1.0 - EVAPORATION_RATE);
        }
    }

    // Update pheromones
    #pragma omp parallel for schedule(dynamic, 5)
    for (int ant = 0; ant < NUM_ANTS; ant++) {
        if (visited[ant].size() < 2) continue;

        double tour_cost = 0.0;
        double tour_prize = prizes[visited[ant].back()];
        for (size_t i = 0; i < visited[ant].size() - 1; i++) {
            tour_cost += distances[visited[ant][i]][visited[ant][i + 1]];
            tour_prize += prizes[visited[ant][i]];

        }
        // double tour_prize = 0;
        // for (int city : visited[ant]) {
        //     tour_prize += prizes[city];
        // }
        #pragma omp critical
        if (tour_prize > best_prize) {
            best_prize = tour_prize;
            best_tour = visited[ant];
            // std::cout << "New best prize found: " << best_prize << ", cost: " << tour_cost << std::endl;
        }

        double contribution = Q * tour_prize / tour_cost;
        for (size_t i = 0; i < visited[ant].size() - 1; i++) {
            #pragma omp atomic
            pheromones[visited[ant][i]][visited[ant][i + 1]] += contribution;
        }
    }

    return best_prize;
}

std::vector<int> AntColony::ant_colony_optimization(double budget, int start_city, int end_city) {
    std::vector<int> best_tour;
    double best_prize = 0;

    for (int iteration = 0; iteration < MAX_ITERATIONS; iteration++) {
        double prize = simulate_ants(best_tour, best_prize, budget, start_city, end_city);
        // std::cout << "best_prize: " << best_prize << std::endl;
        // std::cout << "budget: " << budget << std::endl;
        // best_prize = std::max(best_prize, prize);
    }
    return best_tour;

}