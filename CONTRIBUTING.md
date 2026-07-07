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

Each opportunity should include:

- Organization
- Opportunity name
- Source URL
- Status
- Deadline or "Rolling"
- Location
- Eligibility
- Why it fits this design-focused list

## Data Format

Add entries to [data/opportunities.csv](data/opportunities.csv), then regenerate the README:

```bash
python3 scripts/generate_readme.py
```

Use these status labels:

- `Open`
- `Monitor`
- `Future Cycle`
- `Closing Soon`
- `Closed`
- `Job Board`
- `Resource`

Use these priority labels:

- `High`
- `Medium`
- `Low`

## Review Rules

- Prefer official company, program, or organization links.
- Use job boards only when the source is useful as an ongoing search.
- Do not add roles that are purely software engineering unless design is a meaningful part of the work.
- Move expired items to [ARCHIVE.md](ARCHIVE.md) instead of deleting them.

