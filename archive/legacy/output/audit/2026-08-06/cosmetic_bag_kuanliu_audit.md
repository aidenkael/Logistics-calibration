# 物流核算审计记录

> 本次盲测商品：高颜值新款手提防水旅行洗漱包整理袋（黑色款式六）
> 运行时间：2026-08-06T11:06:53
> Git SHA：b5cd600

## 一、请求身份

- **request_id**：`req-61182200-1`
- **product_signature**：`83612e303e18045c`
- **标题**：高颜值新款手提防水旅行洗漱包整理袋随身大容量化妆品收纳包批发
- **SKU**：黑色款式六
- **数量**：1件
- **模式**：`head_only`（默认沿用本地已保存）

## 二、关键事实与来源

| 字段 | 值 | source | scope | 置信度 | 说明 |
|---|---|---|---|---|---|
| `purchase_price_rmb` | 9.00 | user_confirmed | - | high | 截图1价格行 ¥9.00 |
| `domestic_freight_rmb` | 5.00 | user_confirmed | - | high | 截图1"另需运费(预估): ¥5" |
| `net_weight` | 0.1 kg (100 g) | image_visible → user_confirmed | - | high | 截图3重量表"款六0.1kg"，用户已选款式六 |
| `display_size` | [22, 18, 10] cm | image_visible | display_size | medium | 截图2尺寸图为"款式二"专用的 22×18×10cm，并非用户选中款式六的shipping尺寸 |
| `shipping_package_size` | (无) | - | - | - | 用户选款式六，但商家未给出款式六尺寸；不能机械等同款式二 |

> 备注：`display_size` 是款式二的展示尺寸（image_visible），按事实来源契约，**不直接等同于用户所选款式六的 shipping_package_size**，仅作 AI 推断款式六包装尺寸的参考依据。

## 三、材质与结构证据（structure_evidence）

| fact | source | location |
|---|---|---|
| transparent_panel | image_visible | 图1主图正面可见透明PVC/TPU窗口 |
| fabric_panel_with_print | image_visible | 图1主图侧面印花布料面（米色+alo字样） |
| soft_handles | image_visible | 图2尺寸图顶部织带提手（顶高15cm） |
| no_hard_bottom_visible | image_visible | 图1主图无可见硬底/硬框/硬衬结构，袋子自然下榻 |
| size_kuaner_display | image_visible | 图2尺寸图标注款二 22×18×10cm（主体） |
| weight_table_kuanliu | merchant_text | 图3重量表款六=0.1kg |

## 四、当前 SKU 是否命中所要求的字段

| AGENTS.md 要求字段 | 当前 AI JSON | 备注 |
|---|---|---|
| material_family | `transparent_soft_plastic` | ✓ |
| dimension_scope | `display_size` | ✓（款式二图片可见） |
| structure_evidence | 6 条 | ✓ |
| rigidity | `soft` | ✓ |
| foldability | `good` | ✓ |
| compressibility | `good` | ✓ |
| overall_form | `soft_hollow`（仲裁后保持） | ✓ |
| has_rigid_parts | false | ✓ |
| requires_shape_retention | false | ✓ |

## 五、精确校准

- 是否命中：**否**
- 原因：当前标题 + SKU（黑色款式六）在 `calibration_cases.jsonl` 中未找到精确命中，立即进入正常估算，未做模糊搜索。

## 六、包装聚合规则命中

- **命中规则 ID**：`ARB-PVC-THIN-001`
- 优先级：10
- 触发条件全部满足：
  - product_type_keywords 命中（标题含"收纳包"/cosmetic_bag）
  - material_family ∈ {pvc, tpu, transparent_soft_plastic} ✓
  - rigidity = soft ✓
  - foldability ∈ {good, limited} ✓
  - no_strong_hard_evidence = true ✓
- 规则动作效果：
  - 厚度轴（10cm）按公式压缩：3 × √(22×18 / 10×10) = 3 × 1.99 = 6.0
  - 保守档：5 × √(22×18 / 14×12) = 5 × 1.535 = 7.7
  - normal_packaging_method → "充分折叠后袋装"
  - 折叠动作叠加 "把手折叠"

