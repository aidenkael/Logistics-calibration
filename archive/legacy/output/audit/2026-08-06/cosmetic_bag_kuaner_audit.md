# 物流核算审计记录

> 本次盲测商品：高颜值新款手提防水旅行洗漱包整理袋（款式二）
> 运行时间：2026-08-06T11:40:32
> Git SHA：b5cd600

## 一、请求身份

- **request_id**：`req-77997700-1`
- **product_signature**：`303d1827199b7f98`
- **标题**：高颜值新款手提防水旅行洗漱包整理袋随身大容量化妆品收纳包批发
- **SKU**：款式二
- **数量**：1件
- **模式**：`head_only`（沿用本地已保存）

## 二、关键事实与来源

| 字段 | 值 | source | scope | 置信度 | 说明 |
|---|---|---|---|---|---|
| `purchase_price_rmb` | 12.00 | user_confirmed | - | high | 截图1规格列表中款式二价格（用户确认） |
| `domestic_freight_rmb` | 5.00 | user_confirmed | - | high | 截图1「另需运费(预估): ¥5」 |
| `net_weight` | 0.17 kg (170 g) | merchant_text → user_confirmed | - | high | 图3重量表「款二 0.17kg」 |
| `display_size` | [22, 18, 10] cm | image_visible | display_size | medium | 图2尺寸图标注「款二」的展示尺寸，**非已确认运输包装尺寸** |

## 三、结构证据（structure_evidence）

| fact | source | location |
|---|---|---|
| transparent_panel | image_visible | 图1主图正面可见透明PVC/TPU窗口 |
| fabric_panel_with_print | image_visible | 图1主图侧面印花布料面（米色+alo字样） |
| soft_handles | image_visible | 图2尺寸图顶部织带提手（顶高15cm） |
| no_hard_bottom_visible | image_visible | 图1主图无可见硬底/硬框/硬衬，袋子自然下榻 |
| size_kuaner_display | image_visible | 图2尺寸图标注款二尺寸22×18×10cm（主体） |
| weight_table_kuaner | merchant_text | 图3重量表款二=0.17kg |

## 四、AI JSON 必填字段检查

| 字段 | 值 | 状态 |
|---|---|---|
| `material_family` | `transparent_soft_plastic` | ✓ |
| `dimension_scope` | `display_size` | ✓ |
| `structure_evidence` | 6条 | ✓ |
| `rigidity` | `soft` | ✓ |
| `foldability` | `good` | ✓ |
| `compressibility` | `good` | ✓ |
| `overall_form` | `soft_hollow` | ✓ |
| `has_rigid_parts` | `false` | ✓ |
| `requires_shape_retention` | `false` | ✓ |

## 五、精确校准

- 是否命中：**否**
- 原因：当前标题 + SKU（款式二）未在 `calibration_cases.jsonl` 精确命中，立即进入正常估算。

## 六、包装聚合规则命中

- **命中规则**：`ARB-PVC-THIN-001`
- 优先级：10
- 触发条件：
  - `product_type_keywords` 命中（标题含「收纳包」/ cosmetic_bag）✓
  - `material_family` ∈ {pvc, tpu, transparent_soft_plastic} ✓
  - `rigidity = soft` ✓
  - `foldability` ∈ {good, limited} ✓
  - `no_strong_hard_evidence = true` ✓
- 规则动作：
  - `no_display_thickness_as_shipping`：按 `_fix_thickness_min_axis_only` 压缩厚度
  - 正常档参考包 [10,10,3] → 3 × √(22×18 / 10×10) = 3 × 1.99 = **6.0 cm**
  - 保守档参考包 [14,12,5] → 5 × √(22×18 / 14×12) = 5 × 1.54 = **7.7 cm**
  - `normal_packaging_method` → 「充分折叠后袋装」

| 维度 | 仲裁前 | 仲裁后（正常） | 仲裁后（保守） |
|---|---|---|---|
| 长×宽×厚 cm | 22×18×10 | 22×18×6.0 | 22×18×7.7 |
| 包装方式 | OPP袋 | 充分折叠后袋装 | 充分折叠后袋装 |
| 折叠动作 | 把手折叠 | 把手折叠 | 把手折叠 |

## 七、仲裁前 AI JSON（关键字段）

```json
{
  "product_type": "cosmetic_bag",
  "selected_sku": "款式二",
  "category": "bag",
  "material_family": "transparent_soft_plastic",
  "rigidity": "soft",
  "foldability": "good",
  "compressibility": "good",
  "has_rigid_parts": false,
  "requires_shape_retention": false,
  "ai_net_weight_kg": 0.17,
  "ai_package_size_cm": [22, 18, 10],
  "ai_package_weight_kg": 0.18,
  "conservative_package_size_cm": [22, 18, 10],
  "conservative_package_weight_kg": 0.18,
  "overall_form": "soft_hollow",
  "dimension_scope": "display_size",
  "weight_scope": "net_weight",
  "conservative_risk_basis": "thickness_uncertainty",
  "modifiers": ["hollow"],
  "foldable_parts": ["handle"],
  "shape_retention_scope": "none"
}
```

## 八、仲裁后 AI JSON（关键字段）

```json
{
  "product_type": "cosmetic_bag",
  "selected_sku": "款式二",
  "category": "bag",
  "material_family": "transparent_soft_plastic",
  "rigidity": "soft",
  "foldability": "good",
  "compressibility": "good",
  "has_rigid_parts": false,
  "requires_shape_retention": false,
  "ai_net_weight_kg": 0.17,
  "ai_package_size_cm": [22, 18, 6.0],
  "ai_package_weight_kg": 0.18,
  "conservative_package_size_cm": [22, 18, 7.7],
  "conservative_package_weight_kg": 0.18,
  "overall_form": "soft_hollow",
  "dimension_scope": "display_size",
  "weight_scope": "net_weight",
  "packaging_method": "充分折叠后袋装",
  "folding_action": "把手折叠",
  "compression_action": "轻度压缩",
  "modifiers": ["hollow"],
  "shape_retention_scope": "none"
}
```

## 九、推算摘要（仅审计留存，不进入最终回复）

- 软品空心，体积重主导：正常档22×18×6.0/8000=0.297kg > 包装重0.18kg
- 计费重 0.297kg > 0.2kg 临界点 → 深圳单价¥80更低，所选货代为深圳正常档
- 深圳正常档：纯头程¥23.76 + 固定费¥10 = **¥33.76**
- 风险：款式二的22×18cm L×W面未经运输包装确认，实际可能有偏差

## 十、最终 Renderer 输出（stdout 原文）

```
商品：高颜值新款手提防水旅行洗漱包整理袋随身大容量化妆品收纳包批发，1件；采购价¥12.0，国内运费¥5.0；正常档采用，保守档采用，识别置信度low。

| 方案 | 包装尺寸（cm） | 包装后重量（g） | 计费重（g） | 纯头程（¥） | 固定费（¥） | 总头程（¥） |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 义乌正常 | 22×18×6 | 180 | 297 | 29.70 | 6.00 | 35.70 |
| 义乌保守 | 22×18×8 | 180 | 381 | 38.12 | 6.00 | 44.12 |
| 深圳正常 | 22×18×6 | 180 | 297 | 23.76 | 10.00 | 33.76 |
| 深圳保守 | 22×18×8 | 180 | 381 | 30.50 | 10.00 | 40.50 |

推算：把手折叠；正常档计费重297g，保守档计费重381g；体积重主导；四种方案中深圳正常总头程最低，为¥33.76。
```
