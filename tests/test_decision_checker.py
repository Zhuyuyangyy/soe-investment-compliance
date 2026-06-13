"""
Tests for decision_checker.py - Three-Major-Decisions compliance validation.
Covers: DecisionChecker class, triple-one detection, procedure determination, chain validation.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.services.decision_checker import DecisionChecker, check_triple_one_compliance


class TestDecisionCheckerTripleOneDetection:
    """Test triple-one item detection."""

    def test_high_amount_is_triple_one(self):
        checker = DecisionChecker()
        data = {"investment_amount": 10000000, "project_name": "普通项目", "doc_types": []}
        assert checker._is_triple_one_item(data) is True

    def test_medium_amount_is_triple_one(self):
        checker = DecisionChecker()
        data = {"investment_amount": 5000000, "project_name": "普通项目", "doc_types": []}
        assert checker._is_triple_one_item(data) is True

    def test_low_amount_not_triple_one(self):
        checker = DecisionChecker()
        data = {"investment_amount": 100000, "project_name": "日常采购", "doc_types": []}
        assert checker._is_triple_one_item(data) is False

    def test_keyword_triggers_triple_one(self):
        checker = DecisionChecker()
        data = {"investment_amount": 0, "project_name": "对外投资项目", "doc_types": []}
        assert checker._is_triple_one_item(data) is True

    def test_meeting_minutes_trigger_triple_one(self):
        checker = DecisionChecker()
        data = {"investment_amount": 0, "project_name": "普通", "doc_types": ["meeting_minutes"]}
        assert checker._is_triple_one_item(data) is True

    def test_board_resolution_triggers_triple_one(self):
        checker = DecisionChecker()
        data = {"investment_amount": 0, "project_name": "普通", "doc_types": ["board_resolution"]}
        assert checker._is_triple_one_item(data) is True


class TestDecisionCheckerProcedures:
    """Test required procedure determination."""

    def test_high_value_requires_all_procedures(self):
        checker = DecisionChecker()
        procs = checker._determine_required_procedures(20000000, {"project_name": "", "project_type": ""})
        assert "feasibility_study" in procs
        assert "party_committee_review" in procs
        assert "board_resolution" in procs
        assert "supervision_committee_review" in procs
        assert "public_disclosure" in procs

    def test_medium_value_requires_board(self):
        checker = DecisionChecker()
        procs = checker._determine_required_procedures(7000000, {"project_name": "", "project_type": ""})
        assert "feasibility_study" in procs
        assert "board_resolution" in procs
        assert "party_committee_review" not in procs

    def test_low_value_requires_management_review(self):
        checker = DecisionChecker()
        procs = checker._determine_required_procedures(1000000, {"project_name": "", "project_type": ""})
        assert "feasibility_study" in procs
        assert "management_review" in procs
        assert "board_resolution" not in procs

    def test_procurement_project_adds_competition(self):
        checker = DecisionChecker()
        procs = checker._determine_required_procedures(1000000, {"project_name": "设备采购项目", "project_type": ""})
        assert "procurement_competition" in procs

    def test_engineering_project_adds_approval(self):
        checker = DecisionChecker()
        procs = checker._determine_required_procedures(1000000, {"project_name": "", "project_type": "建设工程"})
        assert "engineering_approval" in procs


class TestDecisionCheckerCompliance:
    """Test full compliance checking."""

    def test_compliant_project_passes(self, sample_project_data):
        result = check_triple_one_compliance(sample_project_data)
        assert "is_compliant" in result
        assert "risk_level" in result
        assert "issues" in result
        assert "required_procedures" in result
        assert "recommendations" in result

    def test_non_triple_one_project(self):
        data = {
            "investment_amount": 10000,
            "project_name": "办公用品采购",
            "doc_types": [],
            "documents": [],
            "decision_chain": [],
        }
        result = check_triple_one_compliance(data)
        assert result["is_triple_one"] is False

    def test_missing_documents_raises_issues(self):
        data = {
            "investment_amount": 10000000,
            "project_name": "大型投资项目",
            "doc_types": [],
            "documents": [],
            "decision_chain": [],
        }
        result = check_triple_one_compliance(data)
        assert result["is_compliant"] is False
        assert len(result["issues"]) > 0

    def test_decision_chain_chronology_check(self):
        checker = DecisionChecker()
        chain = [
            {"node_type": "decision", "timestamp": "2024-03-01"},
            {"node_type": "approval", "timestamp": "2024-02-01"},
        ]
        issues = checker._check_decision_chain(chain, ["board_resolution"])
        assert any(i["code"] == "CHRONOLOGY_VIOLATION" for i in issues)

    def test_empty_decision_chain(self):
        checker = DecisionChecker()
        issues = checker._check_decision_chain([], ["board_resolution"])
        assert any(i["code"] == "NO_DECISION_CHAIN" for i in issues)

    def test_missing_approver_detected(self):
        checker = DecisionChecker()
        data = {
            "documents": [
                {"doc_type": "project_proposal"},
                {"doc_type": "feasibility_study"},
                {"doc_type": "meeting_minutes"},
            ],
        }
        chain = [{"node_type": "decision"}]
        issues = checker._check_decision_compliance(data, chain)
        assert any(i["code"] == "MISSING_APPROVER" for i in issues)

    def test_generate_recommendations_for_missing_feasibility(self):
        checker = DecisionChecker()
        result = {"missing_procedures": ["feasibility_study"]}
        recs = checker._generate_recommendations(result)
        assert len(recs) > 0
        assert any("可行性" in r for r in recs)

    def test_generate_recommendations_for_compliant(self):
        checker = DecisionChecker()
        result = {"missing_procedures": []}
        recs = checker._generate_recommendations(result)
        assert any("基本完整" in r for r in recs)
