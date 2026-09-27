#include "quantrisk/stress/scenario.hpp"

#include "quantrisk/core/validation.hpp"

namespace quantrisk::stress {

const char *to_string(ScenarioKind kind) {
    switch (kind) {
    case ScenarioKind::deterministic:
        return "deterministic";
    case ScenarioKind::historical:
        return "historical";
    case ScenarioKind::monte_carlo:
        return "monte_carlo";
    }
    return "unknown";
}

Real Shock::relative_from_absolute(Real level) const {
    if (level == 0.0) {
        throw ValidationError("quantrisk: cannot express an absolute move on a factor "
                              "quoted at level zero; the relative move is undefined "
                              "rather than infinite");
    }
    return absolute / level;
}

} // namespace quantrisk::stress
