#!/usr/bin/env python3
"""Render an animated GitHub-style contribution heatmap SVG."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT = PROJECT_ROOT / "data" / "contributions.json"
OUTPUT = PROJECT_ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_WIDTH = 30
TOP_LABEL_HEIGHT = 20
TITLEBAR_HEIGHT = 30

BG = "#0a0e14"
BG_TOP = "#0d1420"
FRAME = "#1f6feb"
MUTED = "#7d8590"
ACCENT = "#22d3ee"
GREEN = "#39d353"
GOLD = "#f2cc60"

COLUMN_DELAY = 0.018
ROW_DELAY = 0.045
CELL_DURATION = 0.42


def level_for(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5


def build_grid(days: list[dict[str, Any]]) -> list[list[tuple[str, int, int] | None]]:
    first = dt.date.fromisoformat(days[0]["date"])
    leading = (first.weekday() + 1) % 7
    grid: list[list[tuple[str, int, int] | None]] = []
    column: list[tuple[str, int, int] | None] = [None] * leading

    for item in days:
        day = dt.date.fromisoformat(item["date"])
        weekday = (day.weekday() + 1) % 7
        while len(column) < weekday:
            column.append(None)
        count = max(0, int(item.get("count", 0)))
        column.append((item["date"], count, level_for(count)))
        if len(column) == 7:
            grid.append(column)
            column = []

    if column:
        column.extend([None] * (7 - len(column)))
        grid.append(column)
    return grid


def render(data: dict[str, Any]) -> str:
    days = data["days"]
    grid = build_grid(days)
    column_count = len(grid)
    art_width = column_count * STEP
    art_height = 7 * STEP

    month_labels: list[tuple[int, str]] = []
    seen_months: set[tuple[int, int]] = set()
    for column_index, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            day = dt.date.fromisoformat(cell[0])
            month_key = (day.year, day.month)
            if month_key not in seen_months and day.day <= 7:
                seen_months.add(month_key)
                month_labels.append((column_index, day.strftime("%b")))
            break

    canvas_width = PAD + LEFT_LABEL_WIDTH + art_width + PAD
    stats_height = 88
    canvas_height = TITLEBAR_HEIGHT + TOP_LABEL_HEIGHT + art_height + stats_height + PAD

    css = f"""
