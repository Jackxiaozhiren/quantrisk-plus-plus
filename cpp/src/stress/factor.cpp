#include "quantrisk/stress/factor.hpp"

#include <cmath>

#include "quantrisk/core/validation.hpp"

namespace quantrisk::stress {

const char *to_string(FactorClass asset_class) {
    switch (asset_class) {
    case FactorClass::equity_index:
        return "equity_index";
    case FactorClass::rate:
        return "rate";
    case FactorClass::volatility:
        return "volatility";
    case FactorClass::credit_spread:
        return "credit_spread";
    }
    return "unknown";
}

Count FactorSet::index_of(const std::string &id) const {
    for (std::size_t i = 0; i < factors.size(); ++i) {
        if (factors[i].id == id) {
            return static_cast<Count>(i);
        }
    }
    throw ValidationError("quantrisk: stress factor '" + id +
                          "' is not in the portfolio's factor set; a shock to an "
                          "unlisted factor would be silently ignored, which is the one "
                          "failure mode a stress report must not have");
}

void ExposureVector::validate_against(const FactorSet &factors, const char *owner) const {
    Count present = -1;
    for (const std::vector<Real> *block : {&delta, &gamma, &duration, &vega, &credit}) {
        if (block->empty()) {
            continue;
        }
        if (present < 0) {
            present = static_cast<Count>(block->size());
        }
        if (static_cast<Count>(block->size()) != present) {
            throw ValidationError(std::string("quantrisk: ") + owner +
                                  " has sensitivity blocks of different lengths (" +
                                  std::to_string(present) + " and " +
                                  std::to_string(block->size()) + ")");
        }
        for (const Real value : *block) {
            if (!std::isfinite(value)) {
                throw ValidationError(std::string("quantrisk: ") + owner +
                                      " carries a non-finite sensitivity");
            }
        }
    }
    if (present >= 0 && present != factors.size()) {
        throw ValidationError(std::string("quantrisk: ") + owner + " has " +
                              std::to_string(present) + " sensitivities but the factor set lists " +
                              std::to_string(factors.size()) +
                              "; positional alignment is what makes the attribution exact");
    }
}

bool ExposureVector::empty() const {
    return delta.empty() && gamma.empty() && duration.empty() && vega.empty() && credit.empty();
}

ExposureVector Portfolio::aggregate() const {
    if (positions.empty()) {
        throw ValidationError("quantrisk: a portfolio with no positions has nothing to "
                              "stress; refusing to report a confident zero");
    }
    ExposureVector total;
    // A block is only materialised when some position carries it, so a delta-only book
    // does not pay for five vectors it will never read.
    auto accumulate = [&](std::vector<Real> &target, const auto ExposureVector::*member) {
        std::vector<const std::vector<Real> *> blocks;
        for (const Position &position : positions) {
            const std::vector<Real> &block = position.exposures.*member;
            if (block.empty()) {
                continue; // a position genuinely insensitive to this block
            }
            position.exposures.validate_against(factors, position.name.c_str());
            blocks.push_back(&block);
        }
        if (blocks.empty()) {
            return;
        }
        target.assign(static_cast<std::size_t>(factors.size()), 0.0);
        for (const std::vector<Real> *block : blocks) {
            for (std::size_t i = 0; i < block->size(); ++i) {
                target[i] += (*block)[i];
            }
        }
    };
    accumulate(total.delta, &ExposureVector::delta);
    accumulate(total.gamma, &ExposureVector::gamma);
    accumulate(total.duration, &ExposureVector::duration);
    accumulate(total.vega, &ExposureVector::vega);
    accumulate(total.credit, &ExposureVector::credit);
    return total;
}

} // namespace quantrisk::stress
