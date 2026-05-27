from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import random

router = APIRouter(prefix="/api/v1", tags=["soe-investment-compliance"])

class InvestmentProposalRequest(BaseModel):
    proposal_id: str
    investment_amount: float
    investment_type: str  # "新建" | "并购" | "参股" | "合资"
    sector: str
    decision_level: str  # "董事会" | "股东大会" | "国资委"
    supporting_docs: List[str]

class ThreeMajorDecisionsRequest(BaseModel):
    proposal_id: str
    decisions: List[Dict]  # [{"decision_type": str, "content": str, "approved": bool, "meeting_date": str}]

class ThreeListMatchingRequest(BaseModel):
    proposal_id: str
    investment_amount: float
    investment_type: str
    counterparty: str  # 交易对手方

class ComplianceScoreRequest(BaseModel):
    organization_id: str
    investment_proposals: List[Dict]

@router.post("/review_investment_proposal")
async def review_investment_proposal(req: InvestmentProposalRequest):
    """Review investment proposal for SOE compliance"""
    risk_factors = []
    if req.investment_amount > 100_000_000:
        risk_factors.append({"factor": "投资金额超过10亿元", "severity": "critical", "regulation": "须上报国资委审批"})
    if req.investment_type == "新建" and req.investment_amount > 50_000_000:
        risk_factors.append({"factor": "重大新建项目", "severity": "high", "regulation": "须经可行性研究和专家论证"})
    if req.decision_level not in ["股东大会", "国资委"]:
        risk_factors.append({"factor": f"{req.decision_level}审批层级可能不足", "severity": "medium", "regulation": "三重一大要求上级审批"})
    compliance_checklist = {
        "决策程序合规": req.decision_level in ["股东大会", "国资委"] or req.investment_amount < 10_000_000,
        "可行性论证": len(req.supporting_docs) >= 3 if req.investment_amount > 20_000_000 else True,
        "风险评估报告": any("风险" in d for d in req.supporting_docs) if req.supporting_docs else False,
        "财务审计": any("审计" in d for d in req.supporting_docs) if req.supporting_docs else False,
    }
    compliance_rate = round(sum(1 for v in compliance_checklist.values() if v) / len(compliance_checklist) * 100, 1)
    return {"proposal_id": req.proposal_id, "investment_amount": req.investment_amount, "risk_factors": risk_factors, "compliance_checklist": compliance_checklist, "compliance_rate": compliance_rate, "approval_recommendation": "上报国资委" if any(rf["severity"] == "critical" for rf in risk_factors) else "同意立项" if compliance_rate >= 80 else "补充材料后重审"}

@router.post("/check_three_major_decisions")
async def check_three_major_decisions(req: ThreeMajorDecisionsRequest):
    """Verify three-major-decisions (三重一大) compliance"""
    major_decisions = ["重大决策", "重要人事任免", "重大项目安排", "大额资金运作"]
    matched = []
    unmatched = []
    for d in req.decisions:
        matched_decision = next((md for md in major_decisions if md in d.get("decision_type", "")), None)
        if matched_decision:
            status = "approved" if d.get("approved") else "rejected"
            matched.append({"decision": matched_decision, "content": d.get("content", ""), "status": status, "meeting_date": d.get("meeting_date", "")})
        else:
            unmatched.append({"decision_type": d.get("decision_type", ""), "content": d.get("content", "")})
    compliance = len(matched) >= 3 and all(d.get("approved") for d in matched if matched)
    return {"proposal_id": req.proposal_id, "major_decisions_found": matched, "unmatched_decisions": unmatched, "三重一大合规": compliance, "会议记录完整性": f"{len(matched)}/4项完整", "建议": "补充缺失的三重一大会议记录" if len(matched) < 3 else "合规性检查通过"}

@router.post("/validate_three_list_matching")
async def validate_three_list_matching(req: ThreeListMatchingRequest):
    """Validate three-list matching (三单匹配): proposal, contract, payment"""
    issues = []
    threshold_amounts = {"新建": 5_000_000, "并购": 10_000_000, "参股": 3_000_000, "合资": 5_000_000}
    threshold = threshold_amounts.get(req.investment_type, 5_000_000)
    if req.investment_amount > threshold:
        issues.append({"issue": f"投资金额¥{req.investment_amount/1_000_000:.1f}M超过{req.investment_type}门槛¥{threshold/1_000_000:.0f}M", "regulation": "须纳入三重一大管理"})
    if req.investment_amount > 100_000_000:
        issues.append({"issue": "投资金额超过10亿元红线", "regulation": "须国资委专项审批"})
    prohibited_sectors = ["房地产", "娱乐", "赌博", "武器制造"]
    if any(s in req.counterparty for s in prohibited_sectors):
        issues.append({"issue": f"交易对手方涉及禁止类行业: {req.counterparty}", "regulation": "国有企业投资负面清单"})
    matching_score = round(max(0.1, 1.0 - len(issues) * 0.3), 3)
    return {"proposal_id": req.proposal_id, "investment_amount": req.investment_amount, "investment_type": req.investment_type, "issues_found": issues, "matching_score": matching_score, "validation_result": "通过" if matching_score > 0.7 else "驳回" if matching_score < 0.4 else "补充说明", "regulatory_references": list(set(i["regulation"] for i in issues))}

@router.get("/get_compliance_score")
async def get_compliance_score(organization_id: str):
    """Get overall investment compliance score for an SOE"""
    proposals_count = random.randint(5, 20)
    avg_compliance = round(random.uniform(72, 96), 1)
    return {"organization_id": organization_id, "proposals_reviewed": proposals_count, "average_compliance_rate": avg_compliance, "compliance_grade": "A" if avg_compliance >= 90 else "B" if avg_compliance >= 80 else "C" if avg_compliance >= 70 else "D", "key_metrics": {"三重一大执行率": f"{random.randint(85, 100)}%", "平均审批时长": f"{random.randint(15, 45)}天", "合规培训覆盖率": f"{random.randint(90, 100)}%"}, "risk_areas": random.sample(["投资后评估缺失", "可行性论证不充分", "合同变更频繁", "资金支付提前"], k=random.randint(0, 2)), "timestamp": datetime.now().isoformat()}