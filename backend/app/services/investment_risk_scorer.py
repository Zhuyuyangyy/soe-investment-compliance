# backend/app/services/investment_risk_scorer.py
"""
投资风险熵评分
输出流程风险、资金风险、关联风险、责任风险
多维风险耦合模型
"""
import json
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class InvestmentRiskScorer:
    """投资风险熵评分器"""

    def __init__(self):
        # 风险维度权重
        self.weights = {
            "process_risk": 0.30,      # 流程风险
            "capital_risk": 0.35,      # 资金风险
            "related_risk": 0.20,      # 关联风险
            "responsibility_risk": 0.15,  # 责任风险
        }

        # 风险等级阈值
        self.risk_thresholds = {
            "low": 30,
            "medium": 60,
            "high": 80,
            "critical": 100,
        }

    def calculate_risk_entropy(self, project_id: int,
                                project_data: Dict,
                                triple_match_result: Dict = None,
                                decision_check_result: Dict = None,
                                responsibility_chain: Dict = None) -> Dict[str, Any]:
        """
        计算投资风险熵
        多维风险耦合模型
        """
        result = {
            "project_id": project_id,
            "total_score": 0.0,
            "risk_level": "low",
            "process_risk": 0.0,
            "capital_risk": 0.0,
            "related_risk": 0.0,
            "responsibility_risk": 0.0,
            "risk_factors": [],
            "risk_entropy_detail": {},
        }

        # 1. 计算流程风险
        result["process_risk"] = self._calculate_process_risk(
            project_data, decision_check_result
        )

        # 2. 计算资金风险
        result["capital_risk"] = self._calculate_capital_risk(
            project_data, triple_match_result
        )

        # 3. 计算关联风险
        result["related_risk"] = self._calculate_related_risk(
            project_data, responsibility_chain
        )

        # 4. 计算责任风险
        result["responsibility_risk"] = self._calculate_responsibility_risk(
            project_data, responsibility_chain
        )

        # 5. 加权汇总
        total = (
            result["process_risk"] * self.weights["process_risk"] +
            result["capital_risk"] * self.weights["capital_risk"] +
            result["related_risk"] * self.weights["related_risk"] +
            result["responsibility_risk"] * self.weights["responsibility_risk"]
        )
        result["total_score"] = round(min(100.0, total), 2)

        # 6. 确定风险等级
        result["risk_level"] = self._get_risk_level(result["total_score"])

        # 7. 提取风险因子
        result["risk_factors"] = self._extract_risk_factors(
            project_data, triple_match_result, decision_check_result, responsibility_chain
        )

        # 8. 风险熵详情
        result["risk_entropy_detail"] = {
            "dimensions": {
                "process": {
                    "score": result["process_risk"],
                    "weight": self.weights["process_risk"],
                    "contribution": result["process_risk"] * self.weights["process_risk"],
                },
                "capital": {
                    "score": result["capital_risk"],
                    "weight": self.weights["capital_risk"],
                    "contribution": result["capital_risk"] * self.weights["capital_risk"],
                },
                "related": {
                    "score": result["related_risk"],
                    "weight": self.weights["related_risk"],
                    "contribution": result["related_risk"] * self.weights["related_risk"],
                },
                "responsibility": {
                    "score": result["responsibility_risk"],
                    "weight": self.weights["responsibility_risk"],
                    "contribution": result["responsibility_risk"] * self.weights["responsibility_risk"],
                },
            },
            "entropy_calculation": "weighted_sum",
        }

        return result

    def _calculate_process_risk(self, project_data: Dict,
                                  decision_check: Dict = None) -> float:
        """计算流程风险"""
        risk_score = 0.0

        # 检查文档完整性
        doc_types = set(d.get("doc_type") for d in project_data.get("documents", []))
        required_docs = ["project_proposal", "feasibility_study", "contract"]
        missing_count = sum(1 for d in required_docs if d not in doc_types)
        risk_score += missing_count * 15

        # 使用决策检查结果
        if decision_check:
            if not decision_check.get("is_compliant", True):
                risk_score += 40
            missing_procs = len(decision_check.get("missing_procedures", []))
            risk_score += missing_procs * 10

        # 检查决策链
        decision_chain = project_data.get("decision_chain", [])
        if not decision_chain:
            risk_score += 25
        elif len(decision_chain) < 3:
            risk_score += 10

        # 检查会议纪要
        has_minutes = any("meeting_minutes" in d.get("doc_type", "") for d in project_data.get("documents", []))
        if not has_minutes:
            risk_score += 20

        return min(100.0, risk_score)

    def _calculate_capital_risk(self, project_data: Dict,
                                 triple_match: Dict = None) -> float:
        """计算资金风险"""
        risk_score = 0.0

        investment_amount = project_data.get("investment_amount", 0)

        # 投资金额越大，风险贡献越高
        if investment_amount >= 10000000:  # 1000万以上
            risk_score += 25
        elif investment_amount >= 5000000:  # 500万以上
            risk_score += 15
        else:
            risk_score += 5

        # 使用三单匹配结果
        if triple_match:
            mismatches = triple_match.get("mismatches", [])
            risk_score += len(mismatches) * 15

            mismatch_amount = triple_match.get("details", {}).get("mismatch_amount_sum", 0)
            if mismatch_amount > 0:
                ratio = mismatch_amount / investment_amount if investment_amount > 0 else 0
                risk_score += min(30, ratio * 100)

        # 检查付款记录
        payments = project_data.get("payments", [])
        if not payments and investment_amount > 0:
            risk_score += 20

        return min(100.0, risk_score)

    def _calculate_related_risk(self, project_data: Dict,
                                 chain: Dict = None) -> float:
        """计算关联风险（关联交易风险）"""
        risk_score = 0.0

        # 检查供应商关联
        contracts = project_data.get("contracts", [])
        project_dept = project_data.get("department", "")

        for contract in contracts:
            parties = contract.get("parties", "")
            # 检测潜在关联交易关键词
            related_keywords = ["集团", "关联", "子公司", "兄弟公司", "实际控制"]
            for kw in related_keywords:
                if kw in parties:
                    risk_score += 30
                    break

            # 检测供应商与项目部门的关联
            if any(dept in parties for dept in [project_dept]):
                risk_score += 25

        # 检查责任链中的关联
        if chain:
            nodes = chain.get("nodes", [])
            # 检测同一人员多重角色
            node_roles = {}
            for node in nodes:
                name = node.get("name", "")
                role = node.get("role", "")
                if name and role:
                    key = f"{name}_{role}"
                    if key in node_roles:
                        risk_score += 20
                    node_roles[key] = True

        return min(100.0, risk_score)

    def _calculate_responsibility_risk(self, project_data: Dict,
                                        chain: Dict = None) -> float:
        """计算责任风险"""
        risk_score = 0.0

        # 检测责任链完整性
        if not chain:
            risk_score += 40
        else:
            nodes = chain.get("nodes", [])
            edges = chain.get("edges", [])

            # 节点太少
            if len(nodes) < 3:
                risk_score += 25

            # 边太少（关系不完整）
            if len(edges) < len(nodes) - 1:
                risk_score += 20

        # 检测关键角色缺失
        decision_chain = project_data.get("decision_chain", [])
        approvers = [n.get("approver") for n in decision_chain if n.get("approver")]
        if not approvers:
            risk_score += 30

        # 检测责任追溯困难（RULE_SOE_007）
        docs = project_data.get("documents", [])
        for doc in docs:
            content = doc.get("content", "")
            if "免责" in content or "责任豁免" in content:
                risk_score += 25

        # 检测审批流程不完整
        has_approval = any("approval" in d.get("doc_type", "") for d in docs)
        if not has_approval:
            risk_score += 15

        return min(100.0, risk_score)

    def _get_risk_level(self, score: float) -> str:
        """根据分数确定风险等级"""
        if score >= self.risk_thresholds["critical"]:
            return "critical"
        elif score >= self.risk_thresholds["high"]:
            return "high"
        elif score >= self.risk_thresholds["medium"]:
            return "medium"
        else:
            return "low"

    def _extract_risk_factors(self, project_data: Dict,
                               triple_match: Dict = None,
                               decision_check: Dict = None,
                               chain: Dict = None) -> List[Dict]:
        """提取风险因子"""
        factors = []

        # 流程风险因子
        if decision_check:
            for issue in decision_check.get("issues", []):
                factors.append({
                    "dimension": "process",
                    "code": issue.get("code", "UNKNOWN"),
                    "severity": issue.get("severity", "medium"),
                    "description": issue.get("message", ""),
                })

        # 资金风险因子
        if triple_match:
            for mismatch in triple_match.get("mismatches", []):
                factors.append({
                    "dimension": "capital",
                    "code": mismatch.get("code", "RULE_SOE_005"),
                    "severity": "high",
                    "description": f"金额偏差: {mismatch.get('deviation_pct', 0):.2f}%",
                })
            for warning in triple_match.get("warnings", []):
                factors.append({
                    "dimension": "capital",
                    "code": warning.get("code", ""),
                    "severity": warning.get("severity", "medium"),
                    "description": warning.get("message", ""),
                })

        # 关联风险因子
        contracts = project_data.get("contracts", [])
        for contract in contracts:
            parties = contract.get("parties", "")
            related_keywords = ["集团", "关联", "子公司"]
            for kw in related_keywords:
                if kw in parties:
                    factors.append({
                        "dimension": "related",
                        "code": "RULE_SOE_006",
                        "severity": "critical",
                        "description": f"检测到潜在关联交易: {parties}",
                    })
                    break

        # 责任风险因子
        if chain:
            for risk_node in chain.get("metadata", {}).get("risk_nodes", []):
                factors.append({
                    "dimension": "responsibility",
                    "code": "RULE_SOE_007",
                    "severity": risk_node.get("risk_type", "medium"),
                    "description": risk_node.get("risk_desc", ""),
                })

        return factors

    def generate_risk_radar_data(self, risk_result: Dict) -> Dict[str, Any]:
        """生成风险雷达图数据"""
        return {
            "dimensions": [
                {"axis": "流程风险", "value": risk_result.get("process_risk", 0)},
                {"axis": "资金风险", "value": risk_result.get("capital_risk", 0)},
                {"axis": "关联风险", "value": risk_result.get("related_risk", 0)},
                {"axis": "责任风险", "value": risk_result.get("responsibility_risk", 0)},
            ],
            "total_score": risk_result.get("total_score", 0),
            "risk_level": risk_result.get("risk_level", "low"),
        }


def calculate_investment_risk(project_id: int,
                               project_data: Dict,
                               triple_match_result: Dict = None,
                               decision_check_result: Dict = None,
                               responsibility_chain: Dict = None) -> Dict[str, Any]:
    """计算投资风险熵顶层接口"""
    scorer = InvestmentRiskScorer()
    return scorer.calculate_risk_entropy(
        project_id, project_data,
        triple_match_result, decision_check_result, responsibility_chain
    )