"""Reference Pydantic models for the additive FOI-O V2 empirical overlay.

These models intentionally reference existing FOI-O record IDs rather than
implementing a second event, ledger, trace, lineage, annotation, or gold-set
system.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, ClassVar, Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, field_validator, model_validator

NonEmpty = Annotated[str, Field(min_length=1)]
Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class StrictModel(BaseModel):
    """Reject undeclared fields across all empirical contracts."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class CodebookMaturity(StrEnum):
    """Describe the governed maturity of a codebook entry."""

    SEED = "seed"
    PILOT = "pilot"
    ADJUDICATED = "adjudicated"
    VALIDATED = "validated"
    STABLE = "stable"
    DEPRECATED = "deprecated"


class EpistemicStatus(StrEnum):
    """Describe how strongly an assertion is established."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    ASSERTED = "asserted"
    CERTIFIED = "certified"
    UNKNOWN = "unknown"


class ReviewStatus(StrEnum):
    """Describe the human-review state of a record."""

    UNREVIEWED = "unreviewed"
    SINGLE_REVIEWED = "single_reviewed"
    DUAL_REVIEWED = "dual_reviewed"
    ADJUDICATED = "adjudicated"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExtractionMethod(StrEnum):
    """Identify how a candidate assertion was produced."""

    IMPORTED_METADATA = "imported_metadata"
    DETERMINISTIC_RULE = "deterministic_rule"
    STATISTICAL_MODEL = "statistical_model"
    LANGUAGE_MODEL = "language_model"
    HUMAN_ANNOTATION = "human_annotation"
    OFFICIAL_SOURCE_IMPORT = "official_source_import"


class ExtractionContractArtifact(StrictModel):
    """Pin one repository artifact used by an extraction contract."""

    artifact_id: NonEmpty
    kind: Literal["ontology", "schema", "codebook", "vocabulary", "migration"]
    path: Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._/-]+$")]
    version: NonEmpty
    identifier: NonEmpty
    sha256: Sha256

    @field_validator("path")
    @classmethod
    def reject_mutable_paths(cls, value: str) -> str:
        """Reject branch-like or traversal references instead of guessing a revision."""
        parts = value.split("/")
        if ".." in parts or any(part in {"main", "latest"} for part in parts):
            raise ValueError("artifact path must be immutable and repository-relative")
        return value


class ExtractionContractReference(StrictModel):
    """Reference a versioned artifact pinned in the same contract."""

    id: NonEmpty
    version: NonEmpty
    artifact_id: NonEmpty


class OntologyContractReference(StrictModel):
    """Pin the ontology plus the schema used by future release manifests."""

    manifest_schema_id: Literal["urn:foi-o:schema:ontology-release-manifest:0.1.0"]
    manifest_schema_artifact_id: NonEmpty
    ontology_id: Literal["https://w3id.org/foio-nz/ontology"]
    ontology_version: Literal["0.1.0"]
    artifact_id: NonEmpty


class CandidateStatusVocabulary(ExtractionContractReference):
    """Declare the only statuses permitted for unpromoted extraction output."""

    allowed_statuses: list[Literal["observed", "inferred", "asserted", "unknown"]] = Field(
        min_length=4, max_length=4
    )
    certified_status_allowed: Literal[False]

    @field_validator("allowed_statuses")
    @classmethod
    def require_candidate_statuses(cls, value: list[str]) -> list[str]:
        """Keep the candidate vocabulary complete, ordered, and certification-free."""
        expected = ["observed", "inferred", "asserted", "unknown"]
        if value != expected:
            raise ValueError("candidate statuses must be observed, inferred, asserted, unknown")
        return value


class ExtractionMigration(StrictModel):
    """Describe an explicit migration into the extraction contract."""

    migration_id: NonEmpty
    from_version: NonEmpty
    to_contract_version: Literal["0.1.0"]
    artifact_id: NonEmpty
    automatic_scope: Literal["linkage_only"]
    human_promotion_required: Literal[True]


class ExtractionVersionRange(StrictModel):
    """Declare one bounded compatible semver interval."""

    minimum_inclusive: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]
    maximum_exclusive: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]

    @model_validator(mode="after")
    def validate_bounds(self) -> ExtractionVersionRange:
        """Reject empty or reversed compatibility intervals."""
        minimum = tuple(int(part) for part in self.minimum_inclusive.split("."))
        maximum = tuple(int(part) for part in self.maximum_exclusive.split("."))
        if minimum >= maximum:
            raise ValueError("compatibility range must have an increasing upper bound")
        return self


class ExtractionCompatibility(StrictModel):
    """Define fail-closed version compatibility for extraction consumers."""

    exact_versions: list[Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]] = Field(
        min_length=1
    )
    version_ranges: list[ExtractionVersionRange] = Field(min_length=1)
    unknown_major_behavior: Literal["reject"]
    unknown_revision_behavior: Literal["reject"]


class ExtractionContract(StrictModel):
    """Versioned, candidate-only extraction contract for downstream consumers."""

    schema_version: Literal["foi-o.extraction-contract.v0.1.0"]
    contract_id: Literal["foi-o.extraction-contract"]
    contract_version: Literal["0.1.0"]
    producer_id: Literal["foi-o-nz"]
    consumer_id: Literal["nlp-policy-nz"]
    ontology_release: OntologyContractReference
    schema_ids: list[NonEmpty] = Field(min_length=1)
    codebook: ExtractionContractReference
    provenance_identifiers: list[NonEmpty] = Field(min_length=1)
    candidate_status_vocabulary: CandidateStatusVocabulary
    compatibility: ExtractionCompatibility
    capability_ids: list[NonEmpty] = Field(min_length=1)
    migration_catalogue: list[ExtractionMigration] = Field(min_length=1)
    artifacts: list[ExtractionContractArtifact] = Field(min_length=1)
    human_promotion_required: Literal[True]

    @model_validator(mode="after")
    def validate_references(self) -> ExtractionContract:
        """Require unique pins and resolve every internal artifact reference."""
        artifact_ids = [artifact.artifact_id for artifact in self.artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("artifact IDs must be unique")
        artifacts = {artifact.artifact_id: artifact for artifact in self.artifacts}
        known = set(artifacts)
        references = {
            self.ontology_release.artifact_id,
            self.ontology_release.manifest_schema_artifact_id,
            self.codebook.artifact_id,
            self.candidate_status_vocabulary.artifact_id,
            *(migration.artifact_id for migration in self.migration_catalogue),
        }
        if not references.issubset(known):
            raise ValueError("every contract reference must resolve to a pinned artifact")
        ontology = artifacts[self.ontology_release.artifact_id]
        if (
            ontology.kind != "ontology"
            or ontology.identifier != self.ontology_release.ontology_id
            or ontology.version != self.ontology_release.ontology_version
        ):
            raise ValueError("ontology reference must match its pinned artifact")
        manifest_schema = artifacts[self.ontology_release.manifest_schema_artifact_id]
        if (
            manifest_schema.kind != "schema"
            or manifest_schema.identifier != self.ontology_release.manifest_schema_id
        ):
            raise ValueError("ontology manifest schema must match its pinned artifact")
        schema_identifiers = {
            artifact.identifier for artifact in self.artifacts if artifact.kind == "schema"
        }
        if not set(self.schema_ids).issubset(schema_identifiers):
            raise ValueError("every schema ID must resolve to a pinned schema artifact")
        codebook = artifacts[self.codebook.artifact_id]
        if (
            codebook.kind != "codebook"
            or codebook.identifier != self.codebook.id
            or codebook.version != self.codebook.version
        ):
            raise ValueError("codebook reference must match its pinned artifact")
        vocabulary = artifacts[self.candidate_status_vocabulary.artifact_id]
        if (
            vocabulary.kind != "vocabulary"
            or vocabulary.identifier != self.candidate_status_vocabulary.id
            or vocabulary.version != self.candidate_status_vocabulary.version
        ):
            raise ValueError("candidate vocabulary must match its pinned artifact")
        if any(
            artifacts[migration.artifact_id].kind != "migration"
            for migration in self.migration_catalogue
        ):
            raise ValueError("migration references must resolve to migration artifacts")
        return self


class ChangeControl(StrictModel):
    """Record approval requirements and completed approvals."""

    proposal_id: NonEmpty
    approval_required: bool
    approved_by: list[NonEmpty] = Field(default_factory=list)
    approved_at: datetime | None = None


class CodebookEntry(StrictModel):
    """Define a versioned empirical code with maturity controls."""

    code_id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._/-]+$")]
    label: NonEmpty
    jurisdiction_scope: list[NonEmpty] = Field(min_length=1)
    definition: Annotated[str, Field(min_length=20)]
    maturity: CodebookMaturity
    review_status: ReviewStatus
    origins: list[NonEmpty] = Field(min_length=1)
    inclusion_criteria: list[NonEmpty] = Field(default_factory=list)
    exclusion_criteria: list[NonEmpty] = Field(default_factory=list)
    positive_example_ids: list[NonEmpty] = Field(default_factory=list)
    negative_example_ids: list[NonEmpty] = Field(default_factory=list)
    empirical_support_count: int = Field(default=0, ge=0)
    normative_source_ids: list[NonEmpty] = Field(default_factory=list)
    known_ambiguities: list[NonEmpty] = Field(default_factory=list)
    version_introduced: NonEmpty
    deprecated_by: NonEmpty | None = None
    change_control: ChangeControl

    @model_validator(mode="after")
    def validate_maturity(self) -> CodebookEntry:
        """Enforce approval and evidence requirements for mature codes."""
        if self.maturity == CodebookMaturity.STABLE:
            if self.review_status != ReviewStatus.APPROVED:
                raise ValueError("stable code requires approved review status")
            if self.empirical_support_count < 1:
                raise ValueError("stable code requires empirical support")
            if not self.change_control.approved_by or self.change_control.approved_at is None:
                raise ValueError("stable code requires recorded approval")
        if self.maturity == CodebookMaturity.DEPRECATED and not self.deprecated_by:
            raise ValueError("deprecated code requires deprecated_by")
        return self


class SubjectRef(StrictModel):
    """Reference an existing FOI-O subject without duplicating it."""

    kind: Literal[
        "request",
        "message",
        "attachment",
        "event",
        "decision",
        "review",
        "authority",
        "source_span",
    ]
    id: NonEmpty


class CertificationAuthority(StrictModel):
    """Identify the human or official source behind certification."""

    authority_type: Literal["human", "official_source"]
    authority_id: NonEmpty
    role_or_source: NonEmpty
    certified_at: datetime | None = None


class LabelAssertion(StrictModel):
    """Attach a governed candidate or certified label to a subject."""

    assertion_id: NonEmpty
    subject: SubjectRef
    code_id: NonEmpty
    codebook_version: NonEmpty
    epistemic_status: EpistemicStatus
    review_status: ReviewStatus
    extraction_method: ExtractionMethod
    confidence: float | None = Field(default=None, ge=0, le=1)
    requires_human_review: bool
    evidence_assertion_ids: list[NonEmpty] = Field(default_factory=list)
    certification_authority: CertificationAuthority | None = None
    created_at: datetime
    notes: str | None = None

    @model_validator(mode="after")
    def guard_certification(self) -> LabelAssertion:
        """Prevent automated methods from certifying assertions."""
        model_methods = {ExtractionMethod.STATISTICAL_MODEL, ExtractionMethod.LANGUAGE_MODEL}
        if self.extraction_method in model_methods:
            if not self.requires_human_review:
                raise ValueError("model outputs require human review")
            if self.epistemic_status == EpistemicStatus.CERTIFIED:
                raise ValueError("model output cannot certify an assertion")
        if self.epistemic_status == EpistemicStatus.CERTIFIED:
            if self.certification_authority is None:
                raise ValueError("certified assertion requires certification authority")
            if self.review_status not in {ReviewStatus.ADJUDICATED, ReviewStatus.APPROVED}:
                raise ValueError("certified assertion must be adjudicated or approved")
            if self.requires_human_review:
                raise ValueError("certified assertion cannot remain pending human review")
            if not self.evidence_assertion_ids:
                raise ValueError("certified assertion requires evidence")
        return self


class EvidenceDimensions(StrictModel):
    """Describe evidence across authority, integrity, time, and access axes."""

    authority: Literal[
        "binding_law",
        "authoritative_interpretation",
        "official_administration",
        "platform_record",
        "participant_account",
        "model_output",
    ]
    directness: Literal["direct", "corroborative", "contextual", "inferred"]
    integrity: Literal["hash_verified", "archived_unverified", "live_unverified", "derived"]
    temporal_applicability: Literal[
        "event_time_match", "retrospective_context", "prospective_context", "unknown"
    ]
    visibility: Literal["public", "restricted", "internal_required", "unknown"]


class EvidenceSourceRef(StrictModel):
    """Reference an existing evidence-bearing repository record."""

    kind: Literal[
        "ledger_entry",
        "trace_span",
        "lineage_node",
        "legal_source",
        "attachment",
        "message",
        "platform_record",
        "human_annotation",
        "model_output",
    ]
    id: NonEmpty
    content_sha256: Sha256 | None = None
    source_uri: AnyUrl | None = None


class CreatedBy(StrictModel):
    """Identify who or what created an evidence assertion."""

    kind: Literal["human", "software", "official_import"]
    id: NonEmpty
    version: str | None = None


class EvidenceAssertion(StrictModel):
    """Relate evidence to supported and contradicted claims."""

    evidence_assertion_id: NonEmpty
    supports: list[NonEmpty] = Field(min_length=1)
    contradicts: list[NonEmpty] = Field(default_factory=list)
    source_ref: EvidenceSourceRef
    dimensions: EvidenceDimensions
    display_grade: Literal["A", "B", "C", "D", "E"] | None = None
    observed_at: datetime
    created_by: CreatedBy
    limitations: list[NonEmpty] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_source_authority(self) -> EvidenceAssertion:
        """Keep source kinds aligned with their authority dimension."""
        expected = {"model_output": "model_output", "platform_record": "platform_record"}
        wanted = expected.get(self.source_ref.kind)
        if wanted and self.dimensions.authority != wanted:
            raise ValueError(f"{self.source_ref.kind} source must use {wanted} authority")
        return self


class EffectiveTime(StrictModel):
    """Represent the interval in which a source was legally effective."""

    from_: date = Field(alias="from")
    to: date | None = None

    @model_validator(mode="after")
    def validate_interval(self) -> EffectiveTime:
        """Reject an effective interval whose end precedes its start."""
        if self.to is not None and self.to < self.from_:
            raise ValueError("effective to date precedes from date")
        return self


class ObservationTime(StrictModel):
    """Separate observation time from retrieval time."""

    observed_at: datetime
    retrieved_at: datetime


class SourceVersion(StrictModel):
    """Identify a language-specific official source version."""

    source_version_id: NonEmpty
    official_version_label: str | None = None
    language: str = "en"


class SourceIntegrity(StrictModel):
    """Record source content integrity and archival location."""

    sha256: Sha256
    archived_uri: AnyUrl | None = None


class SourceRights(StrictModel):
    """Record access and redistribution rights for a source."""

    access_basis: NonEmpty
    redistribution_status: Literal["permitted", "restricted", "metadata_only", "unknown"]
    license_or_terms: str | None = None
    rights_notes: str | None = None

    @model_validator(mode="after")
    def require_terms_for_permission(self) -> SourceRights:
        """Require supporting terms before claiming redistribution permission."""
        if self.redistribution_status == "permitted" and not self.license_or_terms:
            raise ValueError("permitted redistribution requires licence or terms")
        return self


class NormativeRelationship(StrictModel):
    """Relate one normative source version to another."""

    relation: Literal[
        "amends",
        "amended_by",
        "supersedes",
        "superseded_by",
        "commences",
        "interprets",
        "cites",
        "implements",
    ]
    target_source_id: NonEmpty


class NormativeSource(StrictModel):
    """Represent a bitemporal, rights-aware normative source."""

    source_id: NonEmpty
    jurisdiction: NonEmpty
    source_type: NonEmpty
    title: NonEmpty
    provider: NonEmpty
    source_uri: AnyUrl
    authority_level: Literal[
        "binding_law",
        "binding_decision",
        "authoritative_interpretation",
        "official_guidance",
        "administrative_material",
        "contextual_material",
    ]
    effective_time: EffectiveTime
    observation_time: ObservationTime
    version: SourceVersion
    integrity: SourceIntegrity
    rights: SourceRights
    relationships: list[NormativeRelationship] = Field(default_factory=list)
    provision_index_ref: str | None = None
    review_status: Literal["needs_review", "human_reviewed", "approved", "rejected"] = (
        "needs_review"
    )


class JurisdictionProfileProvenance(StrictModel):
    """Pin the source manifest and generator used to build a profile."""

    source_manifest_id: NonEmpty
    source_manifest_sha256: Sha256
    generated_at: datetime
    generated_by: NonEmpty
    certified_by: NonEmpty | None = None
    certified_at: datetime | None = None

    @model_validator(mode="after")
    def validate_certification(self) -> JurisdictionProfileProvenance:
        """Keep certification metadata complete when supplied."""
        if (self.certified_by is None) != (self.certified_at is None):
            raise ValueError("profile certification requires certifier and timestamp")
        return self


class JurisdictionProfile(StrictModel):
    """Describe an additive jurisdiction profile without changing FOI-O core semantics."""

    profile_id: Annotated[str, Field(pattern=r"^foi-o-[a-z0-9-]+-v[0-9]+\.[0-9]+\.[0-9]+$")]
    jurisdiction: NonEmpty
    name: NonEmpty
    status: Literal["candidate", "validated", "stable", "deprecated"]
    core_compatibility: NonEmpty
    supported_surfaces: list[NonEmpty] = Field(min_length=1)
    unsupported_surfaces: list[NonEmpty] = Field(min_length=1)
    uncertain_surfaces: list[NonEmpty] = Field(min_length=1)
    human_certified_surfaces: list[NonEmpty] = Field(default_factory=list)
    sources: list[NormativeSource] = Field(min_length=1)
    provenance: JurisdictionProfileProvenance

    @model_validator(mode="after")
    def validate_profile(self) -> JurisdictionProfile:
        """Prevent cross-jurisdiction leakage and unsupported validation claims."""
        if any(source.jurisdiction != self.jurisdiction for source in self.sources):
            raise ValueError("profile sources must match the profile jurisdiction")
        declared = (
            set(self.supported_surfaces)
            | set(self.unsupported_surfaces)
            | set(self.uncertain_surfaces)
        )
        if len(declared) != len(
            self.supported_surfaces + self.unsupported_surfaces + self.uncertain_surfaces
        ):
            raise ValueError("profile surfaces must be mutually exclusive")
        if not set(self.human_certified_surfaces).issubset(self.supported_surfaces):
            raise ValueError("human-certified surfaces must be supported surfaces")
        if self.status in {"validated", "stable"}:
            if not self.human_certified_surfaces:
                raise ValueError("validated profile requires human-certified surfaces")
            if self.provenance.certified_by is None or self.provenance.certified_at is None:
                raise ValueError("validated profile requires certification provenance")
            if any(source.review_status != "approved" for source in self.sources):
                raise ValueError(
                    "validated profile certification requires approved normative sources"
                )
        return self


class SamplingDesign(StrictModel):
    """Describe an estimand-aware empirical sampling design."""

    design_type: Literal[
        "probability_stratified", "rare_event_enrichment", "census", "purposive_qualitative"
    ]
    strata_variables: list[NonEmpty] = Field(default_factory=list)
    population_estimation_allowed: bool
    weights_available: bool
    inclusion_probability_field: str | None = None
    weight_field: str | None = None
    finite_population_correction: bool | None = None
    replacement_rule: str | None = None

    @model_validator(mode="after")
    def validate_design(self) -> SamplingDesign:
        """Enforce weighting requirements and enrichment limitations."""
        if self.design_type == "probability_stratified":
            if not self.population_estimation_allowed or not self.weights_available:
                raise ValueError("probability sample must support weighted estimation")
            if not self.inclusion_probability_field or not self.weight_field:
                raise ValueError("probability sample requires probability and weight fields")
        if self.design_type == "rare_event_enrichment" and self.population_estimation_allowed:
            raise ValueError("enrichment sample cannot estimate population prevalence directly")
        return self


class AuthorityActiveTime(StrictModel):
    """Represent the active interval for an authority identity."""

    from_: date = Field(alias="from")
    to: date | None = None

    @model_validator(mode="after")
    def validate_interval(self) -> AuthorityActiveTime:
        """Reject an authority interval whose end precedes its start."""
        if self.to is not None and self.to < self.from_:
            raise ValueError("authority active interval ends before it begins")
        return self


class AuthorityName(StrictModel):
    """Record a sourced authority name over a bounded interval."""

    name: NonEmpty
    valid_from: date
    valid_to: date | None = None
    name_type: (
        Literal["official", "former_official", "platform_display", "abbreviation", "alternate"]
        | None
    ) = None
    source_ids: list[NonEmpty] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_interval(self) -> AuthorityName:
        """Reject a name interval whose end precedes its start."""
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("authority name interval ends before it begins")
        return self


class PlatformIdentifier(StrictModel):
    """Record a platform identifier over a bounded interval."""

    platform: NonEmpty
    identifier: NonEmpty
    valid_from: date
    valid_to: date | None = None
    source_uri: AnyUrl | None = None

    @model_validator(mode="after")
    def validate_interval(self) -> PlatformIdentifier:
        """Reject an identifier interval whose end precedes its start."""
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("platform identifier interval ends before it begins")
        return self


class AuthorityRelationship(StrictModel):
    """Record a sourced temporal relationship between authorities."""

    relation: Literal[
        "predecessor_of",
        "successor_of",
        "merged_into",
        "split_from",
        "renamed_to",
        "administered_by",
    ]
    target_authority_identity_id: NonEmpty
    effective_from: date
    effective_to: date | None = None
    source_ids: list[NonEmpty] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_interval(self) -> AuthorityRelationship:
        """Reject a relationship interval whose end precedes its start."""
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("authority relationship interval ends before it begins")
        return self


class AuthorityIdentityRecord(StrictModel):
    """Resolve a time-versioned authority identity while preserving conflicts."""

    authority_identity_id: NonEmpty
    canonical_name: NonEmpty
    jurisdiction: NonEmpty
    authority_types: list[NonEmpty] = Field(default_factory=list)
    active_time: AuthorityActiveTime
    names: list[AuthorityName] = Field(min_length=1)
    platform_identifiers: list[PlatformIdentifier]
    relationships: list[AuthorityRelationship] = Field(default_factory=list)
    identity_source_ids: list[NonEmpty] = Field(min_length=1)
    observed_at: datetime
    record_sha256: Sha256 | None = None
    review_status: Literal["needs_review", "human_reviewed", "approved", "rejected"]
    identity_conflict: bool
    conflict_notes: list[NonEmpty] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_identity(self) -> AuthorityIdentityRecord:
        """Require conflict notes and hashes for approved identities."""
        if self.identity_conflict and not self.conflict_notes:
            raise ValueError("identity conflict requires conflict notes")
        if self.review_status == "approved" and self.record_sha256 is None:
            raise ValueError("approved authority identity requires a record hash")
        return self


class EventStreamRef(StrictModel):
    """Reference a hashed, versioned event stream and its provenance."""

    path_or_uri: NonEmpty
    sha256: Sha256
    schema_version: NonEmpty
    snapshot_id: NonEmpty
    lineage_graph_ref: str | None = None
    ledger_ref: str | None = None


class EventSelectionPolicy(StrictModel):
    """Record which events and epistemic states an analysis consumes."""

    allowed_epistemic_statuses: list[EpistemicStatus] = Field(min_length=1)
    requires_evidence_reference: bool
    unknown_handling: Literal["retain_as_state", "exclude_with_count", "sensitivity_analysis"]
    minimum_review_status: (
        Literal["unreviewed", "single_reviewed", "dual_reviewed", "adjudicated", "approved"] | None
    ) = None
    event_type_allowlist: list[NonEmpty] = Field(default_factory=list)


class UncertaintyPolicy(StrictModel):
    """Describe how analysis propagates uncertainty and abstentions."""

    strategy: Literal[
        "descriptive_stratification",
        "sensitivity_bounds",
        "probability_weighting",
        "multiple_imputation",
        "not_applicable",
    ]
    abstentions_reported: Literal[True]
    extraction_uncertainty_propagated: bool
    sensitivity_analysis_ref: str | None = None


class CensoringPolicy(StrictModel):
    """Describe censoring assumptions for temporal analyses."""

    status: Literal["not_applicable", "right_censored", "mixed"]
    censor_date_field: str | None = None
    competing_event_fields: list[NonEmpty] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_censoring(self) -> CensoringPolicy:
        """Require a censoring field whenever censoring is active."""
        if self.status in {"right_censored", "mixed"} and not self.censor_date_field:
            raise ValueError("censored analysis requires censor_date_field")
        return self


class AnalysisOutput(StrictModel):
    """Reference one hashed output of a reproducible analysis run."""

    kind: Literal[
        "summary",
        "transition_matrix",
        "variant_table",
        "duration_table",
        "survival_estimate",
        "object_centric_log",
        "case_centric_log",
        "evaluation_report",
        "derivability_report",
    ]
    path: NonEmpty
    sha256: Sha256


class SoftwareRef(StrictModel):
    """Identify versioned software used in an analysis run."""

    name: NonEmpty
    version: NonEmpty
    git_sha: Annotated[str, Field(pattern=r"^[a-f0-9]{7,40}$")] | None = None


class ProcessAnalysisRun(StrictModel):
    """Describe a reproducible process analysis with a non-legal boundary."""

    run_id: NonEmpty
    analysis_type: Literal[
        "descriptive", "process_mining", "survival", "extractor_evaluation", "comparative"
    ]
    generated_at: datetime
    event_stream_ref: EventStreamRef
    event_selection: EventSelectionPolicy
    uncertainty_policy: UncertaintyPolicy
    censoring_policy: CensoringPolicy
    outputs: list[AnalysisOutput] = Field(min_length=1)
    software: list[SoftwareRef] = Field(min_length=1)
    pre_registration_ref: str | None = None
    comparability_assessment_ref: str | None = None
    estimand_ids: list[NonEmpty] = Field(default_factory=list)
    legal_claims_permitted: Literal[False]
    result_scope: Literal["public_process_indicators_only"]
    review_status: Literal["draft", "human_reviewed", "approved", "rejected"]
    approved_by: list[NonEmpty] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_run(self) -> ProcessAnalysisRun:
        """Enforce comparison prerequisites and approval provenance."""
        if self.analysis_type == "comparative":
            if not self.comparability_assessment_ref or not self.estimand_ids:
                raise ValueError(
                    "comparative analysis requires a comparability assessment and estimand IDs"
                )
        if self.review_status == "approved" and not self.approved_by:
            raise ValueError("approved analysis run requires recorded approver")
        return self
