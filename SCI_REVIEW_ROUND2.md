# Q2-Level SCI Review Round 2: SOE Investment Compliance System

**Reviewer**: AI Code Review Agent
**Date**: 2026-05-29
**Repository**: soe-investment-compliance
**Language**: Python (FastAPI) + Vue 3 Frontend
**Previous Review**: SCI_REVIEW_Q2.md (Round 1, score 4.75/10)

---

## Round 1 Issue Status

| # | Issue | Severity | Round 1 | Round 2 Status |
|---|-------|----------|---------|----------------|
| 1 | `cur.to_dict()` crash in `/register_project` | Critical | FIXED | **CONFIRMED FIXED** -- `dict(row)` at routes.py:65 |
| 2 | `pass` in `_check_invoice_consistency` (line 270) | High | Open | **STILL OPEN** -- duplicate invoice detection unimplemented |
| 3 | `pass` in `_check_timeline_consistency` (line 229) | High | Open | **STILL OPEN** -- acceptance-after-payment check unimplemented |
| 4 | `random.randint/uniform` in `get_compliance_score` | High | Open | **STILL OPEN** -- non-deterministic compliance scores |
| 5 | Hardcoded risk weights | Medium | Open | **STILL OPEN** -- weights remain class attributes |
| 6 | `init_db()` at module import time | Medium | Open | **STILL OPEN** -- routes.py:24 |
| 7 | Silent `except Exception: pass` in `log_audit` | Medium | Open | **STILL OPEN** -- routes.py:38-39 |
| 8 | Raw sqlite3, no connection pooling | Medium | Open | **STILL OPEN** -- database.py unchanged |
| 9 | Fragile substring matching in `_calculate_related_risk` | Medium | Open | **STILL OPEN** -- investment_risk_scorer.py:203 |
| 10 | Rules loaded to DB but never queried | Low | Open | **STILL OPEN** -- no service reads from rules table |

---

## New Issues Discovered in Round 2

### NEW-1: API Routing Prefix Mismatch (High)

**Files**: `app/api/routes.py`, `app.py`, `nginx.conf`, `Dockerfile`

The router in `app/api/routes.py` is defined as `router = APIRouter()` with **no prefix**. The `app.py` includes it without adding a prefix. However:
- The frontend calls `http://localhost:8017/api/...`
- The nginx config proxies `/api/` to `http://backend:8017/api/`
- The Dockerfile health check expects `http://localhost:8017/api/health`

All these expect an `/api/` prefix that does not exist on the router. Every API call through nginx or the Docker health check would return 404. This is a **deployment-blocking bug**.

**Fix**: Change `router = APIRouter()` to `router = APIRouter(prefix="/api")` in `app/api/routes.py`.

### NEW-2: Rules JSON Count Mismatch (Low)

The JSON file `backend/app/rules/soe_investment_rules.json` contains 10 rules (RULE_SOE_001 through RULE_SOE_010), but `database.py` only seeds 7 rules (RULE_SOE_001 through RULE_SOE_007). Rules 008-010 are never loaded. Combined with Issue #10 (rules never queried), the rule system is doubly disconnected.

### NEW-3: `sqlalchemy` Dependency Unused (Low)

`sqlalchemy==2.0.25` is listed in `requirements.txt` but is never imported anywhere in the codebase. The entire system uses raw `sqlite3`. This adds unnecessary deployment weight and confuses developers.

---

## What Improved Since Round 1

### 1. Test Suite -- Major Improvement

The test suite expanded from a single import-check smoke test to a comprehensive suite:

| Test File | Test Count | Coverage |
|-----------|:---:|----------|
| `test_routes.py` | 25 | Full API integration: health, CRUD, triple match, chain, analysis, audit |
| `test_triple_match_checker.py` | 14 | Amount matching, timeline, invoice, report generation |
| `test_investment_risk_scorer.py` | 22 | All 4 risk dimensions, risk levels, radar data |
| `test_decision_checker.py` | 12 | Triple-one detection, procedures, compliance, chain validation |
| `test_responsibility_chain.py` | 15 | Node extraction, edge building, risk detection, visualization |
| `test_report_generator.py` | 11 | Executive summary, issues list, rectification plan, markdown export |
| `test_project_parser.py` | 17 | Document parsing, field extraction, virtual coords, batch operations |
| `conftest.py` | -- | Shared fixtures: tmp_db, sample data, mismatch scenarios |

