#!/usr/bin/env python3
"""Refresh recent design internships from official company ATS boards."""

from __future__ import annotations

import csv
import concurrent.futures
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "data" / "company_sources.csv"
OUTPUT_PATH = ROOT / "data" / "internships.csv"

LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "14"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "12"))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "24"))
NOW = datetime.now(timezone.utc)
CUTOFF = NOW - timedelta(days=LOOKBACK_DAYS)

EARLY_ROLE = re.compile(
    r"\b(intern|internship|co-?op|co op|fellowship|apprentice|new grad|graduate|university|entry level|junior|associate)\b",
    re.IGNORECASE,
)
DESIGN_ROLE = re.compile(
    "|".join(
        [
            r"product design",
            r"product designer",
            r"graphic design",
            r"graphic designer",
            r"visual design",
            r"visual designer",
            r"\bux\b",
            r"\bui\b",
            r"interaction designer",
            r"experience designer",
            r"user experience",
            r"user research",
            r"design research",
            r"industrial design",
            r"footwear design",
            r"motion design",
            r"brand design",
            r"content design",
            r"3d design",
            r"design intern",
            r"design internship",
            r"design co-?op",
            r"designer intern",
            r"designer internship",
            r"associate product designer",
            r"junior product designer",
        ]
    ),
    re.IGNORECASE,
)


def fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "design-opportunities-refresh/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return json.load(response)


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def parse_millis(value: int | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(value / 1000, timezone.utc)


def clean_location(value: object) -> str:
    if isinstance(value, dict):
        value = value.get("name") or value.get("location") or value.get("city")
    if not value:
        return "Check site"
    return str(value).replace("\n", ", ").strip()


def role_matches(title: str) -> bool:
    if re.search(r"\bsoftware engineer\b", title, re.IGNORECASE) and not re.search(
        r"\b(design|designer|ux|ui)\b", title, re.IGNORECASE
    ):
        return False
    return bool(EARLY_ROLE.search(title) and DESIGN_ROLE.search(title))


def source_date(first_seen: datetime | None, updated: datetime | None) -> tuple[datetime | None, str]:
    if first_seen and first_seen >= CUTOFF:
        return first_seen, "first_published"
    if updated and updated >= CUTOFF:
        return updated, "updated"
    return None, ""


def greenhouse_rows(company: str, board: str) -> Iterable[dict[str, str]]:
    data = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true")
    for job in data.get("jobs", []):  # type: ignore[union-attr]
        title = job.get("title", "")
        if not role_matches(title):
            continue
        first_seen = parse_iso(job.get("first_published"))
        updated = parse_iso(job.get("updated_at"))
        date, date_kind = source_date(first_seen, updated)
        if not date:
            continue
        yield {
            "date_posted": date.date().isoformat(),
            "company": company,
            "role": title,
            "location": clean_location(job.get("location")),
            "application_url": job.get("absolute_url", ""),
            "status": "Open",
            "source": f"greenhouse:{board}",
            "source_date_kind": date_kind,
            "notes": "Official company ATS listing.",
        }


def lever_rows(company: str, board: str) -> Iterable[dict[str, str]]:
    data = fetch_json(f"https://api.lever.co/v0/postings/{board}?mode=json")
    for job in data:  # type: ignore[union-attr]
        title = job.get("text", "")
        if not role_matches(title):
            continue
        date, date_kind = source_date(parse_millis(job.get("createdAt")), None)
        if not date:
            continue
        yield {
            "date_posted": date.date().isoformat(),
            "company": company,
            "role": title,
            "location": clean_location(job.get("categories", {}).get("location")),
            "application_url": job.get("hostedUrl", ""),
            "status": "Open",
            "source": f"lever:{board}",
            "source_date_kind": date_kind,
            "notes": "Official company ATS listing.",
        }


def ashby_rows(company: str, board: str) -> Iterable[dict[str, str]]:
    data = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")
    for job in data.get("jobs", []):  # type: ignore[union-attr]
        title = job.get("title", "")
        if not role_matches(title):
            continue
        date, date_kind = source_date(parse_iso(job.get("publishedAt")), None)
        if not date:
            continue
        location = job.get("location") or {}
        yield {
            "date_posted": date.date().isoformat(),
            "company": company,
            "role": title,
            "location": clean_location(location),
            "application_url": job.get("jobUrl", ""),
            "status": "Open",
            "source": f"ashby:{board}",
            "source_date_kind": date_kind,
            "notes": "Official company ATS listing.",
        }


def load_sources() -> list[dict[str, str]]:
    with SOURCES_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fetch_source(source: dict[str, str]) -> list[dict[str, str]]:
    providers = {
        "greenhouse": greenhouse_rows,
        "lever": lever_rows,
        "ashby": ashby_rows,
    }
    provider = source["provider"]
    return list(providers[provider](source["company"], source["board"]))


def main() -> None:
    rows: list[dict[str, str]] = []
    sources = load_sources()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_sources = {executor.submit(fetch_source, source): source for source in sources}
        for future in concurrent.futures.as_completed(future_sources):
            source = future_sources[future]
            try:
                rows.extend(future.result())
            except Exception as exc:
                print(f"warning: failed {source['provider']}:{source['board']}: {exc}")

    deduped = {row["application_url"]: row for row in rows if row["application_url"]}
    ordered = sorted(
        deduped.values(),
        key=lambda row: (row["date_posted"], row["company"], row["role"]),
        reverse=True,
    )

    fields = [
        "date_posted",
        "company",
        "role",
        "location",
        "application_url",
        "status",
        "source",
        "source_date_kind",
        "notes",
    ]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    print(f"wrote {len(ordered)} internships from official company sources")


if __name__ == "__main__":
    main()
