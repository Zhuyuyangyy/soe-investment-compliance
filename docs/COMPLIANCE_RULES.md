# Compliance Rules Reference

## Rule Library

The system implements 10 compliance rules based on Chinese SOE investment regulations.

### RULE_SOE_001 - Investment Decision Basis Insufficiency

- **Type**: investment_decision
- **Severity**: high
- **Description**: Investment decision lacks supporting documentation (feasibility study, approval documents)
- **Penalty**: Supplement materials, suspend payments
- **Detection**: Checks for project_proposal and feasibility_study document presence
- **Regulation**: State-Owned Assets Law, Article 35

### RULE_SOE_002 - Three-Major-Decisions Procedure Missing

- **Type**: triple_one_large
- **Severity**: critical
- **Description**: Major decision procedures (三重一大) are missing or non-compliant
- **Penalty**: Rectification order, accountability追究
- **Detection**: Validates presence of party committee review, board resolution, supervision review
- **Regulation**: "三重一大" Decision-making System Implementation Rules

### RULE_SOE_003 - Contract Amount Anomaly

- **Type**: contract_amount
- **Severity**: medium
- **Description**: Contract amount deviates more than 20% from budget or feasibility estimate
- **Penalty**: Explanation required
- **Detection**: Cross-references contract amounts with feasibility study estimates
- **Regulation**: SOE Investment Supervision Measures

### RULE_SOE_004 - Non-Compliant Procurement

- **Type**: procurement
- **Severity**: high
- **Description**: Procurement process does not follow required bidding procedures
- **Penalty**: Re-execute procurement procedures
- **Detection**: Checks for bidding documents and procurement competition records
- **Regulation**: Government Procurement Law, Bidding Law

### RULE_SOE_005 - Triple-Document Amount Mismatch

- **Type**: triple_match
- **Severity**: high
- **Description**: Contract, payment, and acceptance amounts are inconsistent
- **Penalty**: Suspend payments, full investigation
- **Detection**: Three-way reconciliation with 5% deviation threshold
- **Regulation**: Internal Control Basic Standards (COSO framework)

### RULE_SOE_006 - Undisclosed Related-Party Transaction

- **Type**: related_party
- **Severity**: critical
- **Description**: Related-party transaction exists but is not disclosed or disclosure is inaccurate
- **Penalty**: Refer to discipline inspection
- **Detection**: Keyword scanning for "集团", "关联", "子公司" in contract parties
- **Regulation**: SOE Related-Party Transaction Management Measures

### RULE_SOE_007 - Responsibility Traceability Gap

- **Type**: responsibility_trace
- **Severity**: medium
- **Description**: Responsible parties are unclear, making accountability tracing difficult
- **Penalty**: Clarify responsible parties
- **Detection**: Checks responsibility chain completeness and approver presence
- **Regulation**: SOE Accountability Measures

### RULE_SOE_008 - Document Integrity Issues

- **Type**: document_integrity
- **Severity**: high
- **Description**: Project documents are severely incomplete
- **Penalty**: Supplement missing documents
- **Detection**: Document coverage analysis across required document types

### RULE_SOE_009 - Timeline Compliance Violation

- **Type**: timeline_compliance
- **Severity**: medium
- **Description**: Project timeline violates normal process sequence
- **Penalty**: Verification and explanation required
- **Detection**: Date sequence validation across contracts, payments, and acceptances

### RULE_SOE_010 - Fund Usage Non-Compliance

- **Type**: fund_usage
- **Severity**: high
- **Description**: Fund usage does not match contract terms
- **Penalty**: Stop payments, rectify
- **Detection**: Cross-references payment purposes with contract terms

## Risk Scoring Model

### Four-Dimensional Risk Entropy

| Dimension | Weight | Thresholds |
|-----------|--------|------------|
| Process Risk | 30% | Low: <30, Medium: 30-59, High: 60-79, Critical: 80+ |
| Capital Risk | 35% | Same thresholds |
| Association Risk | 20% | Same thresholds |
| Responsibility Risk | 15% | Same thresholds |

### Risk Level Classification

| Level | Score Range | Action Required |
|-------|-------------|-----------------|
| Low | 0-29 | Continue monitoring |
| Medium | 30-59 | Supplement missing procedures |
| High | 60-79 | Suspend payments, investigate |
| Critical | 80-100 | Immediate escalation, full audit |

## Regulatory References

1. State-Owned Assets Law of PRC (企业国有资产法)
2. "三重一大" Decision-making System Implementation Rules
3. SOE Investment Supervision and Administration Measures
4. Government Procurement Law (政府采购法)
5. Bidding Law (招标投标法)
6. Internal Control Basic Standards (企业内部控制基本规范)
7. SOE Accountability Measures (国有企业违规经营投资责任追究办法)
