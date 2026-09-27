# Phase 1 Gate Evidence — clean clone run

The gate is `clean clone → install → build → import → test`, executed in a
scratch directory against the committed tree (not the working tree), so nothing
untracked can hide a failure.

> The clone source is written as `$HOME/QuantRisk++` rather than the literal host
> path it used; the path was generalised when this repository was published.

Command (run 2026-09-26, macOS arm64, Apple clang 21.0.0, CMake 4.4.3,
uv 0.11.7, CPython 3.12.14):

```bash
rm -rf /tmp/qr-clone && git clone "$HOME/QuantRisk++" /tmp/qr-clone
cd /tmp/qr-clone
uv sync
uv pip install -e .
.venv/bin/python -c "import quantrisk; print(quantrisk.version(), quantrisk.normal_cdf(0.0), quantrisk.build_metadata())"
cmake --preset dev && cmake --build --preset dev && ctest --preset dev
QUANTRISK_REFERENCE_TOOL=/tmp/qr-clone/build/dev/quantrisk_reference_tool \
  .venv/bin/python -m pytest -q
```

Raw output:

```text
=== clone commit ===
bcadd60756b4
=== uv sync ===
 + scipy==1.18.1
 + six==1.17.0
 + typing-extensions==4.16.0
=== uv pip install -e . ===
Uninstalled 1 package in 0.58ms
Installed 1 package in 1ms
 ~ quantrisk==0.1.0 (from file:///private/tmp/qr-clone)
=== import ===
version 0.1.0
normal_cdf(0.0) = 0.5
metadata {'version': '0.1.0', 'git_commit': 'bcadd60756b4', 'compiler': 'AppleClang 21.0.0.21000334', 'arch': 'arm64', 'os': 'Darwin 27.0.0', 'build_type': 'Release', 'cxx_standard': 'C++20', 'cxx_flags': '(none)'}
=== cmake configure/build/ctest ===

100% tests passed out of 31

Total Test time (real) =   0.40 sec
=== pytest ===
.........................................                                [100%]
41 passed in 32.80s
```

Notes:

- `git_commit` in the metadata is the cloned commit, which is what makes the
  artifact chain in `docs/validation_protocol.md` §5 traceable.
- `cxx_flags: "(none)"` is the honest value for this build: no extra
  `CMAKE_CXX_FLAGS` were set, and `CMAKE_BUILD_TYPE=Release` contributes its
  own `-O3` through the per-config variable that the toolchain fills in.
- The 32.8 s pytest run includes the one-time build triggered by the editable
  install path; the steady-state run is 0.4 s.
