# Experimental Mojo guardrail kernels for agent-action replay.
# These are intentionally small so they can survive rapid Mojo/MAX evolution.

fn is_dispositive_event(event_type: String) -> Bool:
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


fn severity_rank(severity: String) -> Int:
    if severity == "error":
        return 3
    if severity == "warning":
        return 2
    if severity == "info":
        return 1
    return 0


fn action_requires_review(safety_class: String, requires_human_certification: Bool) -> Bool:
    if requires_human_certification:
        return True
    if safety_class == "high":
        return True
    if safety_class == "prohibited":
        return True
    return False


fn can_replay_pass(error_count: Int) -> Bool:
    return error_count == 0
