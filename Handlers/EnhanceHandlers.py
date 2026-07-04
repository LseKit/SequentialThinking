"""
Sequential Thinking MCP — 增强工具（9 个 MCP 工具）
路径: Handlers/EnhanceHandlers.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

负责：compare_sessions, suggest_next, rewrite_query, 
      visualize_thinking, replay_thinking, auto_tag,
      moa_analyze, add_connection, detect_contradictions
"""
import asyncio
import json
import re


def _match_with_negation(text: str, keywords: list[str], negations: list[str]) -> bool:
    """检查关键词是否出现在文本中，考虑否定前缀（如"不支持"≠"支持"）。
    
    否定前缀在关键词前 2 字符内出现时，反转匹配结果。
    """
    for kw in keywords:
        idx = text.find(kw)
        if idx == -1:
            continue
        # 检查关键词前是否有否定前缀
        prefix = text[max(0, idx-2):idx]
        if any(neg in prefix for neg in negations):
            continue  # "不支持" → 不算匹配
        return True
    return False


from ..Core import Context
from . import Helpers


def register(mcp):
    """向 FastMCP 实例注册全部增强工具"""

    @mcp.tool(name="compare_sessions")
    async def compare_sessions(session_a: str, session_b: str) -> dict:
        """对比两个会话的推理路径。"""
        a, b = await asyncio.gather(
            Context.store_ref.get_session(session_a),
            Context.store_ref.get_session(session_b)
        )
        if not a or not b:
            return {"error": "一个或两个会话不存在"}
        result = await Helpers._compare(a, b)
        return {
            "shared_assumptions": result.shared_assumptions,
            "divergent_conclusions": result.divergent_conclusions,
            "similarity": result.similarity,
            "recommendation": result.recommendation,
        }

    @mcp.tool(name="suggest_next")
    async def suggest_next(session_id: str) -> dict:
        """基于当前状态推荐3个下一步方向。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        sugs = await Helpers._suggest(session)
        return {"suggestions": sugs}

    @mcp.tool(name="rewrite_query")
    async def rewrite_query(query: str) -> dict:
        """LLM自动优化问题表述。"""
        opt = await Helpers._optimize(query)
        return {"original": query, "optimized": opt}

    @mcp.tool(name="visualize_thinking")
    async def visualize_thinking(session_id: str) -> dict:
        """导出Mermaid思维流程图，可视化推理路径和分支。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        lines = ["```mermaid", "flowchart TB",
                 f'  Problem["🟢 问题: {Helpers._trunc(session.problem, 60)}"]']
        prev = "Problem"
        for step in session.steps:
            shape_map = {
                "analysis": '("🔍","分析")',
                "hypothesis": '["💡","假设"]',
                "verification": '{{"✅","验证"}}',
                "conclusion": '["🎯","结论"]',
            }
            shape = shape_map.get(step.type, '("?")')
            lines.append(f'  S{step.number}{shape}')
            lines.append(f'  {prev} --> S{step.number}')
            prev = f"S{step.number}"
        for bid, branch in session.branches.items():
            lines.append(f'  B_{bid[:8]}["🌿 分支"]')
            lines.append(f'  S{branch.from_step} --> B_{bid[:8]}')
        lines.append("```")
        return {"mermaid": "\n".join(lines), "type": "mermaid"}

    @mcp.tool(name="replay_thinking")
    async def replay_thinking(session_id: str) -> dict:
        """逐步回放推理过程，用于教学和审计。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        frames = [{
            "step": s.number, "type": s.type, "content": s.content,
            "timestamp": s.timestamp.strftime("%H:%M:%S"),
            "connections": s.connections,
        } for s in session.steps]
        return {"session_id": session.id, "problem": session.problem,
                "total_frames": len(frames), "frames": frames}

    @mcp.tool(name="auto_tag")
    async def auto_tag(session_id: str) -> dict:
        """根据会话内容自动生成标签（基于关键词提取）。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        summary = await Helpers._gen_summary(session, "auto")
        text = session.problem + " " + summary
        words = re.split(r'[，。？：、！；\n\s,.:;!?]+', text)
        # 简单停用词表（中文常见无意义词）
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
                     '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
                     '看', '好', '自己', '这', '他', '她', '它', '们', '那', '些', '什么', '怎么',
                     '如何', '可以', '这个', '那个', '还是', '但是', '如果', '因为', '所以', '然后',
                     'the', 'a', 'an', 'is', 'are', 'of', 'to', 'in', 'and', 'for', 'with', 'that'}
        seen, tags = set(), []
        for w in words:
            w = w.strip()
            if len(w) >= 2 and w not in seen and len(tags) < 5 and w not in stopwords:
                seen.add(w)
                tags.append(w)
        if not tags:
            tags = [session.problem[:20]]
        return {"session_id": session.id, "tags": tags,
                "existing_tags": session.tags}

    @mcp.tool(name="moa_analyze")
    async def moa_analyze(
        session_id: str = "",
        problem: str = "",
        rounds: int = 3,
    ) -> dict:
        """Self-MoA多智能体分析：3轮独立LLM采样后投票综合。需要LLM引擎可用。"""
        # 从 session 获取上下文
        steps_text = ""
        if session_id:
            session = await Context.store_ref.get_session(session_id)
            if not session:
                return {"error": f"会话 {session_id} 不存在"}
            problem = problem or session.problem
            steps_text = "\n".join(
                f"[{s.type}] {s.content[:100]}" for s in session.steps[-5:]
            )
        if not problem:
            return {"error": "请提供 problem 参数或有效的 session_id"}
        if not hasattr(Context.engine_ref, '_call'):
            return {"error": "Self-MoA 需要 LLM 引擎支持（当前为启发式引擎）"}
        return await Context.engine_ref.moa_analyze(problem, steps_text, rounds) 

    @mcp.tool(name="add_connection")
    async def add_connection(
        session_id: str,
        from_step: int,
        to_step: int,
        branch_id: str = "",
    ) -> dict:
        """在两个已有步骤间添加双向关联（事后补充推理链路），支持主链和分支。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        # 根据 branch_id 选择步骤来源
        if branch_id:
            if branch_id not in session.branches:
                return {"error": f"分支 {branch_id} 不存在"}
            steps_list = session.branches[branch_id].steps
        else:
            steps_list = session.steps
        steps_by_num = {s.number: s for s in steps_list}
        if from_step not in steps_by_num:
            return {"error": f"步骤 #{from_step} 不存在（branch_id={branch_id or '主链'}）"}
        if to_step not in steps_by_num:
            return {"error": f"步骤 #{to_step} 不存在（branch_id={branch_id or '主链'}）"}
        # 去重：检查 from_step 是否已存在于 to_step 的 connections 中
        to_step_obj = steps_by_num[to_step]
        existing = set(to_step_obj.connections) if to_step_obj.connections else set()
        if from_step in existing:
            return {"success": True, "message": f"关联已存在：步骤 #{from_step} → 步骤 #{to_step}"}

        store = Context.store_ref
        # 双向关联：统一使用参数化查询，不使用 f-string 拼接 WHERE 子句
        bid_val = branch_id if branch_id else ""
        # 更新 to_step：追加 from_step
        await store.db.execute(
            "UPDATE steps SET connections_json=json_set("
            "COALESCE(connections_json,'[]'),'$[#]',?) "
            "WHERE session_id=? AND number=? AND branch_id=?",
            (from_step, session_id, to_step, bid_val)
        )
        # 更新 from_step：追加 to_step（双向）
        await store.db.execute(
            "UPDATE steps SET connections_json=json_set("
            "COALESCE(connections_json,'[]'),'$[#]',?) "
            "WHERE session_id=? AND number=? AND branch_id=?",
            (to_step, session_id, from_step, bid_val)
        )
        await store.db.commit()
        return {
            "success": True,
            "message": f"已添加双向关联：步骤 #{from_step} ↔ 步骤 #{to_step}" + (f"（分支 {branch_id}）" if branch_id else ""),
            "from_step": from_step,
            "to_step": to_step,
            "branch_id": branch_id or "主链",
        }

    @mcp.tool(name="detect_contradictions")
    async def detect_contradictions(session_id: str) -> dict:
        """检测推理链中的自相矛盾（LLM深度扫描或启发式规则）。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        # 启发式检测
        contradictions = []
        steps = session.steps
        # 否定词前缀（在这些词后 2 字符内出现肯定/否定词时反转极性）
        negation_prefixes = ['不', '未', '非', '无', '没有', '并非', '无法', '难以']
        for i, a in enumerate(steps):
            for b in steps[i+1:]:
                # 检查完整内容（非仅前 100 字符），并考虑否定前缀
                pos_words = ['支持', '有利', '可行', '有效', '正确', '是', '增加', '提升', '改善']
                neg_words = ['反对', '不利', '不可行', '无效', '错误', '否', '减少', '降低', '恶化']
                a_pos = _match_with_negation(a.content, pos_words, negation_prefixes)
                b_neg = _match_with_negation(b.content, neg_words, negation_prefixes)
                if a_pos and b_neg:
                    contradictions.append({
                        "step_a": a.number, "step_b": b.number,
                        "detail": f"步骤{a.number}倾向肯定，步骤{b.number}倾向否定",
                    })
                    if len(contradictions) >= 5:
                        break
            if len(contradictions) >= 5:
                break
        # LLM 深度扫描
        llm_analysis = None
        if hasattr(Context.engine_ref, '_call'):
            steps_str = "\n".join(
                f"步骤{s.number}[{s.type}]: {s.content[:150]}" for s in steps
            )
            p = (f'检查以下推理步骤中是否存在逻辑矛盾或自相矛盾，返回JSON数组:\n'
                 f'[{{"step_a":1,"step_b":3,"detail":"矛盾描述"}}]\n'
                 f'若无矛盾返回[]:\n{steps_str}')
            try:
                r = await Context.engine_ref._call(p, max_tokens=400)
                llm_analysis = json.loads(r) if r else []
            except Exception:
                llm_analysis = None
        return {
            "heuristic_contradictions": contradictions,
            "llm_contradictions": llm_analysis,
            "total": len(contradictions) + (len(llm_analysis) if llm_analysis else 0),
        }

    @mcp.tool(name="extract_assumptions")
    async def extract_assumptions(session_id: str) -> dict:
        """LLM从推理步骤中提取隐含假设，追踪验证状态。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        if not hasattr(Context.engine_ref, '_call'):
            return {"error": "extract_assumptions 需要 LLM 引擎支持"}
        steps_str = "\n".join(
            f"步骤{s.number}[{s.type}]: {s.content[:200]}" for s in session.steps
        )
        p = (f'从以下推理过程中提取3-5个关键假设，返回JSON数组:\n'
             f'[{{"id":"A1","text":"假设内容","step_number":1,"confidence":0.8,'
             f'"critical":true,"verified":false}}]\n'
             f'critical=影响结论的关键假设。\n{steps_str}')
        r = await Context.engine_ref._call(p, max_tokens=600)
        try:
            data = json.loads(r)
            # 保存到数据库
            for item in data:
                from ..Core.Models import Assumption
                a = Assumption(**item)
                await Context.store_ref.add_assumption(a, session_id)
            return {"assumptions": data, "total": len(data)}
        except (json.JSONDecodeError, TypeError):
            return {"error": "LLM 返回格式异常，请重试"}

    @mcp.tool(name="update_tags")
    async def update_tags(session_id: str, tags: list[str]) -> dict:
        """更新会话标签（替换全部标签）。"""
        session = await Context.store_ref.get_session(session_id)
        if not session:
            return {"error": f"会话 {session_id} 不存在"}
        store = Context.store_ref
        await store.db.execute("DELETE FROM session_tags WHERE session_id=?", (session_id,))
        for t in tags:
            await store.db.execute("INSERT INTO session_tags(session_id,tag) VALUES(?,?)", (session_id, t))
        await store.db.commit()
        return {"session_id": session_id, "tags": tags, "message": "标签已更新"}
