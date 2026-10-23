"""`uv run python -m quantrisk.experiments.real_data_risk_study [--out DIR]`."""

import sys

from quantrisk.experiments.real_data_risk_study import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
