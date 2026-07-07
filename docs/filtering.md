# Filtering Method

The daily refresh is intentionally strict about the public internship list.

## Goal

Keep software/digital product design roles in `data/internships.csv`:

- Product Designer
- Product Design Intern
- UX/UI Designer
- Interaction Designer
- Design Systems
- Content Design
- Visual, brand, graphic, or motion design internships

## Rejected Signals

Roles are filtered into `data/rejected_matches.csv` when the title or description points to physical-product design instead of Figma-style digital product design.

Examples of rejected signals:

- Product design engineering
- Industrial design
- Mechanical engineering
- CAD, SolidWorks, Creo, Rhino
- 3D printing
- Machine shop or fabrication
- PCB/electronics/hardware
- Materials, manufacturing, or physical prototyping

## Audit Trail

The refresh writes rejected rows to `data/rejected_matches.csv` with a reason such as:

- `physical_title:product design engineering`
- `physical_title:industrial design`
- `physical_content:fabrication, rhino`

That file is not shown in the README, but it is committed so the filter can be reviewed and adjusted.
