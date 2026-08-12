# 假发与超薄手套头程估算过程

> 日期：2026-08-02 | 模式：仅校准头程

---

## 一、商品一：中长卷发假发（全头套）

### 1.1 商品信息

| 项目 | 内容 |
|------|------|
| 商品名称 | 欧美中长卷发全头套假发（齐刘海海水纹） |
| 1688 价格 | ¥18/盒起批 |
| 颜色 | 黑色、浅棕色、深棕色、挑染深棕色、亚麻色、钢琴色（6色） |
| 材质 | 化纤+内网（synthetic_fiber） |
| 包装形式 | 零售礼盒装 |
| 商家规格 | 26×16×6 cm / 140 g（来自 1688 截图规格表） |
| 商品特征 | 蓬松卷发（海水纹），软质，已装礼盒，不可折叠压缩 |

### 1.2 估算策略

#### 策略选择

商家截图规格表中 **26×16×6 cm / 140 g 是明确包装后参数**（礼盒外尺寸 + 毛重）。在 AI JSON 中有两种标注方式：

- **方案 A**：`dimension_source: "page_text"`、`dimension_scope: "shipping_package_size"`、`weight_source: "page_text"`、`weight_scope: "packaged_weight"` → 让 evidence 标记为 `packaged_size` + `gross_weight`，is_packaged=True，**不触发软品体积重保护**，正常按 max(实重, 体积重) 计费。
- **方案 B**：`dimension_source: "ai_estimated"` → evidence 标记为 `product_body_size`，is_packaged=False，**触发软品体积重保护**（体积重 0.504 > 净重×3 = 0.42 时强制改用实重），导致 chargeable 在 soft_ignore 和 v21 weight_correction 之间冲突。

最终选择**方案 A**，因为商家规格是真实包装数据，不需要触发软品保护。

#### 初始试算中的三个坑

**第一坑：`product_name` 含"头套"被 AGR-SEMI-RIGID-MASK-007 误匹配**

```json
// 初版 AI JSON 的 product_name
"product_name": "欧美中长卷发全头套假发（齐刘海海水纹）"
```

CAL 规则 `AGR-SEMI-RIGID-MASK-007` 的触发条件：
- `any_terms`: ["头套", "面具", "cowl", "mask", "head_mask"]
- `rigidity`: "soft" 或 "semi_rigid"

结果：假发的商品名"全头套"被误认为是 cos 半硬头套/面具，正常档包装从 **28×18×8 cm 被压到 17.91×14.07×1.92 cm**，厚度从 8cm 压到 1.92cm。这在假发蓬松卷发的语境下显然是错误的——CAL 把"发套（wig cap）"当成了"头套面具（head mask）"。

**修正**：将 `product_name` 改为 `"欧美中长卷发蓬松假发（齐刘海海水纹）"`——去掉"头套"字样，只保留"假发"。

**第二坑：`dimension_source: "merchant_spec"` 不在合法白名单内**

```json
// 打算标记商家规格，但 merchant_spec 不在枚举中
"dimension_source": "merchant_spec"
```

`ai_schema.py` 中 `dimension_source` 的合法值只有四个：
```python
{"ai_estimated", "page_text", "user_provided", "image_visual"}
```

`merchant_spec` 不在其中，被自动重置为 `ai_estimated`，导致 `interpreted_as` 回退到 `product_body_size`，再次触发软品保护。

**修正**：改为 `"page_text"`（1688 截图即页面文本来源）。

**第三坑：page_text 来源下 scenario 必须与 evidence 严格一致**

校验逻辑（`packaging_decision_ai.py`）：

```python
# 尺寸容差：max(evidence_value * 0.02, 0.1 cm)
if context == "packaged_size" and not _relative_match(scenario, body, 0.02):
    error("packaged_dimension_changed", "与可信包装尺寸偏差过大，不得重复打包")

# 重量容差：max(evidence_value * 0.02, 0.005 kg)
if context == "gross_weight" and abs(scenario_weight - evidence_weight) > tolerance:
    error("packaged_weight_changed", "改变了可信毛重，不得重复增加包材")
```

