# Logistics Calibration

独立的物流校准治理工作台。它将软件第一次 AI baseline 与用户校准归一为同一类记录，帮助积累规律、请求用户确认，并展示 Clean Rules 状态。

- 记录格式：`schemas/calibration_record_v1.json`
- 记录存储：`data/calibration_records.jsonl`（只追加）
- 录入工具：`tools/calibration_intake.py`
- Direct Calibration：`tools/direct_calibration.py`（图片 → 当前 Profit-Accounting 首次 AI baseline）
- 治理规则：`docs/CALIBRATION_RULES.md`
- 当前概览：`CALIBRATION_STATUS.md`

入口有两条：已有软件首次 AI 快照时直接导入；只有图片时，Direct Calibration 在运行时调用 `config/local_paths.json` 指向的 Profit-Accounting `RecognitionService`，复用其当前 Prompt、图像输入和输出合同。它不复制 Prompt、不调用局部重估或包装估算服务，也不生成或导入正式规则包。
