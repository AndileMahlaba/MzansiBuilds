# MzansiBuilds

## Project profiling

To begin the MzansiBuilds project, I first focused on understanding the requirements and the problem the platform is trying to solve. The idea behind the platform is to allow developers to build projects publicly while sharing their progress and collaborating with other developers. Based on the requirements provided in the challenge, the main features of the system include user account creation and management, creating and updating projects, viewing what other developers are working on, interacting through comments or collaboration requests, tracking project milestones, and displaying completed projects on a celebration wall.

After reviewing the requirements, I broke the system down into smaller functional areas so that it would be easier to plan and implement. These areas included authentication for user accounts, project management for creating and updating projects, a developer feed where users can see projects from other developers, milestone tracking to record progress, and a section that highlights completed projects.

Before starting with the implementation, I created diagrams to help visualise the system structure and how the different parts of the application interact with each other. I designed a system architecture diagram to show how the user interface communicates with the backend and database. I also created an entity relationship diagram to outline the database structure and the relationships between users, projects, milestones, and comments. In addition, I mapped out the user flow to understand the typical journey a developer would take on the platform from registering an account to completing a project.

Creating these diagrams helped me organise the project and think through the design before writing any code. This made it easier to understand how the different components of the system connect and ensured that the development process would follow a clear and structured approach.


## System architecture
![System Architecture](docs/architecture.drawio.png)

## Database Design
![Database ER Diagram](docs/ERD.drawio.png)

## User Flow
![User Flow](docs/user-flow_diagram.drawio.png)

## Component Level
![Component Level](docs/component_level.drawio.png)

## Tech stack

- Python 3.11+ with Flask (server-rendered pages and form handling)
- SQLAlchemy + SQLite locally (set `DATABASE_URL` to PostgreSQL when you deploy)
- Flask-Login for sessions, Flask-WTF for CSRF on forms
- HTML, CSS, and minimal JavaScript under `frontend/`

## Repository layout

- `backend/` — Flask app, routes, models, services, repositories, templates
- `frontend/` — static CSS/JS (green, white, black theme)
- `database/schema.sql` — SQL reference matching the ORM models
- `tests/` — pytest suite (auth, projects, algorithms)

## Setup and run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m flask --app backend.app run
```

Open http://127.0.0.1:5000, register an account, then use **New project** in the navigation bar.

For PostgreSQL, set `DATABASE_URL` to a SQLAlchemy URL (for example `postgresql+psycopg2://user:pass@host/dbname`) and set `SECRET_KEY` to a long random string before running.

## Testing

```bash
python -m pytest
```

The tests cover registration, login, project creation, marking a project complete, and a merge helper used for ordered milestone lists (see `backend/algorithms/` and the notes there on time complexity).

## Security notes

Passwords are hashed with Werkzeug’s helpers rather than stored in plain text. Forms that change state use CSRF tokens. Text fields are length-limited in both WTForms and the repository layer. Use a strong `SECRET_KEY` in any shared or production environment.

## Ethical use of AI

I used AI tools as a sparring partner for debugging, structuring tests, and checking edge cases, but the requirements breakdown, architecture, data model, and how features map to routes and services were decisions I made and reworked until they fit the project. If I accepted a suggestion, I still stepped through it in the debugger or tests until I trusted the behaviour.
