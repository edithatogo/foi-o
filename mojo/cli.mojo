from foi_o_nz.clock import is_machine_working_day
from foi_o_nz.guardrail import action_requires_review
from foi_o_nz.hash import bounded_bucket, fnv1a64_seed, fnv1a64_update
from foi_o_nz.redaction import redaction_preview_width
from foi_o_nz.retrieval import blend_scores
from foi_o_nz.state import can_agent_certify_event, normalise_alaveteli_state, requires_human_certification
from foi_o_nz.text import token_estimate_from_chars
from foi_o_nz.transition import is_forward_transition


def main():
    print("FOI-O NZ Mojo deterministic kernel smoke")
    print("successful ->", normalise_alaveteli_state("successful"))
    print("ReleaseMade requires human certification:", requires_human_certification("ReleaseMade"))
    print("Agent can certify ReleaseMade:", can_agent_certify_event("ReleaseMade"))
    print("Monday 2026-06-01 working day:", is_machine_working_day(0, 6, 1))
    print("Token estimate for 17 chars:", token_estimate_from_chars(17))
    print("Blend score:", blend_scores(2.0, 1.0, 0.5))
    print("Action high-risk requires review:", action_requires_review("high", False))
    print("Received -> Searching forward:", is_forward_transition("Received", "Searching"))
    print("Redaction preview width 12:", redaction_preview_width(12))
    var digest = fnv1a64_update(fnv1a64_seed(), UInt8(102))
    print("FNV bucket:", bounded_bucket(digest, 16))
