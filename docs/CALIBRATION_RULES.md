# Calibration Rules（校准规则 V1）

精简校准规则。具体操作见 [SKILL.md](../SKILL.md) 与 `tools/calibration_intake.py`。

## 1. 角色与边界

- Profit-Accounting 是唯一生产计算引擎；本工作台只负责记录、分析、归类、生成 candidate。
- Agent 不实现、不复制第二套物流计算器（estimator / calculator / packing engine / 仲裁器）。
- Agent 不修改正式物流公式，不修改 Profit-Accounting-2.6.1、keyword_tool、product_collector。

## 2. 事实优先

任何校准必须区分四类信息：已知事实、用户反馈、软件原估算、Agent 推断。

- 禁止把推断保存成事实。
- 不知道的值一律写 `UNKNOWN`（数字写 `null`），不得为字段完整而猜测。

## 3. 实际费用不能反推唯一包装

只有实际头程费用时，可以判断：当前估算明显偏高/偏低、可能存在计费重方向问题、可作误差样本。

不能断言：实际包装长宽高、实际包装方式、实际重量、某个轴应压缩多少。

## 4. 单样本不生成通用规则

一个商品只能形成：calibration record、anomaly、possible pattern、exact-case candidate。

默认至少多个独立商品出现相同误差模式，才进入规则归纳。

## 5. 旧档案默认关闭

`archive/legacy/` 默认不读取；CAL77 不是日常校准默认上下文。

除非：用户明确要求参考历史、当前问题与历史案例高度相关、或新规则需要额外回归参考。

## 6. 稳定事实直接复用

已确认并保存的货代、物流公式、固定费用、schema、业务规则直接读取，不重复解释和重新推导。

## 7. 最小必要信息

普通单条校准只完成：读取 → 对比 → 分类 → 保存。

只有出现严重异常、数据冲突、新误差模式、可能形成规则时，才进一步分析。

## 8. 证据等级（仅四级）

- **A**：实际包装尺寸/包装重量等直接测量资料充分。
- **B**：有可靠物流事实或计费事实，但包装资料不完整。
- **C**：主要只有实际物流费用或间接证据。
- **D**：主要来自人工判断或低确定性信息。

## 9. 误差类型（仅以下分类）

```text
DIMENSION_HIGH
DIMENSION_LOW
WEIGHT_HIGH
WEIGHT_LOW
PACKAGING_ASSUMPTION
FOLDING_COMPRESSION
STRUCTURE_MISREAD
QUANTITY_MISMATCH
SKU_MISMATCH
FREIGHT_MISMATCH
FORWARDER_MISMATCH
DATA_CONFLICT
UNKNOWN
```

新案例不属于以上类别时，先使用 `UNKNOWN + user_note`；只有重复出现后才考虑扩展 taxonomy。

## 10. 规则升级门槛

```text
普通 Calibration Record
  → 多个独立商品出现相似问题：PATTERN_CANDIDATE
  → 合理样本量且证据方向一致：RULE_CANDIDATE
  → 交给 Profit-Accounting Validator / Replay
  → 验证通过后才允许进入正式规则包
```

Agent 不得自行宣布 `VALIDATED`；validated 之后必须由软件正式工具生成。

## 11. 默认单位约定

尺寸 cm、重量 g、运费 CNY。若源数据使用其他单位，在 `user_note` 或 `source` 中注明。

## 12. Token 控制

- 单条普通校准默认最多输出五行：记录 / 证据 / 结果 / 分类 / 处理。
- 批量校准默认只报告：总数量、成功、缺失、异常、各 error_type 数量、新发现的重复模式。
- 已正常记录的商品不重复解释；只重点输出数据冲突、严重异常、新模式、需用户判断的记录。

## 13. 禁止复杂自动学习系统

不开发：机器学习、embedding/向量库、自动规则自修改、自动 runtime 激活、第二套 estimator、知识图谱、多 Agent 编排、自动大量模型复审、逐条全历史 replay。

当前目标：稳定积累高质量 Calibration Record。
