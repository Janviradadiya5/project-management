# Django API Skeleton

Reusable Django REST API structure running on Docker with PostgreSQL.

## Run


If PowerShell blocks local scripts, run:

This starts Docker Compose for the backend and then runs the Vite dev server for the frontend.

Start the full stack from the project root:

```powershell
docker compose -f docker/docker-compose.yml up -d --build
```


Stop the stack:

```powershell
docker compose -f docker/docker-compose.yml down
```

