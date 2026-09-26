#include "quantrisk/core/version.hpp"

#include "quantrisk/core/build_config.hpp"

namespace quantrisk {

const std::string &version() {
    static const std::string value = QUANTRISK_VERSION;
    return value;
}

BuildMetadata build_metadata() {
    return BuildMetadata{
        .version = QUANTRISK_VERSION,
        .git_commit = QUANTRISK_GIT_COMMIT,
        .compiler = QUANTRISK_COMPILER,
        .arch = QUANTRISK_ARCH,
        .os = QUANTRISK_OS,
        .build_type = QUANTRISK_BUILD_TYPE,
        .cxx_standard = QUANTRISK_CXX_STANDARD,
        .cxx_flags = QUANTRISK_CXX_FLAGS,
    };
}

} // namespace quantrisk
