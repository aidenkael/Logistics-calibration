#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Calibration Intake V1
============================
物流校准工作台的校准录入工具：单条与批量录入统一转换为 Calibration Record
（schemas/calibration_record_v1.json），追加保存到 data/calibration_records.jsonl。

边界（与 docs/CALIBRATION_RULES.md 一致）：
 - 只记录，不计算运费，不实现第二套物流计算器，不生成或导出规则包。
- 不读取历史归档目录。
- 未知字符串保存为 UNKNOWN，未知数字保存为 null；缺失字段不导致整批失败。
- 只追加不覆盖；record_id 自动生成并保证唯一。
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import io
import json
import re
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
WORKBENCH = TOOL_DIR.parent
DEFAULT_RECORDS_PATH = WORKBENCH / "data" / "calibration_records.jsonl"

ERROR_TYPES = frozenset(
    {
        "DIMENSION_HIGH",
        "DIMENSION_LOW",
        "WEIGHT_HIGH",
        "WEIGHT_LOW",
        "PACKAGING_ASSUMPTION",
        "FOLDING_COMPRESSION",
        "STRUCTURE_MISREAD",
        "QUANTITY_MISMATCH",
        "SKU_MISMATCH",
        "FREIGHT_MISMATCH",
        "FORWARDER_MISMATCH",
        "DATA_CONFLICT",
        "UNKNOWN",
    }
)
ERROR_DIRECTIONS = frozenset({"HIGH", "LOW", "MIXED", "UNKNOWN"})
EVIDENCE_LEVELS = frozenset({"A", "B", "C", "D", "UNKNOWN"})
LIFECYCLE_STATUSES = frozenset(
    {
        "RECORDED",
        "PATTERN_CANDIDATE",
        "APPROVED_PENDING_PUBLICATION",
        "EXPORTED_PENDING_ACTIVATION",
        "SOFTWARE_ACTIVE",
    }
)
AGENT_WRITABLE_STATUSES = LIFECYCLE_STATUSES - {"SOFTWARE_ACTIVE"}
PHYSICAL_MECHANISMS = frozenset(
    {
        "FULL_FLAT_FOLD",
        "STRONG_COMPRESSION",
        "MODERATE_COMPRESSION",
        "SHAPE_RETAINED",
        "UNKNOWN",
    }
)
SOURCE_TYPES = frozenset(
    {
        "SINGLE",
        "BATCH_CSV",
        "BATCH_EXCEL",
        "BATCH_JSON",
        "BATCH_JSONL",
        "BATCH_IMAGES",
        "UNKNOWN",
    }
)
RECORD_ID_RE = re.compile(r"^CAL-\d{4,}$")

DIRECTION_RESULT = {
    "HIGH": "当前估算偏高",
    "LOW": "当前估算偏低",
    "MIXED": "误差方向混合，需复查",
    "UNKNOWN": "误差方向未知",
}

# 批量字段别名：列名 -> 记录字段。只做直接映射，不猜测。
FIELD_ALIASES = {
    "record_id": ("record_id", "recordid", "id"),
    "name": ("name", "product_name", "productname", "商品名称", "品名", "商品名"),
    "sku": ("sku", "货号", "商品编码"),
    "quantity": ("quantity", "qty", "数量", "件数"),
    "images": ("images", "image", "image_path", "image_paths", "图片", "图片路径"),
    "source": ("source", "来源"),
    "evidence_level": ("evidence_level", "evidence", "证据等级"),
    "baseline_dimensions": ("baseline_dimensions", "base_dimensions", "estimated_dimensions", "基准尺寸", "估算尺寸"),
    "baseline_weight": ("baseline_weight", "base_weight", "estimated_weight", "基准重量", "估算重量"),
    "baseline_freight": ("baseline_freight", "base_freight", "estimated_freight", "基准运费", "估算运费"),
    "baseline_forwarder": ("baseline_forwarder", "base_forwarder", "基准货代", "估算货代"),
    "actual_dimensions": ("actual_dimensions", "real_dimensions", "实际尺寸"),
    "actual_weight": ("actual_weight", "real_weight", "实际重量"),
    "actual_freight": ("actual_freight", "real_freight", "实际运费"),
    "actual_forwarder": ("actual_forwarder", "real_forwarder", "实际货代"),
    "user_note": ("user_note", "note", "feedback", "备注", "反馈"),
    "error_direction": ("error_direction", "direction", "误差方向"),
    "error_type": ("error_type", "误差类型", "分类"),
    "status": ("status", "状态"),
    "possible_pattern": ("possible_pattern", "pattern", "可能模式"),
    "physical_mechanism": ("physical_mechanism", "mechanism", "物理机制", "包装机制"),
}


