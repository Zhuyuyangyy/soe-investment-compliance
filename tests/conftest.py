"""
Shared test fixtures for SOE Investment Compliance test suite.
"""
import os
import sys
import json
import sqlite3
import tempfile
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_compliance.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT UNIQUE NOT NULL,
            rule_type TEXT NOT NULL,
            description TEXT,
            severity TEXT NOT NULL,
            penalty TEXT,
            enabled INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            department TEXT,
            investment_amount REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            doc_type TEXT NOT NULL,
            content TEXT,
            upload_time TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            contract_no TEXT,
            amount REAL NOT NULL,
            signing_date TEXT,
            parties TEXT
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            payment_no TEXT,
            amount REAL NOT NULL,
            payment_date TEXT,
            invoice_no TEXT
        );
        CREATE TABLE IF NOT EXISTS acceptance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            acceptance_no TEXT,
            amount REAL NOT NULL,
            acceptance_date TEXT,
            result TEXT
        );
        CREATE TABLE IF NOT EXISTS responsibility_chain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            nodes_json TEXT,
            edges_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            risk_score REAL,
            risk_level TEXT,
            details_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "id": 1,
        "project_name": "新能源光伏发电项目",
        "department": "投资发展部",
        "investment_amount": 8000000,
        "status": "pending",
        "documents": [
            {
                "id": 1,
                "project_id": 1,
                "doc_type": "project_proposal",
                "content": "项目名称：新能源光伏发电项目\n投资额度：800万元\n责任部门：投资发展部",
                "upload_time": "2024-01-15T10:00:00",
            },
            {
                "id": 2,
                "project_id": 1,
                "doc_type": "feasibility_study",
                "content": "项目名称：新能源光伏发电项目\n投资估算：800万元\n投资回报率：15%",
                "upload_time": "2024-01-16T10:00:00",
            },
            {
                "id": 3,
                "project_id": 1,
                "doc_type": "meeting_minutes",
                "content": "董事会会议纪要\n参会人员：张三、李四、王五\n研究决定：同意新能源光伏发电项目立项",
                "upload_time": "2024-01-20T10:00:00",
            },
        ],
        "contracts": [
            {
                "id": 1,
                "project_id": 1,
                "contract_no": "HT-2024-001",
                "amount": 8000000,
                "signing_date": "2024-02-01",
                "parties": "国投集团,阳光新能源有限公司",
            }
        ],
        "payments": [
            {
                "id": 1,
                "project_id": 1,
                "payment_no": "FK-2024-001",
                "amount": 4000000,
                "payment_date": "2024-03-01",
                "invoice_no": "FP-2024-001",
            },
            {
                "id": 2,
                "project_id": 1,
                "payment_no": "FK-2024-002",
                "amount": 4000000,
                "payment_date": "2024-06-01",
                "invoice_no": "FP-2024-002",
            },
        ],
        "acceptances": [
            {
                "id": 1,
                "project_id": 1,
                "acceptance_no": "YS-2024-001",
                "amount": 8000000,
                "acceptance_date": "2024-12-01",
                "result": "合格",
            }
        ],
        "decision_chain": [
            {"node_id": "dc_1", "node_type": "initiation", "approver": "张三", "department": "投资发展部", "timestamp": "2024-01-10"},
            {"node_id": "dc_2", "node_type": "feasibility", "approver": "李四", "department": "技术部", "timestamp": "2024-01-15"},
            {"node_id": "dc_3", "node_type": "decision", "approver": "王五", "department": "董事会", "timestamp": "2024-01-20"},
            {"node_id": "dc_4", "node_type": "approval", "approver": "赵六", "department": "总经理办公会", "timestamp": "2024-01-25"},
        ],
        "doc_types": ["project_proposal", "feasibility_study", "meeting_minutes"],
    }


@pytest.fixture
def sample_contracts():
    """Sample contracts for testing."""
    return [
        {
            "id": 1,
            "project_id": 1,
            "contract_no": "HT-2024-001",
            "amount": 1000000,
            "signing_date": "2024-02-01",
            "parties": "甲方公司,乙方公司",
        }
    ]


@pytest.fixture
def sample_payments():
    """Sample payments for testing."""
    return [
        {
            "id": 1,
            "project_id": 1,
            "payment_no": "FK-2024-001",
            "amount": 1000000,
            "payment_date": "2024-03-01",
            "invoice_no": "FP-2024-001",
        }
    ]


@pytest.fixture
def sample_acceptances():
    """Sample acceptances for testing."""
    return [
        {
            "id": 1,
            "project_id": 1,
            "acceptance_no": "YS-2024-001",
            "amount": 1000000,
            "acceptance_date": "2024-12-01",
            "result": "合格",
        }
    ]


@pytest.fixture
def mismatch_contracts():
    """Contracts with mismatched amounts."""
    return [
        {"id": 1, "project_id": 1, "contract_no": "HT-001", "amount": 1000000, "signing_date": "2024-01-01", "parties": "A公司,B公司"},
    ]


@pytest.fixture
def mismatch_payments():
    """Payments with mismatched amounts."""
    return [
        {"id": 1, "project_id": 1, "payment_no": "FK-001", "amount": 500000, "payment_date": "2024-02-01", "invoice_no": "FP-001"},
    ]


@pytest.fixture
def mismatch_acceptances():
    """Acceptances with mismatched amounts."""
    return [
        {"id": 1, "project_id": 1, "acceptance_no": "YS-001", "amount": 2000000, "acceptance_date": "2024-03-01", "result": "合格"},
    ]
