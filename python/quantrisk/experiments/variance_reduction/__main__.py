"""`uv run python -m quantrisk.experiments.variance_reduction [--out DIR]`."""

import sys

from quantrisk.experiments.variance_reduction import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
