"""The `-m` entry point: `uv run python -m quantrisk.experiments.stress_testing [--out DIR]`."""

import sys

from quantrisk.experiments.stress_testing import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
