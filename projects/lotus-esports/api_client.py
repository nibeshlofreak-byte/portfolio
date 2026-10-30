"""Client for the Lotus API running on the same private Wi-Fi network."""

import os

import httpx

from auth_errors import AuthStoreError


API_BASE_URL = os.environ.get(
    "LOTUS_API_URL", "http://192.168.1.7:8765"
).rstrip("/")
_TIMEOUT = httpx.Timeout(10.0, connect=4.0)


def _post(path, payload):
    try:
        response = httpx.post(
            f"{API_BASE_URL}{path}", json=payload, timeout=_TIMEOUT
        )
    except httpx.RequestError as ex:
        raise AuthStoreError(
            f"No se pudo conectar con Lotus API en {API_BASE_URL}. "
            "Comprueba que la computadora y el teléfono estén en el mismo Wi-Fi "
            "y que el servidor esté iniciado."
        ) from ex

    try:
        body = response.json()
    except ValueError as ex:
        raise AuthStoreError(
            f"Lotus API respondió con un formato inesperado (HTTP {response.status_code})."
        ) from ex

    if response.is_error:
        detail = body.get("detail") if isinstance(body, dict) else None
        if isinstance(detail, str) and detail:
            raise AuthStoreError(detail)
        raise AuthStoreError(
            f"Lotus API rechazó la solicitud (HTTP {response.status_code})."
        )

    name = body.get("name") if isinstance(body, dict) else None
    if not isinstance(name, str) or not name:
        raise AuthStoreError("Lotus API no devolvió el nombre de la cuenta.")
    return name


def register_user(name, email, phone, password):
    return _post(
        "/auth/register",
        {"name": name, "email": email, "phone": phone, "password": password},
    )


def login_user(email, password):
    return _post("/auth/login", {"email": email, "password": password})
