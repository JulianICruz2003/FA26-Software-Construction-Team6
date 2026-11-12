# Miner Project Hub

**Python desktop project-management application for students and professors.**

Miner Project Hub is designed as **installable desktop software**, not a website. The PySide6 desktop application talks to a FastAPI backend backed by PostgreSQL. Projects, tasks, user records, and project memberships can already be saved in the development database. Shared deployment across computers is a future goal.

> **Current status (November 2026): Local development prototype.** The desktop app has Projects, Tasks, Team, Overview, and Files interfaces. Project listing/creation, task listing/creation/completion, user record creation/listing, and project membership listing/creation/removal are connected to FastAPI and PostgreSQL. **Files currently list local selections only; they are not uploaded or synchronized.** Login, verified Student/Professor accounts, authorization, course/review workflows, and role-specific dashboards are not implemented. Do not expose the API publicly or use real student records until authentication, authorization, HTTPS, and secure storage are in place.

## Tech stack

| Component | Technology | Purpose |
| --- | --- | --- |
| Desktop client | Python 3.12, PySide6 (Qt) | Desktop GUI for Windows/macOS/Linux |
| API client | HTTPX | Communicate with the server |
| Backend | FastAPI | API endpoints, future authentication and business rules |
| Database | PostgreSQL 17 | Shared relational data |
| ORM and migrations | SQLAlchemy 2, Alembic | Models and schema changes |
| Database development | Docker Compose | Reproducible local PostgreSQL |
| Tests | pytest, FastAPI TestClient | Automated checks |
| Packaging | PyInstaller | Build an application for each target OS |
| Collaboration | Git + GitHub | Branches, pull requests, code review |

## Architecture

```text
             PySide6 desktop app
                     |
                 HTTPX client
                     |
                 FastAPI API
                     |
                  SQLAlchemy
                     |
                  PostgreSQL

      Future: HTTPS, authentication, roles,
      shared file storage, multi-device access
```

During local development, the desktop and API run on the same computer. In a future deployment, users install **only the desktop app**; the API and database run on a separate server. Desktop clients must never receive direct PostgreSQL credentials. A Student/Professor-specific interface is planned but **not yet implemented**.

## Prerequisites

Install these before following the setup:

1. **Python 3.12**: https://www.python.org/downloads/ (on Windows, check *Add Python to PATH* or use the `py` launcher)
2. **Git**: https://git-scm.com/
3. **Docker Desktop**: https://www.docker.com/products/docker-desktop/ (start Docker Desktop before starting the database)
4. **VS Code** (recommended): https://code.visualstudio.com/ and the Microsoft Python extension

Qt Designer is installed with PySide6. You do **not** need a separate Qt installation for this starter.

## First-time setup — macOS / Linux

Run these commands **from the repository root** in Terminal:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/dev.txt
cp .env.example .env
```

If `python3.12` is not found, check your Python installation and use a verified Python 3.12 executable. Never commit `.env`.

## First-time setup — Windows (PowerShell)

Run these commands **from the repository root**:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements/dev.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, use Command Prompt with `.venv\Scripts\activate.bat`, or use `.\.venv\Scripts\python.exe` directly without activating. Avoid changing machine-wide execution policies solely for this project.

## Run locally (macOS, Linux, or Windows)

Use **three terminal sessions** with the repository root as the working directory. Ensure the virtual environment is active in the terminals running Python.

**Terminal 1 — Start PostgreSQL**

```bash
docker compose up -d db
```

On first run (and after future schema changes), apply database migrations:

```bash
python -m alembic upgrade head
```

**Terminal 2 — Start the API server**

```bash
python -m uvicorn server.main:app --reload
```

The local API listens on `http://127.0.0.1:8000` by default. If port 8000 is already in use, find and stop the existing Uvicorn process instead of unknowingly running a second, outdated server. Try:

- API health: http://127.0.0.1:8000/health
- Database health: http://127.0.0.1:8000/health/db
- Interactive API docs (development only): http://127.0.0.1:8000/docs

**Local database port:** This development setup uses host port **5433** for PostgreSQL (configured in `compose.yaml` and `.env`, because 5432 was occupied). Inside the Docker network, PostgreSQL still listens on 5432. Check your own `compose.yaml` and `.env` before changing this.

