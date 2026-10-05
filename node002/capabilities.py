from dataclasses import dataclass

@dataclass(frozen=True)
class Capability:
    id: str
    version: str
    description: str

X_OBSERVE = Capability(
    "social.x.observe", "0.2",
    "Observe public X activity for a bounded subject and context, returning structured observations with evidence and provenance.",
)
