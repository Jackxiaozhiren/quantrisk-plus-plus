#pragma once

#include <string>
#include <vector>

#include "quantrisk/core/types.hpp"

namespace quantrisk::stress {

/// What a risk factor actually is, which decides how a shock is read.
///
/// The distinction that matters is not the economics but the units: an equity index
/// is shocked by a *relative* move (−20 % of its level, whatever the level is), while
/// a rate, a volatility or a credit spread is shocked by an *absolute* move (+200 bp is
/// +0.02 whether the curve sits at 3 % or 5 %). Getting this backwards is the single
/// most common way a stress library produces a number that looks plausible and is
/// wrong, so the class is carried on the factor rather than inferred at the call site.
enum class FactorClass {
    equity_index,  ///< shocked relatively; carries delta and gamma
    rate,          ///< shocked absolutely, in decimal yield units; carries duration
    volatility,    ///< shocked absolutely, in annualised-vol units; carries vega
    credit_spread, ///< shocked absolutely, in decimal spread units
};

// python: internal -- enum spelling for C++ diagnostics and messages; pybind binds FactorClass.
[[nodiscard]] const char *to_string(FactorClass asset_class);

/// A named factor at a quoted level.
///
/// `level` is carried for reporting and for the relative-to-absolute conversion in
/// `Shock::relative_from_absolute`; no P&L depends on it, because the exposures are
/// already quoted per unit move. That is deliberate: a stress result that changed when
/// only the quoted level changed would be reporting a re-annotation, not a shock.
struct RiskFactor {
    std::string id;
    FactorClass asset_class = FactorClass::equity_index;
    Real level = 0.0;
    std::string units; ///< free text: "index points", "decimal p.a.", "bp"
};

/// The factor universe a portfolio is expressed against.
///
/// Sensitivities are positionally aligned with `factors`, so an exposure vector and a
/// factor set that came from different places cannot be multiplied together silently:
/// `ExposureVector::validate_against` checks the length, and `index_of` resolves the
/// ids a shock names.
struct FactorSet {
    std::vector<RiskFactor> factors;

    [[nodiscard]] Count size() const { return static_cast<Count>(factors.size()); }
    [[nodiscard]] Count index_of(const std::string &id) const;
};

/// One position's sensitivity to every factor, split by the order of the move it
/// responds to. Every vector is either empty or exactly `FactorSet::size()` long.
struct ExposureVector {
    /// Currency P&L per unit *relative* move in the factor: a 100 % move.
    std::vector<Real> delta;
    /// Currency P&L per unit relative move squared, with the ½ already absorbed into
    /// the quoted number so the mapping reads `gamma_i * s_i^2` without a stray factor.
    /// Convention is stated here because the Black-Scholes gamma a caller would derive
    /// this from does *not* carry the ½, and the reconciliation test depends on it.
    std::vector<Real> gamma;
    /// Currency P&L per unit *absolute* move in a rate.
    std::vector<Real> duration;
    /// Currency P&L per unit absolute move in a volatility level.
    std::vector<Real> vega;
    /// Currency P&L per unit absolute move in a credit spread.
    std::vector<Real> credit;

    [[nodiscard]] Count size() const { return static_cast<Count>(delta.size()); }
    void validate_against(const FactorSet &factors, const char *owner) const;
    [[nodiscard]] bool empty() const;
};

/// A named position, expressed only through its exposures.
struct Position {
    std::string name;
    ExposureVector exposures;
};

/// A portfolio is a list of positions plus the factors they are quoted against.
///
/// There is deliberately no instrument list and no price here. The stress layer maps
/// exposures to P&L, which is what makes it independent of the pricing layer — and is
/// also its central approximation, quantified rather than hidden by
/// `tests/cpp/test_stress_engine.cpp`, which re-prices an option book through the
/// Black-Scholes engine and reports the gap.
struct Portfolio {
    FactorSet factors;
    std::vector<Position> positions;

    /// Sum of the position exposures. Exact, since every term is a per-factor addition.
    [[nodiscard]] ExposureVector aggregate() const;
};

} // namespace quantrisk::stress
