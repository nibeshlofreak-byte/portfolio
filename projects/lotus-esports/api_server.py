"""Private-LAN API that lets the Lotus mobile app access MySQL."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from auth_errors import AuthDatabaseError, AuthValidationError
from auth_store import (
    check_database,
    login_user,
    register_user,
)

app = FastAPI(title="Lotus local API", docs_url=None, redoc_url=None)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    phone: str = Field(min_length=8, max_length=32)
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


@app.exception_handler(RequestValidationError)
async def invalid_request_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Solicitud inválida."})


def _database_http_error(ex: AuthDatabaseError) -> HTTPException:
    return HTTPException(status_code=503, detail=str(ex))


@app.get("/health")
def health():
    try:
        check_database()
    except AuthDatabaseError as ex:
        raise _database_http_error(ex) from ex
    return {"status": "ok", "database": "connected"}


@app.post("/auth/register", status_code=201)
def register(request: RegisterRequest):
    try:
        name = register_user(
            request.name, request.email, request.phone, request.password
        )
    except AuthValidationError as ex:
        raise HTTPException(status_code=400, detail=str(ex)) from ex
    except AuthDatabaseError as ex:
        raise _database_http_error(ex) from ex
    return {"name": name}


@app.post("/auth/login")
def login(request: LoginRequest):
    try:
        name = login_user(request.email, request.password)
    except AuthValidationError as ex:
        raise HTTPException(status_code=401, detail=str(ex)) from ex
    except AuthDatabaseError as ex:
        raise _database_http_error(ex) from ex
    return {"name": name}
