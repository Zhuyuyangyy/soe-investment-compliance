# backend/app/api/routes.py
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..models.schemas import (
    ProjectCreate, ProjectResponse, DocumentUpload, ContractCreate,
    PaymentCreate, AcceptanceCreate, TripleMatchCheck, ResponsibilityChainBuild,
    RiskScoreResponse, AuditLogResponse
)
from ..core.database import get_conn, init_db
from ..services.project_parser import parse_project_docs, ProjectParser
from ..services.decision_checker import check_triple_one_compliance
from ..services.triple_match_checker import TripleMatchChecker
from ..services.responsibility_chain import build_responsibility_chain
from ..services.investment_risk_scorer import calculate_investment_risk
from ..services.report_generator import generate_rectification_report

router = APIRouter()

# Initialize DB on startup
init_db()


def log_audit(action: str, target_type: str = None, target_id: int = None, details: str = None):
    """记录审计日志"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audit_logs (action, target_type, target_id, details) VALUES (?, ?, ?, ?)",
            (action, target_type, target_id, details)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@router.post("/register_project", response_model=ProjectResponse)
async def register_project(project: ProjectCreate):
    """注册项目"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO projects (project_name, department, investment_amount, status) VALUES (?, ?, ?, ?)",
            (project.project_name, project.department, project.investment_amount, "pending")
        )
        conn.commit()
        project_id = cur.lastrowid

        log_audit("register_project", "project", project_id, f"Created project: {project.project_name}")

        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cur.to_dict(cur.fetchone())
        return row
    finally:
        conn.close()


@router.post("/upload_document")
async def upload_document(doc: DocumentUpload):
    """上传项目资料"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO documents (project_id, doc_type, content) VALUES (?, ?, ?)",
            (doc.project_id, doc.doc_type, doc.content)
        )
        conn.commit()
        doc_id = cur.lastrowid

        log_audit("upload_document", "document", doc_id, f"Uploaded {doc.doc_type} for project {doc.project_id}")

        # 解析文档内容
        parser = ProjectParser()
        parsed = parser.parse_document(doc.doc_type, doc.content)

        return {
            "status": "success",
            "document_id": doc_id,
            "extracted_fields": parsed.get("extracted_fields", {}),
            "issues": parsed.get("issues", []),
        }
    finally:
        conn.close()


@router.post("/register_contract")
async def register_contract(contract: ContractCreate):
    """登记合同"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO contracts (project_id, contract_no, amount, signing_date, parties) VALUES (?, ?, ?, ?, ?)",
            (contract.project_id, contract.contract_no, contract.amount, contract.signing_date, contract.parties)
        )
        conn.commit()
        contract_id = cur.lastrowid

        log_audit("register_contract", "contract", contract_id, f"Registered contract for project {contract.project_id}")

        return {"status": "success", "contract_id": contract_id}
    finally:
        conn.close()


@router.post("/register_payment")
async def register_payment(payment: PaymentCreate):
    """登记付款"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO payments (project_id, payment_no, amount, payment_date, invoice_no) VALUES (?, ?, ?, ?, ?)",
            (payment.project_id, payment.payment_no, payment.amount, payment.payment_date, payment.invoice_no)
        )
        conn.commit()
        payment_id = cur.lastrowid

        log_audit("register_payment", "payment", payment_id, f"Registered payment for project {payment.project_id}")

        return {"status": "success", "payment_id": payment_id}
    finally:
        conn.close()


@router.post("/register_acceptance")
async def register_acceptance(acceptance: AcceptanceCreate):
    """登记验收"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO acceptance (project_id, acceptance_no, amount, acceptance_date, result) VALUES (?, ?, ?, ?, ?)",
            (acceptance.project_id, acceptance.acceptance_no, acceptance.amount, acceptance.acceptance_date, acceptance.result)
        )
        conn.commit()
        acceptance_id = cur.lastrowid

        log_audit("register_acceptance", "acceptance", acceptance_id, f"Registered acceptance for project {acceptance.project_id}")

        return {"status": "success", "acceptance_id": acceptance_id}
    finally:
        conn.close()


@router.post("/check_triple_match")
async def check_triple_match(check: TripleMatchCheck):
    """三单匹配检测"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 获取合同
        cur.execute("SELECT * FROM contracts WHERE project_id = ?", (check.project_id,))
        contracts = [dict(row) for row in cur.fetchall()]

        # 获取付款
        cur.execute("SELECT * FROM payments WHERE project_id = ?", (check.project_id,))
        payments = [dict(row) for row in cur.fetchall()]

        # 获取验收
        cur.execute("SELECT * FROM acceptance WHERE project_id = ?", (check.project_id,))
        acceptances = [dict(row) for row in cur.fetchall()]

        # 执行三单匹配检测
        checker = TripleMatchChecker()
        result = checker.check_triple_match(check.project_id, contracts, payments, acceptances)

        log_audit("check_triple_match", "project", check.project_id, json.dumps(result, ensure_ascii=False))

        return result
    finally:
        conn.close()


@router.post("/build_responsibility_chain")
async def build_responsibility_chain_api(chain_data: ResponsibilityChainBuild):
    """构建责任链图谱"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 获取项目信息
        cur.execute("SELECT * FROM projects WHERE id = ?", (chain_data.project_id,))
        project_row = cur.fetchone()
        if not project_row:
            raise HTTPException(status_code=404, detail="Project not found")

        project_data = dict(project_row)

        # 获取文档
        cur.execute("SELECT * FROM documents WHERE project_id = ?", (chain_data.project_id,))
        project_data["documents"] = [dict(row) for row in cur.fetchall()]

        # 获取合同
        cur.execute("SELECT * FROM contracts WHERE project_id = ?", (chain_data.project_id,))
        project_data["contracts"] = [dict(row) for row in cur.fetchall()]

        # 获取付款
        cur.execute("SELECT * FROM payments WHERE project_id = ?", (chain_data.project_id,))
        project_data["payments"] = [dict(row) for row in cur.fetchall()]

        # 获取验收
        cur.execute("SELECT * FROM acceptance WHERE project_id = ?", (chain_data.project_id,))
        project_data["acceptances"] = [dict(row) for row in cur.fetchall()]

        # 构建责任链
        result = build_responsibility_chain(
            chain_data.project_id,
            project_data,
            chain_data.nodes,
            chain_data.edges
        )

        # 保存到数据库
        nodes_json = json.dumps(result.get("nodes", []), ensure_ascii=False)
        edges_json = json.dumps(result.get("edges", []), ensure_ascii=False)
        cur.execute(
            "INSERT INTO responsibility_chain (project_id, nodes_json, edges_json) VALUES (?, ?, ?)",
            (chain_data.project_id, nodes_json, edges_json)
        )
        conn.commit()

        log_audit("build_responsibility_chain", "project", chain_data.project_id, "Built responsibility chain")

        return result
    finally:
        conn.close()


