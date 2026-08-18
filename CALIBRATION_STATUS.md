# Calibration Status

- 当前 Clean Rules 版本：0（暂无 Clean Rules）
- 软件已生效规则：0（暂无作用范围）
- 已批准但尚未发布：2（用户已确认批准，等待部署）
  1. **展示/支撑态≠运输态**：可压/可折商品被按展示或展开态计量导致极端高估。7 条独立记录（约 5 条独立商品线）支持，方向稳定 HIGH，均有用户备注直接支持，无明显反例。建议部署层：Prompt。对应记录状态：APPROVED_PENDING_PUBLICATION（CAL-0019/0026/0047/0050/0071/0074/0077）。
  2. **自然折叠/袋装/收纳状态保护**：如果图片或页面已经呈现合理的自然折叠、袋装、闭合、收纳或接近实际运输状态，并且没有更强的新包装证据，不应无依据重新展开、撑开或二次压缩。已逐个读图复核（未调用任何 AI）：真正支持 23 条独立商品（001/004/005/008/012/014/020/034/035/038/043/044/048/049/052/056/057/058/059/060/066/070/076），图片/页面已呈自然收纳或接近运输态且 A 组保持后准确；33 保护集中其余 10 条（010/015/018/028/030/039/046/051/061/079）图为佩戴/悬挂/展开/填充展示态，仅为普通 Replay 保护样本，不计入该规律。保护集内部无明显反例；边界反例材料：032/082（图片已自然平放但 A 组仍 +50%/+97.4% HIGH，因无真实尺寸因果未证实，列于保护集外；运输状态判断合理，也可能存在具体尺寸估算误差，不能据此删除状态保护原则）。建议部署层：Prompt（保持/保护型）。对应记录状态：APPROVED_PENDING_PUBLICATION（23 条）。
- PATTERN_CANDIDATE（3–4 独立样本，未达询问门槛）：1
  1. 小件发货包装（盒/防护包装）未被识别导致系统性低估。4 条记录（021/029/031/033），其中 3 条有用户备注直接支持，方向稳定 LOW。
- 尚未形成规则的数据：83（批次83全部，CAL-0001 至 CAL-0083）；主要机制分布：SHAPE_RETAINED 40 / FULL_FLAT_FOLD 29 / MODERATE_COMPRESSION 11 / STRONG_COMPRESSION 3。
- Replay 保护集：33 条（CAL-0001、CAL-0004、CAL-0005、CAL-0008、CAL-0010、CAL-0012、CAL-0014、CAL-0015、CAL-0018、CAL-0020、CAL-0028、CAL-0030、CAL-0034、CAL-0035、CAL-0038、CAL-0039、CAL-0043、CAL-0044、CAL-0046、CAL-0048、CAL-0049、CAL-0051、CAL-0052、CAL-0056、CAL-0057、CAL-0058、CAL-0059、CAL-0060、CAL-0061、CAL-0066、CAL-0070、CAL-0076、CAL-0079），其中 23 条同时为自然收纳保护规律支持样本、10 条为普通保护样本。任何新 candidate 必须 Replay 该集合及旧错误修正样本，不得静默破坏。
- 证据图片稳定路径：批次83 全部 145 张原始证据图（约 29MB，未重编码）已入库 `data/product_images/prima83/`，记录内引用为仓库相对路径，可长期 Replay。
- 最近一次重要变化：2026-08-16，用户确认批准 2 条规律（展示/支撑态≠运输态、自然折叠/袋装/收纳状态保护），30 条记录状态更新为 APPROVED_PENDING_PUBLICATION；Clean Rules 仍为 0、SOFTWARE_ACTIVE 仍为 0；未生成 Rule Package、未写 EXPORTED_PENDING_ACTIVATION、未修改 Governance/Schema/2.6.1。
- 批次83 最终收口：2026-08-16 完成。最终正式规则包 1 个（`data/formal_rule_package_fb83_final.json`，Agent Calibration Rule Package V1，status=candidate，通过 2.6.1 官方 validator，0 issues），内含 2 条保护规则：
  1. **fb83-protect-shape-retention-v1（硬质/保形保护）**：requires_shape_retention=true 且有可靠刚性证据时禁止无依据压缩/折叠（保持型 scale=1.0）；支持 9 条硬质样本（CAL-0003/0005/0006/0012/0014/0021/0038/0052/0076），保护边界 012/076。
  2. **fb83-protect-natural-storage-v1（自然收纳/软质折叠保护）**：foldability=good+compressibility=good+非硬质时保持收纳外廓，防无依据再展开/二次压缩；支持 17 条软质收纳样本，保护边界 001/034/043/059/066。
- 展示态≠运输态：不单独成规则（V1 词汇无法表达运输外廓数值纠正，且禁反推压缩率），治理意图由引擎内建 `_display_outline_requires_transport_evidence` 承担；触发前置为上游填充柔性商品 requires_shape_retention/dimension_scope。小件包装低估（021/029/031/033）继续保持 PATTERN_CANDIDATE，不进入规则包。
- 规则零命中的根因：83 条 observation 语义字段（rigidity/foldability/compressibility/requires_shape_retention/packing_actions/overall_form）全为空 + 无真实包装 truth；接入最小要求见 `docs/FB83_FINAL_CLOSURE_REPORT.md` §8（全部为数据捕获层字段填充，引擎无修改点）。
- **2026-08-17 费用反推重算完成**：原始 v1.3 baseline、用户备注和实际纯头程全部保持不动；新增 `data/fb83_freight_inference_v1.csv` 与 `docs/FB83_FREIGHT_REINFERENCE_2026-08-17.md`。83/83 可计算费率等价计费重量；79 条 evidence=B 可作为边界证据，002/025/041/075 四条 evidence=D 继续 HOLD。由于 83 条 `actual.weight` 与 `actual.dimensions` 均为空，当前 0 条能够仅凭结构化数据证明实重/体积重主导，0 条可可靠反推运输总体积或长宽高范围；本轮新增数值 CAL=0。
- 2026-08-17 重算进一步支持：展示/支撑态≠运输态的 7 条明确异常样本实际/基线比值约 0.083–0.643，离散很大，因此继续禁止固定压缩倍率；小件包装 4 条 actual/baseline 约 1.60–3.33，方向稳定但无法区分实重/体积来源，继续 PATTERN_CANDIDATE。
- 历史 83 条首次 AI baseline 继续冻结，不允许覆盖；后续新 Prompt 结果必须独立保存。费用派生分析可以继续追加，但不得把 AI baseline 的尺寸/重量当成 truth 自证。
- 当前下一步：暂不重跑新 Prompt。只有获得实际包装后重量、商家可信重量、实际包装尺寸或货代称重/体积记录等独立证据时，再升级实重/体积重主导、总体积或尺寸范围判断。
- **2026-08-18 软件 ↔ 校准 Agent 闭环最小桥接**：新建 `integration/software-calibration-v2` 分支。主入口改为 `tools/software_feedback_v2_intake.py`（读取 Calibration Feedback Export V2）；合同自检 `tools/check_software_contract.py`；去重索引 `data/software_import_index.json`。全部调用主软件官方工具（Validator / Offline Replay / Promotion / Bundle Builder），Agent 不自行实现发布链。83 条历史数据、145 张图片、费用反推结果、旧 candidate 全部 byte-level 冻结。
