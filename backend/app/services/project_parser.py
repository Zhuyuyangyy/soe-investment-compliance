# backend/app/services/project_parser.py
"""
项目资料解析服务
解析立项、可研、会议纪要、合同、付款、验收材料
虚拟文档坐标映射
"""
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class ProjectParser:
    """项目资料解析器"""

    DOC_TYPE_PATTERNS = {
        "project_proposal": ["立项", "项目建议书", "项目申报"],
        "feasibility_study": ["可研", "可行性研究", "可行性分析"],
        "meeting_minutes": ["会议纪要", "党委会", "董事会", "总经理办公会"],
        "contract": ["合同", "协议", "采购合同", "施工合同"],
        "payment": ["付款", "支付", "发票", "记账"],
        "acceptance": ["验收", "竣工验收", "完工验收", "交付"],
    }

    KEY_FIELD_PATTERNS = {
        "project_proposal": {
            "project_name": [r"项目名称[：:]\s*(.+)",
                           r"项目名称\s+(.+)",
                           r"项目\s*名称[：:]\s*(.+)"],
            "investment_amount": [r"投资[额度]*[：:]\s*(\d+[\.,]?\d*)\s*(?:万|元|万元)",
                                 r"总投资[：:]\s*(\d+[\.,]?\d*)"],
            "department": [r"责任部门[：:]\s*(.+)",
                          r"申报单位[：:]\s*(.+)",
                          r"建设单位[：:]\s*(.+)"],
        },
        "feasibility_study": {
            "project_name": [r"项目名称[：:]\s*(.+)"],
            "investment_amount": [r"投资估算[：:]\s*(\d+[\.,]?\d*)\s*(?:万|元|万元)",
                                 r"总投资[：:]\s*(\d+[\.,]?\d*)"],
            "roi": [r"投资回报率[：:]\s*(\d+[\.,]?\d*)%",
                   r"ROI[：:]\s*(\d+[\.,]?\d*)%"],
        },
        "meeting_minutes": {
            "meeting_type": [r"(?:党委会|董事会|总经理办公会|办公会)\s*(?:会议)?纪要"],
            "attendees": [r"参会[人员]*[：:]\s*(.+)",
                         r"出席[人员]*[：:]\s*(.+)"],
            "decision": [r"(?:研究|审议|决定|同意|批准)[：:]\s*(.+)"],
        },
        "contract": {
            "contract_no": [r"合同编号[：:]\s*(\S+)",
                           r"合同号[：:]\s*(\S+)"],
            "amount": [r"合同金额[：:]\s*(\d+[\.,]?\d*)\s*(?:万|元|万元)?"],
            "parties": [r"甲方[：:]\s*(.+?)(?:乙方|$)",
                       r"乙方[：:]\s*(.+?)(?:丙方|$)"],
        },
        "payment": {
            "payment_no": [r"付款编号[：:]\s*(\S+)",
                          r"支付号[：:]\s*(\S+)"],
            "amount": [r"付款金额[：:]\s*(\d+[\.,]?\d*)\s*(?:万|元|万元)?"],
            "invoice_no": [r"发票号[：:]\s*(\S+)",
                          r"发票号码[：:]\s*(\S+)"],
        },
        "acceptance": {
            "acceptance_no": [r"验收编号[：:]\s*(\S+)",
                             r"验收单号[：:]\s*(\S+)"],
            "amount": [r"验收金额[：:]\s*(\d+[\.,]?\d*)\s*(?:万|元|万元)?"],
            "result": [r"验收结果[：:]\s*(合格|通过|不合格|需整改)"],
        },
    }

    def __init__(self):
        self.documents = []

    def parse_document(self, doc_type: str, content: str, upload_time: str = None) -> Dict[str, Any]:
        """解析单个文档"""
        doc_info = {
            "doc_type": doc_type,
            "upload_time": upload_time or datetime.now().isoformat(),
            "raw_content": content,
            "extracted_fields": {},
            "virtual_coords": {},
            "issues": [],
        }

        # 字段提取
        field_patterns = self.KEY_FIELD_PATTERNS.get(doc_type, {})
        for field, patterns in field_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    doc_info["extracted_fields"][field] = match.group(1).strip()
                    break

        # 虚拟文档坐标映射
        doc_info["virtual_coords"] = self._generate_virtual_coords(doc_type, content)

        # 问题检测
        doc_info["issues"] = self._detect_issues(doc_type, content, doc_info["extracted_fields"])

        return doc_info

    def _generate_virtual_coords(self, doc_type: str, content: str) -> Dict[str, Any]:
        """生成虚拟文档坐标"""
        lines = content.split("\n")
        coords = {
            "line_count": len(lines),
            "char_count": len(content),
            "sections": [],
        }

        # 识别文档章节
        section_pattern = r"^第[一二三四五六七八九十\d]+[章节条款]|\n#{1,3}\s+"
        section_matches = list(re.finditer(section_pattern, content))
        for m in section_matches:
            coords["sections"].append({
                "position": m.start(),
                "title": content[m.start():m.start()+50].strip()
            })

        return coords

    def _detect_issues(self, doc_type: str, content: str, extracted: Dict) -> List[Dict]:
        """检测文档问题"""
        issues = []

        if doc_type == "project_proposal":
            if not extracted.get("investment_amount"):
                issues.append({"code": "MISSING_AMOUNT", "severity": "high",
                              "message": "项目建议书缺少投资金额"})
            if not extracted.get("department"):
                issues.append({"code": "MISSING_DEPT", "severity": "medium",
                              "message": "项目建议书缺少责任部门"})

        elif doc_type == "feasibility_study":
            if not extracted.get("investment_amount"):
                issues.append({"code": "MISSING_INVESTMENT", "severity": "critical",
                              "message": "可研报告缺少投资估算"})

        elif doc_type == "meeting_minutes":
            if "同意" not in content and "批准" not in content and "通过" not in content:
                issues.append({"code": "NO_DECISION", "severity": "high",
                              "message": "会议纪要无明确决策结论"})

        elif doc_type == "contract":
            if not extracted.get("amount"):
                issues.append({"code": "MISSING_CONTRACT_AMOUNT", "severity": "critical",
                              "message": "合同缺少金额条款"})

        return issues

    def parse_documents(self, docs: List[Dict]) -> List[Dict]:
        """批量解析文档"""
        results = []
        for doc in docs:
            parsed = self.parse_document(
                doc.get("doc_type", "unknown"),
                doc.get("content", ""),
                doc.get("upload_time")
            )
            parsed["project_id"] = doc.get("project_id")
            results.append(parsed)
        return results

    def build_document_map(self, project_id: int, docs: List[Dict]) -> Dict[str, Any]:
        """构建项目文档映射图"""
        doc_map = {
            "project_id": project_id,
            "documents": self.parse_documents(docs),
            "coverage": {
                "has_proposal": False,
                "has_feasibility": False,
                "has_minutes": False,
                "has_contract": False,
                "has_payment": False,
                "has_acceptance": False,
            },
            "missing_docs": [],
        }

        type_mapping = {
            "project_proposal": "has_proposal",
            "feasibility_study": "has_feasibility",
            "meeting_minutes": "has_minutes",
            "contract": "has_contract",
            "payment": "has_payment",
            "acceptance": "has_acceptance",
        }

        for doc in doc_map["documents"]:
            key = type_mapping.get(doc["doc_type"])
            if key:
                doc_map["coverage"][key] = True

        # 检查缺失文档
        for key, val in doc_map["coverage"].items():
            if not val:
                doc_type = key.replace("has_", "").replace("_", " ")
                doc_map["missing_docs"].append(doc_type)

        return doc_map


def parse_project_docs(project_id: int, docs: List[Dict]) -> Dict[str, Any]:
    """解析项目全部文档（顶层接口）"""
    parser = ProjectParser()
    return parser.build_document_map(project_id, docs)