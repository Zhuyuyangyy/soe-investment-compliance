# SOE Investment Compliance

> State-Owned Enterprise Investment Compliance Review System - Automated compliance auditing and responsibility chain risk tracking for SOE investment activities.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Tests](https://img.shields.io/badge/Tests-90+-brightgreen.svg)
![Coverage](https://img.shields.io/badge/Coverage-80%25+-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![CI/CD](https://img.shields.io/badge/CI/CD-GitHub%20Actions-purple.svg)

---

## Overview

SOE Investment Compliance is purpose-built for the regulatory oversight of state-owned enterprise (SOE) investment activities in China. It automates the verification of "Three-Major-Decisions" (三重一大) procedures, validates consistency across contracts, payments, and acceptance records, builds responsibility chain graphs for accountability tracing, and computes multi-dimensional risk entropy scores for early warning.

---

## Key Features

- **Project Document Parsing** -- Automated extraction of key fields from project proposals, feasibility studies, meeting minutes, contracts, payment records, and acceptance documents
- **Three-Major-Decisions Validation** -- Verifies that major decisions have complete decision records with proper approval chains
- **Triple-Document Matching** -- Cross-validates contract amounts, payment amounts, and acceptance amounts for consistency
- **Responsibility Chain Graph** -- Constructs a relationship graph mapping decision makers, approvers, executors, and suppliers
- **Investment Risk Entropy Scoring** -- Four-dimensional risk model (process, capital, association, responsibility) with multi-factor coupling
- **Remediation Closure Reports** -- Generates issue checklists, responsibility node tracing, and remediation plans
- **Audit Trail** -- Complete operational logging for regulatory inspection and SASAC reporting

---

## Quick Start

### Prerequisites

- Python 3.12+
- Docker (optional)

### Local Development

```bash
# Clone and setup
git clone <repository-url>
cd soe-investment-compliance
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Run backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8017 --reload

# Open frontend
open frontend/index.html
```

### Docker

```bash
docker-compose up -d
```

API server: `http://localhost:8017` | Interactive docs: `http://localhost:8017/docs`

---

## Architecture

```
Document Upload -> Parsing -> Three-Major-Decisions Check -> Triple-Document Match
    -> Responsibility Chain -> Risk Entropy Scoring -> Compliance Report
```

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, uvicorn |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Validation | Pydantic v2 |
| Frontend | Vue 3, ECharts 5 |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/register_project` | Register a new investment project |
| `POST` | `/api/upload_document` | Upload project documents |
| `POST` | `/api/register_contract` | Register a contract record |
| `POST` | `/api/register_payment` | Register a payment record |
| `POST` | `/api/register_acceptance` | Register an acceptance record |
| `POST` | `/api/check_triple_match` | Run triple-document matching |
| `POST` | `/api/build_responsibility_chain` | Construct responsibility chain graph |
| `POST` | `/api/analyze_project` | Run full compliance analysis |
| `GET` | `/api/get_project/{id}` | Retrieve project information |
| `GET` | `/api/get_risk_report/{id}` | Retrieve risk assessment report |
| `GET` | `/api/audit_logs` | Query audit logs |
| `GET` | `/api/list_projects` | List all registered projects |

Full OpenAPI documentation available at `/docs` when the server is running.

---

## Project Structure

```
soe-investment-compliance/
├── backend/
│   ├── app/
│   │   ├── main.py                          # FastAPI application entry
│   │   ├── api/routes.py                    # API endpoints
│   │   ├── core/database.py                 # Database setup
│   │   ├── models/schemas.py                # Pydantic data models
│   │   ├── services/                        # Business logic services
│   │   └── rules/soe_investment_rules.json  # Rule library
│   └── requirements.txt
├── frontend/
│   └── index.html                           # Vue 3 + ECharts 5 frontend
├── tests/                                   # Comprehensive test suite (90+ tests)
│   ├── conftest.py                          # Shared fixtures
│   ├── test_project_parser.py               # Document parsing tests
│   ├── test_decision_checker.py             # Three-Major-Decisions tests
│   ├── test_triple_match_checker.py         # Triple-document matching tests
│   ├── test_responsibility_chain.py         # Responsibility chain tests
│   ├── test_investment_risk_scorer.py       # Risk scoring tests
│   ├── test_report_generator.py             # Report generation tests
│   └── test_routes.py                       # API integration tests
├── docs/                                    # Documentation
│   ├── ARCHITECTURE.md                      # System architecture
│   ├── DEPLOYMENT.md                        # Deployment guide
│   └── COMPLIANCE_RULES.md                  # Rules reference
├── .github/workflows/ci.yml                # CI/CD pipeline
├── Dockerfile                               # Multi-stage Docker build
├── docker-compose.yml                       # Docker Compose orchestration
├── nginx.conf                               # Nginx reverse proxy config
├── TODO.md                                  # Innovation roadmap
├── INNOVATION_ROADMAP.md                    # Patent portfolio
├── OPTIMIZATION_REPORT.md                   # Project optimization report
├── requirements.txt                         # Production dependencies
├── requirements-dev.txt                     # Development dependencies
└── .gitignore
```

---

## Risk Scoring Model

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Process Risk | 30% | Decision procedure completeness, approval chain validity |
| Capital Risk | 35% | Triple-document matching, fund usage compliance |
| Association Risk | 20% | Related-party transactions, conflict of interest indicators |
| Responsibility Risk | 15% | Responsibility chain completeness, traceability gaps |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend --cov-report=term-missing

# Run specific test file
pytest tests/test_decision_checker.py -v
```

---

## Innovation & Patents

| # | Patent Title | Core Innovation |
|---|-------------|-----------------|
| 1 | Responsibility Chain Graph-Based SOE Investment Risk Tracking | Graph-based accountability tracing |
| 2 | Three-Major-Decisions Process Compliance Closure Verification | Closed-loop procedure validation |
| 3 | Multi-Source Document Consistency Detection | Three-way cross-document reconciliation |
| 4 | Investment Decision Anomaly Early Warning via Risk Entropy | Information entropy risk model |

See [INNOVATION_ROADMAP.md](INNOVATION_ROADMAP.md) for the full patent portfolio and innovation pipeline.

---

## Contributing

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for development setup.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest tests/ -v`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## License

This project is licensed under the MIT License.

---

## Disclaimer

This system provides automated compliance analysis for reference purposes only. It does not constitute legal or financial advice. SOE investment decisions should be validated against applicable SASAC regulations and internal governance policies.

---

## Contact

For technical inquiries, collaboration proposals, or patent licensing:

- **Project Lead**: ZYY Project Team
- **Issues**: Please use GitHub Issues for bug reports and feature requests