**Total**: ~116 tests across 7 files with shared fixtures. This is a significant improvement in testability and reproducibility.

### 2. Containerization

- **Dockerfile**: Multi-stage build, non-root user, health check, proper environment variables.
- **docker-compose.yml**: Full orchestration with frontend (nginx) + backend services, health checks, volumes, network isolation.

### 3. Development Tooling

- `pytest.ini` with proper configuration, markers, and verbose output.
- `requirements-dev.txt` with testing (pytest, pytest-cov, pytest-asyncio, pytest-xdist), linting (ruff, black, isort), type checking (mypy), security scanning (bandit, safety), and documentation (mkdocs) dependencies.

---

## 7-Dimension Re-Scoring

| # | Dimension | Round 1 | Round 2 | Delta | Weight | Weighted |
|---|-----------|:---:|:---:|:---:|:---:|:---:|
| D1 | Novelty / Originality | 5 | 5 | 0 | 15% | 0.75 |
| D2 | Technical Rigor | 4 | 5 | +1 | 20% | 1.00 |
| D3 | Completeness | 6 | 7 | +1 | 15% | 1.05 |
| D4 | Scalability | 3 | 3 | 0 | 15% | 0.45 |
| D5 | Reproducibility | 5 | 7 | +2 | 10% | 0.70 |
| D6 | Code Quality / Documentation | 5 | 6 | +1 | 15% | 0.90 |
| D7 | Impact / Significance | 6 | 6 | 0 | 10% | 0.60 |
| | **Total** | **4.75** | **5.45** | **+0.70** | **100%** | **5.45 / 10** |

---

### D1: Novelty / Originality -- 5/10 (unchanged)

No algorithmic changes were made. The risk scoring model remains a weighted linear combination (not entropy), the triple-match checker remains arithmetic comparison, and no advanced NLP or graph-theoretic techniques were introduced.

**Recommendation** (unchanged): Introduce a genuine information-theoretic or graph-theoretic formulation. If using "entropy," compute actual entropy over risk factor distributions.

---

### D2: Technical Rigor -- 5/10 (+1)

**Improved**: The critical `cur.to_dict()` crash has been confirmed fixed. The `/register_project` endpoint now works correctly.

**Remaining issues**:
- Two `pass` branches in `triple_match_checker.py` (lines 229, 270) leave invoice and timeline checks incomplete.
- `random.randint/uniform` in `get_compliance_score` (`app/main.py:85-86`) produces non-deterministic compliance scores -- unacceptable for audit.
- Fragile substring matching (`dept in parties`) at `investment_risk_scorer.py:203`.
- New issue: API routing prefix mismatch (NEW-1) would cause 404 errors on deployment.

**Recommendation**: Complete the two `pass` branches. Replace `random` with actual database aggregation. Fix the routing prefix.

---

### D3: Completeness -- 7/10 (+1)

**Improved**:
- Dockerfile and docker-compose.yml added, enabling containerized deployment.
- Comprehensive test suite (116 tests) covering all major service modules and API endpoints.
- `requirements-dev.txt` with full development tooling.

**Still missing**:
- No authentication or authorization system.
- No pagination on list endpoints.
- Rules loaded to DB but never queried by any service.
- API routing prefix mismatch prevents actual deployment.
- `sqlalchemy` in requirements but never used; raw `sqlite3` throughout.

**Recommendation**: Wire the rule store to checkers. Add authentication. Fix the routing prefix.

---

### D4: Scalability -- 3/10 (unchanged)

No changes to the database layer. Raw `sqlite3` with no connection pooling, no async support, no caching. `init_db()` still called at module import time.

**Recommendation** (unchanged): Migrate to async DB with connection pooling. Add caching for risk calculations.

---

### D5: Reproducibility -- 7/10 (+2)

**Improved**:
- Dockerfile with multi-stage build ensures reproducible container environment.
- docker-compose.yml enables one-command deployment.
- 116 tests with shared fixtures provide reproducible validation.
- `pytest.ini` with proper configuration.

