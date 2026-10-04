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
#include "quantrisk/math/special.hpp"
#include "quantrisk/monte_carlo/engine.hpp"
#include "quantrisk/monte_carlo/path_dependent.hpp"
#include "quantrisk/portfolio/covariance.hpp"
#include "quantrisk/portfolio/cvar.hpp"
#include "quantrisk/portfolio/linear_program.hpp"
#include "quantrisk/portfolio/mean_variance.hpp"
#include "quantrisk/portfolio/risk_parity.hpp"
#include "quantrisk/pricing/binomial_crr.hpp"
#include "quantrisk/pricing/black_scholes.hpp"
#include "quantrisk/pricing/finite_differences.hpp"
#include "quantrisk/pricing/instrument.hpp"
#include "quantrisk/pricing/path_dependent.hpp"
#include "quantrisk/risk/backtest.hpp"
#include "quantrisk/risk/bootstrap.hpp"
#include "quantrisk/risk/measures.hpp"
#include "quantrisk/stochastic/gbm.hpp"
#include "quantrisk/stochastic/heston.hpp"
#include "quantrisk/stress/engine.hpp"
#include "quantrisk/stress/factor.hpp"
#include "quantrisk/stress/scenario.hpp"
#include "quantrisk/stress/simulation.hpp"

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

    // A plain value struct, exactly like `Greeks`: bound containers come back as
    // copies in this project, so nothing here holds one.
    py::class_<quantrisk::SpotDerivatives>(pricing, "SpotDerivatives")
        .def_readonly("third", &quantrisk::SpotDerivatives::third)
        .def_readonly("fourth", &quantrisk::SpotDerivatives::fourth);

    py::class_<quantrisk::VolCrossDerivatives>(pricing, "VolCrossDerivatives")
        .def_readonly("vanna", &quantrisk::VolCrossDerivatives::vanna)
        .def_readonly("volga", &quantrisk::VolCrossDerivatives::volga);

    py::class_<quantrisk::MixedThirdDerivatives>(pricing, "MixedThirdDerivatives")
        .def_readonly("spot_spot_sigma", &quantrisk::MixedThirdDerivatives::spot_spot_sigma)
        .def_readonly("spot_sigma_sigma", &quantrisk::MixedThirdDerivatives::spot_sigma_sigma)
        .def_readonly("sigma_sigma_sigma", &quantrisk::MixedThirdDerivatives::sigma_sigma_sigma);

    py::class_<quantrisk::MixedFourthDerivatives>(pricing, "MixedFourthDerivatives")
        .def_readonly("spot_spot_spot_sigma",
                      &quantrisk::MixedFourthDerivatives::spot_spot_spot_sigma)
        .def_readonly("spot_spot_sigma_sigma",
                      &quantrisk::MixedFourthDerivatives::spot_spot_sigma_sigma)
        .def_readonly("spot_sigma_sigma_sigma",
                      &quantrisk::MixedFourthDerivatives::spot_sigma_sigma_sigma)
        .def_readonly("sigma_sigma_sigma_sigma",
                      &quantrisk::MixedFourthDerivatives::sigma_sigma_sigma_sigma);

    py::class_<quantrisk::MixedFifthDerivatives>(pricing, "MixedFifthDerivatives")
        .def_readonly("spot_spot_spot_spot_spot",
                      &quantrisk::MixedFifthDerivatives::spot_spot_spot_spot_spot)
        .def_readonly("spot_spot_spot_spot_sigma",
                      &quantrisk::MixedFifthDerivatives::spot_spot_spot_spot_sigma)
        .def_readonly("spot_spot_spot_sigma_sigma",
                      &quantrisk::MixedFifthDerivatives::spot_spot_spot_sigma_sigma)
        .def_readonly("spot_spot_sigma_sigma_sigma",
                      &quantrisk::MixedFifthDerivatives::spot_spot_sigma_sigma_sigma)
        .def_readonly("spot_sigma_sigma_sigma_sigma",
                      &quantrisk::MixedFifthDerivatives::spot_sigma_sigma_sigma_sigma)
        .def_readonly("sigma_sigma_sigma_sigma_sigma",
                      &quantrisk::MixedFifthDerivatives::sigma_sigma_sigma_sigma_sigma);

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
    pricing.def("black_scholes_spot_derivatives", &quantrisk::black_scholes_spot_derivatives,
                py::arg("option"), py::arg("market"));
    pricing.def("black_scholes_vol_cross_derivatives",
                &quantrisk::black_scholes_vol_cross_derivatives, py::arg("option"),
                py::arg("market"));
    pricing.def("black_scholes_mixed_third_derivatives",
                &quantrisk::black_scholes_mixed_third_derivatives, py::arg("option"),
                py::arg("market"));
    pricing.def("black_scholes_mixed_fourth_derivatives",
                &quantrisk::black_scholes_mixed_fourth_derivatives, py::arg("option"),
                py::arg("market"));
    pricing.def("black_scholes_mixed_fifth_derivatives",
                &quantrisk::black_scholes_mixed_fifth_derivatives, py::arg("option"),
                py::arg("market"));
    pricing.def("put_call_parity_residual", &quantrisk::put_call_parity_residual, py::arg("market"),
                py::arg("strike"));
    pricing.def("finite_difference_greeks", &quantrisk::finite_difference_greeks, py::arg("option"),
                py::arg("market"), py::arg("policy") = quantrisk::BumpPolicy{});
    pricing.def("crr_binomial", &quantrisk::crr_binomial, py::arg("option"), py::arg("market"),
                py::arg("exercise_style"), py::arg("steps"));
    pricing.def("crr_convergence_to_black_scholes", &quantrisk::crr_convergence_to_black_scholes,
                py::arg("option"), py::arg("market"), py::arg("step_counts"));

    // --- stochastic: GBM path generation --------------------------------
    py::module_ stochastic =
        module.def_submodule("stochastic", "GBM path generation (C++20 core).");
    stochastic.def("terminal_prices", &quantrisk::gbm::terminal_prices, py::arg("market"),
                   py::arg("paths"), py::arg("rng"));
    stochastic.def("antithetic_terminal_prices", &quantrisk::gbm::antithetic_terminal_prices,
                   py::arg("market"), py::arg("paths"), py::arg("rng"));
    stochastic.def("paths_matrix", &quantrisk::gbm::paths_matrix, py::arg("market"),
                   py::arg("paths"), py::arg("steps"), py::arg("rng"));
    stochastic.def("antithetic_paths_matrix", &quantrisk::gbm::antithetic_paths_matrix,
                   py::arg("market"), py::arg("paths"), py::arg("steps"), py::arg("rng"));
    stochastic.def("terminal_prices_physical", &quantrisk::gbm::terminal_prices_physical,
                   py::arg("market"), py::arg("mu"), py::arg("paths"), py::arg("rng"));
    stochastic.def("expected_log_return", &quantrisk::gbm::expected_log_return, py::arg("market"));

    // --- monte_carlo: engine and estimators ------------------------------
    py::module_ monte_carlo =
        module.def_submodule("monte_carlo", "Monte Carlo pricing engine (C++20 core).");

    py::enum_<quantrisk::VarianceReduction>(monte_carlo, "VarianceReduction")
        .value("NONE", quantrisk::VarianceReduction::None)
        .value("ANTITHETIC", quantrisk::VarianceReduction::Antithetic)
        .value("CONTROL_VARIATE", quantrisk::VarianceReduction::ControlVariate)
        .export_values();

    py::class_<quantrisk::MonteCarloResult>(monte_carlo, "MonteCarloResult")
        .def_readonly("price", &quantrisk::MonteCarloResult::price)
        .def_readonly("standard_error", &quantrisk::MonteCarloResult::standard_error)
        .def_readonly("confidence_level", &quantrisk::MonteCarloResult::confidence_level)
        .def_readonly("confidence_low", &quantrisk::MonteCarloResult::confidence_low)
        .def_readonly("confidence_high", &quantrisk::MonteCarloResult::confidence_high)
        .def_readonly("paths", &quantrisk::MonteCarloResult::paths)
        .def_readonly("iid_units", &quantrisk::MonteCarloResult::iid_units)
        .def_readonly("seed", &quantrisk::MonteCarloResult::seed)
        .def_readonly("sample_variance", &quantrisk::MonteCarloResult::sample_variance)
        .def_readonly("sample_stddev", &quantrisk::MonteCarloResult::sample_stddev)
        .def_readonly("control_beta", &quantrisk::MonteCarloResult::control_beta)
        .def_readonly("runtime_seconds", &quantrisk::MonteCarloResult::runtime_seconds)
        .def_readonly("variance_reduction", &quantrisk::MonteCarloResult::variance_reduction)
        .def_readonly("measure", &quantrisk::MonteCarloResult::measure)
        .def_readonly("note", &quantrisk::MonteCarloResult::note)
        .def("__repr__", [](const quantrisk::MonteCarloResult &result) {
            return std::string("<MonteCarloResult price=") + std::to_string(result.price) +
                   " se=" + std::to_string(result.standard_error) +
                   " paths=" + std::to_string(result.paths) +
                   " seed=" + std::to_string(result.seed) + ">";
        });

    py::class_<quantrisk::MonteCarloEngine>(
        monte_carlo, "MonteCarloEngine",
        "One engine owns one reproducible stream; no global RNG state.")
        .def(py::init<quantrisk::Seed>(), py::arg("seed") = quantrisk::Rng::kDefaultSeed)
        .def_property_readonly("seed", &quantrisk::MonteCarloEngine::seed)
        .def_property_readonly("uniform_draws", &quantrisk::MonteCarloEngine::uniform_draws)
        .def(
            "price_european",
            [](quantrisk::MonteCarloEngine &engine, const quantrisk::EuropeanOption &option,
               const quantrisk::MarketParams &market, const std::int64_t paths,
               const quantrisk::VarianceReduction method, const double confidence_level) {
                return engine.price_european(option, market, paths, method, confidence_level);
            },
            py::arg("option"), py::arg("market"), py::arg("paths"),
            py::arg("variance_reduction") = quantrisk::VarianceReduction::None,
            py::arg("confidence_level") = 0.95)
        .def(
            "price_call",
            [](quantrisk::MonteCarloEngine &engine, const quantrisk::MarketParams &market,
               const double strike, const std::int64_t paths,
               const quantrisk::VarianceReduction method, const double confidence_level) {
                return engine.price_european(
                    quantrisk::EuropeanOption{quantrisk::OptionType::Call, strike}, market, paths,
                    method, confidence_level);
            },
            py::arg("market"), py::arg("strike"), py::arg("paths"),
            py::arg("variance_reduction") = quantrisk::VarianceReduction::None,
            py::arg("confidence_level") = 0.95)
        .def(
            "price_put",
            [](quantrisk::MonteCarloEngine &engine, const quantrisk::MarketParams &market,
               const double strike, const std::int64_t paths,
               const quantrisk::VarianceReduction method, const double confidence_level) {
                return engine.price_european(
                    quantrisk::EuropeanOption{quantrisk::OptionType::Put, strike}, market, paths,
                    method, confidence_level);
            },
            py::arg("market"), py::arg("strike"), py::arg("paths"),
            py::arg("variance_reduction") = quantrisk::VarianceReduction::None,
            py::arg("confidence_level") = 0.95);

    monte_carlo.def("normal_confidence_multiplier", &quantrisk::normal_confidence_multiplier,
                    py::arg("confidence_level"));
    monte_carlo.def("variance_reduction_name", [](const quantrisk::VarianceReduction method) {
        return std::string(quantrisk::to_string(method));
    });

    // --- pricing: path-dependent instruments ---------------------------
    py::enum_<quantrisk::AverageType>(pricing, "AverageType")
        .value("ARITHMETIC", quantrisk::AverageType::Arithmetic)
        .value("GEOMETRIC", quantrisk::AverageType::Geometric)
        .export_values();
    py::enum_<quantrisk::BarrierType>(pricing, "BarrierType")
        .value("UP_AND_OUT", quantrisk::BarrierType::UpAndOut)
        .value("DOWN_AND_OUT", quantrisk::BarrierType::DownAndOut)
        .export_values();

    py::class_<quantrisk::AsianOption>(pricing, "AsianOption")
        .def(py::init<const quantrisk::OptionType, double, const quantrisk::AverageType,
                      std::int64_t>(),
             py::arg("type"), py::arg("strike"), py::arg("average_type"),
             py::arg("monitoring_points"))
        .def_readwrite("type", &quantrisk::AsianOption::type)
        .def_readwrite("strike", &quantrisk::AsianOption::strike)
        .def_readwrite("average_type", &quantrisk::AsianOption::average_type)
        .def_readwrite("monitoring_points", &quantrisk::AsianOption::monitoring_points)
        .def("validate", &quantrisk::AsianOption::validate)
        .def("payoff", &quantrisk::AsianOption::payoff, py::arg("sampled"))
        .def("payoff_from_average", &quantrisk::AsianOption::payoff_from_average,
             py::arg("average"));

    py::class_<quantrisk::BarrierOption>(pricing, "BarrierOption")
        .def(py::init<const quantrisk::OptionType, double, const quantrisk::BarrierType, double,
                      double>(),
             py::arg("type"), py::arg("strike"), py::arg("barrier"), py::arg("barrier_level"),
             py::arg("rebate") = 0.0)
        .def_readwrite("type", &quantrisk::BarrierOption::type)
        .def_readwrite("strike", &quantrisk::BarrierOption::strike)
        .def_readwrite("barrier", &quantrisk::BarrierOption::barrier)
        .def_readwrite("barrier_level", &quantrisk::BarrierOption::barrier_level)
        .def_readwrite("rebate", &quantrisk::BarrierOption::rebate)
        .def("validate", &quantrisk::BarrierOption::validate)
        .def("survives", &quantrisk::BarrierOption::survives, py::arg("level"))
        .def("payoff", &quantrisk::BarrierOption::payoff, py::arg("terminal"));

    pricing.def("geometric_asian_price", &quantrisk::geometric_asian_price, py::arg("option"),
                py::arg("market"));
    pricing.def("barrier_continuity_constant", &quantrisk::barrier_continuity_constant);
    pricing.def("continuity_corrected_barrier", &quantrisk::continuity_corrected_barrier,
                py::arg("option"), py::arg("market"), py::arg("dt"));

    // --- monte_carlo: path-dependent estimators -------------------------
    monte_carlo.def("price_asian", &quantrisk::path_dependent::price_asian, py::arg("engine"),
                    py::arg("option"), py::arg("market"), py::arg("paths"),
                    py::arg("use_control_variate"), py::arg("confidence_level") = 0.95);
    monte_carlo.def("price_geometric_asian", &quantrisk::path_dependent::price_geometric_asian,
                    py::arg("engine"), py::arg("option"), py::arg("market"), py::arg("paths"),
                    py::arg("confidence_level") = 0.95);
    monte_carlo.def("price_barrier", &quantrisk::path_dependent::price_barrier, py::arg("engine"),
                    py::arg("option"), py::arg("market"), py::arg("paths"), py::arg("steps"),
                    py::arg("continuous_approximation") = false, py::arg("antithetic") = false,
                    py::arg("confidence_level") = 0.95);

    // --- stochastic: Heston --------------------------------------------
    py::class_<quantrisk::HestonParams>(stochastic, "HestonParams")
        .def(py::init<>())
        .def_readwrite("spot", &quantrisk::HestonParams::spot)
        .def_readwrite("rate", &quantrisk::HestonParams::rate)
        .def_readwrite("dividend_yield", &quantrisk::HestonParams::dividend_yield)
        .def_readwrite("initial_variance", &quantrisk::HestonParams::initial_variance)
        .def_readwrite("kappa", &quantrisk::HestonParams::kappa)
        .def_readwrite("theta", &quantrisk::HestonParams::theta)
        .def_readwrite("xi", &quantrisk::HestonParams::xi)
        .def_readwrite("rho", &quantrisk::HestonParams::rho)
        .def_readwrite("maturity", &quantrisk::HestonParams::maturity)
        .def("validate", &quantrisk::HestonParams::validate)
        .def("feller_condition_satisfied", &quantrisk::HestonParams::feller_condition_satisfied)
        .def("instantaneous_volatility", &quantrisk::HestonParams::instantaneous_volatility);

    py::class_<quantrisk::HestonSimulation>(stochastic, "HestonSimulation")
        .def_readonly("terminals", &quantrisk::HestonSimulation::terminals)
        .def_readonly("terminal_variance", &quantrisk::HestonSimulation::terminal_variance)
        .def_readonly("realised_variance", &quantrisk::HestonSimulation::realised_variance)
        .def_readonly("paths", &quantrisk::HestonSimulation::paths)
        .def_readonly("steps", &quantrisk::HestonSimulation::steps)
        .def_readonly("seed", &quantrisk::HestonSimulation::seed)
        .def_readonly("time_step", &quantrisk::HestonSimulation::time_step)
        .def_readonly("negative_variances_clamped",
                      &quantrisk::HestonSimulation::negative_variances_clamped)
        .def_readonly("runtime_seconds", &quantrisk::HestonSimulation::runtime_seconds)
        .def_readonly("note", &quantrisk::HestonSimulation::note);

    py::class_<quantrisk::HestonPriceResult>(stochastic, "HestonPriceResult")
        .def_readonly("price", &quantrisk::HestonPriceResult::price)
        .def_readonly("standard_error", &quantrisk::HestonPriceResult::standard_error)
        .def_readonly("confidence_low", &quantrisk::HestonPriceResult::confidence_low)
        .def_readonly("confidence_high", &quantrisk::HestonPriceResult::confidence_high)
        .def_readonly("paths", &quantrisk::HestonPriceResult::paths)
        .def_readonly("steps", &quantrisk::HestonPriceResult::steps)
        .def_readonly("seed", &quantrisk::HestonPriceResult::seed)
        .def_readonly("mean_terminal_variance",
                      &quantrisk::HestonPriceResult::mean_terminal_variance)
        .def_readonly("realised_variance_mean",
                      &quantrisk::HestonPriceResult::realised_variance_mean)
        .def_readonly("negative_variances_clamped",
                      &quantrisk::HestonPriceResult::negative_variances_clamped)
        .def_readonly("feller_condition_satisfied",
                      &quantrisk::HestonPriceResult::feller_condition_satisfied)
        .def_readonly("runtime_seconds", &quantrisk::HestonPriceResult::runtime_seconds)
        .def_readonly("note", &quantrisk::HestonPriceResult::note);

    stochastic.def("simulate_heston", &quantrisk::simulate_heston, py::arg("parameters"),
                   py::arg("paths"), py::arg("steps"), py::arg("rng"));
    stochastic.def("price_heston_european", &quantrisk::price_heston_european,
                   py::arg("parameters"), py::arg("option"), py::arg("paths"), py::arg("steps"),
                   py::arg("rng"), py::arg("confidence_level") = 0.95);
    stochastic.def("heston_step_refinement_gap", &quantrisk::heston_step_refinement_gap,
                   py::arg("parameters"), py::arg("option"), py::arg("paths"), py::arg("steps"),
                   py::arg("reference_steps"), py::arg("seed"));

    // --- special functions for hypothesis tests -------------------------
    py::module_ special =
        module.def_submodule("special", "Special functions used by test statistics.");
    special.def("log_gamma", &quantrisk::log_gamma, py::arg("x"));
    special.def("regularized_lower_incomplete_gamma",
                &quantrisk::regularized_lower_incomplete_gamma, py::arg("a"), py::arg("x"));
    special.def("regularized_upper_incomplete_gamma",
                &quantrisk::regularized_upper_incomplete_gamma, py::arg("a"), py::arg("x"));
    special.def("chi_square_sf", &quantrisk::chi_square_sf, py::arg("x"),
                py::arg("degrees_of_freedom"));
    special.def("chi_square_isf", &quantrisk::chi_square_isf, py::arg("probability"),
                py::arg("degrees_of_freedom"));
    special.def("log_binomial_coefficient", &quantrisk::log_binomial_coefficient, py::arg("n"),
                py::arg("k"));

    // --- risk: returns, VaR/ES, bootstrap, backtests --------------------
    py::module_ risk = module.def_submodule("risk", "Market-risk measures (C++20 core).");
    py::module_ returns = risk.def_submodule("returns", "Return definitions (arithmetic vs log).");
    // The core takes non-owning `std::span` views; pybind11 materialises Python
    // sequences (and NumPy arrays) as `std::vector<double>`, so every entry
    // point below goes through a one-line adapter. No conversion logic beyond
    // that lives here (docs/architecture.md §2).
    returns.def(
        "arithmetic",
        [](const std::vector<double> &prices) { return quantrisk::returns::arithmetic(prices); },
        py::arg("prices"));
    returns.def(
        "log_returns",
        [](const std::vector<double> &prices) { return quantrisk::returns::log_returns(prices); },
        py::arg("prices"));

    py::class_<quantrisk::risk::RiskEstimate>(risk, "RiskEstimate")
        .def_readonly("value", &quantrisk::risk::RiskEstimate::value)
        .def_readonly("confidence_level", &quantrisk::risk::RiskEstimate::confidence_level)
        .def_readonly("observations", &quantrisk::risk::RiskEstimate::observations)
        .def_readonly("standard_error", &quantrisk::risk::RiskEstimate::standard_error)
        .def_readonly("ci_low", &quantrisk::risk::RiskEstimate::ci_low)
        .def_readonly("ci_high", &quantrisk::risk::RiskEstimate::ci_high)
        .def_readonly("has_interval", &quantrisk::risk::RiskEstimate::has_interval)
        .def_readonly("method", &quantrisk::risk::RiskEstimate::method)
        .def_readonly("note", &quantrisk::risk::RiskEstimate::note);

    risk.def(
        "historical_var",
        [](const std::vector<double> &sample, const double level) {
            return quantrisk::risk::historical_var(sample, level);
        },
        py::arg("returns_sample"), py::arg("confidence_level"));
    risk.def(
        "historical_es",
        [](const std::vector<double> &sample, const double level) {
            return quantrisk::risk::historical_es(sample, level);
        },
        py::arg("returns_sample"), py::arg("confidence_level"));
    risk.def(
        "gaussian_var",
        [](const std::vector<double> &sample, const double level) {
            return quantrisk::risk::gaussian_var(sample, level);
        },
        py::arg("returns_sample"), py::arg("confidence_level"));
    risk.def(
        "gaussian_es",
        [](const std::vector<double> &sample, const double level) {
            return quantrisk::risk::gaussian_es(sample, level);
        },
        py::arg("returns_sample"), py::arg("confidence_level"));
    risk.def(
        "monte_carlo_var",
        [](const std::vector<double> &pnl, const double level) {
            return quantrisk::risk::monte_carlo_var(pnl, level);
        },
        py::arg("simulated_pnl"), py::arg("confidence_level"));
    risk.def(
        "monte_carlo_es",
        [](const std::vector<double> &pnl, const double level) {
            return quantrisk::risk::monte_carlo_es(pnl, level);
        },
        py::arg("simulated_pnl"), py::arg("confidence_level"));
    risk.def(
        "linear_pnl",
        [](const std::vector<double> &weights, const std::vector<double> &rows,
           const std::int64_t assets, const double capital) {
            return quantrisk::risk::linear_pnl(weights, rows, assets, capital);
        },
        py::arg("weights"), py::arg("returns_rows"), py::arg("assets"), py::arg("capital"));
    risk.def(
        "sample_covariance",
        [](const std::vector<double> &rows, const std::int64_t assets,
           const std::int64_t observations) {
            return quantrisk::risk::sample_covariance(rows, assets, observations);
        },
        py::arg("returns_rows"), py::arg("assets"), py::arg("observations"));

    py::enum_<quantrisk::BootstrapKind>(risk, "BootstrapKind")
        .value("IID", quantrisk::BootstrapKind::Iid)
        .value("MOVING_BLOCK", quantrisk::BootstrapKind::MovingBlock)
        .export_values();

    py::class_<quantrisk::BootstrapEstimate>(risk, "BootstrapEstimate")
        .def_readonly("point", &quantrisk::BootstrapEstimate::point)
        .def_readonly("standard_error", &quantrisk::BootstrapEstimate::standard_error)
        .def_readonly("ci_low", &quantrisk::BootstrapEstimate::ci_low)
        .def_readonly("ci_high", &quantrisk::BootstrapEstimate::ci_high)
        .def_readonly("confidence_level", &quantrisk::BootstrapEstimate::confidence_level)
        .def_readonly("replicates", &quantrisk::BootstrapEstimate::replicates)
        .def_readonly("block_length", &quantrisk::BootstrapEstimate::block_length)
        .def_readonly("observations", &quantrisk::BootstrapEstimate::observations)
        .def_readonly("kind", &quantrisk::BootstrapEstimate::kind)
        .def_readonly("measure", &quantrisk::BootstrapEstimate::measure)
        .def_readonly("note", &quantrisk::BootstrapEstimate::note);

    risk.def(
        "bootstrap_var",
        [](const std::vector<double> &sample, const double confidence_level,
           const std::int64_t replicates, const double interval_level,
           const quantrisk::BootstrapKind kind, const std::int64_t block_length,
           const std::uint64_t seed) {
            return quantrisk::bootstrap_var(sample, confidence_level, replicates, interval_level,
                                            kind, block_length, seed);
        },
        py::arg("returns_sample"), py::arg("confidence_level"), py::arg("replicates") = 2000,
        py::arg("interval_level") = 0.90, py::arg("kind") = quantrisk::BootstrapKind::Iid,
        py::arg("block_length") = 0, py::arg("seed") = quantrisk::Rng::kDefaultSeed);
    risk.def(
        "bootstrap_es",
        [](const std::vector<double> &sample, const double confidence_level,
           const std::int64_t replicates, const double interval_level,
           const quantrisk::BootstrapKind kind, const std::int64_t block_length,
           const std::uint64_t seed) {
            return quantrisk::bootstrap_es(sample, confidence_level, replicates, interval_level,
                                           kind, block_length, seed);
        },
        py::arg("returns_sample"), py::arg("confidence_level"), py::arg("replicates") = 2000,
        py::arg("interval_level") = 0.90, py::arg("kind") = quantrisk::BootstrapKind::Iid,
        py::arg("block_length") = 0, py::arg("seed") = quantrisk::Rng::kDefaultSeed);
    risk.def("suggested_block_length", &quantrisk::suggested_block_length, py::arg("observations"));

    py::class_<quantrisk::ViolationSeries>(risk, "ViolationSeries")
        .def_readonly("flags", &quantrisk::ViolationSeries::flags)
        .def_readonly("observations", &quantrisk::ViolationSeries::observations)
        .def_readonly("exceptions", &quantrisk::ViolationSeries::exceptions)
        .def_readonly("violation_rate", &quantrisk::ViolationSeries::violation_rate);

    py::class_<quantrisk::TransitionCounts>(risk, "TransitionCounts")
        .def_readonly("n00", &quantrisk::TransitionCounts::n00)
        .def_readonly("n01", &quantrisk::TransitionCounts::n01)
        .def_readonly("n10", &quantrisk::TransitionCounts::n10)
        .def_readonly("n11", &quantrisk::TransitionCounts::n11)
        .def_readonly("pi01", &quantrisk::TransitionCounts::pi01)
        .def_readonly("pi11", &quantrisk::TransitionCounts::pi11)
        .def_readonly("pi0", &quantrisk::TransitionCounts::pi0)
        .def_readonly("estimable", &quantrisk::TransitionCounts::estimable);

    py::class_<quantrisk::CoverageTestResult>(risk, "CoverageTestResult")
        .def_readonly("observations", &quantrisk::CoverageTestResult::observations)
        .def_readonly("exceptions", &quantrisk::CoverageTestResult::exceptions)
        .def_readonly("nominal_violation_rate",
                      &quantrisk::CoverageTestResult::nominal_violation_rate)
        .def_readonly("observed_violation_rate",
                      &quantrisk::CoverageTestResult::observed_violation_rate)
        .def_readonly("statistic", &quantrisk::CoverageTestResult::statistic)
        .def_readonly("p_value", &quantrisk::CoverageTestResult::p_value)
        .def_readonly("degrees_of_freedom", &quantrisk::CoverageTestResult::degrees_of_freedom)
        .def_readonly("critical_value_95", &quantrisk::CoverageTestResult::critical_value_95)
        .def_readonly("rejected_at_5_percent",
                      &quantrisk::CoverageTestResult::rejected_at_5_percent)
        .def_readonly("degenerate", &quantrisk::CoverageTestResult::degenerate)
        .def_readonly("test", &quantrisk::CoverageTestResult::test)
        .def_readonly("interpretation", &quantrisk::CoverageTestResult::interpretation);

    py::class_<quantrisk::BacktestReport>(risk, "BacktestReport")
        .def_readonly("series", &quantrisk::BacktestReport::series)
        .def_readonly("kupiec", &quantrisk::BacktestReport::kupiec)
        .def_readonly("independence", &quantrisk::BacktestReport::independence)
        .def_readonly("conditional", &quantrisk::BacktestReport::conditional)
        .def_readonly("note", &quantrisk::BacktestReport::note);

    risk.def(
        "flag_violations",
        [](const std::vector<double> &returns_sample, const std::vector<double> &levels) {
            return quantrisk::flag_violations(returns_sample, levels);
        },
        py::arg("returns_sample"), py::arg("var_levels"));
    risk.def(
        "flag_violations",
        [](const std::vector<double> &returns_sample, const double level) {
            return quantrisk::flag_violations(returns_sample, level);
        },
        py::arg("returns_sample"), py::arg("var_level"));
    risk.def("transition_counts", &quantrisk::transition_counts, py::arg("series"));
    risk.def("kupiec_pof_test", &quantrisk::kupiec_pof_test, py::arg("series"),
             py::arg("confidence_level"));
    risk.def("christoffersen_independence_test", &quantrisk::christoffersen_independence_test,
             py::arg("series"));
    risk.def("christoffersen_conditional_coverage_test",
             &quantrisk::christoffersen_conditional_coverage_test, py::arg("series"),
             py::arg("confidence_level"));
    risk.def(
        "backtest_var",
        [](const std::vector<double> &sample, const std::vector<double> &levels,
           const double confidence_level) {
            return quantrisk::backtest_var(sample, levels, confidence_level);
        },
        py::arg("returns_sample"), py::arg("var_levels"), py::arg("confidence_level"));

    // --- portfolio: covariance estimation --------------------------------
    py::module_ portfolio = module.def_submodule("portfolio", "Portfolio layer (C++20 core).");

    py::class_<quantrisk::portfolio::CovarianceEstimate>(portfolio, "CovarianceEstimate")
        .def_readonly("assets", &quantrisk::portfolio::CovarianceEstimate::assets)
        .def_readonly("observations", &quantrisk::portfolio::CovarianceEstimate::observations)
        .def_readonly("values", &quantrisk::portfolio::CovarianceEstimate::values)
        .def_readonly("estimator", &quantrisk::portfolio::CovarianceEstimate::estimator)
        .def_readonly("decay", &quantrisk::portfolio::CovarianceEstimate::decay)
        .def_readonly("half_life", &quantrisk::portfolio::CovarianceEstimate::half_life)
        .def_readonly("shrinkage_intensity",
                      &quantrisk::portfolio::CovarianceEstimate::shrinkage_intensity)
        .def_readonly("target_scale", &quantrisk::portfolio::CovarianceEstimate::target_scale)
        .def_readonly("largest_eigenvalue",
                      &quantrisk::portfolio::CovarianceEstimate::largest_eigenvalue)
        .def_readonly("smallest_eigenvalue",
                      &quantrisk::portfolio::CovarianceEstimate::smallest_eigenvalue)
        .def_readonly("positive_semidefinite",
                      &quantrisk::portfolio::CovarianceEstimate::positive_semidefinite)
        .def_readonly("note", &quantrisk::portfolio::CovarianceEstimate::note);

    portfolio.def(
        "sample_covariance",
        [](const std::vector<double> &rows, const std::int64_t assets,
           const std::int64_t observations) {
            return quantrisk::portfolio::sample_covariance(rows, assets, observations);
        },
        py::arg("returns_rows"), py::arg("assets"), py::arg("observations"));
    portfolio.def(
        "ewma_covariance",
        [](const std::vector<double> &rows, const std::int64_t assets,
           const std::int64_t observations, const double lambda) {
            return quantrisk::portfolio::ewma_covariance(rows, assets, observations, lambda);
        },
        py::arg("returns_rows"), py::arg("assets"), py::arg("observations"), py::arg("lambda"));
    portfolio.def(
        "shrinkage_covariance",
        [](const std::vector<double> &rows, const std::int64_t assets,
           const std::int64_t observations) {
            return quantrisk::portfolio::shrinkage_covariance(rows, assets, observations);
        },
        py::arg("returns_rows"), py::arg("assets"), py::arg("observations"));
    portfolio.def(
        "condition_number",
        [](const quantrisk::portfolio::CovarianceEstimate &covariance) {
            return quantrisk::portfolio::condition_number(covariance);
        },
        py::arg("covariance"));
    portfolio.def(
        "eigenvalues",
        [](const std::vector<double> &symmetric, const std::int64_t assets) {
            return quantrisk::portfolio::eigenvalues(symmetric, assets);
        },
        py::arg("symmetric"), py::arg("assets"));

    py::class_<quantrisk::portfolio::LinearSolve>(portfolio, "LinearSolve")
        .def_readonly("values", &quantrisk::portfolio::LinearSolve::values)
        .def_readonly("solved", &quantrisk::portfolio::LinearSolve::solved)
        .def_readonly("note", &quantrisk::portfolio::LinearSolve::note);
    portfolio.def(
        "solve",
        [](const std::vector<double> &symmetric, const std::int64_t assets,
           const std::vector<double> &right_hand_side) {
            return quantrisk::portfolio::solve(symmetric, assets, right_hand_side);
        },
        py::arg("symmetric"), py::arg("assets"), py::arg("right_hand_side"));

    py::class_<quantrisk::portfolio::OptimizerInputs>(portfolio, "OptimizerInputs")
        .def(py::init<>())
        .def_readwrite("assets", &quantrisk::portfolio::OptimizerInputs::assets)
        .def_readwrite("covariance", &quantrisk::portfolio::OptimizerInputs::covariance)
        .def_readwrite("expected_returns", &quantrisk::portfolio::OptimizerInputs::expected_returns)
        .def_readwrite("scenario_returns", &quantrisk::portfolio::OptimizerInputs::scenario_returns)
        .def_readwrite("scenario_count", &quantrisk::portfolio::OptimizerInputs::scenario_count);

    py::class_<quantrisk::portfolio::OptimizationRequest>(portfolio, "OptimizationRequest")
        .def(py::init<>())
        .def_readwrite("long_only", &quantrisk::portfolio::OptimizationRequest::long_only)
        .def_readwrite("target_return", &quantrisk::portfolio::OptimizationRequest::target_return)
        .def_readwrite("risk_free_rate", &quantrisk::portfolio::OptimizationRequest::risk_free_rate)
        .def_readwrite("cvar_confidence",
                       &quantrisk::portfolio::OptimizationRequest::cvar_confidence);

    py::class_<quantrisk::portfolio::PortfolioSolution>(portfolio, "PortfolioSolution")
        .def_readonly("assets", &quantrisk::portfolio::PortfolioSolution::assets)
        .def_readonly("weights", &quantrisk::portfolio::PortfolioSolution::weights)
        .def_readonly("expected_return", &quantrisk::portfolio::PortfolioSolution::expected_return)
        .def_readonly("variance", &quantrisk::portfolio::PortfolioSolution::variance)
        .def_readonly("volatility", &quantrisk::portfolio::PortfolioSolution::volatility)
        .def_readonly("sharpe_ratio", &quantrisk::portfolio::PortfolioSolution::sharpe_ratio)
        .def_readonly("value_at_risk", &quantrisk::portfolio::PortfolioSolution::value_at_risk)
        .def_readonly("conditional_var", &quantrisk::portfolio::PortfolioSolution::conditional_var)
        .def_readonly("budget_residual", &quantrisk::portfolio::PortfolioSolution::budget_residual)
        .def_readonly("weight_bound_violation",
                      &quantrisk::portfolio::PortfolioSolution::weight_bound_violation)
        .def_readonly("target_residual", &quantrisk::portfolio::PortfolioSolution::target_residual)
        .def_readonly("tolerance", &quantrisk::portfolio::PortfolioSolution::tolerance)
        .def_readonly("feasible", &quantrisk::portfolio::PortfolioSolution::feasible)
        .def_readonly("verified_optimal",
                      &quantrisk::portfolio::PortfolioSolution::verified_optimal)
        .def_readonly("method", &quantrisk::portfolio::PortfolioSolution::method)
        .def_readonly("note", &quantrisk::portfolio::PortfolioSolution::note);

    portfolio.def("minimum_variance", &quantrisk::portfolio::minimum_variance, py::arg("inputs"),
                  py::arg("request"));
    portfolio.def(
        "efficient_frontier",
        [](const quantrisk::portfolio::OptimizerInputs &inputs, const std::vector<double> &targets,
           const quantrisk::portfolio::OptimizationRequest &request) {
            return quantrisk::portfolio::efficient_frontier(inputs, targets, request);
        },
        py::arg("inputs"), py::arg("target_returns"), py::arg("request"));
    portfolio.def("maximum_sharpe", &quantrisk::portfolio::maximum_sharpe, py::arg("inputs"),
                  py::arg("request"));
    py::class_<quantrisk::portfolio::RiskParitySolution>(portfolio, "RiskParitySolution")
        .def_readonly("assets", &quantrisk::portfolio::RiskParitySolution::assets)
        .def_readonly("weights", &quantrisk::portfolio::RiskParitySolution::weights)
        .def_readonly("variance", &quantrisk::portfolio::RiskParitySolution::variance)
        .def_readonly("volatility", &quantrisk::portfolio::RiskParitySolution::volatility)
        .def_readonly("contributions", &quantrisk::portfolio::RiskParitySolution::contributions)
        .def_readonly("max_contribution_gap",
                      &quantrisk::portfolio::RiskParitySolution::max_contribution_gap)
        .def_readonly("cycles", &quantrisk::portfolio::RiskParitySolution::cycles)
        .def_readonly("converged", &quantrisk::portfolio::RiskParitySolution::converged)
        .def_readonly("positive_definite",
                      &quantrisk::portfolio::RiskParitySolution::positive_definite)
        .def_readonly("note", &quantrisk::portfolio::RiskParitySolution::note);
    portfolio.def(
        "risk_parity",
        [](const std::vector<double> &covariance, const std::int64_t assets) {
            return quantrisk::portfolio::risk_parity(covariance, assets);
        },
        py::arg("covariance"), py::arg("assets"));
    portfolio.def(
        "risk_parity",
        [](const std::vector<double> &covariance, const std::int64_t assets,
           const std::vector<double> &budget) {
            return quantrisk::portfolio::risk_parity(covariance, assets, budget);
        },
        py::arg("covariance"), py::arg("assets"), py::arg("starting_weights"));
    py::enum_<quantrisk::portfolio::LpStatus>(portfolio, "LpStatus")
        .value("OPTIMAL", quantrisk::portfolio::LpStatus::Optimal)
        .value("INFEASIBLE", quantrisk::portfolio::LpStatus::Infeasible)
        .value("UNBOUNDED", quantrisk::portfolio::LpStatus::Unbounded)
        .value("NUMERICAL_FAILURE", quantrisk::portfolio::LpStatus::NumericalFailure)
        .export_values();

    py::class_<quantrisk::portfolio::LinearProgramResult>(portfolio, "LinearProgramResult")
        .def_readonly("status", &quantrisk::portfolio::LinearProgramResult::status)
        .def_readonly("values", &quantrisk::portfolio::LinearProgramResult::values)
        .def_readonly("objective", &quantrisk::portfolio::LinearProgramResult::objective)
        .def_readonly("pivots", &quantrisk::portfolio::LinearProgramResult::pivots)
        .def_readonly("residual", &quantrisk::portfolio::LinearProgramResult::residual)
        .def_readonly("dual_gap", &quantrisk::portfolio::LinearProgramResult::dual_gap)
        .def_readonly("note", &quantrisk::portfolio::LinearProgramResult::note);
    portfolio.def("solve_linear_program", &quantrisk::portfolio::solve_linear_program,
                  py::arg("objective"), py::arg("constraint_rows"), py::arg("rhs"),
                  py::arg("variables"), py::arg("constraints"));

    py::class_<quantrisk::portfolio::CvarRequest>(portfolio, "CvarRequest")
        .def(py::init<>())
        .def_readwrite("assets", &quantrisk::portfolio::CvarRequest::assets)
        .def_readwrite("scenarios", &quantrisk::portfolio::CvarRequest::scenarios)
        .def_readwrite("scenario_returns", &quantrisk::portfolio::CvarRequest::scenario_returns)
        .def_readwrite("expected_returns", &quantrisk::portfolio::CvarRequest::expected_returns)
        .def_readwrite("confidence", &quantrisk::portfolio::CvarRequest::confidence)
        .def_readwrite("target_return", &quantrisk::portfolio::CvarRequest::target_return);

    py::class_<quantrisk::portfolio::CvarSolution>(portfolio, "CvarSolution")
        .def_readonly("weights", &quantrisk::portfolio::CvarSolution::weights)
        .def_readonly("alpha", &quantrisk::portfolio::CvarSolution::alpha)
        .def_readonly("cvar", &quantrisk::portfolio::CvarSolution::cvar)
        .def_readonly("recomputed_cvar", &quantrisk::portfolio::CvarSolution::recomputed_cvar)
        .def_readonly("budget_residual", &quantrisk::portfolio::CvarSolution::budget_residual)
        .def_readonly("weight_bound_violation",
                      &quantrisk::portfolio::CvarSolution::weight_bound_violation)
        .def_readonly("target_residual", &quantrisk::portfolio::CvarSolution::target_residual)
        .def_readonly("pivots", &quantrisk::portfolio::CvarSolution::pivots)
        .def_readonly("status", &quantrisk::portfolio::CvarSolution::status)
        .def_readonly("solved", &quantrisk::portfolio::CvarSolution::solved)
        .def_readonly("certified", &quantrisk::portfolio::CvarSolution::certified)
        .def_readonly("note", &quantrisk::portfolio::CvarSolution::note);
    portfolio.def("minimise_cvar", &quantrisk::portfolio::minimise_cvar, py::arg("request"));
    // --- stress: factors, exposures, scenarios, attribution --------------
    py::module_ stress = module.def_submodule("stress", "Scenario and stress engine (C++20 core).");
    namespace s = quantrisk::stress;

    py::enum_<s::FactorClass>(stress, "FactorClass")
        .value("equity_index", s::FactorClass::equity_index)
        .value("rate", s::FactorClass::rate)
        .value("volatility", s::FactorClass::volatility)
        .value("credit_spread", s::FactorClass::credit_spread)
        .export_values();

    py::enum_<s::ScenarioKind>(stress, "ScenarioKind")
        .value("deterministic", s::ScenarioKind::deterministic)
        .value("historical", s::ScenarioKind::historical)
        .value("monte_carlo", s::ScenarioKind::monte_carlo)
        .export_values();

    py::class_<s::RiskFactor>(stress, "RiskFactor")
        .def(py::init<>())
        .def(py::init<const std::string &, s::FactorClass, quantrisk::Real, const std::string &>(),
             py::arg("id"), py::arg("asset_class"), py::arg("level"), py::arg("units"))
        .def_readwrite("id", &s::RiskFactor::id)
        .def_readwrite("asset_class", &s::RiskFactor::asset_class)
        .def_readwrite("level", &s::RiskFactor::level)
        .def_readwrite("units", &s::RiskFactor::units);

    py::class_<s::FactorSet>(stress, "FactorSet")
        .def(py::init<>())
        .def_readwrite("factors", &s::FactorSet::factors)
        .def("index_of", &s::FactorSet::index_of, py::arg("id"))
        .def("size", &s::FactorSet::size);

    py::class_<s::ExposureVector>(stress, "ExposureVector")
        .def(py::init<>())
        .def_readwrite("delta", &s::ExposureVector::delta)
        .def_readwrite("gamma", &s::ExposureVector::gamma)
        .def_readwrite("duration", &s::ExposureVector::duration)
        .def_readwrite("vega", &s::ExposureVector::vega)
        .def_readwrite("credit", &s::ExposureVector::credit)
        .def("size", &s::ExposureVector::size)
        .def("empty", &s::ExposureVector::empty);

    py::class_<s::Position>(stress, "Position")
        .def(py::init<>())
        .def_readwrite("name", &s::Position::name)
        .def_readwrite("exposures", &s::Position::exposures);

    py::class_<s::Portfolio>(stress, "Portfolio")
        .def(py::init<>())
        .def_readwrite("factors", &s::Portfolio::factors)
        .def_readwrite("positions", &s::Portfolio::positions)
        .def("aggregate", &s::Portfolio::aggregate);

    py::class_<s::Shock>(stress, "Shock")
        .def(py::init<>())
        .def(py::init<const std::string &, quantrisk::Real, quantrisk::Real>(),
             py::arg("factor_id"), py::arg("relative") = 0.0, py::arg("absolute") = 0.0)
        .def_readwrite("factor_id", &s::Shock::factor_id)
        .def_readwrite("relative", &s::Shock::relative)
        .def_readwrite("absolute", &s::Shock::absolute);

    py::class_<s::DistributionShift>(stress, "DistributionShift")
        .def(py::init<>())
        .def_readwrite("volatility_multiplier", &s::DistributionShift::volatility_multiplier)
        .def_readwrite("correlation_increment", &s::DistributionShift::correlation_increment);

    py::class_<s::Scenario>(stress, "Scenario")
        .def(py::init<>())
        .def_readwrite("name", &s::Scenario::name)
        .def_readwrite("kind", &s::Scenario::kind)
        .def_readwrite("assumptions", &s::Scenario::assumptions)
        .def_readwrite("shocks", &s::Scenario::shocks)
        .def_readwrite("distribution", &s::Scenario::distribution)
        .def_readwrite("seed", &s::Scenario::seed)
        .def_readwrite("paths", &s::Scenario::paths)
        .def_readwrite("horizon", &s::Scenario::horizon);

    py::class_<s::FactorContribution>(stress, "FactorContribution")
        .def_readonly("factor_id", &s::FactorContribution::factor_id)
        .def_readonly("asset_class", &s::FactorContribution::asset_class)
        .def_readonly("relative_move", &s::FactorContribution::relative_move)
        .def_readonly("absolute_move", &s::FactorContribution::absolute_move)
        .def_readonly("linear", &s::FactorContribution::linear)
        .def_readonly("convexity", &s::FactorContribution::convexity)
        .def_readonly("rate", &s::FactorContribution::rate)
        .def_readonly("volatility", &s::FactorContribution::volatility)
        .def_readonly("credit", &s::FactorContribution::credit)
        .def("total", &s::FactorContribution::total);

    py::class_<s::PositionContribution>(stress, "PositionContribution")
        .def_readonly("name", &s::PositionContribution::name)
        .def_readonly("pnl", &s::PositionContribution::pnl);

    py::class_<s::ScenarioResult>(stress, "ScenarioResult")
        .def_readonly("scenario_name", &s::ScenarioResult::scenario_name)
        .def_readonly("kind", &s::ScenarioResult::kind)
        .def_readonly("assumptions", &s::ScenarioResult::assumptions)
        .def_readonly("horizon", &s::ScenarioResult::horizon)
        .def_readonly("pnl_change", &s::ScenarioResult::pnl_change)
        .def_readonly("by_factor", &s::ScenarioResult::by_factor)
        .def_readonly("by_position", &s::ScenarioResult::by_position)
        .def_readonly("factor_attribution_residual",
                      &s::ScenarioResult::factor_attribution_residual)
        .def_readonly("position_attribution_residual",
                      &s::ScenarioResult::position_attribution_residual)
        .def_readonly("has_risk_metrics", &s::ScenarioResult::has_risk_metrics)
        .def_readonly("base_volatility", &s::ScenarioResult::base_volatility)
        .def_readonly("stressed_volatility", &s::ScenarioResult::stressed_volatility)
        .def_readonly("base_var", &s::ScenarioResult::base_var)
        .def_readonly("stressed_var", &s::ScenarioResult::stressed_var)
        .def_readonly("base_es", &s::ScenarioResult::base_es)
        .def_readonly("stressed_es", &s::ScenarioResult::stressed_es)
        .def_readonly("var_change", &s::ScenarioResult::var_change)
        .def_readonly("var_change_from_level", &s::ScenarioResult::var_change_from_level)
        .def_readonly("var_change_from_distribution",
                      &s::ScenarioResult::var_change_from_distribution)
        .def_readonly("var_decomposition_residual", &s::ScenarioResult::var_decomposition_residual)
        .def_readonly("es_change", &s::ScenarioResult::es_change)
        .def_readonly("volatility_change", &s::ScenarioResult::volatility_change)
        .def_readonly("var_components_stressed", &s::ScenarioResult::var_components_stressed)
        .def_readonly("var_component_residual", &s::ScenarioResult::var_component_residual)
        .def_readonly("note", &s::ScenarioResult::note);

    stress.def(
        "run_scenario",
        [](const s::Portfolio &portfolio, const s::Scenario &scenario,
           const std::vector<double> &factor_move_covariance, const double confidence) {
            return s::run_scenario(portfolio, scenario, factor_move_covariance, confidence);
        },
        py::arg("portfolio"), py::arg("scenario"),
        py::arg("factor_move_covariance") = std::vector<double>{}, py::arg("confidence") = 0.95);

    stress.def(
        "shift_covariance",
        [](const std::vector<double> &covariance, const quantrisk::Count assets,
           const s::DistributionShift &shift) {
            std::string note;
            std::vector<quantrisk::Real> out = s::shift_covariance(covariance, assets, shift, note);
            return std::make_tuple(out, note);
        },
        py::arg("covariance"), py::arg("assets"), py::arg("shift"));

    py::class_<s::ScenarioSample>(stress, "ScenarioSample")
        .def_readonly("moves", &s::ScenarioSample::moves)
        .def_readonly("paths", &s::ScenarioSample::paths)
        .def_readonly("assets", &s::ScenarioSample::assets)
        .def_readonly("seed", &s::ScenarioSample::seed)
        .def_readonly("note", &s::ScenarioSample::note);

    py::class_<s::FactorSummary>(stress, "FactorSummary")
        .def_readonly("factor_id", &s::FactorSummary::factor_id)
        .def_readonly("mean_contribution", &s::FactorSummary::mean_contribution)
        .def_readonly("worst_contribution", &s::FactorSummary::worst_contribution);

    py::class_<s::ScenarioSetResult>(stress, "ScenarioSetResult")
        .def_readonly("scenario_name", &s::ScenarioSetResult::scenario_name)
        .def_readonly("kind", &s::ScenarioSetResult::kind)
        .def_readonly("assumptions", &s::ScenarioSetResult::assumptions)
        .def_readonly("generator", &s::ScenarioSetResult::generator)
        .def_readonly("scenarios", &s::ScenarioSetResult::scenarios)
        .def_readonly("pnl", &s::ScenarioSetResult::pnl)
        .def_readonly("mean_pnl", &s::ScenarioSetResult::mean_pnl)
        .def_readonly("volatility", &s::ScenarioSetResult::volatility)
        .def_readonly("worst_pnl", &s::ScenarioSetResult::worst_pnl)
        .def_readonly("best_pnl", &s::ScenarioSetResult::best_pnl)
        .def_readonly("var", &s::ScenarioSetResult::var)
        .def_readonly("es", &s::ScenarioSetResult::es)
        .def_readonly("by_position", &s::ScenarioSetResult::by_position)
        .def_readonly("by_factor", &s::ScenarioSetResult::by_factor)
        .def_readonly("position_attribution_residual",
                      &s::ScenarioSetResult::position_attribution_residual)
        .def_readonly("factor_attribution_residual",
                      &s::ScenarioSetResult::factor_attribution_residual)
        .def_readonly("note", &s::ScenarioSetResult::note);

    stress.def(
        "sample_factor_moves",
        [](const std::vector<double> &covariance, const quantrisk::Count assets,
           const quantrisk::Count paths, const quantrisk::Seed seed) {
            return s::sample_factor_moves(covariance, assets, paths, seed);
        },
        py::arg("covariance"), py::arg("assets"), py::arg("paths"), py::arg("seed"));

    stress.def(
        "run_historical_scenarios",
        [](const s::Portfolio &portfolio, const s::Scenario &scenario,
           const std::vector<double> &observed_moves, const quantrisk::Count observations,
           const double confidence) {
            return s::run_historical_scenarios(portfolio, scenario, observed_moves, observations,
                                               confidence);
        },
        py::arg("portfolio"), py::arg("scenario"), py::arg("observed_moves"),
        py::arg("observations"), py::arg("confidence") = 0.95);

    stress.def(
        "run_monte_carlo_scenarios",
        [](const s::Portfolio &portfolio, const s::Scenario &scenario,
           const std::vector<double> &covariance, const quantrisk::Count paths,
           const quantrisk::Seed seed, const double confidence) {
            return s::run_monte_carlo_scenarios(portfolio, scenario, covariance, paths, seed,
                                                confidence);
        },
        py::arg("portfolio"), py::arg("scenario"), py::arg("covariance"), py::arg("paths"),
        py::arg("seed"), py::arg("confidence") = 0.95);
}
