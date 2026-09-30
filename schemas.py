from __future__ import annotations

from typing import Any


ALLOWED_STATES = {
    "accepted",
    "running",
    "completed",
    "refused",
    "failed",
    "expired",
}


def valid_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_job(request: dict[str, Any], supported_capabilities: set[str]) -> tuple[bool, str]:
    required = (
        "job_id",
        "protocol_version",
        "capability",
        "consumer",
        "objective",
        "output",
        "payment",
    )

    missing = [key for key in required if key not in request]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    if not valid_nonempty_string(request["job_id"]):
        return False, "job_id must be a non-empty string."

    if not valid_nonempty_string(request["protocol_version"]):
        return False, "protocol_version must be a non-empty string."

    capability = request["capability"]
    if not isinstance(capability, dict):
        return False, "capability must be an object."

    capability_id = capability.get("id")
    capability_version = capability.get("version")

    if not valid_nonempty_string(capability_id):
        return False, "capability.id must be a non-empty string."

    if not valid_nonempty_string(capability_version):
        return False, "capability.version must be a non-empty string."

    if capability_id not in supported_capabilities:
        return False, f"Unsupported capability: {capability_id}"

    if not isinstance(request["consumer"], dict):
        return False, "consumer must be an object."

    if not valid_nonempty_string(request["consumer"].get("consumer_id")):
        return False, "consumer.consumer_id is required."

    if not isinstance(request["objective"], dict):
        return False, "objective must be an object."

    if not isinstance(request["output"], dict):
        return False, "output must be an object."

    if not isinstance(request["payment"], dict):
        return False, "payment must be an object."

    payment = request["payment"]
    if not valid_nonempty_string(payment.get("payment_reference")):
        return False, "payment.payment_reference is required."
    if payment.get("currency") != "USDC":
        return False, "payment.currency must be USDC."
    if payment.get("network") != "solana":
        return False, "payment.network must be solana."
    if not valid_nonempty_string(payment.get("payer")):
        return False, "payment.payer is required."
    if not valid_nonempty_string(payment.get("payee")):
        return False, "payment.payee is required."

    return True, ""


def validate_x_observe_job(request: dict[str, Any]) -> tuple[bool, str]:
    subject = request.get("subject")
    if not isinstance(subject, dict):
        return False, "subject is required for social.x.observe."

    if subject.get("type") != "x_account":
        return False, "social.x.observe requires subject.type=x_account."

    if not valid_nonempty_string(subject.get("id")):
        return False, "social.x.observe requires subject.id."

    return True, ""
