"""`uv run python -m quantrisk.experiments.fourth_order_crossing_map [--out DIR]`."""

import sys

from quantrisk.experiments.fourth_order_crossing_map import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
