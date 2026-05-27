# backend/app/services/report_generator.py
"""
整改闭环报告生成
生成问题清单、责任节点、整改建议
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class ReportGenerator:
    """整改闭环报告生成器"""

    def __init__(self):
        self.report_sections = [
            "executive_summary",
            "project_overview",
            "compliance_check_results",
            "risk_analysis",
            "triple_match_results",
            "responsibility_chain",
            "issues_list",
            "rectification_plan",
            "appendices",
        ]

    def generate_comprehensive_report(self, project_id: int,
                                       project_data: Dict,
                                       risk_result: Dict,
                                       triple_match_result: Dict,
                                       decision_check_result: Dict,
                                       responsibility_chain: Dict) -> Dict[str, Any]:
        """
        生成完整合规审查报告
        """
        report = {
            "report_id": f"REPORT_{project_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "project_id": project_id,
            "generated_at": datetime.now().isoformat(),
            "sections": {},
        }

        # 1. 执行摘要
        report["sections"]["executive_summary"] = self._generate_executive_summary(
            project_data, risk_result, triple_match_result, decision_check_result
        )

        # 2. 项目概况
        report["sections"]["project_overview"] = self._generate_project_overview(project_data)

        # 3. 合规检查结果
        report["sections"]["compliance_check_results"] = self._generate_compliance_results(
            decision_check_result
        )

        # 4. 风险分析
        report["sections"]["risk_analysis"] = self._generate_risk_section(risk_result)

        # 5. 三单匹配结果
        report["sections"]["triple_match_results"] = self._generate_triple_match_section(
            triple_match_result
        )

        # 6. 责任链图谱
        report["sections"]["responsibility_chain"] = self._generate_chain_section(
            responsibility_chain
        )

        # 7. 问题清单
        report["sections"]["issues_list"] = self._generate_issues_list(
            risk_result, triple_match_result, decision_check_result
        )

        # 8. 整改计划
        report["sections"]["rectification_plan"] = self._generate_rectification_plan(
            risk_result, triple_match_result, decision_check_result
        )

        # 9. 附录
        report["sections"]["appendices"] = self._generate_appendices(project_data)

        return report

    def _generate_executive_summary(self, project_data: Dict,
                                     risk_result: Dict,
                                     triple_match_result: Dict,
                                     decision_check_result: Dict) -> Dict[str, Any]:
        """生成执行摘要"""
        risk_level = risk_result.get("risk_level", "unknown")
        total_score = risk_result.get("total_score", 0)

        issues_count = len(risk_result.get("risk_factors", []))
        critical_issues = sum(1 for f in risk_result.get("risk_factors", [])
                            if f.get("severity") == "critical")
        high_issues = sum(1 for f in risk_result.get("risk_factors", [])
                        if f.get("severity") == "high")

        is_compliant = decision_check_result.get("is_compliant", True) if decision_check_result else True
        is_matched = triple_match_result.get("is_matched", True) if triple_match_result else True

        summary = {
            "project_name": project_data.get("project_name", ""),
            "investment_amount": project_data.get("investment_amount", 0),
            "overall_assessment": "合规" if (is_compliant and is_matched and risk_level == "low") else "存在风险",
            "risk_level": risk_level,
            "risk_score": total_score,
            "key_findings": [],
            "recommendations_summary": [],
        }

        # 关键发现
        if critical_issues > 0:
            summary["key_findings"].append(f"发现{critical_issues}项严重问题，需要立即处理")
        if high_issues > 0:
            summary["key_findings"].append(f"发现{high_issues}项高风险问题，需要重点关注")
        if not is_compliant:
            summary["key_findings"].append("三重一大决策程序存在缺陷")
        if not is_matched:
            summary["key_findings"].append("合同-付款-验收三单存在金额不一致")

        # 建议摘要
        if risk_level in ["critical", "high"]:
            summary["recommendations_summary"].append("建议暂停项目支付，全面核查后再说")
        elif risk_level == "medium":
            summary["recommendations_summary"].append("建议补充缺失程序，加强过程监控")
        else:
            summary["recommendations_summary"].append("项目风险可控，建议持续监控")

        return summary

    def _generate_project_overview(self, project_data: Dict) -> Dict[str, Any]:
        """生成项目概况"""
        return {
            "project_id": project_data.get("id", 0),
            "project_name": project_data.get("project_name", ""),
            "department": project_data.get("department", ""),
            "investment_amount": project_data.get("investment_amount", 0),
            "project_type": project_data.get("project_type", ""),
            "status": project_data.get("status", "pending"),
            "created_at": project_data.get("created_at", ""),
        }

    def _generate_compliance_results(self, decision_check: Dict) -> Dict[str, Any]:
        """生成合规检查结果"""
        if not decision_check:
            return {"status": "not_checked", "message": "未进行合规检查"}

        return {
            "status": "compliant" if decision_check.get("is_compliant") else "non_compliant",
            "is_triple_one": decision_check.get("is_triple_one", False),
            "required_procedures": decision_check.get("required_procedures", []),
            "missing_procedures": decision_check.get("missing_procedures", []),
            "issues": decision_check.get("issues", []),
            "recommendations": decision_check.get("recommendations", []),
        }

    def _generate_risk_section(self, risk_result: Dict) -> Dict[str, Any]:
        """生成风险分析章节"""
        return {
            "total_score": risk_result.get("total_score", 0),
            "risk_level": risk_result.get("risk_level", "unknown"),
            "dimensions": {
                "process_risk": risk_result.get("process_risk", 0),
                "capital_risk": risk_result.get("capital_risk", 0),
                "related_risk": risk_result.get("related_risk", 0),
                "responsibility_risk": risk_result.get("responsibility_risk", 0),
            },
            "risk_factors": risk_result.get("risk_factors", []),
        }

    def _generate_triple_match_section(self, triple_match: Dict) -> Dict[str, Any]:
        """生成三单匹配章节"""
        if not triple_match:
            return {"status": "not_checked"}

        return {
            "status": triple_match.get("overall_status", "unknown"),
            "is_matched": triple_match.get("is_matched", True),
            "contract_count": triple_match.get("contract_count", 0),
            "payment_count": triple_match.get("payment_count", 0),
            "acceptance_count": triple_match.get("acceptance_count", 0),
            "mismatches": triple_match.get("mismatches", []),
            "warnings": triple_match.get("warnings", []),
            "risk_score": triple_match.get("risk_score", 0),
        }

    def _generate_chain_section(self, chain: Dict) -> Dict[str, Any]:
        """生成责任链章节"""
        if not chain:
            return {"status": "not_built"}

        return {
            "status": "built",
            "total_nodes": chain.get("metadata", {}).get("total_nodes", 0),
            "total_edges": chain.get("metadata", {}).get("total_edges", 0),
            "decision_makers": chain.get("metadata", {}).get("decision_makers", []),
            "executors": chain.get("metadata", {}).get("executors", []),
            "suppliers": chain.get("metadata", {}).get("suppliers", []),
            "risk_nodes": chain.get("metadata", {}).get("risk_nodes", []),
        }

    def _generate_issues_list(self, risk_result: Dict,
                                triple_match: Dict,
                                decision_check: Dict) -> List[Dict]:
        """生成问题清单"""
        issues = []

        # 风险因子问题
        for factor in risk_result.get("risk_factors", []):
            issues.append({
                "id": f"ISSUE_{len(issues)+1}",
                "dimension": factor.get("dimension", ""),
                "code": factor.get("code", ""),
                "severity": factor.get("severity", "medium"),
                "description": factor.get("description", ""),
                "source": "risk_analysis",
            })

        # 三单匹配问题
        for mismatch in triple_match.get("mismatches", []) if triple_match else []:
            issues.append({
                "id": f"ISSUE_{len(issues)+1}",
                "dimension": "capital",
                "code": mismatch.get("code", "RULE_SOE_005"),
                "severity": "high",
                "description": f"{mismatch.get('type', '')}: {mismatch.get('deviation_pct', 0):.2f}%",
                "source": "triple_match",
            })

        # 决策合规问题
        for issue in decision_check.get("issues", []) if decision_check else []:
            issues.append({
                "id": f"ISSUE_{len(issues)+1}",
                "dimension": "process",
                "code": issue.get("code", ""),
                "severity": issue.get("severity", "medium"),
                "description": issue.get("message", ""),
                "source": "compliance_check",
            })

        # 按严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))

        return issues

    def _generate_rectification_plan(self, risk_result: Dict,
                                       triple_match: Dict,
                                       decision_check: Dict) -> List[Dict]:
        """生成整改计划"""
        plans = []

        # 根据风险因子生成整改计划
        for factor in risk_result.get("risk_factors", []):
            dimension = factor.get("dimension", "")
            code = factor.get("code", "")

            plan = {
                "id": f"PLAN_{len(plans)+1}",
                "dimension": dimension,
                "issue_code": code,
                "severity": factor.get("severity", "medium"),
                "rectification_action": "",
                "responsible_party": "",
                "deadline": "",
                "status": "pending",
            }

            # 根据维度生成具体整改措施
            if dimension == "process":
                if code == "RULE_SOE_001":
                    plan["rectification_action"] = "补充立项文件和可行性研究报告"
                    plan["responsible_party"] = "项目发起部门"
                    plan["deadline"] = "5个工作日内"
                elif code == "RULE_SOE_002":
                    plan["rectification_action"] = "补充三重一大决策会议纪要和批复文件"
                    plan["responsible_party"] = "综合管理部"
                    plan["deadline"] = "3个工作日内"
                elif "MISSING" in code:
                    plan["rectification_action"] = f"补充缺失的决策程序: {code.replace('MISSING_', '')}"
                    plan["responsible_party"] = "综合管理部"
                    plan["deadline"] = "5个工作日内"
            elif dimension == "capital":
                if code == "RULE_SOE_005":
                    plan["rectification_action"] = "核查合同、付款、验收三单金额差异原因，补充说明或更正"
                    plan["responsible_party"] = "财务部"
                    plan["deadline"] = "7个工作日内"
            elif dimension == "related":
                if code == "RULE_SOE_006":
                    plan["rectification_action"] = "补充关联交易披露和审批文件，或提供非关联说明"
                    plan["responsible_party"] = "综合管理部"
                    plan["deadline"] = "10个工作日内"
            elif dimension == "responsibility":
                if code == "RULE_SOE_007":
                    plan["rectification_action"] = "明确各节点责任人，补充责任追溯链"
                    plan["responsible_party"] = "人力资源部"
                    plan["deadline"] = "5个工作日内"

            plans.append(plan)

        # 从决策检查建议生成整改计划
        if decision_check:
            for rec in decision_check.get("recommendations", []):
                plans.append({
                    "id": f"PLAN_{len(plans)+1}",
                    "dimension": "process",
                    "issue_code": "COMPLIANCE_REC",
                    "severity": "medium",
                    "rectification_action": rec,
                    "responsible_party": "相关部门",
                    "deadline": "按建议执行",
                    "status": "pending",
                })

        return plans

    def _generate_appendices(self, project_data: Dict) -> Dict[str, Any]:
        """生成附录"""
        return {
            "document_list": [
                {"doc_type": d.get("doc_type", ""), "upload_time": d.get("upload_time", "")}
                for d in project_data.get("documents", [])
            ],
            "contract_summary": {
                "count": len(project_data.get("contracts", [])),
                "total_amount": sum(c.get("amount", 0) for c in project_data.get("contracts", [])),
            },
            "payment_summary": {
                "count": len(project_data.get("payments", [])),
                "total_amount": sum(p.get("amount", 0) for p in project_data.get("payments", [])),
            },
            "acceptance_summary": {
                "count": len(project_data.get("acceptances", [])),
                "total_amount": sum(a.get("amount", 0) for a in project_data.get("acceptances", [])),
            },
        }

    def export_to_markdown(self, report: Dict) -> str:
        """导出为Markdown格式"""
        md = []
        md.append(f"# 国企经营投资合规审查报告")
        md.append(f"\n**报告编号**: {report.get('report_id', '')}")
        md.append(f"**生成时间**: {report.get('generated_at', '')}")
        md.append(f"**项目编号**: {report.get('project_id', '')}")

        # 执行摘要
        summary = report.get("sections", {}).get("executive_summary", {})
        md.append("\n## 一、执行摘要")
        md.append(f"- **项目名称**: {summary.get('project_name', '')}")
        md.append(f"- **投资金额**: {summary.get('investment_amount', 0):,.2f} 元")
        md.append(f"- **综合评估**: {summary.get('overall_assessment', '')}")
        md.append(f"- **风险等级**: {summary.get('risk_level', '')}")
        md.append(f"- **风险评分**: {summary.get('risk_score', 0)}")

        # 问题清单
        issues = report.get("sections", {}).get("issues_list", [])
        md.append(f"\n## 二、问题清单 (共{len(issues)}项)")
        for issue in issues:
            md.append(f"- **[{issue.get('severity', '').upper()}]** {issue.get('code', '')}: {issue.get('description', '')}")

        # 整改计划
        plans = report.get("sections", {}).get("rectification_plan", [])
        md.append(f"\n## 三、整改计划 (共{len(plans)}项)")
        for plan in plans:
            md.append(f"\n### {plan.get('id')}: {plan.get('rectification_action', '')}")
            md.append(f"- 责任部门: {plan.get('responsible_party', '')}")
            md.append(f"- 完成期限: {plan.get('deadline', '')}")
            md.append(f"- 状态: {plan.get('status', '')}")

        return "\n".join(md)


def generate_rectification_report(project_id: int,
                                   project_data: Dict,
                                   risk_result: Dict,
                                   triple_match_result: Dict,
                                   decision_check_result: Dict,
                                   responsibility_chain: Dict) -> Dict[str, Any]:
    """生成整改闭环报告顶层接口"""
    generator = ReportGenerator()
    return generator.generate_comprehensive_report(
        project_id, project_data, risk_result,
        triple_match_result, decision_check_result, responsibility_chain
    )