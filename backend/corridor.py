# C:\TouchdownOld\FRMCS-RAIL-IQ\backend\corridor.py
# Author: Ahmad Sharique
# Email:  ahmad@iabg.de
# Project: FRMCS-RAIL-IQ — Episode 3: Network Risk & Response Orchestration

from dataclasses import dataclass
from typing import Optional


@dataclass
class Tower:
    id: int
    name: str
    lat: float
    lon: float
    risk_score: float = 0.0
    status: str = "GREEN"
    threat_type: Optional[str] = None
    threat_confidence: Optional[float] = None
    pki_status: str = "ACTIVE"
    ntn_standby: bool = False
    handover_target: Optional[int] = None
    last_event: Optional[str] = None


# 10 towers — Munich to Augsburg corridor
TOWERS: dict[int, Tower] = {
    1:  Tower(id=1,  name="München Hbf",   lat=48.1402, lon=11.5580),
    2:  Tower(id=2,  name="Pasing",         lat=48.1497, lon=11.4613),
    3:  Tower(id=3,  name="Lochhausen",     lat=48.1681, lon=11.3672),
    4:  Tower(id=4,  name="Dachau",         lat=48.2597, lon=11.4342),
    5:  Tower(id=5,  name="Schwabhausen",   lat=48.2991, lon=11.3100),
    6:  Tower(id=6,  name="Althegnenberg",  lat=48.2750, lon=11.1200),
    7:  Tower(id=7,  name="Moorenweis",     lat=48.2553, lon=11.0100),
    8:  Tower(id=8,  name="Geltendorf",     lat=48.0397, lon=10.9836),
    9:  Tower(id=9,  name="Kaufering",      lat=48.0833, lon=10.8700),
    10: Tower(id=10, name="Augsburg Hbf",   lat=48.3654, lon=10.8855),
}

# Corridor adjacency — each tower's direct neighbors
ADJACENCY: dict[int, list[int]] = {
    1:  [2],
    2:  [1, 3],
    3:  [2, 4],
    4:  [3, 5],
    5:  [4, 6],
    6:  [5, 7],
    7:  [6, 8],
    8:  [7, 9],
    9:  [8, 10],
    10: [9],
}


def reset_corridor():
    """Reset all towers to clean GREEN state."""
    for tower in TOWERS.values():
        tower.risk_score = 0.0
        tower.status = "GREEN"
        tower.threat_type = None
        tower.threat_confidence = None
        tower.pki_status = "ACTIVE"
        tower.ntn_standby = False
        tower.handover_target = None
        tower.last_event = None


if __name__ == "__main__":
    print("FRMCS Corridor loaded")
    print(f"Total towers: {len(TOWERS)}")
    for t in TOWERS.values():
        print(f"{t.id} - {t.name} ({t.status})")