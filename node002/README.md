# DRAYN Node 002 — v0.2

Independent reference provider for the DRAYN social.x.observe capability.

This implementation is based on Provider Contract v0.2 / v0.2.1 clarification and is independent of DRAYN core.

Wire: HTTPS/JSON, Authorization: Bearer, POST /jobs, GET /jobs/{job_id}, GET /jobs/{job_id}/result.

Capability: social.x.observe version 0.2.

The job supplies subject.type=x_account, subject.id=@username, and constraints.time_window.from/to. The provider owns X credentials. DRAYN credentials and X credentials are separate.

Node 002 returns structured observations and provenance. It does not answer the higher-level intelligence question.

Only USDC on Solana is accepted. payment_reference is preserved for reconciliation; settlement verification remains DRAYN-side.

Run: python server.py
Test: python -m unittest discover -s tests -v

Without X_BEARER_TOKEN the adapter returns clearly labelled synthetic observations for contract testing. That proves the provider boundary, not live X readiness.
