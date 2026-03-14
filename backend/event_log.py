# C:\TouchdownOld\FRMCS-RAIL-IQ\backend\event_log.py
# Author: Ahmad Sharique
# Email:  ahmad@iabg.de
# Project: FRMCS-RAIL-IQ — Episode 3: Network Risk & Response Orchestration

from datetime import datetime, timezone
from typing import Optional

# In-memory event log — list of dicts, newest appended last
_log: list[dict] = []
_sequence: int = 0


def append_event(
    tower_id: int,
    tower_name: str,
    event: str,
    action: str,
    confidence: Optional[float],
    status: str,
    timestamp: Optional[str] = None
) -> dict:
    """Append one event entry to the log. Returns the entry."""
    global _sequence
    _sequence += 1

    entry = {
        "seq":         _sequence,
        "timestamp":   timestamp or datetime.now(timezone.utc).isoformat(),
        "tower_id":    tower_id,
        "tower_name":  tower_name,
        "event":       event,
        "action":      action,
        "confidence":  confidence,
        "status":      status
    }
    _log.append(entry)
    return entry


def append_from_actions(actions: list[dict]) -> None:
    """Bulk-append the actions list returned by the risk engine."""
    for a in actions:
        append_event(
            tower_id=a["tower_id"],
            tower_name=a["tower_name"],
            event=a["event"],
            action=a["action"],
            confidence=a.get("confidence"),
            status=a["new_status"],
            timestamp=a.get("timestamp")
        )


def get_log(limit: int = 50) -> list[dict]:
    """Return the last N entries, newest first."""
    return list(reversed(_log[-limit:]))


def clear_log() -> None:
    """Wipe the log and reset sequence counter."""
    global _sequence
    _log.clear()
    _sequence = 0


def log_size() -> int:
    return len(_log)


if __name__ == "__main__":
    from risk_engine import process_threat_event

    print("=== Event Log Test ===")
    result = process_threat_event(
        tower_id=4,
        event_type="jamming",
        confidence=0.83
    )
    append_from_actions(result["actions"])

    print(f"Log size: {log_size()}")
    print("\nTimeline (newest first):")
    for entry in get_log():
        print(f"  #{entry['seq']} [{entry['timestamp']}] "
              f"Tower {entry['tower_id']} ({entry['tower_name']}) — "
              f"{entry['event']} | {entry['action']} | {entry['status']}")