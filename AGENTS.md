# Logistics Calibration Workbench

本目录是 Profit-Accounting-2.6.1 的离线物流校准工作台。

## 硬禁止

- 禁止实现或复制第二套物流计算器（estimator / calculator / packing engine / 仲裁器）。
- 禁止修改 Profit-Accounting-2.6.1、keyword_tool、product_collector。
- 禁止把 Agent 推断保存成事实；未知值一律 `UNKNOWN`（数字为 `null`），不得猜测。
- 禁止从实际费用反推唯一包装尺寸/重量/方式。
- 禁止因单个样本修改品类规则；禁止自行宣布 `VALIDATED`。
- `archive/legacy/` 默认禁止读取；CAL77 不是日常默认上下文。

## 工作边界

- 修改范围永远限制在 `Logistics calibration/**`。
- 校准录入使用 `tools/calibration_intake.py`，默认只输出最小信息。
- 临时批次进入 `work/`，用户导入资料进入 `inbox/`。

## 新会话入口

参见 [START_HERE_FOR_AGENT.md](START_HERE_FOR_AGENT.md)；
规则细节见 [docs/CALIBRATION_RULES.md](docs/CALIBRATION_RULES.md)。
