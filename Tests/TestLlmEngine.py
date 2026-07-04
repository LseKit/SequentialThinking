# ============================================================================
# Engine/Engine.py — LLMEngine 单元测试（mock API，全异步）
# 路径: Tests/TestLlmEngine.py
# 原作者: 小逸 (Da Bai 生成)
# 仓库: https://github.com/LseKit/SequentialThinking
# ============================================================================
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from GitHubSrc.Core.Models import (
    ThinkingSession, ThinkingStep,
    QualityReport, BiasResult, ConfidenceMeta, ComplexityEstimate,
    SessionCompare, MergeResult, ThinkingPattern,
)
from GitHubSrc.Engine.Engine import LLMEngine, HeuristicEngine


# ══════════════════════════════════════════════
# 辅助
# ══════════════════════════════════════════════

def _mk_rsp(content: str) -> dict:
    """构建模拟 LLM API 响应"""
    return {"choices": [{"message": {"content": content}}]}


def _mk_ses(steps_data=None, **kw) -> ThinkingSession:
    """快速构建 ThinkingSession"""
    now = datetime.now(timezone.utc)
    session = ThinkingSession(
        id=kw.get("id", "test-session"),
        problem=kw.get("problem", "测试问题"),
        quality_score=kw.get("quality_score", 0.5),
        status=kw.get("status", "active"),
        created=now, last_modified=now,
    )
    if steps_data:
        session.steps = [
            ThinkingStep(number=n, type=t, content=c, connections=cn, timestamp=now)
            for n, t, c, cn in steps_data
        ]
    return session


# ══════════════════════════════════════════════
# 夹具
# ══════════════════════════════════════════════

@pytest.fixture
def mp():
    """mock httpx.AsyncClient.post"""
    m = AsyncMock()
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = _mk_rsp("{}")
    m.return_value = r
    return m


@pytest.fixture
def eng(mp):
    """创建 mock LLMEngine"""
    with patch("httpx.AsyncClient.post", mp):
        e = LLMEngine(api_key="k", api_base="http://m", model="m")
        yield e


class TestIdentity:
    """引擎识别"""

    def test_is_llm(self, eng):
        assert eng.is_llm is True

    def test_heuristic_is_not(self):
        assert HeuristicEngine().is_llm is False


# ══════════════════════════════════════════════
# 文本生成
# ══════════════════════════════════════════════

