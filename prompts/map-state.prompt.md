# Prompt: map source request state

Map a source-platform request state to the global FOI-O core using an explicit,
versioned jurisdiction profile. The model originated in New Zealand; Australian
Commonwealth and subdivision adapters are later jurisdiction iterations.

Rules:

- Preserve `source_state` exactly.
- Require `jurisdiction`, `regime`, and `jurisdiction_profile` inputs.
- Use only the mapping declared by the selected profile.
- `mappings/alaveteli-state-map.yaml` is an NZ/FYI source mapping, not a global
  default and not an Australian mapping.
- Never infer legal equivalence between NZ, Australian Commonwealth, state, or
  territory states.
- Inspect correspondence evidence when available.
- Prefer `unknown` over overconfident mapping.
- Explain uncertainty in `state_mapping.notes`.
- Stop with a blocking warning when the selected profile is missing,
  incompatible, or not promoted for the requested capability.
