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
