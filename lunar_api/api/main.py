# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from lunarflow.components import ComponentRegistry
from lunarflow.context import InMemoryContext
from lunarflow.runner import PythonRunner
from starlette.middleware.cors import CORSMiddleware

from lunar_api.app_context import get_app_context
from lunar_api.api.routers import (
    report as report_router,
    flow as flow_router,
    component as component_router,
    auth as auth_router,
)
from lunar_api.flow_context.flow_context_registration import dependency_registration

MODEL = "gpt-4.1"

app_context = get_app_context()

components = ComponentRegistry()
context = InMemoryContext(components)
dependency_registration(context)

runner = PythonRunner(context=context)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    _ = fastapi_app
    app_context.start()
    yield
    app_context.stop()


app = FastAPI(lifespan=lifespan)

origins_env = os.getenv("FRONTEND_URL", "http://localhost")
allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)
app.include_router(flow_router)
app.include_router(component_router)
app.include_router(auth_router)

@app.get("/knowledge_base")
def get_knowledge_base():
    return []
