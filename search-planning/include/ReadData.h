#pragma once

#include <vector>
#include <string>
#include <limits>

//Read Tiling Data
void readTiles(const std::string& filename, 
             std::vector<int>& ranks, 
             std::vector<double>& ras, 
             std::vector<double>& decs, 
             std::vector<std::vector<int>>& member_pixels);



// //Read Probability Map
// void readHEALPixels(const std::string& filename, std::vector<int>& pixel_ids, 
//                 std::vector<double>& pixel_probs);     

// bool readHEALPixels(const std::string& filename,std::vector<int>& pixel_ids,
//                     std::vector<double>& pixel_probs,
//                     int pixel_count);

bool readHEALPixelsCSV(const std::string& filename,
                       std::vector<double>& pixel_probs,
                       int nside=64);

bool readHEALPixelsTXT(const std::string& filename,
                    std::vector<double>& pixel_probs,
                    int nside=64);

bool readHEALPixelsHDF5(const std::string& filename,
                        std::vector<double>& pixel_probs,
                        int nside=64,
                        const std::string& pix_id_dataset = "/pixel",
                        const std::string& prob_dataset = "/probability");

bool readHEALPixelsHDF5(const std::string& filename,
                        std::vector<double>& pixel_probs,
                        int nside,
                        std::vector<double>& source,
                        int64_t& n_src_events,
                        int64_t& n_bkg_events,
                        const std::string& pix_id_dataset = "/pixel",
                        const std::string& prob_dataset = "/probability");

bool readHEALPixels(const std::string& filename,
                    std::vector<double>& pixel_probs,
                    int nside);



void computeTileProbs(const std::vector<std::vector<int>>& member_pixels,
                    const std::vector<double>& pixel_probs,
                    std::vector<double>& tile_probs);        

int getTopTileIndices(std::vector<double>& tile_probs, 
                    std::vector<int>& ranks, 
                    std::vector<double>& ras, 
                    std::vector<double>& decs, 
                    std::vector<std::vector<int>>& member_pixels,
                    double coverage=0.99);

int getNonZeroTileIndices(std::vector<double>& tile_probs,
                      std::vector<int>& ranks,
                      std::vector<double>& ras,
                      std::vector<double>& decs,
                      std::vector<std::vector<int>>& member_pixels);

void read_data_from_file(const std::string& filename, std::vector<double>& probability, 
                        std::vector<int>& ranks, std::vector<double>& ra, std::vector<double>& dec);