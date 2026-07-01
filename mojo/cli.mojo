from foi_o_nz.state import can_agent_certify_event, normalise_alaveteli_state, requires_human_certification


def main():
    print("FOI-O NZ Mojo smoke")
    print("successful ->", normalise_alaveteli_state("successful"))
    print("ReleaseMade requires human certification:", requires_human_certification("ReleaseMade"))
    print("Agent can certify ReleaseMade:", can_agent_certify_event("ReleaseMade"))
