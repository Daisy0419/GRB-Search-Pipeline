#include "AntColony.h"
#include "Genetic.h"
#include "Greedy.h"
#include "ReadData.h"
// #include "BranchBound.h"
#include "ILP_gurobi.h"
#include "SimulatedAnnealing.h"
// #include "bpc_tsp.h"
#include "GCP.h"
// #include "ILP_cplex.h"
#include "SaveResults.h"
#include "BuildGraph.h"

#include <chrono>
#include <string>
#include <iostream>
#include <sstream>
#include <fstream>
#include <filesystem> 
#include <numeric>

#include <fstream>
#include <sstream>
#include <string>
#include <unordered_map>


struct SourceTileInfo {
    int tile_id;
    int ipix;
    double ra;
    double dec;
};

std::unordered_map<std::string, SourceTileInfo> load_source_tiles(const std::string& csv_path) {
    std::unordered_map<std::string, SourceTileInfo> lookup;
    std::ifstream fin(csv_path);
    std::string line;
    std::getline(fin, line); // skip header: map,RightTile,RightIpix,RightRA,RightDec

    while (std::getline(fin, line)) {
        std::istringstream ss(line);
        std::string map_name, tile_str, ipix_str, ra_str, dec_str;
        std::getline(ss, map_name, ',');
        std::getline(ss, tile_str, ',');
        std::getline(ss, ipix_str, ',');
        std::getline(ss, ra_str, ',');
        std::getline(ss, dec_str, ',');

        lookup[map_name] = {
            std::stoi(tile_str),
            std::stoi(ipix_str),
            std::stod(ra_str),
            std::stod(dec_str)
        };
    }
    return lookup;
}


// auto source_lookup = load_source_tiles("source_tiles.csv");

// std::string map_name = std::filesystem::path(mapfile).filename().string();
// auto it = source_lookup.find(map_name);
// if (it == source_lookup.end()) {
//     std::cerr << "No source tile for " << map_name << "\n";
//     return 1;
// }
// int source_tile = it->second.tile_id;


// //wrapper function on small instances test
// //test algorihms: greedy, genetic, GCP, gurobi
// int test_algorithms (std::string tilefile, std::string mapfile, std::string out_file, 
//                     double budget, double dwell_time, 
//                     double w_max, double w_acc, double settle_time,
//                     bool is_deepslow, int& num_tiles) {
//     // std::chrono::high_resolution_clock::time_point start = std::chrono::high_resolution_clock::now();

//     std::vector<std::vector<double>> costs;
//     std::vector<double> probability;
//     std::vector<int> ranks;
//     std::vector<double> dwell_times;

//     std::vector<double> source;
//     int64_t nsrc_events, n_bkg_events;
//     int zenithtile;

//     // std::string file = mapfile;
//     double time_limit = 1200;
//     double accu_thr = 1e-6;
//     int init_pos_idx = -1;

//     // auto [start_idx, end_idx, padding] = buildGraphOrienteering(file, costs, probability, ranks, dwell_times,
//     //                                                             slew_rate, is_deepslow, init_pos_idx);
//     // get_timer().mark("init");
//     auto [start_idx, end_idx, padding] = buildGraphOrienteering(tilefile, mapfile, costs, probability, ranks, dwell_times, 
//                                                                 dwell_time, w_max, w_acc, settle_time, is_deepslow, num_tiles, 
//                                                                 init_pos_idx, zenithtile, source, nsrc_events, n_bkg_events);
//     get_timer().mark("mapping");

        
//     // std::cout << "padding: " << padding << "\n";
//     // std::chrono::high_resolution_clock::time_point start;
//     // std::chrono::high_resolution_clock::time_point end;
//     // std::chrono::duration<double> elapsed_seconds;

//     // std::chrono::high_resolution_clock::time_point mapping_end = std::chrono::high_resolution_clock::now();
//     // std::chrono::duration<double> mapping_elapsed_seconds = mapping_end - mapping_start;
//     // std::cout << "mapping time (wallclock): " << mapping_elapsed_seconds.count() << " seconds" << std::endl;