@router.post("/analyze_project")
async def analyze_project(project_id: int):
    """分析项目合规性"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 获取项目信息
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project_row = cur.fetchone()
        if not project_row:
            raise HTTPException(status_code=404, detail="Project not found")

        project_data = dict(project_row)

        # 获取文档
        cur.execute("SELECT * FROM documents WHERE project_id = ?", (project_id,))
        project_data["documents"] = [dict(row) for row in cur.fetchall()]

        # 获取合同
        cur.execute("SELECT * FROM contracts WHERE project_id = ?", (project_id,))
        contracts = [dict(row) for row in cur.fetchall()]
        project_data["contracts"] = contracts

        # 获取付款
        cur.execute("SELECT * FROM payments WHERE project_id = ?", (project_id,))
        payments = [dict(row) for row in cur.fetchall()]
        project_data["payments"] = payments

        # 获取验收
        cur.execute("SELECT * FROM acceptance WHERE project_id = ?", (project_id,))
        acceptances = [dict(row) for row in cur.fetchall()]
        project_data["acceptances"] = acceptances

        # 解析文档
        doc_map = parse_project_docs(project_id, project_data["documents"])
        project_data["doc_types"] = [d.get("doc_type") for d in project_data["documents"]]

        # 执行三重一大检测
        decision_check = check_triple_one_compliance(project_data)

        # 执行三单匹配检测
        triple_match_checker = TripleMatchChecker()
        triple_match_result = triple_match_checker.check_triple_match(
            project_id, contracts, payments, acceptances
        )

        # 构建责任链
        chain_result = build_responsibility_chain(project_id, project_data)
        project_data["responsibility_chain"] = chain_result

        # 计算风险熵
        risk_result = calculate_investment_risk(
            project_id, project_data,
            triple_match_result, decision_check, chain_result
        )

        # 生成整改报告
        report = generate_rectification_report(
            project_id, project_data, risk_result,
            triple_match_result, decision_check, chain_result
        )

        # 保存分析结果
        details_json = json.dumps({
            "risk_result": risk_result,
            "triple_match": triple_match_result,
            "decision_check": decision_check,
        }, ensure_ascii=False)

        cur.execute(
            "INSERT INTO analysis_results (project_id, risk_score, risk_level, details_json) VALUES (?, ?, ?, ?)",
            (project_id, risk_result.get("total_score", 0), risk_result.get("risk_level", "unknown"), details_json)
        )
        conn.commit()

        log_audit("analyze_project", "project", project_id, f"Risk score: {risk_result.get('total_score', 0)}")

        return {
            "project_id": project_id,
            "risk_result": risk_result,
            "triple_match_result": triple_match_result,
            "decision_check": decision_check,
            "responsibility_chain": chain_result,
            "report": report,
        }
    finally:
        conn.close()


@router.get("/get_project/{project_id}")
async def get_project(project_id: int):
    """获取项目信息"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        project = dict(row)

        # 获取关联数据
        cur.execute("SELECT * FROM documents WHERE project_id = ?", (project_id,))
        project["documents"] = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM contracts WHERE project_id = ?", (project_id,))
        project["contracts"] = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM payments WHERE project_id = ?", (project_id,))
        project["payments"] = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM acceptance WHERE project_id = ?", (project_id,))
        project["acceptances"] = [dict(r) for r in cur.fetchall()]

        return project
    finally:
        conn.close()


@router.get("/get_risk_report/{project_id}")
async def get_risk_report(project_id: int):
    """获取风险报告"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM analysis_results WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
            (project_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No analysis result found")

        result = dict(row)
        result["details"] = json.loads(result.get("details_json", "{}"))
        return result
    finally:
        conn.close()


@router.get("/get_responsibility_chain/{project_id}")
async def get_responsibility_chain(project_id: int):
    """获取责任链图谱"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM responsibility_chain WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
            (project_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No responsibility chain found")

        result = dict(row)
        result["nodes"] = json.loads(result.get("nodes_json", "[]"))
        result["edges"] = json.loads(result.get("edges_json", "[]"))
        return result
    finally:
        conn.close()


@router.get("/audit_logs")
async def get_audit_logs(limit: int = 100):
    """获取审计日志"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [dict(row) for row in cur.fetchall()]
        return {"total": len(rows), "logs": rows}
    finally:
        conn.close()


@router.get("/list_projects")
async def list_projects():
    """获取项目列表"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = [dict(row) for row in cur.fetchall()]
        return {"total": len(rows), "projects": rows}
    finally:
        conn.close()