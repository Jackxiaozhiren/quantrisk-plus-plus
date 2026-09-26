// Reference-value dumper used by the Python/C++ consistency test
// (tests/python/test_cpp_python_consistency.py).
//
// It prints the *C++* results for a fixed seed and a fixed parameter grid as
// JSON with 17 significant digits, so a Python comparison against these
// numbers proves the pybind11 boundary transports values exactly rather than
// approximately. The pure-Python layer never recomputes these formulas, so any
// mismatch is a binding or packaging defect, not a modelling difference.

#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/version.hpp"
#include "quantrisk/math/normal.hpp"

namespace {

std::string to_json(const double value) {
    std::ostringstream os;
    os << std::setprecision(17);
    if (std::isfinite(value)) {
        os << value;
    } else {
        os << "null";
    }
    return os.str();
}

template <typename T> std::string json_array(const std::vector<T> &values) {
    std::ostringstream os;
    os << std::setprecision(17) << "[";
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i > 0) {
            os << ", ";
        }
        os << to_json(static_cast<double>(values[i]));
    }
    os << "]";
    return os.str();
}

} // namespace

int main() {
    using quantrisk::Rng;
    using quantrisk::stats::mean;
    using quantrisk::stats::quantile;
    using quantrisk::stats::sample_variance;

    constexpr quantrisk::Seed kSeed = 42;
    constexpr std::size_t kNormalCount = 256;

    std::vector<double> normals;
    {
        Rng rng(kSeed);
        normals = rng.standard_normal_vector(kNormalCount);
    }

    std::vector<double> uniform_01;
    {
        Rng rng(kSeed);
        for (std::size_t i = 0; i < 64; ++i) {
            uniform_01.push_back(rng.uniform01());
        }
    }

    std::vector<double> indices;
    {
        Rng rng(kSeed);
        for (std::size_t i = 0; i < 2000; ++i) {
            indices.push_back(static_cast<double>(rng.uniform_index(97)));
        }
    }

    std::vector<double> xs;
    for (int i = -40; i <= 40; ++i) {
        xs.push_back(static_cast<double>(i) / 4.0);
    }
    std::vector<double> cdfs;
    std::vector<double> pdfs;
    for (const double x : xs) {
        cdfs.push_back(quantrisk::normal_cdf(x));
        pdfs.push_back(quantrisk::normal_pdf(x));
    }

    std::vector<double> probabilities;
    for (int i = 1; i <= 999; ++i) {
        probabilities.push_back(static_cast<double>(i) / 1000.0);
    }
    std::vector<double> ppfs;
    for (const double p : probabilities) {
        ppfs.push_back(quantrisk::inverse_normal_cdf(p));
    }

    const std::vector<double> sample = {2, 4, 4, 4, 5, 5, 7, 9};
    const double sample_mean = mean(sample);
    const double sample_var = sample_variance(sample);
    std::vector<double> quantiles;
    for (const double p : {0.0, 0.1, 0.25, 0.5, 0.6, 0.75, 0.9, 1.0}) {
        quantiles.push_back(quantile(sample, p));
    }

    std::cout << "{\n"
              << "  \"version\": \"" << quantrisk::version() << "\",\n"
              << "  \"seed\": " << kSeed << ",\n"
              << "  \"normals\": " << json_array(normals) << ",\n"
              << "  \"uniform01\": " << json_array(uniform_01) << ",\n"
              << "  \"uniform_index_97\": " << json_array(indices) << ",\n"
              << "  \"xs\": " << json_array(xs) << ",\n"
              << "  \"normal_cdf\": " << json_array(cdfs) << ",\n"
              << "  \"normal_pdf\": " << json_array(pdfs) << ",\n"
              << "  \"probabilities\": " << json_array(probabilities) << ",\n"
              << "  \"inverse_normal_cdf\": " << json_array(ppfs) << ",\n"
              << "  \"sample\": " << json_array(sample) << ",\n"
              << "  \"sample_mean\": " << to_json(sample_mean) << ",\n"
              << "  \"sample_variance\": " << to_json(sample_var) << ",\n"
              << "  \"sample_quantiles\": " << json_array(quantiles) << "\n"
              << "}\n";
    return 0;
}
