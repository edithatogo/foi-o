# Experimental Mojo retrieval planning kernels.
# These are small numeric helpers for eventual native retrieval/reranking paths.


def blend_scores(
    lexical_score: Float64, vector_score: Float64, lexical_weight: Float64
) -> Float64:
    var weight = lexical_weight
    if weight < 0.0:
        weight = 0.0
    if weight > 1.0:
        weight = 1.0
    return weight * lexical_score + (1.0 - weight) * vector_score


def normalise_cosine(cosine_score: Float64) -> Float64:
    if cosine_score <= -1.0:
        return 0.0
    if cosine_score >= 1.0:
        return 1.0
    return (cosine_score + 1.0) / 2.0


def should_include_hit(score: Float64, min_score: Float64) -> Bool:
    return score >= min_score


def clamp_top_k(top_k: Int, max_top_k: Int) -> Int:
    if top_k <= 0:
        return 1
    if top_k > max_top_k:
        return max_top_k
    return top_k
