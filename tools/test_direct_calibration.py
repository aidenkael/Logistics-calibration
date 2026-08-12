#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Focused Direct Calibration tests; no live API call and no production write."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import direct_calibration as dc  # noqa: E402


PASS, FAIL = [], []


def check(name, condition):
    (PASS if condition else FAIL).append(name)
    print(("PASS  " if condition else "FAIL  ") + name)


def fake_resolver(paths):
    assert paths
    return dc.FirstAIBaseline("AI 商品", {"length": 12.0, "width": 8.0, "height": 3.0}, 150.0, "test-production-prompt", "test-model")


def main():
    contract = dc.production_contract()
    check("1 读取当前生产首次 AI 合同", contract["service"] == "RecognitionService.recognize" and bool(contract["prompt_version"]) and "shipment" in contract["response_schema"]["properties"])
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        image = root / "one.png"
        image.write_bytes(b"test-image")
        records = root / "records.jsonl"
        result = dc.process_single(records, {"actual_weight": "120", "user_note": "用户校准"}, image_paths=[str(image)], resolver=fake_resolver)
        check("2 单张图片生成首次 AI baseline", result["ai_called"] and result["record"]["baseline"]["weight"] == 150.0)
        check("2 单张图片加校准写入记录", result["written"] and records.exists())
        supplied = dc.process_single(records, {"name": "导入", "baseline_dimensions": "10x8x2", "baseline_weight": "100", "actual_weight": "90"}, image_paths=[str(image)], resolver=lambda _: (_ for _ in ()).throw(AssertionError("不应调用 AI")))
        check("3 已有 baseline 不重复调用 AI", not supplied["ai_called"] and supplied["written"])
        (root / "two.png").write_bytes(b"second-image")
        rows = [
            {"name": "A", "images": "one.png", "actual_weight": "120"},
            {"name": "B", "images": "two.png"},
        ]
        batch = dc.process_batch(records, rows, image_dir=root, resolver=fake_resolver)
        check("4 批量图片与数据表逐条归一", len(batch["saved"]) == 1 and batch["ai_calls"] == 2 and batch["saved"][0]["provenance"]["source_type"] == "BATCH_IMAGES")
        check("5 缺少用户校准只预览不写入", batch["previews"] == [2])
    print("PASS=%d FAIL=%d" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
