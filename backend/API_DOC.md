# SOE Investment Compliance API Documentation

## Base URL
```
/api/v1
```

## Endpoints

### 1. POST `/review_investment_proposal`

Review investment proposal for SOE compliance.

**Request Body:**
```json
{
  "proposal_id": "string",
  "investment_amount": 150000000,
  "investment_type": "新建 | 并购 | 参股 | 合资",
  "sector": "string",
  "decision_level": "董事会 | 股东大会 | 国资委",
  "supporting_docs": ["风险评估报告.pdf", "财务审计报告.pdf", "可行性论证.pdf"]
}
```

**Response:**
```json
{
  "proposal_id": "string",
  "investment_amount": 150000000,
  "risk_factors": [
    {"factor": "投资金额超过10亿元", "severity": "critical", "regulation": "须上报国资委审批"}
  ],
  "compliance_checklist": {
    "决策程序合规": true,
    "可行性论证": true,
    "风险评估报告": true,
    "财务审计": true
  },
  "compliance_rate": 100.0,
  "approval_recommendation": "上报国资委 | 同意立项 | 补充材料后重审"
}
```

---

### 2. POST `/check_three_major_decisions`

Verify three-major-decisions (三重一大) compliance.

**Request Body:**
```json
{
  "proposal_id": "string",
  "decisions": [
    {"decision_type": "重大决策", "content": "年产10万吨新能源项目投资", "approved": true, "meeting_date": "2024-03-15"},
    {"decision_type": "重要人事任免", "content": "任命张三为项目负责人", "approved": true, "meeting_date": "2024-03-15"},
    {"decision_type": "重大项目安排", "content": "项目进度安排与资金计划", "approved": true, "meeting_date": "2024-03-20"},
    {"decision_type": "大额资金运作", "content": "首期资金支付¥5000万", "approved": true, "meeting_date": "2024-03-20"}
  ]
}
```

**Response:**
```json
{
  "proposal_id": "string",
  "major_decisions_found": [
    {"decision": "重大决策", "content": "...", "status": "approved", "meeting_date": "2024-03-15"}
  ],
  "unmatched_decisions": [],
  "三重一大合规": true,
  "会议记录完整性": "4/4项完整",
  "建议": "合规性检查通过 | 补充缺失的三重一大会议记录"
}
```

---

### 3. POST `/validate_three_list_matching`

Validate three-list matching (三单匹配): proposal, contract, payment.

**Request Body:**
```json
{
  "proposal_id": "string",
  "investment_amount": 80000000,
  "investment_type": "新建 | 并购 | 参股 | 合资",
  "counterparty": "交易对手方名称"
}
```

**Response:**
```json
{
  "proposal_id": "string",
  "investment_amount": 80000000,
  "investment_type": "新建",
  "issues_found": [
    {"issue": "投资金额¥80.0M超过新建门槛¥5M", "regulation": "须纳入三重一大管理"}
  ],
  "matching_score": 0.7,
  "validation_result": "通过 | 驳回 | 补充说明",
  "regulatory_references": ["须纳入三重一大管理"]
}
```

---

### 4. GET `/get_compliance_score`

Get overall investment compliance score for an SOE.

**Query Parameters:**
- `organization_id` (string, required): Organization ID

**Response:**
```json
{
  "organization_id": "string",
  "proposals_reviewed": 12,
  "average_compliance_rate": 85.5,
  "compliance_grade": "A | B | C | D",
  "key_metrics": {
    "三重一大执行率": "95%",
    "平均审批时长": "28天",
    "合规培训覆盖率": "100%"
  },
  "risk_areas": ["投资后评估缺失", "可行性论证不充分"],
  "timestamp": "2024-03-20T10:30:00"
}
```

---

## Compliance Grades

| Grade | Average Compliance Rate |
|-------|------------------------|
| A     | ≥ 90%                  |
| B     | 80% - 89%              |
| C     | 70% - 79%              |
| D     | < 70%                  |

## Investment Type Thresholds (三单匹配)

| Type | Threshold (CNY) |
|------|-----------------|
| 新建 | 5,000,000       |
| 并购 | 10,000,000      |
| 参股 | 3,000,000       |
| 合资 | 5,000,000       |

## Key Regulations

- **10亿元红线**: 投资金额超过10亿元须上报国资委专项审批
- **三重一大**: 重大决策、重要人事任免、重大项目安排、大额资金运作须上级审批
- **负面清单**: 房地产、娱乐、赌博、武器制造等禁止类行业不得投资