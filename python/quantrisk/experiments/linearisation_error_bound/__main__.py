"""`uv run python -m quantrisk.experiments.linearisation_error_bound [--out DIR]`."""

import sys

from quantrisk.experiments.linearisation_error_bound import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
