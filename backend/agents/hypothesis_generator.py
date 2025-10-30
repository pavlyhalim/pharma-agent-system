"""
Hypothesis Generator Agent - GEMINI ONLY VERSION

Proposes formulation and dosing strategies using Google Gemini 2.5 Flash
with grounding for latest clinical guidelines.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from models.schemas import AgentState
from services.gemini_service import GeminiService
import logging
import re

logger = logging.getLogger(__name__)


def clean_markdown(text: str) -> str:
    """
    Remove markdown formatting from text to make it readable for normal users.

    Removes:
    - **bold** and __bold__
    - *italic* and _italic_
    - # headers
    - [links](url)
    - `code`
    - > blockquotes
    - - and * bullets
    - HTML tags

    Args:
        text: Text with markdown formatting

    Returns:
        Clean plain text
    """
    if not text:
        return text

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove headers (##, ###, etc.)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold and italic (keep the text)
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # Bold+italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)      # Bold
    text = re.sub(r'__(.+?)__', r'\1', text)          # Bold (underscore)
    text = re.sub(r'\*(.+?)\*', r'\1', text)          # Italic
    text = re.sub(r'_(.+?)_', r'\1', text)            # Italic (underscore)

    # Remove links [text](url) - keep only text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove code blocks
    text = re.sub(r'```[^\n]*\n(.+?)\n```', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Inline code

    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    # Remove bullet points (keep the content)
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)

    # Remove extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text


class Hypothesis(BaseModel):
    """Single hypothesis for improving drug response."""
    rank: int = Field(ge=1, description="Priority ranking")
    title: str = Field(max_length=100, description="Concise hypothesis statement")
    rationale: str = Field(description="Mechanistic explanation")
    evidence: List[str] = Field(description="Supporting citations")
    confidence: str = Field(description="Confidence level: high, moderate, or low")
    implementation: str = Field(description="How to implement clinically")


class HypothesesOutput(BaseModel):
    """Collection of hypotheses."""
    hypotheses: List[Hypothesis] = Field(max_items=3, description="2-3 ranked hypotheses")


class HypothesisGeneratorAgent:
    """
    Agent responsible for generating actionable hypotheses.

    Uses ONLY Gemini 2.5 Flash with:
    - Google Search grounding for latest guidelines
    - Structured output for consistent formatting
    """

    def __init__(self, google_api_key: str):
        """Initialize generator."""
        self.gemini = GeminiService(api_key=google_api_key)

    async def run(self, state: AgentState) -> AgentState:
        """
        Execute hypothesis generation.

        Args:
            state: Current agent state with normalized data and genetic variants

        Returns:
            Updated state with hypotheses
        """
        logger.info(f"Hypothesis Generator (Gemini-only): Generating strategies for {state.drug}")

        state.current_agent = "hypothesis_generator"

        try:
            # Get recent evidence with grounding
            recent_evidence = None
            if self.gemini.is_available():
                try:
                    recent_evidence = await self._get_recent_evidence(state.drug, state.indication)
                except Exception as e:
                    logger.warning(f"Gemini evidence search failed: {e}")

            # Generate hypotheses
            hypotheses = await self._generate_hypotheses_gemini(
                drug=state.drug,
                indication=state.indication,
                non_response_rate=state.pooled_metrics,
                variants=state.variants,
                mechanisms=state.mechanisms,
                studies=state.normalized_data,
                recent_evidence=recent_evidence
            )

            state.hypotheses = hypotheses

            logger.info(f"Hypothesis Generator: Generated {len(hypotheses)} hypotheses")

        except Exception as e:
            logger.error(f"Hypothesis generation failed: {e}")
            state.errors.append(f"Hypothesis generation error: {str(e)}")

        return state

    async def _get_recent_evidence(self, drug: str, indication: str) -> Dict[str, Any]:
        """
        Use Gemini with grounding to find latest clinical evidence.

        Args:
            drug: Drug name
            indication: Disease/condition

        Returns:
            Recent evidence with citations
        """
        prompt = f"""Find the latest SPECIFIC clinical data and actionable protocols (2020-2025) for:
