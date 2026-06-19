# CLAUDE.md — Catatan proyek KOLEGA

Panduan singkat untuk melanjutkan pekerjaan di sesi baru.

## Apa ini
KOLEGA (Kolaborasi Layanan Ekonomi & Geliat Warga) — platform hyperlocal yang
menghubungkan warga dengan penyedia jasa informal (tukang las, penjahit, guru
les, dll). Proposal *inovasi daerah* untuk Kota Padang Panjang.

**Branch kerja:** `claude/laughing-cannon-g04oxx` (push semua ke sini).

## Stack
FastAPI + SQLAlchemy 2 (async) + Alembic. DB: **SQLite by default** (zero setup),
PostgreSQL opsional via `DATABASE_URL`. Frontend: satu file SPA di
`app/static/index.html` (vanilla JS/CSS, tanpa framework). Bahasa UI: Indonesia.

## Cara jalan (lokal, tanpa Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # buka http://localhost:8000
```
- Tabel dibuat otomatis saat startup kalau pakai SQLite (tanpa alembic).
- Catatan: di laptop user pakai `py -3.12 -m ...` (Python 3.14 gagal build wheel).

## Perintah berguna
```bash
pytest                                   # 57 tes, semua hijau
python -m app.scripts.seed_demo          # isi data dummy (semua password: password123)
python -m app.scripts.create_admin <user> <email> <pass>   # buat admin
alembic upgrade head                     # migrasi (untuk PostgreSQL)
```
Cek sintaks JS setelah edit `index.html`: ekstrak isi `<script>` lalu `node --check`.

## Akun demo (setelah seed_demo) — password: `password123`
- `pengelola` (admin), `budi_las` / `pak_anton` (penyedia verified),
  `siti_jahit` (penyedia belum verified), `warga` / `warga2` (warga).

## Fitur yang sudah ada
Auth + 3 peran (warga/penyedia/pengelola); profil & layanan penyedia; browse +
filter kategori; landing page; ulasan & rating; verifikasi penyedia + dasbor
pengelola (infografik); pemesanan (booking) dgn ringkasan + timeline status;
moderasi (hapus ulasan, nonaktif akun); halaman Privasi & Ketentuan; **foto
penyedia (upload dari perangkat** ke storage lokal, atau via URL); estimasi
pendapatan; badge notifikasi; chat in-app per pesanan. Logo SVG monogram, font
Plus Jakarta Sans, ikon kategori custom.

## Arsitektur singkat
- `app/models/` ORM: user, provider (ProviderProfile/Service/Review), booking,
  message, enums. Daftarkan model baru di `app/models/__init__.py`.
- `app/crud/`, `app/schemas/`, `app/api/routes/` (auth, providers, bookings,
  admin). Router digabung di `app/api/router.py`.
- Migrasi di `alembic/versions/` (terakhir 0006). `alembic/env.py` pakai
  `settings.DATABASE_URL` (async) + import `app.models` agar semua tabel terdaftar.
- Deploy: `Dockerfile` + `DEPLOYMENT.md` (panduan untuk tim teknis/Diskominfo).

## Foto profil (upload)
- Endpoint `POST /providers/me/photo` (penyedia, multipart `file`) menyimpan
  gambar ke `app/static/uploads/` dan membalas `{"url": "/uploads/<uuid>.ext"}`.
  Sengaja stateless — URL disimpan lewat create/update profil biasa, jadi jalan
  saat buat maupun edit. Batas 5 MB; tipe: JPG/PNG/WebP/GIF.
- File disajikan via `StaticFiles` mount "/" di `app/main.py` (akses `/uploads/…`).
- Folder di-`.gitignore` (isi diabaikan, `.gitkeep` dipertahankan). **Deploy
  Docker: mount volume ke `app/static/uploads` agar foto tak hilang saat redeploy.**
- Belum ada: hapus file lama saat ganti foto (file lama jadi yatim), validasi
  isi gambar sebenarnya (cuma cek content-type), resize/thumbnail.

## Yang BELUM dikerjakan (perlu keputusan/infra)
1. **Notifikasi real-time/push** — butuh WebSocket/push service.
2. **Kategori dinamis (admin bisa tambah) + sub-kategori** — refactor: kategori
   kini enum (`ServiceCategory`) dgn ikon/warna baku per kategori; kalau dibuat
   bebas, kategori baru tak punya ikon/warna. Menunggu keputusan user.
3. **Verifikasi email saat daftar** — butuh layanan email (dari Diskominfo).

## Konvensi
- Jangan commit/push kecuali diminta; selalu ke branch di atas.
- Pertahankan gaya kode sekitarnya; UI berbahasa Indonesia.
- Jangan taruh identitas model di commit/PR/kode.
