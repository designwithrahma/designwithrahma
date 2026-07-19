from __future__ import annotations

import html
import json
import math
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "contributions.json"
OUTPUT_FILE = PROJECT_ROOT / "contrib-heatmap.svg"

CELL_SIZE = 12
CELL_GAP = 4
CELL_STEP = CELL_SIZE + CELL_GAP

GRAPH_X = 56
GRAPH_Y = 48

TOP_PADDING = 18
RIGHT_PADDING = 30
BOTTOM_PADDING = 92

DAY_LABELS = {
    1: "Mon",
    3: "Wed",
    5: "Fri",
}


def load_contribution_data() -> dict[str, Any]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "data/contributions.json not found. "
            "Run python scripts/fetch_contributions.py first."
        )

    data = json.loads(
        INPUT_FILE.read_text(encoding="utf-8")
    )

    if not isinstance(data, dict):
        raise ValueError(
            "Contribution JSON root must be an object."
        )

    days = data.get("days")

    if not isinstance(days, list) or not days:
        raise ValueError(
            "Contribution JSON does not contain valid days."
        )

    return data


def clamp_level(value: Any) -> int:
    try:
        level = int(value)
    except (TypeError, ValueError):
        return 0

    return max(0, min(level, 4))


def format_number(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def create_day_cells(
    days: list[dict[str, Any]],
    leading_cells: int,
) -> tuple[str, int]:
    cells: list[str] = []

    total_slots = leading_cells + len(days)
    week_count = math.ceil(total_slots / 7)

    for day_index, day in enumerate(days):
        slot_index = leading_cells + day_index

        week_index = slot_index // 7
        weekday_index = slot_index % 7

        x_position = GRAPH_X + week_index * CELL_STEP
        y_position = GRAPH_Y + weekday_index * CELL_STEP

        level = clamp_level(day.get("level", 0))

        raw_count = day.get("count", 0)

        try:
            count = max(0, int(raw_count))
        except (TypeError, ValueError):
            count = 0

        raw_date = str(day.get("date", "Unknown date"))

        escaped_date = html.escape(raw_date)
        escaped_title = html.escape(
            f"{count} contribution"
            f"{'' if count == 1 else 's'} on {raw_date}"
        )

        animation_delay = (
            week_index * 0.012
            + weekday_index * 0.008
        )

        cells.append(
            f"""
            <rect
                class="day-cell level-{level}"
                x="{x_position}"
                y="{y_position}"
                width="{CELL_SIZE}"
                height="{CELL_SIZE}"
                rx="3"
                data-date="{escaped_date}"
                data-count="{count}"
                style="animation-delay: {animation_delay:.3f}s"
            >
                <title>{escaped_title}</title>
            </rect>
            """
        )

    return "".join(cells), week_count


def create_day_labels() -> str:
    labels: list[str] = []

    for weekday_index, label in DAY_LABELS.items():
        y_position = (
            GRAPH_Y
            + weekday_index * CELL_STEP
            + CELL_SIZE - 2
        )

        labels.append(
            f"""
            <text
                class="axis-label"
                x="8"
                y="{y_position}"
            >{label}</text>
            """
        )

    return "".join(labels)


def create_month_labels(
    days: list[dict[str, Any]],
    leading_cells: int,
) -> str:
    labels: list[str] = []

    previous_month: str | None = None
    previous_label_week = -10

    for day_index, day in enumerate(days):
        raw_date = day.get("date")

        if not isinstance(raw_date, str):
            continue

        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError:
            continue

        month_key = parsed_date.strftime("%Y-%m")

        if month_key == previous_month:
            continue

        slot_index = leading_cells + day_index
        week_index = slot_index // 7

        # Avoid month names overlapping when a month
        # starts very close to the previous label.
        if week_index - previous_label_week < 3:
            previous_month = month_key
            continue

        x_position = GRAPH_X + week_index * CELL_STEP

        labels.append(
            f"""
            <text
                class="month-label"
                x="{x_position}"
                y="30"
            >{parsed_date.strftime("%b")}</text>
            """
        )

        previous_month = month_key
        previous_label_week = week_index

    return "".join(labels)


def create_legend(
    graph_width: int,
    graph_bottom: int,
) -> str:
    legend_x = GRAPH_X + graph_width - 156
    legend_y = graph_bottom + 24

    legend_parts = [
        f"""
        <text
            class="legend-label"
            x="{legend_x}"
            y="{legend_y + 10}"
        >Less</text>
        """
    ]

    first_cell_x = legend_x + 38

    for level in range(5):
        x_position = first_cell_x + level * 17

        legend_parts.append(
            f"""
            <rect
                class="legend-cell level-{level}"
                x="{x_position}"
                y="{legend_y}"
                width="11"
                height="11"
                rx="3"
            />
            """
        )

    legend_parts.append(
        f"""
        <text
            class="legend-label"
            x="{first_cell_x + 90}"
            y="{legend_y + 10}"
        >More</text>
        """
    )

    return "".join(legend_parts)


def create_stats(
    summary: dict[str, Any],
    graph_bottom: int,
) -> str:
    total = format_number(
        summary.get("total_contributions", 0)
    )

    active_days = format_number(
        summary.get("active_days", 0)
    )

    current_streak = format_number(
        summary.get("current_streak", 0)
    )

    longest_streak = format_number(
        summary.get("longest_streak", 0)
    )

    stats_y = graph_bottom + 63

    return f"""
        <g class="stats">
            <text
                class="stat-primary"
                x="{GRAPH_X}"
                y="{stats_y}"
            >{total} contributions</text>

            <text
                class="stat-secondary"
                x="{GRAPH_X + 190}"
                y="{stats_y}"
            >{active_days} active days</text>

            <text
                class="stat-secondary"
                x="{GRAPH_X + 360}"
                y="{stats_y}"
            >Current streak: {current_streak}d</text>

            <text
                class="stat-secondary"
                x="{GRAPH_X + 565}"
                y="{stats_y}"
            >Longest: {longest_streak}d</text>
        </g>
    """


def build_svg(data: dict[str, Any]) -> str:
    days = data["days"]
    summary = data.get("summary", {})
    username = html.escape(
        str(data.get("username", "designwithrahma"))
    )

    first_date = date.fromisoformat(days[0]["date"])

    # Python weekday:
    # Monday = 0, Sunday = 6.
    # Heatmap rows:
    # Sunday = 0, Monday = 1.
    leading_cells = (first_date.weekday() + 1) % 7

    day_cells, week_count = create_day_cells(
        days,
        leading_cells,
    )

    graph_width = (
        week_count * CELL_STEP
        - CELL_GAP
    )

    graph_height = (
        7 * CELL_STEP
        - CELL_GAP
    )

    graph_bottom = GRAPH_Y + graph_height

    width = (
        GRAPH_X
        + graph_width
        + RIGHT_PADDING
    )

    height = (
        GRAPH_Y
        + graph_height
        + BOTTOM_PADDING
    )

    month_labels = create_month_labels(
        days,
        leading_cells,
    )

    day_labels = create_day_labels()

    legend = create_legend(
        graph_width,
        graph_bottom,
    )

    stats = create_stats(
        summary,
        graph_bottom,
    )

    return f"""<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
    role="img"
    aria-labelledby="title description"
>
    <title id="title">
        {username} animated GitHub contribution heatmap
    </title>

    <desc id="description">
        GitHub contribution activity for the previous year,
        including total contributions and streak statistics.
    </desc>

    <style>
        .background {{
            fill: #0d1117;
            stroke: #30363d;
            stroke-width: 1;
        }}

        .day-cell {{
            opacity: 0;
            transform-box: fill-box;
            transform-origin: center;
            transform: scale(0.35);
            animation: reveal-cell 0.34s ease-out forwards;
        }}

        .level-0 {{
            fill: #161b22;
        }}

        .level-1 {{
            fill: #0e4429;
        }}

        .level-2 {{
            fill: #006d32;
        }}

        .level-3 {{
            fill: #26a641;
        }}

        .level-4 {{
            fill: #39d353;
        }}

        .axis-label,
        .month-label,
        .legend-label,
        .stat-primary,
        .stat-secondary {{
            font-family:
                "Cascadia Code",
                "SFMono-Regular",
                Consolas,
                "Liberation Mono",
                monospace;
        }}

        .axis-label,
        .month-label,
        .legend-label {{
            fill: #8b949e;
            font-size: 12px;
        }}

        .stat-primary {{
            fill: #c9d1d9;
            font-size: 15px;
            font-weight: 700;
        }}

        .stat-secondary {{
            fill: #8b949e;
            font-size: 13px;
            font-weight: 600;
        }}

        .stats {{
            opacity: 0;
            animation: reveal-text 0.5s ease forwards;
            animation-delay: 0.85s;
        }}

        @keyframes reveal-cell {{
            from {{
                opacity: 0;
                transform: scale(0.35);
            }}

            to {{
                opacity: 1;
                transform: scale(1);
            }}
        }}

        @keyframes reveal-text {{
            from {{
                opacity: 0;
                transform: translateY(6px);
            }}

            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @media (prefers-color-scheme: light) {{
            .background {{
                fill: #ffffff;
                stroke: #d0d7de;
            }}

            .level-0 {{
                fill: #ebedf0;
            }}

            .level-1 {{
                fill: #9be9a8;
            }}

            .level-2 {{
                fill: #40c463;
            }}

            .level-3 {{
                fill: #30a14e;
            }}

            .level-4 {{
                fill: #216e39;
            }}

            .axis-label,
            .month-label,
            .legend-label,
            .stat-secondary {{
                fill: #57606a;
            }}

            .stat-primary {{
                fill: #24292f;
            }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            .day-cell,
            .stats {{
                opacity: 1;
                transform: none;
                animation: none;
            }}
        }}
    </style>

    <rect
        class="background"
        x="0.5"
        y="0.5"
        width="{width - 1}"
        height="{height - 1}"
        rx="14"
    />

    {month_labels}

    {day_labels}

    {day_cells}

    {legend}

    {stats}
</svg>
"""


def main() -> None:
    try:
        contribution_data = load_contribution_data()

        svg_content = build_svg(
            contribution_data
        )

        OUTPUT_FILE.write_text(
            svg_content,
            encoding="utf-8",
        )

        print(
            f"Contribution heatmap created: "
            f"{OUTPUT_FILE}"
        )

    except Exception as error:
        raise SystemExit(
            f"Heatmap generation failed: {error}"
        ) from error


if __name__ == "__main__":
    main()