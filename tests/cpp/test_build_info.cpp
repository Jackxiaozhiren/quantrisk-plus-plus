#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include <regex>
#include <string>

#include "quantrisk/core/version.hpp"

TEST_CASE("version() reports a semantic version string") {
    const std::string &value = quantrisk::version();
    REQUIRE_FALSE(value.empty());
    CHECK_THAT(value, Catch::Matchers::Matches(R"(^\d+\.\d+\.\d+$)"));
}

TEST_CASE("build metadata is complete and agrees with version()") {
    const quantrisk::BuildMetadata meta = quantrisk::build_metadata();
    CHECK(meta.version == quantrisk::version());
    CHECK_FALSE(meta.git_commit.empty());
    CHECK_FALSE(meta.compiler.empty());
    CHECK_FALSE(meta.arch.empty());
    CHECK_FALSE(meta.os.empty());
    CHECK_FALSE(meta.build_type.empty());
    CHECK(meta.cxx_standard == "C++20");
    CHECK_FALSE(meta.cxx_flags.empty());
}

TEST_CASE("the core really is compiled as C++20") {
#if __cplusplus < 202002L
    FAIL("__cplusplus reports " << __cplusplus << ", expected C++20 or newer");
#else
    SUCCEED();
#endif
}
