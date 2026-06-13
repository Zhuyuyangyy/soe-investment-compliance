"""
Tests for report_generator.py - Compliance report generation.
Covers: executive summary, issues list, rectification plan, markdown export.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.services.report_generator import ReportGenerator, generate_rectification_report


class TestReportGeneratorSections:
    """Test report section generation."""

    def test_full_report_has_all_sections(self, sample_project_data):
        generator = ReportGenerator()
        risk_result = {
            "total_score": 35, "risk_level": "medium",
            "process_risk": 30, "capital_risk": 20, "related_risk": 10, "responsibility_risk": 15,
            "risk_factors": [],
        }
        triple_match = {"is_matched": True, "overall_status": "normal", "mismatches": [], "warnings": []}
        decision_check = {"is_compliant": True, "issues": []}
        chain = {"metadata": {"total_nodes": 5, "total_edges": 4, "risk_nodes": []}}

        report = generator.generate_comprehensive_report(
            1, sample_project_data, risk_result, triple_match, decision_check, chain
        )

        assert "report_id" in report
        assert "generated_at" in report
        sections = report["sections"]
        assert "executive_summary" in sections
        assert "project_overview" in sections
        assert "compliance_check_results" in sections
        assert "risk_analysis" in sections
        assert "triple_match_results" in sections
        assert "responsibility_chain" in sections
        assert "issues_list" in sections
        assert "rectification_plan" in sections
        assert "appendices" in sections

    def test_report_id_format(self, sample_project_data):
        generator = ReportGenerator()
        risk_result = {"total_score": 0, "risk_level": "low", "risk_factors": []}
        report = generator.generate_comprehensive_report(
            42, sample_project_data, risk_result, None, None, None
        )
        assert report["report_id"].startswith("REPORT_42_")
        assert report["project_id"] == 42


class TestExecutiveSummary:
    """Test executive summary generation."""

    def test_compliant_project_summary(self, sample_project_data):
        generator = ReportGenerator()
        risk_result = {"total_score": 10, "risk_level": "low", "risk_factors": []}
        summary = generator._generate_executive_summary(
            sample_project_data, risk_result,
            {"is_matched": True}, {"is_compliant": True}
        )
        assert summary["overall_assessment"] == "合规"

    def test_risky_project_summary(self, sample_project_data):
        generator = ReportGenerator()
        risk_result = {
            "total_score": 85, "risk_level": "critical",
            "risk_factors": [
                {"severity": "critical", "dimension": "process", "code": "C1", "description": "test"},
                {"severity": "high", "dimension": "capital", "code": "C2", "description": "test"},
            ],
        }
        summary = generator._generate_executive_summary(
            sample_project_data, risk_result,
            {"is_matched": False}, {"is_compliant": False}
        )
        assert summary["overall_assessment"] == "存在风险"
        assert len(summary["key_findings"]) > 0
        assert len(summary["recommendations_summary"]) > 0

    def test_summary_includes_project_info(self, sample_project_data):
        generator = ReportGenerator()
        risk_result = {"total_score": 10, "risk_level": "low", "risk_factors": []}
        summary = generator._generate_executive_summary(
            sample_project_data, risk_result, {"is_matched": True}, {"is_compliant": True}
        )
        assert summary["project_name"] == "新能源光伏发电项目"
        assert summary["investment_amount"] == 8000000


class TestIssuesList:
    """Test issues list generation."""

    def test_issues_sorted_by_severity(self):
        generator = ReportGenerator()
        risk_result = {
            "risk_factors": [
                {"dimension": "process", "code": "LOW1", "severity": "low", "description": "low issue"},
                {"dimension": "capital", "code": "CRIT1", "severity": "critical", "description": "critical issue"},
                {"dimension": "related", "code": "MED1", "severity": "medium", "description": "medium issue"},
            ]
        }
        issues = generator._generate_issues_list(risk_result, {"mismatches": []}, {"issues": []})

        assert issues[0]["severity"] == "critical"
        assert issues[-1]["severity"] == "low"

    def test_issues_from_multiple_sources(self):
        generator = ReportGenerator()
        risk_result = {"risk_factors": [{"dimension": "process", "code": "R1", "severity": "high", "description": "risk"}]}
        triple_match = {"mismatches": [{"code": "RULE_SOE_005", "type": "amount_mismatch", "deviation_pct": 50}]}
        decision_check = {"issues": [{"code": "DC1", "severity": "medium", "message": "decision issue"}]}

        issues = generator._generate_issues_list(risk_result, triple_match, decision_check)
        sources = {i["source"] for i in issues}
        assert "risk_analysis" in sources
        assert "triple_match" in sources
        assert "compliance_check" in sources


class TestRectificationPlan:
    """Test rectification plan generation."""

    def test_plan_generated_for_each_risk_factor(self):
        generator = ReportGenerator()
        risk_result = {
            "risk_factors": [
                {"dimension": "process", "code": "RULE_SOE_001", "severity": "high"},
                {"dimension": "capital", "code": "RULE_SOE_005", "severity": "high"},
                {"dimension": "related", "code": "RULE_SOE_006", "severity": "critical"},
                {"dimension": "responsibility", "code": "RULE_SOE_007", "severity": "medium"},
            ]
        }
        plans = generator._generate_rectification_plan(risk_result, None, None)
        assert len(plans) >= 4

    def test_plan_has_required_fields(self):
        generator = ReportGenerator()
        risk_result = {"risk_factors": [{"dimension": "process", "code": "RULE_SOE_001", "severity": "high"}]}
        plans = generator._generate_rectification_plan(risk_result, None, None)

        plan = plans[0]
        assert "id" in plan
        assert "rectification_action" in plan
        assert "responsible_party" in plan
        assert "deadline" in plan
        assert "status" in plan


class TestMarkdownExport:
    """Test markdown export functionality."""

    def test_export_to_markdown(self, sample_project_data):
        generator = ReportGenerator()
        risk_result = {"total_score": 30, "risk_level": "low", "risk_factors": []}
        report = generator.generate_comprehensive_report(
            1, sample_project_data, risk_result, {"is_matched": True, "mismatches": []},
            {"is_compliant": True, "issues": []}, {"metadata": {"total_nodes": 3}}
        )
        md = generator.export_to_markdown(report)

        assert "国企经营投资合规审查报告" in md
        assert "执行摘要" in md
        assert "问题清单" in md
        assert "整改计划" in md


class TestAppendices:
    """Test appendix generation."""

    def test_appendix_has_summaries(self, sample_project_data):
        generator = ReportGenerator()
        appendix = generator._generate_appendices(sample_project_data)

        assert "document_list" in appendix
        assert "contract_summary" in appendix
        assert "payment_summary" in appendix
        assert "acceptance_summary" in appendix
        assert appendix["contract_summary"]["count"] == 1
        assert appendix["contract_summary"]["total_amount"] == 8000000


class TestReportTopLevel:
    """Test top-level report generation function."""

    def test_generate_rectification_report_function(self, sample_project_data):
        risk_result = {"total_score": 20, "risk_level": "low", "risk_factors": []}
        report = generate_rectification_report(
            1, sample_project_data, risk_result,
            {"is_matched": True, "mismatches": [], "warnings": []},
            {"is_compliant": True, "issues": [], "missing_procedures": []},
            {"metadata": {"total_nodes": 5, "total_edges": 4, "risk_nodes": []}}
        )
        assert report["project_id"] == 1
        assert "sections" in report
