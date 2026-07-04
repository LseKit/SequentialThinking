"""
Sequential Thinking MCP — 会话管理工具（7 个 MCP 工具）
路径: Handlers/SessionHandlers.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

负责：start_thinking, add_step, update_step, review_thinking, 
      branch_thinking, merge_insights, delete_session
"""
import asyncio
from typing import Optional

from ..Core.Models import STEP_TYPES, MAX_STEP_CONTENT_LENGTH, MAX_PROBLEM_LENGTH
from ..Core import Context
from ..Core.Templates import get_template
from . import Helpers


def register(mcp):
    """向 FastMCP 实例注册全部会话管理工具"""

    @mcp.tool(name="start_thinking")
    async def start_thinking(
        problem: str,
        template: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> dict:
        """创建思维会话。支持9种模板，返回复杂度评估和优化后的问题。"""
        if not problem or not problem.strip():
            return {"error": "问题描述不能为空"}
        problem = problem.strip()
        if len(problem) > MAX_PROBLEM_LENGTH:
            return {"error": f"问题描述过长（{len(problem)} > {MAX_PROBLEM_LENGTH}字符）"}
        from ..Core.Models import ComplexityEstimate
        ctx = {}
        if template:
            tmpl = get_template(template)
            if not tmpl:
                return {"error": f'模板 "{template}" 不存在'}
            ctx["template_type"] = tmpl["type"]
            ctx["template_name"] = tmpl["name"]

        session = await Context.store_ref.create_session(problem, ctx, tags or [])

        analysis, complexity, optimized = "", ComplexityEstimate(), problem
        if hasattr(Context.engine_ref, "_call"):
            coros = [
                Context.engine_ref.generate_initial_analysis(problem),
                Context.engine_ref.estimate_complexity(problem),
                Context.engine_ref.optimize_query(problem),
            ]
            results = await asyncio.gather(*coros, return_exceptions=True)
            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    continue
                if i == 0: analysis = r
                elif i == 1: complexity = r
                elif i == 2: optimized = r
        else:
            analysis = Context.engine_ref.generate_initial_analysis(problem)
            complexity = Context.engine_ref.estimate_complexity(problem)
            optimized = Context.engine_ref.optimize_query(problem)

        return {
            "session_id": session.id,
            "initial_analysis": analysis,
            "complexity": {
                "level": complexity.level,
                "estimated_steps": complexity.estimated_steps,
                "suggested_template": complexity.suggested_template,
            },
            "optimized_query": optimized,
            "quality_score": session.quality_score,
        }

    @mcp.tool(name="add_step")
    async def add_step(
        session_id: str,
        step_content: str,
        step_type: str = "analysis",
        branch_id: Optional[str] = None,
        parent_step: Optional[int] = None,
        is_revision: bool = False,
        revises_step: Optional[int] = None,
    ) -> dict:
        """添加推理步骤。支持修订标记(is_revision/revises_step)和4种类型。"""
        if not step_content or not step_content.strip():
            return {"error": "步骤内容不能为空"}
        step_content = step_content.strip()
        if len(step_content) > MAX_STEP_CONTENT_LENGTH:
            return {"error": f"步骤内容过长（{len(step_content)} > {MAX_STEP_CONTENT_LENGTH}字符）"}
        if step_type not in STEP_TYPES:
            return {"error": f'无效步骤类型 "{step_type}"，可选: {", ".join(STEP_TYPES)}'}
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}

        if branch_id:
            step = await Context.store_ref.add_step_to_branch(
                session_id, branch_id, step_content, step_type, parent_step,
            )
        else:
            step = await Context.store_ref.add_step(
                session_id, step_content, step_type, parent_step,
                is_revision=is_revision, revises_step=revises_step,
            )

        session = await Context.store_ref.get_session(session_id)
        qs = await Helpers._calc_qs(session)
        conf = await Helpers._calc_conf(step, session)
        sugs = await Helpers._calc_sugs(session)

        # 自动完成：添加 conclusion 步骤且质量分 > 0.7 时自动标记会话为完成
        auto_completed = False
        if step_type == "conclusion" and float(qs) > 0.7:
            await Context.store_ref.complete_session(session_id)
            auto_completed = True

        return {
            "step_number": step.number,
            "quality_score": qs,
            "confidence": {"score": conf.score, "rationale": conf.rationale,
                           "risks": conf.risks},
            "suggestions": sugs,
            "progress": f"会话共 {len(session.steps)} 步",
            "auto_completed": auto_completed,
        }

    @mcp.tool(name="update_step")
    async def update_step(
        session_id: str,
        step_number: int,
        step_content: Optional[str] = None,
        step_type: Optional[str] = None,
    ) -> dict:
        """更新已有推理步骤的内容、类型或元数据。"""
        step = await Context.store_ref.update_step(session_id, step_number, step_content, step_type)
        if not step:
            return {"error": f"步骤 #{step_number} 不存在"}
        return {
            "step_number": step.number,
            "content_changed": step_content is not None,
            "type_changed": step_type is not None,
        }

    @mcp.tool(name="review_thinking")
    async def review_thinking(
        session_id: str,
        format: str = "linear",
    ) -> dict:
        """获取完整思维链（linear/tree/summary）。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        summary = await Helpers._gen_summary(session, format)
        return {
            "steps": [{
                "number": s.number, "type": s.type, "content": s.content,
                "timestamp": s.timestamp.isoformat(),
                "connections": s.connections,
            } for s in session.steps],
            "quality_score": session.quality_score,
            "summary": summary,
            "branches": {k: {"id": v.id, "from_step": v.from_step,
                             "steps": len(v.steps)}
                         for k, v in session.branches.items()},
        }

    @mcp.tool(name="branch_thinking")
    async def branch_thinking(
        session_id: str,
        from_step: int,
        alternative_reasoning: str,
    ) -> dict:
        """从指定步骤创建替代推理分支。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        branch = await Context.store_ref.create_branch(session_id, from_step, alternative_reasoning)
        await Context.store_ref.add_step_to_branch(
            session_id, branch.id, alternative_reasoning, "hypothesis"
        )
        return {"branch_id": branch.id, "divergence_point": from_step}

    @mcp.tool(name="merge_insights")
    async def merge_insights(session_id: str, branch_ids: list[str]) -> dict:
        """合并多个推理分支的洞察。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        main = [s.content for s in session.steps if s.type == "conclusion"]
        # 兜底：如果没有 conclusion 步骤，收集所有步骤内容（最多 5 步）
        if not main:
            main = [s.content for s in session.steps[-5:]]
        branch_ins = {}
        for bid in branch_ids:
            if bid in session.branches:
                branch_conclusions = [
                    s.content for s in session.branches[bid].steps
                    if s.type == "conclusion"
                ]
                # 兜底：如果分支没有 conclusion，收集所有步骤
                if not branch_conclusions:
                    branch_conclusions = [
                        s.content for s in session.branches[bid].steps[-5:]
                    ]
                branch_ins[bid] = branch_conclusions
        result = await Helpers._merge(main, branch_ins)
        return {"synthesis": result.synthesis, "conflicts": result.conflicts,
                "confidence": result.confidence, "strengths": result.strengths}

    @mcp.tool(name="complete_session")
    async def complete_session(session_id: str) -> dict:
        """将会话标记为已完成。"""
        completed = await Context.store_ref.complete_session(session_id)
        if not completed:
            return {"error": f"会话 {session_id} 不存在"}
        return {"success": True, "message": f"会话 {session_id} 已标记为完成"}

    @mcp.tool(name="delete_session")
    async def delete_session(session_id: str) -> dict:
        """删除指定会话及其所有关联数据（步骤、分支、标签）。"""
        deleted = await Context.store_ref.delete_session(session_id)
        if not deleted:
            return {"error": f"会话 {session_id} 不存在"}
        return {"success": True, "message": f"会话 {session_id} 及其关联数据已删除"}