- Drug: {drug}
- Indication: {indication or 'all indications'}

Provide CONCRETE, DATA-DRIVEN information (NOT "consult a professional"):

1. **Alternative Drugs for Non-Responders**:
   - Specific drug names and doses
   - Mechanism differences
   - Clinical trial data with response rates

2. **Genotype-Guided Dosing**:
   - EXACT genotypes (e.g., CYP2C19 *2/*2, *1/*2, etc.)
   - SPECIFIC dose recommendations (mg) for each genotype
   - Loading vs maintenance doses
   - CPIC guideline level recommendations

3. **FDA/EMA Pharmacogenomics Labels**:
   - Specific label text for genetic testing
   - Black box warnings
   - Dosing algorithms

4. **Clinical Protocols**:
   - Step-by-step treatment algorithms
   - When to switch medications
   - Monitoring parameters

Provide NUMBERS, DOSES, GENOTYPES, and SPECIFIC PROTOCOLS. Do NOT just say "consult guidelines" - give the actual guideline recommendations."""

        result = await self.gemini.generate_with_grounding(
            prompt=prompt,
            temperature=0.2,
            max_tokens=1500
        )

        return result

    async def _generate_hypotheses_gemini(
        self,
        drug: str,
        indication: str,
        non_response_rate: Dict[str, Any],
        variants: List[Dict[str, Any]],
        mechanisms: List[Dict[str, Any]],
        studies: List[Dict[str, Any]],
        recent_evidence: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Use Gemini with structured output to generate evidence-based hypotheses.

        Args:
            drug: Drug name
            indication: Disease/condition
            non_response_rate: Pooled non-response metrics
            variants: Genetic variants
            mechanisms: PK/PD mechanisms
            studies: Normalized study data
            recent_evidence: Recent evidence from grounding

        Returns:
            List of ranked hypotheses
        """
        # Prepare context
        overall_rate = non_response_rate.get("overall", {}).get("rate")
        overall_n = non_response_rate.get("overall", {}).get("n", 0)
        subgroups = non_response_rate.get("by_subgroup", {})

        context = f"""# Drug Non-Response Analysis: {drug}

## Indication
{indication or "Not specified"}

## Non-Response Rate
"""

        # Handle case when no valid data was extracted
        if overall_rate is not None:
            context += f"Overall: {overall_rate*100:.1f}% ({overall_n:,} patients)\n"
        else:
            context += "Overall: No sufficient clinical data available from literature\n"
            context += f"Note: Analyzed {len(studies)} studies but could not extract valid response rates\n"

        if subgroups:
            context += "\n### Subgroups:\n"
            for name, metrics in subgroups.items():
                rate = metrics.get('rate')
                if rate is not None:
                    context += f"- {name}: {rate*100:.1f}% (n={metrics['n']})\n"

        if variants:
            context += "\n## Genetic Variants\n"
            for variant in variants[:10]:
                gene = variant.get("gene", "")
                rs_id = variant.get("rs_id", "")
                effect = variant.get("effect", "")
                context += f"- {rs_id} ({gene}): {effect}\n"

        if mechanisms:
            context += "\n## Mechanisms\n"
            for mech in mechanisms[:5]:
                context += f"- {mech['gene']} ({mech['type']}): {mech.get('description', '')}\n"

        context += f"\n## Evidence Base\n{len(studies)} clinical studies analyzed\n"

        if recent_evidence:
            context += f"\n## Recent Clinical Evidence (2023-2025)\n{recent_evidence.get('text', '')}\n"

            citations = recent_evidence.get("citations") or []
            if citations and isinstance(citations, list):
                for citation in citations:
                    if citation and isinstance(citation, dict):
                        context += f"- {citation.get('title', 'Source')}: {citation.get('url', '')}\n"

        # Generate hypotheses with structured output
        prompt = f"""{context}

You are a clinical pharmacologist and pharmacogenomics expert conducting RESEARCH. Based on the non-response data and genetic mechanisms above, propose 2-3 CONCRETE, DATA-DRIVEN strategies to improve outcomes for non-responders.

CRITICAL: Provide SPECIFIC clinical data (doses, genotypes, protocols) - NOT vague recommendations like "consult a professional" or "refer to clinic". This is for RESEARCH purposes.

For each hypothesis, provide SPECIFIC, ACTIONABLE information:

1. **Alternative Drugs**:
   - EXACT drug names and doses (e.g., "Prasugrel 10mg daily" or "Ticagrelor 90mg BID")
   - Specific response rate improvements (%)
   - Trial names and PMID references

2. **Genotype-Guided Dosing**:
   - EXACT genotypes (e.g., CYP2C19 *1/*2, *2/*2, *17/*17)
   - SPECIFIC dose for each genotype (e.g., "Poor metabolizers: 600mg loading, 150mg maintenance")
   - CPIC guideline level (e.g., "Level A recommendation")

3. **Treatment Protocols**:
   - Step-by-step algorithm with decision points
   - When to escalate/switch (specific criteria)
   - Monitoring frequency and parameters

For EACH hypothesis provide:
- rank: 1, 2, or 3
- title: Specific action (e.g., "Switch CYP2C19 poor metabolizers to prasugrel 10mg")
- rationale: Mechanistic explanation with DATA (include percentages, effect sizes)
- evidence: Specific trials, CPIC guidelines, FDA labels (NOT just "consult guidelines")
- confidence: high/moderate/low based on evidence strength
- implementation: SPECIFIC protocol (doses, genotypes, monitoring) - NOT "refer to specialist"

Use the recent evidence provided to get REAL clinical data and specific recommendations."""

        try:
            if not self.gemini.is_available():
                raise RuntimeError("Gemini service not available")

            # Generate hypotheses using Gemini with grounding for REAL data
            result = await self.gemini.generate_with_grounding(
                prompt=prompt,
                temperature=0.3,
                max_tokens=3000
            )

            # Parse the response (Gemini will return text with grounding)
            response_text = result.get("text", "").strip()
            citations = result.get("citations", [])

            # Check if response is empty or too short
            if not response_text or len(response_text) < 100:
                logger.error(f"Gemini returned insufficient text: {len(response_text)} chars")
                raise RuntimeError(
                    f"Gemini returned empty or minimal response ({len(response_text)} chars). "
                    f"This may be due to: (1) API rate limits, (2) Content filtering, "
                    f"(3) Grounding issues. Check API quota and retry."
                )

            # Parse hypotheses from Gemini's response
            # Look for numbered sections (1., 2., 3. or ##, ###)
            import re

            hypotheses = []

            # Split by common delimiters for hypotheses
            # Try different patterns to extract structured hypotheses
            sections = re.split(r'(?:^|\n)(?:#{1,3}\s*)?(?:Hypothesis\s*)?(\d+)[.:\)]?\s*', response_text, flags=re.MULTILINE)

            if len(sections) > 1:
                # We found numbered sections
                for i in range(1, len(sections), 2):
                    if i + 1 < len(sections):
                        rank = int(sections[i])
                        content = sections[i + 1].strip()

                        # Extract title (usually first line or bolded text)
                        title_match = re.search(r'\*\*(.+?)\*\*|^(.+?)(?:\n|$)', content)
                        title = title_match.group(1) or title_match.group(2) if title_match else f"Strategy {rank}"
                        title = clean_markdown(title)[:100].strip()  # Clean and limit length

                        # Extract implementation (look for "Implementation:" section)
                        impl_match = re.search(r'Implementation:?\s*(.+?)(?=\n\n|\n[A-Z]|Evidence:|$)', content, re.DOTALL | re.IGNORECASE)
                        implementation = clean_markdown(impl_match.group(1).strip() if impl_match else content[:200])

                        # Extract confidence
                        conf_match = re.search(r'Confidence:?\s*(high|moderate|low)', content, re.IGNORECASE)
                        confidence = conf_match.group(1).lower() if conf_match else "moderate"

                        # Extract evidence (look for trials, guidelines, PMIDs)
                        evidence = []
                        evidence_match = re.search(r'Evidence:?\s*(.+?)(?=\n\n|\nImplementation:|$)', content, re.DOTALL | re.IGNORECASE)
                        if evidence_match:
                            ev_text = evidence_match.group(1)
                            # Extract bullet points or citations and clean markdown
                            evidence = [clean_markdown(e.strip('- ').strip()) for e in ev_text.split('\n') if e.strip()]

                        # Add citations from grounding (safely handle None)
                        if citations and isinstance(citations, list):
                            for citation in citations[:2]:
                                if citation and isinstance(citation, dict):
                                    evidence.append(f"{citation.get('title', 'Source')}: {citation.get('url', '')}")

                        hypotheses.append({
                            "rank": rank,
                            "title": title,
                            "rationale": clean_markdown(content[:500].strip()),  # Clean markdown from rationale
                            "evidence": evidence[:5] if evidence else ["Based on pharmacogenomics literature"],
                            "confidence": confidence,
                            "implementation": implementation[:300]
                        })

            # If parsing failed but we have Gemini's response, use it directly (NOT hardcoded data)
            if not hypotheses and response_text:
                logger.warning(f"Regex parsing failed for {len(response_text)} chars. Using raw Gemini output.")
                logger.debug(f"Response preview: {response_text[:500]}")
                
                # Try simpler parsing - split by double newlines or headers
                paragraphs = [p.strip() for p in response_text.split('\n\n') if len(p.strip()) > 100]
                
                if paragraphs:
                    for i, paragraph in enumerate(paragraphs[:3], 1):
                        # Extract title from first line
                        lines = paragraph.split('\n')
                        title = clean_markdown(lines[0].strip('*# ').strip())[:100]

                        # Use REAL Gemini output (with grounding), not fake data
                        # Safely extract citations (handle None)
                        evidence_list = []
                        if citations and isinstance(citations, list):
                            evidence_list = [f"{c.get('title', 'Source')}: {c.get('url', '')}" for c in citations[:3] if c and isinstance(c, dict)]
                        if not evidence_list:
                            evidence_list = ["Based on clinical literature"]

                        hypotheses.append({
                            "rank": i,
                            "title": title or f"Evidence-based strategy {i}",
                            "rationale": clean_markdown(paragraph[:500]),
                            "evidence": evidence_list,
                            "confidence": "moderate",
                            "implementation": clean_markdown(lines[-1][:300] if len(lines) > 1 else paragraph[:300])
                        })
                else:
                    # Last resort: use single hypothesis with all content
                    # Safely extract citations (handle None)
                    evidence_list = []
                    if citations and isinstance(citations, list):
                        evidence_list = [f"{c.get('title', 'Source')}: {c.get('url', '')}" for c in citations[:3] if c and isinstance(c, dict)]
                    if not evidence_list:
                        evidence_list = ["Based on clinical literature"]

                    hypotheses.append({
                        "rank": 1,
                        "title": "Clinical evidence-based recommendation from Gemini",
                        "rationale": clean_markdown(response_text[:500]),
                        "evidence": evidence_list,
                        "confidence": "moderate",
                        "implementation": clean_markdown(response_text[500:800] if len(response_text) > 500 else response_text[:300])
                    })
                    logger.warning("Used fallback single-hypothesis format")

            # If no hypotheses generated at all, raise error (don't return empty list)
            if not hypotheses:
                error_msg = (
                    f"Gemini returned text but no parseable hypotheses. "
                    f"Response length: {len(response_text)} chars. "
                    f"Check if grounding is working correctly or if response format changed."
                )
                logger.error(error_msg)
                logger.debug(f"Full response: {response_text}")
                raise RuntimeError(error_msg)

            logger.info(f"Successfully generated {len(hypotheses)} hypotheses")
            return hypotheses[:3]

        except Exception as e:
            logger.error(f"Failed to generate hypotheses from Gemini: {e}")
            # NO FALLBACK - Raise error to show real failure
            raise RuntimeError(f"Hypothesis generation failed - Gemini API error: {str(e)}. No hardcoded fallback data available.")
