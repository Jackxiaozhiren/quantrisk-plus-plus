"""Plot helpers. Figures are generated, never hand-edited
(PROJECT_SPEC.md §4), so styling lives here rather than in each script."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # headless and identical on every machine

import matplotlib.pyplot as plt  # noqa: E402


def save_figure(figure: plt.Figure, path: str | Path, *, dpi: int = 130) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target, dpi=dpi, bbox_inches="tight")
    plt.close(figure)
    return target


def log_log_convergence_plot(
    xs: list[float],
    series: dict[str, list[float]],
    *,
    title: str,
    xlabel: str,
    ylabel: str,
    reference_slope: float | None = None,
    path: str | Path,
) -> Path:
    """One line per method on log-log axes, with an optional reference slope."""
    figure, axis = plt.subplots(figsize=(6.0, 4.2))
    for label, values in series.items():
        positive = [(x, v) for x, v in zip(xs, values, strict=True) if x > 0 and v > 0]
        if positive:
            axis.plot([p[0] for p in positive], [p[1] for p in positive], marker="o", label=label)

    if reference_slope is not None and xs:
        positive = [
            (x, v) for x, v in zip(xs, list(series.values())[0], strict=True) if x > 0 and v > 0
        ]
        if positive:
            anchor_x = positive[0][0]
            anchor_y = positive[0][1]
            factor = (2.0 * anchor_x / anchor_x) ** reference_slope
            axis.plot(
                [anchor_x, 2.0 * anchor_x],
                [anchor_y, anchor_y * factor],
                ls="--",
                color="black",
                label=f"slope {reference_slope:g}",
            )

    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True, which="both", alpha=0.3)
    axis.legend(fontsize=8)
    return save_figure(figure, path)


def line_plot(
    xs: list[float],
    series: dict[str, list[float]],
    *,
    title: str,
    xlabel: str,
    ylabel: str,
    path: str | Path,
    log_x: bool = False,
    annotations: dict[str, Any] | None = None,
) -> Path:
    figure, axis = plt.subplots(figsize=(6.0, 4.2))
    for label, values in series.items():
        if len(values) != len(xs):
            raise ValueError(
                f"series {label!r} has {len(values)} points but xs has {len(xs)}; "
                "x and y must come from the same filtered subset"
            )
        axis.plot(xs, values, marker="o", label=label)
    if log_x:
        axis.set_xscale("log")
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True, alpha=0.3)
    axis.legend(fontsize=8)
    for note, (x_fraction, y_fraction) in (annotations or {}).items():
        axis.annotate(note, xy=(x_fraction, y_fraction), xycoords="axes fraction", fontsize=7)
    return save_figure(figure, path)
