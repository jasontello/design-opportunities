#!/usr/bin/env python3
"""Generate README tables from CSV data files."""

from __future__ import annotations

import csv
import re
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPPORTUNITIES_PATH = ROOT / "data" / "opportunities.csv"
INTERNSHIPS_PATH = ROOT / "data" / "internships.csv"
README_PATH = ROOT / "README.md"

INTERNSHIPS_START = "<!-- INTERNSHIPS:START -->"
INTERNSHIPS_END = "<!-- INTERNSHIPS:END -->"
START = "<!-- OPPORTUNITIES:START -->"
END = "<!-- OPPORTUNITIES:END -->"


def cell(value: str) -> str:
    return (value or "TBD").replace("|", "\\|").strip()


def link(label: str, url: str) -> str:
    label = cell(label)
    url = (url or "").strip()
    return f"[{label}]({url})" if url else label


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def format_date(iso_date: str) -> str:
    _, month, day = iso_date.split("-")
    names = {
        "01": "Jan",
        "02": "Feb",
        "03": "Mar",
        "04": "Apr",
        "05": "May",
        "06": "Jun",
        "07": "Jul",
        "08": "Aug",
        "09": "Sep",
        "10": "Oct",
        "11": "Nov",
        "12": "Dec",
    }
    return f"{names[month]} {int(day):02d}"


def apply_button(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return "TBD"
    badge = "https://img.shields.io/badge/Apply-555555?style=for-the-badge"
    return f"[![Apply]({badge})]({url})"


def replace_block(readme: str, start: str, end: str, generated: str) -> str:
    before, marker, rest = readme.partition(start)
    if not marker:
        raise SystemExit(f"Missing marker: {start}")
    _, marker, after = rest.partition(end)
    if not marker:
        raise SystemExit(f"Missing marker: {end}")
    return f"{before}{start}\n{generated}{end}{after}"


def replace_internship_badge(readme: str, count: int) -> str:
    return re.sub(
        r"recent%20internships-\d+-555555",
        f"recent%20internships-{count}-555555",
        readme,
    )


def build_internship_table(rows: list[dict[str, str]]) -> str:
    sorted_rows = sorted(rows, key=lambda row: row["date_posted"], reverse=True)
    lines = [
        "| Company | Role | Location | Application/Link | Date Posted |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in sorted_rows:
        company = cell(row["company"])
        if row.get("status") == "Closed":
            company = f"{company} [CLOSED]"
        lines.append(
            "| "
            + " | ".join(
                [
                    company,
                    cell(row["role"]),
                    cell(row["location"]),
                    apply_button(row["application_url"]),
                    cell(format_date(row["date_posted"])),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_opportunity_tables(rows: list[dict[str, str]]) -> str:
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
    internships = load_rows(INTERNSHIPS_PATH)
    opportunities = load_rows(OPPORTUNITIES_PATH)
    readme = README_PATH.read_text(encoding="utf-8")
    readme = replace_internship_badge(readme, len(internships))
    readme = replace_block(readme, INTERNSHIPS_START, INTERNSHIPS_END, build_internship_table(internships))
    readme = replace_block(readme, START, END, build_opportunity_tables(opportunities))
    README_PATH.write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
