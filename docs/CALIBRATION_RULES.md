# Calibration Governance V1

## 1. 输入和职责边界

每条日常校准只比较两项：软件第一次 AI 估算，以及用户在 Profit-Accounting 中得到的用户校准结果。局部重估、直接修改和其他软件内部操作都属于用户校准结果。

Agent 不复制局部重估、不运行第二套物流估算、不还原中间操作、不修改 Profit-Accounting Prompt，也不成为生产估算器。

## 2. 物理机制标签

`analysis.physical_mechanism` 仅用于聚合独立商品与识别系统性误差：

```text
FULL_FLAT_FOLD
STRONG_COMPRESSION
MODERATE_COMPRESSION
SHAPE_RETAINED
UNKNOWN
```

无法可靠判断时必须使用 `UNKNOWN`。`packing_action` 等细节可以作为辅助证据，但不是强制规则形成维度，也不得扩展出大量主分类。

## 3. 样本与成熟度

同一规律必须同时满足：同一主要物理/包装机制、同一种误差原因、相同且稳定的误差方向，以及真正独立的商品。颜色、尺寸变化或不同链接的同款商品不得重复计入独立样本；无法确认独立性时不得计数。

| 独立样本 | 处理 |
|---|---|
| 1–2 | 只记录。 |
| 3–4 | 若机制、原因和方向稳定，可标记 `PATTERN_CANDIDATE`。 |
| 约 5 个或更多 | 仅当机制、原因、方向、独立性、证据质量和无明显反例同时成立时，才可提醒用户考虑规则。 |

“约 5 个”是默认决策门槛，不会自动形成规则。高度相似商品只能支持窄范围；多个不同子类型仍稳定时才可扩大范围。AI 原估算正确的记录也必须保存，用于将来的 Replay 和保护正确行为。

## 4. 用户确认与生命周期

首次达到规则条件时，Agent 简短提示：

> 当前 XXX 规律已有 X 个独立样本，误差方向稳定，已达到规则候选条件。是否纳入待发布规则？

用户同意“纳入”只将该规律标为 `APPROVED_PENDING_PUBLICATION`。它不生成 Rule Package、ZIP，不导入软件，也不生效。用户暂不纳入后继续积累；除非有新反例、明显新证据或范围实质扩大，不因每条新增记录重复提醒。

统一生命周期：

```text
RECORDED
→ PATTERN_CANDIDATE
→ APPROVED_PENDING_PUBLICATION
→ EXPORTED_PENDING_ACTIVATION
→ SOFTWARE_ACTIVE
```

Agent 不能自行写入 `SOFTWARE_ACTIVE`，也不能声明 `VALIDATED`。只有 Profit-Accounting 正式 Replay、Validator、Promotion 完成且确认实际激活后，才允许记录软件已生效。

## 5. Clean Rules

`archive/legacy/`、CAL77 与旧补丁继续保存，但默认不读取、不自动加入 Clean Rules，也不是新规则来源。

下一版 Clean Rules 只能由“上一版 Clean Rules + 本轮用户批准待发布规则”组成。新规则若与现有 Clean Rule 重叠，必须明确标为：补充、缩小范围、扩大范围或替代；不得依靠 priority 静默覆盖。

## 6. 非目标

本 V1 不修改 Profit-Accounting 或其 Prompt，不开发第二个 estimator、自动 Candidate Rule 生成、数据库、ML、向量库、知识图谱、多 Agent 系统、正式规则包/ZIP 导出，也不批量重分析 legacy。
