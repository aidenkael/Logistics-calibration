# Calibration Workflow

## 0. 校准录入（Intake V1）

单条/批量校准先通过 `tools/calibration_intake.py` 写入 `data/calibration_records.jsonl`；记录格式见 `schemas/calibration_record_v1.json`，规则见 `docs/CALIBRATION_RULES.md`。录入只记录，不生成规则；不读取 `archive/legacy/`。

## 标准校准流程

### 1. 获取 Feedback V2

从 Profit-Accounting-2.6.1 导出校准反馈包：

```
校准反馈_YYYYMMDD_HHMMSS/
├─ 校准反馈.xlsx    # 人工查看
├─ manifest.json   # 机器分析主入口
└─ images/          # 商品图片
```

### 2. 数据质量检查

解析 `manifest.json`，确认：
- 格式版本为 `Calibration Feedback Export V2`
- `export_batch_id` 存在
- `records` 数组非空
- 每条记录包含 `machine_facts.ai_initial` 和 `machine_facts.user_feedback`

### 3. Agent 分析误差

- 对比 AI 初始估算与用户反馈
- 统计误差分布
- 聚类分析误差模式
- 识别系统性偏差

### 4. 生成 Candidate

Agent 基于分析结果生成候选规则包（JSON 格式）。

**candidate 之前 Agent 可以自主分析；validated 之后必须由软件正式工具生成。**

### 5. 软件正式验证

依次调用软件工具：

1. **Validator** — `calibration_rule_package_validator.py` 验证候选包结构
2. **Offline Replay** — `calibration_offline_replay_v1.py` 历史数据重跑
3. **Promotion** — `calibration_promote_candidate_v1.py` 提升为 validated
4. **Runtime Bundle** — `calibration_build_runtime_bundle_v1.py` 构建正式包

### 6. 导入

软件导入 inactive 规则包，用户手动启用。
