# Hello Kitty PVC 化妆包 头程估算过程文档

> 商品：2026新款透明手提化妆包大容量防水包包HelloKitty可爱收纳包BL
> 日期：2026-08-04 | 模式：仅头程 | 结果：normal ✅（命中精确校准案例）

---

## 一、模式确认

用户输入"仅头程" + 商品截图，直接进入模式 2（仅头程），无需参数询问。

---

## 二、商品识别

通过 1688 截图提取关键信息：

| 字段 | 值 |
|---|---|
| 商品标题 | 2026新款透明手提化妆包大容量防水包包HelloKitty可爱收纳包BL |
| 选中 SKU | 凯蒂猫大包 |
| 数量 | 1 件 |
| 采购价 | ¥16.83 |
| 商家 | 军送包具 |
| 材质 | 透明 PVC / TPU |
| 结构 | 软质空心手提化妆包 |

---

## 三、精确校准键查询

按 AGENTS.md "每商品快速路径"规则，执行精确校准查询：

```bash
grep -i "HelloKitty|化妆包|凯蒂猫" knowledge/calibration_cases.jsonl
```

**命中案例：`PVC-COSMETIC-BAG-001`**

| 验证字段 | 值 | 匹配 |
|---|---|---|
| status | `validated` | ✅ |
| usage_scope | `exact_product_sku_only` | ✅ |
| 标题关键标识 | 透明手提化妆包 / HelloKitty | ✅ |
| selected_sku | 凯蒂猫大包 | ✅ |
| quantity | 1 | ✅ |

命中后直接使用案例的 `calibrated_estimate_normal` 和 `calibrated_estimate_conservative` 参数，不做模糊搜索。

---

## 四、案例参数提取

### 4.1 包装参数

| 参数 | 正常档 | 保守档 |
|---|---|---|
| 包装尺寸 (cm) | 22.0 × 18.0 × 1.4 | 23.0 × 19.0 × 1.6 |
| 包装后重量 (g) | 70.0 | 87.5 |
| 计费重 (g) | 70.0 | 87.5 |
| 包装方式 | 折叠压扁后袋装 | 较少压缩后袋装 |

### 4.2 结构字段

| 字段 | 值 | 来源 |
|---|---|---|
| runtime_overall_form | `soft_bulky` | 案例 |
| runtime_modifiers | `["hollow"]` | 案例 |
| structure_type | `soft_hollow` | 案例 |
| shape_retention_scope | `none` | 案例 |
| foldable_parts | `["包身", "提手"]` | 案例 |
| detachable_parts | `[]` | 案例 |
| material | 透明 PVC/TPU | 案例 |
| actual_pure_head_cost_rmb | 7.0 元 | 用户确认 |

### 4.3 AI JSON 其他字段映射

按 AGENTS.md 2026-08-04 补充规则：

| 字段 | 值 | 规则依据 |
|---|---|---|
| rigidity | `"soft"` | 透明 PVC 无硬壳 |
| foldability | `"none"` | MEMORY 规则：不要尝试 high/medium |
| compressibility | `"low"` | 避免与 foldability 联动 |
| has_rigid_parts | `false` | 无五金/硬壳 |
| requires_shape_retention | `false` | shape_retention_scope=none |
| folding_action | `"不折叠"` | 已反映折叠后尺寸，不再做折叠 |
| compression_action | `"不压缩"` | 同上 |
| packaging_type | `"opp_bag"` | 袋装 |
| weight_scope | `"packaged_weight"` | 包装后重量 |
| dimension_scope | `"shipping_package_size"` | 运输包装尺寸 |

---

## 五、校验失败与修正

### 5.1 初次构造（失败）

`rigid_body_size_cm` 初填 `[25.0, 15.0, 10.0]`（商品展开外廓），render 结果为：

```
status: "blocked"
review_reasons:
  - normal档包装尺寸小于硬质部件最小外廓
  - conservative档包装尺寸小于硬质部件最小外廓
```

所有方案显示 0×0×0 / 0g / 0.00 元。

### 5.2 根因分析

`rigid_body_size_cm` 字段定义：**运输时不可缩小的主体最小外廓**。

对于软质可完全压扁的 PVC 包：
- 正常档包装 22×18×1.4cm 已是折叠压扁后的最小状态
- 填 25×15×10（展开外廓）意味着"不可缩小到 1.4cm"，触发硬质外廓校验阻断

### 5.3 修正

将 `rigid_body_size_cm` 改为 `[22.0, 18.0, 1.4]`（= 正常档包装尺寸），因为软质空心包可以压扁至此尺寸，无需保型外壳。

修正后通过校验，status: `calculated`。

---

## 六、计费重计算

### 6.1 正常档

```
体积重 = 22.0 × 18.0 × 1.4 / 8000 = 0.0693 kg = 69.3g
实重   = 70.0g
计费重 = max(70.0, 69.3) = 70.0g  → 实重主导
```

### 6.2 保守档

```
体积重 = 23.0 × 19.0 × 1.6 / 8000 = 0.0874 kg = 87.4g
实重   = 87.5g
计费重 = max(87.5, 87.4) = 87.5g  → 实重主导（差值 0.1g）
```

### 6.3 货代对比

| 方案 | 单价 | 计费重 | 纯头程 | 固定费 | 总头程 |
|---|---|---|---|---|---|
| 义乌正常 | 100 元/kg | 70g | 7.00 | 6.00 | **13.00** ✅ |
| 义乌保守 | 100 元/kg | 88g | 8.75 | 6.00 | 14.75 |
| 深圳正常 | 80 元/kg | 70g | 5.60 | 10.00 | 15.60 |
| 深圳保守 | 80 元/kg | 88g | 7.00 | 10.00 | 17.00 |

**推荐：义乌正常，纯头程 ¥7.00，总头程 ¥13.00。**

---

## 七、与实际值对比验证

| 指标 | 估算值 | 实际值 | 偏差 |
|---|---|---|---|
| 纯头程 | ¥7.00（义乌正常） | 约 ¥7 | ≈ 0% |
| 货代 | 义乌（推荐） | 未知 | 待确认 |

**结论：正常档精确命中，纯头程偏差 < 3%。** 因包装尺寸和重量由 `PVC-COSMETIC-BAG-001` 已验证案例直接提供（非 AI 估算），置信度为 high。

---

## 八、教训记录

1. **精确校准查询命中时直接使用案例参数**，不自行估算包装尺寸/重量，不走 AI 推理路径。
2. **`rigid_body_size_cm` 必须 ≤ `packaged_size_cm`**：对于可完全压扁的软质空心商品，`rigid_body_size_cm` 应等同于或小于包装后的实际尺寸，不能填展开外廓。
3. **PVC 透明化妆包 ≤ 100g**：单件计费重 70-88g，义乌正常档纯头程 ¥7，与用户确认值一致。
4. **foldability=`none` + folding_action=`不折叠`** 组合在 MEMORY 规则中被封存，当前包装尺寸已是折叠后状态时正确使用此组合。
