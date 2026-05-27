# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class ProjectCreate(BaseModel):
    project_name: str
    department: Optional[str] = None
    investment_amount: Optional[float] = None

class ProjectResponse(BaseModel):
    id: int
    project_name: str
    department: Optional[str]
    investment_amount: Optional[float]
    status: str
    created_at: str

class DocumentUpload(BaseModel):
    project_id: int
    doc_type: str  # project_proposal, feasibility_study, meeting_minutes, contract, payment, acceptance
    content: str

class ContractCreate(BaseModel):
    project_id: int
    contract_no: Optional[str] = None
    amount: float
    signing_date: Optional[str] = None
    parties: Optional[str] = None

class PaymentCreate(BaseModel):
    project_id: int
    payment_no: Optional[str] = None
    amount: float
    payment_date: Optional[str] = None
    invoice_no: Optional[str] = None

class AcceptanceCreate(BaseModel):
    project_id: int
    acceptance_no: Optional[str] = None
    amount: float
    acceptance_date: Optional[str] = None
    result: Optional[str] = None

class TripleMatchCheck(BaseModel):
    project_id: int

class ResponsibilityChainBuild(BaseModel):
    project_id: int
    nodes: List[dict] = []  # [{id, name, role, department}]
    edges: List[dict] = []  # [{from, to, relation}]

class RiskScoreResponse(BaseModel):
    project_id: int
    risk_score: float
    risk_level: str
    process_risk: float
    capital_risk: float
    related_risk: float
    responsibility_risk: float
    details: List[dict]

class AuditLogResponse(BaseModel):
    id: int
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    details: Optional[str]
    created_at: str