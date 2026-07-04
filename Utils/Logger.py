"""
Sequential Thinking MCP — 日志工具
路径: Utils/Logger.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

设计说明:
    仅使用 StreamHandler 输出到 stdout，不写文件。
    日志持久化由 PM2 统一管理（pm2-logrotate 负责轮转）。
    避免 FileHandler + PM2 双写导致日志重复。
"""
import sys
import logging


def setup_logger(name: str) -> logging.Logger:
    """
    创建仅输出到 stdout 的 logger

    Args:
        name: logger 名称（通常用模块名，如 "server", "engine"）

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 防止重复添加 handler（模块热重载时）
    if logger.handlers:
        return logger

    # 仅保留 StreamHandler（stdout）
    # PM2 会捕获 stdout/stderr 并写入自己的日志文件 + 轮转
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "[%(name)s] %(message)s"
    ))
    logger.addHandler(ch)

    return logger
