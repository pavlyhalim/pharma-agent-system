"""
GWAS Catalog service for genetic variant data.
"""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)


class GWASService:
    """Service for querying GWAS Catalog API."""

    BASE_URL = "https://www.ebi.ac.uk/gwas/rest/api"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_drug_associations(
        self,
        drug: str,
        indication: str = None,
        p_value_threshold: float = 5e-8
    ) -> List[Dict[str, Any]]:
        """
        Search for genetic associations related to drug response.

        Research Citation: GWAS_IMPLEMENTATION_ANALYSIS.md - Issue 1 (HAL Navigation)
        Best Practice: Use HAL _links for navigation, don't construct URLs manually

        Args:
            drug: Drug name
            indication: Disease/condition being treated (e.g., "cardiovascular disease")
            p_value_threshold: P-value cutoff for significance (default: 5e-8 genome-wide)

        Returns:
            List of associations with genetic variants
        """
        # Search for indication-related traits if provided
        # GWAS catalog organizes by disease traits, not drugs
        if indication:
            traits = await self._search_traits(indication)
            if traits:
                logger.info(f"Found {len(traits)} GWAS EFO traits for indication: {indication}")
        else:
            # If no indication, skip GWAS search
            # (drug names alone don't work as disease traits)
            logger.info(f"No indication provided for {drug}, skipping GWAS trait search")
            return []

        if not traits:
            logger.info(f"No GWAS traits found for indication: {indication}")
            return []

        # Fetch associations for top EFO traits (limit to 5 to avoid excessive API calls)
        # Research: Use actual trait data, not just slicing - respect API structure
        all_associations = []
        processed_count = 0

        for trait in traits:
            if processed_count >= 5:
                break

            # Extract EFO ID from trait URI (e.g., "http://www.ebi.ac.uk/efo/EFO_0001645" -> "EFO_0001645")
            efo_uri = trait.get("uri", "")
            if not efo_uri:
                continue

            efo_id = efo_uri.split("/")[-1]
            if not efo_id.startswith("EFO_"):
                continue

            trait_name = trait.get("trait", "Unknown")
            logger.debug(f"Fetching associations for EFO trait: {trait_name} ({efo_id})")

            associations = await self._fetch_associations_for_trait(efo_id, p_value_threshold)
            all_associations.extend(associations)
            processed_count += 1

        logger.info(f"Found {len(all_associations)} GWAS associations for {indication} across {processed_count} EFO traits")
        return all_associations

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _search_traits(self, disease_trait: str) -> List[Dict[str, Any]]:
        """
        Search for traits related to a disease.

        Note: GWAS Catalog organizes by disease traits (e.g., "cardiovascular disease"),
        not by drug names. This searches for genetic associations with the disease itself.

        Args:
            disease_trait: Disease or condition name (e.g., "cardiovascular disease", "diabetes")
        """
        endpoint = f"{self.BASE_URL}/studies/search/findByDiseaseTrait"
        params = {"diseaseTrait": disease_trait}

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract EFO traits from studies
            studies = data.get("_embedded", {}).get("studies", [])
            traits = []
            for study in studies:
                efo_traits = study.get("efoTraits", [])
                traits.extend(efo_traits)

            return traits

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"No GWAS traits found for disease: {disease_trait}")
                return []
            raise
        except Exception as e:
            logger.error(f"GWAS trait search failed: {e}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_associations_for_trait(
        self,
        efo_id: str,
        p_value_threshold: float = 5e-8
    ) -> List[Dict[str, Any]]:
        """
        Fetch associations for a specific EFO trait using correct endpoint with pagination.

        Research Citation: GWAS_IMPLEMENTATION_ANALYSIS.md - Issue 2 (Correct Endpoint)
        Correct endpoint: /efoTraits/{EFO_ID}/associations (not /associations/search/findByEfoTraitsId)

        Research Citation: GWAS_IMPLEMENTATION_ANALYSIS.md - Issue 3 (Pagination)
        Best Practice: Follow HAL _links.next to retrieve all pages

        Args:
            efo_id: EFO trait identifier (e.g., "EFO_0001645")
            p_value_threshold: P-value cutoff (default: 5e-8 genome-wide significance)

        Returns:
            List of parsed associations
        """
        endpoint = f"{self.BASE_URL}/efoTraits/{efo_id}/associations"
        params = {'size': 100}  # Max results per page

        all_associations = []
        url = endpoint
        page_count = 0
        max_pages = 5  # Limit to prevent excessive API calls

        try:
            while url and page_count < max_pages:
                # Use params only for first request, subsequent URLs already have params
                response = await self.client.get(url, params=params if url == endpoint else {})
                response.raise_for_status()
                data = response.json()

                # Extract associations from HAL _embedded structure
                associations = data.get('_embedded', {}).get('associations', [])

                if not associations:
                    break

                # Parse and filter associations
                for assoc in associations:
                    parsed = self._parse_association(assoc)
                    # Client-side p-value filtering (research: server-side filtering not reliable)
                    if parsed and parsed.get('p_value') and parsed['p_value'] <= p_value_threshold:
                        all_associations.append(parsed)

                # Follow HAL next link for pagination
                url = data.get('_links', {}).get('next', {}).get('href')
                page_count += 1

                # Safety limit on total associations
                if len(all_associations) >= 500:
                    logger.debug(f"Reached 500 associations limit for {efo_id}")
                    break

            logger.debug(f"Retrieved {len(all_associations)} associations for {efo_id} across {page_count} pages")
            return all_associations

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"No associations found for EFO trait: {efo_id}")
                return []
            logger.error(f"HTTP error fetching associations for {efo_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch associations for trait {efo_id}: {e}")
            return []

    def _parse_association(self, association: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse GWAS association data following actual API structure.

        Research Citation: GWAS_IMPLEMENTATION_ANALYSIS.md - Issue 4 (Data Structure)
        Real field names: rsId, riskAllele, pvalue (lowercase), orPerCopyNum, betaNum, loci structure

        Args:
            association: Raw association dict from GWAS Catalog API

        Returns:
            Parsed association with standardized fields
        """
        try:
            # Extract loci information (for chromosome, position, genes)
            loci = association.get('loci', [])
            chromosome = None
            position = None
            genes = []

            if loci and len(loci) > 0:
                locus = loci[0]

                # Get chromosome and position from location
                location = locus.get('location', {})
                if location:
                    chromosome = location.get('chromosomeName')
                    position = location.get('chromosomePosition')

                # Extract genes from strongest risk alleles
                strongest_alleles = locus.get('strongestRiskAlleles', [])
                for allele in strongest_alleles:
                    risk_allele_name = allele.get('riskAlleleName', '')
                    # Format: "rs123456-A" or "rs123456-G"
                    if '-' in risk_allele_name:
                        gene_part = risk_allele_name.split('-')[1] if len(risk_allele_name.split('-')) > 1 else None
                        if gene_part and len(gene_part) < 20:  # Filter out non-gene strings
                            genes.append(gene_part)

                # Also extract author reported genes
                author_genes = locus.get('authorReportedGene', [])
                if isinstance(author_genes, list):
                    for gene in author_genes:
                        if isinstance(gene, dict) and gene.get('geneName'):
                            genes.append(gene['geneName'])

            # Extract rsID from strongest risk allele or snps
            rs_id = None
            if loci and len(loci) > 0:
                strongest_alleles = loci[0].get('strongestRiskAlleles', [])
                if strongest_alleles:
                    risk_allele_name = strongest_alleles[0].get('riskAlleleName', '')
                    # Format: "rs123456-A"
                    if '-' in risk_allele_name:
                        rs_id = risk_allele_name.split('-')[0]
                    elif risk_allele_name.startswith('rs'):
                        rs_id = risk_allele_name

            # Extract risk allele
            risk_allele = None
            if loci and len(loci) > 0:
                strongest_alleles = loci[0].get('strongestRiskAlleles', [])
                if strongest_alleles:
                    risk_allele = strongest_alleles[0].get('riskAlleleName')

            # Extract p-value (note: lowercase 'pvalue' in API)
            p_value = association.get('pvalue')  # lowercase!
            if p_value is None:
                # Try alternative fields
                p_value_mantissa = association.get('pvalueMantissa')
                p_value_exponent = association.get('pvalueExponent')
                if p_value_mantissa is not None and p_value_exponent is not None:
                    p_value = float(p_value_mantissa) * (10 ** float(p_value_exponent))

            # Extract effect size metrics
            odds_ratio = association.get('orPerCopyNum')  # Correct field name
            beta = association.get('betaNum')
            beta_unit = association.get('betaUnit')

            # Extract trait information
            trait = None
            traits = association.get('trait', []) or association.get('efoTraits', [])
            if isinstance(traits, list) and len(traits) > 0:
                trait = traits[0].get('trait') if isinstance(traits[0], dict) else None

            # Extract study information
            study_accession = None
            if '_links' in association and 'study' in association['_links']:
                study_href = association['_links']['study'].get('href', '')
                if study_href:
                    study_accession = study_href.split('/')[-1]

            return {
                "rs_id": rs_id,
                "chromosome": chromosome,
                "position": position,
                "genes": list(set(genes)) if genes else [],
                "risk_allele": risk_allele,
                "p_value": p_value,
                "odds_ratio": odds_ratio,
                "beta": beta,
                "beta_unit": beta_unit,
                "trait": trait,
                "study_accession": study_accession
            }

        except Exception as e:
            logger.error(f"Error parsing association: {e}")
            # Return minimal structure on error
            return {
                "rs_id": None,
                "chromosome": None,
                "position": None,
                "genes": [],
                "risk_allele": None,
                "p_value": association.get('pvalue'),
                "odds_ratio": None,
                "beta": None,
                "beta_unit": None,
                "trait": None,
                "study_accession": None
            }

    async def fetch_variant_details(self, rs_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific variant.

        Args:
            rs_id: dbSNP reference SNP ID

        Returns:
            Variant details
        """
        endpoint = f"{self.BASE_URL}/singleNucleotidePolymorphisms/search/findByRsId"
        params = {"rsId": rs_id}

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            snp = data.get("_embedded", {}).get("singleNucleotidePolymorphisms", [{}])[0]

            return {
                "rs_id": snp.get("rsId"),
                "merged": snp.get("merged"),
                "functional_class": snp.get("functionalClass"),
                "locations": snp.get("locations", []),
                "last_update_date": snp.get("lastUpdateDate")
            }

        except Exception as e:
            logger.error(f"Failed to fetch variant details for {rs_id}: {e}")
            return None

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
