# Architecture notes

## Development baseline

- **Desktop:** Python/PySide6 GUI sends HTTP requests to the FastAPI server using HTTPX.
- **API:** FastAPI owns authentication and future project operations. No public business endpoints have been implemented in this starter.
- **Data:** SQLAlchemy models and Alembic migrations control a central PostgreSQL database.
- **Files:** Not implemented yet. Plan object storage (or protected server-side storage) and keep file metadata/permissions in PostgreSQL.

## Security boundary

Desktop apps are untrusted clients. Never connect a deployed desktop app directly to PostgreSQL. All role checks, group membership checks, and file permissions must be enforced by FastAPI. HTTPS is required across networks.

## Proposed workflow

```text
User action -> PySide6 UI -> HTTPX request -> FastAPI validation and authorization
            -> SQLAlchemy -> PostgreSQL -> API response -> desktop refresh
```

Start with normal API requests and manual/polling refresh. Add WebSockets later if genuine real-time updates are required. Offline edits and merge conflict resolution are separate future features.

## Next work items

1. Agree on user/course/project/group requirements and data model.
2. Implement signup/login via a suitable identity provider or secure credential flow.
3. Add role-based permissions and access-controlled CRUD routes.
4. Implement student/professor Qt windows and API integration with nonblocking network calls.
5. Add file storage and secure downloads.
6. Add tests, encrypted deployment, migrations, logging, backup/restore, and packaging.
