# Logistics Calibration Governance Workflow

## 录入

两条入口都使用 `tools/calibration_intake.py` 向 `data/calibration_records.jsonl` 追加同一种记录。字段格式见 `schemas/calibration_record_v1.json`。

```text
python tools/calibration_intake.py single --name "商品" --sku "SKU-1" --source "软件导出" --baseline-weight 200 --actual-freight 44.20 --error-direction HIGH --error-type FOLDING_COMPRESSION --physical-mechanism STRONG_COMPRESSION --user-note "用户校准结果"
```

- **Software Import**：用户已有软件首次 AI baseline 与用户校准时，直接调用 `calibration_intake.py`，不得再次调用 AI。
- **Direct Calibration**：用户只有图片时，调用 `direct_calibration.py`。它运行时导入 `config/local_paths.json` 指向的 Profit-Accounting `RecognitionService`，直接复用当前首次 AI Prompt、响应 schema、图像排序和 API 配置；不维护同步 Prompt 副本。
- Direct 单条示例：`python tools/direct_calibration.py single --images 商品.png --actual-weight 120 --user-note "用户校准"`。若缺少用户校准，只显示 baseline 预览，不写入正式记录。
- Direct 批量示例：`python tools/direct_calibration.py batch --file 校准表.csv --image-dir 图片目录`。表中的 `images` 列必须能匹配图片；已有完整 baseline 的行不调用 AI。
- 核心比较仅是软件第一次 AI baseline 与用户校准结果；不分析局部重估的中间过程。
- 未知字符串写 `UNKNOWN`，未知数字写 `null`，机制无法可靠判断时写 `UNKNOWN`。
- `physical_mechanism` 仅可为 `FULL_FLAT_FOLD`、`STRONG_COMPRESSION`、`MODERATE_COMPRESSION`、`SHAPE_RETAINED`、`UNKNOWN`；它用于聚合，不是自动规则。
- `packing_action` 等细节只能是辅助证据，不是强制规则维度。
- 录入不会计算运费、不会生成候选规则包，也不会读取 `archive/legacy/`。Direct 只取首次视觉服务的 `normal` 包装候选作为 baseline，不调用 `LocalReestimateService` 或 `PackagingEstimationService`。

## 治理

按 `docs/CALIBRATION_RULES.md` 判断独立样本、误差原因、方向、证据和反例。达到条件时只向用户发出一次简短纳入询问；用户同意后状态变为 `APPROVED_PENDING_PUBLICATION`，仍不导出、不导入、不生效。

状态为：`RECORDED → PATTERN_CANDIDATE → APPROVED_PENDING_PUBLICATION → EXPORTED_PENDING_ACTIVATION → SOFTWARE_ACTIVE`。最后一项只能在 Profit-Accounting 正式流程完成并确认实际激活后记录；intake 拒绝写入该状态和 `VALIDATED`。

## 进度查询

优先读取 `CALIBRATION_STATUS.md` 和必要的当前记录。默认不重扫 `archive/legacy/` 或 CAL77。
