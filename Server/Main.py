#!/usr/bin/env python3
"""
Sequential Thinking MCP Server — Python Edition v1.2.1
路径: Server/Main.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

v3.3 变更:
- 支持 CLI 参数传入 db_path（由 __main__.py 设置 SERVER_CONFIG）
- 支持 http / stdio 两种传输协议
- 移除模块级 asyncio.run()，改用 FastMCP lifespan 生命周期管理
- 正确关闭资源（Store 和 Engine）
"""
import os, sys, asyncio
from pathlib import Path

# ── 将 GitHubSrc 的父目录加入 sys.path（使相对导入正常工作）──
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ..Utils.Logger import setup_logger
log = setup_logger("server")

from fastmcp import FastMCP
from ..Core import Context
from ..Storage.Store import Store
from ..Engine.Engine import HeuristicEngine, LLMEngine

# ── CLI 参数配置（由 __main__.py 在 lifespan 触发前设置）──
SERVER_CONFIG = {
    "transport": "http",
    "db_path": None,      # None = 使用默认值 Data/sequential-thinking.db
    "host": "127.0.0.1",
    "port": 20010,
    "env_path": None,     # .env 文件路径（由 --env-file 参数传入）
}

# 初始化标志（确保只初始化一次）
_initialized = False


async def _init():
    """初始化 Store 和 Engine（由 FastMCP lifespan 调用）"""
    global _initialized
    if _initialized:
        return
    _initialized = True

    # ── 加载 .env 文件（路径由 __main__.py 从 --env-file 参数传入）──
    # 必须在 os.getenv("DEEPSEEK_API_KEY") 之前执行
    env_path = SERVER_CONFIG.get("env_path")
    if env_path:
        _env = Path(env_path)
        if not _env.is_absolute():
            # 相对路径相对于项目根目录（GitHubSrc 的父目录）
            _env = Path(__file__).resolve().parent.parent.parent / env_path
        if _env.exists():
            from dotenv import load_dotenv
            load_dotenv(str(_env), override=True)
            log.info("已加载 .env | path=%s", _env)

    # 使用 CLI 传入的 db_path（None 则 Store 使用默认值）
    Context.store_ref = Store(db_path=SERVER_CONFIG.get("db_path"))
    await Context.store_ref.open()
    log.info("数据库已打开 | path=%s", Context.store_ref.db_path)

    # 初始化 LLM 引擎或启发式引擎。
    # 所有配置从环境变量读取，代码中不写死任何默认模型名。
    selector = int(os.getenv("ST_LLM_SELECTOR", "1"))
    if selector == 0:
        Context.engine_ref = HeuristicEngine()
        log.info("ST_LLM_SELECTOR=0 → 使用启发式引擎（无 LLM）")
    else:
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            Context.engine_ref = HeuristicEngine()
            log.info("DEEPSEEK_API_KEY 为空 → 降级为启发式引擎")
        else:
            api_key2 = os.getenv("DASHSCOPE_API_KEY", "")
            Context.engine_ref = LLMEngine(
                api_key=api_key,
                api_base=os.getenv("ST_LLM_API_BASE", ""),
                model=os.getenv("ST_LLM_MODEL", ""),
                timeout=int(os.getenv("ST_LLM_TIMEOUT", "120")),
                api_key2=api_key2,
                api_base2=os.getenv("ST_LLM2_API_BASE", ""),
                model2=os.getenv("ST_LLM2_MODEL", ""),
                selector=selector,
                moa_rounds=int(os.getenv("ST_MOA_ROUNDS", "3")),
                mode=os.getenv("ST_LLM_MODE", "self-moa"),
            )
            log.info("LLM 引擎已启用 | selector=%d | mode=%s | model1=%s model2=%s | rounds=%d",
                     selector,
                     os.getenv("ST_LLM_MODE", "self-moa"),
                     os.getenv("ST_LLM_MODEL", ""),
                     os.getenv("ST_LLM2_MODEL", ""),
                     int(os.getenv("ST_MOA_ROUNDS", "3")))


async def _shutdown():
    """优雅关闭：清理 httpx 连接池和数据库连接"""
    if Context.engine_ref and hasattr(Context.engine_ref, 'close'):
        await Context.engine_ref.close()
        log.info("LLM 引擎已关闭（httpx 连接池释放）")
    if Context.store_ref:
        await Context.store_ref.close()
        log.info("数据库连接已关闭")


# ── FastMCP 生命周期管理 ──
from contextlib import asynccontextmanager

@asynccontextmanager
async def _lifespan(server):
    """启动时初始化，关闭时清理"""
    await _init()
    yield {}
    await _shutdown()


# ── 创建 FastMCP 实例（lifespan 通过构造函数参数传入）──
mcp = FastMCP("sequential-thinking", lifespan=_lifespan)


# ── 注册全部 23 个 MCP 工具 ──
from ..Handlers.Register import register_all
register_all(mcp)
log.info("23 个 MCP 工具已委托注册（4 子模块）")

# 工具计数仅用于 resource 元数据，新增工具时更新此处即可
_TOOL_COUNT = 26
log.info("%d 个 MCP 工具已注册", _TOOL_COUNT)


@mcp.resource("config://server")
def server_config() -> dict:
    return {
        "name": "sequential-thinking",
        "title": "Sequential Thinking",
        "version": "1.2.0",
        "tools_count": _TOOL_COUNT,
    }


@mcp.resource("thinking://templates/catalog")
def templates_catalog() -> dict:
    """返回全部 9 种思维模板的目录"""
    from ..Core.Templates import get_all_templates
    tmpls = get_all_templates()
    return {
        "total": len(tmpls),
        "templates": [
            {"id": tid, "name": t["name"], "description": t["description"],
             "when_to_use": t["when_to_use"]}
            for tid, t in tmpls.items()
        ],
    }


@mcp.prompt()
def problem_breakdown(problem: str) -> str:
    """引导智能体将复杂问题分解为子问题"""
    return f"""请将以下问题分解为3-5个子问题，每个子问题应独立可分析：

问题：{problem}

对于每个子问题：
1. 明确子问题的范围
2. 识别需要的信息
3. 建议分析方法
4. 预估复杂度（easy/medium/hard）

最后，给出推荐的解决顺序。"""


@mcp.prompt()
def critical_analysis(session_summary: str) -> str:
    """引导智能体对推理结论进行批判性审视"""
    return f"""请对以下推理过程和结论进行批判性分析：

{session_summary}

请从以下角度挑战：
1. 是否存在逻辑漏洞？
2. 有哪些隐含假设未被验证？
3. 结论是否过度泛化？
4. 是否有重要的替代解释被忽略？
5. 如果结论是错误的，最可能的原因是什么？

最后，给出一个1-10的置信度评分并解释理由。"""


@mcp.prompt()
def synthesis_prompt(insights: str) -> str:
    """引导智能体将多个洞察综合为统一结论"""
    return f"""请将以下多个洞察综合为一个统一的结论：

{insights}

要求：
1. 识别各洞察之间的共识和分歧
2. 按重要性排序关键发现
3. 给出综合结论（不超过3句话）
4. 标注结论的置信度（高/中/低）
5. 列出需要进一步验证的假设"""