def now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def norm_str(value) -> str:
    """字符串规整：空值返回 UNKNOWN。"""
    if value is None:
        return "UNKNOWN"
    text = str(value).strip()
    return text if text else "UNKNOWN"


def parse_number(value):
    """纯数字解析（不处理单位）：空/无法解析返回 None。"""
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.upper() in ("UNKNOWN", "N/A", "NA", "-"):
        return None
    try:
        return int(text) if text.lstrip("+-").isdigit() else float(text)
    except ValueError:
        return None


def parse_weight(value):
    """重量解析：默认 g；支持 kg/千克 换算为 g；无法解析返回 None。"""
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text.endswith("kg") or text.endswith("千克"):
        base = text[:-2].strip()
        if base and base.replace(".", "", 1).isdigit():
            return round(float(base) * 1000, 3)
        return None
    if text.endswith("g") or text.endswith("克"):
        base = text[:-1].strip()
        if base and base.replace(".", "", 1).isdigit():
            return float(base)
        return None
    return parse_number(text)


def parse_freight(value):
    """运费解析：去掉常见货币符号后解析；无法解析返回 None。"""
    if value is None:
        return None
    text = str(value).strip().replace("￥", "").replace("¥", "").replace("$", "").replace("元", "").replace(",", "").strip()
    return parse_number(text)


def parse_dimensions(value):
    """尺寸解析：接受 '10x5x3' / '10*5*3' / '10,5,3' / [10,5,3] / {length,width,height}。"""
    if value is None:
        return None
    if isinstance(value, dict):
        dims = {}
        for key in ("length", "width", "height"):
            if key in value:
                dims[key] = parse_number(value[key])
        return dims if dims else None
    if isinstance(value, (list, tuple)):
        nums = [parse_number(v) for v in value]
        if len(nums) == 3 and all(n is not None for n in nums):
            return {"length": nums[0], "width": nums[1], "height": nums[2]}
        return None
    text = str(value).strip().replace("cm", "").strip()
    parts = [p for p in re.split(r"[xX*×,，\s]+", text) if p]
    if len(parts) != 3:
        return None
    nums = [parse_number(p) for p in parts]
    if all(n is not None for n in nums):
        return {"length": nums[0], "width": nums[1], "height": nums[2]}
    return None


def parse_images(value, image_dir=None):
    """图片路径列表：接受数组或用 ; | , 分隔的字符串。"""
    if value is None:
        return []
    if isinstance(value, list):
        items = [str(v).strip() for v in value]
    else:
        items = re.split(r"[;|,，\n]+", str(value).strip())
    result = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        if image_dir and not Path(item).is_absolute() and "/" not in item and "\\" not in item:
            item = str(Path(image_dir) / item)
        result.append(item)
    return result


def norm_enum(value, allowed, default="UNKNOWN"):
    text = norm_str(value).upper().replace("-", "_").replace(" ", "_")
    return text if text in allowed else default


def make_record(
    record_id=None,
    name=None,
    sku=None,
    quantity=None,
    images=None,
    source=None,
    evidence_level=None,
    baseline_dimensions=None,
    baseline_weight=None,
    baseline_freight=None,
    baseline_forwarder=None,
    actual_dimensions=None,
    actual_weight=None,
    actual_freight=None,
    actual_forwarder=None,
    user_note=None,
    error_direction=None,
    error_type=None,
    status=None,
    possible_pattern=None,
    physical_mechanism=None,
    source_type="SINGLE",
    created_at=None,
    image_dir=None,
):
    return {
        "record_id": record_id,
        "product": {
            "name": norm_str(name),
            "sku": norm_str(sku),
            "quantity": parse_number(quantity),
        },
        "evidence": {
            "images": parse_images(images, image_dir),
            "source": norm_str(source),
            "evidence_level": norm_enum(evidence_level, EVIDENCE_LEVELS),
        },
        "baseline": {
            "dimensions": parse_dimensions(baseline_dimensions),
            "weight": parse_weight(baseline_weight),
            "freight": parse_freight(baseline_freight),
            "forwarder": norm_str(baseline_forwarder),
        },
        "actual": {
            "dimensions": parse_dimensions(actual_dimensions),
            "weight": parse_weight(actual_weight),
            "freight": parse_freight(actual_freight),
            "forwarder": norm_str(actual_forwarder),
        },
        "feedback": {
            "user_note": "" if user_note is None else str(user_note).strip(),
            "error_direction": norm_enum(error_direction, ERROR_DIRECTIONS),
            "error_type": norm_enum(error_type, ERROR_TYPES),
        },
        "analysis": {
            "status": norm_enum(status, AGENT_WRITABLE_STATUSES, default="RECORDED"),
            "possible_pattern": "" if possible_pattern is None else str(possible_pattern).strip(),
            "physical_mechanism": norm_enum(physical_mechanism, PHYSICAL_MECHANISMS),
        },
        "provenance": {
            "created_at": created_at or now_iso(),
            "source_type": norm_enum(source_type, SOURCE_TYPES),
        },
    }


