# backend/app/services/decision_checker.py
"""
三重一大流程校验
检查重大事项决策流程是否完整
决策程序合法性检测
"""
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class DecisionChecker:
    """三重一大决策流程校验器"""

    # 三重一大涉及的事项类型
    TRIPLE_ONE_LARGE_TYPES = [
        "重大事项", "重要项目", "大额资金", "重要人事",
        "重大投资", "重大资产", "大额采购", "重大合同"
    ]

    # 决策程序要求
    DECISION_PROCEDURES = {
        "budget_above_500w": {
            "threshold": 5000000,  # 500万以上
            "require_board": True,
            "require_feasibility": True,
            "require_competition": True,
        },
        "budget_above_1000w": {
            "threshold": 10000000,  # 1000万以上
            "require_party_committee": True,
            "require_board": True,
            "require_feasibility": True,
            "require_competition": True,
            "require_supervision": True,
        },
        "major_asset_transfer": {
            "require_valuation": True,
            "require_competition": True,
            "require_approval": True,
        },
    }

    # 必需决策节点
    REQUIRED_DECISION_NODES = [
        "initiation",      # 发起
        "feasibility",     # 可研论证
        "review",          # 审核
        "decision",        # 决策
        "implementation",   # 实施
    ]

    def __init__(self):
        self.issues = []

    def check_triple_one_compliance(self, project_data: Dict) -> Dict[str, Any]:
        """检测三重一大合规性"""
        self.issues = []
        result = {
            "is_compliant": True,
            "risk_level": "low",
            "issues": [],
            "required_procedures": [],
            "missing_procedures": [],
            "recommendations": [],
        }

        investment_amount = project_data.get("investment_amount", 0)
        doc_map = project_data.get("document_map", {})

        # 1. 判断是否属于三重一大范畴
        is_triple_one = self._is_triple_one_item(project_data)
        result["is_triple_one"] = is_triple_one

        if not is_triple_one:
            return result

        result["is_compliant"] = False  # 默认不合规，需要验证
        result["risk_level"] = "high"

        # 2. 确定需要的决策程序
        required_procs = self._determine_required_procedures(investment_amount, project_data)
        result["required_procedures"] = required_procs

        # 3. 检查已执行的决策程序
        for proc in required_procs:
            if not self._procedure_completed(proc, doc_map):
                result["missing_procedures"].append(proc)
                self._add_issue(proc)

        # 4. 检查决策链完整性
        decision_chain = project_data.get("decision_chain", [])
        chain_issues = self._check_decision_chain(decision_chain, required_procs)
        result["issues"].extend(chain_issues)

        # 5. 决策合规性校验
        compliance_issues = self._check_decision_compliance(project_data, decision_chain)
        result["issues"].extend(compliance_issues)

        # 6. 生成整改建议
        result["recommendations"] = self._generate_recommendations(result)

        if result["missing_procedures"] or result["issues"]:
            result["is_compliant"] = False
        else:
            result["is_compliant"] = True
            result["risk_level"] = "low"

        return result

    def _is_triple_one_item(self, project_data: Dict) -> bool:
        """判断是否属于三重一大事项"""
        investment_amount = project_data.get("investment_amount", 0)
        project_name = project_data.get("project_name", "")
        doc_types = project_data.get("doc_types", [])

        # 金额阈值判断
        if investment_amount >= 5000000:
            return True

        # 关键词判断
        triple_one_keywords = [
            "投资", "采购", "建设", "工程", "资产", "股权",
            "并购", "转让", "出租", "对外", "重大", "重要"
        ]
        for kw in triple_one_keywords:
            if kw in project_name:
                return True

        # 文档类型判断
        critical_docs = ["meeting_minutes", "board_resolution", "party_committee"]
        for doc_type in doc_types:
            if doc_type in critical_docs:
                return True

        return False

    def _determine_required_procedures(self, investment_amount: float, project_data: Dict) -> List[str]:
        """确定所需的决策程序"""
        procedures = []

        if investment_amount >= 10000000:  # 1000万以上
            procedures.extend([
                "feasibility_study",
                "party_committee_review",
                "board_resolution",
                "supervision_committee_review",
                "public_disclosure",
            ])
        elif investment_amount >= 5000000:  # 500万以上
            procedures.extend([
                "feasibility_study",
                "management_review",
                "board_resolution",
            ])
        else:
            procedures.extend([
                "feasibility_study",
                "management_review",
            ])

        # 特殊类型检查
        project_type = project_data.get("project_type", "")
        if "采购" in project_type or "采购" in project_data.get("project_name", ""):
            procedures.append("procurement_competition")
        if "工程" in project_type or "建设" in project_type:
            procedures.append("engineering_approval")

        return procedures

    def _procedure_completed(self, procedure: str, doc_map: Dict) -> bool:
        """检查某项程序是否已完成"""
        procedure_doc_map = {
            "feasibility_study": ["feasibility_study"],
            "party_committee_review": ["meeting_minutes_party"],
            "board_resolution": ["meeting_minutes_board", "board_resolution"],
            "management_review": ["meeting_minutes"],
            "supervision_committee_review": ["supervision_report"],
            "public_disclosure": ["disclosure_record"],
            "procurement_competition": ["bidding_doc", "bidding_result"],
            "engineering_approval": ["engineering_approval_doc"],
        }

        required_docs = procedure_doc_map.get(procedure, [])
        coverage = doc_map.get("coverage", {})

        for doc_key in required_docs:
            for key, val in coverage.items():
                if doc_key in key and val:
                    return True

        return False

    def _check_decision_chain(self, chain: List[Dict], required_procs: List[str]) -> List[Dict]:
        """检查决策链完整性"""
        issues = []

        if not chain:
            issues.append({
                "code": "NO_DECISION_CHAIN",
                "severity": "critical",
                "message": "项目缺少完整的决策链记录",
            })
            return issues

        # 检查关键节点
        chain_nodes = [node.get("node_type") for node in chain]
        critical_nodes = ["decision", "approval"]

        for node in critical_nodes:
            if node not in chain_nodes:
                issues.append({
                    "code": f"MISSING_{node.upper()}",
                    "severity": "high",
                    "message": f"决策链缺少关键节点: {node}",
                })

        # 检查时间顺序
        for i in range(len(chain) - 1):
            t1 = chain[i].get("timestamp")
            t2 = chain[i+1].get("timestamp")
            if t1 and t2 and t1 > t2:
                issues.append({
                    "code": "CHRONOLOGY_VIOLATION",
                    "severity": "critical",
                    "message": "决策顺序违反时间先后",
                })

        return issues

    def _check_decision_compliance(self, project_data: Dict, decision_chain: List[Dict]) -> List[Dict]:
        """检查决策合规性"""
        issues = []

        # 检查决策依据
        docs = project_data.get("documents", [])
        has_feasibility = any(d.get("doc_type") == "feasibility_study" for d in docs)
        has_proposal = any(d.get("doc_type") == "project_proposal" for d in docs)

        if not has_proposal:
            issues.append({
                "code": "RULE_SOE_001",
                "severity": "high",
                "message": "投资决策依据不足，缺少立项文件",
            })

        if not has_feasibility:
            issues.append({
                "code": "MISSING_FEASIBILITY",
                "severity": "high",
                "message": "缺少可行性研究报告",
            })

        # 检查决策程序
        meeting_count = sum(1 for d in docs if "meeting_minutes" in d.get("doc_type", ""))
        if meeting_count < 1:
            issues.append({
                "code": "RULE_SOE_002",
                "severity": "critical",
                "message": "三重一大决策程序缺失，缺少会议纪要",
            })

        # 检查决策参与人
        for node in decision_chain:
            if not node.get("approver"):
                issues.append({
                    "code": "MISSING_APPROVER",
                    "severity": "medium",
                    "message": f"决策节点 {node.get('node_type')} 缺少审批人",
                })

        return issues

    def _add_issue(self, procedure: str):
        """添加问题"""
        issue_map = {
            "feasibility_study": {"code": "MISSING_FEASIBILITY", "severity": "high"},
            "party_committee_review": {"code": "MISSING_PARTY_REVIEW", "severity": "critical"},
            "board_resolution": {"code": "MISSING_BOARD_RESOLUTION", "severity": "critical"},
            "management_review": {"code": "MISSING_MANAGEMENT_REVIEW", "severity": "medium"},
            "supervision_committee_review": {"code": "MISSING_SUPERVISION", "severity": "medium"},
            "public_disclosure": {"code": "MISSING_DISCLOSURE", "severity": "medium"},
            "procurement_competition": {"code": "RULE_SOE_004", "severity": "high"},
            "engineering_approval": {"code": "MISSING_ENGINEERING_APPROVAL", "severity": "high"},
        }

        info = issue_map.get(procedure, {"code": "UNKNOWN", "severity": "medium"})
        self.issues.append({
            "code": info["code"],
            "severity": info["severity"],
            "message": f"缺少必要程序: {procedure}",
        })

    def _generate_recommendations(self, result: Dict) -> List[str]:
        """生成整改建议"""
        recs = []

        if "feasibility_study" in result.get("missing_procedures", []):
            recs.append("补充编制可行性研究报告并经相应层级审批")
        if "party_committee_review" in result.get("missing_procedures", []):
            recs.append("补充召开党委会进行前置研究讨论")
        if "board_resolution" in result.get("missing_procedures", []):
            recs.append("补充召开董事会进行正式决议")
        if "procurement_competition" in result.get("missing_procedures", []):
            recs.append("补充履行招标采购程序或申请单一来源审批")

        if not recs:
            recs.append("项目决策程序基本完整，建议持续监控实施过程")

        return recs


def check_triple_one_compliance(project_data: Dict) -> Dict[str, Any]:
    """三重一大合规检测顶层接口"""
    checker = DecisionChecker()
    return checker.check_triple_one_compliance(project_data)