//     // // gurobi with time limit
//     // get_memory_log().sample_start("ilp");
//     // std::cout << "*********gurobi solution with time limit*********" << std::endl;
//     // // start = std::chrono::high_resolution_clock::now();
//     // std::vector<int> ilp_path2 = gurobiSolveST(costs, probability, start_idx, end_idx, budget+padding, accu_thr, time_limit);
//     // get_timer().mark("ilp");
//     // // end = std::chrono::high_resolution_clock::now();
//     // print_path(costs, probability, ranks, ilp_path2, padding);
//     // // elapsed_seconds = end - start;
//     // // std::cout << "running time (wallclock): " << elapsed_seconds.count() << "seconds" << std::endl;
//     // // save_result(out_file, "Gurobi_Flow", file, budget, w_max,costs, probability, ranks, ilp_path2, elapsed_seconds.count(), padding);
//     // save_result(out_file, "ilp", mapfile, budget, w_max,costs, probability, ranks, ilp_path2, get_timer().get_elapsed("ilp")/1000, padding);
//     // get_memory_log().sample_stop("ilp");

//     // std::chrono::high_resolution_clock::time_point start = std::chrono::high_resolution_clock::now();
//     // get_memory_log().sample_start("gcp");
//     // GCP
//     std::cout << "*********running GCP*********" << std::endl;
//     // start = std::chrono::high_resolution_clock::now();
//     std::vector<int> mst_pathH1 = GCP(costs, probability, budget+padding, start_idx, end_idx);
//     get_timer().mark("gcp1");
    
//     double eff_budget = budget + padding - (get_timer().get_elapsed("mapping") + get_timer().get_elapsed("gcp1"))/1000;
//     std::vector<int> mst_pathH2 = GCP(costs, probability, eff_budget, start_idx, end_idx);
//     get_timer().mark("gcp2");

//     double runtime1 = (get_timer().get_elapsed("mapping") + get_timer().get_elapsed("gcp1"))/1000;
//     double runtime2 = (get_timer().get_elapsed("mapping") + get_timer().get_elapsed("gcp2"))/1000;
//     save_result(out_file, "GCP", mapfile, budget, w_max,costs, probability, ranks, mst_pathH2, 
//                 runtime1, runtime2, padding, num_tiles, zenithtile, source, nsrc_events, n_bkg_events, source_tile, detected);

//     // std::cout << mst_pathH1.size() << " " << mst_pathH2.size() << "\n";
//     return mst_pathH2.size();


//     // get_memory_log().sample_start("annealing");
//     // // annealing
//     // std::cout << "*********running annealing*********" << std::endl;
//     // // start = std::chrono::high_resolution_clock::now();
//     // // genetic_optimization(costs, budget, 0);
//     // std::vector<int>  annealing_path = simulated_annealing_optimization(costs, probability, budget+padding, start_idx, end_idx);
//     // get_timer().mark("Annealing");
//     // // end = std::chrono::high_resolution_clock::now();
//     // // print_path(costs, probability, ranks, annealing_path, padding);
//     // // elapsed_seconds = end - start;
//     // // std::cout << "running time (wallclock): " << elapsed_seconds.count() << "seconds" << std::endl;
//     // save_result(out_file, "Annealing", mapfile, budget, w_max,costs, probability, ranks, annealing_path, get_timer().get_elapsed("Annealing")/1000, padding);
//     // get_memory_log().sample_stop("annealing");

// }

bool is_detected(const std::vector<int>& path, const std::vector<int>& ranks, int source) {
    for(int p : path) {
        if(source == ranks[p]) return true;
    }
    return false;
}



