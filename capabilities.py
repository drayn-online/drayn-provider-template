from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Capability:
    id: str
    version: str
    description: str


X_OBSERVE = Capability(
    id="social.x.observe",
    version="0.2",
    description=(
        "Observe public X activity for a bounded subject and context, "
        "returning structured observations with evidence and provenance."
    ),
)


def capability_document(capability: Capability) -> dict[str, Any]:
    return {
        "id": capability.id,
        "version": capability.version,
        "description": capability.description,
    }
