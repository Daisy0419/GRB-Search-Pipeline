#include "ReadData.h"
#include "BuildGraph.h"

#include <iostream>
#include <fstream>
#include <sstream>
#include <cmath>
#include <iomanip>
#include <random>
#include <algorithm>
#include <unordered_set>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>

#define DEG_TO_RAD (M_PI / 180.0)
#define RAD_TO_DEG (180.0 / M_PI)

double angularDistance(double ra1, double dec1, double ra2, double dec2) {
    double ra1_rad = ra1 * DEG_TO_RAD;
    double dec1_rad = dec1 * DEG_TO_RAD;
    double ra2_rad = ra2 * DEG_TO_RAD;
    double dec2_rad = dec2 * DEG_TO_RAD;

    double delta_ra = fmod(ra1_rad - ra2_rad + M_PI, 2 * M_PI) - M_PI;

    double cos_angle = sin(dec1_rad) * sin(dec2_rad) +
                       cos(dec1_rad) * cos(dec2_rad) * cos(delta_ra);

    // Clamp to [-1, 1]
    cos_angle = std::min(1.0, std::max(-1.0, cos_angle));

    double angle_rad = acos(cos_angle);

    return angle_rad * RAD_TO_DEG;
}


// Normalize angle to [0, 360)
double norm_deg(double x_deg) {
    double y = std::fmod(x_deg, 360.0);
    if (y < 0.0) y += 360.0;
    return y;
}

// Signed delta between two angles (deg) along the track that does not cross 0/360 directly, in (-360, 360)
double non_crossing_delta_deg(double a_deg, double b_deg) {
    return norm_deg(a_deg) - norm_deg(b_deg);
}

// Inputs in degrees; RA can be any real, Dec in [-90, 90]
double two_axes_distance_deg(double ra1_deg, double dec1_deg,
                             double ra2_deg, double dec2_deg) {
    const double dRA = std::abs(non_crossing_delta_deg(ra1_deg, ra2_deg));
    const double dDec = std::abs(dec1_deg - dec2_deg);
    // std::cout << std::max(dRA, dDec) << " ";
    return std::max(dRA, dDec);

}

double compute_slew_time(double theta, double theta_min, double w_max, double w_acc) {
    constexpr double EPS = 1e-15;

    if (theta < 0.0) {
        theta = -theta;
    }

    // if (theta > 180.0) {
    //     theta = 180 - theta;
    // }

    if (theta == 0.0) return 0.0;
    if (w_acc <= 0.0 || w_max <= 0.0) throw std::invalid_argument("alpha must be > 0");

    // Trapezoid: accelerate to w_max, cruise, decelerate.
    if (theta  >= theta_min) {
        const double t_acc    = 2 * w_max / w_acc;
        const double t_cruise = (theta - theta_min) / w_max;
        return t_acc + t_cruise;
    } else { // Triangle
        return 2.0 * std::sqrt(theta / w_acc);
    }
}



// Computes air mass using the Kasten & Young model
double computeAirMass(double zenithAngleDegrees) {
    // if (zenithAngleDegrees >= 90.0) {
    //     std::cerr << "Zenith angle must be less than 90 degrees.";
    // }
    double theta = DEG_TO_RAD * zenithAngleDegrees;
    double numerator = 1.0;
    double denominator = std::cos(theta) + 0.50572 * std::pow(96.07995 - zenithAngleDegrees, -1.6364);
    return numerator / denominator;
}

// Computes the light attenuation scaling factor for a given air mass
double computeScalingFactor(double airMass) {
    return 1.1129 * std::exp(-0.107 * airMass);
}

// Computes the scaled dwell time needed to achieve same SNR as reference dwell time t_ref at s=1
double computeDwellTime(double t_ref, double scalingFactor) {
    return t_ref / (scalingFactor * scalingFactor);
}


