# 批次 83 校准收口报告（最终版）

- 日期：2026-08-16
- 范围：CAL-0001 ~ CAL-0083（83 条）最终收口，不再开展新实验
- 基线：Profit-Accounting 2.6.1 main（`packaging-estimation-v2-candidate-arbitration`，空 registry `runtime-safety-empty-v1`，empty baseline `runtime-safety-baseline-v1`）
- 本报告与规则文件**未修改任何 2.6.1 文件、未调用 AI API、未重新识别图片、未导入、未激活任何规则**。

---

## 1. 最终形成几条规则

**2 条正式规则**（均已写入 Rule Package，通过 2.6.1 官方 `AgentCalibrationRulePackageValidator` 校验，is_valid=True、0 issues）。另有 1 个治理意图（展示态≠运输态）不单独成规则，由引擎内建检查承担；1 个候选（小件低估）不进入。

## 2. 每条规则中文意思

- **R1 `fb83-protect-shape-retention-v1`（硬质/保形保护）**：当 observation 判定 `requires_shape_retention=true` 且有可靠刚性证据（硬底/硬框/刚性部件/硬背板）时，CAL 以原始外廓为基准（scale=1.0），禁止 AI 或 CAL 无依据压扁、折叠或大幅缩小；AI 提案完整时零修改，缺字段时保持型填充。
- **R2 `fb83-protect-natural-storage-v1`（自然收纳/软质折叠保护）**：对 `foldability=good`、`compressibility=good` 且非硬质的商品，若已处于折叠/袋装/闭合/盘卷等收纳或接近运输状态，CAL 保持原始外廓（scale=1.0），防止无依据再次展开或二次压缩；不等于直接采用图片尺寸。

## 3. 保护规则 / 纠错规则

- **保护规则 2 条**（R1、R2）：均为"保持型"，不引入任何压缩率/倍数；`conservative:1.06` 为引擎既有默认保护边距，不是反推值。
- **纠错规则 0 条**：83 条无真实包装尺寸 truth + 用户禁止反推压缩率，V1 词汇无法表达"运输外廓数值纠正"，任何数值纠错规则都无合规依据，故不生成。

## 4. 各自主要由哪些 83 样本支持

- **R1**：硬质/保形 9 条——003 磨蒜器(-50%)、005 徽章(-13.3%)、006 徽章(+100%)、012 招财猫(0%)、014 保温杯(+8.7%)、021 卡祖笛(-64.3%)、038 象鼻神(-13.1%)、052 麦芽糖球(-14.3%)、076 化妆镜(-3.4%)。
- **R2**：自然收纳支持 23 条中的 17 条软质可折叠样本——HIGH 6（008 贝壳包 +12.5%、035 背带 +7.1%、056 粘毛器 +10%、057 便签夹 +5%、058 冰敷帽 +15.8%、070 折扇 +15.8%）、LOW 6（004 零钱包 -8.3%、020 皮革花 -6.2%、044 信封包 -8.8%、048 发抓 -10%、049 折叠水杯 -12%、060 行李牌 -12.5%）及 5 条正常样本（见下）。

## 5. 哪些正常样本用于防止误伤

- **R1 边界**：012 招财猫(0%)、076 化妆镜(-3.4%)——硬质但 AI 估算正确，R1 命中时零字段修改。
- **R2 边界**：001 分趾袜(0%)、034 手柄(0%)、043 宠物梳(+4.2%)、059 溜溜球(0%)、066 钥匙扣(0%)——软质收纳但 AI 已正确，R2 命中时保持外廓不破坏。
- **反例防护**：R1 对软质商品误填保形自证——引擎 `_remove_unsupported_shape_retention` 先移除，不放大 AI 自证；R2 对硬质商品误填 foldability=good——`forbid_hard_structure` 排除。
- 其余普通保护 10 条（010/015/018/028/030/039/046/051/061/079）与证据不足 4 条（002/025/041/075）不直接支撑任何规则，保留在记录中作为未来 Replay 保护集。

