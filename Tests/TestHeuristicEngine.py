"""
Sequential Thinking MCP — HeuristicEngine 单元测试
路径: Tests/TestHeuristicEngine.py
原作者: 小逸
官方仓库: https://github.com/LseKit/SequentialThinking

测试覆盖: HeuristicEngine 全部 13 个公共方法
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from datetime import datetime, timezone
from GitHubSrc.Core.Models import (
    ThinkingSession, ThinkingStep, Branch, QualityReport,
    BiasResult, ConfidenceMeta, MergeResult, SessionCompare,
    ComplexityEstimate, ThinkingPattern,
)
from GitHubSrc.Engine.Engine import HeuristicEngine


class TestHeuristicEngine:
    """HeuristicEngine 13 个方法的完整测试"""

    @pytest.fixture
    def engine(self):
        return HeuristicEngine()

    @pytest.fixture
    def empty_session(self):
        return ThinkingSession(id="test-1", problem="测试问题")

    @pytest.fixture
    def basic_session(self):
        """包含 4 种类型 + 关联的完整会话"""
        s = ThinkingSession(id="test-2", problem="如何提升系统性能")
        s.steps = [
            ThinkingStep(number=1, type="analysis", content="当前系统CPU使用率80%，内存使用率60%"),
            ThinkingStep(number=2, type="hypothesis", content="瓶颈可能在数据库查询", connections=[1]),
            ThinkingStep(number=3, type="verification", content="EXPLAIN分析显示全表扫描", connections=[2]),
            ThinkingStep(number=4, type="conclusion", content="建议添加索引idx_users_created_at", connections=[3]),
        ]
        return s

    # ── 1. is_llm ──
    def test_is_llm_false(self, engine):
        assert engine.is_llm is False

    # ── 2. generate_initial_analysis ──
    def test_generate_analysis_has_keywords(self, engine):
        result = engine.generate_initial_analysis("为什么系统响应慢")
        assert "系统响应慢" in result
        assert "关键词" in result or "推荐模板" in result

    def test_generate_analysis_empty(self, engine):
        result = engine.generate_initial_analysis("")
        assert len(result) > 0

    # ── 3. calculate_quality ──
    def test_calculate_quality_empty(self, engine, empty_session):
        assert engine.calculate_quality(empty_session) == 0.5

    def test_calculate_quality_full_session(self, engine, basic_session):
        score = engine.calculate_quality(basic_session)
        assert 0 < score <= 1.0
        # 再加一步，分数应增长
        basic_session.steps.append(
            ThinkingStep(number=5, type="analysis", content="网络延迟正常", connections=[1])
        )
        new_score = engine.calculate_quality(basic_session)
        assert new_score >= score

    # ── 4. evaluate_quality ──
    def test_evaluate_quality_returns_5_dimensions(self, engine, basic_session):
        qr = engine.evaluate_quality(basic_session)
        assert isinstance(qr, QualityReport)
        assert 0 <= qr.coherence <= 1
        assert 0 <= qr.completeness <= 1
        assert 0 <= qr.rigor <= 1
        assert 0 <= qr.novelty <= 1
        assert 0 <= qr.actionable <= 1

    def test_evaluate_quality_empty(self, engine):
        qr = engine.evaluate_quality(None)
        assert qr.overall == 0.5

    # ── 5. detect_biases ──
    def test_detect_biases_empty(self, engine):
        assert engine.detect_biases(None) == []

    def test_detect_biases_unverified_hypothesis(self, engine):
        """有假设无验证 → 应检测出未验证假设偏见"""
        s = ThinkingSession(id="b-1", problem="测试")
        s.steps = [
            ThinkingStep(number=1, type="analysis", content="分析"),
            ThinkingStep(number=2, type="hypothesis", content="假设X成立"),
        ]
        biases = engine.detect_biases(s)
        names = [b.name for b in biases]
        assert "未验证假设" in names

    def test_detect_biases_confirmation(self, engine):
        """所有结论都有支撑但无反例 → 确认偏见"""
        s = ThinkingSession(id="b-2", problem="测试")
        s.steps = [
            ThinkingStep(number=1, type="conclusion", content="结论A", connections=[2]),
            ThinkingStep(number=2, type="conclusion", content="结论B", connections=[1]),
        ]
        biases = engine.detect_biases(s)
        names = [b.name for b in biases]
        assert "确认偏见" in names or "过度自信" in names

    # ── 6. estimate_complexity ──
    def test_estimate_easy(self, engine):
        c = engine.estimate_complexity("今天是星期几")
        assert c.level == "easy"
        assert c.estimated_steps > 0

    def test_estimate_hard(self, engine):
        c = engine.estimate_complexity("如何设计一个分布式高可用微服务架构系统同时兼顾性能和安全")
        assert c.level in ("medium", "hard")
        assert c.estimated_steps >= 10

    # ── 7. analyze_confidence ──
    def test_confidence_no_step(self, engine):
        cm = engine.analyze_confidence(None)
        assert cm.score == 0.5

    def test_confidence_with_connections(self, engine, basic_session):
        step = basic_session.steps[3]  # conclusion with connections
        cm = engine.analyze_confidence(step, basic_session)
        assert cm.score > 0.5
        assert len(cm.rationale) > 0

    # ── 8. compare_sessions ──
    def test_compare_none(self, engine):
        c = engine.compare_sessions(None, None)
        assert c.similarity == 0.0

    def test_compare_similar(self, engine, basic_session):
        c = engine.compare_sessions(basic_session, basic_session)
        assert c.similarity > 0.5  # 相同会话相似度应高

    # ── 9. suggest_next ──
    def test_suggest_empty(self, engine):
        sugs = engine.suggest_next(None)
        assert len(sugs) > 0

    def test_suggest_after_analysis(self, engine):
        s = ThinkingSession(id="s-1", problem="测试")
        s.steps = [ThinkingStep(number=1, type="analysis", content="分析了问题")]
        sugs = engine.suggest_next(s)
        assert any("假设" in sug or "hypothesis" in sug.lower() for sug in sugs)

    # ── 10. optimize_query ──
    def test_optimize_strips_prefix(self, engine):
        result = engine.optimize_query("请问为什么系统变慢了")
        assert not result.startswith("请问")

    def test_optimize_adds_question_mark(self, engine):
        result = engine.optimize_query("为什么系统变慢")
        assert result.endswith("？")

    # ── 11. merge_insights ──
    def test_merge_simple(self, engine):
        result = engine.merge_insights(["结论1: A方案最优"], {"b1": ["分支结论: B方案也可行"]})
        assert isinstance(result, MergeResult)
        assert "A方案" in result.synthesis or "B方案" in result.synthesis

    # ── 12. generate_summary ──
    def test_summary_linear(self, engine, basic_session):
        summary = engine.generate_summary(basic_session, "linear")
        assert len(summary) > 0

    def test_summary_stats(self, engine, basic_session):
        summary = engine.generate_summary(basic_session, "stats")
        assert "总步骤" in summary

    def test_summary_key_points(self, engine, basic_session):
        summary = engine.generate_summary(basic_session, "key_points")
        assert len(summary) > 0

    # ── 13. detect_patterns ──
    def test_detect_patterns_empty(self, engine):
        assert engine.detect_patterns(None) == []
        assert engine.detect_patterns({}) == []

    def test_detect_patterns_with_data(self, engine):
        sessions = {}
        for i in range(3):
            s = ThinkingSession(id=f"p-{i}", problem=f"测试问题{i}")
            s.steps = [ThinkingStep(number=1, type="analysis", content="分析")]
            s.context = {"template_name": "根因分析"}
            sessions[s.id] = s
        patterns = engine.detect_patterns(sessions)
        assert len(patterns) > 0
        assert any("根因分析" in p.name for p in patterns)
