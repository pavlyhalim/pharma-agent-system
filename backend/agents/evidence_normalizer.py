"""
Evidence Normalizer Agent - Standardizes heterogeneous clinical data.
"""

import asyncio
from typing import Dict, Any, List, Optional
from models.schemas import AgentState
from utils.stats import (
    wilson_score_interval,
    pooled_proportion,
    random_effects_meta_analysis,
    assess_data_quality
)
import logging
import numpy as np

logger = logging.getLogger(__name__)


class EvidenceNormalizerAgent:
    """
    Agent responsible for normalizing evidence and computing pooled metrics.

    Tasks:
    - Convert heterogeneous endpoints (ORR, PFS, DFS) to response rates
    - Pool data across studies with meta-analysis
    - Compute confidence intervals
    - Stratify by subgroups (genetic status, ancestry)

    Note: This agent uses pure statistical methods, no LLM required.
    """

    def __init__(self):
        """Initialize normalizer."""
        pass  # No AI model needed for statistical analysis

    async def run(self, state: AgentState) -> AgentState:
        """
        Execute evidence normalization.

        Args:
            state: Current agent state with literature data

        Returns:
            Updated state with normalized metrics
        """
        logger.info(f"Evidence Normalizer: Processing {len(state.pubmed_studies)} studies")

        state.current_agent = "evidence_normalizer"

        try:
            # Normalize individual studies
            normalized = await self._normalize_studies(
                state.pubmed_studies + state.clinical_trials,
                state.drug
            )

            state.normalized_data = normalized

            # Compute pooled metrics
            overall_metrics = self._compute_pooled_metrics(normalized)
            subgroup_metrics = self._compute_subgroup_metrics(normalized)

            state.pooled_metrics = {
                "overall": overall_metrics,
                "by_subgroup": subgroup_metrics
            }

            logger.info(
                f"Evidence Normalizer: Pooled data from {len(normalized)} studies, "
                f"found {len(subgroup_metrics)} subgroups"
            )

        except Exception as e:
            logger.error(f"Evidence normalization failed: {e}")
            state.errors.append(f"Normalization error: {str(e)}")

        return state

    async def _normalize_studies(
        self,
        studies: List[Dict[str, Any]],
        drug: str
    ) -> List[Dict[str, Any]]:
        """
        Normalize studies to standard format.

        Args:
            studies: Raw study data
            drug: Drug name

        Returns:
            Normalized study data
        """
        normalized = []

        for study in studies:
            # Skip if missing critical data
            if not study.get("sample_size") or study.get("sample_size") == 0:
                continue

            # Calculate non-response rate
            if study.get("non_response_rate") is not None:
                non_response = study["non_response_rate"]
            elif study.get("response_rate") is not None:
                non_response = 1 - study["response_rate"]
            else:
                continue  # Can't determine response

            sample_size = study["sample_size"]

            # Calculate confidence interval
            non_responders = int(non_response * sample_size)
            ci_lower, ci_upper = wilson_score_interval(non_responders, sample_size)

            # Assess quality
            quality, concerns = assess_data_quality(
                sample_size=sample_size,
                study_design=study.get("publication_types", [""])[0] if "publication_types" in study else "unknown",
                has_randomization=True,  # Assume from RCT filter
                has_blinding=True,
                has_intent_to_treat=True
            )

            # Add data provenance for transparency
            study_source = study.get("pmid") or study.get("nct_id") or "Unknown"
            study_url = None
            if study.get("pmid"):
                study_url = f"https://pubmed.ncbi.nlm.nih.gov/{study['pmid']}"
            elif study.get("nct_id"):
                study_url = f"https://clinicaltrials.gov/study/{study['nct_id']}"

            normalized_study = {
                "study_id": study_source,
                "study_url": study_url,
                "title": study.get("title", ""),
                "sample_size": sample_size,
                "non_response_rate": non_response,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "endpoint": study.get("endpoint", "unknown"),
                "subgroups": study.get("subgroups", []),
                "quality": quality,
                "concerns": concerns,
                "citation": study.get("citation", ""),
                # Add abstract snippet for verification
                "abstract_snippet": study.get("abstract", "")[:200] if study.get("abstract") else ""
            }

            normalized.append(normalized_study)

        logger.info(f"Normalized {len(normalized)}/{len(studies)} studies")
        return normalized

    def _compute_pooled_metrics(self, studies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute pooled non-response rate across all studies.

        Args:
            studies: Normalized studies

        Returns:
            Pooled metrics with CI
        """
        if not studies:
            return {
                "rate": None,
                "ci": {"lower": None, "upper": None},
                "n": 0
            }

        proportions = [s["non_response_rate"] for s in studies]
        sample_sizes = [s["sample_size"] for s in studies]

        # Compute pooled proportion
        pooled_rate, (ci_lower, ci_upper) = pooled_proportion(
            proportions,
            sample_sizes,
            method="inverse_variance"
        )

        total_n = sum(sample_sizes)

        return {
            "rate": float(pooled_rate),
            "ci": {
                "lower": float(ci_lower),
                "upper": float(ci_upper)
            },
            "n": int(total_n),
            "n_studies": len(studies),
            "contributing_studies": [
                {
                    "id": s["study_id"],
                    "url": s.get("study_url"),
                    "title": s["title"][:100],
                    "n": s["sample_size"],
                    "rate": s["non_response_rate"]
                }
                for s in studies
            ]
        }

    def _compute_subgroup_metrics(
        self,
        studies: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute metrics stratified by subgroups (e.g., genotype).

        Args:
            studies: Normalized studies

        Returns:
            Subgroup-specific metrics
        """
        # Collect all subgroups
        subgroup_data = {}

        for study in studies:
            for subgroup in study.get("subgroups", []):
                name = subgroup.get("name")
                if not name:
                    continue

                if name not in subgroup_data:
                    subgroup_data[name] = {
                        "proportions": [],
                        "sample_sizes": []
                    }

                # Calculate non-response rate for subgroup
                response_rate = subgroup.get("response_rate")
                if response_rate is not None:
                    non_response = 1 - response_rate
                    sample_size = subgroup.get("sample_size", 0)

                    if sample_size > 0:
                        subgroup_data[name]["proportions"].append(non_response)
                        subgroup_data[name]["sample_sizes"].append(sample_size)

        # Compute pooled metrics for each subgroup
        subgroup_metrics = {}

        for name, data in subgroup_data.items():
            if not data["proportions"]:
                continue

            pooled_rate, (ci_lower, ci_upper) = pooled_proportion(
                data["proportions"],
                data["sample_sizes"],
                method="inverse_variance"
            )

            subgroup_metrics[name] = {
                "rate": float(pooled_rate),
                "ci": {
                    "lower": float(ci_lower),
                    "upper": float(ci_upper)
                },
                "n": int(sum(data["sample_sizes"])),
                "n_studies": len(data["sample_sizes"])
            }

        return subgroup_metrics

    async def close(self):
        """Clean up resources."""
        pass  # No resources to clean up
