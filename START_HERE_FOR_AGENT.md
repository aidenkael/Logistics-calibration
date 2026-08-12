# START_HERE_FOR_AGENT

每次新会话开始时，按以下步骤执行。

## 1. 先读哪些文件

1. `AGENTS.md` —— 硬禁止与工作边界
2. `SKILL.md` —— 校准录入与工作流操作
3. `docs/CALIBRATION_RULES.md` —— 精简校准规则
4. `config/local_paths.json` —— 确认 `profit_accounting_root` 路径存在

## 2. 判断任务类型

| 类型 | 说明 |
|------|------|
| 校准录入（单条/批量） | 使用 `tools/calibration_intake.py`，操作见 SKILL.md |
| Feedback V2 分析 | 读取软件导出的校准反馈，分析误差 |
| CAL77/历史数据重跑 | 基于历史数据研究（不生成正式 candidate） |
| 候选规则生成 | 根据分析结果生成 candidate 规则包 |
| Replay / Promotion | 调用软件正式工具执行验证/提升 |

## 3. 最小读取原则

- 只读取当前任务需要的文件，不默认扫描整个目录树。
- `archive/legacy/` 默认不读取；CAL77 不是日常默认上下文。

## 4. 禁止事项

- 不询问"利润核算"或"仅头程"模式
- 不自行维护生产 estimator
- 不修改 Profit-Accounting-2.6.1 / keyword_tool / product_collector
- 不自行宣布 VALIDATED
