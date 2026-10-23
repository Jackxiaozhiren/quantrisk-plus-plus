"""`uv run python -m quantrisk.experiments.monte_carlo_convergence [--out DIR]`."""

import sys

from quantrisk.experiments.monte_carlo_convergence import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