**Still weak**:
- No seed data or fixture scripts for manual testing.
- `random`-based endpoint makes compliance scores non-reproducible.
- No CI/CD pipeline configuration (though `requirements-dev.txt` includes the right tools).

**Recommendation**: Add seed data scripts. Remove `random` from compliance scoring. Add CI/CD configuration.

---

### D6: Code Quality / Documentation -- 6/10 (+1)

**Improved**:
- Comprehensive test suite demonstrates expected behavior for all major components.
- `conftest.py` with well-structured shared fixtures.
- `requirements-dev.txt` with linting and type-checking tools.

**Remaining issues**:
- API routing prefix mismatch (NEW-1) is a deployment blocker.
- Silent `except Exception: pass` in `log_audit()`.
- Magic numbers throughout risk scoring (15, 30, 40, 25, etc.) without configuration.
- No type hints on return values of most service methods.
- `loguru` in requirements but never used.

**Recommendation**: Fix the routing prefix. Extract magic numbers to configuration. Add structured logging.

---

### D7: Impact / Significance -- 6/10 (unchanged)

No changes to the domain contribution. The system still addresses a real regulatory domain with practical value, but lacks user studies, case comparisons, and expanded rule coverage.

**Recommendation** (unchanged): Conduct a pilot study. Expand rule coverage. Add regulatory citation links.

---

## Updated Issue Priority List

| Rank | File | Issue | Severity | Status |
|------|------|-------|----------|--------|
| 1 | `routes.py` | API routing prefix mismatch -- deployment blocker | **High (NEW)** | Open |
| 2 | `triple_match_checker.py:270` | `pass` in `_check_invoice_consistency` | High | Open |
| 3 | `triple_match_checker.py:229` | `pass` in `_check_timeline_consistency` | High | Open |
| 4 | `app/main.py:85` | `random.randint/uniform` in compliance score | High | Open |
| 5 | `routes.py:64` | `cur.to_dict()` crash | Critical | **FIXED** |
| 6 | `investment_risk_scorer.py:18` | Hardcoded risk weights | Medium | Open |
| 7 | `routes.py:24` | `init_db()` at import time | Medium | Open |
| 8 | `routes.py:38` | Silent `except Exception: pass` | Medium | Open |
| 9 | `database.py` | Raw sqlite3, no pooling, no async | Medium | Open |
| 10 | `investment_risk_scorer.py:203` | Fragile substring matching | Medium | Open |
| 11 | `soe_investment_rules.json` | Rules loaded to DB but never queried | Low | Open |
| 12 | `requirements.txt` | `sqlalchemy` listed but never imported | Low | Open |
| 13 | `database.py` vs `soe_investment_rules.json` | Rule count mismatch (7 vs 10) | Low | Open |

---

## Verdict

**Conditional Accept with Major Revisions (Score: 5.45/10, up from 4.75/10)**

The project has made meaningful progress since Round 1. The critical crash bug is fixed, and the test suite has grown from near-zero to 116 meaningful tests. Containerization with Dockerfile and docker-compose improves reproducibility significantly.

However, the system still cannot be deployed as-is due to the API routing prefix mismatch (NEW-1). Three high-severity code issues remain: two `pass` branches in the triple-match checker and `random`-based compliance scoring. The rule engine remains disconnected from the rule store.

**Required before acceptance**:

1. **Fix the API routing prefix** -- add `prefix="/api"` to the router.
2. **Complete the two `pass` branches** in `triple_match_checker.py`.
3. **Remove `random`** from `get_compliance_score` -- query actual data from the database.
4. **Wire the rule store** to the checker services.
5. **Add meaningful test coverage for edge cases** -- the current tests cover happy paths well but lack negative/boundary tests for the `pass` branches and `random` endpoint.

**Recommended improvements**:

6. Migrate to async DB with connection pooling.
7. Add authentication and authorization.
8. Formalize the "risk entropy" model or rename it accurately.
9. Extract magic numbers to configuration.
10. Add pagination to list endpoints.

With these revisions, the system would reach the 6.5-7.0 range and be suitable for a Q2 journal contribution in RegTech or government informatics.
