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
| Database        | SQLite by default (zero setup); PostgreSQL (async via `asyncpg`) optional |
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

## Quick start (no Docker, no PostgreSQL)

By default the app uses a local **SQLite** file (`kolega.db`) and creates its
tables automatically on startup — so you only need Python:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

- Web client: <http://localhost:8000/>
- Interactive API docs: <http://localhost:8000/docs>

That's it. Register an account (choose **Penyedia** to create a profile and
list services, or **Warga** to browse). Data is stored in `kolega.db` in the
project folder; delete that file to start fresh.

> Set `SECRET_KEY` (`export SECRET_KEY=$(openssl rand -hex 32)` or via `.env`)
> before any real/shared deployment — the built-in default is for local use only.

## Using PostgreSQL instead (optional)

For a production-like setup, point `DATABASE_URL` at PostgreSQL and use Alembic
for migrations:

```bash
cp .env.example .env            # then set DATABASE_URL (see the file) + SECRET_KEY
docker compose up -d            # starts local PostgreSQL
pip install -r requirements.txt
alembic upgrade head            # create tables
uvicorn app.main:app --reload
```

Example `DATABASE_URL`:
`postgresql+asyncpg://kolega:kolega@localhost:5432/kolega`

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

**Reviews (ulasan)**

| Method | Path                              | Access   | Description                         |
| ------ | --------------------------------- | -------- | ----------------------------------- |
| GET    | `/api/v1/providers/{id}/reviews`  | public   | List a provider's reviews           |
| POST   | `/api/v1/providers/{id}/reviews`  | user     | Add/update my review (1–5 + comment)|

**Bookings (pemesanan)**

| Method | Path                              | Access   | Description                          |
| ------ | --------------------------------- | -------- | ------------------------------------ |
| POST   | `/api/v1/bookings`                | user     | Book a provider/service              |
| GET    | `/api/v1/bookings/me`             | user     | Bookings I placed                    |
| GET    | `/api/v1/bookings/incoming`       | provider | Bookings addressed to me             |
| POST   | `/api/v1/bookings/{id}/status`    | provider | Accept / reject / complete           |
| POST   | `/api/v1/bookings/{id}/cancel`    | user     | Cancel my pending booking            |

**Admin (pengelola)**

| Method | Path                                       | Access | Description                  |
| ------ | ------------------------------------------ | ------ | ---------------------------- |
| GET    | `/api/v1/admin/stats`                      | admin  | Platform counts              |
| GET    | `/api/v1/admin/providers`                  | admin  | List all providers           |
| POST   | `/api/v1/admin/providers/{id}/verify`      | admin  | Verify a provider            |
| POST   | `/api/v1/admin/providers/{id}/unverify`    | admin  | Remove verification          |

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
- [x] Verifikasi identitas penyedia (admin/pengelola)
- [x] Sistem pemesanan (booking)
- [x] Ulasan & penilaian
- [x] Dasbor pengelola

## Demo data (akun dummy)

To explore every dashboard quickly, seed demo accounts and data:

```bash
python -m app.scripts.seed_demo
```

All accounts use the password `password123`:

| Role                      | Username     | What you'll see                              |
| ------------------------- | ------------ | -------------------------------------------- |
| Pengelola (admin)         | `pengelola`  | Verify providers + platform stats            |
| Penyedia (verified)       | `budi_las`   | Services, reviews, 2 incoming bookings       |
| Penyedia (verified)       | `pak_anton`  | Tutor profile with a review                  |
| Penyedia (unverified)     | `siti_jahit` | Waiting for admin verification               |
| Warga                     | `warga`      | 2 placed bookings to track                   |
| Warga                     | `warga2`     | 1 accepted booking                           |

Re-running is refused if demo data exists — delete `kolega.db` to reseed.

## Provisioning an admin (pengelola)

Admin accounts can't be created through the public API. Create one locally with:

```bash
python -m app.scripts.create_admin <username> <email> <password>
```

If the username already exists it is promoted to the admin role. Then log in
through the web client to reach the pengelola dashboard (verify providers, view
stats).
