"""
network.py — In-memory network simulation state.

States: NORMAL | DEGRADED | OFFLINE
Admin controls latency (ms) and packet_loss (%).
"""

import random
import time

# ---------------------------------------------------------------------------
# Singleton state (module-level, lives in process memory)
# ---------------------------------------------------------------------------
_state = {
    "network_state": "NORMAL",
    "latency": 0,
    "packet_loss": 0,
}


def get_state() -> dict:
    return dict(_state)


def set_state(network_state: str, latency: int = 0, packet_loss: int = 0) -> None:
    _state["network_state"] = network_state.upper()
    _state["latency"] = max(0, int(latency))
    _state["packet_loss"] = max(0, min(100, int(packet_loss)))


def simulate_transmission() -> dict:
    """
    Simulate sending one packet through the current network.

    Returns:
        {"delivered": bool, "delay_ms": int, "reason": str}
    """
    state = _state["network_state"]

    if state == "OFFLINE":
        return {"delivered": False, "delay_ms": 0, "reason": "Network OFFLINE — message queued locally"}

    if state == "DEGRADED":
        # Apply packet-loss roll
        if random.randint(1, 100) <= _state["packet_loss"]:
            return {"delivered": False, "delay_ms": 0, "reason": "Packet lost (simulated degraded network)"}
        delay = _state["latency"] + random.randint(0, 200)
        time.sleep(min(delay / 1000, 0.5))   # cap sleep at 500 ms so UI isn't blocked
        return {"delivered": True, "delay_ms": delay, "reason": f"Delivered with {delay} ms latency (degraded)"}

    # NORMAL
    delay = random.randint(5, 30)
    return {"delivered": True, "delay_ms": delay, "reason": f"Delivered normally ({delay} ms)"}
