# START HERE FOR AGENT

每次新会话先读：

1. `AGENTS.md`
2. `SKILL.md`
3. `docs/CALIBRATION_RULES.md`
4. `CALIBRATION_STATUS.md`

## 主入口

日常主入口是 `tools/software_feedback_v2_intake.py`，读取主软件导出的 Calibration Feedback Export V2 目录或 manifest.json。

- **ai_initial**：永远是首次 AI baseline（`machine_facts.ai_initial.packaging_proposal.normal`）
- **local_adopted / reestimate_history**：可作为根因解释证据读取，但不能替代 baseline，也不能作为 truth
- **suggested_package**：用户建议/校准值
- **actual_logistics.actual_package_***：只有真实实测时才是包装 truth
- 实际费用不能被反推成唯一包装尺寸

## 备用入口

Direct Calibration（`tools/direct_calibration.py`）仅当用户只有图片、尚未进入主软件时使用。

## 边界

- 先判断入口：用户提供软件首次 AI baseline 时，用 `tools/software_feedback_v2_intake.py` 导入；用户只提供图片时，用 `tools/direct_calibration.py` 获取同源首次 AI baseline。
- 若图片同时有用户校准，则完成比较并追加；若没有用户校准，只展示 baseline 并等待补充，不能写正式记录。
- 没有可靠物理机制时填写 `UNKNOWN`。不自动生成规则，不自动分析 `archive/legacy/`。
- Agent 不自行实现 Replay Engine / Validator / Promotion / Formal Bundle Builder / 第二套 estimator；全部调用当前主软件官方工具。

当用户问当前进度、成熟规律或未形成规则的记录数，先以 `CALIBRATION_STATUS.md` 和当前记录回答。只有用户明确要求历史参考或回归时，才读取 `archive/legacy/`。