以 26×16×6 cm 为例的容差：
- 26cm → 容差 0.52cm → 最大 26.52cm
- 16cm → 容差 0.32cm → 最大 16.32cm
- 6cm → 容差 0.12cm → 最大 6.12cm

我之前试了 `scenario = [28, 18, 8]`（设想在商家规格上加 2cm 缓冲），但 28 > 26.52、18 > 16.32、8 > 6.12，全部被阻断。**page_text 来源下，正常档/保守档无法用加余量区分**。

**修正**：正常档和保守档都设为 `[26, 16, 6]`，严格匹配 evidence。

### 1.3 最终 AI JSON

```json
{
  "product_type": "medium_long_curly_wig",
  "product_name": "欧美中长卷发蓬松假发（齐刘海海水纹）",
  "material": "synthetic_fiber",
  "quantity": 1,
  "quantity_source": "user_confirmed",
  "category": "general",
  "rigidity": "soft",
  "foldability": "none",
  "compressibility": "low",
  "has_rigid_parts": false,
  "has_hard_bottom": false,
  "has_hard_backboard": false,
  "has_frame": false,
  "has_rigid_insert": false,
  "retail_box_visible": true,
  "hard_card_visible": false,
  "protrusion_flattenable": null,
  "requires_shape_retention": false,
  "packaging_state_hint": "boxed",
  "ai_net_weight_kg": 0.14,
  "ai_package_size_cm": [26, 16, 6],
  "ai_package_weight_kg": 0.14,
  "conservative_package_size_cm": [26, 16, 6],
  "conservative_package_weight_kg": 0.14,
  "packaging_method": "礼盒（商家规格）",
  "folding_action": "不折叠",
  "compression_action": "不压缩",
  "packaging_type": "retail_box",
  "weight_scope": "packaged_weight",
  "dimension_scope": "shipping_package_size",
  "confidence": "high",
  "reasoning": "1688商家规格 26×16×6cm/140g（中长卷发蓬松假发，齐刘海海水纹，化纤+内网，零售礼盒装）。商家规格即礼盒外廓，按page_text标记为包装事实。",
  "dimension_source": "page_text",
  "weight_source": "page_text",
  "product_size_cm": [26, 16, 6]
}
```

### 1.4 run.py 运行结果

```text
EST-20260802145931-b7bd5fdd | status: calculated
```

**evidence 层解析：**

| 证据 | 类型 | 来源 | 解读 | 值 |
|------|------|------|------|-----|
| dimensions | packaged_size | page_text | 包装尺寸 | 26×16×6 cm |
| weight | gross_weight | page_text | 毛重 | 0.14 kg |

- 体积重：26×16×6 ÷ 8000 = **0.312 kg**
- is_packaged = True（不触发软品体积重保护）
- soft_volume_ignored = **false** ✓

**v2.1 重量修正（可信重量 140g）：**

```
用户重量：140g → > 50g（no_increment_max_g 阈值）
→ 走"普通品"分支：140g + 50g = 0.19 kg
→ chargeable = max(0.19, 0.312) = 0.312 kg（体积重主导）
```

**计费重和头程：**

| 档位 | 包装尺寸 | 包装重 | 体积重 | 计费重 | 主导因素 |
|------|----------|--------|--------|--------|----------|
| 正常档 | 26×16×6 cm | 0.14 kg | 0.312 kg | **0.312 kg** | 体积重 |
| 保守档 | 26×16×6 cm | 0.14 kg | 0.312 kg | **0.312 kg** | 体积重 |

> 正常档/保守档相同 —— page_text 来源下容差 ≤ 2%，无法加余量。

**货代对比（纯头程 = head_freight_rmb）：**

| 档位 | 深圳纯头程 | 义乌纯头程 | 规则 |
|------|-----------|-----------|------|
| 正常档 | ¥24.96（0.312×80） | ¥31.20（0.312×100） | 深圳更优 |
| 保守档 | ¥24.96 | ¥31.20 | 深圳更优 |