std::vector<int> test_algorithms2 (std::string tilefile, std::string mapfile, std::string out_file, 
                    double budget, double dwell_time, 
                    double w_max, double w_acc, double settle_time,
                    bool is_deepslow, bool is_save_result, int& num_tiles) {

    std::vector<std::vector<double>> costs;
    std::vector<double> probability;
    std::vector<int> ranks;
    std::vector<double> dwell_times;

    std::vector<double> source;
    int64_t nsrc_events, n_bkg_events;
    int zenithtile;
    int init_pos_idx = -1;

    auto [start_idx, end_idx, padding] = buildGraphOrienteering(tilefile, mapfile, costs, probability, ranks, dwell_times, 
                                                                dwell_time, w_max, w_acc, settle_time, is_deepslow, num_tiles, 
                                                                init_pos_idx, zenithtile, source, nsrc_events, n_bkg_events);
    get_timer().mark("mapping");

        
    // GCP
    std::cout << "*********running GCP*********" << std::endl;
    // start = std::chrono::high_resolution_clock::now();
    std::vector<int> mst_pathH1 = GCP(costs, probability, budget+padding, start_idx, end_idx);
    get_timer().mark("gcp1");
    
    double eff_budget = budget + padding - (get_timer().get_elapsed("mapping") + get_timer().get_elapsed("gcp1"))/1000;
    std::vector<int> mst_pathH2 = GCP(costs, probability, eff_budget, start_idx, end_idx);
    get_timer().mark("gcp2");

    return mst_pathH2;
}



std::vector<int> find_source(std::string tilefile, std::string mapfile, std::string out_file,
                             double dwell_time, double w_max, double w_acc, double settle_time,
                             bool is_deepslow, int source_tile) {
                    
    // auto map_start = std::chrono::high_resolution_clock::now();
    std::vector<std::vector<double>> costs;
    std::vector<double> probability;
    std::vector<int> ranks;
    std::vector<double> dwell_times;
    std::vector<double> source;
    int64_t nsrc_events, n_bkg_events;
    int zenithtile;
    int init_pos_idx = -1;
    int num_tiles = 0;

    auto [start_idx, end_idx, padding] = buildGraphOrienteering(
                                        tilefile, mapfile, costs, probability, ranks, dwell_times,
                                        dwell_time, w_max, w_acc, settle_time, is_deepslow, num_tiles,
                                        init_pos_idx, zenithtile, source, nsrc_events, n_bkg_events);
    // auto map_end = std::chrono::high_resolution_clock::now();
    // double map_time_sec = std::chrono::duration<double>(map_end - map_start).count();

    // std::cout << "total num_tiles: " << costs.size() << std::endl;
    get_timer().mark("mapping");
    double map_time_sec = get_timer().get_elapsed("mapping") / 1000.0;

    std::cout << "*********running GCP*********" << std::endl;
    int min_budget = 1, max_budget = 1;
    bool detected = false;
    // std::vector<int> mst_pathH2;

    // Exponential search
    while (!detected) {
        // std::cout << " max_budget: " << max_budget << " is_detected: " << detected << "\n";
        min_budget = max_budget;
        max_budget *= 2;

        std::vector<int> mst_pathH1 = GCP(costs, probability, max_budget + padding, start_idx, end_idx);

        // std::cout << "num_tiles: " << num_tiles << " mst_pathH1.size: " << (int)mst_pathH1.size() << "\n"; 
        detected = is_detected(mst_pathH1, ranks, source_tile);
        if ((int)mst_pathH1.size() == num_tiles) break;
    }

    // Binary search
    if (detected) {
        while (max_budget - min_budget > 1) {
            int budget = (min_budget + max_budget) / 2;
            // std::cout << "budget: " << budget << " is_detected: " << detected << "\n";

            std::vector<int> mst_pathH1 = GCP(costs, probability, budget + padding, start_idx, end_idx);

            if (is_detected(mst_pathH1, ranks, source_tile)) {
                max_budget = budget;
            } else {
                min_budget = budget;
            }
        }
    }

    // std::cout << "budget: " << max_budget << std::endl;
    // std::cout << "padding: " << padding << std::endl;
    // Final run with max_budget
    get_timer().start();
    std::vector<int> finalH1 = GCP(costs, probability, max_budget + padding, start_idx, end_idx);
    get_timer().mark("gcp");

    detected = is_detected(finalH1, ranks, source_tile);

    double runtime = map_time_sec + get_timer().get_elapsed("gcp") / 1000.0;
    // double runtime2 = map_time_sec + get_timer().get_elapsed("gcp2") / 1000.0;
    save_result(out_file, "GCP", mapfile, max_budget, w_max, costs, probability, ranks, finalH1,
                0, runtime, padding, num_tiles, zenithtile, source, nsrc_events, n_bkg_events,
                source_tile, detected);

    // std::cout << "tiles in the path:" << finalH1.size() << std::endl;

    return finalH1;
}


