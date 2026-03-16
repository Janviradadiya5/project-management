# Django API Skeleton

Reusable Django REST API structure running on Docker with PostgreSQL.

## Run

For local Windows development, start backend and frontend together from the project root:

```powershell
.\start-dev.ps1
```

If PowerShell blocks local scripts, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

This starts Docker Compose for the backend and then runs the Vite dev server for the frontend.

Start the full stack from the project root:

```powershell
docker compose -f docker/docker-compose.yml up -d --build
```

Available endpoints:

- App: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/
- Health: http://127.0.0.1:8000/health/

Stop the stack:

```powershell
docker compose -f docker/docker-compose.yml down
```