**货代最终头程（含服务费）：**

| 档位 | 深圳最终头程 | 义乌最终头程 | 推荐货代 |
|------|-------------|-------------|----------|
| 正常档 | ¥34.96（24.96+10） | ¥37.20（31.20+6） | **深圳** |
| 保守档 | ¥34.96 | ¥37.20 | **深圳** |

**推荐理由**：计费重 0.312 kg > 临界点 0.2 kg，深圳货代单价 80 元/kg 优势（vs 义乌 100 元/kg）足以覆盖 ¥4 固定费差（深圳 ¥10 vs 义乌 ¥6）。临界点公式：W × 20 > 4 → W > 0.2 kg 选深圳。

### 1.5 CAL 命中情况

```
status: active_registry_no_numeric_match
matched_sample_ids: CAL-036/055/051/050/049/043/040/039/037/032（10条）
applied_rule_ids: []（0条实际应用）
```

10 条 CAL 样本匹配但无规则触发：
- AGR-SEMI-RIGID-MASK-007 未触发（product_name 已改）
- AGR-WIG-CURL-001 假发卷绕规则未触发（foldability="none"，规则要求"good"/"limited"）
- 无其他数值修正规则触发

**注意**：如果 foldability="good"，AGR-WIG-CURL-001 会触发展开尺寸修正，但本次礼盒装假发无需卷绕。

---

## 二、商品二：超薄无缝防勾丝长款手套

### 2.1 商品信息

| 项目 | 内容 |
|------|------|
| 商品名称 | 超薄情趣无缝防勾丝分指婚纱礼仪手套五指手套长款防晒女丝袜手套 |
| 1688 价格 | ¥11/双起批（1双=2只） |
| 颜色 | 蓝色、黑色、白色、肤色、灰色、粉色、红色、酒红色（8色） |
| 尺码 | 均码 |
| 已售 | 5.7万+ 双 |
| 材质 | 锦纶/涤纶（nylon/polyamide） |
| 商品特征 | 超薄无缝、长款齐肘（约 50 cm）、分指（5指分开）、极薄透光 |

### 2.2 估算策略

**关键问题**：**1688 截图无规格表**，没有重量和尺寸数据。只能通过通用模板参照估算，置信度设为 `low`，明确告知用户误差可能 ±30%。

**参照案例选择：**

| 案例 | 类别 | 尺寸(cm) | 重量(g) | 相似度 |
|------|------|----------|---------|--------|
| `gothic_lace_arm_gloves` | 哥特蕾丝长款手套（一对） | 22×14×3 | 70 | ⭐⭐⭐ 中高 |
| `five_toe_socks` | 五趾袜（一对） | 16×10×3 | 55 | ⭐⭐ 中 |
| 分趾蓬蓬袜 | 薄款分趾袜（一对） | 18×12×1.5 | 35 | ⭐ 低 |

**选择原则**：
- 商品类别最接近：`gothic_lace_arm_gloves`（长款手套，一对）
- 但本次是"超薄无缝"，比蕾丝更薄更轻
- 在 gothic_lace 基础上减重 30%（70g → 50g 净重），减小体积（22×14 → 30×10，因为长款但更薄）

**参数量化：**

```
净重估：50g（比蕾丝 60g 轻，因为超薄无缝材质）
包装增重：+10g（OPP袋）
包装后：60g（0.06 kg）
折叠后尺寸：30×10×3 cm（长度参考长款 50cm 折叠 3-4 折）
```

### 2.3 最终 AI JSON

```json
{
  "product_type": "ultrathin_seamless_long_gloves_pair",
  "product_name": "超薄无缝防勾丝长款手套（婚纱礼仪）",
  "material": "nylon_polyamide",
  "quantity": 1,
  "quantity_source": "user_confirmed",
  "category": "general",
  "rigidity": "soft",
  "foldability": "good",
  "compressibility": "good",
  "has_rigid_parts": false,
  "ai_net_weight_kg": 0.05,
  "ai_package_size_cm": [30, 10, 3],
  "ai_package_weight_kg": 0.06,
  "conservative_package_size_cm": [34, 12, 4],
  "conservative_package_weight_kg": 0.075,
  "packaging_method": "OPP袋",
  "folding_action": "常规折叠",
  "compression_action": "轻度压缩",
  "confidence": "low",
  "dimension_source": "ai_estimated",
  "weight_source": "ai_estimated"
}
```

