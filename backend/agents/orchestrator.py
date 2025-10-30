"""
Orchestrator Agent - Coordinates the multi-agent workflow.
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from models.schemas import AgentState
from agents.literature_miner import LiteratureMinerAgent
from agents.evidence_normalizer import EvidenceNormalizerAgent
from agents.genetics_analyst import GeneticsAnalystAgent
from agents.hypothesis_generator import HypothesisGeneratorAgent
from services.drugbank_service import DrugBankService
import logging

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Orchestrator that manages the workflow and agent handoffs.

    Uses LangGraph's swarm pattern where agents dynamically hand off
    control based on data availability and task completion.
    """

    def __init__(self, google_api_key: str):
        """
        Initialize orchestrator with all specialized agents.

        GEMINI-ONLY VERSION - No Anthropic/Claude dependencies.

        Args:
            google_api_key: Google API key for Gemini 2.5 Flash (REQUIRED)
        """
        self.google_api_key = google_api_key

        # Initialize specialized agents (all use Gemini only)
        self.literature_miner = LiteratureMinerAgent(google_api_key)
        self.evidence_normalizer = EvidenceNormalizerAgent()  # Pure statistics, no LLM
        self.genetics_analyst = GeneticsAnalystAgent(google_api_key)
        self.hypothesis_generator = HypothesisGeneratorAgent(google_api_key)

        # Initialize DrugBank service for comprehensive drug data
        try:
            self.drugbank = DrugBankService()
            logger.info("DrugBank service initialized successfully")
        except FileNotFoundError as e:
            logger.warning(f"DrugBank database not available: {e}")
            self.drugbank = None

        # Build the agent graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine.

        Flow:
        1. Start → Literature Miner (parallel with Genetics Analyst)
        2. Literature Miner → Evidence Normalizer
        3. Genetics Analyst → Evidence Normalizer (waits for both)
        4. Evidence Normalizer → Hypothesis Generator
        5. Hypothesis Generator → End
        """
        workflow = StateGraph(AgentState)

        # Add nodes (agents)
        workflow.add_node("literature_miner", self.literature_miner.run)
        workflow.add_node("genetics_analyst", self.genetics_analyst.run)
        workflow.add_node("evidence_normalizer", self.evidence_normalizer.run)
        workflow.add_node("hypothesis_generator", self.hypothesis_generator.run)

        # Set entry point
        workflow.set_entry_point("literature_miner")

        # Define edges (handoffs)
        workflow.add_edge("literature_miner", "genetics_analyst")
        workflow.add_edge("genetics_analyst", "evidence_normalizer")
        workflow.add_edge("evidence_normalizer", "hypothesis_generator")
        workflow.add_edge("hypothesis_generator", END)

        return workflow.compile()

    async def analyze_drug(
        self,
        drug: str,
        indication: str = None,
        population: str = "all"
    ) -> Dict[str, Any]:
        """
        Run complete drug non-response analysis.

        Args:
            drug: Drug name
            indication: Disease/condition
            population: Target population

        Returns:
            Complete analysis results
        """
        logger.info(f"Starting analysis for drug: {drug}")

        # Initialize state
        initial_state = AgentState(
            drug=drug,
            indication=indication,
            population=population
        )

        try:
            # Execute the graph
            final_state = await self.graph.ainvoke(initial_state)

            # Format final output
            result = self._format_results(final_state)

            logger.info(f"Analysis complete for {drug}")
            return result

        except Exception as e:
            logger.error(f"Analysis failed for {drug}: {e}")
            raise

    async def analyze_drug_with_progress(
        self,
        drug: str,
        indication: str = None,
        population: str = "all",
        article_count: int = 5,
        clinical_trials_count: int = 5,
        progress_callback = None
    ) -> Dict[str, Any]:
        """
        Run drug analysis with real-time progress updates.

        Args:
            drug: Drug name
            indication: Disease/condition
            population: Target population
            article_count: Number of PubMed articles to process (1-20, default: 5)
            clinical_trials_count: Number of clinical trials to process (1-20, default: 5)
            progress_callback: Async callback function for progress updates

        Returns:
            Complete analysis results
        """
        logger.info(f"Starting analysis with progress tracking for drug: {drug}")

        # Send initial progress
        if progress_callback:
            await progress_callback({
                "type": "progress",
                "step": "starting",
                "message": f"Starting analysis for {drug}",
                "progress": 0
            })

        # Initialize state
        initial_state = AgentState(
            drug=drug,
            indication=indication,
            population=population
        )

        try:
            # Step 0: Fetch DrugBank data (fast, local database)
            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "step": "fetching_drugbank",
                    "message": "Fetching comprehensive drug data from DrugBank...",
                    "progress": 3
                })

            if self.drugbank:
                try:
                    drugbank_data = self.drugbank.get_drug_by_name(drug)
                    if drugbank_data:
                        initial_state.drugbank_data = drugbank_data
                        logger.info(f"Fetched comprehensive DrugBank data for {drug}")
                    else:
                        logger.warning(f"No DrugBank data found for {drug}")
                except Exception as e:
                    logger.error(f"Failed to fetch DrugBank data: {e}")

            # Step 1: Literature Mining
            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "step": "literature_mining",
                    "message": "Searching PubMed, Clinical Trials, and PharmGKB databases...",
                    "progress": 10
                })

            state = await self.literature_miner.run(initial_state, progress_callback, article_count, clinical_trials_count)

            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "step": "literature_complete",
                    "message": f"Found {len(state.pubmed_studies)} PubMed studies and {len(state.clinical_trials)} clinical trials",
                    "progress": 35
                })

            # Step 2: Genetics Analysis
            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "step": "genetics_analysis",
                    "message": "Analyzing genetic variants from GWAS Catalog...",
                    "progress": 40
                })

            state = await self.genetics_analyst.run(state)

            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "step": "genetics_complete",
                    "message": f"Identified {len(state.variants)} genetic variants with PK/PD mechanisms",
                    "progress": 60
                })

            # Step 3: Evidence Normalization
            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "step": "normalizing",
                    "message": "Computing pooled metrics with meta-analysis...",
                    "progress": 70
                })

            state = await self.evidence_normalizer.run(state)

            if progress_callback:
                overall_rate = state.pooled_metrics.get("overall", {}).get("rate")
                if overall_rate is not None:
                    msg = f"Non-response rate: {overall_rate*100:.1f}% across {len(state.normalized_data)} studies"
                else:
                    msg = "Metrics computed"
                await progress_callback({
                    "type": "progress",
                    "step": "normalization_complete",
                    "message": msg,
                    "progress": 80
                })

            # Step 4: Hypothesis Generation
            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "step": "generating_hypotheses",
                    "message": "Generating evidence-based recommendations with Gemini...",
                    "progress": 85
                })

            state = await self.hypothesis_generator.run(state)

            if progress_callback:
                await progress_callback({
                    "type": "progress",
                    "step": "hypotheses_complete",
                    "message": f"Generated {len(state.hypotheses)} clinical recommendations",
                    "progress": 95
                })

            # Format final results
            result = self._format_results(state)

            logger.info(f"Analysis complete for {drug}")
            return result

        except Exception as e:
            logger.error(f"Analysis with progress failed for {drug}: {e}")
            raise

    def _format_results(self, state: AgentState) -> Dict[str, Any]:
        """
        Format the final state into structured output.

        Args:
            state: Final agent state

        Returns:
            Formatted analysis results
        """
        return {
            "drug": state.drug,
            "indication": state.indication,
            "population": state.population,
            "non_response_rate": state.pooled_metrics,
            "variants": state.variants,
            "hypotheses": state.hypotheses,
            "drugbank_data": state.drugbank_data,  # Include comprehensive DrugBank data
            "metadata": {
                "studies_analyzed": len(state.pubmed_studies) + len(state.clinical_trials),
                "total_patients": self._calculate_total_patients(state),
                "data_quality": self._assess_quality(state),
                "warnings": state.errors
            },
            "citations": list(set(state.citations))
        }

    def _calculate_total_patients(self, state: AgentState) -> int:
        """Calculate total patients across all studies."""
        total = 0

        for study in state.normalized_data:
            total += study.get("sample_size", 0)

        return total

    def _assess_quality(self, state: AgentState) -> str:
        """Assess overall data quality."""
        n_studies = len(state.pubmed_studies) + len(state.clinical_trials)
        total_patients = self._calculate_total_patients(state)

        if n_studies >= 10 and total_patients >= 1000:
            return "high"
        elif n_studies >= 5 and total_patients >= 500:
            return "moderate"
        elif n_studies >= 2 and total_patients >= 100:
            return "low"
        else:
            return "insufficient"

    async def close(self):
        """Clean up resources."""
        await self.literature_miner.close()
        await self.genetics_analyst.close()
