#!/usr/bin/env python3
"""Fetch public GitHub contribution data and write data/contributions.json."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "data" / "contributions.json"
USERNAME = os.environ.get("GH_PROFILE_USER", "designwithrahma")
URL = f"https://github.com/users/{USERNAME}/contributions"
COUNT_PATTERN = re.compile(r"([\d,]+)\s+contributions?", re.IGNORECASE)


def normalize(value: str) -> str:
    return " ".join(value.split())


def parse_count_text(value: str) -> int | None:
    text = normalize(value)
    lower = text.lower()
    if "no contribution" in lower or "0 contribution" in lower:
        return 0
    if text.isdigit():
        return int(text)
    match = COUNT_PATTERN.search(text)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def contribution_count(cell: Tag, soup: BeautifulSoup) -> int:
    candidates: list[str] = []

    for name in ("data-count", "aria-label", "title"):
        value = cell.get(name)
        if isinstance(value, str):
            candidates.append(value)

    for name in ("aria-describedby", "aria-labelledby"):
        refs = cell.get(name)
        if not isinstance(refs, str):
            continue
        for ref in refs.split():
            element = soup.find(id=ref)
            if element:
                candidates.append(element.get_text(" ", strip=True))

    cell_id = cell.get("id")
    if isinstance(cell_id, str) and cell_id:
        for element in soup.find_all(attrs={"for": cell_id}):
            candidates.append(element.get_text(" ", strip=True))

    direct = cell.get_text(" ", strip=True)
    if direct:
        candidates.append(direct)

    for candidate in candidates:
        count = parse_count_text(candidate)
        if count is not None:
            return count
    return 0


def contribution_level(cell: Tag) -> int:
    try:
        return max(0, min(4, int(str(cell.get("data-level", "0")))))
    except (TypeError, ValueError):
        return 0


def fetch_days() -> list[dict[str, Any]]:
    today = dt.date.today()
    start = today - dt.timedelta(days=364)
    response = requests.get(
        URL,
        params={"from": start.isoformat(), "to": today.isoformat()},
        headers={
            "User-Agent": "profile-readme-bot/2.0",
            "Accept-Language": "en-US,en;q=0.9",
        },
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    parsed: dict[dt.date, dict[str, Any]] = {}
    for cell in soup.select("[data-date]"):
        raw_date = cell.get("data-date")
        if not isinstance(raw_date, str):
            continue
        try:
            day = dt.date.fromisoformat(raw_date)
        except ValueError:
            continue
        if not start <= day <= today:
            continue
        parsed[day] = {
            "date": day.isoformat(),
            "count": contribution_count(cell, soup),
            "level": contribution_level(cell),
        }

    if not parsed:
        raise RuntimeError("GitHub contribution cells were not found.")

    days: list[dict[str, Any]] = []
    cursor = start
    while cursor <= today:
        days.append(
            parsed.get(
                cursor,
                {"date": cursor.isoformat(), "count": 0, "level": 0},
            )
        )
        cursor += dt.timedelta(days=1)

    if any(day["level"] > 0 for day in days) and not any(day["count"] > 0 for day in days):
        raise RuntimeError("Activity was found, but contribution counts could not be parsed.")
    return days


def current_streak(days: list[dict[str, Any]]) -> tuple[int, str | None, str | None]:
    index = len(days) - 1
    if index >= 0 and days[index]["count"] == 0:
        index -= 1
    end_index = index
    length = 0
    while index >= 0 and days[index]["count"] > 0:
        length += 1
        index -= 1
    if length == 0:
        return 0, None, None
    return length, days[index + 1]["date"], days[end_index]["date"]


def longest_streak(days: list[dict[str, Any]]) -> tuple[int, str | None, str | None]:
    longest = running = 0
    start_index: int | None = None
    longest_start = longest_end = None
    for index, day in enumerate(days):
        if day["count"] > 0:
            if running == 0:
                start_index = index
            running += 1
            if running > longest and start_index is not None:
                longest = running
                longest_start = days[start_index]["date"]
                longest_end = day["date"]
        else:
            running = 0
            start_index = None
    return longest, longest_start, longest_end


def build_data(days: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(int(day["count"]) for day in days)
    active = sum(1 for day in days if day["count"] > 0)
    best = max(days, key=lambda day: int(day["count"]))
    current_length, current_start, current_end = current_streak(days)
    longest_length, longest_start, longest_end = longest_streak(days)

    monthly_totals: dict[str, int] = {}
    for day in days:
        month = day["date"][:7]
        monthly_totals[month] = monthly_totals.get(month, 0) + int(day["count"])

    return {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "period": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": {
            "length": current_length,
            "start": current_start,
            "end": current_end,
        },
        "longest_streak": {
            "length": longest_length,
            "start": longest_start,
            "end": longest_end,
        },
        "best_day": {"date": best["date"], "count": int(best["count"])},
        "monthly": [
            {"month": month, "total": value}
            for month, value in sorted(monthly_totals.items())
        ],
        "summary": {
            "total_contributions": total,
            "active_days": active,
            "current_streak": current_length,
            "longest_streak": longest_length,
            "best_day": best,
        },
        "monthly_totals": monthly_totals,
        "days": days,
    }


def main() -> None:
    try:
        data = build_data(fetch_days())
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(
            f"wrote {OUTPUT}: {data['total_contributions']} contributions, "
            f"current streak {data['current_streak']['length']}, "
            f"longest streak {data['longest_streak']['length']}"
        )
    except requests.RequestException as error:
        raise SystemExit(f"GitHub request failed: {error}") from error
    except Exception as error:
        raise SystemExit(f"Contribution fetch failed: {error}") from error


if __name__ == "__main__":
    main()