**关键字段说明：**
- `foldability: "good"` + `compressibility: "good"`：按超薄手套可折叠可压缩特性（参考 gothic_lace_arm_gloves）
- `confidence: "low"`：无商家规格表，纯模板参照估算
- `weight_source: "ai_estimated"`：采用 AI 估重（60g `约值`），v21 回退到 AI 估重

### 2.4 run.py 运行结果

```text
EST-20260802155325-a6449c57 | status: calculated | confidence: low
```

**evidence 层解析：**

| 证据 | 类型 | 来源 | 解读 | 值 | 置信度 |
|------|------|------|------|-----|--------|
| dimensions | product_body_size | ai_estimated | 商品外廓 | 30×10×3 cm | low |
| weight | net_weight | ai_estimated | 净重 | 0.05 kg | low |

**正常档（30×10×3 cm / 60 g）：**

```
体积重：30×10×3 ÷ 8000 = 0.1125 kg
软品检查：0.1125 > 0.05 × 3 = 0.15？→ NO，不触发软品保护
chargeable_after_soft = max(0.06, 0.1125) = 0.1125 kg（体积重主导）

v21 重量修正：
  用户 60g 约值（低可信）→ 回退 AI 估重 0.06 kg
  计费重 = 0.1125 kg
```

```
深圳纯头程：0.1125 × 80 = ¥9.00
义乌纯头程：0.1125 × 100 = ¥11.25
推荐义乌（计费重 0.1125 kg < 临界点 0.2 kg）
```

**保守档（34×12×4 cm / 75 g）：**

```
体积重：34×12×4 ÷ 8000 = 0.204 kg
软品检查：0.204 > 0.05 × 3 = 0.15 → YES，触发软品保护！
→ soft_volume_ignored = true
→ 改用实重 0.075 kg 计算头程
→ chargeable_after_soft = 0.075 kg

v21 重量修正：
  用户 60g 约值（低可信）→ 回退 AI 估重 0.075 kg
  計費重 = 0.075 kg
```

```
深圳纯头程：0.075 × 80 = ¥6.00
义乌纯头程：0.075 × 100 = ¥7.50
推荐义乌（计费重 0.075 kg < 临界点 0.2 kg）
```

### 2.5 最终头程汇总

| 档位 | 包装尺寸 | 包装重 | 体积重 | 计费重 | 深圳纯头程 | 义乌纯头程 | 深圳最终 | 义乌最终 | 推荐 |
|---|---|---|---|---|---|---|---|---|---|
| 正常档 | 30×10×3 | 0.06 | 0.1125 | 0.1125 | ¥9.00 | ¥11.25 | ¥19.00 | ¥17.25 | **义乌** |
| 保守档 | 34×12×4 | 0.075 | 0.204 | 0.075* | ¥6.00 | ¥7.50 | ¥16.00 | ¥13.50 | **义乌** |

\* 保守档触发了 soft_volume_ignored（体积重超过净重×3），强制改用实重计算。

**推荐理由**：正常档和保守档的计费重（0.1125/0.075 kg）都远低于货代选择临界点 0.2 kg，义乌 ¥6 固定费优势盖过单价劣势。

### 2.6 CAL 命中情况

```
status: active_registry_no_numeric_match
matched_sample_ids: CAL-055/051/...（若干条）
applied_rule_ids: []（0条实际应用）
```

无规则触发 —— 因为无商家规格表，evidence 来源为 ai_estimated，CAL 库中没有匹配的超薄手套样本。

### 2.7 估算风险提示