def validate_record(record):
    """结构校验，返回问题列表。软件激活状态只能由软件正式流程写入。"""
    problems = []
    if not record.get("record_id") or not RECORD_ID_RE.match(str(record["record_id"])):
        problems.append("record_id 格式应为 CAL-XXXX")
    if record["evidence"]["evidence_level"] not in EVIDENCE_LEVELS:
        problems.append("evidence_level 非法")
    if record["feedback"]["error_direction"] not in ERROR_DIRECTIONS:
        problems.append("error_direction 非法")
    if record["feedback"]["error_type"] not in ERROR_TYPES:
        problems.append("error_type 非法")
    if record["analysis"]["status"] not in LIFECYCLE_STATUSES:
        problems.append("analysis.status 非法")
    if record["analysis"]["physical_mechanism"] not in PHYSICAL_MECHANISMS:
        problems.append("analysis.physical_mechanism 非法")
    if record["provenance"]["source_type"] not in SOURCE_TYPES:
        problems.append("source_type 非法")
    return problems


def load_existing_ids(path):
    ids = set()
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = rec.get("record_id") if isinstance(rec, dict) else None
            if isinstance(rid, str) and RECORD_ID_RE.match(rid):
                ids.add(rid)
    return ids


def next_record_id(existing_ids):
    max_num = 0
    for rid in existing_ids:
        m = re.match(r"^CAL-(\d+)$", rid)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return "CAL-%04d" % (max_num + 1)


