#include <cmath>
#include <iostream>
#include <vector>

// Returns the flux in eV the 645-675 nm band given Band function parameters
// Assumes amplitude A is in ph/cm^2/s/keV
float airis_flux_from_band(float A, float E_peak, float alpha, float beta) {
    constexpr float lower_wavelength = 645.0; // nm
    constexpr float upper_wavelength = 675.0; // nm
    constexpr float hc = 1239.84193; // eV*nm
    constexpr float e_lower = hc / upper_wavelength / 1000; // keV
    constexpr float e_upper = hc / lower_wavelength / 1000; // keV
    constexpr int num_steps = 100;
    constexpr float energy_step = (e_upper - e_lower) / num_steps;

    float total_flux = 0.0;
    for (float e = e_lower + energy_step / 2;  e < e_upper; e += energy_step)
    {
        //From https://iopscience.iop.org/article/10.3847/1538-4357/abf24d/pdf Eqn. 3
        // float band_value = A *
        //     std::pow(e / 100, beta) *
        //     std::exp(beta - alpha) *
        //     std::pow((alpha - beta) * E_peak / (100 * (2 + alpha)), alpha - beta);

        //From https://articles.adsabs.harvard.edu/pdf/1993ApJ...413..281B Eqn. 1
        float E_0 = E_peak / (2 + alpha);
        float band_value = A *
            std::pow(e / 100, alpha) * std::exp(-e / E_0);

        float photon_flux = band_value * energy_step;
        float energy_flux = photon_flux * e * 1000; // convert keV to eV
        total_flux += energy_flux;
    }
    
    // std::cout << "Total flux in band: " << total_flux << " eV/cm^2/s\n";
    return total_flux;

}

// Apply atmospheric attenuation based on polar angle theta in degrees
float airis_attenuate_flux(float flux, float theta, float sig_attenuation=1.0) {
    constexpr float altitude = 40000.0; // in meters
    constexpr float scale_height = 8435.0; // in meters
    float relative_pressure = std::exp(-altitude / scale_height);
    float air_mass = relative_pressure / (
                     std::cos(theta * M_PI / 180.0) +
                     0.50572 * std::pow(96.07995 - theta, -1.6364) );
    float attenuation_factor = std::exp(-0.04558 * air_mass);
    float attenuated_flux = flux * attenuation_factor * sig_attenuation;
    
    // std::cout << "Total attenuated flux in band: " << attenuated_flux << " eV/cm^2/s\n";

    return attenuated_flux;
}

// Convert flux in eV/cm^2/s to magnitude
float airis_flux_to_magnitude(float flux) {
    constexpr float bandpass_width = 300.0; // in Angstroms
    constexpr float zero_point_magnitude = 1198.36974; // in eV/cm^2/s/Angstrom
    constexpr float zero_point_flux = zero_point_magnitude * bandpass_width; // in eV/cm^2/s
    float magnitude = -2.5 * std::log10(flux / zero_point_flux);
    // std::cout << "Computed magnitude: " << magnitude << "\n";
    return magnitude;
}

float dwell_times_airis(float theta, float flux, int snr, float sig_attenuation) {
    // float flux = airis_flux_from_band(A, E_peak, alpha, beta);
    float attenuated_flux = airis_attenuate_flux(flux, theta, sig_attenuation);
    float magnitude = airis_flux_to_magnitude(attenuated_flux);

    return std::pow(
        snr / 897603.0 *
        std::pow(10.0, 0.4 * magnitude * 1.06596),
        1.60636
    );
}

// float dwell_times_airis(std::string grb, float sig_attenuation, float theta, float snr) {
//     float A, E_peak, alpha, beta;
//     if (grb == "bn100612726") {
//         A = 0.05638276; E_peak = 113.3885; alpha = -0.7350030; beta = -2.491069;
//     } else if (grb == "bn161004964") {
//         A = 0.04650384; E_peak = 135.5809; alpha = -0.8107229; beta = -2.392184;
//     } else if (grb == "bn081207680") {
//         A = 0.009403173; E_peak = 420.9654; alpha = -0.5878265; beta = -2.095031;
//     } else if (grb == "bn140329295") {
//         // A = 0.112743; E_peak = 228.8074; alpha = -0.8129236; beta = -2.249880;
//         A = 0.4477047; E_peak = 327.2210; alpha = -0.6919752; beta = -2.345322;
//     } else {
//         std::cout << "Error: Unknown GRB identifier " << grb << "\n";
//         return 0;
//     }
//     float dwell_time = dwell_times_airis(A, E_peak, alpha, beta, sig_attenuation, theta, snr);
//     // std::cout << "Dwell time for " << grb << ": " << dwell_time << " seconds\n";
//     return dwell_time;
// }

// void test() {
//     // std::vector<std::string> GRBs{"bn100612726", "bn161004964", "bn081207680", "bn140329295"};
//     std::vector<double> flux{0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 3.0, 5.0, 10};
//     std::vector<int> snrs{2, 3, 4, 5, 6};
//     // for(auto GRB : GRBs) {
//     // std::cout << GRB << ":\n";
//         for(auto snr : snrs) {
//             std::cout << "snr: " << snr << ":\n";
//             for(auto f : flux) {
//                 double dwell_time = dwell_times_airis(0.0, f, snr);
//                 // std::cout << "flush_ratio: " << flush_ratio << " " << "Dwelltime: " << dwell_time << "\n";
//                 std::cout << dwell_time << "\t";

//             }
//             std::cout << "\n";
//         }
//     // }
// }

// int main() {
//     // dwell_times_airis("bn100612726", 0.2, 0.0, 3.0);
//     // dwell_times_airis("bn161004964", 0.3, 0.0, 3.0);
//     // dwell_times_airis("bn081207680", 0.4, 0.0, 3.0);
//     // dwell_times_airis("bn140329295", 0.9, 0.0, 3.0);
//     // dwell_times_airis("bn100612726", 1.0, 0.0, 3.0);
//     // dwell_times_airis("bn161004964", 1.0, 0.0, 3.0);
//     // dwell_times_airis("bn081207680", 1.0, 0.0, 3.0);
//     // dwell_times_airis("bn140329295", 1.0, 0.0, 3.0);
//     test();
//     return 0;
// }


