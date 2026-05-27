# 国企经营投资合规审查与责任链风险追踪系统 V1.0

## 项目概述

本系统针对国有企业经营投资活动，提供合规审查与责任链风险追踪服务。系统实现了三重一大决策流程校验、合同-付款-验收三单匹配检测、投资风险熵评分、整改闭环报告等核心功能。

## 核心功能

### 1. 项目资料解析 (`project_parser.py`)
- 解析立项、可研、会议纪要、合同、付款、验收材料
- 虚拟文档坐标映射
- 自动提取关键字段

### 2. 三重一大流程校验 (`decision_checker.py`)
- 检查重大事项决策流程是否完整
- 决策程序合法性检测
- 自动识别需要的三重一大程序

### 3. 三单匹配检测 (`triple_match_checker.py`)
- 检查合同金额、付款金额、验收金额是否一致
- 时间线一致性检测
- 发票一致性检测

### 4. 责任链图谱 (`responsibility_chain.py`)
- 建立决策人、审批人、执行人、供应商关系图
- 关联关系可视化
- 风险节点检测

### 5. 投资风险熵评分 (`investment_risk_scorer.py`)
- 流程风险、资金风险、关联风险、责任风险四维评分
- 多维风险耦合模型
- 风险因子提取

### 6. 整改闭环报告 (`report_generator.py`)
- 生成问题清单
- 责任节点追溯
- 整改建议与计划

## 技术架构

```
backend/
  app/
    api/routes.py      # FastAPI 路由
    core/database.py   # SQLite 数据库
    models/schemas.py  # Pydantic 模型
    services/          # 业务逻辑服务
    rules/             # 规则库 JSON
  requirements.txt
  start.bat
frontend/
  index.html           # Vue3 单文件前端
```

## API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/register_project` | 注册项目 |
| POST | `/api/upload_document` | 上传项目资料 |
| POST | `/api/register_contract` | 登记合同 |
| POST | `/api/register_payment` | 登记付款 |
| POST | `/api/register_acceptance` | 登记验收 |
| POST | `/api/check_triple_match` | 三单匹配检测 |
| POST | `/api/build_responsibility_chain` | 构建责任链图谱 |
| POST | `/api/analyze_project` | 分析项目合规性 |
| GET | `/api/get_project/{project_id}` | 获取项目信息 |
| GET | `/api/get_risk_report/{project_id}` | 获取风险报告 |
| GET | `/api/audit_logs` | 获取审计日志 |
| GET | `/api/list_projects` | 获取项目列表 |

## 启动方式

### 后端启动
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8017 --reload
```
或双击 `start.bat`

### 前端
直接用浏览器打开 `frontend/index.html`

## 数据库

SQLite: `backend/soe_investment_compliance.db`

表结构：
- `rules` - 规则库
- `projects` - 项目信息
- `documents` - 项目文档
- `contracts` - 合同记录
- `payments` - 付款记录
- `acceptance` - 验收记录
- `responsibility_chain` - 责任链图谱
- `analysis_results` - 分析结果
- `audit_logs` - 审计日志

## 规则库

| 规则ID | 规则类型 | 描述 |
|--------|----------|------|
| RULE_SOE_001 | investment_decision | 投资决策依据不足 |
| RULE_SOE_002 | triple_one_large | 三重一大程序缺失 |
| RULE_SOE_003 | contract_amount | 合同金额异常 |
| RULE_SOE_004 | procurement | 采购流程不合规 |
| RULE_SOE_005 | triple_match | 三单金额不一致 |
| RULE_SOE_006 | related_party | 关联交易未披露 |
| RULE_SOE_007 | responsibility_trace | 责任追溯困难 |

## 风险评分维度

- **流程风险 (30%)**: 决策程序完整性
- **资金风险 (35%)**: 三单匹配、资金使用
- **关联风险 (20%)**: 关联交易、利益关联
- **责任风险 (15%)**: 责任链完整性、追溯性

## 可拆解专利

1. 一种基于责任链图谱的国企经营投资风险追踪方法
2. 一种面向三重一大流程的合规闭环校验方法
3. 一种合同-付款-验收多源单据一致性检测方法
4. 一种基于风险熵的国企投资决策异常预警系统

## 技术栈

- Python 3.12 + FastAPI + uvicorn
- SQLAlchemy + SQLite
- Pydantic 数据验证
- Vue3 + ECharts5 前端
- 风险熵多维评分模型