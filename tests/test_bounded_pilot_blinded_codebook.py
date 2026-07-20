import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
CODEBOOK = ROOT / "examples/v2/bounded-pilot-blinded-codebook.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-blinded-codebook.schema.json"


def test_codebook_is_valid_and_vocabulary_pinned() -> None:
    result = validate_json_schema(CODEBOOK, SCHEMA)
    assert not result.errors, result.errors
    codebook = json.loads(CODEBOOK.read_text())
    vocabulary = ROOT / codebook["vocabulary"]["path"]
    assert codebook["vocabulary"]["sha256"] == sha256(vocabulary.read_bytes()).hexdigest()


def test_codebook_is_blinded_and_non_executable() -> None:
    codebook = json.loads(CODEBOOK.read_text())
    assert codebook["candidate_mapping_visible"] is False
    assert codebook["candidate_confidence_visible"] is False
    assert codebook["prior_review_outcomes_visible"] is False
    assert codebook["execution_allowed"] is False
    assert "mappings/alaveteli-state-map.yaml" in codebook["excluded_inputs"]
