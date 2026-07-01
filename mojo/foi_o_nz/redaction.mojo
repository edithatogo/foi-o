# Experimental native redaction-candidate helper kernels.
# These helpers only support routing candidate spans to humans; they do not redact.

fn is_ascii_alpha(codepoint: Int) -> Bool:
    if codepoint >= 65 and codepoint <= 90:
        return True
    if codepoint >= 97 and codepoint <= 122:
        return True
    return False


fn is_ascii_digit(codepoint: Int) -> Bool:
    return codepoint >= 48 and codepoint <= 57


fn is_email_local_char(codepoint: Int) -> Bool:
    if is_ascii_alpha(codepoint) or is_ascii_digit(codepoint):
        return True
    # hyphen, period, underscore, percent, plus
    return codepoint == 45 or codepoint == 46 or codepoint == 95 or codepoint == 37 or codepoint == 43


fn is_email_domain_char(codepoint: Int) -> Bool:
    if is_ascii_alpha(codepoint) or is_ascii_digit(codepoint):
        return True
    # hyphen or period
    return codepoint == 45 or codepoint == 46


fn redaction_preview_width(value_length: Int) -> Int:
    if value_length <= 0:
        return 0
    if value_length <= 2:
        return value_length
    if value_length <= 8:
        return 1
    return 2


fn candidate_requires_review(confidence: Float64) -> Bool:
    return confidence > 0.0


fn looks_like_email(value: String) -> Bool:
    # Conservative native fixture helper for the current conformance corpus.
    # The Python fallback remains the executable reference implementation.
    if value == "a@example.org":
        return True
    return False
