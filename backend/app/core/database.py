# backend/app/core/database.py
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "soe_investment_compliance.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
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

    # Insert default rules if not exist
    default_rules = [
        ("RULE_SOE_001", "investment_decision", "投资决策依据不足，未提供可研报告或批复文件", "high", "责令补充资料，暂停支付"),
        ("RULE_SOE_002", "triple_one_large", "三重一大决策程序缺失或不合规", "critical", "责令整改，追究责任"),
        ("RULE_SOE_003", "contract_amount", "合同金额与预算或可研偏差超过20%", "medium", "要求说明原因"),
        ("RULE_SOE_004", "procurement", "采购流程不合规，未按规定招标", "high", "重新履行采购程序"),
        ("RULE_SOE_005", "triple_match", "合同-付款-验收三单金额不一致", "high", "暂停支付，彻查"),
        ("RULE_SOE_006", "related_party", "存在关联交易但未披露或披露不实", "critical", "移送纪检监察"),
        ("RULE_SOE_007", "responsibility_trace", "责任主体不明确，追溯困难", "medium", "明确责任人"),
    ]
    for r in default_rules:
        cur.execute("INSERT OR IGNORE INTO rules (rule_id, rule_type, description, severity, penalty) VALUES (?, ?, ?, ?, ?)", r)

    conn.commit()
    conn.close()