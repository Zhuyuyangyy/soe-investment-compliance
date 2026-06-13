"""
Tests for API routes - Integration tests using FastAPI TestClient.
Covers: health check, project CRUD, document upload, contract/payment/acceptance registration,
        triple match, responsibility chain, analysis, audit logs.
"""
import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def registered_project(client):
    """Register a project and return its data."""
    response = client.post("/api/register_project", json={
        "project_name": "测试投资项目",
        "department": "投资部",
        "investment_amount": 5000000,
    })
    assert response.status_code == 200
    return response.json()


class TestHealthCheck:
    """Test health endpoint."""

    def test_health_returns_ok(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


class TestProjectRegistration:
    """Test project registration."""

    def test_register_project(self, client):
        response = client.post("/api/register_project", json={
            "project_name": "新建项目A",
            "department": "技术部",
            "investment_amount": 1000000,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == "新建项目A"
        assert data["status"] == "pending"

    def test_register_project_minimal(self, client):
        response = client.post("/api/register_project", json={
            "project_name": "最小项目",
        })
        assert response.status_code == 200

    def test_list_projects(self, client, registered_project):
        response = client.get("/api/list_projects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_get_project(self, client, registered_project):
        project_id = registered_project["id"]
        response = client.get(f"/api/get_project/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == "测试投资项目"

    def test_get_nonexistent_project(self, client):
        response = client.get("/api/get_project/99999")
        assert response.status_code == 404


class TestDocumentUpload:
    """Test document upload."""

    def test_upload_document(self, client, registered_project):
        project_id = registered_project["id"]
        response = client.post("/api/upload_document", json={
            "project_id": project_id,
            "doc_type": "project_proposal",
            "content": "项目名称：测试项目\n投资额度：500万元\n责任部门：投资部",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "document_id" in data
        assert "extracted_fields" in data

    def test_upload_meeting_minutes(self, client, registered_project):
        project_id = registered_project["id"]
        response = client.post("/api/upload_document", json={
            "project_id": project_id,
            "doc_type": "meeting_minutes",
            "content": "董事会会议纪要\n参会人员：张三\n研究决定：同意立项",
        })
        assert response.status_code == 200


class TestContractRegistration:
    """Test contract registration."""

    def test_register_contract(self, client, registered_project):
        project_id = registered_project["id"]
        response = client.post("/api/register_contract", json={
            "project_id": project_id,
            "contract_no": "HT-2024-001",
            "amount": 5000000,
            "signing_date": "2024-01-15",
            "parties": "甲方公司,乙方公司",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "contract_id" in data


class TestPaymentRegistration:
    """Test payment registration."""

    def test_register_payment(self, client, registered_project):
        project_id = registered_project["id"]
        response = client.post("/api/register_payment", json={
            "project_id": project_id,
            "payment_no": "FK-001",
            "amount": 2500000,
            "payment_date": "2024-02-01",
            "invoice_no": "FP-001",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestAcceptanceRegistration:
    """Test acceptance registration."""

    def test_register_acceptance(self, client, registered_project):
        project_id = registered_project["id"]
        response = client.post("/api/register_acceptance", json={
            "project_id": project_id,
            "acceptance_no": "YS-001",
            "amount": 5000000,
            "acceptance_date": "2024-06-01",
            "result": "合格",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestTripleMatch:
    """Test triple match checking via API."""

    def test_check_triple_match(self, client, registered_project):
        project_id = registered_project["id"]

        # Register contract, payment, acceptance
        client.post("/api/register_contract", json={
            "project_id": project_id, "amount": 5000000, "contract_no": "C1",
        })
        client.post("/api/register_payment", json={
            "project_id": project_id, "amount": 5000000, "payment_no": "P1",
        })
        client.post("/api/register_acceptance", json={
            "project_id": project_id, "amount": 5000000, "acceptance_no": "A1",
        })

        response = client.post("/api/check_triple_match", json={
            "project_id": project_id,
        })
        assert response.status_code == 200
        data = response.json()
        assert "is_matched" in data
        assert "overall_status" in data


class TestResponsibilityChain:
    """Test responsibility chain building via API."""

    def test_build_chain(self, client, registered_project):
        project_id = registered_project["id"]
        response = client.post("/api/build_responsibility_chain", json={
            "project_id": project_id,
            "nodes": [],
            "edges": [],
        })
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    def test_build_chain_nonexistent_project(self, client):
        response = client.post("/api/build_responsibility_chain", json={
            "project_id": 99999,
            "nodes": [],
            "edges": [],
        })
        assert response.status_code == 404


class TestProjectAnalysis:
    """Test full project analysis via API."""

    def test_analyze_project(self, client, registered_project):
        project_id = registered_project["id"]

        # Upload some documents first
        client.post("/api/upload_document", json={
            "project_id": project_id,
            "doc_type": "project_proposal",
            "content": "项目名称：测试项目\n投资额度：500万元",
        })

        response = client.post(f"/api/analyze_project?project_id={project_id}")
        assert response.status_code == 200
        data = response.json()
        assert "risk_result" in data
        assert "triple_match_result" in data
        assert "decision_check" in data
        assert "responsibility_chain" in data
        assert "report" in data

    def test_analyze_nonexistent_project(self, client):
        response = client.post("/api/analyze_project?project_id=99999")
        assert response.status_code == 404


class TestRiskReport:
    """Test risk report retrieval."""

    def test_get_risk_report_after_analysis(self, client, registered_project):
        project_id = registered_project["id"]
        client.post(f"/api/analyze_project?project_id={project_id}")

        response = client.get(f"/api/get_risk_report/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert "risk_level" in data

    def test_get_risk_report_no_analysis(self, client, registered_project):
        project_id = registered_project["id"]
        response = client.get(f"/api/get_risk_report/{project_id}")
        assert response.status_code == 404


class TestAuditLogs:
    """Test audit log retrieval."""

    def test_audit_logs_recorded(self, client, registered_project):
        response = client.get("/api/audit_logs")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "logs" in data
        assert data["total"] >= 1

    def test_audit_logs_limit(self, client, registered_project):
        response = client.get("/api/audit_logs?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) <= 1
