# Logistics Calibration Governance Workflow

## 录入

### 主入口：Software Feedback V2

`tools/software_feedback_v2_intake.py` 读取主软件导出的 Calibration Feedback Export V2 目录或 manifest.json。

```text
python tools/software_feedback_v2_intake.py --source "path/to/export_dir"
```

- 验证 `contract_version == "Calibration Feedback Export V2"`
- 读取 `record_id`、`export_batch_id`、`image_relative_paths`、`machine_facts.ai_initial`、`machine_facts.local_adopted`、`machine_facts.reestimate_history`、`machine_facts.user_feedback`
- baseline 必须来自 `machine_facts.ai_initial.packaging_proposal.normal`
- 不调用 AI、不修改原始 manifest、不复制完整 machine_facts 到 JSONL
- 转成现有 `calibration_records.jsonl` 所需的治理摘要
- 保存原始 manifest 路径/provenance
- 防止重复导入（通过 `data/software_import_index.json`）
- `suggested_package` 与 `actual_logistics` 必须严格区分
- 实际费用不能被反推成唯一包装尺寸
- 货代、费率、实际费用确认为纯头程时，可计算"费率等价计费重量"，但该值只能作为派生/边界证据；没有独立真实重量/尺寸证据时，不能据此宣布实重或体积重主导
- 不能从单笔费用反推唯一 L×W×H、唯一包装重量或唯一包装方式
- AI baseline 不能作为证明自身正确的 truth

### 备用入口：Direct Calibration

`tools/direct_calibration.py`（仅当用户只有图片、尚未进入主软件时使用）。

```text
python tools/direct_calibration.py single --images 商品.png --actual-weight 120 --user-note "用户校准"
```

- 运行时导入 `config/local_paths.json` 指向的 Profit-Accounting `RecognitionService`，直接复用当前首次 AI Prompt、响应 schema、图像排序和 API 配置；不维护同步 Prompt 副本。
- 若缺少用户校准，只显示 baseline 预览，不写入正式记录。
- Direct 批量示例：`python tools/direct_calibration.py batch --file 校准表.csv --image-dir 图片目录`。

### 旧入口（保留）

`tools/calibration_intake.py` 只追加记录。字段格式见 `schemas/calibration_record_v1.json`。

```text
python tools/calibration_intake.py single --name "商品" --sku "SKU-1" --source "软件导出" --baseline-weight 200 --actual-freight 44.20 --error-direction HIGH --error-type FOLDING_COMPRESSION --physical-mechanism STRONG_COMPRESSION --user-note "用户校准结果"
```

- 核心比较仅是软件第一次 AI baseline 与用户校准结果；不分析局部重估的中间过程。
- 未知字符串写 `UNKNOWN`，未知数字写 `null`，机制无法可靠判断时写 `UNKNOWN`。
- `physical_mechanism` 仅可为 `FULL_FLAT_FOLD`、`STRONG_COMPRESSION`、`MODERATE_COMPRESSION`、`SHAPE_RETAINED`、`UNKNOWN`；它用于聚合，不是自动规则。
- `packing_action` 等细节只能是辅助证据，不是强制规则维度。
- 录入不会计算运费、不会生成候选规则包，也不会读取 `archive/legacy/`。Direct 只取首次视觉服务的 `normal` 包装候选作为 baseline，不调用 `LocalReestimateService` 或 `PackagingEstimationService`。

## 治理

按 `docs/CALIBRATION_RULES.md` 判断独立样本、误差原因、方向、证据和反例。达到条件时只向用户发出一次简短纳入询问；用户同意后状态变为 `APPROVED_PENDING_PUBLICATION`，仍不导出、不导入、不生效。

状态为：`RECORDED → PATTERN_CANDIDATE → APPROVED_PENDING_PUBLICATION → EXPORTED_PENDING_ACTIVATION → SOFTWARE_ACTIVE`。最后一项只能在 Profit-Accounting 正式流程完成并确认实际激活后记录；intake 拒绝写入该状态和 `VALIDATED`。

## 发布

Agent 不自行实现发布链。全部调用当前主软件（Profit-Accounting 2.6.1）官方工具：

- `AgentCalibrationRulePackageValidator`（验证 candidate 包）
- `OfflineCalibrationReplay`（baseline vs candidate 对比）
- `CalibrationRulePackagePromoter`（用户 review 后生成 validated 包）
- `CalibrationRuntimeBundleBuilder`（生成 Formal Bundle ZIP）

合同自检：`tools/check_software_contract.py`

## 进度查询

优先读取 `CALIBRATION_STATUS.md` 和必要的当前记录。默认不重扫 `archive/legacy/` 或 CAL77。
