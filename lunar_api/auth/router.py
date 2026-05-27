# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from fastapi import APIRouter, HTTPException

from lunar_api.app_context import get_app_context, tokens
from lunar_api.auth.model import AuthResponse, LoginRequest, PublicUser, RegisterRequest
from lunar_api.auth.repository.user_repository import UserRepository
from lunar_api.auth.security import generate_session_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
app_context = get_app_context()


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(payload: RegisterRequest):
    user_repository: UserRepository = app_context.container.get(tokens.USER_REPOSITORY)
    existing = user_repository.get_user_by_login(payload.login)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Login is already in use")

    user = user_repository.create_user(
        login=payload.login,
        password_hash=hash_password(payload.password),
    )
    token = generate_session_token()
    user_repository.create_session(user_id=user.id, token=token)

    return AuthResponse(
        access_token=token,
        user=PublicUser(id=user.id, login=user.login),
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    user_repository: UserRepository = app_context.container.get(tokens.USER_REPOSITORY)
    user = user_repository.get_user_by_login(payload.login)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid login or password")

    token = generate_session_token()
    user_repository.create_session(user_id=user.id, token=token)

    return AuthResponse(
        access_token=token,
        user=PublicUser(id=user.id, login=user.login),
    )
