# -*- coding: utf-8 -*-
"""Tests for software_feedback_v2_intake

覆盖：
1. V2记录转换后通过 calibration_record_v1.json
2. record_id 为合法 CAL-XXXX
3. 不产生 Schema 禁止的顶层字段
4. baseline 映射正确
5. actual 与 suggested_package 不混淆
6. user_note 正确保存
7. Schema失败不会写入JSONL/index
8. 同一批完全重复导入会跳过
9. 同 software record 的后续新批次不会被永久挡住
10. 83历史文件全部 byte-level 不变
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import pytest

# 添加 tools 到 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from software_feedback_v2_intake import (
    CONTRACT_VERSION,
    IntakeError,
    _extract_constraints,
    build_calibration_record,
    dedup_key,
    extract_actual,
    extract_baseline,
    extract_feedback,
    import_manifest,
    load_manifest,
    load_schema,
    next_cal_id,
    validate_record_v1,
)

# ── 83 历史文件 hash（byte-level 冻结验证） ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_HASHES = {
    "data/calibration_records.jsonl": "f4c7cf639807f6bc2a345ac02d7aa875f0629fd86016317f07c6039ac46bca1f",
    "data/fb83_freight_inference_v1.csv": "841d51486dbdaf3bd641183325acf476c45731d425a93df2bd2133e747ffb058",
    "data/formal_rule_package_fb83_final.json": "d762d0a0140e83b74fabd848d4810ecc806fa127c1f283de6b7743386b4689fc",
    "docs/FB83_FINAL_CLOSURE_REPORT.md": "d9059cd314f9f4ccc52aaa8a4a2208606d2ed8d9cd9e8624a775c8dcd9de5969",
}


# ── Fixtures ──

def make_minimal_v2_manifest(batch_id="test_batch_001"):
    """创建最小 V2 manifest fixture"""
    return {
        "contract_version": "Calibration Feedback Export V2",
        "export_batch_id": batch_id,
        "records": [
            {
                "record_id": "rec_001",
                "sequence": 1,
                "product_short_name": "测试商品",
                "image_relative_paths": ["001_1.png"],
                "machine_facts": {
                    "ai_initial": {
                        "observation": {
                            "product_name": "测试商品",
                        },
                        "packaging_proposal": {
                            "normal": {
                                "length_cm": 10.0,
                                "width_cm": 5.0,
                                "height_cm": 3.0,
                                "weight_g": 100,
                                "packaging_state": "unknown",
                                "packaging_method": "box",
                                "confidence": "medium",
                            }
                        }
                    },
                    "local_adopted": None,
                    "reestimate_history": [],
                    "user_feedback": {
                        "suggested_package": {
                            "length_cm": 12.0,
                            "width_cm": 6.0,
                            "height_cm": 4.0,
                            "weight_g": 120,
                            "note": "用户校准",
                        },
                        "actual_logistics": {
                            "actual_package_length_cm": 11.0,
                            "actual_package_width_cm": 5.5,
                            "actual_package_height_cm": 3.5,
                            "actual_package_weight_g": 110,
                            "actual_freight": 25.0,
                        }
                    }
                }
            }
        ]
    }


def write_manifest(tmpdir: Path, manifest: dict) -> Path:
    """写入 manifest 到临时目录"""
    manifest_path = tmpdir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)
    return manifest_path


def backup_data_files():
    """备份可能被修改的文件，返回 backup dict"""
    records_path = PROJECT_ROOT / "data" / "calibration_records.jsonl"
    index_path = PROJECT_ROOT / "data" / "software_import_index.json"
    backups = {}
    for label, p in [("records", records_path), ("index", index_path)]:
        backups[label] = p.read_bytes() if p.exists() else None
    return backups


def restore_data_files(backups: dict):
    """恢复备份"""
    records_path = PROJECT_ROOT / "data" / "calibration_records.jsonl"
    index_path = PROJECT_ROOT / "data" / "software_import_index.json"
    for label, content in backups.items():
        p = records_path if label == "records" else index_path
        if content is not None:
            p.write_bytes(content)


# ── Test 1: V2记录转换后通过 schema ──

def test_converted_record_passes_schema():
    """V2记录转换后通过 calibration_record_v1.json 校验"""
    manifest = make_minimal_v2_manifest()
    record = manifest["records"][0]
    cal_record = build_calibration_record(record, "test_batch_001", "CAL-9001")
    errs = validate_record_v1(cal_record)
    assert errs == [], f"Schema 校验失败: {errs}"


# ── Test 2: record_id 为合法 CAL-XXXX ──

def test_record_id_format():
    """record_id 为合法 CAL-XXXX"""
    import re
    manifest = make_minimal_v2_manifest()
    record = manifest["records"][0]
    cal_record = build_calibration_record(record, "test_batch_001", "CAL-9001")
    assert re.match(r"^CAL-\d{4,}$", cal_record["record_id"])


def test_next_cal_id_format():
    """next_cal_id 生成合法 CAL-XXXX"""
    import re
    cid = next_cal_id()
    assert re.match(r"^CAL-\d{4,}$", cid)


# ── Test 3: 不产生 Schema 禁止的顶层字段 ──

def test_no_extra_top_level_fields():
    """不产生 schema 禁止的顶层字段"""
    manifest = make_minimal_v2_manifest()
    record = manifest["records"][0]
    cal_record = build_calibration_record(record, "test_batch_001", "CAL-9002")
    allowed = {"record_id", "product", "evidence", "baseline", "actual", "feedback", "analysis", "provenance"}
    extra = set(cal_record.keys()) - allowed
    assert extra == set(), f"禁止的顶层字段: {extra}"


# ── Test 4: baseline 映射正确 ──

def test_baseline_mapping():
    """baseline 正确映射 ai_initial.packaging_proposal.normal → dimensions/weight"""
    ai_initial = {
        "observation": {"product_name": "测试"},
        "packaging_proposal": {
            "normal": {
                "length_cm": 10.0,
                "width_cm": 5.0,
                "height_cm": 3.0,
                "weight_g": 100,
            }
        }
    }
    baseline = extract_baseline(ai_initial)
    assert baseline["dimensions"]["length"] == 10.0
    assert baseline["dimensions"]["width"] == 5.0
    assert baseline["dimensions"]["height"] == 3.0
    assert baseline["weight"] == 100
    assert baseline["freight"] is None
    assert baseline["forwarder"] is None


def test_baseline_missing_normal():
    """ai_initial.packaging_proposal.normal 缺失时失败"""
    ai_initial = {"observation": {}}
    with pytest.raises(IntakeError, match="normal"):
        extract_baseline(ai_initial)


# ── Test 5: actual 与 suggested_package 不混淆 ──

def test_actual_not_suggested():
    """actual 只来自 actual_logistics，suggested_package 不进入 actual"""
    machine_facts = {
        "user_feedback": {
            "suggested_package": {
                "length_cm": 99.0,  # 故意大值
                "width_cm": 99.0,
                "height_cm": 99.0,
                "weight_g": 999,
            },
            "actual_logistics": {
                "actual_package_length_cm": 11.0,
                "actual_package_width_cm": 5.5,
                "actual_package_height_cm": 3.5,
                "actual_package_weight_g": 110,
                "actual_freight": 25.0,
            }
        }
    }
    actual = extract_actual(machine_facts)
    # actual 应该来自 actual_logistics，不是 suggested_package
    assert actual["dimensions"]["length"] == 11.0
    assert actual["weight"] == 110
    assert actual["freight"] == 25.0
    # 不应出现 suggested 的 99/999
    assert actual["dimensions"]["length"] != 99.0
    assert actual["weight"] != 999


def test_actual_empty_when_no_actual_logistics():
    """无 actual_logistics 时 actual 全 null"""
    machine_facts = {
        "user_feedback": {
            "suggested_package": {"length_cm": 12.0, "weight_g": 120},
        }
    }
    actual = extract_actual(machine_facts)
    assert actual["dimensions"] is None
    assert actual["weight"] is None
    assert actual["freight"] is None


# ── Test 6: user_note 正确保存 ──

def test_user_note_from_feedback():
    """user_note 从 user_feedback.note 提取"""
    machine_facts = {
        "user_feedback": {
            "note": "这是用户备注",
            "suggested_package": {"note": "包装建议备注"},
        }
    }
    fb = extract_feedback(machine_facts)
    assert fb["user_note"] == "这是用户备注"
    assert fb["error_direction"] == "UNKNOWN"
    assert fb["error_type"] == "UNKNOWN"


def test_user_note_fallback_to_suggested():
    """user_feedback.note 为空时 fallback 到 suggested_package.note"""
    machine_facts = {
        "user_feedback": {
            "suggested_package": {"note": "包装建议备注"},
        }
    }
    fb = extract_feedback(machine_facts)
    assert fb["user_note"] == "包装建议备注"


def test_user_note_empty_when_none():
    """都没有时 user_note 为空字符串"""
    machine_facts = {"user_feedback": {}}
    fb = extract_feedback(machine_facts)
    assert fb["user_note"] == ""


# ── Test 7: Schema 失败不会写入 JSONL/index ──

def test_schema_failure_no_write():
    """Schema 校验失败时不写入 JSONL 和 index"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # 创建一个会触发 schema 错误的 manifest（缺少 ai_initial）
        manifest = {
            "contract_version": CONTRACT_VERSION,
            "export_batch_id": "bad_batch",
            "records": [
                {
                    "record_id": "bad_rec",
                    "sequence": 1,
                    "product_short_name": "坏数据",
                    "image_relative_paths": [],
                    "machine_facts": {
                        "ai_initial": {
                            "observation": {},
                            "packaging_proposal": {"normal": {}},  # 空 normal → IntakeError
                        }
                    }
                }
            ]
        }
        write_manifest(tmpdir, manifest)
        backups = backup_data_files()
        try:
            result = import_manifest(tmpdir)
            # 应该报错，不导入
            assert result["imported"] == 0
            assert len(result["errors"]) > 0 or len(result["schema_errors"]) > 0
            # JSONL 不变
            records_path = PROJECT_ROOT / "data" / "calibration_records.jsonl"
            assert records_path.read_bytes() == backups["records"]
        finally:
            restore_data_files(backups)