**Terminal 3 — Launch desktop software**

```bash
python -m desktop.main
```

Press **Check connection**. It should show whether the API and PostgreSQL are responding. This is a real Qt desktop window, not a browser page.

### Features currently available in local development

| Feature | Current behavior |
| --- | --- |
| Projects | List and create projects saved in PostgreSQL; double-click to open a workspace |
| Tasks | List, create, and mark tasks complete for the selected project; saved in PostgreSQL |
| Team | List, add, and remove project memberships; create development user records; saved in PostgreSQL |
| Files | Select/remove local files in the UI only; no upload, download, or persistence yet |
| Overview | Displays selected project information; some values remain placeholders |
| Diagrams, Activity, Courses, Reviews | Planned or placeholder features |
| Sign-in and distinct Student/Professor views | **Not yet implemented**; a `Student` or `Professor` field on a user record is not authentication |

### Current development API routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET / POST | `/projects` | List or create projects |
| GET / POST | `/projects/{project_id}/tasks` | List or create tasks for a project |
| PATCH | `/projects/{project_id}/tasks/{task_id}` | Update task completion |
| GET / POST | `/users` | List or create development user records |
| GET / POST | `/projects/{project_id}/members` | List or add project members |
| DELETE | `/projects/{project_id}/members/{membership_id}` | Remove project membership |
| GET | `/health`, `/health/db` | Check API and database connectivity |

These endpoints currently **lack authentication and authorization**. Do not expose the development API to the internet.

**Stop development services**

Press `Ctrl+C` in the API terminal, close the desktop app, then stop the database:

```bash
docker compose down
```

This keeps your database volume. **Do not run `docker compose down -v` unless you intend to delete local database data.**

## Qt Designer (drag-and-drop GUI design)

With your Python environment active, run:

```bash
pyside6-designer
```

Designer saves `.ui` files. You can generate Python from a `.ui` file using `pyside6-uic`, or load the UI at runtime. Much of the existing desktop UI is currently built directly in Python. On some macOS setups, PySide6 Qt plugins may need `chflags -R nohidden "$VIRTUAL_ENV/lib/python3.12/site-packages/PySide6/Qt/plugins"` to become visible.

## Running tests

```bash
python -m pytest -q
```

The included test checks `/health` without requiring a running database. Once database-backed APIs are developed, add isolated integration tests using a disposable test database.

## Building installable desktop software

Run on the operating system **you want to distribute for**:

```bash
python -m PyInstaller --name MinerProjectHub --windowed --onedir desktop/main.py
```

The output goes to `dist/`. Windows builds must be produced on Windows; macOS builds on macOS. Distributing an executable does **not** deploy the server, and production clients must be configured with a reachable HTTPS API endpoint. Code signing/notarization may be required for smooth installation on users' systems.

## Connecting multiple computers (future deployment)

The `API_BASE_URL` setting in `.env` determines where the desktop app sends requests. `http://127.0.0.1:8000` works only when the server runs on the same computer. For multiple students/professors, deploy the FastAPI server to a trusted host with an HTTPS domain and configure each desktop app to use that URL. Do not expose local PostgreSQL to the internet or simply publish an unauthenticated development server.

For a real deployment, add authentication and authorization, restrict cross-project access, use HTTPS, secure file storage, backup and recovery, and monitoring before handling university data. If using student records, coordinate with university policies and relevant privacy requirements.

## Environment variables

Copy `.env.example` into `.env`. Keep `.env` private and out of Git.

| Variable | Meaning |
| --- | --- |
| `POSTGRES_USER` | Development PostgreSQL user |
| `POSTGRES_PASSWORD` | Development PostgreSQL password (change sample value) |
| `POSTGRES_DB` | Database name |
| `POSTGRES_HOST` | Database hostname as seen by local API (`127.0.0.1` for this starter) |
| `POSTGRES_PORT` | Host-side PostgreSQL port (currently `5433` in this local setup) |
| `API_BASE_URL` | API URL used by the desktop app |

