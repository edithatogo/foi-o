# Experimental Mojo text/risk planning kernels.
# These functions avoid string parsing APIs so they remain stable across early Mojo toolchains.

fn token_estimate_from_chars(char_count: Int) -> Int:
    if char_count <= 0:
        return 1
    return (char_count + 3) // 4


fn risk_level_from_score(score: Int, has_health_identifier: Bool) -> String:
    if has_health_identifier:
        return "high"
    if score >= 5:
        return "high"
    if score >= 1:
        return "medium"
    return "low"


fn review_required_for_score(score: Int, has_health_identifier: Bool) -> Bool:
    if has_health_identifier:
        return True
    return score >= 1


fn can_machine_certify_safety_class(safety_class: String) -> Bool:
    # Current policy: even low-risk machine outputs can assist only; they do not
    # certify legal/process outcomes. This kernel intentionally returns False
    # for all classes until the human-certification boundary changes.
    return False