## 6. 小件包装候选为什么暂不进入

小件低估 4 条（021 卡祖笛 -64.3%、029 硅胶耳塞 -70%、031 香水夹 -37.5%、033 树脂摆件 -58.8%）方向稳定 LOW，但：①仅 4 条独立样本，未达治理门槛（约 5 个）；②无真实包装尺寸 truth，无法确定"盒装/防护包装"的外廓增量，任何数值规则都属反推。按用户指令继续保持 PATTERN_CANDIDATE，不进入本轮规则包。

## 7. 是否完全兼容当前 2.6.1 规则格式

**完全兼容**。match 仅用 {requires_shape_retention, foldability, compressibility, forbid_hard_structure}、guard 用 {any_hard_structure_or_shape_retention}、action 用 smallest_axis_scale，全部落在 V1 词汇集合内；evidence 为精确三键 {source_record_ids, sample_count, rationale}；包级字段（schema_version/status=candidate/validation=null/base_engine_version/source_export_batch_ids）全部通过官方 validator。

## 8. 当前若直接交给主软件，还缺什么最小接入条件

规则在 2.6.1 引擎中**零命中**的根因是上游 observation 语义字段为空（83 条 rigidity/foldability/compressibility/requires_shape_retention/packing_actions/overall_form 全部 unknown/空）。最小接入要求（数据捕获层，非引擎代码）：

1. AI 视觉/manual 录入填充 `rigidity`、`foldability`、`compressibility`、`requires_shape_retention`（R1/R2 命中所必需）；
2. 硬质/保形商品附带可靠刚性证据字段（has_hard_bottom / has_rigid_parts 等 + field_evidence 定位键），使引擎不移除保形结论（R1 前置）；
3. 软质商品产出 `packing_actions`（fold/roll/nest/compress）或 `packaging_state_hint`，使 R2 从"foldability 近似"缩窄为精确收纳态匹配；
4. 展示态≠运输态（R3 意图）触发前置：柔性商品填 `requires_shape_retention=false` + `dimension_scope` 标记，引擎内建 `_display_outline_requires_transport_evidence` 才能拒绝展示外廓当运输事实。

## 9. 是否需要修改主软件代码

**不需要**。引擎、validator、replay、promotion、runtime bundle 全链路零改动；0 命中的根因是数据捕获缺口，不是引擎缺陷。若未来接入（§8），修改点在**上游 observation 捕获链路**（数据层），引擎侧无任何修改点。

## 10. 最终文件路径

| 文件 | 路径 |
|---|---|
| 正式规则包（Rule Package，status=candidate） | `data/formal_rule_package_fb83_final.json` |
| 工作副本与草案过程档案 | `work/formal_bundle_draft_v1/`（gitignored） |
| 本收口报告 | `docs/FB83_FINAL_CLOSURE_REPORT.md` |
| 状态文件 | `CALIBRATION_STATUS.md`（已更新） |
| 83 条校准记录 | `data/calibration_records.jsonl`（CAL-0001 ~ CAL-0083，30 条 APPROVED_PENDING_PUBLICATION） |

## 11. Git 状态与 commit SHA

- 分支：`calibration/83-baseline-governance`（与 `origin/calibration/83-baseline-governance` 同步）
- 当前 HEAD：`0889005575c39e37c36b14e8c24e6dd26f5d8ff1`
- 工作树：3 个变更未提交（新增 `data/formal_rule_package_fb83_final.json`、新增 `docs/FB83_FINAL_CLOSURE_REPORT.md`、更新 `CALIBRATION_STATUS.md`）。本轮按要求**未自动提交/推送**；如需固化，由你指示后提交。

---

**批次 83 至此正式收口。未导入主软件、未修改 2.6.1、未调用 AI API、未激活规则。等待主软件对话框接入（见 §8 最小接入要求）。**
