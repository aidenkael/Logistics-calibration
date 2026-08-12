# Architecture

## 设计原则

**软件是唯一生产计算引擎；Agent 是离线校准、分析和规则编译工具。**

## 正式闭环

```
Calibration Feedback Export V2
  → Agent candidate
  → Validator (软件)
  → Offline Replay V1 (软件)
  → Promotion V1 (软件)
  → validated package
  → Formal Runtime Bundle V1 (软件)
  → 软件导入 inactive
  → 用户手动启用
```

## 本工作台不做的事

- 不维护生产 estimator
- 不决定正式包装尺寸
- 不宣布规则 validated
- 不直接修改软件 builtin registry
- 不修改 SQLite active calibration
- 不激活规则包

## 目录职责

| 目录 | 职责 |
|------|------|
| `config/` | 本机路径配置 |
| `inbox/` | 用户导入的待分析资料 |
| `work/` | Agent 临时工作区 |
| `archive/legacy/` | 旧项目历史档案（默认不读取） |
| `docs/` | 架构和工作流文档 |
