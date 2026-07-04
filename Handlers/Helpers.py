"""
Sequential Thinking MCP — 辅助函数
路径: Handlers/Helpers.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

提供通用辅助函数：
- _dispatch(): 统一处理 LLMEngine（异步）与 HeuristicEngine（同步）的调度
- _trunc(): 字符串截断
- _detect_issues(): 逻辑问题检测
- _calc_validity(): 有效性评分计算
- _find_strong(): 识别推理链优点
"""
from ..Core.Models import (
    ThinkingSession, ThinkingStep, LogicalIssue,
    QualityReport, BiasResult, ConfidenceMeta, MergeResult,
    SessionCompare, MAX_QUALITY_STEPS,
)
from ..Core import Context


async def _dispatch(method_name: str, *args, **kwargs):
    """统一调度：LLM 引擎走异步 await，启发式引擎走同步调用
    
    当 LLM 引擎调用失败时，自动降级到 HeuristicEngine 的对应方法。
    确保即使 LLM API 不可用，MCP 工具仍能返回结果。
    """
    engine = Context.engine_ref
    method = getattr(engine, method_name)
    if engine.is_llm:
        try:
            return await method(*args, **kwargs)
        except Exception as e:
            # LLM 调用失败，降级到启发式引擎（使用模块级单例，避免重复创建）
            from ..Utils.Logger import setup_logger
            log = setup_logger("helpers")
            log.warning(f"LLM 调用 {method_name} 失败: {e}，降级到启发式引擎")
            return _fallback_call(method_name, *args, **kwargs)
    return method(*args, **kwargs)


# 模块级 HeuristicEngine 单例（避免 _dispatch 降级时重复创建实例）
_heuristic_singleton = None


def _get_heuristic():
    """获取模块级 HeuristicEngine 单例"""
    global _heuristic_singleton
    if _heuristic_singleton is None:
        from ..Engine.Engine import HeuristicEngine
        _heuristic_singleton = HeuristicEngine()
    return _heuristic_singleton


def _fallback_call(method_name, *args, **kwargs):
    """在 HeuristicEngine 单例上调用指定方法"""
    heuristic = _get_heuristic()
    method = getattr(heuristic, method_name)
    return method(*args, **kwargs)


def _trunc(s: str, n: int) -> str:
    """截断字符串到 n 字符，超出加 "..." """
    return s if len(s) <= n else s[:n] + "..."


def _detect_issues(session: ThinkingSession, start: int, end: int) -> list[LogicalIssue]:
    """检测推理链中的逻辑问题：无支撑结论、未验证假设"""
    issues = []
    steps_slice = session.steps[max(0, start - 1):end]
    for s in steps_slice:
        if s.type == "conclusion" and not s.connections:
            issues.append(LogicalIssue(
                step_number=s.number, issue_type="无支撑结论",
                description="结论缺乏明确的支撑证据", severity="中",
                suggestion="将此结论与之前的分析或验证步骤关联",
            ))
    has_hyp = any(s.type == "hypothesis" for s in steps_slice)
    has_ver = any(s.type == "verification" for s in steps_slice)
    if has_hyp and not has_ver:
        issues.append(LogicalIssue(
            step_number=0, issue_type="未验证假设",
            description="存在假设但缺乏验证步骤", severity="高",
            suggestion="添加验证步骤来检验假设",
        ))
    return issues


def _calc_validity(issues: list, steps: int) -> float:
    """根据问题数计算有效性评分"""
    if steps == 0:
        return 0.5
    return max(0.0, 1.0 - len(issues) * 0.15)


def _find_strong(session: ThinkingSession, start: int, end: int) -> list[str]:
    """识别推理链中的优点：良好关联、多样类型"""
    strong = []
    steps_slice = session.steps[max(0, start - 1):end]
    conn_count = sum(1 for s in steps_slice if s.connections)
    if conn_count > (end - start + 1) // 2:
        strong.append("步骤关联良好")
    types = set(s.type for s in steps_slice)
    if len(types) >= 3:
        strong.append("使用了多种推理类型")
    return strong


async def _calc_qs(session):
    """计算会话质量分"""
    return await _dispatch("calculate_quality", session)


async def _calc_conf(step, session):
    """计算步骤置信度"""
    return await _dispatch("analyze_confidence", step, session)


async def _calc_sugs(session):
    """生成下一步建议"""
    return await _dispatch("suggest_next", session)


async def _eval_quality(session):
    """5 维质量评估"""
    return await _dispatch("evaluate_quality", session)


async def _detect_bias(session):
    """认知偏见检测"""
    return await _dispatch("detect_biases", session)


async def _compare(a, b):
    """两会话对比"""
    return await _dispatch("compare_sessions", a, b)


async def _suggest(session):
    """智能推荐"""
    return await _dispatch("suggest_next", session)


async def _optimize(query):
    """优化问题表述"""
    return await _dispatch("optimize_query", query)


async def _gen_summary(session, fmt):
    """生成会话摘要"""
    return await _dispatch("generate_summary", session, fmt)


async def _merge(main, branches):
    """合并分支洞察"""
    return await _dispatch("merge_insights", main, branches)


async def _cross_validate_quality(session, llm_result: QualityReport = None) -> dict:
    """LLM↔Heuristic 交叉验证：两个引擎分别计算质量分，分歧>0.2时标记。
    
    Args:
        session: 会话对象
        llm_result: 已由 LLM 计算的质量报告（避免重复调用 LLM API）
    """
    engine = Context.engine_ref
    if not engine.is_llm:
        return {"method": "heuristic_only", "note": "当前为启发式引擎，无需交叉验证"}
    # 使用传入的 LLM 结果，不再重新调用 LLM
    llm_qr = llm_result if llm_result else await _eval_quality(session)
    # 启发式评估
    from ..Engine.Engine import HeuristicEngine
    he = HeuristicEngine()
    he_qr = he.evaluate_quality(session)
    # 计算分歧
    diff = abs(llm_qr.overall - he_qr.overall)
    return {
        "llm_quality": {
            "overall": llm_qr.overall, "coherence": llm_qr.coherence,
            "completeness": llm_qr.completeness,
        },
        "heuristic_quality": {
            "overall": he_qr.overall, "coherence": he_qr.coherence,
            "completeness": he_qr.completeness,
        },
        "divergence": round(diff, 4),
        "needs_review": diff > 0.2,
        "recommendation": (
            "LLM 与启发式引擎评估结果差异较大(>0.2)，建议人工审查"
            if diff > 0.2 else "两引擎评估结果一致"
        ),
    }
