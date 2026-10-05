import json, os
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
class XObserverAdapter:
    def execute(self,job):
        subject=job["subject"]["id"]; username=subject.lstrip("@"); window=job.get("constraints",{}).get("time_window",{}); max_results=int(job.get("constraints",{}).get("max_observations",25)); token=os.getenv("X_BEARER_TOKEN"); retrieved_at=now()
        if not token:
            return {"format":"structured_observations","summary":"Synthetic observation for contract testing; live X credentials are not configured.","observations":[{"subject":subject,"observation":"Synthetic data; live X credentials are not configured.","timestamp":retrieved_at,"source":"x"}],"provenance":[{"source":"x","reference":"mock://node002","observed_at":retrieved_at,"retrieved_at":retrieved_at}]}
        headers={"Authorization":f"Bearer {token}","Accept":"application/json"}
        with urlopen(Request(f"https://api.x.com/2/users/by/username/{username}",headers=headers),timeout=30) as response: data=json.loads(response.read().decode()).get("data")
        if not data or not data.get("id"): raise RuntimeError("X account could not be resolved from subject.id.")
        params={"max_results":max(10,min(max_results,100)),"tweet.fields":"id,text,author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,entities","expansions":"author_id,referenced_tweets.id","user.fields":"id,name,username"}
        if window.get("from"): params["start_time"]=window["from"]
        if window.get("to"): params["end_time"]=window["to"]
        with urlopen(Request(f"https://api.x.com/2/users/{data['id']}/tweets?{urlencode(params)}",headers=headers),timeout=30) as response: payload=json.loads(response.read().decode())
        if payload.get("errors") and not payload.get("data"): raise RuntimeError(payload["errors"][0].get("detail","X API returned an error."))
        retrieved_at=now(); observations=[]; provenance=[]
        for post in payload.get("data",[]):
            created=post.get("created_at"); post_id=post.get("id"); observations.append({"subject":subject,"observation":post.get("text",""),"timestamp":created,"source":"x"}); provenance.append({"source":"x","reference":f"https://x.com/i/web/status/{post_id}","observed_at":created,"retrieved_at":retrieved_at})
        return {"format":"structured_observations","summary":f"Observed {len(observations)} X posts for {subject}.","observations":observations,"provenance":provenance}
