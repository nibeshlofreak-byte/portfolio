"""MySQL-backed account registration and authentication for Lotus."""

import hashlib
import hmac
import os
import re
import secrets

import mysql.connector
from mysql.connector import errorcode

from auth_errors import AuthDatabaseError, AuthValidationError


_PASSWORD_ITERATIONS = 600_000


def _connect():
    password = os.environ.get("MYSQL_PASSWORD")
    if password is None:
        raise AuthDatabaseError(
            "Falta configurar MYSQL_PASSWORD. Consulta la sección de MySQL en README.md."
        )

    try:
        return mysql.connector.connect(
            host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
            port=int(os.environ.get("MYSQL_PORT", "3306")),
            user=os.environ.get("MYSQL_USER", "root"),
            password=password,
            database=os.environ.get("MYSQL_DATABASE", "wprbench"),
            connection_timeout=5,
        )
    except (mysql.connector.Error, ValueError) as ex:
        raise AuthDatabaseError(
            "No se pudo conectar con MySQL. Verifica que el servidor esté activo "
            "y que MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD y "
            "MYSQL_DATABASE sean correctos."
        ) from ex


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


def check_database():
    connection = _connect()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM users LIMIT 1")
        cursor.fetchone()
    except mysql.connector.Error as ex:
        raise AuthDatabaseError(f"No se pudo comprobar MySQL: {ex}") from ex
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def register_user(name, email, phone, password):
    name = name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    if not name or len(name) > 120:
        raise AuthValidationError("Escribe tu nombre (máximo 120 caracteres).")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254:
        raise AuthValidationError("Escribe un correo electrónico válido.")
    if (
        not re.fullmatch(r"\+?[0-9\s().-]{8,32}", phone)
        or not 7 <= sum(character.isdigit() for character in phone) <= 15
    ):
        raise AuthValidationError("Escribe un número telefónico válido.")
    if len(password) < 8:
        raise AuthValidationError("La contraseña debe tener al menos 8 caracteres.")

    connection = _connect()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO users (full_name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, phone, _hash_password(password)),
        )
        connection.commit()
        return name
    except mysql.connector.Error as ex:
        connection.rollback()
        if ex.errno == errorcode.ER_DUP_ENTRY:
            raise AuthValidationError("Ya existe una cuenta con ese correo.") from ex
        raise AuthDatabaseError(f"No se pudo guardar el registro en MySQL: {ex}") from ex
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def login_user(email, password):
    email = email.strip().lower()
    if not email or not password:
        raise AuthValidationError("Escribe tu correo y contraseña.")

    connection = _connect()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT full_name, password_hash FROM users WHERE email = %s",
            (email,),
        )
        row = cursor.fetchone()
        if row is None or not _password_matches(password, row[1]):
            raise AuthValidationError("Correo o contraseña incorrectos.")
        return row[0]
    except mysql.connector.Error as ex:
        raise AuthDatabaseError(f"No se pudo consultar la cuenta en MySQL: {ex}") from ex
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
