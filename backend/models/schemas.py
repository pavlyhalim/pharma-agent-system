"""
Pydantic models for request/response validation and agent state management.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Request Models
# ============================================================================

class DrugQuery(BaseModel):
    """User query for drug analysis."""
    drug: str = Field(..., description="Drug name (generic, brand, or mechanism)")
    indication: Optional[str] = Field(None, description="Disease/condition indication")
    population: Optional[str] = Field(
        "all",
        description="Target population (all, ancestry group, or genotype)"
    )
    article_count: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of PubMed articles to process (1-20, default: 5)"
    )
    clinical_trials_count: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of clinical trials to process (1-20, default: 5)"
    )


class AutocompleteRequest(BaseModel):
    """Drug name autocomplete request."""
    query: str = Field(..., min_length=2, description="Partial drug name")
    limit: int = Field(10, ge=1, le=50, description="Max results")


# ============================================================================
# Response Models
# ============================================================================

class ConfidenceInterval(BaseModel):
    """95% confidence interval."""
    lower: float = Field(..., ge=0, le=1)
    upper: float = Field(..., ge=0, le=1)


class NonResponseMetric(BaseModel):
    """Non-response rate with uncertainty."""
    rate: float = Field(..., ge=0, le=1, description="Non-response proportion")
    ci: ConfidenceInterval = Field(..., description="95% CI")
    n: int = Field(..., ge=0, description="Sample size")


class SubgroupMetrics(BaseModel):
    """Non-response metrics stratified by subgroup."""
    overall: NonResponseMetric
    by_subgroup: Dict[str, NonResponseMetric] = Field(
        default_factory=dict,
        description="Subgroup-specific metrics (e.g., by genotype)"
    )


class Variant(BaseModel):
    """Genetic variant associated with drug response."""
    rs_id: str = Field(..., description="dbSNP reference SNP ID")
    gene: str = Field(..., description="Gene symbol")
    allele: Optional[str] = Field(None, description="Star allele nomenclature")
    effect: str = Field(..., description="Functional consequence")
    frequency: Dict[str, float] = Field(
        default_factory=dict,
        description="Allele frequency by ancestry (EUR, EAS, AFR, etc.)"
    )
    citations: List[str] = Field(default_factory=list, description="PMIDs")


class Hypothesis(BaseModel):
    """Formulation or dosing hypothesis."""
    rank: int = Field(..., ge=1, description="Priority ranking")
    title: str = Field(..., description="Concise hypothesis statement")
    rationale: str = Field(..., description="Mechanistic explanation")
    evidence: List[str] = Field(..., description="Supporting citations")
    confidence: Literal["high", "moderate", "low"] = Field(..., description="Confidence level")


class AnalysisMetadata(BaseModel):
    """Analysis metadata and quality indicators."""
    studies_analyzed: int = Field(..., ge=0)
    total_patients: int = Field(..., ge=0)
    data_quality: Literal["high", "moderate", "low", "insufficient"]
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    warnings: List[str] = Field(default_factory=list)


class DrugAnalysisResult(BaseModel):
    """Complete analysis output."""
    drug: str
    indication: Optional[str]
    population: str
    non_response_rate: SubgroupMetrics
    variants: List[Variant]
    hypotheses: List[Hypothesis]
    metadata: AnalysisMetadata
    citations: List[str] = Field(default_factory=list)


class AutocompleteResult(BaseModel):
    """Drug autocomplete suggestion."""
    name: str
    type: Literal["generic", "brand", "mechanism"]
    description: Optional[str] = None


# ============================================================================
# Agent State (LangGraph)
# ============================================================================

class AgentState(BaseModel):
    """Shared state across all agents in the graph."""

    # User input
    drug: str
    indication: Optional[str] = None
    population: str = "all"

    # Literature Miner outputs
    pubmed_studies: List[Dict[str, Any]] = Field(default_factory=list)
    clinical_trials: List[Dict[str, Any]] = Field(default_factory=list)
    pharmgkb_annotations: List[Dict[str, Any]] = Field(default_factory=list)

    # Evidence Normalizer outputs
    normalized_data: List[Dict[str, Any]] = Field(default_factory=list)
    pooled_metrics: Dict[str, Any] = Field(default_factory=dict)

    # Genetics Analyst outputs
    variants: List[Dict[str, Any]] = Field(default_factory=list)
    mechanisms: List[Dict[str, Any]] = Field(default_factory=list)

    # Hypothesis Generator outputs
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)

    # DrugBank data - comprehensive drug information
    drugbank_data: Optional[Dict[str, Any]] = None

    # Metadata
    citations: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    current_agent: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Internal Data Models
# ============================================================================

class ClinicalStudy(BaseModel):
    """Standardized clinical study representation."""
    study_id: str
    title: str
    design: Literal["RCT", "observational", "meta-analysis", "case-series"]
    drug: str
    indication: str
    sample_size: int
    response_rate: Optional[float] = None
    non_response_rate: Optional[float] = None
    endpoint: str
    subgroups: List[Dict[str, Any]] = Field(default_factory=list)
    citation: str
    pmid: Optional[str] = None


class GeneticAssociation(BaseModel):
    """Gene-drug-phenotype association."""
    gene: str
    variants: List[str]
    drug: str
    phenotype: str
    effect_size: Optional[float] = None
    p_value: Optional[float] = None
    ancestry: Optional[str] = None
    source: str
    pmid: Optional[str] = None


class MechanismAnnotation(BaseModel):
    """Pharmacokinetic/pharmacodynamic mechanism."""
    gene: str
    mechanism_type: Literal["metabolism", "transport", "target", "other"]
    description: str
    drugs_affected: List[str]
    clinical_relevance: str