void verify_maps (std::string tilefile, std::string mapfile, std::string out_file, 
                    double budget, double dwell_time, 
                    double w_max, double w_acc, double settle_time,
                    bool is_deepslow, int source_tile) {
    
    std::vector<std::vector<double>> costs;
    std::vector<double> probability;
    std::vector<int> ranks;
    std::vector<double> dwell_times;

    std::vector<double> source;
    int64_t nsrc_events, n_bkg_events;
    int zenithtile;
    int init_pos_idx = -1;
    int num_tiles = 0;
        
    auto [start_idx, end_idx, padding] = buildGraphOrienteering(
                                                        tilefile, mapfile, costs, probability, ranks, dwell_times,
                                                        dwell_time, w_max, w_acc, settle_time, is_deepslow, num_tiles,
                                                        init_pos_idx, zenithtile, source, nsrc_events, n_bkg_events);

    get_timer().mark("mapping");
    double map_time_sec = get_timer().get_elapsed("mapping") / 1000.0;
    // std::cout << "map_time_sec " << map_time_sec << std::endl;

    if(budget < 0) {
        save_result(out_file, "GCP", mapfile, budget, w_max, costs, probability, ranks, {},
            0, 0, 0, num_tiles, zenithtile, source, nsrc_events, n_bkg_events,
            source_tile, false);
        
            return;
    }

    // GCP
    std::cout << "*********running GCP*********" << std::endl;
    //estimate planning time
    std::vector<int> mst_pathH1 = GCP(costs, probability, budget+padding, start_idx, end_idx);
    get_timer().mark("planning");
    double planning_time_sec = get_timer().get_elapsed("planning") / 1000.0;

    double effective_budget = budget - map_time_sec - planning_time_sec;

    if(effective_budget < 0) {
        save_result(out_file, "GCP", mapfile, budget, w_max, costs, probability, ranks, {},
            0, 0, 0, num_tiles, zenithtile, source, nsrc_events, n_bkg_events,
            source_tile, false);
        
            return;
    }
    // effective_budget = 34.637;
    // std::cout << "effective_budget:" << effective_budget; 
    // std::cout << "padding: " << padding << std::endl;
    std::vector<int> final_pathH1 = GCP(costs, probability, effective_budget + padding, start_idx, end_idx);
    // std::vector<int> finalH1 = GCP(costs, probability, effective_budget + padding, start_idx, end_idx);
    get_timer().mark("gcp");
    double runtime = get_timer().get_elapsed("gcp") / 1000.0;
    runtime += map_time_sec;

    bool detected = is_detected(final_pathH1, ranks, source_tile);
    save_result(out_file, "GCP", mapfile, effective_budget, w_max, costs, probability, ranks, final_pathH1,
                0, runtime, padding, num_tiles, zenithtile, source, nsrc_events, n_bkg_events,
                source_tile, detected);
}



