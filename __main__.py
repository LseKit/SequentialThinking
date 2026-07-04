#!/usr/bin/env python3
"""
Sequential Thinking MCP — 模块入口
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

用途:
    读取环境变量 + 解析 CLI 参数后启动 MCP 服务
    支持 http（Streamable HTTP）和 stdio 两种传输协议

配置优先级: CLI 参数 > 环境变量（ecosystem.config.js 注入）> 代码默认值

环境变量（由 ecosystem.config.js 的 env 字段注入）:
    ST_TRANSPORT  — 传输协议（http / stdio），默认 http
    ST_HOST       — HTTP 监听地址，默认 127.0.0.1
    ST_PORT       — HTTP 监听端口，默认 20010
    ST_DB_PATH    — 数据库路径，默认 Data/sequential-thinking.db

用法:
    python -m GitHubSrc                                     # 使用环境变量配置启动
    python -m GitHubSrc --transport stdio                   # CLI 覆盖环境变量
    python -m GitHubSrc --db-path /custom/path/db.db        # 自定义数据库路径
    python -m GitHubSrc --port 8080                         # 自定义端口
"""
import argparse
import os
import sys
from pathlib import Path

# ── 包上下文建立 ──
# 支持两种启动方式：
#   ① PM2 直接启动：SeqThinkVenV/bin/python GitHubSrc/__main__.py --env-file Config/.env
#   ② 模块启动：      python -m GitHubSrc
# 以下 3 行使方式①等价于方式②，25 处相对导入全部正常工作
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "GitHubSrc"


def main():
    """读取环境变量 + 解析 CLI 参数 + 启动服务"""

    # ── 第一步：解析 CLI 参数 ──
    parser = argparse.ArgumentParser(
        prog="GitHubSrc",
        description="Sequential Thinking MCP Server",
    )
    parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default=None,
        help="MCP 传输协议（覆盖环境变量 ST_TRANSPORT）",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="SQLite 数据库文件路径（覆盖环境变量 ST_DB_PATH）",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="HTTP 监听地址（覆盖环境变量 ST_HOST）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="HTTP 监听端口（覆盖环境变量 ST_PORT）",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help=".env 文件路径（相对路径相对于项目根目录）",
    )
    args = parser.parse_args()

    # ── 第二步：合并配置（CLI > 环境变量 > 默认值）──
    transport = args.transport or os.getenv("ST_TRANSPORT", "http")
    host = args.host or os.getenv("ST_HOST", "127.0.0.1")
    port = args.port or int(os.getenv("ST_PORT", "20010"))
    db_path = args.db_path or os.getenv("ST_DB_PATH", None)

    # 处理相对路径：相对于 GitHubSrc 目录
    if db_path and not os.path.isabs(db_path):
        github_src = Path(__file__).resolve().parent
        db_path = str(github_src / db_path)

    # ── 第三步：将最终配置写入 Server/Main（在 lifespan 触发前生效）──
    from .Server import Main as server_main
    server_main.SERVER_CONFIG = {
        "transport": transport,
        "db_path": db_path,
        "host": host,
        "port": port,
        "env_path": args.env_file,
    }

    # ── 第四步：根据传输协议启动服务 ──
    if transport == "stdio":
        server_main.mcp.run(transport="stdio")
    else:
        server_main.mcp.run(
            transport="http",
            host=host,
            port=port,
        )


if __name__ == "__main__":
    main()
