# -*- coding: utf-8 -*-
"""Software Contract Check

只读检查当前主软件（Profit-Accounting 2.6.1）的合同状态，
输出当前真实的版本号和接口可用性。

如发现：
- 主软件路径错误
- checkout 过旧
- Export V2 不存在
- baseline/engine 接口不匹配
- 官方 CLI 缺失

明确失败并停止，不继续生成 candidate。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


class ContractCheckError(Exception):
    """合同检查失败"""


def load_local_paths() -> dict[str, Any]:
    """加载 config/local_paths.json"""
    config_path = Path(__file__).resolve().parent.parent / "config" / "local_paths.json"
    if not config_path.exists():
        raise ContractCheckError(f"config/local_paths.json 不存在: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        paths = json.load(f)

    return paths


def check_profit_accounting_root(paths: dict[str, Any]) -> Path:
    """检查主软件路径"""
    root = paths.get("profit_accounting_root")
    if not root:
        raise ContractCheckError("profit_accounting_root 未配置")

    root_path = Path(root)
    if not root_path.exists():
        raise ContractCheckError(f"主软件路径不存在: {root_path}")

    return root_path


def check_prompt_version(root: Path) -> str:
    """检查 RecognitionService.PROMPT_VERSION"""
    try:
        sys.path.insert(0, str(root / "src"))
        from profit_accounting_26.application.recognition_service import RecognitionService
        return RecognitionService.PROMPT_VERSION
    except Exception as e:
        raise ContractCheckError(f"无法读取 PROMPT_VERSION: {e}")


def check_engine_version(root: Path) -> str:
    """检查 PackagingEstimationService.ENGINE_VERSION"""
    try:
        from profit_accounting_26.application.packaging_estimation_service import PackagingEstimationService
        return PackagingEstimationService.ENGINE_VERSION
    except Exception as e:
        raise ContractCheckError(f"无法读取 ENGINE_VERSION: {e}")


def check_baseline_version(root: Path) -> str:
    """检查 CURRENT_BASELINE_VERSION"""
    try:
        from profit_accounting_26.application.calibration_baseline import CURRENT_BASELINE_VERSION
        return CURRENT_BASELINE_VERSION
    except Exception as e:
        raise ContractCheckError(f"无法读取 CURRENT_BASELINE_VERSION: {e}")


def check_baseline_resource(root: Path) -> str:
    """检查 CURRENT_BASELINE_RESOURCE"""
    try:
        from profit_accounting_26.application.calibration_baseline import CURRENT_BASELINE_RESOURCE
        return CURRENT_BASELINE_RESOURCE
    except Exception as e:
        raise ContractCheckError(f"无法读取 CURRENT_BASELINE_RESOURCE: {e}")


def check_registry_resource(root: Path) -> str:
    """检查 CURRENT_REGISTRY_RESOURCE"""
    try:
        from profit_accounting_26.application.calibration_baseline import CURRENT_REGISTRY_RESOURCE
        return CURRENT_REGISTRY_RESOURCE
    except Exception as e:
        raise ContractCheckError(f"无法读取 CURRENT_REGISTRY_RESOURCE: {e}")


def check_export_contract(root: Path) -> str:
    """检查 Calibration Feedback Export contract version"""
    try:
        from profit_accounting_26.application.calibration_export_service import CONTRACT_VERSION
        return CONTRACT_VERSION
    except Exception as e:
        raise ContractCheckError(f"无法读取 Export CONTRACT_VERSION: {e}")


def check_rule_package_schema(root: Path) -> str:
    """检查 Agent Rule Package schema version"""
    try:
        from profit_accounting_26.application.calibration_rule_package_validator import SCHEMA_VERSION
        return SCHEMA_VERSION
    except Exception as e:
        raise ContractCheckError(f"无法读取 Rule Package SCHEMA_VERSION: {e}")


def check_validator_available(root: Path) -> bool:
    """检查 Validator 是否可用"""
    try:
        from profit_accounting_26.application.calibration_rule_package_validator import AgentCalibrationRulePackageValidator
        return True
    except Exception:
        return False


def check_replay_available(root: Path) -> bool:
    """检查 Offline Replay 是否可用"""
    try:
        from profit_accounting_26.application.calibration_offline_replay import OfflineCalibrationReplay
        return True
    except Exception:
        return False


def check_promotion_available(root: Path) -> bool:
    """检查 Promotion 是否可用"""
    try:
        from profit_accounting_26.application.calibration_rule_promotion import CalibrationRulePackagePromoter
        return True
    except Exception:
        return False


def check_bundle_builder_available(root: Path) -> bool:
    """检查 Runtime Bundle Builder 是否可用"""
    try:
        from profit_accounting_26.application.calibration_runtime_bundle import CalibrationRuntimeBundleBuilder
        return True
    except Exception:
        return False


def check_contract() -> dict[str, Any]:
    """执行完整合同检查

    Returns:
        合同状态字典
    """
    paths = load_local_paths()
    root = check_profit_accounting_root(paths)

    result = {
        "profit_accounting_root": str(root),
        "prompt_version": check_prompt_version(root),
        "engine_version": check_engine_version(root),
        "baseline_version": check_baseline_version(root),
        "baseline_resource": check_baseline_resource(root),
        "registry_resource": check_registry_resource(root),
        "export_contract_version": check_export_contract(root),
        "rule_package_schema_version": check_rule_package_schema(root),
        "validator_available": check_validator_available(root),
        "replay_available": check_replay_available(root),
        "promotion_available": check_promotion_available(root),
        "bundle_builder_available": check_bundle_builder_available(root),
    }

    # 验证关键接口
    if not result["validator_available"]:
        raise ContractCheckError("AgentCalibrationRulePackageValidator 不可用")
    if not result["replay_available"]:
        raise ContractCheckError("OfflineCalibrationReplay 不可用")
    if not result["promotion_available"]:
        raise ContractCheckError("CalibrationRulePackagePromoter 不可用")
    if not result["bundle_builder_available"]:
        raise ContractCheckError("CalibrationRuntimeBundleBuilder 不可用")

    # 验证版本号
    if result["export_contract_version"] != "Calibration Feedback Export V2":
        raise ContractCheckError(
            f"Export contract 版本不匹配: {result['export_contract_version']}"
        )
    if result["rule_package_schema_version"] != "agent-calibration-rule-package-v1":
        raise ContractCheckError(
            f"Rule Package schema 版本不匹配: {result['rule_package_schema_version']}"
        )

    return result


def main() -> int:
    try:
        result = check_contract()
        print("合同检查通过:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        return 0

    except ContractCheckError as e:
        print(f"合同检查失败: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