# ── Test 8: 同一批完全重复导入会跳过 ──

def test_same_batch_dedup():
    """同一批完全重复导入会跳过"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        manifest = make_minimal_v2_manifest(batch_id="dedup_batch")
        write_manifest(tmpdir, manifest)
        backups = backup_data_files()
        try:
            result1 = import_manifest(tmpdir)
            assert result1["imported"] == 1

            result2 = import_manifest(tmpdir)
            assert result2["skipped"] == 1
            assert result2["imported"] == 0
        finally:
            restore_data_files(backups)


# ── Test 9: 同 software record 的后续新批次不会被永久挡住 ──

def test_new_batch_not_blocked():
    """同 software record 的新批次不被永久阻挡"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # 第一次导入 batch_A
        manifest_a = make_minimal_v2_manifest(batch_id="batch_A")
        write_manifest(tmpdir, manifest_a)
        backups = backup_data_files()
        try:
            result_a = import_manifest(tmpdir)
            assert result_a["imported"] == 1

            # 第二次导入 batch_B（同 software record_id，不同 batch）
            manifest_b = make_minimal_v2_manifest(batch_id="batch_B")
            write_manifest(tmpdir, manifest_b)
            result_b = import_manifest(tmpdir)
            assert result_b["imported"] == 1, "新批次应该能导入"
            assert result_b["skipped"] == 0
        finally:
            restore_data_files(backups)


