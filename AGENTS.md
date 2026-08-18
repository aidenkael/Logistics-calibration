# Logistics Calibration Workbench

本目录是独立的 Logistics Calibration 项目。它只保存校准记录、治理判断和当前状态，不依赖 `E:\Electronic Commerce Auto` 根仓库。

## 硬禁止

- 两条入口归一比较软件第一次 AI baseline 与用户校准：已有软件快照走导入；只有图片时通过 `tools/direct_calibration.py` 运行时调用当前 Profit-Accounting `RecognitionService`。不复制 Prompt、局部重估或 estimator。
- 不修改 Profit-Accounting、其 Prompt、keyword_tool 或 product_collector。
- 不把 Agent 推断写成事实；未知字符串为 `UNKNOWN`，未知数字为 `null`。
- 不从实际费用反推唯一包装尺寸、重量或方式；不因单样本形成规则。
- 不自行生成正式规则包、ZIP、导入或激活规则；不自行声明 `VALIDATED` 或 `SOFTWARE_ACTIVE`。
- `archive/legacy/` 和 CAL77 默认不读取，不进入 Clean Rules。
- Agent 不自行实现 Replay Engine / Validator / Promotion / Formal Bundle Builder / 第二套 estimator；全部调用当前主软件官方工具。

## 日常边界

- **主入口**：`tools/software_feedback_v2_intake.py`（读取主软件导出的 Calibration Feedback Export V2 目录/manifest）。
- **Direct Calibration**（备用）：`tools/direct_calibration.py`（仅当用户只有图片、尚未进入主软件时使用）。
- `tools/calibration_intake.py` 只追加记录。
- `analysis.physical_mechanism` 只可为五种治理标签或 `UNKNOWN`。
- 日常流程是：读取 → 对比 → 分类 → 保存。成熟度判断和用户确认遵循 `docs/CALIBRATION_RULES.md`。
- 查询进度时先读 `CALIBRATION_STATUS.md`，再按需读当前 `data/calibration_records.jsonl`；不默认扫描历史档案。
- 临时批次放 `work/`，用户导入材料放 `inbox/`。

## 数据合同

- **ai_initial**：永远是首次 AI baseline（`machine_facts.ai_initial.packaging_proposal.normal`）。
- **local_adopted / reestimate_history**：可作为根因解释证据读取，但不能替代 baseline，也不能作为 truth。
- **suggested_package**：用户建议/校准值。
- **actual_logistics.actual_package_***：只有真实实测时才是包装 truth。
- **实际费用**：不能被反推成唯一包装尺寸。
- baseline 必须来自 `machine_facts.ai_initial.packaging_proposal.normal`，不能用 current estimate / local adopted 替换。
