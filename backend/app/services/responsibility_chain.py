# backend/app/services/responsibility_chain.py
"""
责任链图谱
建立决策人、审批人、执行人、供应商关系图
关联关系可视化
"""
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime


class ResponsibilityChainBuilder:
    """责任链图谱构建器"""

    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_index = {}

    def build_chain(self, project_id: int,
                    project_data: Dict,
                    user_defined_nodes: List[Dict] = None,
                    user_defined_edges: List[Dict] = None) -> Dict[str, Any]:
        """
        构建责任链图谱
        """
        self.nodes = []
        self.edges = []
        self.node_index = {}

        result = {
            "project_id": project_id,
            "nodes": [],
            "edges": [],
            "metadata": {
                "total_nodes": 0,
                "total_edges": 0,
                "decision_makers": [],
                "executors": [],
                "suppliers": [],
                "risk_nodes": [],
            },
        }

        # 1. 从项目数据提取节点
        self._extract_nodes_from_project(project_data)

        # 2. 添加用户定义的节点
        if user_defined_nodes:
            for node in user_defined_nodes:
                self._add_node(node)

        # 3. 构建关系边
        self._build_default_edges(project_data)

        # 4. 添加用户定义的边
        if user_defined_edges:
            for edge in user_defined_edges:
                self._add_edge(edge)

        # 5. 检测关联风险
        risk_nodes = self._detect_risk_nodes()
        result["metadata"]["risk_nodes"] = risk_nodes

        result["nodes"] = self.nodes
        result["edges"] = self.edges
        result["metadata"]["total_nodes"] = len(self.nodes)
        result["metadata"]["total_edges"] = len(self.edges)

        return result

    def _extract_nodes_from_project(self, project_data: Dict):
        """从项目数据提取节点"""
        # 项目本身作为根节点
        self._add_node({
            "id": f"project_{project_data.get('id', 0)}",
            "name": project_data.get("project_name", "未知项目"),
            "role": "project",
            "department": project_data.get("department", ""),
            "type": "entity",
        })

        # 决策链节点
        decision_chain = project_data.get("decision_chain", [])
        for node in decision_chain:
            self._add_node({
                "id": node.get("node_id", node.get("id", f"node_{len(self.nodes)}")),
                "name": node.get("name", node.get("approver", "未知人员")),
                "role": node.get("node_type", "unknown"),
                "department": node.get("department", ""),
                "type": "person" if node.get("approver") else "entity",
            })

        # 文档关联人员
        docs = project_data.get("documents", [])
        for doc in docs:
            doc_type = doc.get("doc_type", "")
            if doc_type in ["meeting_minutes", "contract"]:
                # 从文档内容提取签名人
                content = doc.get("content", "")
                signers = self._extract_signers(content)
                for signer in signers:
                    self._add_node({
                        "id": f"signer_{signer}",
                        "name": signer,
                        "role": "signer",
                        "department": "",
                        "type": "person",
                    })

        # 供应商节点（从合同）
        contracts = project_data.get("contracts", [])
        for contract in contracts:
            parties = contract.get("parties", "")
            if parties:
                party_list = parties.split(",")
                for party in party_list:
                    party = party.strip()
                    if party and len(party) > 1:
                        self._add_node({
                            "id": f"supplier_{party}",
                            "name": party,
                            "role": "supplier",
                            "department": "",
                            "type": "organization",
                        })

        # 财务相关节点
        payments = project_data.get("payments", [])
        for payment in payments:
            handler = payment.get("handler", payment.get("approver", ""))
            if handler:
                self._add_node({
                    "id": f"handler_{handler}",
                    "name": handler,
                    "role": "payment_handler",
                    "department": "财务部",
                    "type": "person",
                })

        # 验收节点
        acceptances = project_data.get("acceptances", [])
        for acceptance in acceptances:
            inspector = acceptance.get("inspector", acceptance.get("approver", ""))
            if inspector:
                self._add_node({
                    "id": f"inspector_{inspector}",
                    "name": inspector,
                    "role": "inspector",
                    "department": "质量部",
                    "type": "person",
                })

    def _extract_signers(self, content: str) -> List[str]:
        """从文档内容提取签收人"""
        import re
        signers = []
        patterns = [
            r"[签字签名]{2}[人：:]\s*(\S+)",
            r"签[字名]{1}[人：:]\s*(\S+)",
            r"[审定审核]{2}[人：:]\s*(\S+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, content)
            signers.extend(matches)
        return signers

    def _add_node(self, node: Dict):
        """添加节点（去重）"""
        node_id = node.get("id")
        if not node_id:
            return

        if node_id in self.node_index:
            return  # 已存在，跳过

        # 标准化节点数据
        std_node = {
            "id": node_id,
            "name": node.get("name", ""),
            "role": node.get("role", "unknown"),
            "department": node.get("department", ""),
            "type": node.get("type", "person"),
        }
        self.nodes.append(std_node)
        self.node_index[node_id] = std_node

    def _add_edge(self, edge: Dict):
        """添加边"""
        from_id = edge.get("from") or edge.get("source")
        to_id = edge.get("to") or edge.get("target")
        if not from_id or not to_id:
            return

        # 确保节点存在
        if from_id not in self.node_index:
            self._add_node({"id": from_id, "name": from_id, "role": "unknown", "type": "person"})
        if to_id not in self.node_index:
            self._add_node({"id": to_id, "name": to_id, "role": "unknown", "type": "person"})

        std_edge = {
            "from": from_id,
            "to": to_id,
            "relation": edge.get("relation", edge.get("type", "related")),
            "weight": edge.get("weight", 1.0),
        }
        self.edges.append(std_edge)

    def _build_default_edges(self, project_data: Dict):
        """构建默认关系边"""
        project_node_id = f"project_{project_data.get('id', 0)}"

        # 决策链顺序边
        decision_chain = project_data.get("decision_chain", [])
        prev_node_id = project_node_id
        for node in decision_chain:
            node_id = node.get("node_id", node.get("id", f"node_{len(self.nodes)}"))
            self._add_edge({
                "from": prev_node_id,
                "to": node_id,
                "relation": "initiated_by",
            })
            prev_node_id = node_id

        # 合同-供应商边
        contracts = project_data.get("contracts", [])
        for contract in contracts:
            parties = contract.get("parties", "")
            if parties:
                party_list = parties.split(",")
                for party in party_list:
                    party = party.strip()
                    if party:
                        self._add_edge({
                            "from": project_node_id,
                            "to": f"supplier_{party}",
                            "relation": "contracted_with",
                        })

        # 付款-财务处理人边
        payments = project_data.get("payments", [])
        for payment in payments:
            handler = payment.get("handler", payment.get("approver", ""))
            if handler:
                self._add_edge({
                    "from": project_node_id,
                    "to": f"handler_{handler}",
                    "relation": "payment_processed_by",
                })

        # 验收-质检人边
        acceptances = project_data.get("acceptances", [])
        for acceptance in acceptances:
            inspector = acceptance.get("inspector", acceptance.get("approver", ""))
            if inspector:
                self._add_edge({
                    "from": project_node_id,
                    "to": f"inspector_{inspector}",
                    "relation": "acceptance_inspected_by",
                })

    def _detect_risk_nodes(self) -> List[Dict]:
        """检测风险节点"""
        risk_nodes = []

        # 检测同一部门多人
        dept_counts = {}
        for node in self.nodes:
            dept = node.get("department", "")
            if dept:
                dept_counts[dept] = dept_counts.get(dept, 0) + 1

        for node in self.nodes:
            dept = node.get("department", "")
            if dept and dept_counts.get(dept, 0) > 3:
                risk_nodes.append({
                    "node_id": node["id"],
                    "name": node["name"],
                    "risk_type": "concentrated_control",
                    "risk_desc": f"部门'{dept}'集中多人参与，可能存在利益关联",
                })

        # 检测关键角色缺失
        critical_roles = ["decision_maker", "approver", "supervisor"]
        existing_roles = set(n.get("role") for n in self.nodes)
        for role in critical_roles:
            if role not in existing_roles:
                risk_nodes.append({
                    "node_id": "unknown",
                    "name": "未知",
                    "risk_type": "missing_critical_role",
                    "risk_desc": f"缺少关键角色: {role}",
                })

        return risk_nodes

    def get_chain_visualization(self, chain_data: Dict) -> Dict[str, Any]:
        """获取可视化数据"""
        return {
            "nodes": [
                {
                    "id": n["id"],
                    "label": n["name"],
                    "group": n["type"],
                    "role": n["role"],
                }
                for n in chain_data.get("nodes", [])
            ],
            "edges": [
                {
                    "from": e["from"],
                    "to": e["to"],
                    "label": e.get("relation", ""),
                }
                for e in chain_data.get("edges", [])
            ],
        }


def build_responsibility_chain(project_id: int,
                                 project_data: Dict,
                                 nodes: List[Dict] = None,
                                 edges: List[Dict] = None) -> Dict[str, Any]:
    """构建责任链图谱顶层接口"""
    builder = ResponsibilityChainBuilder()
    return builder.build_chain(project_id, project_data, nodes, edges)