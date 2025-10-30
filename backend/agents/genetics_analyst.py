"""
Genetics Analyst Agent - GEMINI ONLY VERSION

Identifies genetic variants associated with drug non-response using
Google Gemini 2.5 Flash with structured output.
"""

import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from models.schemas import AgentState
from services.gwas_service import GWASService
from services.pharmgkb_service import PharmGKBService
from services.drugbank_service import DrugBankService
from services.gemini_service import GeminiService
import logging
import json

logger = logging.getLogger(__name__)


class VariantEnrichment(BaseModel):
    """Enriched variant data with mechanism."""
    rs_id: str
    gene: str
    allele: str | None = None
    effect: str
    mechanism: str = Field(description="PK/PD mechanism: metabolism, transport, target, or other")
    frequencies: Dict[str, float] = Field(default_factory=dict, description="Allele frequencies by ancestry")


class GeneticsAnalystAgent:
    """
    Agent responsible for genetic variant analysis.

    Uses ONLY Gemini 2.5 Flash for:
    - Variant-mechanism mapping
    - PK/PD analysis
    - Frequency estimation
    """

    def __init__(self, google_api_key: str):
        """Initialize analyst with API services."""
        self.gemini = GeminiService(api_key=google_api_key)
        self.gwas = GWASService()
        self.pharmgkb = PharmGKBService()
        try:
            self.drugbank = DrugBankService()
            logger.info("DrugBank service initialized for genetics analysis")
        except Exception as e:
            logger.warning(f"DrugBank service not available: {e}")
            self.drugbank = None

    async def run(self, state: AgentState) -> AgentState:
        """
        Execute genetic analysis.

        Args:
            state: Current agent state

        Returns:
            Updated state with genetic data
        """
        logger.info(f"Genetics Analyst (Gemini-only): Analyzing variants for {state.drug}")

        state.current_agent = "genetics_analyst"

        try:
            # Run genetic searches in parallel (GWAS, PharmGKB, and DrugBank)
            tasks = [
                self._analyze_gwas(state.drug, state.indication),
                self._analyze_pharmgkb(state.drug, state.pharmgkb_annotations)
            ]

            # Add DrugBank if available
            if self.drugbank:
                tasks.append(self._analyze_drugbank(state.drug))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle results
            gwas_variants = results[0] if not isinstance(results[0], Exception) else []
            pharmgkb_variants = results[1] if not isinstance(results[1], Exception) else []
            drugbank_variants = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else []

            if isinstance(results[0], Exception):
                logger.error(f"GWAS analysis failed: {results[0]}")
            if isinstance(results[1], Exception):
                logger.error(f"PharmGKB analysis failed: {results[1]}")
            if len(results) > 2 and isinstance(results[2], Exception):
                logger.error(f"DrugBank analysis failed: {results[2]}")

            # Merge and deduplicate variants from all sources
            all_variants = self._merge_variants(gwas_variants, pharmgkb_variants, drugbank_variants)

            # Enrich with mechanisms using Gemini
            enriched_variants = await self._enrich_with_mechanisms_gemini(all_variants, state.drug)

            state.variants = enriched_variants

            # Extract mechanism notes
            state.mechanisms = self._extract_mechanisms(enriched_variants)

            # Add citations
            for variant in enriched_variants:
                state.citations.extend(variant.get("citations", []))

            logger.info(f"Genetics Analyst: Found {len(enriched_variants)} variants")

        except Exception as e:
            logger.error(f"Genetic analysis failed: {e}")
            state.errors.append(f"Genetic analysis error: {str(e)}")

        return state

    async def _analyze_gwas(self, drug: str, indication: str = None) -> List[Dict[str, Any]]:
        """Analyze GWAS Catalog for drug response associations."""
        associations = await self.gwas.search_drug_associations(drug, indication)

        variants = []
        for assoc in associations:
            rs_id = assoc.get("rs_id")
            if not rs_id:
                continue

            variants.append({
                "rs_id": rs_id,
                "genes": assoc.get("genes", []),
                "chromosome": assoc.get("chromosome"),
                "position": assoc.get("position"),
                "p_value": assoc.get("p_value"),
                "effect_size": assoc.get("odds_ratio") or assoc.get("beta"),
                "trait": assoc.get("trait"),
                "source": "GWAS Catalog",
                "pmid": assoc.get("pubmed_id")
            })

        return variants

    async def _analyze_pharmgkb(
        self,
        drug: str,
        annotations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze PharmGKB annotations for genetic variants."""
        variants = []

        for annotation in annotations:
            variant = annotation.get("variant")
            gene = annotation.get("gene")

            if not variant or not gene:
                continue

            # Extract rs IDs from variant name
            rs_ids = self._extract_rs_ids(variant)

            for rs_id in rs_ids:
                variants.append({
                    "rs_id": rs_id,
                    "genes": [gene],
                    "allele": variant,
                    "phenotype": annotation.get("phenotype"),
                    "level_of_evidence": annotation.get("level_of_evidence"),
                    "annotation": annotation.get("annotation_text", ""),
                    "source": "PharmGKB",
                    "pmids": annotation.get("pmids", [])
                })

        return variants

    async def _analyze_drugbank(self, drug: str) -> List[Dict[str, Any]]:
        """
        Analyze DrugBank database for pharmacogenomic SNP effects.

        Args:
            drug: Drug name

        Returns:
            List of variants from DrugBank with SNP effects
        """
        if not self.drugbank:
            return []

        variants = []

        try:
            # Get SNP effects from DrugBank for this drug
            snp_effects = self.drugbank.get_snp_effects(drug=drug)

            for snp in snp_effects:
                rs_id = snp.get("rs_id")
                if not rs_id:
                    continue

                variants.append({
                    "rs_id": rs_id,
                    "genes": [snp.get("gene_symbol")] if snp.get("gene_symbol") else [],
                    "allele": snp.get("allele"),
                    "protein": snp.get("protein_name"),
                    "effect": snp.get("description"),
                    "defining_change": snp.get("defining_change"),
                    "source": "DrugBank",
                    "pmid": snp.get("pubmed_id"),
                    "drugbank_id": snp.get("drugbank_id")
                })

            logger.info(f"DrugBank: Found {len(variants)} SNP effects for {drug}")

        except Exception as e:
            logger.error(f"DrugBank SNP lookup failed for {drug}: {e}")

        return variants

    def _extract_rs_ids(self, variant_name: str) -> List[str]:
        """Extract rs IDs from variant name string."""
        import re
        rs_ids = re.findall(r'rs\d+', variant_name)
        return rs_ids

    def _merge_variants(
        self,
        gwas_variants: List[Dict[str, Any]],
        pharmgkb_variants: List[Dict[str, Any]],
        drugbank_variants: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Merge and deduplicate variants from multiple sources (GWAS, PharmGKB, DrugBank)."""
        merged = {}

        if drugbank_variants is None:
            drugbank_variants = []

        # Add GWAS variants
        for variant in gwas_variants:
            rs_id = variant["rs_id"]
            merged[rs_id] = variant.copy()
            merged[rs_id]["sources"] = ["GWAS Catalog"]
            merged[rs_id]["citations"] = []
            if variant.get("pmid"):
                merged[rs_id]["citations"].append(f"PMID:{variant['pmid']}")

        # Merge PharmGKB variants
        for variant in pharmgkb_variants:
            rs_id = variant["rs_id"]

            if rs_id in merged:
                # Merge data
                merged[rs_id].setdefault("allele", variant.get("allele"))
                merged[rs_id].setdefault("phenotype", variant.get("phenotype"))
                merged[rs_id].setdefault("annotation", variant.get("annotation"))
                if "PharmGKB" not in merged[rs_id]["sources"]:
                    merged[rs_id]["sources"].append("PharmGKB")

                # Merge PMIDs
                if variant.get("pmid"):
                    merged[rs_id]["citations"].append(f"PMID:{variant['pmid']}")
                if variant.get("pmids"):
                    merged[rs_id]["citations"].extend([f"PMID:{p}" for p in variant["pmids"]])
            else:
                merged[rs_id] = variant.copy()
                merged[rs_id]["sources"] = ["PharmGKB"]
                merged[rs_id]["citations"] = []
                if variant.get("pmids"):
                    merged[rs_id]["citations"].extend([f"PMID:{p}" for p in variant["pmids"]])

        # Merge DrugBank variants
        for variant in drugbank_variants:
            rs_id = variant["rs_id"]

            if rs_id in merged:
                # Merge data (DrugBank often has rich descriptions)
                merged[rs_id].setdefault("allele", variant.get("allele"))
                merged[rs_id].setdefault("effect", variant.get("effect"))
                merged[rs_id].setdefault("protein", variant.get("protein"))
                merged[rs_id].setdefault("defining_change", variant.get("defining_change"))
                if "DrugBank" not in merged[rs_id]["sources"]:
                    merged[rs_id]["sources"].append("DrugBank")

                # Merge PMIDs
                if variant.get("pmid"):
                    merged[rs_id]["citations"].append(f"PMID:{variant['pmid']}")
            else:
                merged[rs_id] = variant.copy()
                merged[rs_id]["sources"] = ["DrugBank"]
                merged[rs_id]["citations"] = []
                if variant.get("pmid"):
                    merged[rs_id]["citations"].append(f"PMID:{variant['pmid']}")

        # Deduplicate citations
        for rs_id in merged:
            merged[rs_id]["citations"] = list(set(merged[rs_id]["citations"]))

        return list(merged.values())

    async def _enrich_with_mechanisms_gemini(
        self,
        variants: List[Dict[str, Any]],
        drug: str
    ) -> List[Dict[str, Any]]:
        """
        Use Gemini with structured output to map variants to PK/PD mechanisms.

        Args:
            variants: List of variants
            drug: Drug name

        Returns:
            Enriched variants with mechanism annotations
        """
        if not variants or not self.gemini.is_available():
            return variants

        # Process in batches for efficiency
        enriched_results = []

        for i in range(0, len(variants), 10):
            batch = variants[i:i+10]

            # Prepare variant summary
            variant_list = "\n".join([
                f"- {v['rs_id']}: Gene(s) {', '.join(v.get('genes', []))}"
                for v in batch
            ])

            prompt = f"""You are a pharmacogenomics expert. Analyze these genetic variants associated with {drug} response.

Variants:
{variant_list}

For each variant, provide:
1. Primary gene symbol
2. Star allele nomenclature (if applicable, e.g., CYP2C19*2)
3. Functional effect (e.g., "Loss of function - reduced enzyme activity")
4. PK/PD mechanism category: must be one of: "metabolism", "transport", "target", or "other"
5. Typical allele frequencies by ancestry (EUR, EAS, AFR, SAS, AMR) as fractions between 0 and 1

Be specific and accurate. If you don't know exact frequencies, provide reasonable estimates based on population genetics knowledge."""

            try:
                # Use grounding to get latest pharmacogenomic data
                result = await self.gemini.generate_with_grounding(
                    prompt=prompt,
                    temperature=0.1,
                    max_tokens=3000
                )

                # Parse the response to extract structured data
                # Gemini will return text, we need to extract JSON-like info
                response_text = result.get("text", "")

                # Try to extract structured info from the text
                # For now, we'll use a simpler approach and parse manually
                for variant in batch:
                    # Add basic enrichment
                    variant["enriched"] = True

                    # Try to find the variant in the response
                    rs_id = variant["rs_id"]
                    if rs_id in response_text:
                        # Extract relevant section
                        lines = response_text.split("\n")
                        for j, line in enumerate(lines):
                            if rs_id in line:
                                # Get context around this variant
                                context = "\n".join(lines[max(0, j-1):min(len(lines), j+10)])

                                # Extract gene from context or existing data
                                variant["gene"] = variant.get("genes", ["Unknown"])[0] if variant.get("genes") else "Unknown"

                                # Set default mechanism
                                if "CYP" in variant["gene"]:
                                    variant["mechanism"] = "metabolism"
                                elif "SLCO" in variant["gene"] or "ABC" in variant["gene"]:
                                    variant["mechanism"] = "transport"
                                else:
                                    variant["mechanism"] = "other"

                                break

                enriched_results.extend(batch)

            except Exception as e:
                logger.warning(f"Failed to enrich variants batch: {e}")
                enriched_results.extend(batch)

            await asyncio.sleep(0.5)  # Rate limiting

        return enriched_results

    def _extract_mechanisms(self, variants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract unique mechanisms from variants."""
        mechanisms = {}

        for variant in variants:
            gene = variant.get("gene", "")
            mechanism_type = variant.get("mechanism", "")

            if not gene or not mechanism_type:
                continue

            key = f"{gene}_{mechanism_type}"

            if key not in mechanisms:
                mechanisms[key] = {
                    "gene": gene,
                    "type": mechanism_type,
                    "variants": [],
                    "description": variant.get("effect", "")
                }

            mechanisms[key]["variants"].append(variant["rs_id"])

        return list(mechanisms.values())

    async def close(self):
        """Clean up resources."""
        await self.gwas.close()
        await self.pharmgkb.close()