# ── Test 10: 83 历史文件全部 byte-level 不变 ──

def test_83_records_byte_frozen():
    """83 条 JSONL byte-level 不变"""
    p = PROJECT_ROOT / "data" / "calibration_records.jsonl"
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    assert actual == EXPECTED_HASHES["data/calibration_records.jsonl"]


def test_145_images_frozen():
    """145 张图片不变"""
    images_dir = PROJECT_ROOT / "data" / "product_images" / "prima83"
    if not images_dir.exists():
        pytest.skip("prima83 目录不存在")
    images = list(images_dir.glob("*"))
    assert len(images) == 145


def test_old_candidate_frozen():
    """旧 candidate 不变"""
    p = PROJECT_ROOT / "data" / "formal_rule_package_fb83_final.json"
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    assert actual == EXPECTED_HASHES["data/formal_rule_package_fb83_final.json"]


def test_freight_inference_frozen():
    """费用反推文件不变"""
    p = PROJECT_ROOT / "data" / "fb83_freight_inference_v1.csv"
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    assert actual == EXPECTED_HASHES["data/fb83_freight_inference_v1.csv"]


# ── 补充：manifest 加载 ──

def test_load_manifest_valid():
    """能加载有效 V2 manifest"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        manifest = make_minimal_v2_manifest()
        write_manifest(tmpdir, manifest)
        loaded = load_manifest(tmpdir)
        assert loaded["contract_version"] == CONTRACT_VERSION
        assert len(loaded["records"]) == 1


def test_load_manifest_wrong_contract():
    """contract 版本错误时拒绝"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        manifest = make_minimal_v2_manifest()
        manifest["contract_version"] = "Wrong Version"
        write_manifest(tmpdir, manifest)
        with pytest.raises(IntakeError, match="contract_version"):
            load_manifest(tmpdir)


