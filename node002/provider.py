import logging, secrets, threading, uuid
from datetime import datetime, timezone
from schemas import validate_job

logger = logging.getLogger("drayn.node002")

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _request_evidence(request):
    subject = request.get("subject", {})
    constraints = request.get("constraints", {})
    return (
        f"job_id={request.get('job_id')} "
        f"subject_type={subject.get('type')} "
        f"subject_id={subject.get('id')} "
        f"time_window={constraints.get('time_window')}"
    )

class Node002Provider:
    def __init__(self):
        self.provider_id = "drayn-node-002"; self.token = secrets.token_urlsafe(32); self.jobs = {}; self.lock = threading.Lock(); self.adapter = None

    def submit(self, request):
        ok, message = validate_job(request)
        if not ok:
            logger.info("submission_rejected job_id=%s error_code=INVALID_REQUEST", request.get("job_id"))
            return 400, {"error":{"code":"INVALID_REQUEST","message":message}}
        job_id = request["job_id"]
        logger.info("submission_received %s", _request_evidence(request))
        with self.lock:
            if job_id in self.jobs:
                job=self.jobs[job_id]
                logger.info("duplicate_submission job_id=%s existing_status=%s no_new_execution=true", job_id, job["status"])
                payload={"job_id":job_id,"provider_id":self.provider_id,"status":job["status"]}
                if job.get("error"): payload["error"]=job["error"]
                return 202,payload
            if self.adapter is None:
                error={"code":"CAPABILITY_UNAVAILABLE","message":"social.x.observe is not available."}
                self.jobs[job_id]={"request":request,"status":"refused","error":error}
                logger.info("state_transition job_id=%s state=refused error_code=%s", job_id, error["code"])
                return 409,{"job_id":job_id,"provider_id":self.provider_id,"status":"refused","error":error}
            self.jobs[job_id]={"request":request,"status":"accepted","accepted_at":now()}
            logger.info("state_transition job_id=%s state=accepted", job_id)
        threading.Thread(target=self._execute,args=(job_id,),daemon=True).start()
        return 202,{"job_id":job_id,"provider_id":self.provider_id,"status":"accepted"}

    def _execute(self,job_id):
        execution_id=f"exec_{uuid.uuid4().hex}"
        with self.lock:
            self.jobs[job_id]["status"]="running"
            self.jobs[job_id]["started_at"]=now()
            self.jobs[job_id]["execution_id"]=execution_id
            request=self.jobs[job_id]["request"]
        logger.info("execution_started job_id=%s execution_id=%s", job_id, execution_id)
        logger.info("state_transition job_id=%s state=running execution_id=%s", job_id, execution_id)
        try:
            result=self.adapter.execute(request)
            work_reference=f"work_{uuid.uuid4().hex[:12]}"
            with self.lock:
                self.jobs[job_id].update(status="completed",completed_at=now(),work_reference=work_reference,result=result)
            logger.info("state_transition job_id=%s state=completed execution_id=%s work_reference=%s", job_id, execution_id, work_reference)
        except Exception as exc:
            error={"code":"EXECUTION_FAILED","message":str(exc)}
            with self.lock:
                self.jobs[job_id].update(status="failed",completed_at=now(),error=error)
            logger.info("state_transition job_id=%s state=failed execution_id=%s error_code=%s", job_id, execution_id, error["code"])

    def status(self,job_id):
        with self.lock: job=self.jobs.get(job_id)
        if not job: return 404,{"error":{"code":"JOB_NOT_FOUND","message":"Job does not exist."}}
        payload={"job_id":job_id,"provider_id":self.provider_id,"status":job["status"]}
        if job.get("error"): payload["error"]=job["error"]
        return 200,payload

    def result(self,job_id):
        with self.lock: job=self.jobs.get(job_id)
        if not job: return 404,{"error":{"code":"JOB_NOT_FOUND","message":"Job does not exist."}}
        if job["status"]!="completed": return 409,{"error":{"code":"RESULT_NOT_READY","message":"Only completed jobs have results."}}
        request,result=job["request"],job["result"]
        return 200,{"job_id":job_id,"provider_id":self.provider_id,"capability":request["capability"],"status":"completed","result":result,"provenance":result.get("provenance",[]),"accounting":{"accepted_at":job["accepted_at"],"started_at":job["started_at"],"completed_at":job["completed_at"],"work_reference":job["work_reference"]},"payment":request["payment"]}
