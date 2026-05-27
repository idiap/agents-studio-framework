# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from fastapi import APIRouter
from lunarflow.components import ComponentRegistry
from lunarflow.context import InMemoryContext

from lunar_api.flow_context.flow_context_registration import dependency_registration

# Local runner/context for component routes
components = ComponentRegistry()
context = InMemoryContext(components)
dependency_registration(context)

router = APIRouter()


@router.get("/component/index")
async def list_components():
    """List all registered components in the dependency registration"""
    registered_components = context.components._components.items()

    return {
        "components": [comp.to_model() for (key, comp) in registered_components],
        "total": len(registered_components),
    }
