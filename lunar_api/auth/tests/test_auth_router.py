# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from lunar_api.app_context import tokens
from lunar_api.auth.repository.user_repository import UserRepository
from lunar_api.auth.router import router
from lunar_api.persistence.connections.sqlite_connection import SQLiteConnection
from lunar_api.persistence.migrations.runner import run_migrations


class _Container:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    def get(self, token):
        if token == tokens.USER_REPOSITORY:
            return self._user_repository
        raise KeyError(f"Unsupported token: {token}")


@pytest.fixture
def user_repository(tmp_path):
    db_path = tmp_path / "auth_router.db"
    connection = SQLiteConnection(str(db_path))
    connection.connect()
    run_migrations(connection)
    repository = UserRepository(connection)
    try:
        yield repository
    finally:
        connection.disconnect()


@pytest.fixture
def client(user_repository: UserRepository):
    app = FastAPI()
    app.include_router(router)
    app_context = SimpleNamespace(container=_Container(user_repository))
    with patch("lunar_api.auth.router.app_context", app_context):
        yield TestClient(app)


def test_register_and_login_flow(client):
    register_response = client.post(
        "/auth/register",
        json={"login": "alice", "password": "secret"},
    )
    assert register_response.status_code == 201
    register_data = register_response.json()
    assert register_data["token_type"] == "bearer"
    assert register_data["access_token"]
    assert register_data["user"]["login"] == "alice"

    login_response = client.post(
        "/auth/login",
        json={"login": "alice", "password": "secret"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["token_type"] == "bearer"
    assert login_data["access_token"]
    assert login_data["user"]["login"] == "alice"


def test_register_rejects_duplicate_login(client):
    first = client.post("/auth/register", json={"login": "bob", "password": "secret"})
    assert first.status_code == 201

    second = client.post("/auth/register", json={"login": "bob", "password": "secret"})
    assert second.status_code == 409
    assert second.json()["detail"] == "Login is already in use"


def test_login_rejects_invalid_password(client):
    register_response = client.post(
        "/auth/register",
        json={"login": "carol", "password": "secret"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"login": "carol", "password": "wrong"},
    )
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid login or password"
