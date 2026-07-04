"""
Sequential Thinking MCP — 全局共享上下文
路径: Core/Context.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

用途:
    存储全局的 Store 和 Engine 引用，解耦 Server 与 Handlers 之间的循环导入。
    Server 在启动时初始化这两个引用，Handlers 通过此模块访问。
"""

# Store 实例引用（Server 启动时赋值）
store_ref = None

# Engine 实例引用（Server 启动时赋值，可能是 HeuristicEngine 或 LLMEngine）
engine_ref = None
