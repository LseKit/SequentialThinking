"""
Sequential Thinking MCP — 质量控制工具（3 个 MCP 工具）
路径: Handlers/QualityHandlers.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

负责：validate_logic, evaluate_quality, detect_biases
"""
from typing import Optional

from ..Core import Context
from . import Helpers


def register(mcp):
    """向 FastMCP 实例注册全部质量控制工具"""

    @mcp.tool(name="validate_logic")
    async def validate_logic(
        session_id: str,
        range_start: Optional[int] = None,
        range_end: Optional[int] = None,
    ) -> dict:
        """检测逻辑谬误（无支撑结论/未验证假设等）。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        start = range_start or 1
        end = range_end or len(session.steps)
        issues = Helpers._detect_issues(session, start, end)
        return {
            "issues": [{
                "step_number": i.step_number, "issue_type": i.issue_type,
                "description": i.description, "severity": i.severity,
                "suggestion": i.suggestion,
            } for i in issues],
            "suggestions": [i.suggestion for i in issues],
            "validity_score": Helpers._calc_validity(issues, end - start + 1),
            "strong_points": Helpers._find_strong(session, start, end),
        }

    @mcp.tool(name="evaluate_quality")
    async def evaluate_quality(session_id: str) -> dict:
        """5维质量评估（一致性/完整性/严谨性/创新性/可操作性）。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        qr = await Helpers._eval_quality(session)
        result = {
            "overall": qr.overall, "coherence": qr.coherence,
            "completeness": qr.completeness, "rigor": qr.rigor,
            "novelty": qr.novelty, "actionable": qr.actionable,
            "strengths": qr.strengths, "weaknesses": qr.weaknesses,
        }
        # LLM↔Heuristic 交叉验证（仅 LLM 引擎时，传入已计算的 LLM 结果避免重复调用）
        if hasattr(Context.engine_ref, 'is_llm') and Context.engine_ref.is_llm:
            xv = await Helpers._cross_validate_quality(session, llm_result=qr)
            result["cross_validation"] = xv
        return result

    @mcp.tool(name="detect_biases")
    async def detect_biases(session_id: str) -> dict:
        """检测8种认知偏见（确认偏见/锚定效应/可得性启发等）。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        biases = await Helpers._detect_bias(session)
        return {"biases": [{
            "name": b.name, "description": b.description,
            "severity": b.severity, "evidence": b.evidence,
            "suggestion": b.suggestion,
        } for b in biases], "total": len(biases)}
