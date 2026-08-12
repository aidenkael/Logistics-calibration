# START HERE FOR AGENT

每次新会话先读：

1. `AGENTS.md`
2. `SKILL.md`
3. `docs/CALIBRATION_RULES.md`
4. `CALIBRATION_STATUS.md`

日常录入只比较软件第一次 AI 估算和用户校准结果。用户在 Profit-Accounting 内作出的局部重估或手动修改只作为用户校准结果；不得复制、重跑或还原其内部过程。

先判断入口：用户提供软件首次 AI baseline 时，用 `tools/calibration_intake.py` 直接导入；用户只提供图片时，用 `tools/direct_calibration.py` 获取同源首次 AI baseline。若图片同时有用户校准，则完成比较并追加；若没有用户校准，只展示 baseline 并等待补充，不能写正式记录。没有可靠物理机制时填写 `UNKNOWN`。不自动生成规则，不自动分析 `archive/legacy/`。

当用户问当前进度、成熟规律或未形成规则的记录数，先以 `CALIBRATION_STATUS.md` 和当前记录回答。只有用户明确要求历史参考或回归时，才读取 `archive/legacy/`。
