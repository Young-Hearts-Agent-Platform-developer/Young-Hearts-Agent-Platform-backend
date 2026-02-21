# Readme-Manager 提示词（设计）完整报告

## 报告日期
2026-01-16

## 核心需求
为项目生成一个新的自定义智能体，具体功能要求如下：
1. 深入研究目前的项目架构、功能实现等关键信息；
2. 生成/更新一份详尽的 README.md 文件。

## 目标文件上下文详情
- 文件路径：`e:\Project\Web_Development\Young-Hearts-Agent-Platform\Young-Hearts-Agent-Platform-backend\.github\agents\Readme-Manager.agent.md`
- 文件用途：作为一个自定义 Agent（`.agent.md`），用于在 VS Code 或 GitHub Copilot 环境中，协助开发者维护项目的 README 文档。
- 上下文核心：项目采用 Python/FastAPI 后端架构，拥有丰富的文档（`docs/` 目录），需要定期将代码变更反映到 README 中。
- 适配逻辑：
    - 使用 YAML frontmatter 定义 Agent 元数据（name, type, tools）。
    - 结构化 Prompt 设计，确保 Agent 能主动调用工具（File Search, Read File）来获取信息，而不是仅仅基于记忆编造。
    - 定义了标准的 `README.md` 模板结构，确保输出的一致性。

## 设计详情

### 核心设计思路
1.  **角色定义 (Role)**: 设定为“高级技术文档工程师”，强调其构建“心理模型”和“转化技术细节”的能力，确保生成的文档既准确又易读。
2.  **工具赋能 (Tools)**: 显式赋予 `read_file`, `list_dir`, `file_search` 等工具权限，强制 Agent 在回答前必须先“看”代码。
3.  **流程拆解 (Workflow)**: 将任务拆解为“全局分析 - 差异对比 - 文档构建 - 自我验证”四个步骤。
    - **全局分析**: 强制检查 `pyproject.toml` 等关键文件，避免遗漏依赖信息。
    - **差异对比**: 专门针对“更新”场景，避免覆盖有效旧信息。
    - **文档构建**: 提供具体的标准 Markdown 章节列表，规范输出格式。
4.  **约束设定 (Constraints)**: 强调“事实导向”，严禁编造不存在的 API 或路径。

### 验证过程
- **模拟场景**:
    - 用户输入：“为当前项目生成 README”。
    - Agent 行为：首先调用 `list_dir` 根目录，发现 `pyproject.toml` 和 `app/`，然后读取 `docs/` 下的功能文档，最后生成包含“Installation”和“Features”章节的 Markdown。
- **验证维度**:
    - 需求匹配度：✓ 符合（涵盖了研究和生成两个核心需求）。
    - 上下文适配度：✓ 贴合（自动识别 Python/FastAPI 项目结构）。
    - 角色清晰度：✓ 清晰（文档工程师）。
    - 流程可执行性：✓ 可执行（步骤明确，工具对应）。

## 使用指南
- **适用场景**:
    - 项目初始化时生成第一版 README。
    - 完成重大功能迭代后，需要更新 README 的功能列表和接口说明。
    - 修复文档中的过时命令或死链。
- **常见问题**:
    - **问题**: Agent 找不到某些文件。
    - **解决**: 建议在 Prompt 中明确文件大概位置，或要求 Agent 先进行全局搜索。
    - **问题**: 生成的内容过于简略。
    - **解决**: 在输入时提供更详细的指令，例如“详细列出所有 API 端点”或“补充详细的配置参数说明”。

## 版本记录
|日期|修改内容|修改原因|
|---|---|---|
|2026-01-16|初始设计完成|满足用户关于“深入研究项目并生成 README”的自定义 Agent 需求|
