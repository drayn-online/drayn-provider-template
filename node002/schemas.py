from typing import Any

PROTOCOL_VERSION = "0.2"
ALLOWED_STATES = {"accepted", "running", "completed", "refused", "failed", "expired"}

def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def validate_job(request: dict[str, Any]) -> tuple[bool, str]:
    for key in ("job_id", "protocol_version", "capability", "consumer", "objective", "output", "payment"):
        if key not in request: return False, f"Missing required field: {key}"
    if not nonempty(request["job_id"]): return False, "job_id must be a non-empty string."
    if request["protocol_version"] != PROTOCOL_VERSION: return False, "protocol_version must be 0.2."
    capability = request["capability"]
    if not isinstance(capability, dict) or capability.get("id") != "social.x.observe": return False, "Unsupported capability: social.x.observe is the only Node 002 capability."
    if capability.get("version") != PROTOCOL_VERSION: return False, "capability.version must be 0.2."
    consumer = request["consumer"]
    if not isinstance(consumer, dict) or not nonempty(consumer.get("consumer_id")): return False, "consumer.consumer_id is required."
    objective = request["objective"]
    if not isinstance(objective, dict): return False, "objective must be an object."
    if not nonempty(objective.get("type")): return False, "objective.type is required."
    if not nonempty(objective.get("question")): return False, "objective.question is required."
    subject = request.get("subject")
    if not isinstance(subject, dict) or subject.get("type") != "x_account" or not nonempty(subject.get("id")): return False, "social.x.observe requires subject.type=x_account and subject.id."
    output = request["output"]
    if not isinstance(output, dict) or output.get("format") != "structured_observations": return False, "output.format must be structured_observations."
    payment = request["payment"]
    if not isinstance(payment, dict): return False, "payment must be an object."
    if not nonempty(payment.get("payment_reference")): return False, "payment.payment_reference is required."
    if payment.get("currency") != "USDC": return False, "payment.currency must be USDC."
    if payment.get("network") != "solana": return False, "payment.network must be solana."
    if not nonempty(payment.get("payer")) or not nonempty(payment.get("payee")): return False, "payment payer and payee are required."
    window = request.get("constraints", {}).get("time_window")
    if window is not None and (not isinstance(window, dict) or not nonempty(window.get("from")) or not nonempty(window.get("to"))): return False, "constraints.time_window requires from and to."
    return True, ""
