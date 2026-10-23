"""`uv run python -m quantrisk.experiments.var_backtesting [--out DIR]`."""

import sys

from quantrisk.experiments.var_backtesting import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
