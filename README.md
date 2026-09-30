# DRAYN Provider Template v0.2

A reusable reference implementation for an independent DRAYN intelligence provider.

**Protocol version:** 0.2  
**Contract clarification:** v0.2.1 clarification revision (protocol remains 0.2)

Canonical public contract:
https://app.notion.com/p/3eb900df8ab3812684aec3eff0d6abe9

The Provider Contract is authoritative. This repository is a reference implementation. If the implementation and contract ever differ, reconcile the implementation to the contract rather than inventing a new wire interpretation.

The important boundary is:

    DRAYN job
        -> generic provider contract
        -> provider capability
        -> provider-owned adapter
        -> observations
        -> result + provenance + accounting

DRAYN describes the job. The provider decides how to perform the work.

The job supplies the subject/entity. External-service credentials stay provider-owned and are never part of DRAYN provider authentication.

## Included

- `server.py` - reusable HTTP provider boundary
- `provider.py` - generic provider implementation and lifecycle
- `capabilities.py` - capability declaration
- `adapters/base.py` - provider adapter interface
- `adapters/x_observer.py` - example X observation adapter
- `schemas.py` - v0.2 contract validation helpers
- `sample-job.json` - canonical observation job
- `sample-x-job.json` - canonical X observation example
- `tests/test_provider.py` - contract-level local tests

## Contract-shaped job

The v0.2 template requires:

- `protocol_version = "0.2"`
- capability ID/version
- `consumer.consumer_id`
- `objective.type`
- `objective.question`
- job-scoped subject for `social.x.observe`
- `constraints.time_window.from/to` when a window is requested
- `output.format = "structured_observations"`
- `payment.payment_reference`
- `payment.currency = "USDC"`
- `payment.network = "solana"`

For `social.x.observe`, the public subject may be a username such as `@WormsOnAcid`. Resolving that identifier to an external-service-specific ID is provider implementation detail.

## Result boundary

Completed results use the canonical DRAYN-facing structure:

- `result.format`
- `result.summary`
- `result.observations[]`
- top-level `provenance[]`
- `accounting`
- original `payment`

Actual external retrievals must populate `provenance[].retrieved_at`.

Providers return observations/evidence, not DRAYN's final answer.

## Authentication

DRAYN provider authentication:

    Authorization: Bearer <DRAYN_PROVIDER_TOKEN>

External service credentials are separate:

    X_BEARER_TOKEN
    GitHub token
    API key
    database credentials
    etc.

The provider controls its DRAYN bearer token. DRAYN never needs the provider's external-service credentials.

## Run locally

    python server.py

Default:

    http://127.0.0.1:8010

Set a provider token if desired:

    NODE002_PROVIDER_TOKEN=...

If no token is supplied, a local token is generated and written to `provider-token.txt`. This file is runtime state and must not be committed.

For remote production exposure, use trusted HTTPS. Local HTTP is sufficient for contract testing.

Without `X_BEARER_TOKEN`, the example X adapter returns clearly labelled synthetic observations for protocol testing. This does not establish live X observation readiness.

With `X_BEARER_TOKEN`, the example adapter demonstrates provider-owned X access, username resolution, requested time-window handling, and canonical observation/provenance output.

## Test

    python -m unittest discover -s tests -v

The supplied tests use a synthetic adapter and do not require external service credentials.

## Payment boundary

The sole accepted settlement route for v0.2 is **USDC on Solana**.

Example:

    "payment": {
      "payment_reference": "pay_x_001",
      "currency": "USDC",
      "network": "solana",
      "payer": "consumer-solana-wallet",
      "payee": "provider-solana-wallet"
    }

The payment reference is the job-level accounting correlation. Settlement verification is outside this generic template unless a provider explicitly adds its own verified settlement mechanism.

## Job lifecycle

Valid states are:

    accepted
    running
    completed
    refused
    failed
    expired

Normal execution is:

    accepted -> running -> completed

Failed/refused jobs retain an explicit error object in the status response.

`expired` is reserved as a valid contract state. This template does not implement an automatic expiry scheduler or invent a new expiry wire requirement.

## Adding another provider capability

Implement `ProviderAdapter` in `adapters/base.py`.

Then declare a capability and register its adapter. The generic HTTP contract remains the same; only the capability declaration and provider-owned adapter change.

The intended architecture is that an independent developer can implement a specialist provider without access to the DRAYN repository.

## Reference status

This repository is the generic provider template, not Node 002 itself.

Node 002 should be an independent provider implementation against the public Provider Contract and capability requirement.