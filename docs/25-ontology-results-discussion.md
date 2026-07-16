# FOI-O NZ results, discussion, and conclusion

## Results

The current global maturation slice preserves the NZ origin, incorporates
Australian jurisdiction iterations, and adds the publication evidence layer that
was planned but not yet explicit: protocol, evidence inventory, claims register,
source register, terminology crosswalk, coverage matrix, generated asset index,
asset manifest schema, and a small evidence-network graph export.

| Result area | Current result | Evidence |
| --- | --- | --- |
| Core/profile boundary | FOI-O is global; NZ is the mature reference implementation and Australian adapters remain candidate-only. | `README.md`, `docs/24-ontology-methods-protocol.md` |
| Competency questions | Ten competency questions cover source-state preservation, candidate events, human certification, clock warnings, legal source versioning, PSC derivability, public-data limits, asset provenance, and global-claim boundaries. | `docs/24-ontology-methods-protocol.md` |
| Evidence inventory | Repo-local materials and external gates are catalogued. | `docs/24-ontology-methods-evidence-inventory.md` |
| Claims register | Supported, unsupported, and design-intent claims are separated. | `docs/24-ontology-claims-register.md` |
| Terminology crosswalk | Source states, FOI-O states, event types, assertion status, legal terms, validation terms, and publication terms are aligned. | `docs/24-ontology-terminology-crosswalk.md` |
| Coverage matrix | Schema, ontology, SKOS, SHACL, examples, tests, and boundaries are tied together. | `docs/24-schema-ontology-coverage-matrix.md` |
| Generated assets | Captions, text alternatives, source inputs, commands, provenance, and locations are recorded. | `docs/25-generated-asset-index.md`, `examples/generated-asset-manifest.foi-o-publication.json` |
| Graph/network data | A small ontology/evidence graph export is committed for Cosmograph-style downstream use, with Mermaid fallback. | `examples/graph-export.foi-o-evidence-network.json`, `docs/assets/foi-o-evidence-network.mmd` |

## Validation Evidence

The maturation layer is designed to pass the same repo-local validation
discipline as the rest of the project:

```bash
uv run python scripts/validate_examples.py
uv run foi-o-nz validate-repo
uv run foi-o-nz schema-drift
uv run pytest -q tests/test_ontology_maturation_plan.py
```

Full publication readiness still requires the full test suite, Ruff checks,
Ruff format checks, available Mojo/Pixi checks, and any submission-specific
checks required by the journal or arXiv route.

## Discussion

The main improvement is evidentiary. The repository already contained schemas,
ontology files, SKOS vocabularies, SHACL shapes, examples, tests, agent
contracts, release metadata, and submission documents. The added layer explains
how those pieces support ontology-development claims and which claims remain
outside repo-local proof.

The core/profile boundary is especially important. The project can reasonably
describe FOI-O as a reusable method because the model separates process events,
source evidence, assertion status, provenance, and human certification in a way
that is not unique to New Zealand. It cannot yet claim empirical validation for
other jurisdictions. That distinction lets the project remain ambitious without
overstating the current evidence.

The generated asset manifest also matters. Diagrams, tables, and graph data are
now treated as reproducible source artefacts with captions, text alternatives,
commands, and provenance. This makes the later manuscript and supplement easier
to review and reduces the chance that figures drift away from the repository
evidence.

## Limitations

The results remain repo-local. They do not prove live FYI/archive intake, live
legal-source freshness, human-reviewed gold-standard completion, registry
publication, arXiv upload, journal acceptance, official PSC reporting, legal
correctness, or cross-jurisdiction transferability.

The empirical task sets remain annotation tasks until reviewed records,
reviewer process, adjudication notes, and provenance are available.

## Conclusion

The global ontology package, grounded in NZ and iterated through Australia, is
now better positioned for publication work
because its claims, evidence, terminology, competency questions, and generated
assets are explicit. The next substantive implementation step should be the
human-reviewed empirical task sets and independently promoted jurisdiction profiles.
