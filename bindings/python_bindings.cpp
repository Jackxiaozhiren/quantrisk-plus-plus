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
#include "quantrisk/pricing/binomial_crr.hpp"
#include "quantrisk/pricing/black_scholes.hpp"
#include "quantrisk/pricing/finite_differences.hpp"
#include "quantrisk/pricing/instrument.hpp"

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

    // --- pricing: instruments, Black-Scholes, CRR lattice, FD Greeks ----
    py::module_ pricing = module.def_submodule("pricing", "Deterministic pricing (C++20 core).");

    py::enum_<quantrisk::OptionType>(pricing, "OptionType")
        .value("CALL", quantrisk::OptionType::Call)
        .value("PUT", quantrisk::OptionType::Put)
        .export_values();

    py::enum_<quantrisk::ExerciseStyle>(pricing, "ExerciseStyle")
        .value("EUROPEAN", quantrisk::ExerciseStyle::European)
        .value("AMERICAN", quantrisk::ExerciseStyle::American)
        .export_values();

    py::class_<quantrisk::MarketParams>(
        pricing, "MarketParams",
        "Continuously compounded rates, annualised volatility, maturity in years.")
        .def(py::init([](const double spot, const double rate, const double dividend_yield,
                         const double volatility, const double maturity) {
                 return quantrisk::MarketParams{.spot = spot,
                                                .rate = rate,
                                                .dividend_yield = dividend_yield,
                                                .volatility = volatility,
                                                .maturity = maturity};
             }),
             py::arg("spot"), py::arg("rate"), py::arg("dividend_yield") = 0.0,
             py::arg("volatility") = 0.0, py::arg("maturity") = 0.0)
        .def_readwrite("spot", &quantrisk::MarketParams::spot)
        .def_readwrite("rate", &quantrisk::MarketParams::rate)
        .def_readwrite("dividend_yield", &quantrisk::MarketParams::dividend_yield)
        .def_readwrite("volatility", &quantrisk::MarketParams::volatility)
        .def_readwrite("maturity", &quantrisk::MarketParams::maturity)
        .def("validate", &quantrisk::MarketParams::validate)
        .def("forward_at", &quantrisk::MarketParams::forward_at, py::arg("time"));

    py::class_<quantrisk::EuropeanOption>(pricing, "EuropeanOption")
        .def(py::init<const quantrisk::OptionType, double>(), py::arg("type"), py::arg("strike"))
        .def_readwrite("type", &quantrisk::EuropeanOption::type)
        .def_readwrite("strike", &quantrisk::EuropeanOption::strike)
        .def("validate", &quantrisk::EuropeanOption::validate)
        .def("payoff", &quantrisk::EuropeanOption::payoff, py::arg("underlying"));

    py::class_<quantrisk::PricingResult>(pricing, "PricingResult")
        .def_readonly("price", &quantrisk::PricingResult::price)
        .def_readonly("d1", &quantrisk::PricingResult::d1)
        .def_readonly("d2", &quantrisk::PricingResult::d2)
        .def_readonly("method", &quantrisk::PricingResult::method)
        .def_readonly("note", &quantrisk::PricingResult::note);

    py::class_<quantrisk::Greeks>(pricing, "Greeks")
        .def_readonly("delta", &quantrisk::Greeks::delta)
        .def_readonly("gamma", &quantrisk::Greeks::gamma)
        .def_readonly("vega", &quantrisk::Greeks::vega)
        .def_readonly("theta", &quantrisk::Greeks::theta)
        .def_readonly("rho", &quantrisk::Greeks::rho);

    py::class_<quantrisk::BumpPolicy>(pricing, "BumpPolicy")
        .def(py::init<>())
        .def_readwrite("spot_relative", &quantrisk::BumpPolicy::spot_relative)
        .def_readwrite("volatility_absolute", &quantrisk::BumpPolicy::volatility_absolute)
        .def_readwrite("rate_absolute", &quantrisk::BumpPolicy::rate_absolute)
        .def_readwrite("time_absolute", &quantrisk::BumpPolicy::time_absolute)
        .def("validate", &quantrisk::BumpPolicy::validate);

    py::class_<quantrisk::BinomialResult>(pricing, "BinomialResult")
        .def_readonly("price", &quantrisk::BinomialResult::price)
        .def_readonly("steps", &quantrisk::BinomialResult::steps)
        .def_readonly("time_step", &quantrisk::BinomialResult::time_step)
        .def_readonly("up", &quantrisk::BinomialResult::up)
        .def_readonly("down", &quantrisk::BinomialResult::down)
        .def_readonly("risk_neutral_up_probability",
                      &quantrisk::BinomialResult::risk_neutral_up_probability)
        .def_readonly("exercise_style", &quantrisk::BinomialResult::exercise_style)
        .def_readonly("note", &quantrisk::BinomialResult::note);

    pricing.def("black_scholes", &quantrisk::black_scholes, py::arg("option"), py::arg("market"));
    pricing.def("black_scholes_greeks", &quantrisk::black_scholes_greeks, py::arg("option"),
                py::arg("market"));
    pricing.def("put_call_parity_residual", &quantrisk::put_call_parity_residual, py::arg("market"),
                py::arg("strike"));
    pricing.def("finite_difference_greeks", &quantrisk::finite_difference_greeks, py::arg("option"),
                py::arg("market"), py::arg("policy") = quantrisk::BumpPolicy{});
    pricing.def("crr_binomial", &quantrisk::crr_binomial, py::arg("option"), py::arg("market"),
                py::arg("exercise_style"), py::arg("steps"));
    pricing.def("crr_convergence_to_black_scholes", &quantrisk::crr_convergence_to_black_scholes,
                py::arg("option"), py::arg("market"), py::arg("step_counts"));
}
