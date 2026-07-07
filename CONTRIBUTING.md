# Contributing

Thanks for helping keep this list useful.

## What Belongs Here

Good additions are opportunities for:

- Product design
- UI/UX design
- UX research
- Design systems
- Design engineering
- Visual design for digital products
- Portfolio-building apprenticeships, fellowships, or challenges

## What To Include

Each internship should include:

- Organization
- Role name
- Application URL
- Location
- Deadline, or `Not listed` when the company ATS does not expose one
- Date posted to this repo
- Status
- Why it fits this design-focused list

## Data Format

Add recent internship rows to [data/internships.csv](data/internships.csv).

Add official company ATS boards to [data/company_sources.csv](data/company_sources.csv) so the daily refresh can find matching roles automatically.

Add broader recurring programs, job boards, and resources to [data/opportunities.csv](data/opportunities.csv).

After editing either CSV, regenerate the README:

```bash
python3 scripts/generate_readme.py
```

Use these status labels:

- `Open`
- `Closing Soon`
- `Closed`
- `Job Board`
- `Monitor`
- `Future Cycle`
- `Resource`

Use these priority labels:

- `High`
- `Medium`
- `Low`

## Review Rules

- Prefer official company, program, or organization links.
- Use third-party job boards only in the broader resources section, not as direct application links in the recent list.
- Keep the recent list U.S.-based.
- Do not add roles that are purely software engineering unless design is a meaningful part of the work.
- Move expired items to [ARCHIVE.md](ARCHIVE.md) instead of deleting them.
