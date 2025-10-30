"""
Literature Miner Agent - GEMINI ONLY VERSION

Retrieves clinical evidence from multiple sources and extracts structured data
using Google Gemini 2.5 Flash with structured output.
"""

import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from models.schemas import AgentState
from services.pubmed_service import PubMedService
from services.clinical_trials_service import ClinicalTrialsService
from services.pharmgkb_service import PharmGKBService
from services.gemini_service import GeminiService
import logging

logger = logging.getLogger(__name__)


# Pydantic models for structured extraction
class SubgroupData(BaseModel):
    """Subgroup response data."""
    name: str
    sample_size: int
    response_rate: float = Field(ge=0, le=1)


class ExtractedClinicalData(BaseModel):
    """Structured clinical data extracted from abstracts."""
    sample_size: int | None = None
    response_rate: float | None = Field(None, ge=0, le=1)
    non_response_rate: float | None = Field(None, ge=0, le=1)
    endpoint: str | None = None
    subgroups: List[SubgroupData] = Field(default_factory=list)
    has_genetic_data: bool = False
    genetic_markers: List[str] = Field(default_factory=list)


class LiteratureMinerAgent:
    """
    Agent responsible for mining clinical literature and trial data.

    Uses ONLY Google Gemini 2.5 Flash for:
    - Real-time literature search with grounding
    - Structured data extraction from abstracts
    - Context gathering for recent research
    """

    def __init__(self, google_api_key: str):
        """Initialize with API services."""
        self.gemini = GeminiService(api_key=google_api_key)
        self.pubmed = PubMedService()
        self.clinical_trials = ClinicalTrialsService()
        self.pharmgkb = PharmGKBService()

    async def run(self, state: AgentState, progress_callback=None, article_count: int = 5, clinical_trials_count: int = 5) -> AgentState:
        """
        Execute literature mining.

        Args:
            state: Current agent state
            progress_callback: Optional callback for progress updates
            article_count: Number of PubMed articles to process (1-20, default: 5)
            clinical_trials_count: Number of clinical trials to process (1-20, default: 5)

        Returns:
            Updated state with literature data
        """
        logger.info(f"Literature Miner (Gemini-only): Mining data for {state.drug}")

        state.current_agent = "literature_miner"

        # Run all searches in parallel
        try:
            pubmed_task = self._mine_pubmed(state.drug, state.indication, progress_callback, article_count)
            trials_task = self._mine_clinical_trials(state.drug, state.indication, progress_callback, clinical_trials_count)
            pharmgkb_task = self._mine_pharmgkb(state.drug)
            gemini_context_task = self._get_gemini_context(state.drug, state.indication)

            pubmed_results, trials_results, pharmgkb_results, gemini_context = await asyncio.gather(
                pubmed_task,
                trials_task,
                pharmgkb_task,
                gemini_context_task,
                return_exceptions=True
            )

            # Handle results
            if isinstance(pubmed_results, Exception):
                logger.error(f"PubMed search failed: {pubmed_results}")
                state.errors.append(f"PubMed error: {str(pubmed_results)}")
                pubmed_results = []

            if isinstance(trials_results, Exception):
                logger.error(f"ClinicalTrials search failed: {trials_results}")
                state.errors.append(f"ClinicalTrials error: {str(trials_results)}")
                trials_results = []

            if isinstance(pharmgkb_results, Exception):
                logger.error(f"PharmGKB search failed: {pharmgkb_results}")
                state.errors.append(f"PharmGKB error: {str(pharmgkb_results)}")
                pharmgkb_results = []

            if isinstance(gemini_context, Exception):
                logger.warning(f"Gemini context search failed: {gemini_context}")
                gemini_context = None

            # Validate that we have at least SOME real data
            if not pubmed_results and not trials_results:
                error_msg = (
                    f"NO DATA SOURCES AVAILABLE - All literature searches failed for {state.drug}. "
                    f"PubMed: {'failed' if isinstance(pubmed_results, list) and len(pubmed_results) == 0 else 'error'}, "
                    f"ClinicalTrials: {'failed' if isinstance(trials_results, list) and len(trials_results) == 0 else 'error'}. "
                    f"Cannot proceed without real clinical data."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            state.pubmed_studies = pubmed_results
            state.clinical_trials = trials_results
            state.pharmgkb_annotations = pharmgkb_results

            # Extract citations
            state.citations.extend([f"PMID:{s['pmid']}" for s in pubmed_results if s.get('pmid')])
            # Use full URL for clinical trials instead of just NCT ID
            state.citations.extend([t['url'] for t in trials_results if t.get('url')])

            # Add Gemini grounding citations
            if gemini_context:
                for cite in gemini_context.get("citations", []):
                    state.citations.append(cite.get("url", ""))

            logger.info(
                f"Literature Miner: Found {len(pubmed_results)} PubMed articles, "
                f"{len(trials_results)} trials, {len(pharmgkb_results)} PharmGKB annotations"
            )

        except RuntimeError as e:
            # Re-raise validation errors (no data available)
            logger.error(f"Literature mining validation failed: {e}")
            state.errors.append(f"Literature mining error: {str(e)}")
            raise  # Stop pipeline if no real data is available
        except Exception as e:
            logger.error(f"Literature mining failed: {e}")
            state.errors.append(f"Literature mining error: {str(e)}")
            raise  # Stop pipeline on critical errors

        return state

    async def _get_gemini_context(self, drug: str, indication: str = None) -> Dict[str, Any]:
        """
        Use Gemini with grounding to find latest research.

        Args:
            drug: Drug name
            indication: Disease/condition

        Returns:
            Context with citations
        """
        if not self.gemini.is_available():
            return {}

        prompt = f"""Find the latest research (2023-2025) on {drug} for {'all indications' if not indication else indication}.

Focus on:
- Clinical trials and RCTs
- Response rates and non-response rates
- Pharmacogenomic studies
- Genetic factors affecting efficacy
- Subgroup analyses by genotype

Provide a concise summary with key findings."""

        try:
            result = await self.gemini.generate_with_grounding(
                prompt=prompt,
                temperature=0.1,
                max_tokens=2000
            )
            return result
        except Exception as e:
            logger.error(f"Gemini context search failed: {e}")
            return {}

    async def _mine_pubmed(self, drug: str, indication: str = None, progress_callback=None, article_count: int = 5) -> List[Dict[str, Any]]:
        """Mine PubMed for clinical studies."""
        # Search for PMIDs
        pmids = await self.pubmed.search_drug_studies(drug, indication, max_results=50)

        if not pmids:
            return []

        # Fetch article details
        articles = await self.pubmed.fetch_article_details(pmids)

        # Use Gemini to extract response data from abstracts
        enriched_articles = await self._extract_response_data_gemini(articles, drug, progress_callback, article_count)

        return enriched_articles

    async def _mine_clinical_trials(self, drug: str, indication: str = None, progress_callback=None, clinical_trials_count: int = 5) -> List[Dict[str, Any]]:
        """Mine ClinicalTrials.gov for trials and extract data."""
        trials = await self.clinical_trials.search_trials(drug, indication, max_results=50)

        # Extract data from trials using Gemini
        enriched_trials = await self._extract_from_clinical_trials(trials, drug, progress_callback, clinical_trials_count)

        return enriched_trials

    async def _mine_pharmgkb(self, drug: str) -> List[Dict[str, Any]]:
        """Mine PharmGKB for pharmacogenomic annotations."""
        drugs = await self.pharmgkb.search_drug(drug)

        if not drugs:
            return []

        drug_id = drugs[0].get("id")
        annotations = await self.pharmgkb.get_drug_annotations(drug_id)
        labels = await self.pharmgkb.get_drug_labels(drug_id)

        return annotations + labels

    async def _extract_single_trial(
        self,
        trial: Dict[str, Any],
        drug: str,
        idx: int,
        total: int,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Extract data from a single clinical trial with Gemini.

        Args:
            trial: Clinical trial data
            drug: Drug name
            idx: Trial index (1-based)
            total: Total number of trials
            progress_callback: Optional progress callback

        Returns:
            Enriched trial with extracted data
        """
        if progress_callback:
            await progress_callback({
                "type": "progress",
                "step": "extracting_trial",
                "message": f"Extracting data from clinical trial {idx}/{total} (NCT: {trial.get('nct_id', 'unknown')})",
                "progress": 35 + (idx / total) * 5  # Progress from 35% to 40%
            })

        # Build description from trial data
        description = f"""
Title: {trial.get('title', '')}
Condition: {trial.get('condition', '')}
Intervention: {trial.get('intervention', '')}
Enrollment: {trial.get('enrollment', 0)} patients
Primary Outcome: {trial.get('primary_outcome_measure', '')}
Primary Outcome Description: {trial.get('primary_outcome_description', '')}
"""

        if len(description.strip()) < 100:
            return trial

        try:
            # Use Gemini to extract response data
            prompt = f"""Extract clinical response data from this clinical trial about {drug}.

Trial Information:
{description}

CRITICAL RULES:
1. ONLY extract numbers explicitly stated in the description
2. DO NOT infer or estimate
3. If no response rate data available, set response/non_response to null
4. Always use the enrollment count as sample_size

Extract:
- sample_size (use the enrollment count: {trial.get('enrollment', 0)})
- response_rate (if explicitly stated in outcome description)
- non_response_rate (if explicitly stated)
- endpoint (primary outcome measure)
"""

            extracted_data = await self.gemini.generate_structured(
                prompt=prompt,
                response_schema=ExtractedClinicalData,
                temperature=0
            )

            if extracted_data:
                # Always use enrollment as sample size
                if not extracted_data.sample_size:
                    extracted_data.sample_size = trial.get('enrollment', 0)

                # Validate extracted data
                if extracted_data.sample_size and extracted_data.sample_size >= 10:
                    if extracted_data.response_rate is not None or extracted_data.non_response_rate is not None:
                        # Validate rates
                        valid = True
                        if extracted_data.response_rate is not None:
                            valid = valid and (0 <= extracted_data.response_rate <= 1)
                        if extracted_data.non_response_rate is not None:
                            valid = valid and (0 <= extracted_data.non_response_rate <= 1)

                        if valid:
                            trial.update({
                                "sample_size": extracted_data.sample_size,
                                "response_rate": extracted_data.response_rate,
                                "non_response_rate": extracted_data.non_response_rate,
                                "endpoint": extracted_data.endpoint or trial.get('primary_outcome_measure', '')
                            })
                            logger.info(
                                f"Extracted VALID data from trial {trial.get('nct_id')}: "
                                f"n={extracted_data.sample_size}, "
                                f"response={extracted_data.response_rate}, "
                                f"non_response={extracted_data.non_response_rate}"
                            )
                        else:
                            logger.warning(f"Extracted INVALID data from trial {trial.get('nct_id')}: Invalid rates")

        except Exception as e:
            logger.warning(f"Failed to extract data from trial {trial.get('nct_id')}: {e}")

        return trial

    async def _extract_from_clinical_trials(
        self,
        trials: List[Dict[str, Any]],
        drug: str,
        progress_callback=None,
        clinical_trials_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract data from clinical trials using Gemini (CONCURRENT VERSION).

        Processes multiple trials in parallel using asyncio.Semaphore to limit
        concurrent requests while respecting rate limits.

        Args:
            trials: List of clinical trials from ClinicalTrials.gov
            drug: Drug name
            progress_callback: Optional callback for progress updates
            clinical_trials_count: Number of trials to process (1-20, default: 5)

        Returns:
            Enriched trials with extracted data
        """
        # Process top trials that have enrollment data
        trials_with_data = [t for t in trials if t.get('enrollment') and t.get('enrollment') > 0]
        trials_to_process = trials_with_data[:clinical_trials_count]  # Use user's choice

        total_trials = len(trials_to_process)

        if total_trials == 0:
            return []

        # Process trials concurrently with semaphore to limit concurrent requests
        # Limit to 5 concurrent requests to avoid overwhelming the API
        semaphore = asyncio.Semaphore(5)

        async def _extract_with_limit(trial, idx):
            async with semaphore:
                # Rate limiter in gemini_service will handle timing automatically
                return await self._extract_single_trial(
                    trial, drug, idx, total_trials, progress_callback
                )

        # Create tasks for all trials
        tasks = [
            _extract_with_limit(trial, idx)
            for idx, trial in enumerate(trials_to_process, 1)
        ]

        # Execute all tasks concurrently, return_exceptions=True to handle individual failures
        enriched = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        result = []
        for trial_result in enriched:
            if isinstance(trial_result, Exception):
                logger.error(f"Trial extraction failed: {trial_result}")
            else:
                result.append(trial_result)

        return result

    async def _extract_single_article(
        self,
        article: Dict[str, Any],
        drug: str,
        idx: int,
        total: int,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Extract data from a single article with Gemini.

        Args:
            article: Article with abstract
            drug: Drug name
            idx: Article index (1-based)
            total: Total number of articles
            progress_callback: Optional progress callback

        Returns:
            Enriched article with extracted data
        """
        abstract = article.get("abstract", "")

        # Send progress update for this article
        if progress_callback:
            await progress_callback({
                "type": "progress",
                "step": "extracting_article",
                "message": f"Extracting data from article {idx}/{total} (PMID: {article.get('pmid', 'unknown')})",
                "progress": 10 + (idx / total) * 25  # Progress from 10% to 35%
            })

        try:
            # Use Gemini's structured output with STRICT validation
            prompt = f"""Extract ONLY explicitly stated clinical response data from this abstract about {drug}.

Abstract:
{abstract}

CRITICAL RULES:
1. ONLY extract numbers that are EXPLICITLY stated in the abstract text
2. DO NOT infer, estimate, or calculate numbers
3. DO NOT extract numbers from secondary analyses or mentions
4. If a field is not EXPLICITLY stated, set it to null
5. Only extract the PRIMARY study endpoint data

Extract information about:
- Total sample size (ONLY if explicitly stated: "n=X" or "X patients")
- Response rate (ONLY if primary endpoint explicitly states a success rate)
- Non-response rate (ONLY if explicitly stated, NOT calculated from response rate)
- Primary endpoint (exact text from abstract)
- Subgroup analyses (ONLY pre-specified subgroups with explicit n and rate)
- Genetic/pharmacogenomic data (ONLY if genotyping results are explicitly reported)
- Genetic markers (ONLY specific rs IDs or gene variants explicitly mentioned)

If you cannot find explicit numbers for sample_size, response_rate, or non_response_rate in the abstract text, set ALL fields to null. Do not guess or infer."""

            # Use Gemini's structured output with Pydantic schema
            extracted_data = await self.gemini.generate_structured(
                prompt=prompt,
                response_schema=ExtractedClinicalData,
                temperature=0
            )

            if extracted_data:
                # STRICT VALIDATION: Only use data if it meets quality thresholds
                is_valid = False
                validation_reason = "No data extracted"

                # Check if we have minimum required data (sample size + outcome)
                if extracted_data.sample_size and extracted_data.sample_size >= 10:
                    if extracted_data.response_rate is not None or extracted_data.non_response_rate is not None:
                        # Validate rates are in valid range
                        if extracted_data.response_rate is not None:
                            if 0 <= extracted_data.response_rate <= 1:
                                is_valid = True
                            else:
                                validation_reason = f"Invalid response_rate: {extracted_data.response_rate}"
                        if extracted_data.non_response_rate is not None:
                            if 0 <= extracted_data.non_response_rate <= 1:
                                is_valid = True
                            else:
                                validation_reason = f"Invalid non_response_rate: {extracted_data.non_response_rate}"
                    else:
                        validation_reason = "No outcome rates extracted"
                else:
                    validation_reason = f"Sample size too small or missing: {extracted_data.sample_size}"

                if is_valid:
                    # Merge with article
                    article.update({
                        "sample_size": extracted_data.sample_size,
                        "response_rate": extracted_data.response_rate,
                        "non_response_rate": extracted_data.non_response_rate,
                        "endpoint": extracted_data.endpoint,
                        "subgroups": [sg.model_dump() for sg in extracted_data.subgroups],
                        "has_genetic_data": extracted_data.has_genetic_data,
                        "genetic_markers": extracted_data.genetic_markers
                    })
                    logger.info(
                        f"Extracted VALID data from PMID {article.get('pmid')}: "
                        f"n={extracted_data.sample_size}, "
                        f"response={extracted_data.response_rate}, "
                        f"non_response={extracted_data.non_response_rate}"
                    )
                else:
                    logger.warning(
                        f"Extracted INVALID data from PMID {article.get('pmid')}: {validation_reason}"
                    )

        except Exception as e:
            logger.warning(f"Failed to extract data from PMID {article.get('pmid')}: {e}")

        return article

    async def _extract_response_data_gemini(
        self,
        articles: List[Dict[str, Any]],
        drug: str,
        progress_callback=None,
        article_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Use Gemini with structured output to extract data from abstracts (CONCURRENT VERSION).

        Processes multiple articles in parallel using asyncio.Semaphore to limit
        concurrent requests while respecting rate limits.

        Args:
            articles: List of articles with abstracts
            drug: Drug name for context
            progress_callback: Optional callback for progress updates
            article_count: Number of articles to process (1-20, default: 5)

        Returns:
            Enriched articles with extracted data
        """
        # Filter out low-quality abstracts (<200 chars) before processing
        # Then process user-specified number of articles (default 5)
        filtered_articles = [a for a in articles if a.get("abstract") and len(a.get("abstract", "")) >= 200]
        articles_to_process = filtered_articles[:article_count]  # Use user's choice

        total_articles = len(articles_to_process)

        if total_articles == 0:
            return []

        # Process articles concurrently with semaphore to limit concurrent requests
        # Limit to 5 concurrent requests to avoid overwhelming the API
        semaphore = asyncio.Semaphore(5)

        async def _extract_with_limit(article, idx):
            async with semaphore:
                # Rate limiter in gemini_service will handle timing automatically
                return await self._extract_single_article(
                    article, drug, idx, total_articles, progress_callback
                )

        # Create tasks for all articles
        tasks = [
            _extract_with_limit(article, idx)
            for idx, article in enumerate(articles_to_process, 1)
        ]

        # Execute all tasks concurrently, return_exceptions=True to handle individual failures
        enriched = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        result = []
        for article_result in enriched:
            if isinstance(article_result, Exception):
                logger.error(f"Article extraction failed: {article_result}")
            else:
                result.append(article_result)

        return result

    async def close(self):
        """Clean up resources."""
        await self.clinical_trials.close()
        await self.pharmgkb.close()
