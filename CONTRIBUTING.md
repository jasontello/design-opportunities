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
- Date posted to this repo
- Status
- Why it fits this design-focused list

## Data Format

Add recent internship rows to [data/internships.csv](data/internships.csv).

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
- Use job boards only when the source is useful as an ongoing search.
- Do not add roles that are purely software engineering unless design is a meaningful part of the work.
- Move expired items to [ARCHIVE.md](ARCHIVE.md) instead of deleting them.
