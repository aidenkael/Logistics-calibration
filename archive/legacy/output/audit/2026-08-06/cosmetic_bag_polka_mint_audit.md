# 商品A 物流核算审计记录

> 商品A：波点便携手提化妆包（波点薄荷）
> 运行时间：2026-08-06
> Git SHA：b5cd600

## 一、请求身份

- **request_id**：（由 run.py 自动生成）
- **product_signature**：（由 run.py 自动生成）
- **标题**：波点便携手提化妆包女超大容量三层收纳防水旅行洗漱包可爱高颜值
- **SKU**：波点薄荷
- **数量**：1件
- **模式**：`head_only`（沿用本地已保存）

## 二、图片分组与SKU关联

本次 3 张图片归类：
- 图1（商品主图+规格列表）：属于商品A
- 图2（帆布袋主图+规格列表）：属于商品B（不同商品）
- 图3（包装信息表 28×18×11/400g）：属于商品A

SKU关联过程：
1. 图1规格列表显示已选「波点薄荷」SKU（数量1，价格¥13.50）
2. 图3包装信息表显示「波点薄荷 28×18×11cm 400g」与图1规格列表的「波点薄荷」自动对应
3. 目标SKU确认为「波点薄荷」；不采用「波点草莓」的同尺寸数据（虽然数值相同，但属不同款式）

## 三、关键事实与来源

| 字段 | 值 | source | scope | confidence | location |
|---|---|---|---|---|---|
| `purchase_price_rmb` | 13.50 | user_confirmed | - | high | 图1规格列表「波点薄荷 ¥13.50」 |
| `domestic_freight_rmb` | 3.20 | user_confirmed | - | high | 图1「另需运费(预估): ¥3.2」 |
| `net_weight` | 0.4 kg (400 g) | merchant_text → user_confirmed | net_weight | high | 图3「波点薄荷 400g」 |
| `product_size` | [28, 18, 11] cm | merchant_text | product_size | medium | 图3「波点薄荷 28×18×11cm」 |
| `material_family` | pu | ai_inferred | - | medium | 图1主图PU皮印刷表面+EVA硬衬推断 |

> 注：28×18×11cm 来自商家「包装信息/商品净重」表，是商品净尺寸（product_size），不属于已确认的运输包装尺寸（shipping_package_size）。商家未额外标注运输外箱尺寸。

## 四、结构证据（structure_evidence）

| fact | source | location |
|---|---|---|
| rigid_lining | image_visible | 图1主图化妆包主体保持完整矩形立体外廓，无下塌特征（强证据） |
| soft_handles | image_visible | 图1主图顶部织带手提把，软质 |
| hollow_interior | image_visible | 化妆包为收纳类，内部空心设计 |
| size_polka_mint | merchant_text | 图3包装信息表波点薄荷 28×18×11cm 400g |

## 五、AI JSON 必填字段检查

| 字段 | 值 | 状态 |
|---|---|---|
| `selected_sku` | 波点薄荷 | ✓ |
| `quantity` | 1 | ✓ |
| `material_family` | pu | ✓ |
| `dimension_scope` | product_size | ✓ |
| `weight_scope` | net_weight | ✓ |
| `structure_evidence` | 4条 | ✓ |
| `rigidity` | semi_rigid | ✓ |
| `foldability` | limited | ✓ |
| `compressibility` | none | ✓ |
| `overall_form` | semi_structured_hollow | ✓ |
| `has_rigid_parts` | true | ✓ |
| `requires_shape_retention` | false | ✓ |
| `ai_net_weight_kg` | 0.4 | ✓ |
| `ai_package_size_cm` | [28, 18, 11] | ✓ |
| `ai_package_weight_kg` | 0.41 | ✓ |
| `conservative_package_size_cm` | [28, 18, 11] | ✓ |
| `conservative_package_weight_kg` | 0.41 | ✓ |

## 六、精确校准

- 是否命中：**否**
- 原因：当前标题 + SKU（波点薄荷）在 `calibration_cases.jsonl` 中未找到精确命中，立即进入正常估算，未做模糊搜索。

## 七、包装聚合规则命中

- **命中规则**：无
- 检查过程：
  - ARB-PU-BAG-001：material_family=pu ✓、category=bag ✓，但 no_strong_hard_evidence = **false**（有 rigid_lining 强证据），故不匹配
  - ARB-OXFORD-BAG-001：material_family 不在 {oxford, canvas, fabric}，故不匹配
  - 其他规则均不匹配
- 仲裁后尺寸保持原值 [28, 18, 11] 不变

## 八、仲裁前 AI JSON（关键字段）

```json
{
  "product_type": "cosmetic_bag",
  "selected_sku": "波点薄荷",
  "category": "bag",
  "material_family": "pu",
  "rigidity": "semi_rigid",
  "foldability": "limited",
  "compressibility": "none",
  "has_rigid_parts": true,
  "requires_shape_retention": false,
  "ai_net_weight_kg": 0.4,
  "ai_package_size_cm": [28, 18, 11],
  "ai_package_weight_kg": 0.41,
  "conservative_package_size_cm": [28, 18, 11],
  "conservative_package_weight_kg": 0.41,
  "overall_form": "semi_structured_hollow",
  "dimension_scope": "product_size",
  "weight_scope": "net_weight",
  "shape_retention_scope": "body",
  "modifiers": ["hollow"]
}
```

## 九、仲裁后 AI JSON（关键字段）

```json
{
  "product_type": "cosmetic_bag",
  "selected_sku": "波点薄荷",
  "category": "bag",
  "material_family": "pu",
  "rigidity": "semi_rigid",
  "foldability": "limited",
  "compressibility": "none",
  "has_rigid_parts": true,
  "requires_shape_retention": false,
  "ai_net_weight_kg": 0.4,
  "ai_package_size_cm": [28, 18, 11],
  "ai_package_weight_kg": 0.41,
  "conservative_package_size_cm": [28, 18, 11],
  "conservative_package_weight_kg": 0.41,
  "overall_form": "semi_structured_hollow",
  "dimension_scope": "product_size",
  "weight_scope": "net_weight",
  "shape_retention_scope": "body",
  "modifiers": ["hollow"],
  "folding_action": "不折叠",
  "compression_action": "不压缩"
}
```

## 十、最终 Renderer 输出（stdout 原文）

```
商品：波点便携手提化妆包女超大容量三层收纳防水旅行洗漱包可爱高颜值，1件；采购价¥13.5，国内运费¥3.2；正常档采用，保守档采用，识别置信度low。

| 方案 | 包装尺寸（cm） | 包装后重量（g） | 计费重（g） | 纯头程（¥） | 固定费（¥） | 总头程（¥） |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 义乌正常 | 28×18×11 | 410 | 693 | 69.30 | 6.00 | 75.30 |
| 义乌保守 | 28×18×11 | 410 | 693 | 69.30 | 6.00 | 75.30 |
| 深圳正常 | 28×18×11 | 410 | 693 | 55.44 | 10.00 | 65.44 |
| 深圳保守 | 28×18×11 | 410 | 693 | 55.44 | 10.00 | 65.44 |

推算：不折叠；正常档计费重693g，保守档计费重693g；体积重主导；四种方案中深圳正常总头程最低，为¥65.44。
```