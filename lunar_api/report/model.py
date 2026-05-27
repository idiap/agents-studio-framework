# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel


class ReportInput(BaseModel):
    name: str
    content: str


class ReportUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    provenance_data: Optional[Dict[str, Any]] = None


class Report(BaseModel):
    id: UUID
    name: str
    content: str
    created_at: datetime
    version: int = 1
    provenance_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
            "provenance_data": self.provenance_data,
        }
