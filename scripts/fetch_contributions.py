from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "data" / "contributions.json"

USERNAME = "designwithrahma"

CONTRIBUTION_PATTERN = re.compile(
    r"([\d,]+)\s+contributions?",
    re.IGNORECASE,
)


def normalize_text(value: str) -> str:
    """Remove unnecessary spaces from extracted HTML text."""

    return " ".join(value.split())


def extract_count_from_text(value: str) -> int | None:
    """Extract an exact contribution count from GitHub text."""

    normalized = normalize_text(value)
    normalized_lower = normalized.lower()

    if (
        "no contribution" in normalized_lower
        or "0 contribution" in normalized_lower
    ):
        return 0

    if normalized.isdigit():
        return int(normalized)

    match = CONTRIBUTION_PATTERN.search(normalized)

    if match:
        return int(match.group(1).replace(",", ""))

    return None


def parse_contribution_count(
    cell: Tag,
    soup: BeautifulSoup,
) -> int:
    """Read a contribution count from old and new GitHub HTML formats."""

    candidates: list[str] = []

    # Older GitHub formats may store counts directly as attributes.
    for attribute_name in (
        "data-count",
        "aria-label",
        "title",
    ):
        attribute_value = cell.get(attribute_name)

        if isinstance(attribute_value, str):
            candidates.append(attribute_value)

    # Accessible labels can reference hidden tooltip elements.
    for reference_attribute in (
        "aria-describedby",
        "aria-labelledby",
    ):
        referenced_ids = cell.get(reference_attribute)

        if not isinstance(referenced_ids, str):
            continue

        for referenced_id in referenced_ids.split():
            referenced_element = soup.find(id=referenced_id)

            if referenced_element:
                candidates.append(
                    referenced_element.get_text(
                        " ",
                        strip=True,
                    )
                )

    # Current GitHub format commonly uses:
    # <tool-tip for="contribution-cell-id">...</tool-tip>
    cell_id = cell.get("id")

    if isinstance(cell_id, str) and cell_id:
        linked_elements = soup.find_all(
            attrs={"for": cell_id},
        )

        for linked_element in linked_elements:
            candidates.append(
                linked_element.get_text(
                    " ",
                    strip=True,
                )
            )

    # Some versions keep accessible text inside the cell itself.
    direct_text = cell.get_text(
        " ",
        strip=True,
    )

    if direct_text:
        candidates.append(direct_text)

    for candidate in candidates:
        parsed_count = extract_count_from_text(candidate)

        if parsed_count is not None:
            return parsed_count

    return 0


def parse_level(cell: Tag) -> int:
    """Read GitHub contribution intensity level between 0 and 4."""

    raw_level = cell.get("data-level", "0")

    try:
        level = int(str(raw_level))
    except (TypeError, ValueError):
        return 0

    return max(0, min(level, 4))


def calculate_longest_streak(
    days: list[dict[str, Any]],
) -> int:
    longest_streak = 0
    running_streak = 0

    for day in days:
        if day["count"] > 0:
            running_streak += 1
            longest_streak = max(
                longest_streak,
                running_streak,
            )
        else:
            running_streak = 0

    return longest_streak


def calculate_current_streak(
    days: list[dict[str, Any]],
    today: date,
) -> int:
    counts_by_date = {
        date.fromisoformat(day["date"]): day["count"]
        for day in days
    }

    reference_day = today

    # Today may not have a contribution yet.
    # In that case, calculate from yesterday.
    if counts_by_date.get(reference_day, 0) == 0:
        reference_day -= timedelta(days=1)

    streak = 0
    cursor = reference_day

    while counts_by_date.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)

    return streak


def calculate_monthly_totals(
    days: list[dict[str, Any]],
) -> dict[str, int]:
    monthly_totals: dict[str, int] = {}

    for day in days:
        month = day["date"][:7]

        monthly_totals[month] = (
            monthly_totals.get(month, 0)
            + int(day["count"])
        )

    return monthly_totals


def fetch_contributions() -> dict[str, Any]:
    today = date.today()
    start_date = today - timedelta(days=364)

    url = (
        f"https://github.com/users/"
        f"{USERNAME}/contributions"
    )

    response = requests.get(
        url,
        params={
            "from": start_date.isoformat(),
            "to": today.isoformat(),
        },
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/150.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    parsed_days: dict[date, dict[str, Any]] = {}

    for cell in soup.select("[data-date]"):
        raw_date = cell.get("data-date")

        if not isinstance(raw_date, str):
            continue

        try:
            contribution_date = date.fromisoformat(
                raw_date
            )
        except ValueError:
            continue

        if not (
            start_date
            <= contribution_date
            <= today
        ):
            continue

        parsed_days[contribution_date] = {
            "date": contribution_date.isoformat(),
            "count": parse_contribution_count(
                cell,
                soup,
            ),
            "level": parse_level(cell),
        }

    if not parsed_days:
        raise RuntimeError(
            "GitHub contribution cells were not found. "
            "GitHub may have changed its HTML structure."
        )

    days: list[dict[str, Any]] = []
    cursor = start_date

    while cursor <= today:
        days.append(
            parsed_days.get(
                cursor,
                {
                    "date": cursor.isoformat(),
                    "count": 0,
                    "level": 0,
                },
            )
        )

        cursor += timedelta(days=1)

    # Detect parsing failure:
    # contribution levels exist, but all exact counts are zero.
    has_visible_activity = any(
        day["level"] > 0
        for day in days
    )

    has_parsed_counts = any(
        day["count"] > 0
        for day in days
    )

    if has_visible_activity and not has_parsed_counts:
        raise RuntimeError(
            "GitHub activity was detected, but exact "
            "contribution counts could not be parsed."
        )

    total_contributions = sum(
        int(day["count"])
        for day in days
    )

    active_days = [
        day
        for day in days
        if day["count"] > 0
    ]

    best_day = (
        max(
            active_days,
            key=lambda day: day["count"],
        )
        if active_days
        else None
    )

    return {
        "username": USERNAME,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "period": {
            "from": start_date.isoformat(),
            "to": today.isoformat(),
        },
        "summary": {
            "total_contributions": total_contributions,
            "active_days": len(active_days),
            "current_streak": (
                calculate_current_streak(
                    days,
                    today,
                )
            ),
            "longest_streak": (
                calculate_longest_streak(days)
            ),
            "best_day": best_day,
        },
        "monthly_totals": (
            calculate_monthly_totals(days)
        ),
        "days": days,
    }


def main() -> None:
    try:
        contribution_data = fetch_contributions()

        OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        OUTPUT_FILE.write_text(
            json.dumps(
                contribution_data,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        summary = contribution_data["summary"]

        print(
            f"Contribution data saved: "
            f"{OUTPUT_FILE}"
        )

        print(
            "Total contributions: "
            f"{summary['total_contributions']}"
        )

        print(
            "Active days: "
            f"{summary['active_days']}"
        )

        print(
            "Current streak: "
            f"{summary['current_streak']} day(s)"
        )

        print(
            "Longest streak: "
            f"{summary['longest_streak']} day(s)"
        )

    except requests.RequestException as error:
        raise SystemExit(
            f"GitHub request failed: {error}"
        ) from error

    except Exception as error:
        raise SystemExit(
            f"Contribution fetch failed: {error}"
        ) from error


if __name__ == "__main__":
    main()