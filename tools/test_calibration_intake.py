#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Calibration Intake V1 关键风险测试。
覆盖：单条保存 / 批量转换 / 缺字段不失败 / UNKNOWN 保存 / 不覆盖 / record_id 唯一 /
不读取历史归档 / 不包含 estimator / 不生成 validated rule / dry-run / JSON/JSONL/Excel。
运行：python tools/test_calibration_intake.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calibration_intake as ci  # noqa: E402

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print("PASS  " + name)
    else:
        FAIL.append(name)
        print("FAIL  " + name + ("  | " + detail if detail else ""))


def fresh_file(tmp):
    return Path(tmp) / "records.jsonl"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # 1. 单条记录能正常保存
        rec_file = fresh_file(tmp)
        rec = ci.intake_single(
            rec_file,
            name="测试商品",
            sku="SKU-1",
            quantity="2",
            evidence_level="B",
            baseline_weight="200",
            actual_freight="44.20",
            error_direction="HIGH",
            error_type="FOLDING_COMPRESSION",
            user_note="偏高",
        )
        check("1 单条保存", rec_file.exists() and len(rec_file.read_text(encoding="utf-8").splitlines()) == 1)
        check("1 record_id 格式", ci.RECORD_ID_RE.match(rec["record_id"]) is not None)
        check(
            "1 必填结构",
            all(k in rec for k in ("record_id", "product", "evidence", "baseline", "actual", "feedback", "analysis", "provenance")),
        )

        # 2/3/4. 批量 CSV 转换 + 缺字段不失败 + UNKNOWN 保存
        csv_path = tmp / "batch.csv"
        csv_path.write_text("name,sku,actual_freight,error_type\n商品A,SKU-A,50,WEIGHT_LOW\n商品B,,,\n", encoding="utf-8")
        rows, src = ci.load_rows_from_file(csv_path)
        saved, summary = ci.intake_batch(rec_file, rows, source_type=src)
        check("2 批量 CSV 转换", len(saved) == 2 and summary["saved"] == 2 and summary["total"] == 2)
        check("3 缺字段不导致整批失败", summary["skipped"] == 0)
        row_b = [r for r in saved if r["product"]["name"] == "商品B"][0]
        check("4 UNKNOWN 字符串保存", row_b["product"]["sku"] == "UNKNOWN" and row_b["feedback"]["error_type"] == "UNKNOWN")
        check("4 未知数字为 null", row_b["baseline"]["weight"] is None and row_b["actual"]["freight"] is None)
        check("4 未知图片为 []", row_b["evidence"]["images"] == [] and row_b["evidence"]["evidence_level"] == "UNKNOWN")

        # 5. 不会覆盖已有 record（只追加）
        before = len(rec_file.read_text(encoding="utf-8").splitlines())
        ci.intake_single(rec_file, name="追加商品")
        after = len(rec_file.read_text(encoding="utf-8").splitlines())
        check("5 只追加不覆盖", after == before + 1)

        # 6. record_id 唯一
        check("6 record_id 递增唯一", ci.next_record_id({"CAL-0001", "CAL-0002"}) == "CAL-0003")
        check("6 record_id 跳号唯一", ci.next_record_id({"CAL-0009"}) == "CAL-0010")
        dup_rows = [{"name": "X", "record_id": "CAL-9999"}, {"name": "Y", "record_id": "CAL-9999"}]
        saved2, summary2 = ci.intake_batch(fresh_file(tmp), dup_rows, source_type="BATCH_CSV")
        check("6 重复 record_id 跳过不覆盖", len(saved2) == 1 and summary2["skipped"] == 1)

        # 7. 不读取 legacy archive（工具源码不含历史归档引用）
        src_text = Path(ci.__file__).read_text(encoding="utf-8")
        check("7 不读取历史归档", "legacy" not in src_text and "archive" not in src_text)

        # 8. 不包含任何 estimator
        forbidden = ("packing_engine", "class Estimator", "def calculate_freight", "volumetric", "logistics_config")
        check("8 不包含 estimator", not any(f in src_text for f in forbidden))

        # 9. 不生成 validated rule
        try:
            ci.intake_single(fresh_file(tmp), name="X", status="VALIDATED")
            check("9 拒绝 VALIDATED", False)
        except ValueError:
            check("9 拒绝 VALIDATED", True)
        rec_normal = ci.intake_single(fresh_file(tmp), name="Y")
        check("9 不写入 VALIDATED", rec_normal["analysis"]["status"] != "VALIDATED")
        rows_v = [{"name": "V", "status": "VALIDATED"}, {"name": "W"}]
        saved_v, summary_v = ci.intake_batch(fresh_file(tmp), rows_v, source_type="BATCH_CSV")
        check("9 批量跳过 VALIDATED 行", len(saved_v) == 1 and summary_v["skipped"] == 1)

        # 10. JSON / JSONL / dry-run / Excel
        json_path = tmp / "batch.json"
        json_path.write_text(json.dumps([{"name": "J1", "actual_weight": "0.2kg"}], ensure_ascii=False), encoding="utf-8")
        rows_j, src_j = ci.load_rows_from_file(json_path)
        saved_j, _ = ci.intake_batch(fresh_file(tmp), rows_j, source_type=src_j)
        check("10 JSON 批量 + kg 换算", len(saved_j) == 1 and saved_j[0]["actual"]["weight"] == 200.0)

        dry_file = fresh_file(tmp)
        dry_before = dry_file.read_text(encoding="utf-8")
        ci.intake_single(dry_file, name="DRY", dry_run=True)
        rows_d = [{"name": "D1"}, {"name": "D2"}]
        ci.intake_batch(dry_file, rows_d, source_type="BATCH_CSV", dry_run=True)
        check("10 dry-run 不写入", dry_file.read_text(encoding="utf-8") == dry_before)

        try:
            import openpyxl  # noqa: F401

            xlsx_path = tmp / "batch.xlsx"
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["name", "sku", "actual_weight"])
            ws.append(["E1", "S1", "150"])
            ws.append(["E2", "S2", "160"])
            wb.save(xlsx_path)
            rows_x, src_x = ci.load_rows_from_file(xlsx_path)
            saved_x, _ = ci.intake_batch(fresh_file(tmp), rows_x, source_type=src_x)
            check("10 Excel 批量", len(saved_x) == 2)
        except ImportError:
            check("10 Excel 批量（openpyxl 缺失，跳过）", True)

    print()
    print("PASS=%d FAIL=%d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("FAILED: " + ", ".join(FAIL))
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
