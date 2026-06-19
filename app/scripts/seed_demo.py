"""Seed the database with demo accounts and data for exploring KOLEGA.

Run once (on the zero-setup SQLite default):

    python -m app.scripts.seed_demo

It creates an admin, a few providers (some verified, with services, reviews,
and incoming bookings) and customers (with placed bookings), then prints the
login credentials. Re-running is refused if demo data already exists — delete
the database (e.g. `kolega.db`) first to reseed.
"""

import asyncio

from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import hash_password
from app.crud import user as user_crud
from app.models.booking import Booking
from app.models.enums import BookingStatus, UserRole
from app.models.provider import ProviderProfile, Review, Service
from app.models.user import User

PASSWORD = "password123"


def _user(username: str, email: str, role: UserRole, verified: bool = False) -> User:
    return User(
        username=username,
        email=email,
        hashed_password=hash_password(PASSWORD),
        role=role.value,
        is_verified=verified,
    )


async def _run() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        if await user_crud.get_user_by_username(db, "budi_las") is not None:
            print(
                "Data demo sudah ada. Hapus database (mis. file kolega.db) "
                "dulu kalau ingin mengisi ulang."
            )
            return

        # --- Users ----------------------------------------------------------
        admin = _user("pengelola", "admin@kolega.id", UserRole.ADMIN, True)
        budi = _user("budi_las", "budi@kolega.id", UserRole.PROVIDER, True)
        anton = _user("pak_anton", "anton@kolega.id", UserRole.PROVIDER, True)
        siti = _user("siti_jahit", "siti@kolega.id", UserRole.PROVIDER, False)
        warga = _user("warga", "warga@kolega.id", UserRole.CUSTOMER)
        warga2 = _user("warga2", "warga2@kolega.id", UserRole.CUSTOMER)
        db.add_all([admin, budi, anton, siti, warga, warga2])
        await db.commit()
        for u in (budi, anton, siti, warga, warga2):
            await db.refresh(u)

        # --- Provider profiles ---------------------------------------------
        p_budi = ProviderProfile(
            user_id=budi.id, display_name="Budi Las Jaya", profession="Tukang Las",
            headline="Las pagar, teralis, kanopi — rapi & bergaransi",
            phone="0812-3456-7890", area="Kel. Silaing Bawah",
            bio="Pengalaman 10 tahun mengerjakan pagar, teralis, dan kanopi.",
        )
        p_anton = ProviderProfile(
            user_id=anton.id, display_name="Pak Anton", profession="Guru Les",
            headline="Les privat Matematika & IPA SD–SMP", phone="0813-1111-2222",
        )
        p_siti = ProviderProfile(
            user_id=siti.id, display_name="Siti Jahit", profession="Penjahit",
            headline="Jahit & permak, seragam sekolah", phone="0852-3333-4444",
        )
        db.add_all([p_budi, p_anton, p_siti])
        await db.commit()
        for p in (p_budi, p_anton, p_siti):
            await db.refresh(p)

        # --- Services -------------------------------------------------------
        s_pagar = Service(provider_id=p_budi.id, title="Pembuatan pagar besi",
                          category="tukang_las", price=350000, price_unit="per meter",
                          description="Termasuk pengukuran dan pemasangan di lokasi.")
        s_teralis = Service(provider_id=p_budi.id, title="Servis & perbaikan teralis",
                            category="tukang_las", price=150000, price_unit="per pekerjaan")
        s_les = Service(provider_id=p_anton.id, title="Les Matematika SD–SMP",
                        category="les_privat", price=60000, price_unit="per sesi")
        s_jahit = Service(provider_id=p_siti.id, title="Jahit baju custom",
                          category="jahit", price=80000, price_unit="per potong")
        s_permak = Service(provider_id=p_siti.id, title="Permak pakaian",
                           category="jahit", price=25000, price_unit="per item")
        db.add_all([s_pagar, s_teralis, s_les, s_jahit, s_permak])
        await db.commit()
        for s in (s_pagar, s_teralis, s_les, s_jahit, s_permak):
            await db.refresh(s)

        # --- Reviews --------------------------------------------------------
        db.add_all([
            Review(provider_id=p_budi.id, author_id=warga.id, rating=5,
                   comment="Pengerjaan rapi dan cepat, pagarnya kokoh!"),
            Review(provider_id=p_budi.id, author_id=warga2.id, rating=4,
                   comment="Bagus, harga sesuai. Recommended."),
            Review(provider_id=p_anton.id, author_id=warga.id, rating=5,
                   comment="Anak saya jadi paham matematika. Sabar mengajar."),
        ])

        # --- Bookings -------------------------------------------------------
        db.add_all([
            Booking(customer_id=warga.id, provider_id=p_budi.id, service_id=s_pagar.id,
                    status=BookingStatus.PENDING.value, preferred_time="Sabtu pagi",
                    note="Tolong buatkan pagar depan ±5 meter."),
            Booking(customer_id=warga2.id, provider_id=p_budi.id, service_id=s_teralis.id,
                    status=BookingStatus.ACCEPTED.value, preferred_time="Minggu siang",
                    note="Teralis jendela belakang lepas."),
            Booking(customer_id=warga.id, provider_id=p_siti.id, service_id=s_permak.id,
                    status=BookingStatus.PENDING.value, note="Permak celana 2 buah."),
        ])
        await db.commit()

    print("\n✓ Data demo berhasil dibuat! Password semua akun: " + PASSWORD + "\n")
    rows = [
        ("Pengelola (admin)", "pengelola", "verifikasi penyedia + statistik"),
        ("Penyedia (terverifikasi)", "budi_las", "punya layanan, ulasan, 2 pesanan masuk"),
        ("Penyedia (terverifikasi)", "pak_anton", "guru les, ada ulasan"),
        ("Penyedia (belum verif.)", "siti_jahit", "menunggu verifikasi admin"),
        ("Warga", "warga", "punya 2 pesanan (pantau status)"),
        ("Warga", "warga2", "punya 1 pesanan (diterima)"),
    ]
    print(f"  {'Peran':<26}{'Username':<12}Keterangan")
    print("  " + "-" * 70)
    for role, username, note in rows:
        print(f"  {role:<26}{username:<12}{note}")
    print()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
