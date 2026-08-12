# 商品B 物流核算审计记录

> 商品B：帆布袋定制（竖款 本色2025）
> 运行时间：2026-08-06
> Git SHA：b5cd600

## 一、请求身份

- **request_id**：（由 run.py 自动生成）
- **product_signature**：（由 run.py 自动生成）
- **标题**：帆布袋定制 广告宣传棉布手提袋空白购物袋单肩帆布包定做
- **SKU**：竖款 本色2025
- **数量**：1件
- **模式**：`head_only`（沿用本地已保存）

## 二、图片分组与SKU关联

本次 3 张图片归类：
- 图1（波点化妆包主图+规格列表）：属于商品A（不同商品）
- 图2（帆布袋主图+规格列表）：属于商品B
- 图3（化妆包包装信息表 28×18×11/400g）：属于商品A（不同商品）

SKU关联过程：
1. 图2规格列表显示已选「竖款 本色2025」SKU（数量1，价格¥0.76）
2. 该SKU的命名规则「2025」按商家 SKU 编码约定解析为 20×25cm
3. 图2主图标注「竖款手提袋35×40cm」是商家为最大SKU展示的尺寸，不属于当前选中SKU「竖款 本色2025」，不能直接套用
4. 目标SKU确认为「竖款 本色2025」；不采用「竖款 本色35×40」等其他款式的尺寸

## 三、关键事实与来源

| 字段 | 值 | source | scope | confidence | location |
|---|---|---|---|---|---|
| `purchase_price_rmb` | 0.76 | user_confirmed | - | high | 图2规格列表「竖款 本色2025 ¥0.76」 |
| `domestic_freight_rmb` | 0.00 | user_confirmed | - | high | 图2「包邮」 |
| `net_weight` | 0.08 kg (80 g) | ai_inferred | net_weight | low | 商家未给出当前SKU重量，AI 按小型帆布袋常见重量估算 |
| `product_size` | [25, 20, 4] cm | merchant_text + ai_inferred | product_size | low | 25×20cm 来自SKU名"2025"按命名规则解析(merchant_text)；厚度4cm为AI推断 |
| `material_family` | canvas | image_visible | - | high | 图2主图可见帆布袋外观 |

> 注：25×20cm 是从 SKU 命名「2025」解析的商品净尺寸；厚度4cm 和重量80g 由 AI 按小型帆布袋常见规格估算（因商家未提供）。商家未额外标注运输外箱尺寸。

## 四、结构证据（structure_evidence）

| fact | source | location |
|---|---|---|
| soft_canvas | image_visible | 图2主图帆布袋呈软质自然褶皱外观，无硬壳结构 |
| soft_handles | image_visible | 图2主图帆布提手带，软质 |
| size_sku_2025 | merchant_text | SKU名「竖款 本色2025」，按命名规则解析为20×25cm |
| no_weight_data | image_visible | 图2未给出当前SKU的重量数据 |

## 五、AI JSON 必填字段检查

| 字段 | 值 | 状态 |
|---|---|---|
| `selected_sku` | 竖款 本色2025 | ✓ |
| `quantity` | 1 | ✓ |
| `material_family` | canvas | ✓ |
| `dimension_scope` | product_size | ✓ |
| `weight_scope` | net_weight | ✓ |
| `structure_evidence` | 4条 | ✓ |
| `rigidity` | soft | ✓ |
| `foldability` | good | ✓ |
| `compressibility` | good | ✓ |
| `overall_form` | soft_flat | ✓ |
| `has_rigid_parts` | false | ✓ |
| `requires_shape_retention` | false | ✓ |
| `ai_net_weight_kg` | 0.08 | ✓ |
| `ai_package_size_cm` | [25, 20, 4] | ✓ |
| `ai_package_weight_kg` | 0.085 | ✓ |
| `conservative_package_size_cm` | [25, 20, 4] | ✓ |
| `conservative_package_weight_kg` | 0.085 | ✓ |

## 六、精确校准

- 是否命中：**否**
- 原因：当前标题 + SKU（竖款 本色2025）在 `calibration_cases.jsonl` 中未找到精确命中，立即进入正常估算，未做模糊搜索。

## 七、包装聚合规则命中

