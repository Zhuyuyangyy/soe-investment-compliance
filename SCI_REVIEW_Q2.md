# Q2-Level SCI Review: SOE Investment Compliance System

**Reviewer**: AI Code Review Agent  
**Date**: 2026-05-29  
**Repository**: soe-investment-compliance  
**Language**: Python (FastAPI) + Vue 3 Frontend  

---

## Executive Summary

This system implements an automated compliance checking platform for Chinese State-Owned Enterprise (SOE) investment activities, covering "Triple-Major-One-Large" (三重一大) decision validation, contract-payment-acceptance triple matching, responsibility chain graph construction, and multi-dimensional risk entropy scoring. The domain problem is well-chosen and practically relevant. However, the system suffers from critical runtime bugs, incomplete algorithm implementations, and lacks the formal rigor expected at the SCI publication level.

---

## 7-Dimension Scoring

| # | Dimension | Score (1-10) | Weight | Weighted |
|---|-----------|:---:|:---:|:---:|
| D1 | Novelty / Originality | 5 | 15% | 0.75 |
| D2 | Technical Rigor | 4 | 20% | 0.80 |
| D3 | Completeness | 6 | 15% | 0.90 |
| D4 | Scalability | 3 | 15% | 0.45 |
| D5 | Reproducibility | 5 | 10% | 0.50 |
| D6 | Code Quality / Documentation | 5 | 15% | 0.75 |
| D7 | Impact / Significance | 6 | 10% | 0.60 |
| | **Total** | | **100%** | **4.75 / 10** |

---

### D1: Novelty / Originality -- 5/10

**Strengths:**
- The "risk entropy" multi-dimensional coupling model (`investment_risk_scorer.py`) is a reasonable domain adaptation, combining process risk, capital risk, related-party risk, and responsibility risk with configurable weights.
- The responsibility chain graph builder (`responsibility_chain.py`) that automatically extracts signer/party/approver nodes from heterogeneous documents and constructs a knowledge graph is a useful contribution.
- The virtual document coordinate mapping in `project_parser.py` is an interesting design for traceability.

**Weaknesses:**
- The core algorithms (weighted sum, keyword matching, threshold-based classification) are elementary. No advanced NLP, graph neural network, or formal verification technique is employed.
- The "risk entropy" naming is misleading -- the system uses a weighted linear combination, not Shannon entropy or any entropy-based measure.
- The triple-match checking is essentially arithmetic comparison with hardcoded thresholds, not a novel matching algorithm.

**Recommendation**: Introduce a genuine information-theoretic or graph-theoretic formulation. If using "entropy," compute actual entropy over risk factor distributions.

---

### D2: Technical Rigor -- 4/10

**Critical Bug (FIXED):**
- `routes.py:64` -- `cur.to_dict(cur.fetchone())` crashes with `AttributeError` because `sqlite3.Cursor` has no `to_dict()` method. This is a showstopper: the `/register_project` endpoint fails on every invocation. **Fixed to `dict(cur.fetchone())`.**

**Algorithmic Issues:**
- `_check_invoice_consistency()` in `triple_match_checker.py` (line 268-270) contains a `pass` statement where actual duplicate-invoice detection logic should exist. This is a dead code path.
- `_check_timeline_consistency()` (line 229) contains a `pass` statement for acceptance-after-payment validation, leaving the check incomplete.
- `_calculate_related_risk()` (line 203) checks `if any(dept in parties for dept in [project_dept])` -- the `[project_dept]` wrapping is redundant and the substring match `dept in parties` is fragile (e.g., "部" would match "部分").
- The O(N*M) nested loop in `_check_amount_match()` for pairwise contract-payment comparison is correct but lacks normalization for multi-contract/multi-payment scenarios.
- `random.randint` / `random.uniform` in `get_compliance_score()` produces non-deterministic results for a compliance scoring endpoint -- completely unacceptable for audit purposes.

**Recommendation**: Replace `random` with actual database aggregation. Complete the two `pass` branches. Add unit tests for edge cases.

---

### D3: Completeness -- 6/10

**Covered:**
- Full pipeline: project registration -> document upload -> contract/payment/acceptance entry -> triple-match check -> responsibility chain build -> risk scoring -> report generation.
- 10 compliance rules in `soe_investment_rules.json` with severity levels.
- Frontend with 7 views: dashboard, project management, triple-match, chain graph, risk radar, report, audit log.
- Audit logging on all write operations.

**Missing:**
- No authentication or authorization system.
- No pagination on list endpoints (`/list_projects`, `/audit_logs`).
- No batch import/export capability.
- Rules in `soe_investment_rules.json` are loaded into DB at startup but never actually queried by any service -- the rule engine is disconnected from the rule store.
- No formal model validation (e.g., Pydantic response models are defined in `schemas.py` but most endpoints return raw dicts without `response_model`).
- `SQLAlchemy` is in `requirements.txt` but never imported -- raw `sqlite3` is used throughout.

**Recommendation**: Wire the rule store to the checkers. Add authentication. Remove unused dependencies.

---

### D4: Scalability -- 3/10

**Critical Bottlenecks:**
- Raw `sqlite3` with no connection pooling. Every request opens and closes a connection. SQLite also has write-lock limitations that prevent concurrent writes.
- `init_db()` is called at module import time in `routes.py` (line 24), coupling startup to schema creation.
- No async database operations despite using FastAPI (all DB calls are synchronous and block the event loop).
- No caching layer for repeated risk calculations.
- The frontend hardcodes `http://localhost:8017` as the API base.

