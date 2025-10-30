"""
PharmGKB API service for pharmacogenomic knowledge.
"""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PharmGKBService:
    """Service for querying PharmGKB API."""

    BASE_URL = "https://api.pharmgkb.org/v1/data"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json"}
        )

    async def search_drug(self, drug_name: str) -> List[Dict[str, Any]]:
        """
        Search for drug in PharmGKB by name with multiple fallback strategies.

        Args:
            drug_name: Drug name (generic or brand)

        Returns:
            List of matching drugs with their PharmGKB IDs
        """
        # Try multiple search strategies
        search_variations = [
            drug_name.strip().lower(),  # Try lowercase first (PharmGKB prefers lowercase)
            drug_name.strip(),          # Try original capitalization
            drug_name.strip().title(),  # Try title case
        ]

        # Remove duplicates while preserving order
        search_variations = list(dict.fromkeys(search_variations))

        for variation in search_variations:
            endpoint = f"{self.BASE_URL}/chemical"
            params = {"name": variation, "view": "base"}

            try:
                response = await self._make_request(endpoint, params)

                if response.get("status") == "success":
                    data = response.get("data", [])
                    if data:
                        logger.info(f"Found {len(data)} PharmGKB entries for {drug_name} (using '{variation}')")
                        return data

            except httpx.HTTPStatusError as e:
                # 404 is expected for drugs not in PharmGKB - continue to next variation
                if e.response.status_code == 404:
                    logger.debug(f"PharmGKB: '{variation}' not found (404) - trying next variation")
                    continue
                else:
                    # Other HTTP errors (500, 503, etc.) - log but continue
                    logger.debug(f"PharmGKB: '{variation}' returned {e.response.status_code}")
                    continue
            except Exception as e:
                # Network errors, timeouts, etc. - log but continue
                logger.debug(f"PharmGKB lookup error for '{variation}': {e}")
                continue

        # All variations failed
        logger.info(f"PharmGKB data not available for {drug_name} (not found in database)")
        return []

    async def get_drug_annotations(self, pharmgkb_id: str) -> List[Dict[str, Any]]:
        """
        Get clinical annotations for a drug.

        Args:
            pharmgkb_id: PharmGKB accession ID (e.g., PA...)

        Returns:
            List of clinical annotations

        Note: This endpoint frequently returns 404. PharmGKB may have restricted or deprecated it.
        """
        # Skip this endpoint - consistently returns 404 for most chemicals
        # PharmGKB API documentation is outdated or endpoint requires special access
        logger.debug(f"Skipping PharmGKB annotations (endpoint unavailable for most chemicals)")
        return []
        
        # Original implementation (disabled due to API limitations):
        # endpoint = f"{self.BASE_URL}/clinicalAnnotation"
        # params = {"location.id": pharmgkb_id}
        # try:
        #     response = await self._make_request(endpoint, params)
        #     annotations = response.get("data", [])
        #     logger.info(f"Found {len(annotations)} annotations for {pharmgkb_id}")
        #     return [self._parse_annotation(ann) for ann in annotations]
        # except Exception as e:
        #     logger.info(f"PharmGKB annotations not available for {pharmgkb_id} (optional feature)")
        #     return []

    async def get_drug_labels(self, pharmgkb_id: str) -> List[Dict[str, Any]]:
        """
        Get FDA/EMA/other drug labels with pharmacogenomic info.

        Args:
            pharmgkb_id: PharmGKB drug ID

        Returns:
            List of drug labels

        Note: This endpoint frequently returns 400/404. PharmGKB may have restricted or deprecated it.
        """
        # Skip this endpoint - consistently returns 400/404 for most chemicals
        # PharmGKB API documentation is outdated or endpoint requires special access
        logger.debug(f"Skipping PharmGKB drug labels (endpoint unavailable for most chemicals)")
        return []
        
        # Original implementation (disabled due to API limitations):
        # endpoint = f"{self.BASE_URL}/drugLabel"
        # params = {"chemical.id": pharmgkb_id}
        # try:
        #     response = await self._make_request(endpoint, params)
        #     labels = response.get("data", [])
        #     logger.info(f"Found {len(labels)} drug labels for {pharmgkb_id}")
        #     return [self._parse_label(label) for label in labels]
        # except Exception as e:
        #     logger.info(f"PharmGKB drug labels not available for {pharmgkb_id} (optional feature)")
        #     return []

    async def get_gene_drug_associations(self, gene_symbol: str, drug_name: str) -> List[Dict[str, Any]]:
        """
        Get associations between a gene and drug.

        Args:
            gene_symbol: Gene symbol (e.g., CYP2C19)
            drug_name: Drug name

        Returns:
            List of gene-drug associations
        """
        # First, get gene ID
        gene_data = await self._search_gene(gene_symbol)
        if not gene_data:
            return []

        gene_id = gene_data[0].get("id")

        # Get annotations involving this gene
        endpoint = f"{self.BASE_URL}/clinicalAnnotation"
        params = {"gene.id": gene_id}

        try:
            response = await self._make_request(endpoint, params)
            annotations = response.get("data", [])

            # Filter for the specific drug
            drug_annotations = [
                ann for ann in annotations
                if drug_name.lower() in str(ann.get("chemicals", [])).lower()
            ]

            logger.info(f"Found {len(drug_annotations)} associations for {gene_symbol}-{drug_name}")
            return [self._parse_annotation(ann) for ann in drug_annotations]

        except Exception as e:
            logger.info(f"PharmGKB gene-drug associations not available (optional feature)")
            return []

    async def get_variant_annotations(self, rs_id: str) -> List[Dict[str, Any]]:
        """
        Get clinical annotations for a specific variant.

        Args:
            rs_id: dbSNP rs ID

        Returns:
            List of variant annotations
        """
        # First, search for the variant
        variant_data = await self._search_variant(rs_id)
        if not variant_data:
            return []

        variant_id = variant_data[0].get("id")

        # Get annotations
        endpoint = f"{self.BASE_URL}/clinicalAnnotation"
        params = {"variant.id": variant_id}

        try:
            response = await self._make_request(endpoint, params)
            annotations = response.get("data", [])

            logger.info(f"Found {len(annotations)} annotations for {rs_id}")
            return [self._parse_annotation(ann) for ann in annotations]

        except Exception as e:
            logger.info(f"PharmGKB variant annotations not available for {rs_id} (optional feature)")
            return []

    async def _search_gene(self, gene_symbol: str) -> List[Dict[str, Any]]:
        """Search for gene by symbol."""
        # Correct endpoint: /gene with symbol parameter (not /gene/search with query)
        endpoint = f"{self.BASE_URL}/gene"
        params = {
            "view": "base",
            "symbol": gene_symbol
        }

        try:
            response = await self._make_request(endpoint, params)
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Gene search failed for {gene_symbol}: {e}")
            return []

    async def _search_variant(self, rs_id: str) -> List[Dict[str, Any]]:
        """Search for variant by rs ID."""
        # Correct endpoint: /variant with name parameter (not /variant/search with query)
        endpoint = f"{self.BASE_URL}/variant"
        params = {
            "view": "base",
            "name": rs_id
        }

        try:
            response = await self._make_request(endpoint, params)
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Variant search failed for {rs_id}: {e}")
            return []

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to PharmGKB API with smart retry logic.

        Retries: 500, 503, 429 (server errors, rate limits)
        Does NOT retry: 404, 400 (client errors - expected for missing data)
        """
        max_retries = 3
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = await self.client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code

                # Don't retry client errors (400-499) - they indicate bad requests or missing data
                if 400 <= status_code < 500:
                    # 404 is completely expected - many drugs aren't in PharmGKB
                    # Don't log these at all since we handle them gracefully
                    if status_code != 404:
                        logger.debug(f"PharmGKB {status_code} error: {endpoint}")
                    raise  # Don't retry client errors

                # Retry server errors and rate limits
                if attempt < max_retries - 1 and status_code in [429, 500, 502, 503, 504]:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"PharmGKB {status_code} error. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"PharmGKB connection error. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise

        # Should not reach here, but raise last exception if we do
        if last_exception:
            raise last_exception

    def _parse_annotation(self, annotation: Dict[str, Any]) -> Dict[str, Any]:
        """Parse clinical annotation."""
        return {
            "id": annotation.get("id"),
            "type": annotation.get("type"),
            "gene": annotation.get("gene", {}).get("symbol"),
            "variant": annotation.get("variant", {}).get("name"),
            "chemicals": [c.get("name") for c in annotation.get("chemicals", [])],
            "phenotype": annotation.get("phenotype", {}).get("name"),
            "level_of_evidence": annotation.get("levelOfEvidence"),
            "annotation_text": annotation.get("textMarkdown"),
            "pmids": annotation.get("literature", []),
            "url": f"https://www.pharmgkb.org/clinicalAnnotation/{annotation.get('id')}"
        }

    def _parse_label(self, label: Dict[str, Any]) -> Dict[str, Any]:
        """Parse drug label."""
        return {
            "id": label.get("id"),
            "source": label.get("source"),
            "drug": label.get("chemical", {}).get("name"),
            "has_pgx_info": label.get("hasPrescribingInfo", False),
            "genes": [g.get("symbol") for g in label.get("genes", [])],
            "variants": [v.get("name") for v in label.get("variants", [])],
            "text": label.get("textMarkdown"),
            "url": f"https://www.pharmgkb.org/labelAnnotation/{label.get('id')}"
        }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
