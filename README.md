# KOLEGA

**Kolaborasi Layanan Ekonomi & Geliat Warga** — a hyperlocal public-service
platform that registers informal workers (*pekerja informal*) and connects them
with residents who need their services. Submitted as a regional innovation
(*inovasi daerah*) proposal for Kota Padang Panjang.

This repository is the backend foundation: project scaffolding, the `users`
table with role-based actors, and user **registration / login** with JWT
authentication. It maps directly to the proposal's first mandatory feature,
*"Daftar & masuk akun"*.

> Note: an earlier draft used the working codename **Yorozuya**. The project is
> now **KOLEGA**.

## Actors

KOLEGA serves three groups that depend on one another:

| Role (`role`) | Indonesian | Description |
| ------------- | ---------- | ----------- |
| `customer`    | Warga pemesan | Residents who order services. Default on sign-up. |
| `provider`    | Penyedia | Informal workers who offer services. Verified before going live. |
| `admin`       | Pengelola | City staff who verify, moderate, and oversee. Provisioned internally. |

## Stack

| Concern         | Choice                                   |
| --------------- | ---------------------------------------- |
| Web framework   | FastAPI                                  |
| ASGI server     | Uvicorn                                  |
| Database        | PostgreSQL (async via `asyncpg`)         |
| ORM             | SQLAlchemy 2.0 (async)                   |
| Migrations      | Alembic                                  |
| Validation      | Pydantic v2 / pydantic-settings          |
| Password hashing| bcrypt                                   |
| Tokens          | JWT (PyJWT), OAuth2 password flow        |

## Project layout

```
app/
├── main.py              # FastAPI app, health route, static frontend mount
├── core/
│   ├── config.py        # Settings from environment / .env
│   ├── database.py      # Async engine, session, declarative Base
│   └── security.py      # Password hashing + JWT helpers
├── models/
│   ├── enums.py         # UserRole (customer / provider / admin)
│   └── user.py          # User ORM model
├── schemas/
│   ├── user.py          # User request/response schemas
│   └── token.py         # Token schemas
├── crud/
│   └── user.py          # User database operations
├── api/
│   ├── deps.py          # Shared dependencies (current user)
│   ├── router.py        # Aggregate v1 router
│   └── routes/
│       └── auth.py      # register / login / me
└── static/
    └── index.html       # Single-page web client (login / register / profile)
alembic/                 # Database migrations
docker-compose.yml       # Local PostgreSQL
```

## Getting started

### 1. Configure environment

```bash
cp .env.example .env
# Generate a real secret key:
openssl rand -hex 32   # paste into SECRET_KEY
```

### 2. Start PostgreSQL

```bash
docker compose up -d
```

### 3. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Run the app

```bash
uvicorn app.main:app --reload
```

- Web client: <http://localhost:8000/>
- Interactive API docs: <http://localhost:8000/docs>

## API

Base prefix: `/api/v1`

**Auth**

| Method | Path                    | Description                              |
| ------ | ----------------------- | ---------------------------------------- |
| POST   | `/api/v1/auth/register` | Create a new user (`customer`/`provider`)|
| POST   | `/api/v1/auth/login`    | Obtain a JWT access token (OAuth2 form)  |
| GET    | `/api/v1/auth/me`       | Get the current authenticated user       |

**Providers & services**

| Method | Path                                  | Access   | Description                          |
| ------ | ------------------------------------- | -------- | ----------------------------------- |
| GET    | `/api/v1/providers`                   | public   | Browse providers (`q`, `category`)  |
| GET    | `/api/v1/providers/{id}`              | public   | Provider detail with services       |
| POST   | `/api/v1/providers/me`                | provider | Create my provider profile          |
| GET    | `/api/v1/providers/me`                | provider | Get my provider profile             |
| PATCH  | `/api/v1/providers/me`                | provider | Update my provider profile          |
| POST   | `/api/v1/providers/me/services`       | provider | Add a service                       |
| GET    | `/api/v1/providers/me/services`       | provider | List my services                    |
| PATCH  | `/api/v1/providers/me/services/{id}`  | provider | Update my service                   |
| DELETE | `/api/v1/providers/me/services/{id}`  | provider | Delete my service                   |

| Method | Path        | Description       |
| ------ | ----------- | ----------------- |
| GET    | `/health`   | Liveness probe    |

### Example

```bash
# Register as a provider (penyedia)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"budi@kolega.id","username":"budi_las","password":"lasterbaik1","role":"provider"}'

# Login (form-encoded, OAuth2 password flow)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=budi_las&password=lasterbaik1"

# Access a protected route
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

Admin accounts cannot be created through `/auth/register` (the API rejects
`role: "admin"`); they are provisioned internally.

## Tests

Tests run against an in-memory SQLite database, so no PostgreSQL instance is
needed:

```bash
pip install -r requirements-dev.txt
pytest
```

## Database migrations

```bash
# Create a new autogenerated migration after changing models
alembic revision --autogenerate -m "describe change"

# Apply migrations
alembic upgrade head

# Roll back one revision
alembic downgrade -1
```

## Roadmap

Per the proposal's mandatory (*Wajib*) tier-1 features:

- [x] Daftar & masuk akun (register / login + roles)
- [x] Profil penyedia (skills, services, pricing)
- [x] Pencarian & filter penyedia (browse)
- [x] Dasbor penyedia (kelola profil & layanan)
- [ ] Verifikasi identitas penyedia (admin/pengelola)
- [ ] Sistem pemesanan (booking)
- [ ] Ulasan & penilaian
- [ ] Dasbor pengelola
