import io, logging, time, unittest
from provider import Node002Provider

JOB={"job_id":"test-1","protocol_version":"0.2","capability":{"id":"social.x.observe","version":"0.2"},"consumer":{"consumer_id":"test-consumer"},"objective":{"type":"observation","question":"Observe activity."},"subject":{"type":"x_account","id":"@WormsOnAcid"},"constraints":{"time_window":{"from":"2026-09-30T00:00:00Z","to":"2026-09-30T23:59:59Z"}},"output":{"format":"structured_observations"},"payment":{"payment_reference":"pay-1","currency":"USDC","network":"solana","payer":"payer","payee":"payee"}}

class TestNode002(unittest.TestCase):
 def setUp(self):
  self.p=Node002Provider()
  class A:
   def execute(self,job): return {"format":"structured_observations","summary":"test","observations":[{"subject":job["subject"]["id"],"observation":"test","timestamp":"2026-09-30T00:00:00Z","source":"synthetic"}],"provenance":[{"source":"synthetic","reference":"mock://test","observed_at":"2026-09-30T00:00:00Z","retrieved_at":"2026-09-30T00:00:01Z"}]}
  self.p.adapter=A()
  self.log_stream=io.StringIO()
  self.log_handler=logging.StreamHandler(self.log_stream)
  self.log_handler.setFormatter(logging.Formatter("%(message)s"))
  logging.getLogger("drayn.node002").addHandler(self.log_handler)
  logging.getLogger("drayn.node002").setLevel(logging.INFO)

 def tearDown(self):
  logging.getLogger("drayn.node002").removeHandler(self.log_handler)

 def wait(self,id,status="completed"):
  for _ in range(100):
   s,p=self.p.status(id)
   if p["status"]==status:return s,p
   time.sleep(.01)
  return s,p

 def test_contract_job_completes(self):
  s,p=self.p.submit(JOB); self.assertEqual(s,202); s,p=self.wait("test-1"); self.assertEqual(p["status"],"completed"); s,r=self.p.result("test-1"); self.assertEqual(s,200); self.assertEqual(r["result"]["format"],"structured_observations"); self.assertEqual(r["payment"]["network"],"solana")
  logs=self.log_stream.getvalue()
  self.assertIn("submission_received job_id=test-1 subject_type=x_account subject_id=@WormsOnAcid",logs)
  self.assertIn("time_window={'from': '2026-09-30T00:00:00Z', 'to': '2026-09-30T23:59:59Z'}",logs)
  self.assertIn("execution_started job_id=test-1 execution_id=exec_",logs)
  self.assertIn("state_transition job_id=test-1 state=accepted",logs)
  self.assertIn("state_transition job_id=test-1 state=running execution_id=exec_",logs)
  self.assertIn("state_transition job_id=test-1 state=completed execution_id=exec_",logs)
  self.assertIn("work_reference=work_",logs)

 def test_duplicate_is_idempotent(self):
  self.assertEqual(self.p.submit(JOB)[0],202); self.assertEqual(self.p.submit(JOB)[0],202); self.assertEqual(self.wait("test-1")[1]["status"],"completed")
  logs=self.log_stream.getvalue()
  self.assertIn("duplicate_submission job_id=test-1 existing_status=running no_new_execution=true",logs)
  self.assertEqual(logs.count("execution_started job_id=test-1"),1)

 def test_missing_question_rejected(self): self.assertEqual(self.p.submit({**JOB,"job_id":"bad","objective":{"type":"observation"}})[0],400)
 def test_wrong_version_rejected(self): self.assertEqual(self.p.submit({**JOB,"job_id":"bad-version","protocol_version":"99"})[0],400)

 def test_refused_logs_error(self):
  self.p.adapter=None
  job={**JOB,"job_id":"refused-1"}
  s,p=self.p.submit(job)
  self.assertEqual(s,409); self.assertEqual(p["status"],"refused"); self.assertEqual(p["error"]["code"],"CAPABILITY_UNAVAILABLE")
  s,p=self.p.status("refused-1"); self.assertEqual(p["error"]["code"],"CAPABILITY_UNAVAILABLE")
  logs=self.log_stream.getvalue()
  self.assertIn("state_transition job_id=refused-1 state=refused error_code=CAPABILITY_UNAVAILABLE",logs)

 def test_failed_logs_error(self):
  class F:
   def execute(self,job): raise RuntimeError("controlled test failure")
  self.p.adapter=F()
  job={**JOB,"job_id":"failed-1"}
  s,p=self.p.submit(job); self.assertEqual(s,202); s,p=self.wait("failed-1","failed"); self.assertEqual(p["error"]["code"],"EXECUTION_FAILED")
  logs=self.log_stream.getvalue()
  self.assertIn("execution_started job_id=failed-1 execution_id=exec_",logs)
  self.assertIn("state_transition job_id=failed-1 state=failed execution_id=exec_",logs)
  self.assertIn("error_code=EXECUTION_FAILED",logs)

if __name__=="__main__": unittest.main()
