# C:\TouchdownOld\FRMCS-RAIL-IQ\backend\risk_engine.py
# Author: Ahmad Sharique
# Email:  ahmad@iabg.de
# Project: FRMCS-RAIL-IQ — Episode 3: Network Risk & Response Orchestration

from datetime import datetime, timezone
from corridor import TOWERS, ADJACENCY

# Risk score thresholds
THRESHOLD_RED    = 0.6
THRESHOLD_YELLOW = 0.3

# Adjacency weight — how much a neighbor's threat bleeds into your score
ADJACENCY_WEIGHT = 0.4

# Confidence required to trigger PKI pause and handover
ACTION_THRESHOLD = 0.7


def _status_from_score(score: float) -> str:
    if score >= THRESHOLD_RED:
        return "RED"
    elif score >= THRESHOLD_YELLOW:
        return "YELLOW"
    return "GREEN"


def _corridor_status() -> str:
    """Overall corridor label based on worst tower."""
    statuses = [t.status for t in TOWERS.values()]
    if "RED" in statuses:
        return "CRITICAL" if statuses.count("RED") >= 2 else "ELEVATED"
    if "YELLOW" in statuses:
        return "ELEVATED"
    return "NOMINAL"


def process_threat_event(
    tower_id: int,
    event_type: str,
    confidence: float,
    timestamp: str = None
) -> dict:
    """
    Core risk engine entry point.
    Takes a threat event, updates corridor state, returns action log.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    actions = []

    # --- Step 1: Update the affected tower ---
    tower = TOWERS[tower_id]
    tower.threat_type = event_type
    tower.threat_confidence = confidence
    tower.risk_score = confidence
    tower.status = _status_from_score(tower.risk_score)
    tower.last_event = timestamp

    actions.append({
        "timestamp": timestamp,
        "tower_id": tower_id,
        "tower_name": tower.name,
        "event": f"{event_type} detected",
        "confidence": confidence,
        "new_status": tower.status,
        "action": "TOWER_STATUS_UPDATED"
    })

    # --- Step 2: Propagate adjacency risk ---
    for neighbor_id in ADJACENCY[tower_id]:
        neighbor = TOWERS[neighbor_id]
        adjacency_score = confidence * ADJACENCY_WEIGHT
        # Only escalate, never de-escalate via adjacency
        if adjacency_score > neighbor.risk_score:
            neighbor.risk_score = adjacency_score
            neighbor.status = _status_from_score(neighbor.risk_score)
            actions.append({
                "timestamp": timestamp,
                "tower_id": neighbor_id,
                "tower_name": neighbor.name,
                "event": "adjacency risk propagated",
                "confidence": round(adjacency_score, 3),
                "new_status": neighbor.status,
                "action": "ADJACENCY_RISK_UPDATED"
            })

    # --- Step 3: Deterministic response actions ---
    if confidence >= ACTION_THRESHOLD and event_type in ("jamming", "spoofing", "replay"):

        # Pause PKI on the affected tower
        tower.pki_status = "PAUSED"
        actions.append({
            "timestamp": timestamp,
            "tower_id": tower_id,
            "tower_name": tower.name,
            "event": "PKI AT issuance paused",
            "confidence": confidence,
            "new_status": tower.status,
            "action": "PKI_PAUSED"
        })

        # Prepare handover to best adjacent neighbor (lowest risk score)
        neighbors = ADJACENCY[tower_id]
        if neighbors:
            best = min(neighbors, key=lambda nid: TOWERS[nid].risk_score)
            tower.handover_target = best
            actions.append({
                "timestamp": timestamp,
                "tower_id": tower_id,
                "tower_name": tower.name,
                "event": f"handover prepared → Tower {best} ({TOWERS[best].name})",
                "confidence": confidence,
                "new_status": tower.status,
                "action": "HANDOVER_PREPARED"
            })

        # NTN standby on the affected tower
        tower.ntn_standby = True
        actions.append({
            "timestamp": timestamp,
            "tower_id": tower_id,
            "tower_name": tower.name,
            "event": "NTN failover on standby",
            "confidence": confidence,
            "new_status": tower.status,
            "action": "NTN_STANDBY"
        })

    corridor_status = _corridor_status()

    return {
        "corridor_status": corridor_status,
        "affected_tower": tower_id,
        "actions": actions
    }


if __name__ == "__main__":
    print("=== Risk Engine Test ===")
    print("Simulating jamming on Tower 4 (Dachau), confidence 0.83\n")

    result = process_threat_event(
        tower_id=4,
        event_type="jamming",
        confidence=0.83
    )

    print(f"Corridor Status: {result['corridor_status']}")
    print(f"\nActions taken ({len(result['actions'])}):")
    for a in result["actions"]:
        print(f"  [{a['timestamp']}] {a['tower_name']} — {a['event']} → {a['action']}")

    print("\nTower states after event:")
    for t in TOWERS.values():
        print(f"  Tower {t.id} ({t.name}): {t.status} | PKI: {t.pki_status} | NTN: {t.ntn_standby}")