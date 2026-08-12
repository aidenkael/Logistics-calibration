#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Direct Calibration: reuse Profit-Accounting's current first-AI vision boundary.

This module intentionally imports the production RecognitionService at runtime.
It does not copy the Prompt, construct AppContext, open the production database,
run local re-estimate, or invoke PackagingEstimationService.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import calibration_intake as intake


WORKBENCH = Path(__file__).resolve().parent.parent
LOCAL_PATHS = WORKBENCH / "config" / "local_paths.json"


@dataclass(frozen=True)
class FirstAIBaseline:
    product_name: str
    dimensions: dict[str, float] | None
    weight_g: float | None
    prompt_version: str
    model: str


def profit_accounting_root() -> Path:
    try:
        configured = json.loads(LOCAL_PATHS.read_text(encoding="utf-8"))
        root = Path(str(configured["profit_accounting_root"])).expanduser()
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("无法读取 config/local_paths.json 的 profit_accounting_root") from exc
    if not (root / "src" / "profit_accounting_26" / "application" / "recognition_service.py").is_file():
        raise ValueError("profit_accounting_root 未指向包含 RecognitionService 的当前 Profit-Accounting 源码")
    return root


def _production_imports():
    root = profit_accounting_root()
    source = str(root / "src")
    if source not in sys.path:
        sys.path.insert(0, source)
    from profit_accounting_26.application.api_profile_store import ApiProfileStore  # noqa: PLC0415
    from profit_accounting_26.application.recognition_service import RecognitionService  # noqa: PLC0415
    from profit_accounting_26.application.settings_service import SettingsService  # noqa: PLC0415
    from profit_accounting_26.shared.paths import ApplicationPaths  # noqa: PLC0415

    return root, ApiProfileStore, RecognitionService, SettingsService, ApplicationPaths


def production_contract() -> dict[str, Any]:
    """Read, without calling AI, the current production first-AI contract."""
    root, _, RecognitionService, _, _ = _production_imports()
    return {
        "profit_accounting_root": str(root),
        "service": "RecognitionService.recognize",
        "prompt_version": RecognitionService.PROMPT_VERSION,
        "response_schema": RecognitionService.RESPONSE_SCHEMA,
    }


def _production_recognizer() -> Callable[[list[str]], FirstAIBaseline]:
    root, ApiProfileStore, RecognitionService, SettingsService, ApplicationPaths = _production_imports()

    class ReadOnlySettingsService(SettingsService):
        def save(self, data: dict) -> None:  # type: ignore[override]
            raise RuntimeError("生产设置需要迁移或修复；Direct Calibration 不会写入 Profit-Accounting 设置")

    paths = ApplicationPaths.default()
    settings = ReadOnlySettingsService(paths.settings_path, defaults_path=root / "config" / "defaults.json")
    service = RecognitionService(settings, ApiProfileStore(paths.data_dir))

    def recognize(image_paths: list[str]) -> FirstAIBaseline:
        observation, proposal = service.recognize([{"path": path} for path in image_paths])
        if proposal is None or not proposal.normal.is_complete():
            raise ValueError("首次 AI 未返回完整 normal 包装 baseline；请补充图片或在软件中完成首次 AI 估算后导入")
        normal = proposal.normal
        return FirstAIBaseline(
            product_name=str(observation.product_name or "UNKNOWN"),
            dimensions={
                "length": float(normal.length_cm),
                "width": float(normal.width_cm),
                "height": float(normal.height_cm),
            },
            weight_g=float(normal.weight_g),
            prompt_version=str(observation.prompt_version or RecognitionService.PROMPT_VERSION),
            model=str(observation.model or ""),
        )

    return recognize


def has_user_calibration(fields: dict[str, Any]) -> bool:
    return any(
        fields.get(key) not in (None, "", "UNKNOWN")
        for key in (
            "actual_dimensions", "actual_weight", "actual_freight", "actual_forwarder",
            "user_note", "error_direction", "error_type",
        )
    )


def has_complete_baseline(fields: dict[str, Any]) -> bool:
    return (
        intake.parse_dimensions(fields.get("baseline_dimensions")) is not None
        and intake.parse_weight(fields.get("baseline_weight")) is not None
    )


