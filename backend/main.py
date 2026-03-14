# C:\TouchdownOld\FRMCS-RAIL-IQ\backend\main.py
# Author: Ahmad Sharique
# Email:  ahmad@iabg.de
# Project: FRMCS-RAIL-IQ — Episode 3: Network Risk & Response Orchestration

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from corridor import TOWERS, ADJACENCY, reset_corridor
from risk_engine import process_threat_event, _corridor_status
from event_log import append_from_actions, get_log, clear_log, log_size

app = FastAPI(
    title="FRMCS-RAIL-IQ",
    description="Network Risk & Response Orchestration — Munich-Augsburg Corridor",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request models ---

class ThreatEventRequest(BaseModel):
    tower_id: int
    event_type: str          # jamming / spoofing / replay
    confidence: float
    timestamp: Optional[str] = None


# --- Routes ---

@app.get("/")
def root():
    return {
        "project": "FRMCS-RAIL-IQ",
        "author": "Ahmad Sharique",
        "email": "ahmad@iabg.de",
        "status": "online"
    }


@app.get("/corridor/state")
def corridor_state():
    """Return current state of all 10 towers."""
    return {
        "corridor_status": _corridor_status(),
        "towers": [
            {
                "id":                 t.id,
                "name":               t.name,
                "lat":                t.lat,
                "lon":                t.lon,
                "status":             t.status,
                "risk_score":         round(t.risk_score, 3),
                "threat_type":        t.threat_type,
                "threat_confidence":  t.threat_confidence,
                "pki_status":         t.pki_status,
                "ntn_standby":        t.ntn_standby,
                "handover_target":    t.handover_target,
                "last_event":         t.last_event,
            }
            for t in TOWERS.values()
        ]
    }


@app.get("/corridor/timeline")
def corridor_timeline(limit: int = 50):
    """Return the event log, newest first."""
    return {
        "total_events": log_size(),
        "events": get_log(limit=limit)
    }


@app.post("/corridor/simulate")
def simulate_threat(req: ThreatEventRequest):
    """Trigger a synthetic threat event — main demo endpoint."""
    if req.tower_id not in TOWERS:
        raise HTTPException(status_code=404, detail=f"Tower {req.tower_id} not found")
    if req.confidence < 0.0 or req.confidence > 1.0:
        raise HTTPException(status_code=400, detail="Confidence must be between 0.0 and 1.0")

    result = process_threat_event(
        tower_id=req.tower_id,
        event_type=req.event_type,
        confidence=req.confidence,
        timestamp=req.timestamp or datetime.now(timezone.utc).isoformat()
    )
    append_from_actions(result["actions"])

    return {
        "corridor_status": result["corridor_status"],
        "affected_tower":  req.tower_id,
        "actions_taken":   len(result["actions"]),
        "actions":         result["actions"]
    }


@app.post("/corridor/reset")
def corridor_reset():
    """Reset corridor to clean GREEN state and wipe event log."""
    reset_corridor()
    clear_log()
    return {
        "message": "Corridor reset to GREEN",
        "corridor_status": _corridor_status()
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "towers": len(TOWERS),
        "log_entries": log_size()
    }