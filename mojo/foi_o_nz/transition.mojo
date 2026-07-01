# Experimental Mojo transition kernels.
# These are diagnostic helpers; the Python state machine remains the source of
# full transition-policy detail until generated Mojo tables are in place.

fn transition_rank(state: String) -> Int:
    if state == "Drafted":
        return 0
    if state == "Submitted":
        return 1
    if state == "Received":
        return 2
    if state == "Acknowledged":
        return 3
    if state == "ValidityChecking" or state == "AwaitingClarification":
        return 4
    if state == "Valid":
        return 5
    if state == "SearchPlanning":
        return 6
    if state == "Searching":
        return 7
    if state == "DocumentsIdentified" or state == "ConsultationRequired":
        return 8
    if state == "ThirdPartyConsultation" or state == "ChargeAssessment" or state == "ExtensionApplied":
        return 9
    if state == "DecisionDrafting":
        return 10
    if state == "HumanDecisionRequired":
        return 11
    if state == "DecisionApproved":
        return 12
    if state == "ReleasedInFull" or state == "ReleasedInPart" or state == "Refused" or state == "NoDocumentsFound" or state == "Withdrawn" or state == "Closed":
        return 13
    return -1


fn is_forward_transition(from_state: String, to_state: String) -> Bool:
    var source_rank = transition_rank(from_state)
    var target_rank = transition_rank(to_state)
    if source_rank < 0 or target_rank < 0:
        return False
    return target_rank >= source_rank
