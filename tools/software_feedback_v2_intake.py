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
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "Calibration Feedback Export V2"
INDEX_PATH = Path(__file__).resolve().parent.parent / "data" / "software_import_index.json"
RECORDS_PATH = Path(__file__).resolve().parent.parent / "data" / "calibration_records.jsonl"


class IntakeError(Exception):
    """Intake 失败"""


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


def extract_baseline(ai_initial: dict[str, Any]) -> dict[str, Any]:
    """从 ai_initial 提取 baseline（machine_facts.ai_initial.packaging_proposal.normal）"""
    packaging_proposal = ai_initial.get("packaging_proposal") or {}
    normal = packaging_proposal.get("normal") or {}

    if not normal:
        raise IntakeError("ai_initial.packaging_proposal.normal 不存在或为空")

    # 提取关键字段
    baseline = {
        "length_cm": normal.get("length_cm"),
        "width_cm": normal.get("width_cm"),
        "height_cm": normal.get("height_cm"),
        "weight_g": normal.get("weight_g"),
        "packaging_state": normal.get("packaging_state"),
        "packaging_method": normal.get("packaging_method"),
        "confidence": normal.get("confidence"),
    }

    # 提取 observation 关键字段
    observation = ai_initial.get("observation") or {}
    baseline["product_name"] = observation.get("product_name")

    return baseline


def extract_user_feedback(machine_facts: dict[str, Any]) -> dict[str, Any]:
    """提取用户反馈（suggested_package / actual_logistics）"""
    user_feedback = machine_facts.get("user_feedback") or {}

    # suggested_package（用户建议/校准值）
    suggested = user_feedback.get("suggested_package") or {}
    suggested_package = {
        "length_cm": suggested.get("length_cm"),
        "width_cm": suggested.get("width_cm"),
        "height_cm": suggested.get("height_cm"),
        "weight_g": suggested.get("weight_g"),
        "note": suggested.get("note"),
    } if suggested else None

    # actual_logistics（真实实测包装 truth）
    actual = user_feedback.get("actual_logistics") or {}
    actual_logistics = {
        "actual_package_length_cm": actual.get("actual_package_length_cm"),
        "actual_package_width_cm": actual.get("actual_package_width_cm"),
        "actual_package_height_cm": actual.get("actual_package_height_cm"),
        "actual_package_weight_g": actual.get("actual_package_weight_g"),
        "actual_freight": actual.get("actual_freight"),
    } if actual else None

    return {
        "suggested_package": suggested_package,
        "actual_logistics": actual_logistics,
    }


def extract_process_evidence(machine_facts: dict[str, Any]) -> dict[str, Any]:
    """提取过程证据（local_adopted / reestimate_history）"""
    local_adopted = machine_facts.get("local_adopted")
    reestimate_history = machine_facts.get("reestimate_history") or []

    return {
        "local_adopted": local_adopted,
        "reestimate_history_count": len(reestimate_history),
    }


def build_governance_summary(
    record: dict[str, Any],
    manifest_path: Path,
    export_batch_id: str,
) -> dict[str, Any]:
    """构建治理摘要（写入 calibration_records.jsonl 的格式）"""
    machine_facts = record.get("machine_facts") or {}
    ai_initial = machine_facts.get("ai_initial") or {}

    # baseline 必须来自 ai_initial
    baseline = extract_baseline(ai_initial)

    # 用户反馈
    feedback = extract_user_feedback(machine_facts)

    # 过程证据
    process = extract_process_evidence(machine_facts)

    # 图片路径
    image_paths = record.get("image_relative_paths") or []

    # 构建治理摘要
    summary = {
        "record_id": record.get("record_id"),
        "sequence": record.get("sequence"),
        "product_short_name": record.get("product_short_name"),
        "product": {
            "name": baseline.get("product_name") or record.get("product_short_name") or "UNKNOWN",
            "sku": "UNKNOWN",
        },
        "source": "software_export_v2",
        "baseline": {
            "weight_g": baseline.get("weight_g"),
            "package_size_cm": [
                baseline.get("length_cm"),
                baseline.get("width_cm"),
                baseline.get("height_cm"),
            ],
            "packaging_state": baseline.get("packaging_state"),
            "packaging_method": baseline.get("packaging_method"),
            "confidence": baseline.get("confidence"),
        },
        "user_calibration": {
            "suggested_package": feedback.get("suggested_package"),
            "actual_logistics": feedback.get("actual_logistics"),
            "note": None,  # 可从 user_feedback.note 提取
        },
        "analysis": {
            "physical_mechanism": "UNKNOWN",
            "error_direction": "UNKNOWN",
            "error_type": "UNKNOWN",
        },
        "evidence": {
            "images": image_paths,
            "process_evidence": process,
        },
        "provenance": {
            "source_manifest": str(manifest_path),
            "export_batch_id": export_batch_id,
            "software_record_id": record.get("record_id"),
            "imported_at": datetime.now(timezone.utc).isoformat(),
        },
        "governance": {
            "status": "RECORDED",
        },
    }

    return summary


def import_manifest(source: str | Path, dry_run: bool = False) -> dict[str, Any]:
    """导入 manifest

    Returns:
        导入结果统计
    """
    manifest = load_manifest(source)
    manifest_path = Path(source) if Path(source).is_dir() else Path(source).parent
    export_batch_id = manifest.get("export_batch_id", "UNKNOWN")
    records = manifest.get("records") or []

    # 加载去重索引
    index = load_index()

    imported = 0
    skipped = 0
    errors = []

    for record in records:
        software_record_id = record.get("record_id")
        if not software_record_id:
            errors.append(f"record 缺少 record_id")
            continue

        # 检查去重
        if software_record_id in index["records"]:
            skipped += 1
            continue

        try:
            # 构建治理摘要
            summary = build_governance_summary(record, manifest_path, export_batch_id)

            if not dry_run:
                # 追加到 calibration_records.jsonl
                with open(RECORDS_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(summary, ensure_ascii=False) + "\n")

                # 更新去重索引
                index["records"][software_record_id] = {
                    "software_record_id": software_record_id,
                    "export_batch_id": export_batch_id,
                    "local_calibration_record_id": summary["record_id"],
                    "source_manifest": str(manifest_path),
                    "imported_at": summary["provenance"]["imported_at"],
                }

            imported += 1

        except IntakeError as e:
            errors.append(f"{software_record_id}: {e}")

    # 保存去重索引
    if not dry_run and (imported > 0 or skipped > 0):
        save_index(index)

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "dry_run": dry_run,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Software Feedback V2 Intake")
    parser.add_argument("--source", required=True, help="导出目录或 manifest.json 路径")
    parser.add_argument("--dry-run", action="store_true", help="只验证，不实际写入")
    args = parser.parse_args()

    try:
        result = import_manifest(args.source, dry_run=args.dry_run)
        print(f"导入完成: {result['imported']} 条, 跳过 {result['skipped']} 条")
        if result["errors"]:
            print(f"错误: {len(result['errors'])} 条")
            for err in result["errors"]:
                print(f"  - {err}")
        if result["dry_run"]:
            print("(dry-run 模式，未实际写入)")
        return 0 if not result["errors"] else 1

    except IntakeError as e:
        print(f"导入失败: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
