"""
FastAPI main application.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import logging
import asyncio
from datetime import datetime
import json
import uuid

from models.schemas import DrugQuery, DrugAnalysisResult, AutocompleteRequest, AutocompleteResult
from agents.orchestrator import OrchestratorAgent
from services.drugbank_service import DrugBankService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator: Optional[OrchestratorAgent] = None

# DrugBank service for drug data
drugbank_service: Optional[DrugBankService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI.

    Replaces deprecated @app.on_event("startup") and @app.on_event("shutdown").
    Code before yield runs on startup, code after yield runs on shutdown.
    """
    # STARTUP: Initialize services
    global orchestrator, drugbank_service

    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        raise RuntimeError(
            "GOOGLE_API_KEY not set in environment. "
            "Get your key from https://aistudio.google.com/app/apikey"
        )
    
    # Validate API key format
    if not google_key.startswith("AIzaSy"):
        logger.warning(
            f"GOOGLE_API_KEY format looks incorrect (should start with 'AIzaSy'). "
            f"Current key starts with: {google_key[:10]}..."
        )
    
    logger.info(f"Initializing with Google API key: {google_key[:10]}...{google_key[-4:]}")

    try:
        orchestrator = OrchestratorAgent(google_key)
        logger.info("✓ Orchestrator agent initialized successfully (GEMINI-ONLY)")
        
        # Test Gemini service availability
        from services.gemini_service import GeminiService
        gemini_test = GeminiService(api_key=google_key)
        if not gemini_test.is_available():
            logger.error("✗ Gemini service failed to initialize. Check API key validity.")
            raise RuntimeError("Gemini service not available. Verify your GOOGLE_API_KEY.")
        else:
            logger.info("✓ Gemini service validated successfully")
            
    except Exception as e:
        logger.error(f"✗ Failed to initialize orchestrator: {e}")
        raise RuntimeError(
            f"Service initialization failed: {str(e)}. "
            f"Please check your GOOGLE_API_KEY and network connection."
        )

    # Initialize DrugBank service for drug data
    try:
        drugbank_service = DrugBankService()
        # Quick test to ensure database is accessible
        test_count = len(drugbank_service.search_drugs("clopidogrel", limit=1))
        logger.info(f"✓ DrugBank database initialized successfully ({test_count > 0 and 'working' or 'empty'})")
    except Exception as e:
        logger.error(f"✗ Failed to initialize DrugBank service: {e}")
        logger.warning("  Drug autocomplete will be limited. Run drugbank_parser.py to build database.")
        drugbank_service = None
    
    logger.info("=" * 60)
    logger.info("🚀 Pharma Agent System is ready!")
    logger.info("=" * 60)

    yield  # Application runs here

    # SHUTDOWN: Cleanup resources
    logger.info("Shutting down services...")
    if orchestrator:
        # Note: OrchestratorAgent doesn't have a close method currently
        # Add cleanup here if needed in future
        logger.info("✓ Orchestrator agent closed")
    logger.info("👋 Shutdown complete")


# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="Pharmacogenomics Non-Response Analysis API",
    description="AI agent system for quantifying drug non-response and genetic drivers",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Hardcoded drug list REMOVED - Now using DrugBank database (17,430+ drugs)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Pharmacogenomics Non-Response Analysis API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/autocomplete", response_model=List[AutocompleteResult])
async def autocomplete_drug(request: AutocompleteRequest):
    """
    Autocomplete drug names using DrugBank database.

    Args:
        request: Query string and limit

    Returns:
        List of matching drugs from DrugBank (17,430+ drugs)
    """
    query = request.query.strip()

    if len(query) < 2:
        return []

    # Check if DrugBank service is available
    if drugbank_service is None:
        logger.warning("DrugBank service not available - autocomplete limited")
        return []

    try:
        # Search DrugBank database (searches both names and synonyms)
        results = drugbank_service.search_drugs(
            query=query,
            limit=request.limit,
            approved_only=True  # Only show approved drugs
        )

        # Convert to AutocompleteResult format
        matches = [
            AutocompleteResult(
                name=drug["name"],
                type="generic",  # DrugBank primary names are generic
                description=drug.get("description", "")
            )
            for drug in results
        ]

        logger.info(f"Autocomplete: '{query}' returned {len(matches)} results")
        return matches

    except Exception as e:
        logger.error(f"Autocomplete search failed: {e}")
        return []


@app.post("/api/analyze", response_model=DrugAnalysisResult)
async def analyze_drug(query: DrugQuery):
    """
    Analyze drug non-response with genetic insights.

    This is the main endpoint that orchestrates all agents.

    Args:
        query: Drug analysis query

    Returns:
        Complete analysis results

    Raises:
        HTTPException: If analysis fails
    """
    logger.info(f"Analysis request: {query.drug}, {query.indication}")

    try:
        result = await orchestrator.analyze_drug(
            drug=query.drug,
            indication=query.indication,
            population=query.population
        )

        # Convert to response model
        return DrugAnalysisResult(
            drug=result["drug"],
            indication=result.get("indication"),
            population=result["population"],
            non_response_rate=result["non_response_rate"],
            variants=result["variants"],
            hypotheses=result["hypotheses"],
            metadata=result["metadata"],
            citations=result.get("citations", [])
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-stream")
async def analyze_drug_stream(query: DrugQuery):
    """
    Analyze drug with real-time progress updates via Server-Sent Events (SSE).

    Returns a stream of progress updates as JSON objects:
    - type: "progress" | "complete" | "error"
    - step: current workflow step
    - message: human-readable status
    - progress: 0-100 percentage
    - result: final analysis (only on complete)
    """
    logger.info(f"SSE Analysis request: {query.drug}, {query.indication}")

    async def event_generator():
        progress_queue = asyncio.Queue()

        async def progress_callback(update: Dict[str, Any]):
            """Callback to receive progress updates from orchestrator."""
            await progress_queue.put(update)

        # Start analysis in background task
        async def run_analysis():
            try:
                result = await orchestrator.analyze_drug_with_progress(
                    drug=query.drug,
                    indication=query.indication,
                    population=query.population,
                    article_count=query.article_count,
                    clinical_trials_count=query.clinical_trials_count,
                    progress_callback=progress_callback
                )

                # Send completion with result
                await progress_queue.put({
                    "type": "complete",
                    "message": "Analysis complete",
                    "progress": 100,
                    "result": result
                })
            except Exception as e:
                logger.error(f"SSE Analysis failed: {e}", exc_info=True)
                await progress_queue.put({
                    "type": "error",
                    "message": str(e),
                    "progress": -1
                })

        # Start analysis task
        task = asyncio.create_task(run_analysis())

        try:
            while True:
                # Wait for next progress update
                update = await progress_queue.get()

                # Send update as SSE event
                yield f"data: {json.dumps(update)}\n\n"

                # Break if complete or error
                if update.get("type") in ["complete", "error"]:
                    break
        finally:
            # Cleanup
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "orchestrator": orchestrator is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
