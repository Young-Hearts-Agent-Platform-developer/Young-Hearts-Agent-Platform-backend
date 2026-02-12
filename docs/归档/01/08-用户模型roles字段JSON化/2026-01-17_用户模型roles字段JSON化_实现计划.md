# 用户模型 roles 字段 JSON 化实现计划

## 版本记录

| 日期 | 版本 | 修改内容 | 修改原因 |
|---|---|---|---|
| 2026-01-17 | v1.0 | 初始计划 | 基于 2026-01-17 研究报告 |

## 关联研究
[docs/tasks/罗问然/08-用户模型roles字段JSON化/2026-01-17_用户模型roles字段JSON化_研究报告.md](docs/tasks/罗问然/08-用户模型roles字段JSON化/2026-01-17_用户模型roles字段JSON化_研究报告.md)

## 功能概述
将 User 模型的 roles 字段明确为 JSON 字符串（数组），并在所有相关代码层去除冗余类型兼容与转换逻辑，确保 API 返回 roles 字段始终为 List[str]，提升一致性与可维护性。

---

## Phase 1: ORM 与 Schema 层统一

### 目标
- 明确 User.roles 字段注释和类型，确保为 JSON 字符串存储。
- Pydantic schema 明确 roles 为 List[str]，优化 validator，去除冗余兼容代码。

### 修改文件清单
|文件路径|修改类型|说明|
|---|---|---|
|app/models/user.py|修改|roles 字段注释、类型说明|
|app/schemas/user.py|修改|roles 字段类型、validator 优化|

### 具体变更
- 明确 roles 字段注释为“JSON 字符串数组”，无需兼容 None/非 JSON。
- Pydantic schema 只接受/输出 List[str]，validator 仅做 json.loads/json.dumps，无需多余类型判断。

### 成功标准
- 自动验证：pytest 通过，roles 字段类型断言均为 List[str]。
- 手动验证：数据库 roles 字段均为 JSON 字符串，API 返回 roles 为数组。

---

## Phase 2: Service 与 API 层精简

### 目标
- 注册、登录、权限校验流程 roles 处理逻辑精简，去除冗余类型判断和转换。
- API 路由 roles 相关处理，去除冗余类型兼容代码。

### 修改文件清单
|文件路径|修改类型|说明|
|---|---|---|
|app/services/auth.py|修改|roles 处理逻辑精简|
|app/api/v1/routes/auth.py|修改|API 路由 roles 处理精简|

### 具体变更
- 只处理 roles 为 JSON 字符串与 List[str] 的互转，无需兼容 None/非 JSON。
- 依赖 schema 层校验，去除 API 层 roles 类型判断。

### 成功标准
- 自动验证：pytest 通过，注册/登录/鉴权相关测试 roles 字段断言均为 List[str]。
- 手动验证：API 注册、登录、用户信息接口 roles 字段为数组。

---

## Phase 3: 测试用例与文档同步

### 目标
- 测试用例 roles 字段断言与传参，确保类型一致。
- 文档 roles 字段描述同步为 JSON 字符串数组。
- openapi.json roles 字段类型为数组。

### 修改文件清单
|文件路径|修改类型|说明|
|---|---|---|
|tests/test_users.py|修改|roles 字段断言与传参|
|openapi.json|修改|roles 字段类型为数组|
|docs/“心青年”智能体平台-数据模型与 API 设计.md|修改|roles 字段描述同步|

### 具体变更
- 测试用例注册/登录/用户信息 roles 字段传参与断言均为 List[str]。
- 文档与 openapi.json roles 字段类型为数组，描述为“JSON 字符串数组”。

### 成功标准
- 自动验证：pytest 通过，roles 相关测试无类型错误。
- 手动验证：openapi.json、文档 roles 字段描述一致。

---

## Phase 4: 全链路验证与回归

### 目标
- 全链路验证 roles 字段类型一致性，无兼容性遗留。

### 修改文件清单
|文件路径|修改类型|说明|
|---|---|---|
|无|验证阶段|

### 具体变更
- 运行全量测试，手动验证注册、登录、用户信息、权限校验等接口 roles 字段类型。

### 成功标准
- 自动验证：pytest 全部通过。
- 手动验证：所有 API 返回 roles 字段为 List[str]，无类型兼容遗留。

---

## Commit message 模板

feat: 明确 User.roles 为 JSON 字符串数组，去除冗余类型兼容逻辑

- User ORM、schema、service、API 层 roles 字段类型统一
- 去除 roles 字段 None/非 JSON 字符串兼容逻辑
- 测试用例、文档、openapi.json roles 字段同步修正

## PR 描述要点
- 明确 roles 字段为 JSON 字符串数组，所有 API 返回为 List[str]
- 去除所有冗余类型兼容与转换逻辑，依赖 schema 层校验
- 测试、文档、openapi.json roles 字段同步
- 已全链路验证，无兼容性遗留
