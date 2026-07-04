# ============================================================================
# Handlers/Helpers.py 单元测试 — 辅助函数
# 路径: Tests/TestHandlersHelpers.py
# 原作者: 小逸 (Da Bai 生成)
# 仓库: https://github.com/LseKit/SequentialThinking
# ============================================================================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from datetime import datetime

from GitHubSrc.Core.Models import (
    ThinkingSession, ThinkingStep, LogicalIssue, QualityReport,
)
from GitHubSrc.Handlers.Helpers import (
    _trunc,
    _detect_issues,
    _calc_validity,
    _find_strong,
    _get_heuristic,
    _fallback_call,
)


# ── 测试夹具 ──

def _make_session(
    steps_data: list[tuple] = None
) -> ThinkingSession:
    """快速构建 ThinkingSession。steps_data: [(number, type, content, connections), ...]"""
    session = ThinkingSession(id="test-session", problem="测试问题")
    if steps_data:
        session.steps = []
        for n, t, c, conn in steps_data:
            session.steps.append(ThinkingStep(
                number=n, type=t, content=c,
                connections=conn,
                timestamp=datetime(2025, 1, n),
            ))
    return session


class TestTrunc:
    """测试 _trunc() 截断函数"""

    def test_short_string_unchanged(self):
        """短字符串不应被截断"""
        assert _trunc("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        """恰好等于限制长度不应截断"""
        s = "1234567890"
        assert _trunc(s, 10) == s

    def test_long_string_truncated(self):
        """超出限制的字符串应被截断并加 '...'"""
        result = _trunc("12345678901", 10)
        assert result == "1234567890..."
        assert len(result) == 13

    def test_empty_string(self):
        """空字符串保持为空"""
        assert _trunc("", 5) == ""

    def test_zero_limit(self):
        """限制为 0 时返回 '...'"""
        assert _trunc("test", 0) == "..."


class TestDetectIssues:
    """测试 _detect_issues() 逻辑问题检测"""

    def test_no_issues_in_clean_session(self):
        """正常会话不应检测到问题"""
        session = _make_session([
            (1, "analysis", "分析步骤", [2]),
            (2, "conclusion", "结论步骤", [1]),
        ])
        issues = _detect_issues(session, 1, 2)
        assert len(issues) == 0

    def test_detects_unsupported_conclusion(self):
        """没有连接的结论应被检测到"""
        session = _make_session([
            (1, "analysis", "分析", []),
            (2, "conclusion", "结论", []),
        ])
        issues = _detect_issues(session, 1, 2)
        unsupported = [i for i in issues if i.issue_type == "无支撑结论"]
        assert len(unsupported) == 1
        assert unsupported[0].step_number == 2

    def test_detects_unverified_hypothesis(self):
        """有假设但无验证步骤应被检测到"""
        session = _make_session([
            (1, "analysis", "分析", []),
            (2, "hypothesis", "假设", []),
        ])
        issues = _detect_issues(session, 1, 2)
        unverified = [i for i in issues if i.issue_type == "未验证假设"]
        assert len(unverified) == 1

    def test_hypothesis_with_verification_no_flag(self):
        """有假设且有验证步骤时不应标记"""
        session = _make_session([
            (1, "analysis", "分析", []),
            (2, "hypothesis", "假设", []),
            (3, "verification", "验证", []),
        ])
        issues = _detect_issues(session, 1, 3)
        unverified = [i for i in issues if i.issue_type == "未验证假设"]
        assert len(unverified) == 0

    def test_empty_session_no_issues(self):
        """空会话不产生问题"""
        session = _make_session([])
        issues = _detect_issues(session, 0, 0)
        assert len(issues) == 0

    def test_start_end_range(self):
        """start/end 范围正确限制检测范围"""
        session = _make_session([
            (1, "analysis", "分析", []),
            (2, "hypothesis", "假设", []),
        ])
        issues = _detect_issues(session, 1, 1)
        unverified = [i for i in issues if i.issue_type == "未验证假设"]
        assert len(unverified) == 0


class TestCalcValidity:
    """测试 _calc_validity() 有效性评分"""

    def test_no_issues_full_score(self):
        """没有问题应为满分"""
        assert _calc_validity([], 5) == 1.0

    def test_one_issue_reduces_score(self):
        """一个问题降低 0.15"""
        issues = [LogicalIssue(
            step_number=1, issue_type="test", description="test",
            severity="低", suggestion="",
        )]
        assert _calc_validity(issues, 5) == 0.85

    def test_zero_steps_returns_default(self):
        """0 步时返回默认 0.5"""
        assert _calc_validity([], 0) == 0.5

    def test_floor_at_zero(self):
        """评分不会低于 0"""
        many_issues = [
            LogicalIssue(
                step_number=i, issue_type="test", description="",
                severity="低", suggestion="",
            )
            for i in range(20)
        ]
        assert _calc_validity(many_issues, 1) == 0.0


class TestFindStrong:
    """测试 _find_strong() 优点识别"""

    def test_well_connected_steps(self):
        """步骤关联良好时识别"""
        session = _make_session([
            (1, "analysis", "步骤1", [2]),
            (2, "hypothesis", "步骤2", [1, 3]),
            (3, "verification", "步骤3", [2]),
        ])
        strong = _find_strong(session, 1, 3)
        assert "步骤关联良好" in strong

    def test_diverse_types(self):
        """使用多种类型时识别"""
        session = _make_session([
            (1, "analysis", "步骤1", []),
            (2, "hypothesis", "步骤2", []),
            (3, "verification", "步骤3", []),
        ])
        strong = _find_strong(session, 1, 3)
        assert "使用了多种推理类型" in strong

    def test_no_strengths_in_poor_session(self):
        """差劲的会话不应有优点"""
        session = _make_session([
            (1, "analysis", "步骤1", []),
            (2, "analysis", "步骤2", []),
        ])
        strong = _find_strong(session, 1, 2)
        assert len(strong) == 0


class TestGetHeuristic:
    """测试 _get_heuristic() 单例获取"""

    def test_returns_engine(self):
        """应返回 HeuristicEngine 实例"""
        he = _get_heuristic()
        assert he is not None
        assert hasattr(he, "is_llm")
        assert he.is_llm is False

    def test_singleton_same_instance(self):
        """多次调用返回同一个实例"""
        he1 = _get_heuristic()
        he2 = _get_heuristic()
        assert he1 is he2

    def test_evaluate_quality_works(self):
        """HeuristicEngine.evaluate_quality 真实可用"""
        session = _make_session([
            (1, "analysis", "步骤", []),
            (2, "conclusion", "结论", [1]),
        ])
        report = _get_heuristic().evaluate_quality(session)
        assert isinstance(report, QualityReport)
        assert 0.0 <= report.overall <= 1.0


class TestFallbackCall:
    """测试 _fallback_call() 降级调度"""

    def test_can_call_evaluate_quality(self):
        """通过 fallback 调用 evaluate_quality"""
        session = _make_session([
            (1, "analysis", "测试", []),
        ])
        result = _fallback_call("evaluate_quality", session)
        assert isinstance(result, QualityReport)

    def test_can_call_calculate_quality(self):
        """通过 fallback 调用 calculate_quality"""
        session = _make_session([
            (1, "analysis", "测试", []),
        ])
        result = _fallback_call("calculate_quality", session)
        assert isinstance(result, (int, float))

    def test_raises_on_invalid_method(self):
        """无效方法名应抛出 AttributeError"""
        with pytest.raises(AttributeError):
            _fallback_call("nonexistent_method")
