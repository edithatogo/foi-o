from __future__ import annotations

import json
from pathlib import Path

from rdflib import RDF, Graph, Namespace
from rdflib.namespace import OWL, SH, SKOS

from foi_o_nz.jsonld_context import FOIO_CONTEXT
from foi_o_nz.rdf_export import FOIO

FOIO_NAMESPACE = "https://w3id.org/foio-nz/ontology#"
FOIO_NS = Namespace(FOIO_NAMESPACE)


def _graph(path: Path) -> Graph:
    graph = Graph()
    graph.parse(path, format="turtle")
    return graph


def test_semantic_namespace_bindings_are_consistent() -> None:
    context = json.loads(Path("contexts/foi-o-nz.context.jsonld").read_text(encoding="utf-8"))[
        "@context"
    ]

    assert str(FOIO) == FOIO_NAMESPACE
    assert FOIO_CONTEXT["foio"] == FOIO_NAMESPACE
    assert context["foio"] == FOIO_NAMESPACE


def test_ontology_exposes_required_maturation_terms() -> None:
    graph = _graph(Path("ontology/foi-o-nz.ttl"))

    for class_name in [
        "ReviewTask",
        "RiskAssessment",
        "RedactionCandidate",
        "Chunk",
        "DatasetPublication",
        "DisclosureLog",
        "ProviderRun",
        "LegalSourceVersion",
        "PermissionPolicy",
    ]:
        assert (FOIO_NS[class_name], RDF.type, OWL.Class) in graph

    for property_name in [
        "sourceSystem",
        "sourceUrl",
        "contentSha256",
        "humanReviewRequired",
        "legalEffect",
        "machineCertificationAllowed",
        "generatedOutputIncluded",
        "hasDistribution",
        "hasPolicy",
        "sourceVersionId",
    ]:
        assert (FOIO_NS[property_name], RDF.type, None) in graph


def test_skos_vocabularies_parse_and_cover_current_event_types() -> None:
    required_event_types = {
        "RequestObserved",
        "MessageObserved",
        "ExtensionNotified",
        "TransferNotified",
        "ClarificationRequested",
        "ChargeNoticeSent",
        "DecisionCommunicated",
        "ReleaseMade",
        "RefusalCommunicated",
        "ComplaintObserved",
    }
    event_graph = _graph(Path("vocab/event-types.skos.ttl"))
    present_event_types = {
        str(subject).rsplit("/", maxsplit=1)[-1]
        for subject in event_graph.subjects(RDF.type, SKOS.Concept)
    }

    assert required_event_types <= present_event_types

    for vocab_path in sorted(Path("vocab").glob("*.skos.ttl")):
        graph = _graph(vocab_path)
        schemes = set(graph.subjects(RDF.type, SKOS.ConceptScheme))
        concepts = set(graph.subjects(RDF.type, SKOS.Concept))
        assert schemes, vocab_path
        assert concepts, vocab_path
        for concept in concepts:
            assert any(graph.objects(concept, SKOS.prefLabel)), concept


def test_jsonld_context_covers_current_safety_and_publication_terms() -> None:
    context = json.loads(Path("contexts/foi-o-nz.context.jsonld").read_text(encoding="utf-8"))[
        "@context"
    ]

    for term in [
        "source_url",
        "content_sha256",
        "human_review_required",
        "legal_effect",
        "machine_certification_allowed",
        "generated_output_included",
        "legal_references",
        "dataset_resources",
        "publication_caveats",
        "source_version_id",
    ]:
        assert term in context


def test_shacl_shapes_include_agent_publication_and_review_profiles() -> None:
    graph = _graph(Path("shacl/foi-o-nz.shapes.ttl"))

    for shape_name in [
        "ProcessEventShape",
        "DecisionLikeEventShape",
        "AgentActionShape",
        "ReviewTaskShape",
        "DatasetPublicationShape",
    ]:
        assert (FOIO_NS[shape_name], RDF.type, SH.NodeShape) in graph
