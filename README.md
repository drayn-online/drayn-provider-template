# DRAYN Provider Template v0.2

A reusable starting point for an independent DRAYN intelligence provider.

The important boundary is:

    DRAYN job
        -> generic provider contract
        -> provider capability
        -> provider-owned adapter
        -> observations
        -> result + provenance + accounting

The provider decides how it performs the work.

The DRAYN job decides what subject/entity is being observed or processed.

External credentials stay provider-owned. They are never part of the DRAYN provider authentication credential.

## Included

- `server.py` - reusable HTTP provider boundary
- `provider.py` - generic provider implementation and lifecycle
- `capabilities.py` - capability declaration
- `adapters/base.py` - provider adapter interface
- `adapters/x_observer.py` - example X observation adapter
- `schemas.py` - validation helpers
- `sample-job.json` - generic observation job
- `sample-x-job.json` - X observation example
- `tests/test_provider.py` - contract-level local tests

## The key abstraction

A provider is not a research agent.

A provider supplies a declared capability.

For example:

    social.x.observe

The job supplies the target:

    subject.type = x_account
    subject.id   = <account identifier>

The provider owns the credentials required to access X.

This means the same provider can observe different accounts on different jobs without changing its configuration.

## Run locally

    python server.py

Default:

    http://127.0.0.1:8010

Set a provider token if desired:

    NODE002_PROVIDER_TOKEN=...

Otherwise one is generated locally and stored in `provider-token.txt`.

For a real deployment, put the service behind a trusted HTTPS endpoint. Local HTTP is sufficient for contract testing.

## Test

    python -m unittest discover -s tests -v

The tests use a synthetic adapter. No external service credentials are required.

## Adding another provider

Implement `ProviderAdapter` in `adapters/base.py`.

Then declare a capability and register the adapter:

    capability id: weather.observe
    capability id: github.observe
    capability id: market.data.observe
    capability id: company.telemetry.observe

The generic HTTP contract does not change.

Only the capability declaration and provider-owned adapter change.

## Important separation

DRAYN provider authentication:

    Authorization: Bearer <DRAYN_PROVIDER_TOKEN>

External service credentials:

    X_BEARER_TOKEN
    GitHub token
    API key
    database credentials
    etc.

These are different credentials with different owners and must never be conflated.

## Payment boundary (v0.2)

The provider contract accepts **USDC on Solana only**.

Every job must include:

```json
"payment": {
  "payment_reference": "pay_x_001",
  "currency": "USDC",
  "network": "solana",
  "payer": "consumer-solana-wallet",
  "payee": "provider-solana-wallet"
}
```

The provider should treat the payment reference as the job-level accounting reference. Settlement verification remains outside this template unless a provider explicitly adds a verified settlement adapter.

Other currencies or networks are rejected by the template.

## Job lifecycle

`expired` is reserved as a valid lifecycle state in the contract. This template does not implement an automatic expiry scheduler; a production provider that uses expiry should implement and document its own expiry policy.
