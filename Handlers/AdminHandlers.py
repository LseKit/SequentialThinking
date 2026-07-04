"""
Sequential Thinking MCP — 管理工具（5 个 MCP 工具）
路径: Handlers/AdminHandlers.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

负责：export_session, list_sessions, search_sessions, get_metrics
"""
import json
from typing import Optional

from ..Core import Context


def register(mcp):
    """向 FastMCP 实例注册全部管理工具"""

    @mcp.tool(name="export_session")
    async def export_session(
        session_id: str,
        format: str = "markdown",
        include_branches: bool = False,
    ) -> dict:
        """导出会话（markdown/json/text）。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        if format == "json":
            content = json.dumps({
                "id": session.id, "problem": session.problem,
                "steps": [{"number": s.number, "type": s.type, "content": s.content,
                           "timestamp": s.timestamp.isoformat()}
                          for s in session.steps],
                "quality": session.quality_score,
            }, ensure_ascii=False, indent=2)
        else:
            parts = [f"# 思维会话\n**问题:** {session.problem}",
                     f"**质量:** {session.quality_score:.2f}",
                     f"**状态:** {session.status}\n"]
            parts.extend(f"### {s.type.upper()} #{s.number}\n{s.content}"
                         for s in session.steps)
            content = "\n\n".join(parts) if format == "markdown" else \
                f"思维会话\n问题: {session.problem}\n质量: {session.quality_score:.2f}"
        fn = f"thinking_{session.id[:8]}.{format}"
        return {"content": content, "format": format, "filename": fn}

    @mcp.tool(name="list_sessions")
    async def list_sessions(
        status: Optional[str] = None,
        limit: int = 50,
    ) -> dict:
        """列出所有会话，按状态/标签过滤。"""
        sessions = await Context.store_ref.list_sessions(status or "", [], limit)
        return {"sessions": [{
            "id": s.id, "problem": s.problem,
            "step_count": s.step_count, "branch_count": s.branch_count,
            "status": s.status, "quality_score": s.quality_score,
            "created": s.created.isoformat(),
            "last_modified": s.last_modified.isoformat(),
            "tags": s.tags,
        } for s in sessions], "total": len(sessions)}

    @mcp.tool(name="search_sessions")
    async def search_sessions(query: str) -> dict:
        """按关键词全文搜索历史会话。"""
        sessions = await Context.store_ref.search_sessions(query)
        return {"sessions": [{
            "id": s.id, "problem": s.problem,
            "status": s.status, "quality_score": s.quality_score,
        } for s in sessions], "total": len(sessions), "query": query}

    @mcp.tool(name="get_metrics")
    async def get_metrics(time_range: str = "all") -> dict:
        """获取统计指标（day/week/month/all）。"""
        metrics = await Context.store_ref.get_metrics(time_range)
        return {"metrics": {
            "total_sessions": metrics.total_sessions,
            "active_sessions": metrics.active_sessions,
            "completed_sessions": metrics.completed_sessions,
            "average_steps": round(metrics.average_steps, 2),
            "average_quality": round(metrics.average_quality, 2),
            "average_branches": round(metrics.average_branches, 2),
        }}
