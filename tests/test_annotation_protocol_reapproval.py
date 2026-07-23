import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/annotation-protocol-reapproval.pending.json"


def test_protocol_reapproval_packet_is_fail_closed_and_current_hash_pinned() -> None:
    packet = json.loads(PACKET.read_text())
    protocol = ROOT / packet["protocol_path"]
    digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    assert digest == packet["current_protocol_sha256"]
    assert packet["status"] == "pending_human_reapproval"
    assert packet["change_requires_reapproval"] is True
    assert packet["execution_authorized"] is False
    assert packet["promotion_allowed"] is False
    assert digest != packet["prior_approved_protocol_sha256"]
