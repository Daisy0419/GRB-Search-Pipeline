#pragma once
#include <vector>
#include <string>
#include <list>
#include <unordered_map>

#include <lemon/list_graph.h>
#include <lemon/kruskal.h>
#include <lemon/matching.h>


void sortNodesInRange(const std::vector<double>& prizes, std::vector<int>& indices, std::pair<int, int> range);
void selectNodesPrizeRatio(const std::vector<std::vector<double>>& costs,
                            const std::vector<double>& prizes,
                            std::vector<double>& prizes_selected, 
                            std::vector<std::vector<double>>& costs_selected, 
                            std::vector<int>& indices, 
                            int init_pos, double cost_threshold);


typedef lemon::ListGraph Graph;
typedef Graph::Node Node;
typedef Graph::Edge Edge;

void buildGraphUpdate(const std::vector<std::vector<double>>& costs, 
                      const std::vector<int>& indices, int N_nodes,
                      Graph& g, Graph::EdgeMap<double>& weight);
void buildMST(const Graph& g, const Graph::EdgeMap<double>& weight, std::vector<Edge>& mst_edges);

double computeMSTWeight(const Graph& g, const Graph::EdgeMap<double>& weight, 
                        const std::vector<Edge>& mst_edges);

void buildGraph(const std::vector<std::vector<double>>& costs, Graph& g, Graph::EdgeMap<double>& weight);

std::vector<int> GCP_BestPrizeTwoFix(const std::vector<std::vector<double>>& costs, 
                          const std::vector<double>& prizes, 
                          double budget, int s_idx, int t_idx);

std::vector<int> GCP_PrizeBoostTwoFix(const std::vector<std::vector<double>>& costs, 
                          const std::vector<double>& prizes, 
                          double budget, int s_idx, int t_idx);

std::vector<int> GCP_PrizeRatioTwoFix(const std::vector<std::vector<double>>& costs, 
                          const std::vector<double>& prizes, 
                          double budget, int s_idx, int t_idx);

std::vector<int> GCP(const std::vector<std::vector<double>>& costs, 
                                    const std::vector<double>& prizes, 
                                    double budget, int s_idx, int t_idx);



double sumPrizes(const std::vector<double>& prizes, const std::vector<int>& path);

std::vector<int> christofidesPathTwoFixed(const Graph& g,
                         const std::vector<std::vector<double>>& costs,
                         const std::vector<int>& indices,
                         int N_nodes,
                         const std::vector<Edge>& mst_edges,
                         int s_idx,
                         int t_idx);

void greedyExtendPath(const std::vector<std::vector<double>>& costs, const std::vector<double>& prizes,
                      std::vector<int>& path, double& total_cost, double budget);


// void selectNodesPrizeRatio_2(const std::vector<std::vector<double>>& costs,
//                             const std::vector<double>& prizes,
//                             std::vector<int>& indices, 
//                             std::vector<bool>& selected,
//                             std::vector<double>& minDist,
//                             std::priority_queue<std::pair<double, int>>& heap,
//                             int num);

// void selectNodesPrizeRatio_(const std::vector<std::vector<double>>& costs,
//                             const std::vector<double>& prizes,
//                             std::vector<int>& indices, 
//                             std::vector<bool>& selected,
//                             std::vector<double>& minDist,
//                             std::priority_queue<std::pair<double, int>>& heap,
//                             int num);

struct PrimMSTResult {
    double totalWeight;
    std::vector<std::vector<std::pair<int,double>>> adj;  // adjacency list
    std::vector<int> parent;                               // parent array
};

PrimMSTResult primMST(const std::vector<std::vector<double>>& costs,
                      const std::vector<int>& indices,
                      int N);

std::vector<int> christofidesPathTwoFixed(
        const std::vector<std::vector<double>>& costs,
        const std::vector<int>& indices,
        int N_nodes,
        const PrimMSTResult& mst,
        int s_idx,
        int t_idx);

// void binarySearchBestPathTwoFixed(
//         const std::vector<std::vector<double>>& costs,
//         const std::vector<double>& prizes,
//         const std::vector<int>& indices,
//         std::vector<int>& best_mst_path,
//         int N_min, int N_max, double budget);