| 维度 | 仲裁前 | 仲裁后（正常） | 仲裁后（保守） |
|---|---|---|---|
| 长×宽×厚 cm | 22×18×10 | 22×18×6.0 | 22×18×7.7 |
| packaging_method | OPP袋 | 充分折叠后袋装 | 充分折叠后袋装 |
| folding_action | 把手折叠 | 把手折叠 | 把手折叠 |

> 注：选择此规则是因为款式二图片中可见明显的透明 PVC/TPU 窗口，符合商品属于"薄款透明软包"的形态归类。在仲裁规则系统中，本规则是 `transparent_panel + soft + bag + 透明塑料材质` 的最高优先级匹配。

## 七、仲裁前 AI JSON（截选关键字段）

```json
{
  "product_type": "cosmetic_bag",
  "category": "bag",
  "material_family": "transparent_soft_plastic",
  "rigidity": "soft",
  "foldability": "good",
  "compressibility": "good",
  "has_rigid_parts": false,
  "requires_shape_retention": false,
  "ai_net_weight_kg": 0.1,
  "ai_package_size_cm": [22, 18, 10],
  "ai_package_weight_kg": 0.105,
  "conservative_package_size_cm": [22, 18, 10],
  "conservative_package_weight_kg": 0.105,
  "overall_form": "soft_hollow",
  "dimension_scope": "display_size",
  "weight_scope": "net_weight",
  "modifiers": ["hollow"],
  "shape_retention_scope": "none"
}
```

## 八、仲裁后 AI JSON（截选关键字段）

```json
{
  "product_type": "cosmetic_bag",
  "category": "bag",
  "material_family": "transparent_soft_plastic",
  "rigidity": "soft",
  "foldability": "good",
  "compressibility": "good",
  "has_rigid_parts": false,
  "requires_shape_retention": false,
  "ai_net_weight_kg": 0.1,
  "ai_package_size_cm": [22, 18, 6.0],
  "ai_package_weight_kg": 0.105,
  "conservative_package_size_cm": [22, 18, 7.7],
  "conservative_package_weight_kg": 0.105,
  "overall_form": "soft_hollow",
  "dimension_scope": "display_size",
  "weight_scope": "net_weight",
  "modifiers": ["hollow"],
  "shape_retention_scope": "none",
  "packaging_method": "充分折叠后袋装",
  "folding_action": "把手折叠",
  "compression_action": "轻度压缩"
}
```

## 九、最终 Renderer 输出（stdout 原文）

```
商品：高颜值新款手提防水旅行洗漱包整理袋随身大容量化妆品收纳包批发，1件；采购价¥9.0，国内运费¥5.0；正常档采用，保守档采用，识别置信度low。

| 方案 | 包装尺寸（cm） | 包装后重量（g） | 计费重（g） | 纯头程（¥） | 固定费（¥） | 总头程（¥） |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 义乌正常 | 22×18×6 | 105 | 297 | 29.70 | 6.00 | 35.70 |
| 义乌保守 | 22×18×8 | 105 | 381 | 38.12 | 6.00 | 44.12 |
| 深圳正常 | 22×18×6 | 105 | 297 | 23.76 | 10.00 | 33.76 |
| 深圳保守 | 22×18×8 | 105 | 381 | 30.50 | 10.00 | 40.50 |

推算：把手折叠；正常档计费重297g，保守档计费重381g；体积重主导；四种方案中深圳正常总头程最低，为¥33.76。
```

## 十、本次推算补充说明（仅审计留存，不进入最终回复）

- 体积重主导：22×18×6 / 8000 = 0.297 kg，按 max(0.105, 0.297)=0.297 kg 计费
- 选货代：计费重 0.297 kg > 0.2 kg 临界点，深圳单价 80 ¥/kg 比义乌 100 ¥/kg 的优势大于固定费 ¥4 差额，因此深圳正常档最优（¥33.76）
- 风险提示：款式六的真实尺寸未知（仅款式二的 display_size 已知），实际款式六可能比款式二更小，因此本估算存在「可能略偏大」的不确定性
