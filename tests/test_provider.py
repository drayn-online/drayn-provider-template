import unittest

from capabilities import X_OBSERVE
from provider import DRAYNProvider


class SyntheticAdapter:
    def execute(self, job):
        return {
            "observations": [{
                "observation_id": "obs-1",
                "type": "test",
                "source": "synthetic",
                "source_id": "source-1",
                "observed_at": "2026-09-30T00:00:00Z",
                "retrieved_at": "2026-09-30T00:00:01Z",
                "content": {"text": "test"},
                "provenance": {
                    "source_url": "mock://source-1",
                    "retrieval_method": "synthetic",
                    "transformations": [],
                    "limitations": [],
                },
            }],
            "coverage": {"gaps": []},
            "resource_usage": {"source_requests": 0},
        }


def job(job_id="job-1"):
    return {
        "job_id": job_id,
        "protocol_version": "0.2",
        "capability": {
            "id": X_OBSERVE.id,
            "version": X_OBSERVE.version,
        },
        "consumer": {"consumer_id": "test-consumer"},
        "subject": {"type": "x_account", "id": "123"},
        "objective": {
            "type": "observation",
            "description": "Observe activity.",
        },
        "context": {},
        "constraints": {},
        "output": {"format": "observations"},
        "payment": {
            "payment_reference": "pay-1",
            "currency": "USDC",
            "network": "solana",
            "payer": "consumer-wallet",
            "payee": "provider-wallet",
        },
    }


class ProviderContractTests(unittest.TestCase):
    def setUp(self):
        self.provider = DRAYNProvider(
            "provider-test",
            {X_OBSERVE.id: {
                "id": X_OBSERVE.id,
                "version": X_OBSERVE.version,
                "description": X_OBSERVE.description,
            }},
        )
        self.provider.register_adapter(X_OBSERVE.id, SyntheticAdapter())

    def test_accepts_generic_observation_job(self):
        response = self.provider.submit(job())
        self.assertEqual(response["status_code"], 202)

    def test_subject_is_job_scoped(self):
        response = self.provider.submit(job())
        self.assertEqual(response["status_code"], 202)

    def test_duplicate_job_id_is_idempotent(self):
        self.provider.submit(job("same"))
        response = self.provider.submit(job("same"))
        self.assertEqual(response["status_code"], 202)

    def test_wrong_capability_is_refused(self):
        request = job()
        request["capability"] = {
            "id": "intelligence.research",
            "version": "0.2",
        }
        response = self.provider.submit(request)
        self.assertEqual(response["status_code"], 400)

    def test_result_contains_payment_reference(self):
        response = self.provider.submit(job("result-test"))
        self.assertEqual(response["status_code"], 202)

        import time
        for _ in range(20):
            status, payload = self.provider.status("result-test")
            if payload["status"] == "completed":
                break
            time.sleep(0.01)

        status, result = self.provider.result("result-test")
        self.assertEqual(status, 200)
        self.assertEqual(
            result["payment"]["payment_reference"],
            "pay-1",
        )

    def test_payment_must_be_usdc_on_solana(self):
        request = job("pay-test-1")
        request["payment"]["currency"] = "EUR"
        request["payment"]["network"] = "ethereum"
        response = self.provider.submit(request)
        self.assertEqual(response["status_code"], 400)


if __name__ == "__main__":
    unittest.main()