**Recommendation**: Migrate to `SQLAlchemy` async with connection pooling, or at least use `aiosqlite`. Add Redis caching for analysis results.

---

### D5: Reproducibility -- 5/10

**Strengths:**
- `requirements.txt` with pinned versions.
- `start.bat` and `start.sh` scripts.
- SQLite file-based DB makes data portable.

**Weaknesses:**
- No Dockerfile or containerization.
- No seed data or fixture scripts for testing.
- `tests/test_smoke.py` is a single import check -- effectively zero test coverage.
- No CI/CD configuration.
- The `random`-based endpoint makes results non-reproducible across calls.

**Recommendation**: Add Dockerfile, seed data scripts, and meaningful test suite.

---

### D6: Code Quality / Documentation -- 5/10

**Strengths:**
- Consistent module structure: `services/`, `models/`, `core/`, `api/`, `rules/`.
- Chinese docstrings are domain-appropriate for the target audience.
- Each service module has a top-level convenience function (e.g., `check_triple_one_compliance()`).
- Pydantic schemas for request validation.

**Weaknesses:**
- No type hints on return values of most service methods.
- `routes.py` mixes two API namespaces: the `router = APIRouter()` (used by the real app) and a separate `router = APIRouter(prefix="/api/v1")` in `app/api/routes.py` -- actually there's only one router, but `app/main.py` is empty and `app.py` imports from `app.api.routes` while the frontend calls `/api/...` -- the routing prefix inconsistency will cause 404 errors.
- Silent exception swallowing in `log_audit()` (line 38: `except Exception: pass`).
- Magic numbers throughout (e.g., `15`, `30`, `40`, `25` risk scores) without justification or configuration.
- No logging framework usage despite `loguru` being in requirements.

**Recommendation**: Extract magic numbers to configuration. Add structured logging. Add API prefix consistency.

---

### D7: Impact / Significance -- 6/10

**Strengths:**
- Addresses a real and important regulatory domain: SOE investment compliance is governed by SASAC (State-owned Assets Supervision and Administration Commission) regulations.
- The responsibility chain graph has practical value for accountability tracing.
- The automated report generation with rectification plans is directly usable.
- The system covers the full investment lifecycle (proposal -> contract -> payment -> acceptance).

**Weaknesses:**
- No user study or case study demonstrating real-world effectiveness.
- No comparison with existing commercial or academic systems.
- The rule set is too small (10 rules) for production use.
- No integration with actual regulatory document sources.

**Recommendation**: Conduct a pilot study with a real SOE. Expand rule coverage. Add regulatory citation links.

---

## Top 1 Critical Issue -- FIXED

### Issue: `AttributeError` crash in `/register_project` endpoint

**File**: `backend/app/api/routes.py`, line 64  
**Severity**: Critical (Showstopper)  
**Code Before**:
```python
row = cur.to_dict(cur.fetchone())
return row
```

**Problem**: `sqlite3.Cursor` has no `to_dict()` method. Every call to `POST /register_project` raises `AttributeError: 'sqlite3.Cursor' object has no attribute 'to_dict'`, making project registration completely non-functional.

**Code After**:
```python
row = cur.fetchone()
return dict(row)
```

**Root Cause**: Likely confusion between `sqlite3.Row` (which supports `dict(row)`) and a non-existent cursor method.

---

## Additional Issues Ranked by Severity

| Rank | File | Line | Issue | Severity |
|------|------|------|-------|----------|
| 2 | `triple_match_checker.py` | 268 | `pass` in `_check_invoice_consistency` -- duplicate invoice detection unimplemented | High |
| 3 | `triple_match_checker.py` | 229 | `pass` in `_check_timeline_consistency` -- acceptance-after-payment check unimplemented | High |
| 4 | `routes.py` | 85 | `get_compliance_score()` uses `random.randint/uniform` -- non-deterministic compliance scores | High |
| 5 | `investment_risk_scorer.py` | 18 | Weights are hardcoded class attributes, not configurable via rules DB | Medium |
| 6 | `routes.py` | 24 | `init_db()` called at module import, blocking startup | Medium |
| 7 | `routes.py` | 38 | Silent `except Exception: pass` in `log_audit()` | Medium |
| 8 | `database.py` | 1-113 | Raw sqlite3 with no connection pooling, no async support | Medium |
| 9 | `investment_risk_scorer.py` | 203 | Fragile substring matching for related-party detection | Medium |
| 10 | `soe_investment_rules.json` | 1-98 | Rules loaded to DB but never queried by any service | Low |

---

## Verdict

**Conditional Accept with Major Revisions**

The system demonstrates a practical understanding of SOE compliance requirements and provides a functional prototype. However, it requires:

1. **Critical fix** (DONE): The `cur.to_dict()` crash.
2. **Complete the two `pass` branches** in triple-match checking.
3. **Remove `random`** from compliance scoring.
4. **Wire the rule store** to the checker services.
5. **Add meaningful test coverage** (currently near-zero).
6. **Migrate to async DB** for FastAPI compatibility.
7. **Formalize the "risk entropy" model** or rename it accurately.

With these revisions, the system would be suitable for a Q2 journal contribution in the domain of regulatory technology (RegTech) or government informatics.
