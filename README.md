# Pharmacogenomics Drug Non-Response Analysis Platform

A comprehensive AI-powered platform for analyzing drug non-response rates using pharmacogenomics data, GWAS analysis, and multi-agent AI orchestration. This system helps researchers and clinicians understand why certain medications fail to work for specific patient populations by analyzing genetic variants, biomarker correlations, and existing literature.

## Overview

Drug non-response is a significant challenge in modern medicine, with many patients failing to respond to first-line treatments due to genetic variations affecting drug metabolism, receptor binding, or transport mechanisms. This platform leverages advanced AI agents, real-world genomic databases, and clinical trial data to provide evidence-based insights into drug efficacy variations across different genetic backgrounds.

The system employs a multi-agent architecture powered by Google's Gemini 2.5 Flash model, orchestrating specialized agents that handle different aspects of the analysis pipeline including literature mining, genetic analysis, hypothesis generation, and evidence normalization.

## Key Features

### Drug Analysis Pipeline
- Comprehensive drug information retrieval from DrugBank database
- Real-time GWAS catalog integration for genetic variant analysis
- PubMed literature mining with citation tracking
- PharmGKB pharmacogenomic annotations and clinical guidelines
- ClinicalTrials.gov integration for active trial discovery

### AI-Powered Analysis
- Multi-agent orchestration using LangGraph for complex reasoning workflows
- Literature mining agent for extracting relevant research findings
- Genetics analyst agent for variant-drug association analysis
- Hypothesis generation agent for proposing mechanisms of non-response
- Evidence normalization agent for synthesizing findings across sources

### Interactive User Interface
- Real-time streaming analysis progress with Server-Sent Events
- Responsive Material-UI design with accessibility compliance (WCAG 2.1 AA)
- Drug autocomplete with intelligent fuzzy matching
- Interactive visualizations using Recharts
- Detailed breakdown of confidence levels and evidence quality

### Data Integration
- DrugBank XML parsing for comprehensive drug information
- GWAS Catalog API integration for genetic associations
- PubMed E-utilities for literature searches
- PharmGKB REST API for pharmacogenomic data
- Clinical trials data aggregation

## Architecture

### Backend Architecture

The backend follows a clean architecture pattern with clear separation of concerns:

```
backend/
├── api/           # FastAPI endpoints and HTTP layer
├── agents/        # Multi-agent AI orchestration system
├── services/      # External API integrations and data services
├── models/        # Pydantic schemas and data models
└── utils/         # Statistical analysis and helper functions
```

The agent system uses a directed graph structure (LangGraph) where each agent is a specialized node with defined inputs, outputs, and conditional edges. The orchestrator manages state transitions and coordinates information flow between agents.

### Frontend Architecture

The frontend is built with React 18 and TypeScript, following modern component composition patterns:

```
frontend/src/
├── components/    # Reusable UI components
├── services/      # API client and data fetching
├── hooks/         # Custom React hooks
├── types/         # TypeScript type definitions
└── theme.ts       # Material-UI theme configuration
```

State management uses React Query for server state and Zustand for client state, providing efficient caching and real-time updates.

## Technology Stack

### Backend Technologies
- **Framework**: FastAPI 0.109.0 - Modern async Python web framework
- **AI Engine**: Google Gemini 2.5 Flash via google-genai SDK
- **Agent Framework**: LangChain 0.1.20 and LangGraph 0.0.55
- **Data Processing**: Pandas 2.2.0, NumPy 1.26.3, SciPy 1.12.0
- **Bioinformatics**: Biopython 1.83, pandasgwas 0.1.0
- **Statistics**: scikit-learn 1.4.0, statsmodels 0.14.1
- **HTTP Clients**: httpx 0.26.0, aiohttp 3.9.3
- **Validation**: Pydantic 2.6.0

### Frontend Technologies
- **Framework**: React 18.2.0 with TypeScript 5.3.3
- **Build Tool**: Vite 5.1.0 for fast development and optimized builds
- **UI Library**: Material-UI 5.15.10 (MUI)
- **Animation**: Framer Motion 12.23.24 for smooth transitions
- **Data Fetching**: TanStack React Query 5.20.5
- **State Management**: Zustand 4.5.0
- **Charts**: Recharts 2.12.0 for data visualization
- **HTTP Client**: Axios 1.6.7

## Prerequisites

Before setting up the platform, ensure you have the following installed:

