# Architecture

本独立项目有两条校准入口：Software Import 与 Direct Calibration；它们都追加 Calibration Record、按 Governance V1 评估成熟度、维护开发者状态页。它不是物流估算器，也不包含正式规则发布工具。

```text
Software Import：已有首次 AI baseline + 用户校准
  ─┐
   ├→ Calibration Record
Direct Calibration：图片 → Profit-Accounting RecognitionService 首次 AI baseline + 用户校准
  ─┘
  → 成熟度判断与用户确认
  → 待发布状态
  → 外部 Profit-Accounting 正式流程
  → 确认激活后才可标记 SOFTWARE_ACTIVE
```

| 路径 | 职责 |
|---|---|
| `data/` | 当前只追加的校准记录 |
| `schemas/` | Calibration Record schema |
| `tools/` | 录入与测试 |
| `CALIBRATION_STATUS.md` | 当前 Clean Rules 和成熟度概览 |
| `archive/legacy/` | 历史档案，默认不读取 |

正式软件验证、Replay、Promotion、导入与激活发生在外部软件中；它们不是本仓库的自动化任务。

Direct Calibration 动态导入 `config/local_paths.json` 指向的生产 `RecognitionService`，因此 Prompt、图像输入排序、响应 schema 和视觉 API 配置仍由 Profit-Accounting 单一来源维护。它以只读设置保护运行，不构建 AppContext，不写软件数据库或设置，也不调用局部重估或包装估算服务。
