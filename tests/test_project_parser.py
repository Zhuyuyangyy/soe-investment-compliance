"""
Tests for project_parser.py - Document parsing engine.
Covers: ProjectParser class, field extraction, virtual coords, issue detection, batch parsing.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.services.project_parser import ProjectParser, parse_project_docs


class TestProjectParserParseDocument:
    """Test ProjectParser.parse_document method."""

    def test_parse_project_proposal_with_all_fields(self):
        parser = ProjectParser()
        content = "项目名称：智慧城市建设项目\n投资额度：5000万元\n责任部门：信息技术部"
        result = parser.parse_document("project_proposal", content)

        assert result["doc_type"] == "project_proposal"
        assert "extracted_fields" in result
        assert result["extracted_fields"]["project_name"] == "智慧城市建设项目"
        assert result["extracted_fields"]["investment_amount"] == "5000"
        assert result["extracted_fields"]["department"] == "信息技术部"

    def test_parse_project_proposal_missing_amount(self):
        parser = ProjectParser()
        content = "项目名称：测试项目\n责任部门：测试部"
        result = parser.parse_document("project_proposal", content)

        assert "investment_amount" not in result["extracted_fields"]
        issues = result["issues"]
        assert any(i["code"] == "MISSING_AMOUNT" for i in issues)

    def test_parse_project_proposal_missing_department(self):
        parser = ProjectParser()
        content = "项目名称：测试项目\n投资额度：100万元"
        result = parser.parse_document("project_proposal", content)

        issues = result["issues"]
        assert any(i["code"] == "MISSING_DEPT" for i in issues)

    def test_parse_feasibility_study(self):
        parser = ProjectParser()
        content = "项目名称：新能源项目\n投资估算：3000万元\nROI：12.5%"
        result = parser.parse_document("feasibility_study", content)

        assert result["extracted_fields"]["project_name"] == "新能源项目"
        assert result["extracted_fields"]["investment_amount"] == "3000"

    def test_parse_feasibility_study_missing_investment(self):
        parser = ProjectParser()
        content = "可行性分析报告\n项目前景良好"
        result = parser.parse_document("feasibility_study", content)

        issues = result["issues"]
        assert any(i["code"] == "MISSING_INVESTMENT" for i in issues)

    def test_parse_meeting_minutes_with_decision(self):
        parser = ProjectParser()
        content = "董事会会议纪要\n参会人员：张三、李四\n研究决定：同意立项"
        result = parser.parse_document("meeting_minutes", content)

        assert result["extracted_fields"]["meeting_type"] is not None
        issues = result["issues"]
        assert not any(i["code"] == "NO_DECISION" for i in issues)

    def test_parse_meeting_minutes_without_decision(self):
        parser = ProjectParser()
        content = "总经理办公会纪要\n讨论了项目进展"
        result = parser.parse_document("meeting_minutes", content)

        issues = result["issues"]
        assert any(i["code"] == "NO_DECISION" for i in issues)

    def test_parse_contract_with_fields(self):
        parser = ProjectParser()
        content = "合同编号：HT-2024-001\n合同金额：500万元\n甲方：国投集团\n乙方：建设公司"
        result = parser.parse_document("contract", content)

        assert result["extracted_fields"]["contract_no"] == "HT-2024-001"

    def test_parse_contract_missing_amount(self):
        parser = ProjectParser()
        content = "合同编号：HT-2024-001\n甲方：国投集团"
        result = parser.parse_document("contract", content)

        issues = result["issues"]
        assert any(i["code"] == "MISSING_CONTRACT_AMOUNT" for i in issues)

    def test_parse_payment(self):
        parser = ProjectParser()
        content = "付款编号：FK-2024-001\n付款金额：200万元\n发票号：FP-001"
        result = parser.parse_document("payment", content)

        assert result["extracted_fields"]["payment_no"] == "FK-2024-001"
        assert result["extracted_fields"]["invoice_no"] == "FP-001"

    def test_parse_acceptance(self):
        parser = ProjectParser()
        content = "验收编号：YS-2024-001\n验收金额：500万元\n验收结果：合格"
        result = parser.parse_document("acceptance", content)

        assert result["extracted_fields"]["acceptance_no"] == "YS-2024-001"
        assert result["extracted_fields"]["result"] == "合格"

    def test_parse_unknown_doc_type(self):
        parser = ProjectParser()
        result = parser.parse_document("unknown_type", "some content")

        assert result["doc_type"] == "unknown_type"
        assert result["extracted_fields"] == {}

    def test_parse_empty_content(self):
        parser = ProjectParser()
        result = parser.parse_document("project_proposal", "")

        assert result["raw_content"] == ""
        assert result["extracted_fields"] == {}

    def test_virtual_coords_generated(self):
        parser = ProjectParser()
        content = "第一章 总则\n第二章 项目概况\n第三章 投资估算"
        result = parser.parse_document("project_proposal", content)

        coords = result["virtual_coords"]
        assert coords["line_count"] >= 1
        assert coords["char_count"] > 0

    def test_upload_time_preserved(self):
        parser = ProjectParser()
        result = parser.parse_document("project_proposal", "test", upload_time="2024-01-01T00:00:00")
        assert result["upload_time"] == "2024-01-01T00:00:00"


class TestProjectParserBatchOperations:
    """Test batch parsing and document map building."""

    def test_parse_documents_batch(self):
        parser = ProjectParser()
        docs = [
            {"doc_type": "project_proposal", "content": "项目名称：A项目", "project_id": 1},
            {"doc_type": "contract", "content": "合同编号：HT-001", "project_id": 1},
        ]
        results = parser.parse_documents(docs)

        assert len(results) == 2
        assert results[0]["project_id"] == 1
        assert results[1]["doc_type"] == "contract"

    def test_build_document_map_full_coverage(self):
        parser = ProjectParser()
        docs = [
            {"doc_type": "project_proposal", "content": "项目名称：A"},
            {"doc_type": "feasibility_study", "content": "可研报告"},
            {"doc_type": "meeting_minutes", "content": "会议纪要"},
            {"doc_type": "contract", "content": "合同"},
            {"doc_type": "payment", "content": "付款"},
            {"doc_type": "acceptance", "content": "验收"},
        ]
        doc_map = parser.build_document_map(1, docs)

        assert doc_map["coverage"]["has_proposal"] is True
        assert doc_map["coverage"]["has_feasibility"] is True
        assert doc_map["coverage"]["has_minutes"] is True
        assert doc_map["coverage"]["has_contract"] is True
        assert doc_map["coverage"]["has_payment"] is True
        assert doc_map["coverage"]["has_acceptance"] is True
        assert len(doc_map["missing_docs"]) == 0

    def test_build_document_map_partial_coverage(self):
        parser = ProjectParser()
        docs = [
            {"doc_type": "project_proposal", "content": "项目名称：A"},
        ]
        doc_map = parser.build_document_map(1, docs)

        assert doc_map["coverage"]["has_proposal"] is True
        assert doc_map["coverage"]["has_feasibility"] is False
        assert len(doc_map["missing_docs"]) > 0


class TestParseProjectDocsTopLevel:
    """Test the top-level parse_project_docs function."""

    def test_parse_project_docs_function(self):
        docs = [
            {"doc_type": "project_proposal", "content": "项目名称：测试"},
        ]
        result = parse_project_docs(1, docs)

        assert result["project_id"] == 1
        assert "documents" in result
        assert "coverage" in result

    def test_parse_project_docs_empty(self):
        result = parse_project_docs(1, [])
        assert result["project_id"] == 1
        assert len(result["documents"]) == 0
