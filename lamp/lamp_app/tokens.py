from contextlib import suppress
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Union

from fastapi import HTTPException, Request
from fastapi.responses import ORJSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JOSEError
from passlib.context import CryptContext
from sqlmodel import select

from .models import Tokens
from .utils import (ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM,
                    JWT_REFRESH_SECRET_KEY, JWT_SECRET_KEY,
                    REFRESH_TOKEN_EXPIRE_MINUTES)

password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {'exp': expires_delta, 'sub': str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)

    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode = {'exp': expires_delta, 'sub': str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt


def decode_jwt(jwtoken: str):
    payload = None
    with suppress(JOSEError):
        payload = jwt.decode(jwtoken, JWT_SECRET_KEY, ALGORITHM)
    return payload


def token_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:

        payload = jwt.decode(kwargs['dependencies'], JWT_SECRET_KEY, ALGORITHM)
        user_id = payload['sub']
        query = select(Tokens).filter_by(
            user_id=user_id,
            access_token=kwargs['dependencies'],
            status=True
        )
        data = kwargs['session'].exec(query)
        data = data.first()
        if data:
            result = await func(*args, **kwargs)
            return result
        else:
            return ORJSONResponse([{'message': 'Token was blocked.'}])

    return wrapper


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == 'Bearer':
                raise HTTPException(status_code=403, detail='Invalid authentication scheme.')
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail='Invalid or expired token.')
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail='Invalid authorization code.')

    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            _ = decode_jwt(jwtoken)
        except Exception:
            return False
        return True
