# Logistics Calibration Workbench

本目录是独立的 Logistics Calibration 项目。它只保存校准记录、治理判断和当前状态，不依赖 `E:\Electronic Commerce Auto` 根仓库。

## 硬禁止

- 只比较软件第一次 AI 估算与用户校准结果；不复制局部重估，不还原用户中间操作，不开发第二套 estimator。
- 不修改 Profit-Accounting、其 Prompt、keyword_tool 或 product_collector。
- 不把 Agent 推断写成事实；未知字符串为 `UNKNOWN`，未知数字为 `null`。
- 不从实际费用反推唯一包装尺寸、重量或方式；不因单样本形成规则。
- 不自行生成正式规则包、ZIP、导入或激活规则；不自行声明 `VALIDATED` 或 `SOFTWARE_ACTIVE`。
- `archive/legacy/` 和 CAL77 默认不读取，不进入 Clean Rules。

## 日常边界

- 使用 `tools/calibration_intake.py` 只追加记录；`analysis.physical_mechanism` 只可为五种治理标签或 `UNKNOWN`。
- 日常流程是：读取 → 对比 → 分类 → 保存。成熟度判断和用户确认遵循 `docs/CALIBRATION_RULES.md`。
- 查询进度时先读 `CALIBRATION_STATUS.md`，再按需读当前 `data/calibration_records.jsonl`；不默认扫描历史档案。
- 临时批次放 `work/`，用户导入材料放 `inbox/`。
