# Logistics Calibration Workbench

本目录是独立的 Logistics Calibration 项目。它只保存校准记录、治理判断和当前状态，不依赖 `E:\Electronic Commerce Auto` 根仓库。

## 硬禁止

- 两条入口归一比较软件第一次 AI baseline 与用户校准：已有软件快照走导入；只有图片时通过 `tools/direct_calibration.py` 运行时调用当前 Profit-Accounting `RecognitionService`。不复制 Prompt、局部重估或 estimator。
- 不修改 Profit-Accounting、其 Prompt、keyword_tool 或 product_collector。
- 不把 Agent 推断写成事实；未知字符串为 `UNKNOWN`，未知数字为 `null`。
- 允许在货代、费率、实际费用确认为纯头程时计算“费率等价计费重量”，并在计费规则已确认时用于实重/体积的边界约束；只有存在额外独立证据时，才允许进一步判断实重/体积重主导或估计运输尺寸范围。禁止从单笔费用反推唯一 L×W×H、唯一包装重量或唯一包装方式。
- 不因单样本形成规则。
- 不自行生成正式规则包、ZIP、导入或激活规则；不自行声明 `VALIDATED` 或 `SOFTWARE_ACTIVE`。
- `archive/legacy/` 和 CAL77 默认不读取，不进入 Clean Rules。

## 日常边界

- 使用 `tools/calibration_intake.py` 只追加记录；Direct Calibration 由 `tools/direct_calibration.py` 先取得首次 AI baseline。`analysis.physical_mechanism` 只可为五种治理标签或 `UNKNOWN`。
- 原始首次 AI baseline、用户原始备注和实际纯头程不得被后续重跑覆盖；新 Prompt 结果或费用反推结果必须作为独立实验/派生分析保存。
- 日常流程是：读取 → 对比 → 分类 → 保存。成熟度判断和用户确认遵循 `docs/CALIBRATION_RULES.md`。
- 查询进度时先读 `CALIBRATION_STATUS.md`，再按需读当前 `data/calibration_records.jsonl`；不默认扫描历史档案。
- 临时批次放 `work/`，用户导入材料放 `inbox/`。
