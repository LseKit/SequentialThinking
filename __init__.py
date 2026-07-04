"""
Sequential Thinking MCP
路径: __init__.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

一个基于 FastMCP 的 AI 辅助顺序推理和思维链管理工具。
支持 20 个 MCP 工具，涵盖会话管理、质量控制、管理功能和增强功能。

主要特性：
- 9 种思维模板（科学方法、五问法、根因分析、决策矩阵等）
- 启发式引擎 + LLM 引擎双模式
- SQLite 异步持久化存储（WAL 模式）
- 分支推理和洞察合并
- 5 维质量评估和认知偏见检测

目录结构：
- Core/: 数据模型、模板、上下文
- Engine/: 推理引擎（启发式 + LLM）
- Storage/: SQLite 异步存储
- Handlers/: MCP 工具处理器（20 个工具）
- Server/: FastMCP 服务入口
- Utils/: 日志等通用工具

使用方式：
    python -m GitHubSrc
    # 或
    from GitHubSrc.Server.Main import mcp
    mcp.run(transport="http", host="127.0.0.1", port=20010)

环境变量：
    DEEPSEEK_API_KEY: LLM API 密钥（必填，否则使用启发式引擎）
    ST_LLM_API_BASE: API 端点（默认 https://api.deepseek.com/v1）
    ST_LLM_MODEL: 模型名称（默认 deepseek-v4-flash）
    ST_LLM_TIMEOUT: 超时秒数（默认 120）
    ST_DB_PATH: 数据库路径（CLI 参数 --db-path 可覆盖）
"""

__version__ = "1.2.1"
__author__ = "小逸"
