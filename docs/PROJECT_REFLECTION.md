# Project reflection

## Understanding the problem

MzansiBuilds is meant to let developers **build projects in public**: share progress, collaborate, comment, track milestones, and celebrate completed work. Core feature areas map to **authentication**, **project CRUD**, **feed and discovery**, **milestones**, **comments**, **collaboration requests**, and a **celebration wall** for finished projects.

## Design approach

Requirements were decomposed into these functional areas first, then modelled with diagrams before implementation:

- **Architecture** — how the browser talks to Flask and how Flask talks to Postgres (see `docs/architecture.drawio.png`).
- **ERD** — entities and relationships (`docs/ERD.drawio.png`).
- **User flow** — typical journeys from registration through project completion (`docs/user-flow_diagram.drawio.png`).
- **Components** — UI/API layering (`docs/component_level.drawio.png`).

That structure kept the implementation aligned with a clear data model and API surface (`/api/v1`).
