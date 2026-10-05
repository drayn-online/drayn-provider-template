import time,unittest
from provider import Node002Provider
JOB={"job_id":"test-1","protocol_version":"0.2","capability":{"id":"social.x.observe","version":"0.2"},"consumer":{"consumer_id":"test-consumer"},"objective":{"type":"observation","question":"Observe activity."},"subject":{"type":"x_account","id":"@WormsOnAcid"},"constraints":{"time_window":{"from":"2026-09-30T00:00:00Z","to":"2026-09-30T23:59:59Z"}},"output":{"format":"structured_observations"},"payment":{"payment_reference":"pay-1","currency":"USDC","network":"solana","payer":"payer","payee":"payee"}}
class TestNode002(unittest.TestCase):
 def setUp(self):
  self.p=Node002Provider()
  class A:
   def execute(self,job): return {"format":"structured_observations","summary":"test","observations":[{"subject":job["subject"]["id"],"observation":"test","timestamp":"2026-09-30T00:00:00Z","source":"synthetic"}],"provenance":[{"source":"synthetic","reference":"mock://test","observed_at":"2026-09-30T00:00:00Z","retrieved_at":"2026-09-30T00:00:01Z"}]}
  self.p.adapter=A()
 def wait(self,id,status="completed"):
  for _ in range(100):
   s,p=self.p.status(id)
   if p["status"]==status:return s,p
   time.sleep(.01)
  return s,p
 def test_contract_job_completes(self):
  s,p=self.p.submit(JOB); self.assertEqual(s,202); s,p=self.wait("test-1"); self.assertEqual(p["status"],"completed"); s,r=self.p.result("test-1"); self.assertEqual(s,200); self.assertEqual(r["result"]["format"],"structured_observations"); self.assertEqual(r["payment"]["network"],"solana")
 def test_duplicate_is_idempotent(self): self.assertEqual(self.p.submit(JOB)[0],202); self.assertEqual(self.p.submit(JOB)[0],202)
 def test_missing_question_rejected(self): self.assertEqual(self.p.submit({**JOB,"job_id":"bad","objective":{"type":"observation"}})[0],400)
 def test_wrong_version_rejected(self): self.assertEqual(self.p.submit({**JOB,"job_id":"bad-version","protocol_version":"99"})[0],400)