# ── 补充：validate_record_v1 自身 ──

def test_validate_rejects_extra_fields():
    """validate 拒绝含额外顶层字段的记录"""
    record = {
        "record_id": "CAL-0001",
        "product": {"name": "test", "sku": "X"},
        "evidence": {"images": []},
        "baseline": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "actual": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "feedback": {"user_note": "", "error_direction": "UNKNOWN", "error_type": "UNKNOWN"},
        "analysis": {"status": "RECORDED", "possible_pattern": "", "physical_mechanism": "UNKNOWN"},
        "provenance": {"created_at": "2026-01-01T00:00:00Z", "source_type": "SINGLE"},
        "extra_field": "not allowed",  # 额外字段
    }
    errs = validate_record_v1(record)
    assert any("禁止的顶层字段" in e for e in errs)


def test_validate_rejects_bad_record_id():
    """validate 拒绝非法 record_id"""
    record = {
        "record_id": "rec_001",  # 不是 CAL-XXXX
        "product": {"name": "test", "sku": "X"},
        "evidence": {"images": []},
        "baseline": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "actual": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "feedback": {"user_note": "", "error_direction": "UNKNOWN", "error_type": "UNKNOWN"},
        "analysis": {"status": "RECORDED", "possible_pattern": "", "physical_mechanism": "UNKNOWN"},
        "provenance": {"created_at": "2026-01-01T00:00:00Z", "source_type": "SINGLE"},
    }
    errs = validate_record_v1(record)
    assert any("pattern" in e for e in errs)


def test_validate_accepts_minimal_record():
    """validate 接受最小合规记录"""
    record = {
        "record_id": "CAL-0001",
        "product": {"name": "test", "sku": "X"},
        "evidence": {"images": []},
        "baseline": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "actual": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "feedback": {"user_note": "", "error_direction": "UNKNOWN", "error_type": "UNKNOWN"},
        "analysis": {"status": "RECORDED", "possible_pattern": "", "physical_mechanism": "UNKNOWN"},
        "provenance": {"created_at": "2026-01-01T00:00:00Z", "source_type": "SINGLE"},
    }
    errs = validate_record_v1(record)
    assert errs == []


# ── 补充：dry-run 不写入 ──

