# -*- coding: utf-8 -*-
"""Software Feedback V2 Intake

读取主软件导出的 Calibration Feedback Export V2 目录或 manifest.json，
转成现有 calibration_records.jsonl 所需的治理摘要。

- 验证 contract_version == "Calibration Feedback Export V2"
- baseline 必须来自 machine_facts.ai_initial.packaging_proposal.normal
- 不调用 AI、不修改原始 manifest、不复制完整 machine_facts 到 JSONL
- 防止重复导入（通过 data/software_import_index.json）
- suggested_package 与 actual_logistics 必须严格区分
- 实际费用不能被反推成唯一包装尺寸
- 每条写入前严格校验 schemas/calibration_record_v1.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "Calibration Feedback Export V2"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = PROJECT_ROOT / "data" / "software_import_index.json"
RECORDS_PATH = PROJECT_ROOT / "data" / "calibration_records.jsonl"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "calibration_record_v1.json"

class IntakeError(Exception):
    """Intake 失败"""


# ── Schema 驱动校验（schema 文件为唯一真实来源） ──

_schema_cache: dict[str, Any] | None = None


def load_schema(*, reload: bool = False) -> dict[str, Any]:
    """加载并缓存 schemas/calibration_record_v1.json。

    reload=True 强制重新读取文件（测试用）。
    """
    global _schema_cache
    if _schema_cache is None or reload:
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Schema 文件不存在: {SCHEMA_PATH}")
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            _schema_cache = json.load(f)
    return _schema_cache


def _extract_constraints(schema: dict[str, Any]) -> dict[str, Any]:
    """从 schema JSON 提取校验所需的约束（不硬编码任何值）。"""
    props = schema.get("properties", {})

    # record_id pattern
    rid_pattern = props.get("record_id", {}).get("pattern", r"^CAL-\d{4,}$")

    # enum 提取
    def _enum(path_parts: list[str]) -> set[str]:
        node = props
        for part in path_parts:
            node = node.get(part, {}).get("properties", node) if part != path_parts[-1] else node.get(part, {})
        # 最后一级取 enum
        if isinstance(node, dict) and "enum" in node:
            return set(node["enum"])
        return set()

    evidence_levels = set(props.get("evidence", {}).get("properties", {}).get("evidence_level", {}).get("enum", []))
    fb_props = props.get("feedback", {}).get("properties", {})
    error_dirs = set(fb_props.get("error_direction", {}).get("enum", []))
    error_types = set(fb_props.get("error_type", {}).get("enum", []))
    an_props = props.get("analysis", {}).get("properties", {})
    statuses = set(an_props.get("status", {}).get("enum", []))
    mechanisms = set(an_props.get("physical_mechanism", {}).get("enum", []))
    pr_props = props.get("provenance", {}).get("properties", {})
    source_types = set(pr_props.get("source_type", {}).get("enum", []))

    return {
        "required": set(schema.get("required", [])),
        "allowed_top": set(props.keys()),  # additionalProperties: false
        "additional_properties": schema.get("additionalProperties", True),
        "record_id_pattern": re.compile(rid_pattern),
        "evidence_levels": evidence_levels,
        "error_directions": error_dirs,
        "error_types": error_types,
        "statuses": statuses,
        "mechanisms": mechanisms,
        "source_types": source_types,
    }


def validate_record_v1(record: dict[str, Any], *, _schema: dict[str, Any] | None = None) -> list[str]:
    """校验单条 record 是否严格符合 calibration_record_v1.json。

    返回 error 列表；空列表 = 通过。
    约束全部从 schema 文件读取，不硬编码。
    可传入 _schema 覆盖（测试用）。
    """
    errors: list[str] = []

    if not isinstance(record, dict):
        return ["record 不是 object"]

    # 从 schema 提取约束
    schema = _schema if _schema is not None else load_schema()
    c = _extract_constraints(schema)

    # additionalProperties: false
    if c["additional_properties"] is False:
        extra = set(record.keys()) - c["allowed_top"]
        if extra:
            errors.append(f"禁止的顶层字段: {sorted(extra)}")

    # required
    missing = c["required"] - set(record.keys())
    if missing:
        errors.append(f"缺少必填字段: {sorted(missing)}")
        return errors  # 缺必填字段时后续检查无意义

    # record_id pattern
    rid = record.get("record_id")
    if not isinstance(rid, str) or not c["record_id_pattern"].match(rid):
        errors.append(f"record_id 不符合 schema pattern: {rid!r}")

    # product
    prod = record.get("product")
    if not isinstance(prod, dict):
        errors.append("product 必须是 object")

    # baseline 结构
    bl = record.get("baseline")
    if not isinstance(bl, dict):
        errors.append("baseline 必须是 object")
    else:
        dims = bl.get("dimensions")
        if dims is not None and not isinstance(dims, dict):
            errors.append("baseline.dimensions 必须是 object 或 null")

    # actual 结构
    act = record.get("actual")
    if not isinstance(act, dict):
        errors.append("actual 必须是 object")
    else:
        dims = act.get("dimensions")
        if dims is not None and not isinstance(dims, dict):
            errors.append("actual.dimensions 必须是 object 或 null")

    # feedback enum
    fb = record.get("feedback")
    if isinstance(fb, dict):
        if c["error_directions"] and fb.get("error_direction") not in c["error_directions"]:
            errors.append(f"feedback.error_direction 非法: {fb.get('error_direction')!r}")
        if c["error_types"] and fb.get("error_type") not in c["error_types"]:
            errors.append(f"feedback.error_type 非法: {fb.get('error_type')!r}")

    # analysis enum
    an = record.get("analysis")
    if isinstance(an, dict):
        if c["statuses"] and an.get("status") not in c["statuses"]:
            errors.append(f"analysis.status 非法: {an.get('status')!r}")
        if c["mechanisms"] and an.get("physical_mechanism") not in c["mechanisms"]:
            errors.append(f"analysis.physical_mechanism 非法: {an.get('physical_mechanism')!r}")

    # evidence enum
    ev = record.get("evidence")
    if isinstance(ev, dict):
        if c["evidence_levels"] and ev.get("evidence_level") is not None and ev.get("evidence_level") not in c["evidence_levels"]:
            errors.append(f"evidence.evidence_level 非法: {ev.get('evidence_level')!r}")

    # provenance enum
    pr = record.get("provenance")
    if isinstance(pr, dict):
        if c["source_types"] and pr.get("source_type") is not None and pr.get("source_type") not in c["source_types"]:
            errors.append(f"provenance.source_type 非法: {pr.get('source_type')!r}")

    return errors


# ── 去重索引 ──

def load_index() -> dict[str, Any]:
    """加载去重索引"""
    if not INDEX_PATH.exists():
        return {"records": {}}
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_index(index: dict[str, Any]) -> None:
    """保存去重索引"""
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")


def dedup_key(software_record_id: str, export_batch_id: str) -> str:
    """去重键：同一 software record + 同一 batch = 重复；
    同一 software record + 不同 batch = 允许。"""
    return f"{software_record_id}@{export_batch_id}"


# ── CAL-XXXX ID 生成 ──

def next_cal_id() -> str:
    """生成下一个 CAL-XXXX ID（基于现有 JSONL 中最大编号 +1）。"""
    max_num = 0
    if RECORDS_PATH.exists():
        with open(RECORDS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    rid = rec.get("record_id", "")
                    if rid.startswith("CAL-"):
                        num = int(rid.split("-", 1)[1])
                        if num > max_num:
                            max_num = num
                except (json.JSONDecodeError, ValueError):
                    pass
    return f"CAL-{max_num + 1:04d}"


# ── 字段映射 ──

def extract_baseline(ai_initial: dict[str, Any]) -> dict[str, Any]:
    """从 ai_initial 提取 baseline → schema 格式。

    machine_facts.ai_initial.packaging_proposal.normal
    → baseline.dimensions.{length,width,height}
    → baseline.weight
    → baseline.freight = null（V2 observation 无独立运费事实）
    → baseline.forwarder = null
    """
    packaging_proposal = ai_initial.get("packaging_proposal") or {}
    normal = packaging_proposal.get("normal") or {}

    if not normal:
        raise IntakeError("ai_initial.packaging_proposal.normal 不存在或为空")

    def _num(v: Any) -> float | int | None:
        if isinstance(v, (int, float)):
            return v
        return None

    return {
        "dimensions": {
            "length": _num(normal.get("length_cm")),
            "width": _num(normal.get("width_cm")),
            "height": _num(normal.get("height_cm")),
        },
        "weight": _num(normal.get("weight_g")),
        "freight": None,
        "forwarder": None,
    }


def extract_actual(machine_facts: dict[str, Any]) -> dict[str, Any]:
    """提取 actual（仅真实实测包装 truth）。

    只从 machine_facts.user_feedback.actual_logistics.actual_package_* 映射。
    suggested_package 绝不进入 actual。
    """
    user_feedback = machine_facts.get("user_feedback") or {}
    actual = user_feedback.get("actual_logistics") or {}

    def _num(v: Any) -> float | int | None:
        if isinstance(v, (int, float)):
            return v
        return None

    has_any = any(
        actual.get(k) is not None
        for k in ("actual_package_length_cm", "actual_package_width_cm",
                   "actual_package_height_cm", "actual_package_weight_g",
                   "actual_freight", "actual_forwarder")
    )

    if not has_any:
        return {
            "dimensions": None,
            "weight": None,
            "freight": None,
            "forwarder": None,
        }

    has_dims = any(
        actual.get(k) is not None
        for k in ("actual_package_length_cm", "actual_package_width_cm", "actual_package_height_cm")
    )

    return {
        "dimensions": {
            "length": _num(actual.get("actual_package_length_cm")),
            "width": _num(actual.get("actual_package_width_cm")),
            "height": _num(actual.get("actual_package_height_cm")),
        } if has_dims else None,
        "weight": _num(actual.get("actual_package_weight_g")),
        "freight": _num(actual.get("actual_freight")),
        "forwarder": actual.get("actual_forwarder"),
    }


def extract_feedback(machine_facts: dict[str, Any]) -> dict[str, Any]:
    """提取 feedback → schema 格式。

    user_note: 来自 user_feedback.note 或 suggested_package.note
    error_direction / error_type: 初始 UNKNOWN
    """
    user_feedback = machine_facts.get("user_feedback") or {}
    note = user_feedback.get("note") or ""

    # 如果 user_feedback.note 为空，尝试 suggested_package.note
    if not note:
        suggested = user_feedback.get("suggested_package") or {}
        note = suggested.get("note") or ""

    return {
        "user_note": str(note) if note else "",
        "error_direction": "UNKNOWN",
        "error_type": "UNKNOWN",
    }


def build_calibration_record(
    record: dict[str, Any],
    export_batch_id: str,
    cal_id: str,
) -> dict[str, Any]:
    """构建一条严格符合 calibration_record_v1.json 的记录。

    不产生任何 schema 禁止的顶层字段。
    """
    machine_facts = record.get("machine_facts") or {}
    ai_initial = machine_facts.get("ai_initial") or {}

    # baseline 必须来自 ai_initial
    baseline = extract_baseline(ai_initial)

    # actual 只来自真实实测
    actual = extract_actual(machine_facts)

    # feedback
    feedback = extract_feedback(machine_facts)

    # 图片路径
    image_paths = record.get("image_relative_paths") or []

    # product
    observation = ai_initial.get("observation") or {}
    product_name = observation.get("product_name") or record.get("product_short_name") or "UNKNOWN"

    # evidence.source 简洁标记来源
    source_text = f"software_export_v2 (batch={export_batch_id})"

    return {
        "record_id": cal_id,
        "product": {
            "name": product_name,
            "sku": "UNKNOWN",
            "quantity": None,
        },
        "evidence": {
            "images": list(image_paths),
            "source": source_text,
            "evidence_level": "UNKNOWN",
        },
        "baseline": baseline,
        "actual": actual,
        "feedback": feedback,
        "analysis": {
            "status": "RECORDED",
            "possible_pattern": "",
            "physical_mechanism": "UNKNOWN",
        },
        "provenance": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_type": "BATCH_JSON",
        },
    }


# ── Manifest 加载 ──

def load_manifest(source: str | Path) -> dict[str, Any]:
    """加载 manifest.json"""
    source = Path(source)
    if source.is_dir():
        manifest_path = source / "manifest.json"
    elif source.name == "manifest.json":
        manifest_path = source
    else:
        raise IntakeError(f"source 必须是目录或 manifest.json 文件: {source}")

    if not manifest_path.exists():
        raise IntakeError(f"manifest.json 不存在: {manifest_path}")

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    if not isinstance(manifest, dict):
        raise IntakeError("manifest.json 必须是 JSON 对象")

    contract = manifest.get("contract_version")
    if contract != CONTRACT_VERSION:
        raise IntakeError(
            f"contract_version 必须是 {CONTRACT_VERSION!r}，得到 {contract!r}"
        )

    return manifest


# ── 主导入逻辑 ──

def import_manifest(source: str | Path, dry_run: bool = False) -> dict[str, Any]:
    """导入 manifest

    Returns:
        导入结果统计
    """
    manifest = load_manifest(source)
    manifest_path = str(Path(source) if Path(source).is_dir() else Path(source).parent)
    export_batch_id = manifest.get("export_batch_id", "UNKNOWN")
    records = manifest.get("records") or []

    # 加载去重索引
    index = load_index()

    imported = 0
    skipped = 0
    schema_errors = []
    other_errors = []

    for record in records:
        software_record_id = record.get("record_id")
        if not software_record_id:
            other_errors.append("record 缺少 record_id")
            continue

        # 去重：同 software_record + 同 batch 跳过
        dk = dedup_key(software_record_id, export_batch_id)
        if dk in index["records"]:
            skipped += 1
            continue

        try:
            # 生成 CAL-XXXX ID
            cal_id = next_cal_id() if not dry_run else f"CAL-9999"

            # 构建符合 schema 的记录
            cal_record = build_calibration_record(record, export_batch_id, cal_id)

            # Schema 校验
            errs = validate_record_v1(cal_record)
            if errs:
                schema_errors.append(f"{software_record_id}: {errs}")
                continue  # 不写入 JSONL / index

            if not dry_run:
                # 追加到 calibration_records.jsonl
                with open(RECORDS_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(cal_record, ensure_ascii=False) + "\n")

                # 更新去重索引
                index["records"][dk] = {
                    "software_record_id": software_record_id,
                    "export_batch_id": export_batch_id,
                    "local_calibration_record_id": cal_id,
                    "source_manifest": manifest_path,
                    "imported_at": cal_record["provenance"]["created_at"],
                }

                # 递增 ID 计数器（内存中）
                # next_cal_id 每次从文件读，已在写入后自动 +1

            imported += 1

        except IntakeError as e:
            other_errors.append(f"{software_record_id}: {e}")

    # 保存去重索引
    if not dry_run and (imported > 0 or skipped > 0):
        save_index(index)

    return {
        "imported": imported,
        "skipped": skipped,
        "schema_errors": schema_errors,
        "errors": other_errors,
        "dry_run": dry_run,
    }


# ── CLI ──

def main() -> int:
    parser = argparse.ArgumentParser(description="Software Feedback V2 Intake")
    parser.add_argument("--source", required=True, help="导出目录或 manifest.json 路径")
    parser.add_argument("--dry-run", action="store_true", help="只验证，不实际写入")
    args = parser.parse_args()

    try:
        result = import_manifest(args.source, dry_run=args.dry_run)
        print(f"导入完成: {result['imported']} 条, 跳过 {result['skipped']} 条")
        if result["schema_errors"]:
            print(f"Schema 错误: {len(result['schema_errors'])} 条")
            for err in result["schema_errors"]:
                print(f"  - {err}")
        if result["errors"]:
            print(f"其他错误: {len(result['errors'])} 条")
            for err in result["errors"]:
                print(f"  - {err}")
        if result["dry_run"]:
            print("(dry-run 模式，未实际写入)")
        has_errors = bool(result["schema_errors"] or result["errors"])
        return 0 if not has_errors else 1

    except IntakeError as e:
        print(f"导入失败: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
