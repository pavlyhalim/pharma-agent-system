"""
ClinicalTrials.gov API v2.0 service.
"""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)


class ClinicalTrialsService:
    """Service for querying ClinicalTrials.gov API v2.0."""

    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_trials(
        self,
        drug: str,
        indication: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for clinical trials involving a drug.

        Args:
            drug: Drug name
            indication: Disease/condition (optional)
            max_results: Maximum results

        Returns:
            List of trial data
        """
        # Build query
        query_parts = [drug]
        if indication:
            query_parts.append(indication)

        params = {
            "query.term": " AND ".join(query_parts),
            "filter.overallStatus": "COMPLETED",
            "pageSize": min(max_results, 1000),
            "format": "json",
            "fields": "NCTId,BriefTitle,Condition,InterventionName,Phase,EnrollmentCount,PrimaryOutcomeMeasure,PrimaryOutcomeDescription,ResultsFirstPostDate"
        }

        logger.info(f"ClinicalTrials.gov search: {params['query.term']}")

        try:
            response = await self._make_request(params)
            studies = response.get("studies", [])

            logger.info(f"Found {len(studies)} clinical trials")
            return self._parse_studies(studies)

        except Exception as e:
            logger.error(f"ClinicalTrials.gov search failed: {e}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to ClinicalTrials.gov API."""
        response = await self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json()

    def _parse_studies(self, studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse and normalize study data."""
        parsed = []

        for study in studies:
            try:
                protocol = study.get("protocolSection", {})
                identification = protocol.get("identificationModule", {})
                design = protocol.get("designModule", {})
                arms = protocol.get("armsInterventionsModule", {})
                outcomes = protocol.get("outcomesModule", {})

                nct_id = identification.get("nctId")
                parsed.append({
                    "nct_id": nct_id,
                    "title": identification.get("briefTitle", ""),
                    "conditions": identification.get("conditions", []),
                    "interventions": [
                        i.get("name") for i in arms.get("interventions", [])
                    ],
                    "phase": design.get("phases", ["N/A"])[0],
                    "enrollment": design.get("enrollmentInfo", {}).get("count"),
                    "primary_outcome": outcomes.get("primaryOutcomes", [{}])[0].get("measure", ""),
                    "has_results": bool(study.get("hasResults")),
                    "url": f"https://www.clinicaltrials.gov/study/{nct_id}" if nct_id else None,
                    "citation": nct_id  # Keep for backward compatibility
                })

            except Exception as e:
                logger.warning(f"Failed to parse trial: {e}")
                continue

        return parsed

    async def fetch_trial_results(self, nct_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed results for a specific trial.

        Args:
            nct_id: NCT identifier

        Returns:
            Trial results data
        """
        params = {
            "query.term": nct_id,
            "format": "json",
            "fields": "NCTId,ResultsSection"
        }

        try:
            response = await self._make_request(params)
            studies = response.get("studies", [])

            if not studies:
                return None

            results_section = studies[0].get("resultsSection", {})
            return self._parse_results(results_section)

        except Exception as e:
            logger.error(f"Failed to fetch results for {nct_id}: {e}")
            return None

    def _parse_results(self, results_section: Dict[str, Any]) -> Dict[str, Any]:
        """Parse trial results section."""
        outcome_measures = results_section.get("outcomeMeasuresModule", {}).get("outcomeMeasures", [])

        parsed_outcomes = []
        for outcome in outcome_measures:
            parsed_outcomes.append({
                "title": outcome.get("title", ""),
                "description": outcome.get("description", ""),
                "groups": outcome.get("groups", []),
                "results": outcome.get("classes", [])
            })

        return {
            "participant_flow": results_section.get("participantFlowModule"),
            "baseline_characteristics": results_section.get("baselineCharacteristicsModule"),
            "outcome_measures": parsed_outcomes,
            "adverse_events": results_section.get("adverseEventsModule")
        }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
