cmake_minimum_required(VERSION 3.26)

project(quantrisk
  VERSION 0.1.0
  DESCRIPTION "Reproducible C++/Python engine for stochastic pricing, Monte Carlo, portfolio risk and stress testing"
  LANGUAGES CXX)

include(FetchContent)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# A wheel build (scikit-build-core) only needs the library and the extension
# module; the C++ test suite belongs to the CMake/CTest developer path.
if(SKBUILD OR skbuild OR DEFINED ENV{SKBUILD})
  set(QUANTRISK_DEFAULT_BUILD_TESTS OFF)
else()
  set(QUANTRISK_DEFAULT_BUILD_TESTS ON)
endif()

option(QUANTRISK_BUILD_TESTS "Build the Catch2 C++ test suite" ${QUANTRISK_DEFAULT_BUILD_TESTS})
option(QUANTRISK_BUILD_BINDINGS "Build the pybind11 Python extension module" ON)

# --------------------------------------------------------------------------
# Reproducibility metadata (docs/validation_protocol.md §3): compiler, arch,
# commit and flags are part of every artifact, so they are captured at
# configure time and baked into the library.
# --------------------------------------------------------------------------
find_package(Git QUIET)
set(QUANTRISK_GIT_COMMIT "unknown")
if(GIT_FOUND AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/.git")
  execute_process(
    COMMAND ${GIT_EXECUTABLE} rev-parse --short=12 HEAD
    OUTPUT_VARIABLE quantrisk_git_commit
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET)
  if(quantrisk_git_commit)
    set(QUANTRISK_GIT_COMMIT "${quantrisk_git_commit}")
  endif()
endif()

set(QUANTRISK_VERSION "${PROJECT_VERSION}")
set(QUANTRISK_COMPILER "${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
set(QUANTRISK_ARCH "${CMAKE_SYSTEM_PROCESSOR}")
set(QUANTRISK_OS "${CMAKE_SYSTEM_NAME} ${CMAKE_SYSTEM_VERSION}")
set(QUANTRISK_BUILD_TYPE "${CMAKE_BUILD_TYPE}")
set(QUANTRISK_CXX_STANDARD "C++${CMAKE_CXX_STANDARD}")
set(QUANTRISK_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CMAKE_CXX_FLAGS_${CMAKE_BUILD_TYPE}}")
string(STRIP "${QUANTRISK_CXX_FLAGS}" QUANTRISK_CXX_FLAGS)
if(NOT QUANTRISK_CXX_FLAGS)
  set(QUANTRISK_CXX_FLAGS "(none)")
endif()

configure_file(
  "${CMAKE_CURRENT_SOURCE_DIR}/cmake/quantrisk_build_config.hpp.in"
  "${CMAKE_CURRENT_BINARY_DIR}/generated/quantrisk/core/build_config.hpp"
  @ONLY)

# --------------------------------------------------------------------------
# C++20 numerical core
# --------------------------------------------------------------------------
add_library(quantrisk_core STATIC
  cpp/src/core/rng.cpp
  cpp/src/core/statistics.cpp
  cpp/src/core/version.cpp
  cpp/src/math/normal.cpp
  cpp/src/pricing/black_scholes.cpp
  cpp/src/pricing/binomial_crr.cpp
  cpp/src/pricing/finite_differences.cpp
  cpp/src/pricing/path_dependent.cpp
  cpp/src/monte_carlo/path_dependent.cpp
  cpp/src/stochastic/gbm.cpp
  cpp/src/monte_carlo/engine.cpp
  cpp/src/stochastic/heston.cpp)

target_include_directories(quantrisk_core PUBLIC
  "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/cpp/include>"
  "$<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/generated>")

target_compile_features(quantrisk_core PUBLIC cxx_std_20)

if(MSVC)
  target_compile_options(quantrisk_core PRIVATE /W4)
else()
  target_compile_options(quantrisk_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

# --------------------------------------------------------------------------
# Reference-value tool: the Python/C++ consistency test compares the pybind11
# results against this program's stdout, which pins the binding boundary rather
# than re-testing the formulas.
# --------------------------------------------------------------------------
add_executable(quantrisk_reference_tool cpp/src/tools/dump_reference.cpp)
target_link_libraries(quantrisk_reference_tool PRIVATE quantrisk_core)
if(MSVC)
  target_compile_options(quantrisk_reference_tool PRIVATE /W4)
else()
  target_compile_options(quantrisk_reference_tool PRIVATE -Wall -Wextra -Wpedantic)
endif()
set_target_properties(quantrisk_reference_tool PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

# --------------------------------------------------------------------------
# C++ tests: Catch2 (pinned tag) registered with CTest
# --------------------------------------------------------------------------
if(QUANTRISK_BUILD_TESTS)
  FetchContent_Declare(Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.8.1
    GIT_SHALLOW TRUE)
  FetchContent_MakeAvailable(Catch2)
  list(APPEND CMAKE_MODULE_PATH "${catch2_SOURCE_DIR}/extras")

  include(CTest)
  include(Catch)

  add_executable(quantrisk_tests
    tests/cpp/test_validation.cpp
    tests/cpp/test_rng.cpp
    tests/cpp/test_statistics.cpp
    tests/cpp/test_normal.cpp
    tests/cpp/test_build_info.cpp
    tests/cpp/test_black_scholes.cpp
    tests/cpp/test_greeks.cpp
    tests/cpp/test_binomial.cpp
    tests/cpp/test_gbm.cpp
    tests/cpp/test_monte_carlo.cpp
    tests/cpp/test_path_dependent.cpp
    tests/cpp/test_heston.cpp)

  target_link_libraries(quantrisk_tests PRIVATE quantrisk_core Catch2::Catch2WithMain)

  catch_discover_tests(quantrisk_tests)

  add_test(NAME reference_tool_emits_json
           COMMAND quantrisk_reference_tool)
  set_tests_properties(reference_tool_emits_json PROPERTIES
    PASS_REGULAR_EXPRESSION "\"version\":")
endif()

# --------------------------------------------------------------------------
# Python extension module (pybind11)
# --------------------------------------------------------------------------
if(QUANTRISK_BUILD_BINDINGS)
  if(DEFINED ENV{VIRTUAL_ENV})
    set(Python_ROOT_DIR "$ENV{VIRTUAL_ENV}")
  endif()
  find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

  # Prefer the pybind11 installed in the active Python environment (this is how
  # a scikit-build-core isolated build finds it); fall back to a pinned fetch
  # so a bare `cmake --preset dev` works without a virtualenv.
  execute_process(
    COMMAND ${Python_EXECUTABLE} -m pybind11 --cmakedir
    OUTPUT_VARIABLE quantrisk_pybind11_cmake_dir
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET)
  if(quantrisk_pybind11_cmake_dir)
    list(APPEND CMAKE_PREFIX_PATH "${quantrisk_pybind11_cmake_dir}")
  endif()

  find_package(pybind11 CONFIG QUIET)
  if(NOT pybind11_FOUND)
    message(STATUS "pybind11 not provided by ${Python_EXECUTABLE}; fetching v2.13.6")
    FetchContent_Declare(pybind11
      GIT_REPOSITORY https://github.com/pybind/pybind11.git
      GIT_TAG v2.13.6
      GIT_SHALLOW TRUE)
    FetchContent_MakeAvailable(pybind11)
  endif()

  pybind11_add_module(_quantrisk bindings/python_bindings.cpp)
  target_link_libraries(_quantrisk PRIVATE quantrisk_core)

  # `cmake --build` puts the module next to the pure-Python package inside the
  # build tree, so the CMake developer path can import it with
  # PYTHONPATH=build/<preset>/python.
  set_target_properties(_quantrisk PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/python/quantrisk")

  install(TARGETS _quantrisk LIBRARY DESTINATION quantrisk)
endif()
