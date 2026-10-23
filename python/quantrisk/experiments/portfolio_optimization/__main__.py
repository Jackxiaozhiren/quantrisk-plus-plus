"""`uv run python -m quantrisk.experiments.portfolio_optimization [--out DIR]`."""

import sys

from quantrisk.experiments.portfolio_optimization import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
