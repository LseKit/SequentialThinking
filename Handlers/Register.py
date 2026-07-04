"""
Sequential Thinking MCP — 工具注册入口
路径: Handlers/Register.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

v3.1 重构：从单文件拆分为 5 个职责子模块。
本文件仅保留 register_all() 入口，向各子模块委派工具注册。
"""
from ..Utils.Logger import setup_logger
log = setup_logger("handlers")

# 子模块导入（按职责拆分为 4 个 handler + 1 个 helpers）
from . import SessionHandlers
from . import QualityHandlers
from . import AdminHandlers
from . import EnhanceHandlers


def register_all(mcp):
    """注册全部 MCP 工具——向各职责子模块委派"""
    SessionHandlers.register(mcp)   # 8 工具：会话生命周期
    QualityHandlers.register(mcp)   # 3 工具：质量控制
    AdminHandlers.register(mcp)     # 4 工具：管理功能
    EnhanceHandlers.register(mcp)   # 11 工具：增强功能（含 Self-MoA、假设提取）
    # 8 + 3 + 4 + 11 = 26
    log.info("MCP 工具已委托注册（4 子模块）")
