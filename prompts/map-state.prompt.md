# Prompt: map source request state

Map a source FYI/Alaveteli request state to a FOI-O NZ normalised state.

Rules:

- Preserve `source_state` exactly.
- Use `mappings/alaveteli-state-map.yaml` only as a starting point.
- Inspect correspondence evidence when available.
- Prefer `unknown` over overconfident mapping.
- Explain uncertainty in `state_mapping.notes`.