// overload 
//Orienteering Graph incorporate accerlation, decerlation, settle time
// cost[i][j] = anguler_distance[i][j]/slew_rate + 0.5*dwelltime[i] + 0.5*dwelltime[j] + settle_time
void compute_costs_orienteering(const std::vector<double>& ra, const std::vector<double>& dec, 
                        const std::vector<double>& dwell_times,
                        std::vector<std::vector<double>>& costs, 
                        double w_max, double w_acc, double settle_time, 
                        int end_pos, double& _padding, bool is_SlowDeep) {

    size_t n = ra.size();
    if(n != end_pos) {
        std::cerr << "Wrong sizing in compute_costs_orienteering func" << std::endl;
    }

    double theta_min = w_max * w_max / w_acc;

    costs.assign(n + 1, std::vector<double>(n + 1, 0.0)); //to include end_pos t'

    _padding = 0.0;
    // double slew_min = 10000;
    // double slew_max = 0.0;
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = i+1; j < n; ++j) {
            if (i != j) {
                double theta;
                if(is_SlowDeep)
                    theta = two_axes_distance_deg(ra[i], dec[i], ra[j], dec[j]);
                else
                    theta = angularDistance(ra[i], dec[i], ra[j], dec[j]);
                double slew_time = compute_slew_time(theta, theta_min, w_max, w_acc);
                // std::cout << slew_time << " ";
                // slew_min = std::min(slew_min, slew_time);
                // slew_max = std::max(slew_max, slew_time);
                costs[i][j] = slew_time + 0.5 * dwell_times[i] + 0.5 * dwell_times[j] + settle_time;
                costs[j][i] = costs[i][j];
                // std::cout << "theta"<<theta<<":" << costs[j][i] << "\t";
                if(slew_time + settle_time > _padding) _padding = slew_time + settle_time;
            }
        }
        // costs[i][i] = std::numeric_limits<double>::infinity(); 
        // std::cout << "slew_time: " << "min-" << slew_min << "  max-" << slew_max;
        // std::cout << "\n";
        costs[i][i] = dwell_times[i];
    }
    // std::cout << "slew_time: " << "min-" << slew_min << "  max-" << slew_max;
    // std::cout << "\n";
    // std::cout << "\n";
    _padding = ceil(_padding); //smallest big enough padding
    for (size_t i = 0; i < n; ++i) {
            costs[i][end_pos] = 0.5 * dwell_times[i] + _padding;
            costs[end_pos][i] = costs[i][end_pos];
    }

}

// overload, incorporate accerlation decerlation and settle time
// build graph for s-t orienteering
std::tuple<int, int, double> buildGraphOrienteering(const std::string& filename, 
                std::vector<std::vector<double>>& costs, 
               std::vector<double>& probability, std::vector<int>& ranks, 
               std::vector<double>& dwell_times, double dwell_zenith,
               double w_max, double w_acc, double settle_time, 
               bool is_SlowDeep, int init_pos) {

    std::vector<double> ra, dec;
    // get probability, ranks, ra, dec
    read_data_from_file(filename, probability, ranks, ra, dec);
    double init_ra, init_dec;
    int n = (int)ra.size();
    if (init_pos >= 0 && init_pos < n) {
        init_ra = ra[init_pos], init_dec = dec[init_pos];
    } 
    else if (init_pos < 0) {
        unsigned int fixed_seed = 419;
        std::mt19937 generator(fixed_seed);
        std::uniform_int_distribution<int> distribution(0, n-1);
        init_pos = distribution(generator);
        init_ra = ra[init_pos], init_dec = dec[init_pos];
    }
    else {
        throw std::invalid_argument("Invalid init position.");
    }
    std::cout << "init_pos: " << init_pos << std::endl;
    int end_rank = probability.size();

    dwell_times.resize(probability.size());
    double dwelltime_ref = dwell_zenith;
    double ra_zenith = ra[0], dec_zenith = dec[0];

    std::vector<size_t> valid_indices;
    for (size_t i = 0; i < probability.size(); ++i) {
        double zenithAngle = angularDistance(ra[i], dec[i], ra_zenith, dec_zenith);
        if (zenithAngle >= 90.0) {
            continue; // Skip this index
        }
        double airMass = computeAirMass(zenithAngle);
        double scalingFactor = computeScalingFactor(airMass);
        dwell_times[i] = computeDwellTime(dwelltime_ref, scalingFactor);
        // dwell_times[i] = 1.0;
        valid_indices.push_back(i);
    }

    // Filter all vectors based on valid_indices
    std::vector<double> filtered_ra, filtered_dec, filtered_probability, filtered_dwell_times;
    std::vector<int> filtered_ranks;
    for (size_t idx : valid_indices) {
        filtered_ra.push_back(ra[idx]);
        filtered_dec.push_back(dec[idx]);
        filtered_probability.push_back(probability[idx]);
        filtered_ranks.push_back(ranks[idx]);
        filtered_dwell_times.push_back(dwell_times[idx]);
    }
    ra = std::move(filtered_ra);
    dec = std::move(filtered_dec);
    probability = std::move(filtered_probability);
    ranks = std::move(filtered_ranks);
    dwell_times = std::move(filtered_dwell_times);

    int start_pos = probability.size();
    ra.push_back(init_ra);
    dec.push_back(init_dec);
    probability.push_back(0.0);
    ranks.push_back(init_pos);
    dwell_times.push_back(0.0);

    // Push as end node
    int end_pos = probability.size();
    probability.push_back(0.0);
    ranks.push_back(-1);
    dwell_times.push_back(0.0);

    double padding_value;
    compute_costs_orienteering(ra, dec, dwell_times, costs, w_max, w_acc, settle_time, end_pos, padding_value, is_SlowDeep);

    return {start_pos, end_pos, padding_value};
}



