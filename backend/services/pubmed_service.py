"""
PubMed/NCBI E-utilities service for literature mining.
"""

import asyncio
from typing import List, Dict, Any, Optional
from Bio import Entrez
import xml.etree.ElementTree as ET
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import logging

logger = logging.getLogger(__name__)

# Configure Entrez
Entrez.email = os.getenv("NCBI_EMAIL", "user@example.com")
Entrez.api_key = os.getenv("NCBI_API_KEY")


class PubMedService:
    """Service for querying PubMed literature."""

    def __init__(self):
        self.rate_limit = int(os.getenv("PUBMED_REQUESTS_PER_SECOND", "3"))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_drug_studies(
        self,
        drug: str,
        indication: Optional[str] = None,
        max_results: int = 100
    ) -> List[str]:
        """
        Search PubMed for clinical studies on a drug.

        Args:
            drug: Drug name
            indication: Disease/condition (optional)
            max_results: Maximum results to return

        Returns:
            List of PMIDs
        """
        # Build search query
        query_parts = [
            f'"{drug}"[Title/Abstract]',
            '("clinical trial"[Publication Type] OR "randomized controlled trial"[Publication Type] OR "meta-analysis"[Publication Type])',
        ]

        if indication:
            query_parts.insert(1, f'"{indication}"[Title/Abstract]')

        query = " AND ".join(query_parts)

        logger.info(f"PubMed search query: {query}")

        # Execute search
        try:
            handle = await asyncio.to_thread(
                Entrez.esearch,
                db="pubmed",
                term=query,
                retmax=max_results,
                sort="relevance"
            )
            record = await asyncio.to_thread(Entrez.read, handle)
            handle.close()

            pmids = record.get("IdList", [])
            logger.info(f"Found {len(pmids)} PubMed articles")
            return pmids

        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_article_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed metadata for a list of PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of article metadata dicts
        """
        if not pmids:
            return []

        # Batch fetch (max 200 at a time)
        batch_size = 200
        all_articles = []

        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i:i + batch_size]
            pmid_str = ",".join(batch_pmids)

            try:
                handle = await asyncio.to_thread(
                    Entrez.efetch,
                    db="pubmed",
                    id=pmid_str,
                    rettype="xml",
                    retmode="xml"
                )
                xml_data = await asyncio.to_thread(handle.read)
                handle.close()

                # Parse XML
                root = ET.fromstring(xml_data)
                articles = self._parse_pubmed_xml(root)
                all_articles.extend(articles)

                # Rate limiting
                if i + batch_size < len(pmids):
                    await asyncio.sleep(1.0 / self.rate_limit)

            except Exception as e:
                logger.error(f"Failed to fetch PMIDs {pmid_str}: {e}")
                continue

        logger.info(f"Fetched details for {len(all_articles)} articles")
        return all_articles

    def _parse_pubmed_xml(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Parse PubMed XML response."""
        articles = []

        for article_node in root.findall(".//PubmedArticle"):
            try:
                pmid = article_node.findtext(".//PMID")
                title = article_node.findtext(".//ArticleTitle", "")
                abstract_parts = article_node.findall(".//AbstractText")
                abstract = " ".join([part.text or "" for part in abstract_parts])

                # Journal info
                journal = article_node.findtext(".//Journal/Title", "")
                pub_year = article_node.findtext(".//PubDate/Year", "")

                # Publication types
                pub_types = [
                    pt.text for pt in article_node.findall(".//PublicationType")
                ]

                articles.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "journal": journal,
                    "year": pub_year,
                    "publication_types": pub_types,
                    "citation": f"PMID:{pmid}"
                })

            except Exception as e:
                logger.warning(f"Failed to parse article: {e}")
                continue

        return articles

    async def extract_response_data(
        self,
        articles: List[Dict[str, Any]],
        drug: str
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to extract response/non-response data from abstracts.

        Args:
            articles: List of article metadata
            drug: Drug name for context

        Returns:
            List of extracted data with response rates
        """
        # This will be implemented with Claude API
        # For now, return structured placeholder
        extracted = []

        for article in articles:
            # TODO: Implement LLM extraction
            # Send abstract to Claude with structured prompt
            # Extract: sample size, response rate, non-response rate, endpoint, subgroups

            extracted.append({
                "pmid": article["pmid"],
                "title": article["title"],
                "year": article["year"],
                "sample_size": None,  # Extract from abstract
                "response_rate": None,  # Extract from abstract
                "endpoint": None,  # Extract from abstract
                "raw_abstract": article["abstract"]
            })

        return extracted
