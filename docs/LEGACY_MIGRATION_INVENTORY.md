# Legacy Migration Inventory

来源：`E:\EcommerceSkills\logistics-cost-skill-2.0`
审计日期：2026-08-12
审计文件/目录总数：约 130 个文件（含 __pycache__）

## 分类说明

| 分类 | 含义 |
|------|------|
| KEEP_AS_DATA | 历史事实数据，可迁移到当前工作区 |
| KEEP_AS_ARCHIVE | 历史档案，放入 archive/legacy/，默认不读取 |
| REIMPLEMENT_THIN | 如有需要可重新实现为精简工具 |
| DO_NOT_MIGRATE | 不迁移，属于旧双引擎架构 |

---

## 根目录文件

| 文件 | 用途 | 分类 | 原因 |
|------|------|------|------|
| AGENTS.md | 旧 Agent 行为规则 | DO_NOT_MIGRATE | 旧架构规则，会污染新 Agent 判断 |
| START_HERE_FOR_AGENT.md | 旧会话入口 | DO_NOT_MIGRATE | 含旧模式选择逻辑 |
| SKILL.md | 旧技能描述 | DO_NOT_MIGRATE | 含旧双引擎工作流 |
| OUTPUT_CONTRACT.md | 旧输出合同 | DO_NOT_MIGRATE | 旧输出格式约束 |
| CALIBRATION.md | 旧校准运行规则 | DO_NOT_MIGRATE | 旧校准运行逻辑 |
| README.md | 旧项目说明 | DO_NOT_MIGRATE | 旧项目文档 |
| run.py | 旧生产入口 | DO_NOT_MIGRATE | 旧"双引擎"入口脚本 |
| requirements.txt | 旧依赖列表 | DO_NOT_MIGRATE | 旧项目依赖 |
| feedback_correction.py | 旧反馈修正逻辑 | DO_NOT_MIGRATE | 含旧 estimator 耦合逻辑 |
| extract_and_verify.sh | 旧验证脚本 | DO_NOT_MIGRATE | 旧 shell 脚本 |
| run_mac.sh | 旧 Mac 运行脚本 | DO_NOT_MIGRATE | 旧平台脚本 |
| MAC使用说明.md | 旧 Mac 使用说明 | DO_NOT_MIGRATE | 旧文档 |
| .gitignore | 旧忽略规则 | DO_NOT_MIGRATE | 新目录有独立 .gitignore |

## logistics_cost/ — 独立计算引擎

| 文件 | 分类 | 原因 |
|------|------|------|
| calculator.py | DO_NOT_MIGRATE | 旧独立计算引擎 |
| estimator.py | DO_NOT_MIGRATE | 旧 estimator |
| packing_engine.py | DO_NOT_MIGRATE | 旧打包引擎 |
| packaging_arbitrator.py | DO_NOT_MIGRATE | 旧仲裁器 |
| packaging_decision_ai.py | DO_NOT_MIGRATE | 旧 AI 决策 |
| profit_calculator.py | DO_NOT_MIGRATE | 旧利润计算（与校准无关） |
| soft_goods_rules.py | DO_NOT_MIGRATE | 旧生产修正规则 |
| weight_rules.py | DO_NOT_MIGRATE | 旧重量规则 |
| calibration_resolver.py | DO_NOT_MIGRATE | 旧校准解析器 |
| output_renderer.py | DO_NOT_MIGRATE | 旧固定输出表格 |
| output_contract_guard.py | DO_NOT_MIGRATE | 旧输出守卫 |
| evidence_resolver.py | DO_NOT_MIGRATE | 旧证据解析器 |
| product_request.py | DO_NOT_MIGRATE | 旧请求处理 |
| request_audit.py | DO_NOT_MIGRATE | 旧审计 |
| request_freshness_guard.py | DO_NOT_MIGRATE | 旧新鲜度守卫 |
| session_preferences.py | DO_NOT_MIGRATE | 旧会话偏好 |
| storage.py | DO_NOT_MIGRATE | 旧存储 |
| config.py | DO_NOT_MIGRATE | 旧配置 |
| ai_schema.py | DO_NOT_MIGRATE | 旧 AI schema |
| artifact_delivery.py | DO_NOT_MIGRATE | 旧 artifact 交付 |
| feedback.py | DO_NOT_MIGRATE | 旧反馈处理 |
| __init__.py | DO_NOT_MIGRATE | 旧模块初始化 |
| inference/ 子目录 | DO_NOT_MIGRATE | 旧推理适配器 |
| __pycache__/ | DO_NOT_MIGRATE | 缓存文件 |

## data/

| 文件 | 分类 | 原因 |
|------|------|------|
| head_cost_feedback.csv | KEEP_AS_DATA | 真实头程费用反馈数据（1 行 header，含列定义） |
| product_images/ | KEEP_AS_DATA | 商品图片目录（当前为空） |

## knowledge/

| 文件 | 分类 | 原因 |
|------|------|------|
| calibration_cases.jsonl | KEEP_AS_ARCHIVE | 2 个校准案例，含真实头程费用事实，但属于旧案例格式 |
| packaging_arbitration_rules.json | DO_NOT_MIGRATE | 旧仲裁规则算法，会污染新 Agent |
| physical_packaging_rules.json | DO_NOT_MIGRATE | 旧包装规则算法，会污染新 Agent |
| validated_packaging_profiles.json | DO_NOT_MIGRATE | 空 profiles，旧架构产物 |
| README.md | DO_NOT_MIGRATE | 旧知识库说明 |

