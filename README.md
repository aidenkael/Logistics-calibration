# Logistics Calibration

独立的物流校准治理工作台。它保存软件第一次 AI 估算与用户校准的比较记录，帮助积累规律、请求用户确认，并展示 Clean Rules 状态。

- 记录格式：`schemas/calibration_record_v1.json`
- 记录存储：`data/calibration_records.jsonl`（只追加）
- 录入工具：`tools/calibration_intake.py`
- 治理规则：`docs/CALIBRATION_RULES.md`
- 当前概览：`CALIBRATION_STATUS.md`

本项目不实现物流估算器、不生成或导入正式规则包，也不包含 Profit-Accounting、product_collector 或 keyword_tool 的代码。
