# -*- coding: utf-8 -*-
"""Tests for check_software_contract"""
import json
import sys
from pathlib import Path

import pytest

# 添加 tools 到 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from check_software_contract import (
    ContractCheckError,
    check_contract,
    check_engine_version,
    check_export_contract,
    check_prompt_version,
    check_validator_available,
    load_local_paths,
)


def test_load_local_paths():
    """能加载 config/local_paths.json"""
    paths = load_local_paths()
    assert isinstance(paths, dict)
    assert "profit_accounting_root" in paths


def test_check_profit_accounting_root():
    """主软件路径存在"""
    paths = load_local_paths()
    root = Path(paths["profit_accounting_root"])
    assert root.exists()


def test_check_prompt_version():
    """能读取当前 Prompt 版本"""
    paths = load_local_paths()
    root = Path(paths["profit_accounting_root"])
    version = check_prompt_version(root)
    assert isinstance(version, str)
    assert version  # 非空


def test_check_engine_version():
    """能读取当前 Engine 版本"""
    paths = load_local_paths()
    root = Path(paths["profit_accounting_root"])
    version = check_engine_version(root)
    assert isinstance(version, str)
    assert version  # 非空


def test_check_export_contract():
    """能读取 Export contract 版本"""
    paths = load_local_paths()
    root = Path(paths["profit_accounting_root"])
    contract = check_export_contract(root)
    assert contract == "Calibration Feedback Export V2"


def test_check_validator_available():
    """Validator 可用"""
    paths = load_local_paths()
    root = Path(paths["profit_accounting_root"])
    assert check_validator_available(root) is True


def test_check_contract():
    """完整合同检查通过"""
    result = check_contract()
    assert isinstance(result, dict)
    assert result["export_contract_version"] == "Calibration Feedback Export V2"
    assert result["rule_package_schema_version"] == "agent-calibration-rule-package-v1"
    assert result["validator_available"] is True
    assert result["replay_available"] is True
    assert result["promotion_available"] is True
    assert result["bundle_builder_available"] is True


def test_check_contract_with_wrong路径(monkeypatch):
    """路径错误时明确失败"""
    def fake_load():
        return {"profit_accounting_root": "/nonexistent/path"}

    monkeypatch.setattr("check_software_contract.load_local_paths", fake_load)

    with pytest.raises(ContractCheckError, match="不存在"):
        check_contract()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