class TestGenAnalysis:
    """generate_initial_analysis()"""

    async def test_str(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("80字分析")
        r = await eng.generate_initial_analysis("问题")
        assert isinstance(r, str)
        assert len(r) > 0

    async def test_empty(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("")
        r = await eng.generate_initial_analysis("测试")
        assert isinstance(r, str)


class TestOptimize:
    """optimize_query()"""

    async def test_str(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("优化后")
        r = await eng.optimize_query("原始")
        assert isinstance(r, str)

    async def test_fallback(self, eng, mp):
        mp.return_value.json.side_effect = json.JSONDecodeError("bad", "x", 0)
        r = await eng.optimize_query("原始")
        assert r == "原始"


class TestSummary:
    """generate_summary()"""

    async def test_str(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("摘要")
        s = _mk_ses([(1, "analysis", "A", []), (2, "conclusion", "C", [1])])
        r = await eng.generate_summary(s, "linear")
        assert isinstance(r, str)

    async def test_none(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("空")
        r = await eng.generate_summary(None, "linear")
        assert isinstance(r, str)


# ══════════════════════════════════════════════
# 数值解析
# ══════════════════════════════════════════════

class TestCalcQuality:
    """calculate_quality()"""

    async def test_valid(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("0.85")
        s = _mk_ses([(1, "analysis", "T", [])])
        score = await eng.calculate_quality(s)
        assert 0.0 <= score <= 1.0

    async def test_clamped(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("1.5")
        s = _mk_ses([(1, "analysis", "T", [])])
        score = await eng.calculate_quality(s)
        assert 0.0 <= score <= 1.0

    async def test_bad(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("x")
        s = _mk_ses([(1, "analysis", "T", [])])
        score = await eng.calculate_quality(s)
        assert score == 0.5

    async def test_none(self, eng):
        score = await eng.calculate_quality(None)
        assert score == 0.5


# ══════════════════════════════════════════════
# JSON 结构化解析
# ══════════════════════════════════════════════

class TestEvalQuality:
    """evaluate_quality()"""

    async def test_report(self, eng, mp):
        d = {"overall":0.8,"coherence":0.85,"completeness":0.75,"rigor":0.8,
             "novelty":0.7,"actionable":0.9,"strengths":["好"],"weaknesses":["缺"]}
        mp.return_value.json.return_value = _mk_rsp(json.dumps(d))
        s = _mk_ses([(1,"analysis","T",[])])
        r = await eng.evaluate_quality(s)
        assert isinstance(r, QualityReport)
        assert r.overall == 0.8

    async def test_bad_json(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("bad")
        s = _mk_ses([(1,"analysis","T",[])])
        r = await eng.evaluate_quality(s)
        assert isinstance(r, QualityReport)


class TestBiases:
    """detect_biases()"""

    async def test_list(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp(
            json.dumps([{"name":"确认偏见","severity":"中"}])
        )
        s = _mk_ses([(1,"analysis","T",[])])
        r = await eng.detect_biases(s)
        assert isinstance(r, list)
        assert len(r) >= 1

    async def test_bad(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("bad")
        r = await eng.detect_biases(None)
        assert isinstance(r, list)


class TestConfidence:
    """analyze_confidence()"""

    async def test_meta(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp(
            json.dumps({"score":0.85,"rationale":"充分","risks":["边界"]})
        )
        step = ThinkingStep(number=1,type="analysis",content="T")
        s = _mk_ses([(1,"analysis","T",[])])
        r = await eng.analyze_confidence(step, s)
        assert isinstance(r, ConfidenceMeta)
        assert 0.0 <= r.score <= 1.0

    async def test_none(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp(
            json.dumps({"score":0.0,"rationale":"","risks":[]})
        )
        r = await eng.analyze_confidence(None, None)
        assert isinstance(r, ConfidenceMeta)


class TestComplexity:
    """estimate_complexity()"""

    async def test_est(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp(
            json.dumps({"level":"hard","estimated_steps":20,"suggested_template":"t"})
        )
        r = await eng.estimate_complexity("复杂")
        assert isinstance(r, ComplexityEstimate)
        assert r.level in ("easy","medium","hard")

    async def test_bad(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("bad")
        r = await eng.estimate_complexity("问题")
        assert isinstance(r, ComplexityEstimate)


class TestCompare:
    """compare_sessions()"""

    async def test_cmp(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp(
            json.dumps({"shared_assumptions":[],"divergent_conclusions":[],
                        "similarity":0.6,"recommendation":"R"})
        )
        a = _mk_ses(id="a",problem="A")
        b = _mk_ses(id="b",problem="B")
        r = await eng.compare_sessions(a, b)
        assert isinstance(r, SessionCompare)

    async def test_none(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp(
            json.dumps({"shared_assumptions":[],"divergent_conclusions":[],
                        "similarity":0.0,"recommendation":""})
        )
        r = await eng.compare_sessions(None, None)
        assert isinstance(r, SessionCompare)


class TestSuggest:
    """suggest_next()"""

    async def test_list(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp(json.dumps(["A","B","C"]))
        s = _mk_ses([(1,"analysis","T",[])])
        r = await eng.suggest_next(s)
        assert isinstance(r, list)
        assert len(r) >= 1


class TestMerge:
    """merge_insights()"""

    async def test_result(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp(
            json.dumps({"synthesis":"S","conflicts":["C"],"confidence":0.75,"strengths":["S"]})
        )
        r = await eng.merge_insights(main=["A"], branches={"b1": ["C"]})
        assert isinstance(r, MergeResult)


class TestPatterns:
    """detect_patterns()"""

    async def test_list(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp(
            json.dumps([{"name":"收敛","frequency":3,"confidence":0.8,"description":"D"}])
        )
        r = await eng.detect_patterns({})
        assert isinstance(r, list)

    async def test_empty(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("[]")
        r = await eng.detect_patterns({})
        assert isinstance(r, list)


class TestMoa:
    """moa_analyze()"""

    async def test_dict(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("结果")
        r = await eng.moa_analyze(problem="P", rounds=2)
        assert isinstance(r, dict)
        assert "total_rounds" in r

    async def test_one_round(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("单轮")
        r = await eng.moa_analyze(problem="P", rounds=1)
        assert r.get("total_rounds") == 1

    async def test_consensus(self, eng, mp):
        mp.return_value.json.return_value = _mk_rsp("一致")
        r = await eng.moa_analyze(problem="P", rounds=3)
        assert "consensus_ratio" in r


class TestErrors:
    """错误处理"""

    async def test_http_error(self, eng, mp):
        mp.side_effect = Exception("Connection refused")
        s = _mk_ses([(1,"analysis","T",[])])
        score = await eng.calculate_quality(s)
        assert 0.0 <= score <= 1.0


# ══════════════════════════════════════════════
# 多模型 MoA 测试（新增 — v1.3.0）
# ══════════════════════════════════════════════

@pytest.fixture
def eng_dual(mp):
    with patch("httpx.AsyncClient.post", mp):
        e = LLMEngine(
            api_key="k1", api_base="http://m1", model="m1",
            api_key2="k2", api_base2="http://m2", model2="m2",
            selector=3, moa_rounds=2, mode="self-moa",
        )
        yield e


@pytest.fixture
def eng_iter(mp):
    with patch("httpx.AsyncClient.post", mp):
        e = LLMEngine(
            api_key="k1", api_base="http://m1", model="m1",
            api_key2="k2", api_base2="http://m2", model2="m2",
            selector=3, moa_rounds=2, mode="iterative",
        )
        yield e


@pytest.fixture
def eng_off(mp):
    with patch("httpx.AsyncClient.post", mp):
        e = LLMEngine(
            api_key="k1", api_base="http://m1", model="m1",
            selector=0, moa_rounds=2, mode="self-moa",
        )
        yield e


class TestMoaSelector:
    async def test_selector_off(self, eng_off):
        r = await eng_off.moa_analyze(problem="P")
        assert isinstance(r, dict)
        assert "error" in r


class TestMoaDual:
    async def test_dual_rounds(self, eng_dual, mp):
        mp.return_value.json.return_value = _mk_rsp("双模型结果")
        r = await eng_dual.moa_analyze(problem="P", rounds=2)
        assert len(r.get("all_perspectives", [])) == 4

    async def test_dual_consensus(self, eng_dual, mp):
        mp.return_value.json.return_value = _mk_rsp("一致结果")
        r = await eng_dual.moa_analyze(problem="P", rounds=1)
        assert "consensus_ratio" in r
        assert len(r.get("all_perspectives", [])) == 2

    async def test_no_key2_fallback(self, mp):
        with patch("httpx.AsyncClient.post", mp):
            e = LLMEngine(api_key="k1", api_base="http://m1", model="m1",
                          selector=3, moa_rounds=2, mode="self-moa")
        mp.return_value.json.return_value = _mk_rsp("单模型")
        r = await e.moa_analyze(problem="P", rounds=2)
        assert len(r.get("all_perspectives", [])) == 2


class TestIterativeMoa:
    async def test_basic(self, eng_iter, mp):
        mp.return_value.json.return_value = _mk_rsp("迭代结果")
        r = await eng_iter.moa_analyze(problem="P", rounds=2)
        assert len(r.get("all_perspectives", [])) == 4

    async def test_no_key2_fallback(self, mp):
        with patch("httpx.AsyncClient.post", mp):
            e = LLMEngine(api_key="k1", api_base="http://m1", model="m1",
                          selector=3, moa_rounds=2, mode="iterative")
        mp.return_value.json.return_value = _mk_rsp("单模型")
        r = await e.moa_analyze(problem="P", rounds=2)
        assert len(r.get("all_perspectives", [])) == 2


class TestMakeTemps:
    def test_3_rounds(self):
        t = LLMEngine._make_temps(3)
        assert len(t) == 3
        assert t == [0.3, 0.7, 1.0]

    def test_10_rounds(self):
        t = LLMEngine._make_temps(10)
        assert len(t) == 10
        assert t[0] == 0.1
        assert 0.9 <= t[-1] <= 1.0

    def test_20_rounds(self):
        t = LLMEngine._make_temps(20)
        assert len(t) == 20
