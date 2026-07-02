# Experimental epistemic-status and confidence helper kernels.
# These are process-support helpers only; they never certify legal outcomes.


def assertion_status_rank(status: String) -> Int:
    if status == "unknown":
        return 0
    if status == "inferred":
        return 1
    if status == "asserted":
        return 2
    if status == "observed":
        return 3
    if status == "certified":
        return 4
    return -1


def confidence_band(score: Float64) -> String:
    if score <= 0.0:
        return "none"
    if score < 0.5:
        return "low"
    if score < 0.8:
        return "medium"
    return "high"


def can_agent_assert_status(status: String) -> Bool:
    if status == "observed":
        return True
    if status == "inferred":
        return True
    if status == "asserted":
        return True
    return False
