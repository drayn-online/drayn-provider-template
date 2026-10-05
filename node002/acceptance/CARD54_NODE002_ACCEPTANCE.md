# Card 54 — Node 002 acceptance evidence

Target: DRAYN Provider Contract v0.2 / v0.2.1 clarification.

Implemented:
- Independent provider boundary.
- social.x.observe v0.2.
- Job-scoped X subject.
- constraints.time_window.from/to.
- Mandatory objective.type and objective.question.
- output.format=structured_observations.
- USDC/Solana payment validation.
- Separate DRAYN bearer auth and X credentials.
- accepted/running/completed/refused/failed lifecycle handling.
- Duplicate job_id idempotency.
- Structured observations, provenance, accounting/work_reference and payment preservation.
- Live X adapter passes the requested time window to the X API.

Local synthetic tests are included under node002/tests and require no external credentials.

Still required for Card 54 acceptance:
1. Run the provider in a real environment behind trusted HTTPS.
2. Submit the canonical job from an independent DRAYN consumer.
3. Verify the job-scoped subject and exact requested time window reach Node 002.
4. Verify accepted -> running -> completed.
5. Retrieve the result only after completed.
6. Verify provenance, accounting/work_reference and payment_reference survive.
7. Exercise refused and failed paths.
8. Repeat the same job_id and verify no duplicate execution.

Synthetic tests prove contract behavior only. They do not prove live X credentials, X API availability, or production HTTPS.
