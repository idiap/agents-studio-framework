# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from lunar_api.app_context import get_app_context, tokens
from lunar_api.auth.model import AuthenticatedUser
from lunar_api.auth.repository.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None:
        raise _unauthorized()

    if credentials.scheme.lower() != "bearer":
        raise _unauthorized("Invalid authentication scheme")

    app_context = get_app_context()
    user_repository: UserRepository = app_context.container.get(tokens.USER_REPOSITORY)
    user = user_repository.get_user_by_session_token(credentials.credentials)
    if not user:
        raise _unauthorized("Invalid or expired token")

    return AuthenticatedUser(id=user.id, login=user.login)