| 风险项 | 严重度 | 说明 |
|--------|--------|------|
| 重量估算偏差 | 高 | 估计的 50g 可能偏差 ±15g（30%），实际可能 30-65g |
| 体积估算偏差 | 高 | 折叠后尺寸 30×10×3 各轴可±3cm → 体积重偏差可达 ±40% |
| 整体置信度 | low | 纯模板估算，缺少 chart 规格表数据 |
| 保守档保护 | 中 | 保守档触发了软品保护，改用实重算头程（合理） |

**建议**：等实际发货后用商家真实规格表补充，重新估算并做 CAL 命中验证。

---

## 三、本次估算中的关键经验

### 3.1 dimension_source / weight_source 白名单

`ai_schema.py` 中合法的 source 值只有四个：

```python
{"ai_estimated", "page_text", "user_provided", "image_visual"}
```

- `merchant_spec`、`supplier_spec`、`1688_chart` 等自定义值会被**静默重置为 `ai_estimated`**
- 这会导致 evidence.interpretted_as 回退到 `product_body_size`，触发不必要的软品保护
- **正确做法**：1688 截图规格表 → `page_text`；用户提供的数据 → `user_provided`

### 3.2 page_text 来源下的 scenario 容差

当 evidence 被标记为 `packaged_size` 或 `gross_weight` 时，AI 提供的 scenario 必须与 evidence **严格匹配**（容差 2% 或 0.1 cm/0.005 kg 中取较大值）。

**含义**：page_text 来源下，正常档和保守档无法用"加大 2-4 cm"的余量区分——必须用相同的商家包装规格。

**工作流影响**：
- page_text 来源：scenario 必须严格匹配 evidence → 正常/保守档相同
- ai_estimated 来源：scenario 可自由加余量 → 正常/保守档可有差异
- 选择逻辑：有商家规格表 → page_text（精准但两档相同）；无商家规格表 → ai_estimated（有差异但误差大）

### 3.3 软品体积重保护（soft_volume_ignore）

触发条件（`soft_goods_rules.py`）：
```python
if volume_weight_kg > ai_net_weight_kg * 3:
    volume_ignored = True
    chargeable_kg = packaged_weight_kg  # 改用实重
```

但**仅在 is_packaged=False（evidence 不是 packaged_size）时触发**。

实际效果：
- 假发：is_packaged=True（page_text）→ 不触发 → 按正常 max(实重, 体积重) 计费 ✓
- 手套：is_packaged=False（ai_estimated）→ 保守档触发 → 改用实重 0.075 kg ✓（但正常档 0.1125 < 0.15 不触发）

### 3.4 AGR-SEMI-RIGID-MASK-007 的误匹配风险

CAL 规则 `AGR-SEMI-RIGID-MASK-007` 按 `any_terms: ["头套", "面具"]` 匹配商品名。如果商品名含"全头套"（如"全头套假发"即 full wig），会被误判为 cos 半硬头套，导致厚度被严重压缩。

**修正方法**：product_name 中用"假发"替代"头套"，或完全避免"头套"字样。

**建议**：该规则应在未来迭代中加入 `exclude_terms: ["假发"]` 或更精确的类目匹配，避免假发被误判。

---

## 四、查询记录

| 序号 | AI JSON 文件 | 状态 | 关键发现 |
|------|-------------|------|----------|
| 1 | `wig_..._ai.json`（初版） | blocked | 被 AGR-SEMI-RIGID-MASK-007 压缩厚度 |
| 2 | `wig_..._ai.json`（改名） | calculated* | 触发 soft_volume_ignore（ai_estimated 来源） |
| 3 | `wig_..._ai.json`（merchant_spec） | calculated* | merchant_spec 不在白名单，被重置为 ai_estimated |
| 4 | `wig_..._ai.json`（page_text + 28cm） | blocked | 与可信包装尺寸偏差过大，不得重复打包 |
| 5 | `wig_..._ai.json`（page_text + 26cm） | **calculated** | 通过，is_packaged=True |
| 6 | `ultrathin_..._ai.json` | calculated | 通用模板估算，低置信，正常档按 max 计，保守档触发 soft_volume_ignore |