def test_dry_run_no_write():
    """dry-run 不实际写入"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        manifest = make_minimal_v2_manifest()
        write_manifest(tmpdir, manifest)
        backups = backup_data_files()
        try:
            result = import_manifest(tmpdir, dry_run=True)
            assert result["imported"] == 1
            assert result["dry_run"] is True
            # 文件不变
            records_path = PROJECT_ROOT / "data" / "calibration_records.jsonl"
            index_path = PROJECT_ROOT / "data" / "software_import_index.json"
            if backups["records"] is not None:
                assert records_path.read_bytes() == backups["records"]
            if backups["index"] is not None:
                assert index_path.read_bytes() == backups["index"]
        finally:
            restore_data_files(backups)


# ── Schema 驱动校验测试 ──

def test_schema_file_loads():
    """schema 文件可正常加载"""
    schema = load_schema(reload=True)
    assert isinstance(schema, dict)
    assert schema["type"] == "object"
    assert "record_id" in schema["properties"]
    assert schema.get("additionalProperties") is False


def test_schema_validates_v2_record():
    """schema 加载后验证 V2 转换记录通过"""
    schema = load_schema(reload=True)
    manifest = make_minimal_v2_manifest()
    record = manifest["records"][0]
    cal_record = build_calibration_record(record, "test_batch_001", "CAL-9001")
    errs = validate_record_v1(cal_record, _schema=schema)
    assert errs == [], f"Schema 驱动校验失败: {errs}"


def test_schema_drives_required():
    """validator 的 required 从 schema 读取，不是硬编码"""
    schema = load_schema(reload=True)

    # 构造一个缺少 evidence 字段的记录
    minimal = {
        "record_id": "CAL-0001",
        "product": {"name": "test", "sku": "X"},
        # "evidence" 缺失
        "baseline": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "actual": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "feedback": {"user_note": "", "error_direction": "UNKNOWN", "error_type": "UNKNOWN"},
        "analysis": {"status": "RECORDED", "possible_pattern": "", "physical_mechanism": "UNKNOWN"},
        "provenance": {"created_at": "2026-01-01T00:00:00Z", "source_type": "SINGLE"},
    }
    # 原始 schema 应报错
    errs = validate_record_v1(minimal, _schema=schema)
    assert any("evidence" in e for e in errs)

    # 修改 schema：移除 evidence 从 required
    modified = json.loads(json.dumps(schema))
    modified["required"] = ["record_id", "product", "baseline", "actual", "feedback", "analysis", "provenance"]
    errs2 = validate_record_v1(minimal, _schema=modified)
    # 不应再报 evidence 缺失
    assert not any("evidence" in e for e in errs2)


def test_schema_drives_enum():
    """validator 的 enum 从 schema 读取，不是硬编码"""
    schema = load_schema(reload=True)

    # 构造一条 analysis.status = "RECORDED" 的合规记录
    minimal = {
        "record_id": "CAL-0001",
        "product": {"name": "test", "sku": "X"},
        "evidence": {"images": []},
        "baseline": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "actual": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "feedback": {"user_note": "", "error_direction": "UNKNOWN", "error_type": "UNKNOWN"},
        "analysis": {"status": "RECORDED", "possible_pattern": "", "physical_mechanism": "UNKNOWN"},
        "provenance": {"created_at": "2026-01-01T00:00:00Z", "source_type": "SINGLE"},
    }

    # 原始 schema 通过
    assert validate_record_v1(minimal, _schema=schema) == []

    # 修改 schema：新增一个 status 值
    modified = json.loads(json.dumps(schema))
    modified["properties"]["analysis"]["properties"]["status"]["enum"].append("NEW_STATUS")
    minimal["analysis"]["status"] = "NEW_STATUS"
    # 应该通过（schema 允许了）
    assert validate_record_v1(minimal, _schema=modified) == []

    # 用原始 schema 则应失败
    errs = validate_record_v1(minimal, _schema=schema)
    assert any("status" in e for e in errs)


def test_schema_drives_pattern():
    """validator 的 record_id pattern 从 schema 读取，不是硬编码"""
    schema = load_schema(reload=True)

    minimal = {
        "record_id": "CAL-0001",
        "product": {"name": "test", "sku": "X"},
        "evidence": {"images": []},
        "baseline": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "actual": {"dimensions": None, "weight": None, "freight": None, "forwarder": None},
        "feedback": {"user_note": "", "error_direction": "UNKNOWN", "error_type": "UNKNOWN"},
        "analysis": {"status": "RECORDED", "possible_pattern": "", "physical_mechanism": "UNKNOWN"},
        "provenance": {"created_at": "2026-01-01T00:00:00Z", "source_type": "SINGLE"},
    }
    assert validate_record_v1(minimal, _schema=schema) == []

    # 修改 schema pattern 为只接受 REC- 前缀
    modified = json.loads(json.dumps(schema))
    modified["properties"]["record_id"]["pattern"] = "^REC-\\d{4,}$"
    minimal["record_id"] = "REC-0001"
    assert validate_record_v1(minimal, _schema=modified) == []

    # 原始 schema 应拒绝 REC- 前缀
    errs = validate_record_v1(minimal, _schema=schema)
    assert any("pattern" in e for e in errs)


def test_extract_constraints_reads_all_enums():
    """_extract_constraints 从 schema 正确提取所有 enum 集合"""
    schema = load_schema(reload=True)
    c = _extract_constraints(schema)

    assert "RECORDED" in c["statuses"]
    assert "SOFTWARE_ACTIVE" in c["statuses"]
    assert "HIGH" in c["error_directions"]
    assert "DIMENSION_HIGH" in c["error_types"]
    assert "FULL_FLAT_FOLD" in c["mechanisms"]
    assert "BATCH_JSON" in c["source_types"]
    assert "A" in c["evidence_levels"]
    assert "UNKNOWN" in c["evidence_levels"]
    assert c["record_id_pattern"].match("CAL-0001")
    assert not c["record_id_pattern"].match("REC-0001")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
