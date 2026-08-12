# Calibration Workflow

1. 选择入口：已有软件保存的首次 AI baseline 时，使用 `tools/calibration_intake.py` 直接导入；只有图片时，使用 `tools/direct_calibration.py` 调用当前 Profit-Accounting 首次视觉服务取得 baseline。两条入口最终都追加同一个 Calibration Record。
2. Direct Calibration 若没有用户校准，只预览 baseline、不写入记录；已有完整 baseline 时不重复调用 AI。
3. 为记录填写已知事实、误差原因、方向与可判断的五类物理机制；不确定为 `UNKNOWN`/`null`。
4. 按当前记录聚合真正独立的商品，判断机制、原因、方向、证据、反例和样本多样性。
5. 1–2 条只记录；3–4 条稳定时标记 `PATTERN_CANDIDATE`；约 5 条且全部治理条件满足时询问用户是否纳入待发布。
6. 用户同意后只标记 `APPROVED_PENDING_PUBLICATION`，并更新 `CALIBRATION_STATUS.md`；不生成、导出、导入或启用规则。
7. 外部软件正式流程完成并确认实际激活后，才允许标记 `SOFTWARE_ACTIVE`；本项目的 intake 不能写入该状态。

进度查询首先读取 `CALIBRATION_STATUS.md` 和必要的 `data/calibration_records.jsonl`。`archive/legacy/` 只在用户明确要求档案或回归参考时读取。