## archive/calibration/

| 文件 | 分类 | 原因 |
|------|------|------|
| 79_items_original.json | KEEP_AS_ARCHIVE | CAL77 原始数据 |
| 79_items_verified.json | KEEP_AS_ARCHIVE | CAL77 验证后数据 |
| 79_items_visual_estimates.json | KEEP_AS_ARCHIVE | CAL77 视觉估算数据 |
| calibration_round_01_replay_report.md | KEEP_AS_ARCHIVE | 第一轮 replay 报告 |
| calibration_samples.json | KEEP_AS_ARCHIVE | 校准样本原始版 |
| calibration_samples_cleaned_v1.json | KEEP_AS_ARCHIVE | 校准样本清洗版 |
| calibration_samples_round_02.json | KEEP_AS_ARCHIVE | 第二轮校准样本 |
| calibration_validation_report.md | KEEP_AS_ARCHIVE | 校准验证报告 |
| evidence/ (空目录) | KEEP_AS_ARCHIVE | 证据目录（空） |

## examples/

| 文件 | 分类 | 原因 |
|------|------|------|
| 70 个 *_ai.json 文件 | KEEP_AS_ARCHIVE | AI 估算示例，已复制到 2.6.1/calibration/r2/examples/ |

## scripts/

| 文件 | 分类 | 原因 |
|------|------|------|
| phase1_clean_data.py | DO_NOT_MIGRATE | 旧 phase5 replay 相关 |
| phase5_replay.py | DO_NOT_MIGRATE | 旧正式 replay（已被 2.6.1 工具取代） |

## tools/

| 文件 | 分类 | 原因 |
|------|------|------|
| mac_bootstrap.py | DO_NOT_MIGRATE | 旧 Mac 引导脚本 |

## config/

| 文件 | 分类 | 原因 |
|------|------|------|
| local_user_preferences.json | DO_NOT_MIGRATE | 旧用户偏好（含利润参数） |
| logistics_config.json | DO_NOT_MIGRATE | 旧物流配置（含公式参数） |

## output/

| 文件 | 分类 | 原因 |
|------|------|------|
| *.md, sessions/*.json | KEEP_AS_ARCHIVE | 历史输出记录，可供复盘 |

## tests/

| 文件 | 分类 | 原因 |
|------|------|------|
| 所有测试文件 | DO_NOT_MIGRATE | 测试旧双引擎逻辑 |
| golden/ | DO_NOT_MIGRATE | 旧 golden 输出 |

## references/

| 文件 | 分类 | 原因 |
|------|------|------|
| ai-reasoning-schema.md | DO_NOT_MIGRATE | 旧 AI 推理 schema |
| calibration.md | DO_NOT_MIGRATE | 旧校准文档 |
| packaging-policy.md | DO_NOT_MIGRATE | 旧包装策略 |

## docs/

| 文件 | 分类 | 原因 |
|------|------|------|
| LOGISTICS_MAINTENANCE_WORKFLOW.md | DO_NOT_MIGRATE | 旧维护工作流 |
| NEXT_CALIBRATION_SESSION.md | DO_NOT_MIGRATE | 旧下次校准计划 |

## .workbuddy/

| 文件 | 分类 | 原因 |
|------|------|------|
| memory/*.md | DO_NOT_MIGRATE | 旧 Agent 会话记忆 |

## .pytest_cache/

| 文件 | 分类 | 原因 |
|------|------|------|
| 全部 | DO_NOT_MIGRATE | 测试缓存 |

---

## 汇总

### KEEP_AS_DATA（可迁移到当前工作区）

- `data/head_cost_feedback.csv` — 真实头程费用反馈（1 行 header）
- `data/product_images/` — 商品图片目录（当前为空）

### KEEP_AS_ARCHIVE（放入 archive/legacy/，默认不读取）

- `archive/calibration/79_items_original.json`
- `archive/calibration/79_items_verified.json`
- `archive/calibration/79_items_visual_estimates.json`
- `archive/calibration/calibration_round_01_replay_report.md`
- `archive/calibration/calibration_samples.json`
- `archive/calibration/calibration_samples_cleaned_v1.json`
- `archive/calibration/calibration_samples_round_02.json`
- `archive/calibration/calibration_validation_report.md`
- `knowledge/calibration_cases.jsonl` — 2 个校准案例
- `examples/` — 70 个 AI 估算示例
- `output/` — 历史输出记录

### REIMPLEMENT_THIN（如有需要可精简重新实现）

当前无。旧项目中没有发现与生产算法无关、确实还能复用的纯数据解析工具。

### DO_NOT_MIGRATE（主要内容）

- **logistics_cost/** — 整个独立计算引擎（estimator、calculator、packing_engine 等 20+ 模块）
- **旧 Agent 文档** — AGENTS.md、SKILL.md、START_HERE_FOR_AGENT.md、OUTPUT_CONTRACT.md、CALIBRATION.md
- **旧规则/算法** — packaging_arbitration_rules.json、physical_packaging_rules.json、soft_goods_rules.py
- **旧生产脚本** — run.py、phase5_replay.py、phase1_clean_data.py
- **旧测试** — 全部测试文件和 golden 输出
- **旧配置** — logistics_config.json、local_user_preferences.json

---

## 本阶段实际复制

本阶段（工作台初始化）不复制任何文件到正式工作区。

KEEP_AS_DATA 文件（head_cost_feedback.csv）可在后续历史数据迁移阶段按需复制。
KEEP_AS_ARCHIVE 文件可在后续阶段按需复制到 archive/legacy/。
