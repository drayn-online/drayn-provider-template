import time
import unittest

from capabilities import X_OBSERVE
from provider import DRAYNProvider


class SyntheticAdapter:
    def execute(self, job):
        return {
            "format": "structured_observations",
            "summary": "Synthetic test result.",
            "observations": [{
                "subject": job["subject"]["id"],
                "observation": "test",
                "timestamp": "2026-09-30T00:00:00Z",
                "source": "synthetic",
            }],
            "provenance": [{
                "source": "synthetic",
                "reference": "mock://source-1",
                "observed_at": "2026-09-30T00:00:00Z",
                "retrieved_at": "2026-09-30T00:00:01Z",
            }],
        }


def job(job_id="job-1"):
    return {
        "job_id": job_id,
        "protocol_version": "0.2",
        "capability": {"id": X_OBSERVE.id, "version": X_OBSERVE.version},
        "consumer": {"consumer_id": "test-consumer"},
        "objective": {
            "type": "observation",
            "question": "Observe activity.",
        },
        "subject": {"type": "x_account", "id": "@WormsOnAcid"},
        "constraints": {
            "time_window": {
                "from": "2026-09-30T00:00:00Z",
                "to": "2026-09-30T23:59:59Z",
            },
            "max_observations": 25,
        },
        "output": {"format": "structured_observations"},
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

    def wait_for_status(self, job_id, expected="completed"):
        for _ in range(100):
            status, payload = self.provider.status(job_id)
            if payload["status"] == expected:
                return status, payload
            time.sleep(0.01)
        return status, payload

    def test_accepts_contract_shaped_observation_job(self):
        response = self.provider.submit(job())
        self.assertEqual(response["status_code"], 202)

    def test_subject_is_job_scoped(self):
        request = job("subject-test")
        request["subject"]["id"] = "@DifferentAccount"
        response = self.provider.submit(request)
        self.assertEqual(response["status_code"], 202)

    def test_duplicate_job_id_is_idempotent(self):
        first = self.provider.submit(job("same"))
        second = self.provider.submit(job("same"))
        self.assertEqual(first["status_code"], 202)
        self.assertEqual(second["status_code"], 202)

    def test_wrong_capability_is_rejected(self):
        request = job("wrong-capability")
        request["capability"] = {"id": "intelligence.research", "version": "0.2"}
        response = self.provider.submit(request)
        self.assertEqual(response["status_code"], 400)

    def test_missing_objective_question_is_rejected(self):
        request = job("missing-question")
        del request["objective"]["question"]
        response = self.provider.submit(request)
        self.assertEqual(response["status_code"], 400)

    def test_missing_output_format_is_rejected(self):
        request = job("missing-format")
        del request["output"]["format"]
        response = self.provider.submit(request)
        self.assertEqual(response["status_code"], 400)

    def test_wrong_protocol_version_is_rejected(self):
        request = job("wrong-protocol")
        request["protocol_version"] = "99"
        response = self.provider.submit(request)
        self.assertEqual(response["status_code"], 400)

    def test_wrong_capability_version_is_rejected(self):
        request = job("wrong-capability-version")
        request["capability"]["version"] = "99"
        response = self.provider.submit(request)
        self.assertEqual(response["status_code"], 400)

    def test_completed_result_has_canonical_shape_and_payment(self):
        response = self.provider.submit(job("result-test"))
        self.assertEqual(response["status_code"], 202)

        status, payload = self.wait_for_status("result-test")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "completed")

        status, result = self.provider.result("result-test")
        self.assertEqual(status, 200)
        self.assertEqual(result["result"]["format"], "structured_observations")
        self.assertIn("observations", result["result"])
        self.assertIsInstance(result["provenance"], list)
        self.assertEqual(result["payment"]["payment_reference"], "pay-1")
        self.assertEqual(result["payment"]["currency"], "USDC")
        self.assertEqual(result["payment"]["network"], "solana")

    def test_failed_status_exposes_error(self):
        class FailingAdapter:
            def execute(self, job):
                raise RuntimeError("synthetic failure")

        provider = DRAYNProvider(
            "provider-fail",
            {X_OBSERVE.id: {
                "id": X_OBSERVE.id,
                "version": X_OBSERVE.version,
                "description": X_OBSERVE.description,
            }},
        )
        provider.register_adapter(X_OBSERVE.id, FailingAdapter())
        provider.submit(job("failure-test"))

        status, payload = self.wait_for_status("failure-test", "failed")
        self.assertEqual(status, 200)
        self.assertEqual(payload["error"]["code"], "EXECUTION_FAILED")
        self.assertEqual(payload["error"]["message"], "synthetic failure")

    def test_payment_must_be_usdc_on_solana(self):
        request = job("pay-test")
        request["payment"]["currency"] = "EUR"
        response = self.provider.submit(request)
        self.assertEqual(response["status_code"], 400)


if __name__ == "__main__":
    unittest.main()
