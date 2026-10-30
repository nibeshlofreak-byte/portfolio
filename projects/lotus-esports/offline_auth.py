"""Temporary in-memory registration and login for offline testing."""

import hashlib
import hmac
import re
import secrets

from auth_errors import AuthStoreError


_PASSWORD_ITERATIONS = 600_000


def _hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS
    )
    return f"{_PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def _password_matches(password, stored_hash):
    try:
        iterations_text, salt_hex, digest_hex = stored_hash.split("$")
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (AttributeError, ValueError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(actual, expected)


def register_user(accounts, name, email, phone, password):
    name = name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    if not name or len(name) > 120:
        raise AuthStoreError("Escribe tu nombre (máximo 120 caracteres).")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254:
        raise AuthStoreError("Escribe un correo electrónico válido.")
    if (
        not re.fullmatch(r"\+?[0-9\s().-]{8,32}", phone)
        or not 7 <= sum(character.isdigit() for character in phone) <= 15
    ):
        raise AuthStoreError("Escribe un número telefónico válido.")
    if len(password) < 8:
        raise AuthStoreError("La contraseña debe tener al menos 8 caracteres.")
    if email in accounts:
        raise AuthStoreError("Ya existe una cuenta con ese correo en esta sesión.")

    accounts[email] = {
        "name": name,
        "phone": phone,
        "password_hash": _hash_password(password),
    }
    return name


def login_user(accounts, email, password):
    email = email.strip().lower()
    account = accounts.get(email)
    if account is None or not _password_matches(password, account["password_hash"]):
        raise AuthStoreError("Correo o contraseña incorrectos.")
    return account["name"]
