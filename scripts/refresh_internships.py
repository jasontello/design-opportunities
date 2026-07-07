#!/usr/bin/env python3
"""Refresh recent design internships from official company ATS boards."""

from __future__ import annotations

import csv
import concurrent.futures
import html
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
REJECTED_PATH = ROOT / "data" / "rejected_matches.csv"

LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "14"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "12"))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "24"))
NOW = datetime.now(timezone.utc)
CUTOFF = NOW - timedelta(days=LOOKBACK_DAYS)

EARLY_ROLE = re.compile(
    r"\b(intern|internship|co-?op|co op|fellowship|apprentice|new grad|graduate|university|entry level|junior)\b",
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
            r"associate ux designer",
            r"associate ui designer",
            r"associate visual designer",
            r"junior product designer",
        ]
    ),
    re.IGNORECASE,
)
PHYSICAL_TITLE = re.compile(
    "|".join(
        [
            r"product design engineering",
            r"industrial design",
            r"hardware design",
            r"reliability design",
            r"mechanical",
            r"\bcad\b",
            r"3d design",
            r"footwear design",
            r"manufacturing",
            r"electrical",
            r"electronics",
            r"antenna",
            r"power electronics",
            r"control systems",
            r"guidance, navigation",
        ]
    ),
    re.IGNORECASE,
)
PHYSICAL_CONTENT = re.compile(
    "|".join(
        [
            r"mechanical engineering",
            r"industrial design",
            r"product design engineering",
            r"\bcad software\b",
            r"\bcad\b",
            r"solidworks",
            r"\bcreo\b",
            r"\brhino\b",
            r"3d printing",
            r"physical prototypes?",
            r"machine shop",
            r"\bpcb",
            r"electronics",
            r"arduino",
            r"raspberry pi",
            r"hardware",
            r"ergonomics",
            r"materials",
            r"manufacturing",
            r"fabrication",
            r"power electronics",
            r"control systems",
        ]
    ),
    re.IGNORECASE,
)
DIGITAL_TITLE = re.compile(
    "|".join(
        [
            r"product designer",
            r"product design intern",
            r"apprentice product designer",
            r"\bux\b",
            r"\bui\b",
            r"user experience",
            r"interaction designer",
            r"experience designer",
            r"design systems?",
            r"content design",
            r"brand design",
            r"graphic design",
            r"visual design",
            r"motion design",
        ]
    ),
    re.IGNORECASE,
)
DIGITAL_CONTENT = re.compile(
    "|".join(
        [
            r"\bfigma\b",
            r"wireframes?",
            r"design systems?",
            r"user interface",
            r"digital product",
            r"web app",
            r"mobile app",
            r"\bsaas\b",
            r"usability",
            r"user research",
            r"product strategy",
            r"interaction design",
            r"prototype in figma",
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


def plain_text(value: object) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(value))
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def broad_role_matches(title: str, description: str) -> bool:
    if re.search(r"\bsoftware engineer\b", title, re.IGNORECASE) and not re.search(
        r"\b(design|designer|ux|ui)\b", title, re.IGNORECASE
    ):
        return False
    early_title = EARLY_ROLE.search(title) or re.search(
        r"\bassociate (product|ux|ui|visual|graphic|content|brand|interaction) designer\b",
        title,
        re.IGNORECASE,
    )
    return bool(early_title and DESIGN_ROLE.search(title))


def classify_role(title: str, description: str) -> tuple[str, str]:
    physical_title = PHYSICAL_TITLE.search(title)
    if physical_title:
        return "Rejected", f"physical_title:{physical_title.group(0).lower()}"

    physical_hits = sorted({match.group(0).lower() for match in PHYSICAL_CONTENT.finditer(description)})
    digital_title = DIGITAL_TITLE.search(title)
    digital_content = DIGITAL_CONTENT.search(description)
    if physical_hits and not digital_title and len(physical_hits) >= 2:
        return "Rejected", "physical_content:" + ", ".join(physical_hits[:4])
    if physical_hits and not (digital_title or digital_content):
        return "Rejected", "physical_content:" + ", ".join(physical_hits[:4])

    if digital_title:
        return "Open", "digital_title:" + digital_title.group(0).lower()
    if re.search(r"\bdesign intern(ship)?\b", title, re.IGNORECASE) and digital_content:
        return "Open", "digital_content:" + digital_content.group(0).lower()
    return "Needs Review", "weak_digital_signal"


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
        description = plain_text(job.get("content", ""))
        if not broad_role_matches(title, description):
            continue
        first_seen = parse_iso(job.get("first_published"))
        updated = parse_iso(job.get("updated_at"))
        date, date_kind = source_date(first_seen, updated)
        if not date:
            continue
        decision, decision_reason = classify_role(title, description)
        yield {
            "date_posted": date.date().isoformat(),
            "company": company,
            "role": title,
            "location": clean_location(job.get("location")),
            "application_url": job.get("absolute_url", ""),
            "status": decision,
            "source": f"greenhouse:{board}",
            "source_date_kind": date_kind,
            "notes": decision_reason,
        }


def lever_rows(company: str, board: str) -> Iterable[dict[str, str]]:
    data = fetch_json(f"https://api.lever.co/v0/postings/{board}?mode=json")
    for job in data:  # type: ignore[union-attr]
        title = job.get("text", "")
        description = plain_text(
            " ".join(
                [
                    str(job.get("descriptionPlain", "")),
                    str(job.get("additionalPlain", "")),
                    str(job.get("descriptionBodyPlain", "")),
                ]
            )
        )
        if not broad_role_matches(title, description):
            continue
        date, date_kind = source_date(parse_millis(job.get("createdAt")), None)
        if not date:
            continue
        decision, decision_reason = classify_role(title, description)
        yield {
            "date_posted": date.date().isoformat(),
            "company": company,
            "role": title,
            "location": clean_location(job.get("categories", {}).get("location")),
            "application_url": job.get("hostedUrl", ""),
            "status": decision,
            "source": f"lever:{board}",
            "source_date_kind": date_kind,
            "notes": decision_reason,
        }


def ashby_rows(company: str, board: str) -> Iterable[dict[str, str]]:
    data = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")
    for job in data.get("jobs", []):  # type: ignore[union-attr]
        title = job.get("title", "")
        description = plain_text(job.get("descriptionPlain") or job.get("descriptionHtml"))
        if not broad_role_matches(title, description):
            continue
        date, date_kind = source_date(parse_iso(job.get("publishedAt")), None)
        if not date:
            continue
        decision, decision_reason = classify_role(title, description)
        location = job.get("location") or {}
        yield {
            "date_posted": date.date().isoformat(),
            "company": company,
            "role": title,
            "location": clean_location(location),
            "application_url": job.get("jobUrl", ""),
            "status": decision,
            "source": f"ashby:{board}",
            "source_date_kind": date_kind,
            "notes": decision_reason,
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

    accepted_rows = [row for row in rows if row["status"] == "Open"]
    rejected_rows = [row for row in rows if row["status"] != "Open"]
    deduped = {row["application_url"]: row for row in accepted_rows if row["application_url"]}
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

    rejected_fields = [
        "date_posted",
        "company",
        "role",
        "location",
        "application_url",
        "source",
        "source_date_kind",
        "notes",
    ]
    rejected_ordered = sorted(
        rejected_rows,
        key=lambda row: (row["date_posted"], row["company"], row["role"]),
        reverse=True,
    )
    with REJECTED_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rejected_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row[field] for field in rejected_fields} for row in rejected_ordered)
    print(
        f"wrote {len(ordered)} internships and {len(rejected_ordered)} rejected matches "
        "from official company sources"
    )


if __name__ == "__main__":
    main()
