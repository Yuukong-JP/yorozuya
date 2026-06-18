"""Domain enums shared across models and schemas."""

from enum import Enum


class UserRole(str, Enum):
    """The three actors in KOLEGA.

    - CUSTOMER (warga pemesan): residents who order services.
    - PROVIDER (penyedia): informal workers who offer services.
    - ADMIN (pengelola): city staff who verify, moderate, and oversee.
    """

    CUSTOMER = "customer"
    PROVIDER = "provider"
    ADMIN = "admin"


class ServiceCategory(str, Enum):
    """Common informal-work categories in the city, used for browse/filter."""

    LES_PRIVAT = "les_privat"
    TUKANG_LAS = "tukang_las"
    SERVIS_ELEKTRONIK = "servis_elektronik"
    JAHIT = "jahit"
    MASAK_KATERING = "masak_katering"
    FOTOGRAFI = "fotografi"
    DESAIN = "desain"
    BANGUNAN = "bangunan"
    KEBERSIHAN = "kebersihan"
    PERAWATAN = "perawatan"
    LAINNYA = "lainnya"
