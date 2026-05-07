# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

This is a **Recipe App API** — a Django REST Framework backend with PostgreSQL, fully containerized via Docker Compose. The two services are:

| Service | Description | Port |
|---------|-------------|------|
| `app` | Django 5.2 REST API (Python 3.12 Alpine) | 8000 |
| `db` | PostgreSQL 17 Alpine | 5432 (internal) |

### Running the stack

All commands run through Docker Compose. The Docker daemon must be running first:

```bash
sudo dockerd &>/tmp/dockerd.log &
```

Start the app (runs `wait_for_db`, `migrate`, then `runserver`):

```bash
sudo docker compose up
```

### Tests

```bash
sudo docker compose run --rm app sh -c "python manage.py wait_for_db && python manage.py test"
```

All 21 tests run inside the container against a temporary PostgreSQL test database.

### Linting

```bash
sudo docker compose run --rm app sh -c "flake8"
```

### Key caveats

- **No SQLite fallback**: the Django app requires `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS` env vars. These are set in `docker-compose.yml` for development.
- **Docker-in-Docker**: this VM runs inside a Firecracker VM. Docker requires `fuse-overlayfs` storage driver and `iptables-legacy`. The update script handles Docker installation.
- **`wait_for_db`**: always run `python manage.py wait_for_db` before `test` or `migrate` — PostgreSQL may not be ready immediately.
- **Image rebuild**: if `requirements.txt` or `requirements.dev.txt` change, rebuild with `sudo docker compose build`.
- **Dev dependencies**: `flake8` is only installed when `DEV=true` build arg is set (which `docker-compose.yml` does by default).
