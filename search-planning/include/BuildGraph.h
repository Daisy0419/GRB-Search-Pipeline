#pragma once

#include <vector>
#include <string>
#include <limits>


std::tuple<int, int, double> buildGraphOrienteering(const std::string& filename, 
                std::vector<std::vector<double>>& costs, 
               std::vector<double>& probability, std::vector<int>& ranks, 
               std::vector<double>& dwell_times, double dwell_zenith,
               double w_max, double w_acc, double settle_time, 
               bool is_SlowDeep = false, int init_pos=-1) ;

std::tuple<int, int, double> buildGraphOrienteering(const std::string& tilefile, 
                const std::string& pro_map_file,
                std::vector<std::vector<double>>& costs, 
               std::vector<double>& probability, std::vector<int>& ranks, 
               std::vector<double>& dwell_times, double dwell_zenith,
               double w_max, double w_acc, double settle_time, 
               bool is_SlowDeep, int& num_tiles, int init_pos=-1);


std::tuple<int, int, double> buildGraphOrienteering(const std::string& tilefile, 
                const std::string& pro_map_file,
                std::vector<std::vector<double>>& costs, 
                std::vector<double>& probability, std::vector<int>& ranks, 
                std::vector<double>& dwell_times, double dwell_zenith,
                double w_max, double w_acc, double settle_time, 
                bool is_SlowDeep, int& num_tiles, int init_pos,
                int& zenithtile, std::vector<double>& source,
                int64_t& nsrc_events, int64_t& nbkg_events);