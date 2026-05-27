# backend/app/services/triple_match_checker.py
"""
合同-付款-验收三单匹配检测
检查合同金额、付款金额、验收金额是否一致
时间线一致性检测
"""
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class TripleMatchChecker:
    """三单匹配校验器"""

    def __init__(self):
        self.thresholds = {
            "amount_deviation_pct": 0.05,  # 金额偏差超过5%算异常
            "time_gap_months": 12,          # 单据时间间隔超过12个月算异常
        }

    def check_triple_match(self, project_id: int,
                           contracts: List[Dict],
                           payments: List[Dict],
                           acceptances: List[Dict]) -> Dict[str, Any]:
        """
        核心三单匹配检测
        """
        result = {
            "project_id": project_id,
            "is_matched": True,
            "overall_status": "normal",
            "contract_count": len(contracts),
            "payment_count": len(payments),
            "acceptance_count": len(acceptances),
            "matches": [],
            "mismatches": [],
            "warnings": [],
            "risk_score": 0.0,
            "details": {},
        }

        if not contracts:
            result["warnings"].append({"code": "NO_CONTRACT", "message": "项目无合同记录"})
            result["is_matched"] = False
            return result

        # 1. 金额匹配检测
        amount_result = self._check_amount_match(contracts, payments, acceptances)
        result["matches"].extend(amount_result["matched"])
        result["mismatches"].extend(amount_result["mismatched"])
        result["risk_score"] += amount_result["risk_contribution"]

        # 2. 时间线一致性检测
        timeline_result = self._check_timeline_consistency(contracts, payments, acceptances)
        result["warnings"].extend(timeline_result["warnings"])
        result["risk_score"] += timeline_result["risk_contribution"]

        # 3. 发票一致性检测
        invoice_result = self._check_invoice_consistency(payments, acceptances)
        result["warnings"].extend(invoice_result["warnings"])

        # 4. 汇总判断
        if result["mismatches"]:
            result["is_matched"] = False
            result["overall_status"] = "mismatch"
            result["details"]["mismatch_amount_sum"] = sum(
                m.get("deviation_amount", 0) for m in result["mismatches"]
            )
        if len(result["warnings"]) > 3:
            result["overall_status"] = "warning" if result["is_matched"] else result["overall_status"]

        # 风险评分标准化
        result["risk_score"] = min(100.0, result["risk_score"])

        return result

    def _check_amount_match(self, contracts: List[Dict], payments: List[Dict],
                            acceptances: List[Dict]) -> Dict[str, Any]:
        """检查金额匹配"""
        result = {
            "matched": [],
            "mismatched": [],
            "risk_contribution": 0.0,
        }

        contract_amounts = {c.get("id"): c.get("amount", 0) for c in contracts}
        payment_amounts = {p.get("id"): p.get("amount", 0) for p in payments}
        acceptance_amounts = {a.get("id"): a.get("amount", 0) for a in acceptances}

        # 计算总额
        total_contract = sum(contract_amounts.values())
        total_payment = sum(payment_amounts.values())
        total_acceptance = sum(acceptance_amounts.values())

        # 总体验证
        if total_contract > 0:
            payment_ratio = total_payment / total_contract
            acceptance_ratio = total_acceptance / total_contract

            if abs(payment_ratio - 1.0) > self.thresholds["amount_deviation_pct"]:
                result["mismatched"].append({
                    "type": "total_payment_vs_contract",
                    "contract_amount": total_contract,
                    "payment_amount": total_payment,
                    "deviation_pct": abs(payment_ratio - 1.0) * 100,
                    "deviation_amount": abs(total_payment - total_contract),
                    "code": "RULE_SOE_005",
                })
                result["risk_contribution"] += 30

            if abs(acceptance_ratio - 1.0) > self.thresholds["amount_deviation_pct"]:
                result["mismatched"].append({
                    "type": "total_acceptance_vs_contract",
                    "contract_amount": total_contract,
                    "acceptance_amount": total_acceptance,
                    "deviation_pct": abs(acceptance_ratio - 1.0) * 100,
                    "deviation_amount": abs(total_acceptance - total_contract),
                    "code": "RULE_SOE_005",
                })
                result["risk_contribution"] += 30

        # 两两对比检测
        for contract in contracts:
            c_amount = contract.get("amount", 0)
            c_no = contract.get("contract_no", str(contract.get("id")))

            for payment in payments:
                p_amount = payment.get("amount", 0)
                p_no = payment.get("payment_no", str(payment.get("id")))

                # 金额差异检测
                if c_amount > 0:
                    ratio = p_amount / c_amount
                    if ratio < 0.5 or ratio > 1.5:
                        result["mismatched"].append({
                            "type": "payment_contract_mismatch",
                            "contract_no": c_no,
                            "payment_no": p_no,
                            "contract_amount": c_amount,
                            "payment_amount": p_amount,
                            "deviation_pct": abs(ratio - 1.0) * 100,
                            "code": "RULE_SOE_005",
                        })
                        result["risk_contribution"] += 15

            for acceptance in acceptances:
                a_amount = acceptance.get("amount", 0)
                a_no = acceptance.get("acceptance_no", str(acceptance.get("id")))

                if c_amount > 0:
                    ratio = a_amount / c_amount
                    if ratio < 0.5 or ratio > 1.5:
                        result["mismatched"].append({
                            "type": "acceptance_contract_mismatch",
                            "contract_no": c_no,
                            "acceptance_no": a_no,
                            "contract_amount": c_amount,
                            "acceptance_amount": a_amount,
                            "deviation_pct": abs(ratio - 1.0) * 100,
                            "code": "RULE_SOE_005",
                        })
                        result["risk_contribution"] += 15

        if not result["mismatched"] and total_contract > 0:
            result["matched"].append({
                "type": "all_amounts_consistent",
                "contract_amount": total_contract,
                "payment_amount": total_payment,
                "acceptance_amount": total_acceptance,
            })

        return result

    def _check_timeline_consistency(self, contracts: List[Dict], payments: List[Dict],
                                    acceptances: List[Dict]) -> Dict[str, Any]:
        """检查时间线一致性"""
        result = {
            "warnings": [],
            "risk_contribution": 0.0,
        }

        def parse_date(date_str):
            if not date_str:
                return None
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m"]:
                try:
                    return datetime.strptime(str(date_str), fmt)
                except:
                    continue
            return None

        # 收集所有日期
        contract_dates = []
        payment_dates = []
        acceptance_dates = []

        for c in contracts:
            d = parse_date(c.get("signing_date", ""))
            if d:
                contract_dates.append((d, c.get("contract_no", str(c.get("id")))))

        for p in payments:
            d = parse_date(p.get("payment_date", ""))
            if d:
                payment_dates.append((d, p.get("payment_no", str(p.get("id")))))

        for a in acceptances:
            d = parse_date(a.get("acceptance_date", ""))
            if d:
                acceptance_dates.append((d, a.get("acceptance_no", str(a.get("id")))))

        # 检查顺序：合同 -> 付款 -> 验收
        if contract_dates and payment_dates:
            earliest_contract = min(d[0] for d in contract_dates)
            latest_payment = max(d[0] for d in payment_dates)
            if earliest_contract > latest_payment:
                result["warnings"].append({
                    "code": "PAYMENT_BEFORE_CONTRACT",
                    "severity": "high",
                    "message": "存在付款日期早于合同签订日期",
                })
                result["risk_contribution"] += 20

        if payment_dates and acceptance_dates:
            earliest_payment = min(d[0] for d in payment_dates)
            latest_acceptance = max(d[0] for d in acceptance_dates)
            # 验收应该在付款之后（如果是付款后验收的话）
            # 这里检查的是：如果有付款，验收不能太早
            pass

        # 时间间隔过长的警告
        if contract_dates and acceptance_dates:
            earliest_contract = min(d[0] for d in contract_dates)
            latest_acceptance = max(d[0] for d in acceptance_dates)
            gap_months = (latest_acceptance - earliest_contract).days / 30
            if gap_months > self.thresholds["time_gap_months"]:
                result["warnings"].append({
                    "code": "EXCESSIVE_TIME_GAP",
                    "severity": "medium",
                    "message": f"合同签订到验收完成间隔{gap_months:.1f}个月，超过正常范围",
                })
                result["risk_contribution"] += 10

        return result

    def _check_invoice_consistency(self, payments: List[Dict],
                                   acceptances: List[Dict]) -> Dict[str, Any]:
        """检查发票一致性"""
        result = {
            "warnings": [],
        }

        payment_invoices = {p.get("invoice_no") for p in payments if p.get("invoice_no")}
        payment_amounts = {p.get("invoice_no"): p.get("amount", 0)
                          for p in payments if p.get("invoice_no")}

        # 检查发票金额与付款金额一致性
        for payment in payments:
            invoice_no = payment.get("invoice_no")
            if not invoice_no:
                result["warnings"].append({
                    "code": "MISSING_INVOICE",
                    "severity": "medium",
                    "message": f"付款记录 {payment.get('id')} 缺少发票号",
                })
            else:
                p_amount = payment.get("amount", 0)
                if p_amount > 0 and invoice_no in payment_amounts:
                    # 同一发票多次付款检测
                    pass

        return result

    def generate_match_report(self, check_result: Dict) -> Dict[str, Any]:
        """生成三单匹配报告"""
        report = {
            "summary": {
                "total_contracts": check_result.get("contract_count", 0),
                "total_payments": check_result.get("payment_count", 0),
                "total_acceptances": check_result.get("acceptance_count", 0),
                "match_status": check_result.get("overall_status", "unknown"),
            },
            "amount_analysis": {
                "total_contract_amount": 0,
                "total_payment_amount": 0,
                "total_acceptance_amount": 0,
                "deviation": 0,
            },
            "issues": [],
            "recommendations": [],
        }

        # 计算汇总
        for match in check_result.get("matches", []):
            if match.get("type") == "all_amounts_consistent":
                report["amount_analysis"]["total_contract_amount"] = match.get("contract_amount", 0)
                report["amount_analysis"]["total_payment_amount"] = match.get("payment_amount", 0)
                report["amount_analysis"]["total_acceptance_amount"] = match.get("acceptance_amount", 0)

        for mismatch in check_result.get("mismatches", []):
            report["issues"].append({
                "code": mismatch.get("code", "UNKNOWN"),
                "type": mismatch.get("type", ""),
                "severity": "high",
                "message": f"{mismatch.get('type')}: 偏差{mismatch.get('deviation_pct', 0):.2f}%",
            })

        # 生成建议
        if check_result.get("mismatches"):
            report["recommendations"].append("立即暂停异常款项支付")
            report["recommendations"].append("核实合同、发票、验收单据真实性")
            report["recommendations"].append("补充说明金额差异原因")

        if len(check_result.get("warnings", [])) > 2:
            report["recommendations"].append("加强项目过程管理，规范单据归档")

        return report


def check_triple_match(project_id: int, contracts: List[Dict],
                       payments: List[Dict], acceptances: List[Dict]) -> Dict[str, Any]:
    """三单匹配检测顶层接口"""
    checker = TripleMatchChecker()
    return checker.check_triple_match(project_id, contracts, payments, acceptances)