// overload, incorporate accerlation decerlation and settle time
// build graph for s-t orienteering
std::tuple<int, int, double> buildGraphOrienteering(const std::string& tilefile, 
                const std::string& pro_map_file,
                std::vector<std::vector<double>>& costs, 
               std::vector<double>& probability, std::vector<int>& ranks, 
               std::vector<double>& dwell_times, double dwell_zenith,
               double w_max, double w_acc, double settle_time, 
               bool is_SlowDeep, int& num_tiles, int init_pos) {

    std::vector<double> ra, dec;
    std::vector<std::vector<int>> member_pixels;
    readTiles(tilefile, ranks, ra, dec, member_pixels);

    // std::vector<int> pixel_ids;
    std::vector<double> pixel_probs;
    // int pixel_count = 12 * 64 * 64;
    // readHEALPixelsTXT(pro_map_file, pixel_probs);
    // readHEALPixelsHDF5(pro_map_file, pixel_probs, 64);
    readHEALPixels(pro_map_file, pixel_probs, 64);


    // std::vector<double> probability;
    computeTileProbs(member_pixels, pixel_probs, probability);

    // double init_ra, init_dec;
    // int n = (int)ra.size();
    // if (init_pos >= 0 && init_pos < n) {
    //     init_ra = ra[init_pos], init_dec = dec[init_pos];
    // } 
    // else if (init_pos < 0) {
    //     unsigned int fixed_seed = 419;
    //     std::mt19937 generator(fixed_seed);
    //     std::uniform_int_distribution<int> distribution(0, n-1);
    //     init_pos = distribution(generator);
    //     init_ra = ra[init_pos], init_dec = dec[init_pos];
    // }
    // else {
    //     throw std::invalid_argument("Invalid init position.");
    // }
    // std::cout << "init_pos: " << init_pos << std::endl;
    
    double coverage = 1.0;
    // int num_tile = getTopTileIndices(probability, ranks, ra, dec, member_pixels, coverage);
    int num_tile = getNonZeroTileIndices(probability, ranks, ra, dec, member_pixels);
    std::cout << "num tiles after trim: " << num_tile << "\n";

    double init_ra, init_dec;
    int n = (int)ra.size();
    if (init_pos >= 0 && init_pos < n) {
        init_ra = ra[init_pos], init_dec = dec[init_pos];
    } 
    else if (init_pos < 0) {
        unsigned int fixed_seed = 419;
        std::mt19937 generator(fixed_seed);
        std::uniform_int_distribution<int> distribution(0, n-1);
        init_pos = distribution(generator);
        init_ra = ra[init_pos], init_dec = dec[init_pos];
    }
    else {
        throw std::invalid_argument("Invalid init position.");
    }
    std::cout << "init_pos: " << ranks[init_pos] << std::endl;

    dwell_times.resize(probability.size());
    double dwelltime_ref = dwell_zenith;
    double ra_zenith = ra[0], dec_zenith = dec[0];

    std::vector<size_t> valid_indices;
    for (size_t i = 0; i < probability.size(); ++i) {
        double zenithAngle = angularDistance(ra[i], dec[i], ra_zenith, dec_zenith);
        if (zenithAngle >= 89.9) {
            zenithAngle = 89.9;
        }
        double airMass = computeAirMass(zenithAngle);
        double scalingFactor = computeScalingFactor(airMass);
        dwell_times[i] = computeDwellTime(dwelltime_ref, scalingFactor);
        // zenithAngle = std::min(zenithAngle, 96.0);
        // dwell_times[i] = dwell_times_airis(zenithAngle);
        // std::cout << "tile " << ranks[i] << ":" << dwell_times[i] << "\t";
        valid_indices.push_back(i);
    }
    std::cout << "\n";

    // // Filter all vectors based on valid_indices
    // std::vector<double> filtered_ra, filtered_dec, filtered_probability, filtered_dwell_times;
    // std::vector<int> filtered_ranks;
    // for (size_t idx : valid_indices) {
    //     filtered_ra.push_back(ra[idx]);
    //     filtered_dec.push_back(dec[idx]);
    //     filtered_probability.push_back(probability[idx]);
    //     filtered_ranks.push_back(ranks[idx]);
    //     filtered_dwell_times.push_back(dwell_times[idx]);
    // }
    // ra = std::move(filtered_ra);
    // dec = std::move(filtered_dec);
    // probability = std::move(filtered_probability);
    // ranks = std::move(filtered_ranks);
    // dwell_times = std::move(filtered_dwell_times);
    // std::cout << "num tiles after filter: " << ra.size() << "\n";
    num_tiles = ra.size();

    int start_pos = probability.size();
    ra.push_back(init_ra);
    dec.push_back(init_dec);
    probability.push_back(0.0);
    ranks.push_back(ranks[init_pos]);
    dwell_times.push_back(0.0);

    // Push as end node
    int end_pos = probability.size();
    probability.push_back(0.0);
    ranks.push_back(-1);
    dwell_times.push_back(0.0);

    double padding_value;
    compute_costs_orienteering(ra, dec, dwell_times, costs, w_max, w_acc, settle_time, end_pos, padding_value, is_SlowDeep);
    // for(int i = 0; i < costs.size(); ++i) {
    //     for(int j = 0; j < costs.size(); ++j) {
    //         std::cout << costs[i][j] << "\t";
    //     }
    //     std::cout << "\n";
    // }
    // std::cout << "1:ra " << ra[1] << " dec " << dec[1] << " rank " << ranks[1];
    // std::cout << "6:ra " << ra[6] << " dec " << dec[6] << " rank " << ranks[6];
    // std::cout << "25:ra " << ra[25] << " dec " << dec[25] << " rank " << ranks[25];

    return {start_pos, end_pos, padding_value};
}


