"""The `-m` entry point: `uv run python -m quantrisk.experiments.restrike_gamma_map [--out DIR]`."""

import sys

from quantrisk.experiments.restrike_gamma_map import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
