# Panduan Deployment KOLEGA

Dokumen ini untuk **tim teknis** (mis. Diskominfo) yang akan menayangkan
aplikasi KOLEGA ke server agar dapat diakses masyarakat.

## Ringkasan teknologi

| Komponen     | Teknologi                                  |
| ------------ | ------------------------------------------ |
| Backend/API  | Python 3.12 + FastAPI (ASGI, Uvicorn)      |
| Database     | PostgreSQL (produksi) — SQLite hanya untuk dev lokal |
| Migrasi      | Alembic                                    |
| Frontend     | Satu halaman statis (di `app/static/`), disajikan oleh aplikasi yang sama |
| Kontainer    | `Dockerfile` tersedia (siap pakai di mana saja) |

Aplikasi menyajikan **API + web** dalam satu proses, port HTTP tunggal.

## Yang perlu disiapkan tim teknis

1. **Server / hosting** yang menyala 24/7 (VPS, cloud pemda, atau platform PaaS).
2. **PostgreSQL** (boleh terkelola/managed atau instan sendiri).
3. **Domain / subdomain**, mis. `kolega.padangpanjang.go.id`.
4. **HTTPS** (umumnya via reverse proxy seperti Nginx/Caddy, atau otomatis di PaaS).

## Variabel lingkungan (environment variables)

Wajib di-set saat produksi:

| Variabel       | Wajib | Contoh / Keterangan                                        |
| -------------- | ----- | ---------------------------------------------------------- |
| `DATABASE_URL` | ✅    | `postgresql+asyncpg://USER:PASS@HOST:5432/NAMADB` (driver **asyncpg**) |
| `SECRET_KEY`   | ✅    | Kunci acak untuk token login. Buat dengan `openssl rand -hex 32` |
| `ENVIRONMENT`  | —     | Set ke `production` (default `development`)                 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | Masa berlaku token login (menit), default `60`         |
| `PORT`         | —     | Port HTTP; banyak PaaS mengisinya otomatis (default `8000`) |

> Penting: `DATABASE_URL` harus memakai skema `postgresql+asyncpg://...`.

## Cara deploy dengan Docker (disarankan)

```bash
# 1. Build image
docker build -t kolega .

# 2. Jalankan (contoh)
docker run -d -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://kolega:rahasia@db-host:5432/kolega" \
  -e SECRET_KEY="$(openssl rand -hex 32)" \
  -e ENVIRONMENT=production \
  -v kolega_uploads:/app/app/static/uploads \
  --name kolega kolega
```

> **Foto profil di-upload disimpan sebagai file** di `app/static/uploads/`.
> Pasang volume (`-v kolega_uploads:/app/app/static/uploads` di atas) agar foto
> tidak hilang saat container di-redeploy. Pada platform PaaS, gunakan persistent
> disk yang di-mount ke path tersebut.

Saat container start, ia **otomatis menjalankan migrasi** (`alembic upgrade head`)
lalu menyalakan server. Tidak perlu langkah migrasi manual.

### Deploy via platform (Railway / Render / dll.)

1. Hubungkan repository GitHub ini ke platform.
2. Tambahkan **PostgreSQL** (platform memberi `DATABASE_URL` — pastikan skemanya
   `postgresql+asyncpg://`; jika platform memberi `postgresql://`, ubah menjadi
   `postgresql+asyncpg://`).
3. Set environment variable `SECRET_KEY` dan `ENVIRONMENT=production`.
4. Platform akan mem-build dari `Dockerfile` dan memberi URL publik.

## Membuat akun pengelola (admin)

Admin tidak bisa dibuat lewat halaman daftar. Setelah aplikasi tayang, jalankan
(di dalam container/host yang punya akses `DATABASE_URL` yang sama):

```bash
python -m app.scripts.create_admin <username> <email> <password>
```

## (Opsional) Mengisi data contoh

```bash
python -m app.scripts.seed_demo
```

> Jangan jalankan `seed_demo` di server produksi yang sudah berisi data nyata —
> ini hanya untuk demonstrasi.

## Catatan keamanan untuk produksi

- Wajib `SECRET_KEY` acak & rahasia (jangan pakai nilai default).
- Selalu aktifkan **HTTPS**.
- Lakukan **backup database** secara berkala.
- Batasi akses kredensial database & variabel lingkungan.

## Pemeriksaan kesehatan (health check)

Endpoint `GET /health` mengembalikan `{"status":"ok"}` — cocok untuk
liveness/readiness probe.

## Dokumentasi API

Saat aplikasi berjalan, dokumentasi interaktif tersedia di `/docs`.
