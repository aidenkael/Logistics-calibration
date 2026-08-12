# Profit-Accounting 物流校准工作流

## 技能名称

Profit-Accounting 物流校准工作流

## 概述

Agent 作为离线校准工具，负责校准录入、分析物流包装估算误差、生成候选规则包，并调用软件正式工具完成验证闭环。规则细节见 `docs/CALIBRATION_RULES.md`。

## 校准录入（Direct Calibration Intake V1）

统一记录格式：`schemas/calibration_record_v1.json`

记录存储：`data/calibration_records.jsonl`（只追加，不覆盖）

工具：`tools/calibration_intake.py`（单条/批量合一）

### 单条校准

用户直接提供图片、软件估算、实际费用、实际尺寸/重量、一句话反馈的任意组合，Agent 归一化后执行：

```text
python tools/calibration_intake.py single --name "商品" --sku "SKU-1" --quantity 1 --images 图片.jpg --source "聊天附件" --evidence-level B --baseline-weight 200 --actual-freight 44.20 --error-direction HIGH --error-type FOLDING_COMPRESSION --user-note "偏高"
```

默认输出最多五行：

```text
记录：CAL-0001
证据：B
结果：当前估算偏高
分类：FOLDING_COMPRESSION
处理：已记录，暂不形成规则
```

### 批量校准

支持 CSV / Excel(.xlsx) / JSON / JSONL / 图片目录+数据表：

```text
python tools/calibration_intake.py batch --file 校准表.csv [--image-dir 图片目录] [--dry-run]
```

批量自动识别字段别名并直接映射；不确定字段写 `UNKNOWN`（数字为 `null`）；缺失字段不导致整批失败。默认只报告：总数量、成功、缺失、异常、各 error_type 数量、新发现的重复模式。

### 录入边界

- 未知字符串保存为 `UNKNOWN`，未知数字保存为 `null`。
- `record_id` 自动生成 `CAL-XXXX` 并保证唯一；不覆盖已有记录。
- 不读取 `archive/legacy/`；不包含 estimator；不生成 validated rule。
- 单条普通校准可用 `--dry-run` 预览而不写入。

## 核心流程

```text
校准录入（Intake V1）
  → 软件 Feedback V2 导出
  → 数据质量检查（manifest.json 解析）
  → Agent 分析误差模式
  → 生成 candidate 规则包
  → 软件 Validator 验证
  → 软件 Offline Replay 重跑
  → 软件 Promotion 提升
  → 软件 Formal Runtime Bundle 构建
  → 软件导入 inactive → 用户手动启用
```

## 职责边界

### Agent 可以做

- 录入单条/批量校准记录（`tools/calibration_intake.py`）
- 解析 Feedback V2 的 `manifest.json`
- 分析 `machine_facts.ai_initial` 与 `machine_facts.user_feedback` 的差异
- 统计误差分布、聚类分析
- 生成 candidate 规则包（JSON 格式）
- 调用软件正式 CLI 工具

### Agent 禁止做

- 自行维护生产 estimator
- 把实际费用反推成包装尺寸/重量
- 宣布规则为 validated
- 直接修改软件 builtin registry 或 SQLite
- 激活规则包

## Feedback V2 输入格式

标准导出结构：

```text
校准反馈_YYYYMMDD_HHMMSS/
├─ 校准反馈.xlsx
├─ manifest.json
└─ images/
```

Agent 优先读取 `manifest.json`，识别：

- `Calibration Feedback Export V2`
- `export_batch_id`
- `records[].machine_facts.ai_initial`
- `records[].machine_facts.user_feedback`

不依赖与包装校准无关的字段（current_estimate、利润、SHEIN 核价、售价、汇率等）。

## 软件正式工具

从 `config/local_paths.json` 的 `profit_accounting_root` 获取软件路径。

| 工具 | 路径 |
|------|------|
| Offline Replay | `tools/calibration_offline_replay_v1.py` |
| Promotion | `tools/calibration_promote_candidate_v1.py` |
| Runtime Bundle | `tools/calibration_build_runtime_bundle_v1.py` |
| PackagingEstimationService | `src/profit_accounting_26/application/packaging_estimation_service.py` |
| AgentCalibrationRulePackageValidator | `src/profit_accounting_26/application/calibration_rule_package_validator.py` |

Agent 通过调用软件路径下的脚本执行操作，不复制这些实现到本目录。

## 历史数据分层

### A 类：有真实包装尺寸/重量

可进入 Packaging Truth Replay 通道。

### B 类：只有真实货代/头程费用

有价值，但不可冒充真实包装尺寸/重量。可用于：
- 预测头程 vs 实际头程比较
- 误差统计与聚类
- 规则假设生成
- CAL77 重跑研究

在正式"头程结果 Replay 通道"完成前，不得因此直接 Promotion 为 validated packaging rule。
