# Logistics Calibration

独立的物流校准治理工作台。它将软件第一次 AI baseline 与用户校准归一为同一类记录，帮助积累规律、请求用户确认，并展示 Clean Rules 状态。

- 记录格式：`schemas/calibration_record_v1.json`
- 记录存储：`data/calibration_records.jsonl`（只追加）
- **主入口**：`tools/software_feedback_v2_intake.py`（读取主软件导出的 Calibration Feedback Export V2 目录/manifest）
- Direct Calibration（备用）：`tools/direct_calibration.py`（仅当用户只有图片、尚未进入主软件时使用）
- 治理规则：`docs/CALIBRATION_RULES.md`
- 当前概览：`CALIBRATION_STATUS.md`

## 数据合同

- **日常主入口**：Calibration Feedback Export V2（主软件 `calibration_export_service.py` 导出）
- **ai_initial**：永远是首次 AI baseline（`machine_facts.ai_initial.packaging_proposal.normal`）
- **local_adopted / reestimate_history**：可作为根因解释证据读取，但不能替代 baseline，也不能作为 truth
- **suggested_package**：用户建议/校准值
- **actual_logistics.actual_package_***：只有真实实测时才是包装 truth
- **实际费用**：不能被反推成唯一包装尺寸

## 边界

- Agent 不自行实现 Replay Engine / Validator / Promotion / Formal Bundle Builder / 第二套 estimator
- 全部调用当前主软件（Profit-Accounting 2.6.1）官方工具：`AgentCalibrationRulePackageValidator`、`OfflineCalibrationReplay`、`CalibrationRulePackagePromoter`、`CalibrationRuntimeBundleBuilder`
- 合同自检：`tools/check_software_contract.py`