**Note:** After a Docker PostgreSQL volume has already been initialized, changing the password in `.env` alone won't change the database user's existing password. Reset it explicitly or recreate a disposable development volume if you can afford to lose its data.

## Repository layout

```text
miner-project-hub/
├── .env.example                 # Example configuration (do not commit .env)
├── .gitignore
├── alembic/                     # Database migrations (projects, tasks, users, memberships)
│   ├── env.py
│   └── versions/
├── alembic.ini
├── compose.yaml                 # PostgreSQL development container
├── desktop/
│   ├── main.py                  # Desktop entry point
│   ├── app_window.py            # Main window and sidebar navigation
│   ├── services/api_client.py   # HTTPX calls to FastAPI
│   ├── dialogs/                 # Create-project dialog
│   └── pages/
│       ├── projects.py          # Project list
│       ├── project_workspace.py # Workspace and tabs
│       └── workspace/           # Overview, Tasks, Files, Team
├── docs/
├── requirements/
│   ├── desktop.txt
│   ├── server.txt
│   └── dev.txt
├── server/
│   ├── database.py
│   ├── main.py                  # FastAPI app and router registrations
│   ├── models.py                # Projects, Tasks, Users, Memberships
│   ├── schemas.py               # Pydantic API schemas
│   └── routes/
│       ├── projects.py
│       ├── tasks.py
│       ├── teams.py
│       └── users.py
└── tests/
```

## Team workflow (GitHub)

1. Protect `main` if your repository settings allow it.
2. Create feature branches such as `feature/login-window`, `feature/projects-api`, and `feature/task-dashboard`.
3. Open a pull request for each coherent change; ask a teammate to review.
4. Run `python -m pytest -q` before merging.
5. Add or update Alembic migrations when changing database models. Avoid editing production schemas manually.
6. Do not commit `.env`, passwords, access tokens, actual student records, or large uploaded project files.

## Roadmap

- [x] Desktop window and local API health checks
- [x] PostgreSQL development configuration and Alembic migrations
- [x] Initial automated API smoke test
- [x] Project listing and creation backed by PostgreSQL
- [x] Task listing, creation, and completion backed by PostgreSQL
- [x] Development user records and project membership endpoints
- [x] Desktop Team Management integration
- [ ] Full Projects/Tasks CRUD (editing and deleting as appropriate)
- [ ] Shared file upload, download, storage, and access control
- [ ] Student and professor registration/sign-in
- [ ] Server-side authentication and role-based permissions
- [ ] Distinct student and professor dashboards
- [ ] Courses, reviews, project assignments, diagrams, and activity history
- [ ] Multi-device synchronization and deployment
- [ ] Packaging, backup/restore, security review, and documentation

## Troubleshooting

- **`python3.12` / `py -3.12` is missing:** Install Python 3.12 and restart your terminal.
- **Docker isn't responding:** Start Docker Desktop, then check `docker compose ps`.
- **Database is not ready:** Wait for `docker compose ps` to show healthy, inspect `docker compose logs db`, and run migrations again.
- **Port 5432 already used:** The current local setup uses host port 5433. If you change it, update both `compose.yaml` and `POSTGRES_PORT` in `.env`.
- **Cannot connect from another computer:** `127.0.0.1` always means *that computer*. A deployed API needs its own reachable address and HTTPS configuration.
- **Qt window does not open:** Check PySide6 in the active `.venv`, launch in a normal graphical desktop session, and see the macOS Qt plugin note above.
- **Users/Teams endpoints missing in Swagger:** Verify `server/main.py` imports and includes the routers, then restart the Uvicorn process serving the configured API port.
- **Add Existing Member finds no users:** Create a development user with **Create New Member** first; existing members are excluded from the dropdown.

## Useful official documentation

- Qt for Python: https://doc.qt.io/qtforpython-6/
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/en/20/
- Alembic: https://alembic.sqlalchemy.org/
- PostgreSQL: https://www.postgresql.org/docs/
- Docker Compose: https://docs.docker.com/compose/
- PyInstaller: https://pyinstaller.org/en/stable/

## License

No license has been selected by the project team yet. Before public distribution, choose an appropriate license and review Qt/PySide6 licensing obligations.