- **Python 3.10+**: Required for backend services
- **Node.js 18+**: Required for frontend development
- **npm or yarn**: Package manager for frontend dependencies
- **Google API Key**: Obtain from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **DrugBank XML File**: Download from [DrugBank](https://go.drugbank.com/releases/latest) (requires free academic account)

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd pharma-agent-system/backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:
```
GOOGLE_API_KEY=your_key_here
LOG_LEVEL=INFO
```

5. Place the DrugBank XML file:
```bash
# Download full database XML from DrugBank
# Place it at: pharma-agent-system/db/full_database.xml
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd pharma-agent-system/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure API endpoint (if needed):
The default configuration points to `http://localhost:8000`. To change this, update the API base URL in `frontend/src/services/api.ts`.

## Running the Application

### Development Mode

#### Option 1: Use the Automated Startup Script

From the project root directory:
```bash
chmod +x start.sh
./start.sh
```

This script handles:
- Virtual environment activation
- Backend startup on port 8000
- Frontend startup on port 3000
- Graceful shutdown of both services

#### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Production Deployment

#### Backend Production Build
```bash
cd backend
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend Production Build
```bash
cd frontend
npm run build
npm run preview  # Preview production build locally
```

The production build outputs to `frontend/dist/` which can be served by any static file server or CDN.

## Configuration

### Backend Configuration

The backend configuration is managed through environment variables in the `.env` file:

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |
| `CORS_ORIGINS` | Allowed CORS origins | No (default: localhost:3000) |
| `DRUGBANK_PATH` | Path to DrugBank XML file | No (default: ../db/full_database.xml) |

### Frontend Configuration

Frontend configuration can be modified in `frontend/src/services/api.ts`:

- **API_BASE_URL**: Backend API endpoint
- **Request timeout**: Default 300 seconds for long-running analyses
- **Retry logic**: Configurable retry attempts for failed requests

## Usage

### Basic Workflow

1. **Access the application**: Open your browser to `http://localhost:3000`

2. **Search for a drug**: Use the autocomplete search to find a drug by:
   - Generic name (e.g., "warfarin")
   - Brand name (e.g., "Coumadin")
   - Mechanism of action keywords

3. **Start analysis**: Click the "Analyze Drug" button to initiate the multi-agent analysis pipeline

4. **Monitor progress**: Watch real-time updates as each agent completes its analysis:
   - Fetching drug information
   - Mining literature
   - Analyzing genetic variants
   - Generating hypotheses
   - Normalizing evidence

5. **Review results**: Explore the comprehensive analysis including:
   - Non-response rate estimates with confidence intervals
   - Genetic variants associated with drug response
   - Biomarker correlations
   - Literature citations with grounding metadata
   - Proposed therapeutic alternatives
   - Active clinical trials

### Advanced Features

#### Filtering Results
Use the sidebar navigation to filter analyses by:
- Confidence level
- Evidence quality
- Genetic variant significance
- Publication date

#### Exporting Data
Results can be exported in multiple formats:
- JSON for programmatic access
- CSV for spreadsheet analysis
- PDF report generation (coming soon)

## API Documentation

### Endpoints

#### POST /analyze
Initiates a comprehensive drug analysis.

**Request Body:**
```json
{
  "drug_name": "warfarin",
  "include_gwas": true,
  "include_trials": true
}
```

**Response:** Server-Sent Events stream with progress updates

**Event Types:**
- `progress`: Analysis step completion
- `result`: Final analysis results
- `error`: Error information

#### POST /analyze-stream
Streaming version of the analysis endpoint with real-time progress updates.

#### POST /autocomplete
Provides drug name autocomplete suggestions.

**Request Body:**
```json
{
  "query": "war",
  "limit": 10
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "name": "Warfarin",
      "drugbank_id": "DB00682",
      "category": "Anticoagulant"
    }
  ]
}
```

#### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Project Structure

### Backend Structure
```
backend/
├── agents/
│   ├── orchestrator.py          # Main agent coordination
│   ├── literature_miner.py      # PubMed literature extraction
│   ├── genetics_analyst.py      # GWAS variant analysis
│   ├── hypothesis_generator.py  # Mechanism hypothesis generation
│   └── evidence_normalizer.py   # Cross-source evidence synthesis
├── api/
│   └── main.py                  # FastAPI application and routes
├── services/
│   ├── gemini_service.py        # Google Gemini AI client
│   ├── drugbank_service.py      # DrugBank XML parsing
│   ├── gwas_service.py          # GWAS Catalog integration
│   ├── pubmed_service.py        # PubMed E-utilities client
│   ├── pharmgkb_service.py      # PharmGKB API client
│   └── clinical_trials_service.py # ClinicalTrials.gov API
├── models/
│   └── schemas.py               # Pydantic data models
└── utils/
    └── stats.py                 # Statistical analysis functions
```

### Frontend Structure
```
frontend/src/
├── components/
│   ├── DrugSearch.tsx           # Drug search autocomplete component
│   ├── AnalysisProgress.tsx     # Real-time progress display
│   ├── ResultsDisplay.tsx       # Main results visualization
│   ├── DrugBankInfo.tsx         # DrugBank data display
│   ├── MetricCard.tsx           # Reusable metric card component
│   └── ConfidenceIndicator.tsx  # Confidence level visualization
├── services/
│   └── api.ts                   # API client with Axios
├── hooks/
│   └── useStreamingAnalysis.ts  # SSE streaming hook
├── types/
│   └── index.ts                 # TypeScript type definitions
└── theme.ts                     # Material-UI theme configuration
```

## Development

### Backend Development

#### Running Tests
```bash
cd backend
pytest tests/ -v
```

#### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .
```

#### Adding New Agents
To add a new agent to the analysis pipeline:

1. Create a new agent class in `backend/agents/`
2. Implement the `analyze()` method
3. Update the orchestrator graph in `orchestrator.py`
4. Add conditional edges for agent coordination

Example agent structure:
```python
class NewAgent:
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    async def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Agent logic here
        return updated_state
```

### Frontend Development

#### Development Server
The Vite development server provides:
- Hot Module Replacement (HMR)
- Fast refresh for React components
- TypeScript error reporting
- ESLint integration

#### Building Components
Follow the established patterns:
- Use TypeScript for type safety
- Implement Material-UI theming
- Add Framer Motion animations for transitions
- Ensure WCAG 2.1 AA accessibility compliance

#### Type Safety
All API responses are typed using TypeScript interfaces defined in `frontend/src/types/index.ts`. Update these types when modifying API responses.

## Data Sources and Attribution

This platform integrates data from several public databases and APIs:

- **DrugBank**: Comprehensive drug information database (Wishart DS, et al. Nucleic Acids Res. 2018)
- **GWAS Catalog**: NHGRI-EBI Catalog of human genome-wide association studies
- **PubMed**: National Library of Medicine literature database
- **PharmGKB**: Pharmacogenomics Knowledgebase (NIH/NIGMS)
- **ClinicalTrials.gov**: NIH clinical trials registry

Please cite these resources appropriately when using data from this platform in publications.

## Troubleshooting

### Common Issues

**Issue**: Backend fails to start with "GOOGLE_API_KEY not set"
- **Solution**: Verify your `.env` file contains a valid Google API key

**Issue**: DrugBank data not loading
- **Solution**: Ensure `full_database.xml` is present in the `db/` directory

**Issue**: Frontend cannot connect to backend
- **Solution**: Verify backend is running on port 8000 and CORS is configured correctly

**Issue**: GWAS analysis returns no results
- **Solution**: Check internet connectivity; GWAS Catalog API requires external network access

**Issue**: Frontend hot reload not working
- **Solution**: Try clearing Vite cache: `rm -rf node_modules/.vite`

## Performance Considerations

### Backend Optimization
- Agent execution uses async/await for concurrent API calls
- DrugBank XML is parsed once at startup and cached in memory
- GWAS queries are cached with 1-hour TTL
- Connection pooling for HTTP clients reduces latency

### Frontend Optimization
- Code splitting with Vite for faster initial load
- React Query caching reduces redundant API calls
- Virtualized lists for large result sets
- Debounced autocomplete to minimize API requests

## Security Considerations

- API keys are stored in environment variables, never committed to version control
- CORS is configured with specific allowed origins in production
- Input validation using Pydantic models prevents injection attacks
- Rate limiting should be implemented for production deployments
- DrugBank data usage must comply with their license terms

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the existing code style and conventions
4. Add tests for new functionality
5. Update documentation as needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style
- **Backend**: Follow PEP 8, use Black formatter, max line length 100
- **Frontend**: Follow Airbnb React/TypeScript style guide
- **Commits**: Use conventional commits format (feat:, fix:, docs:, etc.)

## License

This project is licensed under the MIT License. See the LICENSE file for details.

Note that while this software is MIT licensed, the integrated data sources (DrugBank, GWAS Catalog, etc.) have their own licenses and usage terms that must be respected.

## Acknowledgments

This platform was developed to advance pharmacogenomics research and improve precision medicine approaches. Special thanks to:

- Google for providing the Gemini API for AI-powered analysis
- The DrugBank team for maintaining comprehensive drug data
- NHGRI-EBI for the GWAS Catalog
- PharmGKB for pharmacogenomic annotations
- The open-source community for the excellent tools and libraries

## Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Check existing documentation and troubleshooting guides
- Review closed issues for similar problems

## Roadmap

Planned features and improvements:

- Integration with additional pharmacogenomic databases (ClinVar, ClinGen)
- Support for drug-drug interaction analysis
- Population-specific non-response estimates
- PDF report generation
- Multi-drug combination analysis
- Real-time collaboration features
- Mobile-responsive design improvements
- GraphQL API option
- Docker containerization for easy deployment

## Citation

If you use this platform in your research, please cite:

```
Pharmacogenomics Drug Non-Response Analysis Platform
https://github.com/[your-username]/pharma-agent-system
```

(Note: Update with actual repository URL after publishing)