@keyframes cell-reveal {{
  0%   {{ opacity: 0; transform: translateY(-6px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
.cell {{ opacity: 0; animation: cell-reveal {CELL_DURATION:.2f}s cubic-bezier(.2,.8,.2,1) both; }}
@media (prefers-reduced-motion: reduce) {{ .cell {{ opacity: 1; animation: none; }} }}
""".strip()

    parts: list[str] = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" '
            f'height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}" '
            'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
            'role="img" aria-labelledby="title description">'
        ),
        '<title id="title">Designwithrahma animated GitHub contribution graph</title>',
        '<desc id="description">A one-year contribution calendar with animated cells and streak statistics.</desc>',
        f'<style>{css}</style>',
        '<defs>',
        f'<linearGradient id="heatmap-background" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/>'
        f'<stop offset="1" stop-color="{BG}"/>'
        '</linearGradient>',
        '</defs>',
        f'<rect width="{canvas_width}" height="{canvas_height}" rx="12" fill="url(#heatmap-background)"/>',
        (
            f'<rect x="0.5" y="0.5" width="{canvas_width - 1}" height="{canvas_height - 1}" '
            f'rx="12" fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>'
        ),
        (
            f'<line x1="0" y1="{TITLEBAR_HEIGHT}" x2="{canvas_width}" y2="{TITLEBAR_HEIGHT}" '
            f'stroke="{FRAME}" stroke-opacity="0.35"/>'
        ),
    ]

    for index, dot_color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(
            f'<circle cx="{PAD + index * 16}" cy="{TITLEBAR_HEIGHT / 2}" r="5" fill="{dot_color}"/>'
        )

    parts.append(
        f'<text x="{canvas_width / 2}" y="{TITLEBAR_HEIGHT / 2 + 4}" fill="{MUTED}" '
        'font-size="12" text-anchor="middle">rahma@github: ~/contributions --graph</text>'
    )

    grid_top = TITLEBAR_HEIGHT + TOP_LABEL_HEIGHT
    grid_left = PAD + LEFT_LABEL_WIDTH

    for column_index, label in month_labels:
        x = grid_left + column_index * STEP
        parts.append(
            f'<text x="{x}" y="{TITLEBAR_HEIGHT + 14}" fill="{MUTED}" font-size="10">{label}</text>'
        )

    for weekday_index, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = grid_top + weekday_index * STEP + CELL * 0.78
        parts.append(
            f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="9">{label}</text>'
        )

    for column_index, column in enumerate(grid):
        x = grid_left + column_index * STEP
        for row_index, cell in enumerate(column):
            if cell is None:
                continue
            date_text, count, level = cell
            y = grid_top + row_index * STEP
            delay = column_index * COLUMN_DELAY + row_index * ROW_DELAY
            plural = "s" if count != 1 else ""
            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{PALETTE[level]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{date_text}: {count} contribution{plural}</title></rect>'
            )

    legend_y = grid_top + art_height + 6
    legend_x = canvas_width - PAD - (len(PALETTE) * (CELL - 1) + 70)
    parts.append(
        f'<text x="{legend_x}" y="{legend_y + CELL * 0.8:.1f}" fill="{MUTED}" '
        'font-size="10" text-anchor="end">Less</text>'
    )
    cursor_x = legend_x + 8
    for color in PALETTE:
        parts.append(
            f'<rect x="{cursor_x}" y="{legend_y}" width="{CELL - 1}" height="{CELL - 1}" '
            f'rx="2.2" fill="{color}"/>'
        )
        cursor_x += CELL
    parts.append(
        f'<text x="{cursor_x + 4}" y="{legend_y + CELL * 0.8:.1f}" fill="{MUTED}" '
        'font-size="10">More</text>'
    )

    separator_y = legend_y + CELL + 14
    parts.append(
        f'<line x1="0" y1="{separator_y}" x2="{canvas_width}" y2="{separator_y}" '
        f'stroke="{FRAME}" stroke-opacity="0.25"/>'
    )

    current = int(data["current_streak"]["length"])
    longest = int(data["longest_streak"]["length"])
    total = int(data["total_contributions"])
    best = data["best_day"]
    date_range = data["range"]

    line_y = separator_y + 24
    parts.append(
        f'<text x="{PAD}" y="{line_y}" font-size="13" fill="{GREEN}">'
        f'<tspan font-weight="700">{total:,}</tspan>'
        f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>'
    )
    parts.append(
        f'<text x="{canvas_width - PAD}" y="{line_y}" font-size="12" fill="{MUTED}" '
        f'text-anchor="end">{date_range["start"]} &#8594; {date_range["end"]}</text>'
    )

    line_y += 24
    parts.append(
        f'<text x="{PAD}" y="{line_y}" font-size="13" fill="{MUTED}">current streak '
        f'<tspan fill="{ACCENT}" font-weight="700">{current} days</tspan>'
        f'<tspan fill="{MUTED}">   &#183;   longest </tspan>'
        f'<tspan fill="{ACCENT}" font-weight="700">{longest} days</tspan></text>'
    )
    parts.append(
        f'<text x="{canvas_width - PAD}" y="{line_y}" font-size="12" fill="{MUTED}" '
        f'text-anchor="end">best day <tspan fill="{GOLD}" font-weight="700">'
        f'{int(best["count"])}</tspan> on {best["date"]}</text>'
    )

    parts.append('</svg>')
    return ''.join(parts)


def main() -> None:
    try:
        data = json.loads(INPUT.read_text(encoding="utf-8"))
        svg = render(data)
        OUTPUT.write_text(svg, encoding="utf-8")
        print(f"wrote {OUTPUT} ({len(svg)} bytes)")
    except Exception as error:
        raise SystemExit(f"Heatmap generation failed: {error}") from error


if __name__ == "__main__":
    main()
