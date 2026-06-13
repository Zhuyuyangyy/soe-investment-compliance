# System Architecture

## Overview

SOE Investment Compliance is a full-stack application built with a layered architecture pattern, separating concerns between API routing, business logic services, data persistence, and frontend presentation.

## Architectural Layers

```
+--------------------------------------------------+
|  Frontend (Vue 3 + ECharts 5)                    |
|  Single-page application                         |
|  - Dashboard, Project Mgmt, Risk Radar           |
|  - Responsibility Chain Visualization            |
+--------------------------------------------------+
            |  HTTP / REST API
            v
+--------------------------------------------------+
|  API Layer (FastAPI Router)                       |
|  routes.py                                       |
|  - Request validation (Pydantic)                 |
|  - Authentication / Authorization                |
|  - Audit logging                                 |
+--------------------------------------------------+
            |
            v
+--------------------------------------------------+
|  Service Layer                                    |
|  - project_parser.py      Document parsing       |
|  - decision_checker.py    Three-Major-Decisions   |
|  - triple_match_checker.py  Triple-document match |
|  - responsibility_chain.py  Graph construction    |
|  - investment_risk_scorer.py  Risk entropy model  |
|  - report_generator.py    Report generation       |
+--------------------------------------------------+
            |
            v
+--------------------------------------------------+
|  Data Layer                                       |
|  - database.py (SQLite + raw SQL)                |
|  - schemas.py (Pydantic models)                  |
|  - soe_investment_rules.json (Rule library)       |
+--------------------------------------------------+
```

## Data Flow

### 1. Project Registration Flow
```
User -> POST /api/register_project -> routes.py -> database.py (INSERT projects)
                                                -> audit_logs (INSERT)
```

### 2. Document Upload Flow
```
User -> POST /api/upload_document -> routes.py -> database.py (INSERT documents)
                                              -> project_parser.py (extract fields)
                                              -> Return extracted_fields + issues
```

### 3. Full Analysis Flow
```
User -> POST /api/analyze_project -> routes.py
    -> database.py (fetch project, docs, contracts, payments, acceptances)
    -> project_parser.py (parse all documents)
    -> decision_checker.py (three-major-decisions validation)
    -> triple_match_checker.py (contract/payment/acceptance matching)
    -> responsibility_chain.py (build accountability graph)
    -> investment_risk_scorer.py (calculate four-dimensional risk entropy)
    -> report_generator.py (generate rectification report)
    -> database.py (INSERT analysis_results)
    -> Return comprehensive analysis result
```

## Key Design Decisions

### 1. SQLite for Simplicity
The system uses SQLite for zero-configuration deployment. For production with multiple concurrent users, migrate to PostgreSQL by changing `database.py`.

### 2. Rule-Based Engine
Compliance rules are stored in `soe_investment_rules.json` and the `rules` database table, enabling runtime rule updates without code changes.

### 3. Graph-Based Responsibility Chain
The responsibility chain is modeled as a directed graph (nodes = entities, edges = relationships), enabling path analysis for accountability tracing.

### 4. Risk Entropy Model
The four-dimensional risk model uses weighted sum with configurable weights:
- Process Risk (30%): Decision procedure completeness
- Capital Risk (35%): Financial consistency
- Association Risk (20%): Related-party detection
- Responsibility Risk (15%): Accountability chain completeness

## Component Diagram

```
                    +-------------------+
                    |    FastAPI App    |
                    |    (main.py)      |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
        +-----+-----+ +-----+-----+ +-----+-----+
        |   routes   | |  schemas  | |  database  |
        +-----+------+ +-----------+ +-----+------+
              |
    +---------+---------+---------+---------+---------+
    |         |         |         |         |         |
+---+---+ +---+---+ +---+---+ +---+---+ +---+---+ +---+---+
| parser| |checker| | match | | chain | | scorer| |report |
+-------+ +-------+ +-------+ +-------+ +-------+ +-------+
```

## Database Schema (ER Diagram)

```
projects (1) ----< (N) documents
projects (1) ----< (N) contracts
projects (1) ----< (N) payments
projects (1) ----< (N) acceptance
projects (1) ----< (N) responsibility_chain
projects (1) ----< (N) analysis_results
rules (standalone)
audit_logs (standalone)
```

## Security Considerations

- CORS is configured to allow all origins in development; restrict in production
- No authentication layer currently; add JWT/OAuth for production
- Audit logs capture all write operations for regulatory compliance
- SQL injection prevented by parameterized queries throughout
