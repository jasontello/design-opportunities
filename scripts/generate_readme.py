#!/usr/bin/env python3
"""Generate README opportunity tables from data/opportunities.csv."""

from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "opportunities.csv"
README_PATH = ROOT / "README.md"

START = "<!-- OPPORTUNITIES:START -->"
END = "<!-- OPPORTUNITIES:END -->"


def cell(value: str) -> str:
    return (value or "TBD").replace("|", "\\|").strip()


def link(label: str, url: str) -> str:
    label = cell(label)
    url = (url or "").strip()
    return f"[{label}]({url})" if url else label


def load_rows() -> list[dict[str, str]]:
    with DATA_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_tables(rows: list[dict[str, str]]) -> str:
    grouped: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    for row in rows:
        grouped.setdefault(row["category"], []).append(row)

    lines: list[str] = []
    for category, category_rows in grouped.items():
        lines.append(f"## {category}")
        lines.append("")
        lines.append("| Status | Priority | Organization | Opportunity | Track | Location | Deadline | Notes |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for row in category_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        cell(row["status"]),
                        cell(row["priority"]),
                        cell(row["organization"]),
                        link(row["opportunity"], row["source_url"]),
                        cell(row["track"]),
                        cell(row["location"]),
                        cell(row["deadline"]),
                        cell(row["notes"]),
                    ]
                )
                + " |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    rows = load_rows()
    generated = build_tables(rows)
    readme = README_PATH.read_text(encoding="utf-8")
    before, marker, rest = readme.partition(START)
    if not marker:
        raise SystemExit(f"Missing marker: {START}")
    _, marker, after = rest.partition(END)
    if not marker:
        raise SystemExit(f"Missing marker: {END}")
    README_PATH.write_text(f"{before}{START}\n{generated}{END}{after}", encoding="utf-8")


if __name__ == "__main__":
    main()
