"""
Tests for investment_risk_scorer.py - Multi-dimensional risk entropy scoring.
Covers: process risk, capital risk, related risk, responsibility risk, risk levels, radar data.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.services.investment_risk_scorer import InvestmentRiskScorer, calculate_investment_risk


class TestRiskScorerWeights:
    """Test weight configuration."""

    def test_weights_sum_to_one(self):
        scorer = InvestmentRiskScorer()
        total = sum(scorer.weights.values())
        assert abs(total - 1.0) < 0.001

    def test_weight_keys(self):
        scorer = InvestmentRiskScorer()
        assert "process_risk" in scorer.weights
        assert "capital_risk" in scorer.weights
        assert "related_risk" in scorer.weights
        assert "responsibility_risk" in scorer.weights


class TestProcessRisk:
    """Test process risk calculation."""

    def test_no_documents_high_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"documents": [], "decision_chain": []}
        risk = scorer._calculate_process_risk(data)
        assert risk > 0

    def test_complete_documents_low_risk(self):
        scorer = InvestmentRiskScorer()
        data = {
            "documents": [
                {"doc_type": "project_proposal"},
                {"doc_type": "feasibility_study"},
                {"doc_type": "contract"},
                {"doc_type": "meeting_minutes"},
            ],
            "decision_chain": [{"node_type": "initiation"}, {"node_type": "decision"}, {"node_type": "approval"}],
        }
        risk = scorer._calculate_process_risk(data)
        assert risk < 50

    def test_non_compliant_decision_adds_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"documents": [], "decision_chain": []}
        decision_check = {"is_compliant": False, "missing_procedures": ["a", "b"]}
        risk = scorer._calculate_process_risk(data, decision_check)
        assert risk >= 40

    def test_risk_capped_at_100(self):
        scorer = InvestmentRiskScorer()
        data = {"documents": [], "decision_chain": []}
        decision_check = {"is_compliant": False, "missing_procedures": ["a", "b", "c", "d", "e"]}
        risk = scorer._calculate_process_risk(data, decision_check)
        assert risk <= 100.0


class TestCapitalRisk:
    """Test capital risk calculation."""

    def test_high_investment_increases_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"investment_amount": 50000000, "payments": [{"amount": 50000000}]}
        risk = scorer._calculate_capital_risk(data)
        assert risk >= 25

    def test_low_investment_low_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"investment_amount": 100000, "payments": [{"amount": 100000}]}
        risk = scorer._calculate_capital_risk(data)
        assert risk <= 20

    def test_triple_match_mismatches_increase_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"investment_amount": 1000000, "payments": []}
        triple_match = {
            "mismatches": [{"deviation_pct": 50}, {"deviation_pct": 30}],
            "details": {"mismatch_amount_sum": 500000},
        }
        risk = scorer._calculate_capital_risk(data, triple_match)
        assert risk > 20

    def test_no_payments_with_investment_adds_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"investment_amount": 5000000, "payments": []}
        risk = scorer._calculate_capital_risk(data)
        assert risk >= 20


class TestRelatedRisk:
    """Test related risk (关联交易) calculation."""

    def test_related_party_keywords_detected(self):
        scorer = InvestmentRiskScorer()
        data = {
            "department": "投资部",
            "contracts": [{"parties": "集团公司,子公司A"}],
        }
        risk = scorer._calculate_related_risk(data)
        assert risk >= 30

    def test_no_related_parties_low_risk(self):
        scorer = InvestmentRiskScorer()
        data = {
            "department": "投资部",
            "contracts": [{"parties": "独立供应商A"}],
        }
        risk = scorer._calculate_related_risk(data)
        assert risk < 30

    def test_duplicate_roles_increase_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"department": "", "contracts": []}
        chain = {
            "nodes": [
                {"name": "张三", "role": "approver"},
                {"name": "张三", "role": "approver"},
            ]
        }
        risk = scorer._calculate_related_risk(data, chain)
        assert risk >= 20


class TestResponsibilityRisk:
    """Test responsibility risk calculation."""

    def test_no_chain_high_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"documents": [], "decision_chain": []}
        risk = scorer._calculate_responsibility_risk(data, None)
        assert risk >= 40

    def test_few_nodes_increases_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"documents": [], "decision_chain": []}
        chain = {"nodes": [{"id": "n1"}], "edges": []}
        risk = scorer._calculate_responsibility_risk(data, chain)
        assert risk >= 25

    def test_no_approvers_increases_risk(self):
        scorer = InvestmentRiskScorer()
        data = {"documents": [], "decision_chain": [{"node_type": "initiation"}]}
        chain = {"nodes": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}], "edges": [{"from": "n1", "to": "n2"}]}
        risk = scorer._calculate_responsibility_risk(data, chain)
        assert risk >= 30

    def test_liability_waiver_detected(self):
        scorer = InvestmentRiskScorer()
        data = {
            "documents": [{"content": "本协议包含免责条款", "doc_type": "contract"}],
            "decision_chain": [{"approver": "张三"}],
        }
        chain = {"nodes": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}], "edges": [{"from": "n1", "to": "n2"}, {"from": "n2", "to": "n3"}]}
        risk = scorer._calculate_responsibility_risk(data, chain)
        assert risk >= 25


class TestRiskLevel:
    """Test risk level determination."""

    def test_low_risk(self):
        scorer = InvestmentRiskScorer()
        assert scorer._get_risk_level(10) == "low"
        assert scorer._get_risk_level(29) == "low"

    def test_medium_risk(self):
        scorer = InvestmentRiskScorer()
        assert scorer._get_risk_level(30) == "medium"
        assert scorer._get_risk_level(59) == "medium"

    def test_high_risk(self):
        scorer = InvestmentRiskScorer()
        assert scorer._get_risk_level(60) == "high"
        assert scorer._get_risk_level(79) == "high"

    def test_critical_risk(self):
        scorer = InvestmentRiskScorer()
        assert scorer._get_risk_level(80) == "critical"
        assert scorer._get_risk_level(100) == "critical"


class TestRiskEntropyCalculation:
    """Test full risk entropy calculation."""

    def test_full_calculation_returns_all_fields(self, sample_project_data):
        result = calculate_investment_risk(1, sample_project_data)

        assert "project_id" in result
        assert "total_score" in result
        assert "risk_level" in result
        assert "process_risk" in result
        assert "capital_risk" in result
        assert "related_risk" in result
        assert "responsibility_risk" in result
        assert "risk_factors" in result
        assert "risk_entropy_detail" in result

    def test_total_score_bounded(self, sample_project_data):
        result = calculate_investment_risk(1, sample_project_data)
        assert 0 <= result["total_score"] <= 100

    def test_risk_factors_extracted(self, sample_project_data):
        result = calculate_investment_risk(1, sample_project_data)
        assert isinstance(result["risk_factors"], list)

    def test_entropy_detail_has_dimensions(self, sample_project_data):
        result = calculate_investment_risk(1, sample_project_data)
        detail = result["risk_entropy_detail"]
        assert "dimensions" in detail
        assert "process" in detail["dimensions"]
        assert "capital" in detail["dimensions"]

    def test_risk_radar_data_generation(self, sample_project_data):
        scorer = InvestmentRiskScorer()
        result = scorer.calculate_risk_entropy(1, sample_project_data)
        radar = scorer.generate_risk_radar_data(result)

        assert "dimensions" in radar
        assert len(radar["dimensions"]) == 4
        assert "total_score" in radar
