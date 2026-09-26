#pragma once

#include <string>

#include "quantrisk/core/types.hpp"

namespace quantrisk {

/// Build-time metadata recorded with every experiment and benchmark artifact
/// (docs/validation_protocol.md §3). Values are injected by CMake into
/// `quantrisk/core/build_config.hpp`.
struct BuildMetadata {
    std::string version;
    std::string git_commit;
    std::string compiler;
    std::string arch;
    std::string os;
    std::string build_type;
    std::string cxx_standard;
    std::string cxx_flags;
};

/// Library version, e.g. "0.1.0".
const std::string &version();

BuildMetadata build_metadata();

} // namespace quantrisk
