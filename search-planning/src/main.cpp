#include "ReadData.h"
#include "GCP.h"
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


bool is_detected(const std::vector<int>& path, const std::vector<int>& ranks, int source) {
    for(int p : path) {
        if(source == ranks[p]) return true;
    }
    return false;
}



std::vector<int> find_source(std::string tilefile, std::string mapfile, std::string out_file,
                             double dwell_time, double w_max, double w_acc, double settle_time,
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

    std::cout << "*********running GCP*********" << std::endl;
    int min_budget = 1, max_budget = 1;
    bool detected = false;

    // Exponential search
    while (!detected) {
        min_budget = max_budget;
        max_budget *= 2;

        std::vector<int> mst_pathH1 = GCP(costs, probability, max_budget + padding, start_idx, end_idx);

        detected = is_detected(mst_pathH1, ranks, source_tile);
        if ((int)mst_pathH1.size() == num_tiles) break;
    }

    // Binary search
    if (detected) {
        while (max_budget - min_budget > 1) {
            int budget = (min_budget + max_budget) / 2;

            std::vector<int> mst_pathH1 = GCP(costs, probability, budget + padding, start_idx, end_idx);

            if (is_detected(mst_pathH1, ranks, source_tile)) {
                max_budget = budget;
            } else {
                min_budget = budget;
            }
        }
    }

    get_timer().start();
    std::vector<int> finalH1 = GCP(costs, probability, max_budget + padding, start_idx, end_idx);
    get_timer().mark("gcp");

    detected = is_detected(finalH1, ranks, source_tile);

    double runtime = map_time_sec + get_timer().get_elapsed("gcp") / 1000.0;
    save_result(out_file, "GCP", mapfile, max_budget, w_max, costs, probability, ranks, finalH1,
                0, runtime, padding, num_tiles, zenithtile, source, nsrc_events, n_bkg_events,
                source_tile, detected);


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



int main_train(int argc, char** argv) {
    auto total_start = std::chrono::high_resolution_clock::now();
    get_timer().start();
    // default parameters
    std::string out_file = "../results4/out.csv";
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

    find_source(tilefile, mapfile, out_file,
                dwell_time, w_max, w_acc, settle_time,
                is_deepslow, source_tile);


    auto total_end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed_seconds = total_end - total_start;
    std::cout << "total time (wallclock): " << elapsed_seconds.count() << " seconds" << std::endl;
    return 0;
}


int main_verify(int argc, char** argv) {
    auto total_start = std::chrono::high_resolution_clock::now();
    get_timer().start();
    // default parameters
    std::string out_file = "../results4/out.csv";
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


    verify_maps (tilefile, mapfile, out_file, budget, dwell_time, 
                    w_max, w_acc, settle_time,
                    is_deepslow, source_tile);


    auto total_end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed_seconds = total_end - total_start;
    std::cout << "total time (wallclock): " << elapsed_seconds.count() << " seconds" << std::endl;
    return 0;
}

#if defined(BUILD_SP_TRAIN)

int main(int argc, char** argv) {
    return main_train(argc, argv);
}

#elif defined(BUILD_SP_VERIFY)

int main(int argc, char** argv) {
    return main_verify(argc, argv);
}

#else

#error "Either BUILD_SP_TRAIN or BUILD_SP_VERIFY must be defined."

#endif


