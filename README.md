# Logistics Calibration Workbench

Profit-Accounting-2.6.1 的离线物流校准工作台。

Agent 在此目录中分析校准反馈、生成候选规则包、调用软件正式验证工具。

## 校准录入（Intake V1）

- 记录格式：`schemas/calibration_record_v1.json`
- 记录存储：`data/calibration_records.jsonl`（只追加）
- 工具：`tools/calibration_intake.py`（单条/批量）
- 规则：`docs/CALIBRATION_RULES.md`

本目录不是独立项目，是 `Electronic-Commerce-Auto` 仓库的子目录。
