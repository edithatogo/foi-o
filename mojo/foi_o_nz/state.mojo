# Experimental Mojo kernel for deterministic FOI-O NZ state and boundary checks.
# Keep this layer small while Mojo/MAX APIs evolve.

fn normalise_alaveteli_state(source_state: String) -> String:
    if source_state == "waiting_response":
        return "Received"
    if source_state == "waiting_clarification":
        return "AwaitingClarification"
    if source_state == "gone_postal":
        return "Searching"
    if source_state == "internal_review":
        return "InternalReviewRequested"
    if source_state == "successful":
        return "ReleasedInFull"
    if source_state == "partially_successful":
        return "ReleasedInPart"
    if source_state == "rejected":
        return "Refused"
    if source_state == "not_held":
        return "NoDocumentsFound"
    if source_state == "information_not_held":
        return "NoDocumentsFound"
    if source_state == "user_withdrawn":
        return "Withdrawn"
    if source_state == "not_foi":
        return "Closed"
    return "Unknown"


fn requires_human_certification(event_type: String) -> Bool:
    if event_type == "HumanDecisionCertified":
        return True
    if event_type == "DecisionCommunicated":
        return True
    if event_type == "ReleaseMade":
        return True
    if event_type == "RefusalCommunicated":
        return True
    if event_type == "ChargeNoticeSent":
        return True
    if event_type == "ExtensionNotified":
        return True
    if event_type == "TransferNotified":
        return True
    return False


fn can_agent_certify_event(event_type: String) -> Bool:
    # Agents may draft or flag these events, but they must not certify them.
    return not requires_human_certification(event_type)