- **命中规则**：`ARB-OXFORD-BAG-001`
- 优先级：5
- 触发条件：
  - `material_family` ∈ {oxford, canvas, fabric} ✓ (canvas)
  - `category` ∈ {bag} ✓
  - `no_strong_hard_evidence` ✓ (has_rigid_parts=false)
- 规则动作：
  - `compress_min_axis_only`：仅压缩最小轴（厚度）
  - `min_axis_scale_normal`：0.40
  - `min_axis_scale_conservative`：0.62
  - `min_axis_cm`：4.0
  - `preserve_length_width`：true（保留长宽）
- 实际效果：
  - 初始 [25, 20, 4] → min axis = 4
  - 正常档：max(4×0.40, 4.0) = max(1.6, 4.0) = **4.0**（受 min_axis_cm 限制，不变）
  - 保守档：max(4×0.62, 4.0) = max(2.48, 4.0) = **4.0**（不变）
  - 最终尺寸保持 [25, 20, 4]

| 维度 | 仲裁前 | 仲裁后（正常） | 仲裁后（保守） |
|---|---|---|---|
| 长×宽×厚 cm | 25×20×4 | 25×20×4 | 25×20×4 |
| packaging_method | OPP袋 | OPP袋 | OPP袋 |
| folding_action | 把手折叠 | 把手折叠 | 把手折叠 |

## 八、仲裁前 AI JSON（关键字段）

```json
{
  "product_type": "canvas_tote_bag",
  "selected_sku": "竖款 本色2025",
  "category": "bag",
  "material_family": "canvas",
  "rigidity": "soft",
  "foldability": "good",
  "compressibility": "good",
  "has_rigid_parts": false,
  "requires_shape_retention": false,
  "ai_net_weight_kg": 0.08,
  "ai_package_size_cm": [25, 20, 4],
  "ai_package_weight_kg": 0.085,
  "conservative_package_size_cm": [25, 20, 4],
  "conservative_package_weight_kg": 0.085,
  "overall_form": "soft_flat",
  "dimension_scope": "product_size",
  "weight_scope": "net_weight",
  "shape_retention_scope": "none",
  "conservative_risk_basis": "weight_uncertainty",
  "foldable_parts": ["handle"]
}
```

## 九、仲裁后 AI JSON（关键字段）

```json
{
  "product_type": "canvas_tote_bag",
  "selected_sku": "竖款 本色2025",
  "category": "bag",
  "material_family": "canvas",
  "rigidity": "soft",
  "foldability": "good",
  "compressibility": "good",
  "has_rigid_parts": false,
  "requires_shape_retention": false,
  "ai_net_weight_kg": 0.08,
  "ai_package_size_cm": [25, 20, 4],
  "ai_package_weight_kg": 0.085,
  "conservative_package_size_cm": [25, 20, 4],
  "conservative_package_weight_kg": 0.085,
  "overall_form": "soft_flat",
  "dimension_scope": "product_size",
  "weight_scope": "net_weight",
  "shape_retention_scope": "none",
  "conservative_risk_basis": "weight_uncertainty",
  "foldable_parts": ["handle"],
  "packaging_method": "OPP袋",
  "folding_action": "把手折叠",
  "compression_action": "轻度压缩"
}
```

## 十、最终 Renderer 输出（stdout 原文）

```
商品：帆布袋定制 广告宣传棉布手提袋空白购物袋单肩帆布包定做，1件；采购价¥0.76，国内运费¥0；正常档采用，保守档采用，识别置信度low。

| 方案 | 包装尺寸（cm） | 包装后重量（g） | 计费重（g） | 纯头程（¥） | 固定费（¥） | 总头程（¥） |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 义乌正常 | 25×20×4 | 85 | 85 | 8.50 | 6.00 | 14.50 |
| 义乌保守 | 25×20×4 | 85 | 85 | 8.50 | 6.00 | 14.50 |
| 深圳正常 | 25×20×4 | 85 | 85 | 6.80 | 10.00 | 16.80 |
| 深圳保守 | 25×20×4 | 85 | 85 | 6.80 | 10.00 | 16.80 |

推算：把手折叠；正常档计费重85g，保守档计费重85g；体积重主导；四种方案中义乌正常总头程最低，为¥14.50。
```