int main(int argc, char** argv) {
    auto total_start = std::chrono::high_resolution_clock::now();
    get_timer().start();
    // default parameters
    std::string out_file = "../results/out.csv";
    // std::string tilefile = "../data/tilings/5.36x4.5_tiling.csv";
    std::string tilefile = "../data/tilings/2.5x2.5_tiling.csv";
    // std::string mapfile = "../data/ADAPT_maps_new/test/adapt_p0_a0_51_map.h5";
    // std::string mapfile = "/shared/training/longlow_maps/adapt_p60-00000000000001_a337-49999999999994_1_map.h5";
    std::string mapfile = "/shared/training/longlow_maps/adapt_p60-00000000000001_a337-49999999999994_357_map.h5";
    std::string runtime_file = "../results/time.csv";

    int source_tile = 1350;
    // int source_tile = 1613;
    double w_max = 10;
    double w_acc = 10;
    double dwell_time = 1;
    double settle_time = 0.0;
    bool is_deepslow = false;
    double budget = 0.0;

    if (argc > 2) {
        mapfile = std::string(argv[1]);
        tilefile = std::string(argv[2]);
    }
    if (argc > 7) {
        source_tile = std::stoi(argv[3]);
        w_max = std::stod(argv[4]);
        w_acc = std::stod(argv[5]);
        budget = std::stod(argv[6]);
        is_deepslow = std::stoi(argv[7]);
    }

    std::cout << "Input Parameters:\n";
    std::cout << "  file        = " << mapfile << "\n";
    std::cout << "  source_tile = " << source_tile << "\n";
    std::cout << "  slew_rate   = " << w_max << "\n";
    std::cout << "  dwell_time  = " << dwell_time << "\n\n";

    // find_source(tilefile, mapfile, out_file,
    //             dwell_time, w_max, w_acc, settle_time,
    //             is_deepslow, source_tile);

    verify_maps (tilefile, mapfile, out_file, budget, dwell_time, 
                    w_max, w_acc, settle_time,
                    is_deepslow, source_tile);

    // int min_budget = 1, max_budget = 1;
    // std::vector<int> path;
    // bool detected = false;
    // int num_tiles = 0;
    // bool is_save_result = false;

    // // Double search: find an upper bound where source is detected
    // while (!detected) {
    //     min_budget = max_budget;
    //     max_budget *= 2;
    //     get_timer().start();
    //     path = test_algorithms2(tilefile, mapfile, out_file, max_budget, dwell_time,
    //                             w_max, w_acc, settle_time, is_deepslow, is_save_result, num_tiles);
    //     detected = is_detected(path, source_tile);

    //     if ((int)path.size() == num_tiles) break;
    // }

    // // Binary search: narrow down to minimum budget that detects source
    // if (detected) {
    //     while (max_budget - min_budget > 1) {
    //         int budget = (min_budget + max_budget) / 2;
    //         get_timer().start();
    //         path = test_algorithms2(tilefile, mapfile, out_file, budget, dwell_time,
    //                                 w_max, w_acc, settle_time, is_deepslow, is_save_result, num_tiles);
    //         if (is_detected(path, source_tile)) {
    //             max_budget = budget;
    //         } else {
    //             min_budget = budget;
    //         }
    //     }
    // }

    // // Final run with saving enabled
    // is_save_result = true;
    // get_timer().start();
    // path = test_algorithms2(tilefile, mapfile, out_file, max_budget, dwell_time,
    //                         w_max, w_acc, settle_time, is_deepslow, is_save_result, num_tiles, source_tile);

    auto total_end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed_seconds = total_end - total_start;
    std::cout << "total time (wallclock): " << elapsed_seconds.count() << " seconds" << std::endl;


    // get_timer().mark("total");
    // get_timer().print();
    // get_timer().save_csv(runtime_file, std::filesystem::path(mapfile).filename().string(), budget, num_tiles);
    // get_memory_log().mark("end");
    // get_memory_log().print();
    // get_memory_log().save_csv("../results/memory.csv", std::filesystem::path(mapfile).filename().string(), budget, num_tiles);
    return 0;
}

