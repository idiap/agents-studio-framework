# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class RegisterRequest(BaseModel):
    login: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


class User(BaseModel):
    id: UUID
    login: str
    password_hash: str
    created_at: datetime


class PublicUser(BaseModel):
    id: UUID
    login: str


class AuthenticatedUser(BaseModel):
    id: UUID
    login: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: PublicUser