def resolve_baseline(fields: dict[str, Any], image_paths: list[str], *, resolver=None) -> tuple[dict[str, Any], bool, FirstAIBaseline | None]:
    """Use supplied baseline as-is, otherwise call the current production first-AI service once."""
    if has_complete_baseline(fields):
        return fields, False, None
    if not image_paths:
        raise ValueError("缺少完整 baseline 时必须提供至少一张图片")
    baseline = (resolver or _production_recognizer())(image_paths)
    resolved = dict(fields)
    resolved["baseline_dimensions"] = baseline.dimensions
    resolved["baseline_weight"] = baseline.weight_g
    if not resolved.get("name"):
        resolved["name"] = baseline.product_name
    source = str(resolved.get("source") or "").strip()
    provenance = "Direct Calibration / Profit-Accounting first AI " + baseline.prompt_version
    resolved["source"] = source + ("; " if source else "") + provenance
    return resolved, True, baseline


def process_single(
    records_path: str | Path,
    fields: dict[str, Any],
    *,
    image_paths: list[str],
    dry_run: bool = False,
    source_type: str = "SINGLE",
    resolver=None,
) -> dict[str, Any]:
    resolved, ai_called, baseline = resolve_baseline(fields, image_paths, resolver=resolver)
    preview = not has_user_calibration(resolved)
    if preview:
        return {"written": False, "preview": True, "ai_called": ai_called, "baseline": baseline, "record": None}
    record = intake.intake_single(
        records_path,
        dry_run=dry_run,
        images=image_paths,
        source_type=source_type,
        **resolved,
    )
    return {"written": not dry_run, "preview": False, "ai_called": ai_called, "baseline": baseline, "record": record}


def process_batch(
    records_path: str | Path,
    rows: list[dict[str, Any]],
    *,
    image_dir: str | Path | None = None,
    dry_run: bool = False,
    resolver=None,
) -> dict[str, Any]:
    saved, previews, skipped, ai_calls = [], [], [], 0
    for index, row in enumerate(rows, start=1):
        try:
            fields = intake.map_row(row, image_dir)
            paths = intake.parse_images(fields.pop("images", None), image_dir)
            result = process_single(
                records_path,
                fields,
                image_paths=paths,
                dry_run=dry_run,
                source_type="BATCH_IMAGES",
                resolver=resolver,
            )
            ai_calls += int(result["ai_called"])
            if result["preview"]:
                previews.append(index)
            else:
                saved.append(result["record"])
        except (ValueError, OSError) as exc:
            skipped.append({"row": index, "reason": str(exc)})
    return {"saved": saved, "previews": previews, "skipped": skipped, "ai_calls": ai_calls}


def build_parser():
    parser = argparse.ArgumentParser(description="Direct Calibration：复用 Profit-Accounting 首次 AI baseline")
    parser.add_argument("--records-file", default=str(intake.DEFAULT_RECORDS_PATH))
    sub = parser.add_subparsers(dest="mode", required=True)
    single = sub.add_parser("single")
    for name in ("name", "sku", "quantity", "source", "evidence-level", "baseline-dimensions", "baseline-weight", "baseline-freight", "baseline-forwarder", "actual-dimensions", "actual-weight", "actual-freight", "actual-forwarder", "user-note", "error-direction", "error-type", "physical-mechanism", "record-id"):
        single.add_argument("--" + name)
    single.add_argument("--images", action="append", required=True)
    single.add_argument("--dry-run", action="store_true")
    batch = sub.add_parser("batch")
    batch.add_argument("--file", required=True)
    batch.add_argument("--image-dir", required=True)
    batch.add_argument("--dry-run", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.mode == "single":
        fields = {
            key.replace("-", "_"): getattr(args, key.replace("-", "_"))
            for key in ("name", "sku", "quantity", "source", "evidence-level", "baseline-dimensions", "baseline-weight", "baseline-freight", "baseline-forwarder", "actual-dimensions", "actual-weight", "actual-freight", "actual-forwarder", "user-note", "error-direction", "error-type", "physical-mechanism", "record-id")
        }
        result = process_single(args.records_file, fields, image_paths=args.images, dry_run=args.dry_run)
        if result["preview"]:
            print("首次 AI baseline 已生成；缺少用户校准，未写入 Calibration Record。")
        else:
            print("已写入：" + result["record"]["record_id"])
        return 0
    rows, _ = intake.load_rows_from_file(args.file)
    result = process_batch(args.records_file, rows, image_dir=args.image_dir, dry_run=args.dry_run)
    print("成功：%d\n预览待补校准：%d\n跳过：%d\n首次 AI 调用：%d" % (len(result["saved"]), len(result["previews"]), len(result["skipped"]), result["ai_calls"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
