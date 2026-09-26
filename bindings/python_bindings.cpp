// Thin pybind11 surface over the C++20 numerical core.
//
// Policy (docs/architecture.md §2): this file exposes frozen C++ APIs and
// converts containers. It must never reimplement a formula, add validation
// logic, or hold state that the C++ core does not already own.

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <string>
#include <vector>

#include "quantrisk/core/rng.hpp"
#include "quantrisk/core/statistics.hpp"
#include "quantrisk/core/validation.hpp"
#include "quantrisk/core/version.hpp"
#include "quantrisk/math/normal.hpp"

namespace py = pybind11;

namespace {

py::dict build_metadata_dict() {
    const quantrisk::BuildMetadata meta = quantrisk::build_metadata();
    py::dict out;
    out["version"] = meta.version;
    out["git_commit"] = meta.git_commit;
    out["compiler"] = meta.compiler;
    out["arch"] = meta.arch;
    out["os"] = meta.os;
    out["build_type"] = meta.build_type;
    out["cxx_standard"] = meta.cxx_standard;
    out["cxx_flags"] = meta.cxx_flags;
    return out;
}

} // namespace

PYBIND11_MODULE(_quantrisk, module) {
    module.doc() = "C++20 numerical core behind the quantrisk Python package.";

    py::register_exception<quantrisk::ValidationError>(module, "ValidationError", PyExc_ValueError);

    module.def("version", &quantrisk::version, "Library version string of the compiled C++ core.");
    module.def("build_metadata", &build_metadata_dict,
               "Compiler / commit / architecture metadata of this build.");

    // --- math: standard normal distribution -------------------------------
    module.def("normal_cdf", &quantrisk::normal_cdf, py::arg("x"), "Standard normal CDF N(x).");
    module.def("normal_pdf", &quantrisk::normal_pdf, py::arg("x"), "Standard normal PDF phi(x).");
    module.def("inverse_normal_cdf", &quantrisk::inverse_normal_cdf, py::arg("probability"),
               "Quantile function N^-1(p), p strictly inside (0, 1).");

    // --- core: reproducible RNG ------------------------------------------
    py::class_<quantrisk::Rng>(module, "Rng",
                               "Instance-owned mt19937_64 stream (no global "
                               "RNG state).")
        .def(py::init<quantrisk::Seed>(), py::arg("seed") = quantrisk::Rng::kDefaultSeed)
        .def("uniform01", &quantrisk::Rng::uniform01, "Next uniform variate in [0, 1).")
        .def("standard_normal", &quantrisk::Rng::standard_normal,
             "Next N(0, 1) variate (Marsaglia polar, partner cached).")
        .def("standard_normal_vector", &quantrisk::Rng::standard_normal_vector, py::arg("n"),
             "Next n N(0, 1) variates.")
        .def("uniform_index", &quantrisk::Rng::uniform_index, py::arg("high"),
             "Unbiased integer uniform in [0, high).")
        .def_property_readonly("seed", &quantrisk::Rng::seed)
        .def_property_readonly("uniform_draws", &quantrisk::Rng::uniform_draws)
        .def_property_readonly("has_cached_normal", &quantrisk::Rng::has_cached_normal);

    // --- core: statistics helpers ----------------------------------------
    py::module_ stats = module.def_submodule("stats", "Statistics helpers implemented in C++.");
    stats
        .def(
            "sum_compensated",
            [](const std::vector<double> &data) { return quantrisk::stats::sum_compensated(data); })
        .def("mean", [](const std::vector<double> &data) { return quantrisk::stats::mean(data); })
        .def(
            "sample_variance",
            [](const std::vector<double> &data) { return quantrisk::stats::sample_variance(data); })
        .def("sample_stddev",
             [](const std::vector<double> &data) { return quantrisk::stats::sample_stddev(data); })
        .def("standard_error_of_mean",
             [](const std::vector<double> &data) {
                 return quantrisk::stats::standard_error_of_mean(data);
             })
        .def("quantile",
             [](std::vector<double> data, const double p) {
                 return quantrisk::stats::quantile(std::move(data), p);
             })
        .def("mean_of_largest_sorted",
             [](const std::vector<double> &sorted_ascending, const std::int64_t k) {
                 return quantrisk::stats::mean_of_largest_sorted(sorted_ascending, k);
             })
        .def("autocorrelation", [](const std::vector<double> &data, const std::int64_t lag) {
            return quantrisk::stats::autocorrelation(data, lag);
        });
}