def append_record(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as fh:
        if path.stat().st_size > 0:
            with path.open("rb") as rf:
                rf.seek(-1, io.SEEK_END)
                if rf.read(1) != b"\n":
                    fh.write("\n")
        fh.write(line + "\n")


def intake_single(records_path, dry_run=False, **fields):
    records_path = Path(records_path)
    if fields.get("status") is not None and str(fields["status"]).strip().upper() in {"VALIDATED", "SOFTWARE_ACTIVE"}:
        raise ValueError("Agent 不得写入 VALIDATED 或 SOFTWARE_ACTIVE")
    existing = load_existing_ids(records_path)
    rid = fields.get("record_id")
    if rid:
        rid = str(rid).strip()
        if not RECORD_ID_RE.match(rid):
            raise ValueError("record_id 格式应为 CAL-XXXX: " + rid)
        if rid in existing:
            raise ValueError("record_id 已存在，不覆盖: " + rid)
    else:
        rid = next_record_id(existing)
    fields["record_id"] = rid
    record = make_record(**fields)
    problems = validate_record(record)
    if problems:
        raise ValueError("; ".join(problems))
    if not dry_run:
        append_record(records_path, record)
    return record


def map_row(row, image_dir=None):
    lower = {}
    for key, val in row.items():
        lower[str(key).strip()] = val
        lower[str(key).strip().lower()] = val

    def pick(field):
        for alias in FIELD_ALIASES[field]:
            if alias in row:
                return row[alias]
            low = alias.lower()
            if low in lower:
                return lower[low]
        return None

    return {
        "record_id": pick("record_id"),
        "name": pick("name"),
        "sku": pick("sku"),
        "quantity": pick("quantity"),
        "images": pick("images"),
        "source": pick("source"),
        "evidence_level": pick("evidence_level"),
        "baseline_dimensions": pick("baseline_dimensions"),
        "baseline_weight": pick("baseline_weight"),
        "baseline_freight": pick("baseline_freight"),
        "baseline_forwarder": pick("baseline_forwarder"),
        "actual_dimensions": pick("actual_dimensions"),
        "actual_weight": pick("actual_weight"),
        "actual_freight": pick("actual_freight"),
        "actual_forwarder": pick("actual_forwarder"),
        "user_note": pick("user_note"),
        "error_direction": pick("error_direction"),
        "error_type": pick("error_type"),
        "status": pick("status"),
        "possible_pattern": pick("possible_pattern"),
        "physical_mechanism": pick("physical_mechanism"),
    }


def intake_batch(records_path, rows, source_type="BATCH_CSV", image_dir=None, dry_run=False):
    """批量录入。rows 为原始行（dict）。返回 (saved, summary)。"""
    records_path = Path(records_path)
    seen = set(load_existing_ids(records_path))
    saved = []
    skipped = []
    error_type_counts = {}
    patterns = {}
    for idx, row in enumerate(rows, start=1):
        try:
            if not isinstance(row, dict):
                skipped.append({"row": idx, "reason": "行不是键值对象"})
                continue
            mapped = map_row(row, image_dir)
            if mapped.get("status") is not None and str(mapped["status"]).strip().upper() in {"VALIDATED", "SOFTWARE_ACTIVE"}:
                skipped.append({"row": idx, "reason": "Agent 不得写入 VALIDATED 或 SOFTWARE_ACTIVE"})
                continue
            rid = mapped.pop("record_id", None)
            if rid:
                rid = str(rid).strip()
                if not RECORD_ID_RE.match(rid):
                    skipped.append({"row": idx, "reason": "record_id 格式非法: " + rid})
                    continue
                if rid in seen:
                    skipped.append({"row": idx, "reason": "record_id 重复，不覆盖: " + rid})
                    continue
            else:
                rid = next_record_id(seen)
            seen.add(rid)
            record = make_record(record_id=rid, source_type=source_type, image_dir=image_dir, **mapped)
            problems = validate_record(record)
            if problems:
                skipped.append({"row": idx, "reason": "; ".join(problems)})
                continue
            if not dry_run:
                append_record(records_path, record)
            saved.append(record)
            et = record["feedback"]["error_type"]
            error_type_counts[et] = error_type_counts.get(et, 0) + 1
            pat = record["analysis"]["possible_pattern"]
            if pat:
                patterns[pat] = patterns.get(pat, 0) + 1
        except Exception as exc:  # noqa: BLE001 - 单行异常不拖垮整批
            skipped.append({"row": idx, "reason": str(exc)})
    repeated = sorted(p for p, c in patterns.items() if c >= 2)
    summary = {
        "total": len(rows),
        "saved": len(saved),
        "skipped": len(skipped),
        "anomalies": sum(
            1
            for r in saved
            if r["feedback"]["error_type"] == "DATA_CONFLICT"
        ),
        "error_type_counts": error_type_counts,
        "repeated_patterns": repeated,
    }
    return saved, summary


def _load_csv(path):
    raw = path.read_bytes()
    text = None
    for enc in ("utf-8-sig", "gbk"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _load_excel(path):
    try:
        import openpyxl
    except ImportError:
        raise SystemExit("缺少 openpyxl：请先 pip install openpyxl，或将文件另存为 CSV/JSON/JSONL")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        try:
            header = next(rows_iter)
        except StopIteration:
            return []
        header = [("" if h is None else str(h)).strip() for h in header]
        rows = []
        for values in rows_iter:
            if values is None:
                continue
            row = {}
            for h, v in zip(header, values):
                if h:
                    row[h] = "" if v is None else v
            rows.append(row)
        return rows
    finally:
        wb.close()


def _load_json(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return data["records"]
    raise ValueError("JSON 应为对象数组或 {records: [...]} 结构")


def _load_jsonl(path):
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError("JSONL 第 %d 行不是合法 JSON" % lineno)
        rows.append(obj)
    return rows


def load_rows_from_file(path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _load_csv(path), "BATCH_CSV"
    if suffix in (".xlsx", ".xlsm"):
        return _load_excel(path), "BATCH_EXCEL"
    if suffix == ".json":
        return _load_json(path), "BATCH_JSON"
    if suffix in (".jsonl", ".ndjson"):
        return _load_jsonl(path), "BATCH_JSONL"
    raise ValueError("不支持的文件类型: %s（支持 CSV / Excel / JSON / JSONL）" % suffix)


def format_summary(summary):
    lines = [
        "总数量：" + str(summary["total"]),
        "成功：" + str(summary["saved"]),
        "缺失（跳过）：" + str(summary["skipped"]),
        "异常：" + str(summary["anomalies"]),
    ]
    if summary["error_type_counts"]:
        parts = ", ".join("%s=%d" % (k, v) for k, v in sorted(summary["error_type_counts"].items()))
        lines.append("error_type：" + parts)
    if summary["repeated_patterns"]:
        lines.append("重复模式：" + ", ".join(summary["repeated_patterns"]))
    else:
        lines.append("重复模式：无")
    return "\n".join(lines)


def print_single(record, dry_run=False):
    status = record["analysis"]["status"]
    handling = "已记录，暂不形成规则"
    if dry_run:
        handling = "DRY-RUN，未写入"
    elif status != "RECORDED":
        handling = "已记录：" + status + "，暂不形成规则"
    print("记录：" + record["record_id"])
    print("证据：" + record["evidence"]["evidence_level"])
    print("结果：" + DIRECTION_RESULT.get(record["feedback"]["error_direction"], "误差方向未知"))
    print("分类：" + record["feedback"]["error_type"])
    print("处理：" + handling)


def build_parser():
    parser = argparse.ArgumentParser(description="Direct Calibration Intake V1：单条/批量校准录入")
    parser.add_argument(
        "--records-file",
        default=str(DEFAULT_RECORDS_PATH),
        help="记录文件路径（默认 data/calibration_records.jsonl）",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    single = sub.add_parser("single", help="单条校准")
    single.add_argument("--records-file", default=None, help="记录文件路径（默认 data/calibration_records.jsonl）")
    single.add_argument("--name")
    single.add_argument("--sku")
    single.add_argument("--quantity")
    single.add_argument("--images", action="append", help="图片路径，可重复")
    single.add_argument("--source")
    single.add_argument("--evidence-level")
    single.add_argument("--baseline-dimensions")
    single.add_argument("--baseline-weight")
    single.add_argument("--baseline-freight")
    single.add_argument("--baseline-forwarder")
    single.add_argument("--actual-dimensions")
    single.add_argument("--actual-weight")
    single.add_argument("--actual-freight")
    single.add_argument("--actual-forwarder")
    single.add_argument("--user-note")
    single.add_argument("--error-direction")
    single.add_argument("--error-type")
    single.add_argument("--status")
    single.add_argument("--possible-pattern")
    single.add_argument("--physical-mechanism")
    single.add_argument("--record-id")
    single.add_argument("--dry-run", action="store_true")

    batch = sub.add_parser("batch", help="批量校准（CSV / Excel / JSON / JSONL）")
    batch.add_argument("--records-file", default=None, help="记录文件路径（默认 data/calibration_records.jsonl）")
    batch.add_argument("--file", required=True, help="数据文件路径")
    batch.add_argument("--image-dir", help="图片目录（与数据表中的图片文件名拼接）")
    batch.add_argument("--dry-run", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    records_file = args.records_file or str(DEFAULT_RECORDS_PATH)
    try:
        if args.mode == "single":
            fields = {
                "record_id": args.record_id,
                "name": args.name,
                "sku": args.sku,
                "quantity": args.quantity,
                "images": args.images,
                "source": args.source,
                "evidence_level": args.evidence_level,
                "baseline_dimensions": args.baseline_dimensions,
                "baseline_weight": args.baseline_weight,
                "baseline_freight": args.baseline_freight,
                "baseline_forwarder": args.baseline_forwarder,
                "actual_dimensions": args.actual_dimensions,
                "actual_weight": args.actual_weight,
                "actual_freight": args.actual_freight,
                "actual_forwarder": args.actual_forwarder,
                "user_note": args.user_note,
                "error_direction": args.error_direction,
                "error_type": args.error_type,
                "status": args.status,
                "possible_pattern": args.possible_pattern,
                "physical_mechanism": args.physical_mechanism,
            }
            record = intake_single(records_file, dry_run=args.dry_run, **fields)
            print_single(record, dry_run=args.dry_run)
        else:
            rows, source_type = load_rows_from_file(args.file)
            _, summary = intake_batch(
                records_file,
                rows,
                source_type=source_type,
                image_dir=args.image_dir,
                dry_run=args.dry_run,
            )
            print(format_summary(summary))
            if args.dry_run:
                print("DRY-RUN：未写入任何记录")
    except ValueError as exc:
        print("错误：" + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
