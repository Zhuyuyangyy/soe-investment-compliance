"""
Tests for triple_match_checker.py - Contract/Payment/Acceptance matching.
Covers: amount matching, timeline consistency, invoice validation, report generation.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.services.triple_match_checker import TripleMatchChecker, check_triple_match


class TestTripleMatchAmountMatching:
    """Test amount matching logic."""

    def test_matching_amounts_pass(self, sample_contracts, sample_payments, sample_acceptances):
        checker = TripleMatchChecker()
        result = checker.check_triple_match(1, sample_contracts, sample_payments, sample_acceptances)

        assert result["is_matched"] is True
        assert result["overall_status"] == "normal"

    def test_mismatched_amounts_detected(self, mismatch_contracts, mismatch_payments, mismatch_acceptances):
        checker = TripleMatchChecker()
        result = checker.check_triple_match(1, mismatch_contracts, mismatch_payments, mismatch_acceptances)

        assert result["is_matched"] is False
        assert result["overall_status"] == "mismatch"
        assert len(result["mismatches"]) > 0

    def test_no_contracts_warning(self):
        checker = TripleMatchChecker()
        result = checker.check_triple_match(1, [], [], [])

        assert result["is_matched"] is False
        assert any(w["code"] == "NO_CONTRACT" for w in result["warnings"])

    def test_risk_score_bounded_at_100(self):
        checker = TripleMatchChecker()
        contracts = [{"id": 1, "amount": 100, "contract_no": "C1"}]
        payments = [{"id": 1, "amount": 999999, "payment_no": "P1"}]
        acceptances = [{"id": 1, "amount": 1, "acceptance_no": "A1"}]

        result = checker.check_triple_match(1, contracts, payments, acceptances)
        assert result["risk_score"] <= 100.0

    def test_payment_deviation_detected(self):
        checker = TripleMatchChecker()
        contracts = [{"id": 1, "amount": 1000000, "contract_no": "C1"}]
        payments = [{"id": 1, "amount": 2000000, "payment_no": "P1"}]
        acceptances = [{"id": 1, "amount": 1000000, "acceptance_no": "A1"}]

        result = checker.check_triple_match(1, contracts, payments, acceptances)
        assert len(result["mismatches"]) > 0

    def test_acceptance_deviation_detected(self):
        checker = TripleMatchChecker()
        contracts = [{"id": 1, "amount": 1000000, "contract_no": "C1"}]
        payments = [{"id": 1, "amount": 1000000, "payment_no": "P1"}]
        acceptances = [{"id": 1, "amount": 50000, "acceptance_no": "A1"}]

        result = checker.check_triple_match(1, contracts, payments, acceptances)
        assert len(result["mismatches"]) > 0

    def test_consistent_amounts_reported(self):
        checker = TripleMatchChecker()
        contracts = [{"id": 1, "amount": 500000, "contract_no": "C1"}]
        payments = [{"id": 1, "amount": 500000, "payment_no": "P1"}]
        acceptances = [{"id": 1, "amount": 500000, "acceptance_no": "A1"}]

        result = checker.check_triple_match(1, contracts, payments, acceptances)
        assert len(result["matches"]) > 0
        assert result["matches"][0]["type"] == "all_amounts_consistent"


class TestTripleMatchTimeline:
    """Test timeline consistency checks."""

    def test_payment_before_contract_detected(self):
        checker = TripleMatchChecker()
        contracts = [{"id": 1, "amount": 1000000, "signing_date": "2024-06-01", "contract_no": "C1"}]
        payments = [{"id": 1, "amount": 1000000, "payment_date": "2024-01-01", "payment_no": "P1"}]
        acceptances = []

        result = checker.check_triple_match(1, contracts, payments, acceptances)
        assert any(w["code"] == "PAYMENT_BEFORE_CONTRACT" for w in result["warnings"])

    def test_excessive_time_gap_detected(self):
        checker = TripleMatchChecker()
        contracts = [{"id": 1, "amount": 1000000, "signing_date": "2020-01-01", "contract_no": "C1"}]
        payments = [{"id": 1, "amount": 1000000, "payment_date": "2020-02-01", "payment_no": "P1"}]
        acceptances = [{"id": 1, "amount": 1000000, "acceptance_date": "2024-01-01", "acceptance_no": "A1"}]

        result = checker.check_triple_match(1, contracts, payments, acceptances)
        assert any(w["code"] == "EXCESSIVE_TIME_GAP" for w in result["warnings"])

    def test_valid_timeline_no_warnings(self):
        checker = TripleMatchChecker()
        contracts = [{"id": 1, "amount": 1000000, "signing_date": "2024-01-01", "contract_no": "C1"}]
        payments = [{"id": 1, "amount": 1000000, "payment_date": "2024-02-01", "payment_no": "P1"}]
        acceptances = [{"id": 1, "amount": 1000000, "acceptance_date": "2024-06-01", "acceptance_no": "A1"}]

        result = checker.check_triple_match(1, contracts, payments, acceptances)
        timeline_warnings = [w for w in result["warnings"] if w["code"] in ("PAYMENT_BEFORE_CONTRACT", "EXCESSIVE_TIME_GAP")]
        assert len(timeline_warnings) == 0


class TestTripleMatchInvoice:
    """Test invoice consistency checks."""

    def test_missing_invoice_warning(self):
        checker = TripleMatchChecker()
        payments = [{"id": 1, "amount": 1000000, "payment_no": "P1"}]
        acceptances = []

        result = checker._check_invoice_consistency(payments, acceptances)
        assert any(w["code"] == "MISSING_INVOICE" for w in result["warnings"])

    def test_invoice_present_no_warning(self):
        checker = TripleMatchChecker()
        payments = [{"id": 1, "amount": 1000000, "payment_no": "P1", "invoice_no": "FP-001"}]
        acceptances = []

        result = checker._check_invoice_consistency(payments, acceptances)
        assert len(result["warnings"]) == 0


class TestTripleMatchReport:
    """Test report generation."""

    def test_generate_match_report(self):
        checker = TripleMatchChecker()
        check_result = {
            "contract_count": 1,
            "payment_count": 1,
            "acceptance_count": 1,
            "overall_status": "normal",
            "matches": [{"type": "all_amounts_consistent", "contract_amount": 1000, "payment_amount": 1000, "acceptance_amount": 1000}],
            "mismatches": [],
            "warnings": [],
        }
        report = checker.generate_match_report(check_result)

        assert "summary" in report
        assert "amount_analysis" in report
        assert "issues" in report
        assert "recommendations" in report

    def test_report_with_mismatches_has_recommendations(self):
        checker = TripleMatchChecker()
        check_result = {
            "contract_count": 1,
            "payment_count": 1,
            "acceptance_count": 1,
            "overall_status": "mismatch",
            "matches": [],
            "mismatches": [{"type": "payment_vs_contract", "code": "RULE_SOE_005", "deviation_pct": 50}],
            "warnings": [{"code": "W1"}, {"code": "W2"}, {"code": "W3"}],
        }
        report = checker.generate_match_report(check_result)
        assert len(report["recommendations"]) > 0


class TestTripleMatchTopLevel:
    """Test the top-level check_triple_match function."""

    def test_top_level_function(self, sample_contracts, sample_payments, sample_acceptances):
        result = check_triple_match(1, sample_contracts, sample_payments, sample_acceptances)
        assert "project_id" in result
        assert result["project_id"] == 1
