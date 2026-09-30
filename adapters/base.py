from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProviderAdapter(ABC):
    """Provider-owned implementation of one DRAYN capability."""

    @abstractmethod
    def execute(self, job: dict[str, Any]) -> dict[str, Any]:
        """
        Return provider observations.

        The adapter must not answer the consumer's higher-level question.
        It supplies observations/evidence for DRAYN to reason over.
        """
        raise NotImplementedError