// overload, incorporate accerlation decerlation and settle time
// build graph for s-t orienteering
std::tuple<int, int, double> buildGraphOrienteering(const std::string& tilefile, 
                const std::string& pro_map_file,
                std::vector<std::vector<double>>& costs, 
                std::vector<double>& probability, std::vector<int>& ranks, 
                std::vector<double>& dwell_times, double dwell_zenith,
                double w_max, double w_acc, double settle_time, 
                bool is_SlowDeep, int& num_tiles, int init_pos,
                int& zenithtile, std::vector<double>& source,
                int64_t& nsrc_events, int64_t& nbkg_events) {

    std::vector<double> ra, dec;
    std::vector<std::vector<int>> member_pixels;
    readTiles(tilefile, ranks, ra, dec, member_pixels);

    // std::vector<int> pixel_ids;
    std::vector<double> pixel_probs;
    // int pixel_count = 12 * 64 * 64;
    // readHEALPixelsTXT(pro_map_file, pixel_probs);
    readHEALPixelsHDF5(pro_map_file, pixel_probs, 64, source, nsrc_events, nbkg_events);
    // readHEALPixels(pro_map_file, pixel_probs, 64);


    // std::vector<double> probability;
    computeTileProbs(member_pixels, pixel_probs, probability);

    
    double coverage = 1.0;
    // int num_tile = getTopTileIndices(probability, ranks, ra, dec, member_pixels, coverage);
    int num_tile = getNonZeroTileIndices(probability, ranks, ra, dec, member_pixels);
    std::cout << "num tiles after trim: " << num_tile << "\n";

    double init_ra, init_dec;
    int n = (int)ra.size();
    if (init_pos >= 0 && init_pos < n) {
        init_ra = ra[init_pos], init_dec = dec[init_pos];
    } 
    else if (init_pos < 0) {
        unsigned int fixed_seed = 419;
        std::mt19937 generator(fixed_seed);
        std::uniform_int_distribution<int> distribution(0, n-1);
        init_pos = distribution(generator);
        init_ra = ra[init_pos], init_dec = dec[init_pos];
    }
    else {
        throw std::invalid_argument("Invalid init position.");
    }
    std::cout << "init_pos: " << ranks[init_pos] << std::endl;

    dwell_times.resize(probability.size());
    double dwelltime_ref = dwell_zenith;
    double ra_zenith = ra[0], dec_zenith = dec[0];
    zenithtile = ranks[0];

    std::vector<size_t> valid_indices;
    // double dwell_min = 10000, dwell_max = 0.0;
    for (size_t i = 0; i < probability.size(); ++i) {
        double zenithAngle = angularDistance(ra[i], dec[i], ra_zenith, dec_zenith);
        if (zenithAngle >= 89.9) {
            zenithAngle = 89.9;
        }
        double airMass = computeAirMass(zenithAngle);
        double scalingFactor = computeScalingFactor(airMass);
        dwell_times[i] = computeDwellTime(dwelltime_ref, scalingFactor);
        // zenithAngle = std::min(zenithAngle, 96.0);
        // dwell_times[i] = dwell_times_airis(zenithAngle);
        // std::cout << "tile " << ranks[i] << ":" << dwell_times[i] << "\t";
        // dwell_min = std::min(dwell_times[i], dwell_min);
        // dwell_max = std::max(dwell_times[i], dwell_max);
        valid_indices.push_back(i);
    }
    // std::cout << "dwell_min: " << dwell_min << ", dwell_max: " << dwell_max << "\t";
    // std::cout << "\n";

    // // Filter all vectors based on valid_indices
    // std::vector<double> filtered_ra, filtered_dec, filtered_probability, filtered_dwell_times;
    // std::vector<int> filtered_ranks;
    // for (size_t idx : valid_indices) {
    //     filtered_ra.push_back(ra[idx]);
    //     filtered_dec.push_back(dec[idx]);
    //     filtered_probability.push_back(probability[idx]);
    //     filtered_ranks.push_back(ranks[idx]);
    //     filtered_dwell_times.push_back(dwell_times[idx]);
    // }
    // ra = std::move(filtered_ra);
    // dec = std::move(filtered_dec);
    // probability = std::move(filtered_probability);
    // ranks = std::move(filtered_ranks);
    // dwell_times = std::move(filtered_dwell_times);
    // std::cout << "num tiles after filter: " << ra.size() << "\n";

    int start_pos = probability.size();
    ra.push_back(init_ra);
    dec.push_back(init_dec);
    probability.push_back(0.0);
    ranks.push_back(ranks[init_pos]);
    dwell_times.push_back(0.0);

    // Push as end node
    int end_pos = probability.size();
    probability.push_back(0.0);
    ranks.push_back(-1);
    dwell_times.push_back(0.0);

    num_tiles = probability.size();

    double padding_value;
    compute_costs_orienteering(ra, dec, dwell_times, costs, w_max, w_acc, settle_time, end_pos, padding_value, is_SlowDeep);

    return {start_pos, end_pos, padding_value};
}