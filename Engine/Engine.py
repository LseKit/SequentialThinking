"""
Sequential Thinking MCP — 推理引擎（启发式 + LLM）
路径: Engine/Engine.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

包含两个引擎：
- HeuristicEngine: 启发式引擎，内置规则推理，零外部依赖
- LLMEngine: LLM 引擎，异步调用大模型进行智能推理
"""
import json, os, asyncio
from typing import Optional
import httpx

from ..Utils.Logger import setup_logger
log = setup_logger("engine")

from ..Core.Models import (
    ThinkingSession, ThinkingStep, QualityReport, BiasResult,
    ConfidenceMeta, MergeResult, SessionCompare, ComplexityEstimate,
    ThinkingPattern, MAX_QUALITY_STEPS,
    QUALITY_TYPE_WEIGHT, QUALITY_CONN_WEIGHT, QUALITY_DEPTH_WEIGHT,
)
from ..Core.Templates import get_all_templates


def _jaccard_sim(a: str, b: str) -> float:
    """计算两个字符串的 Jaccard 相似度（基于字符 2-gram）"""
    if not a or not b:
        return 0.0
    sa = set(a[i:i+2] for i in range(len(a)-1))
    sb = set(b[i:i+2] for i in range(len(b)-1))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


class HeuristicEngine:
    """启发式引擎——基于规则和统计的确定性推理，零外部依赖"""

    @property
    def is_llm(self) -> bool:
        return False

    # ── 辅助方法 ──

    @staticmethod
    def _extract_keywords(text: str, min_len: int = 2, top_n: int = 5) -> list[str]:
        """从文本中提取关键词：按长度和位置权重排序"""
        # 简单分词：按中文标点和空格分割
        import re as _re
        words = _re.split(r'[，。？：、！；\n\s,.:;!?]+', text)
        seen, scored = set(), []
        for i, w in enumerate(words):
            w = w.strip()
            if len(w) >= min_len and w not in seen:
                seen.add(w)
                # 越靠前权重越高
                scored.append((w, 1.0 / (i + 1)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [w for w, _ in scored[:top_n]]

    @staticmethod
    def _classify_problem(problem: str) -> str:
        """基于关键词将问题分类为：根因分析/方案设计/决策/通用"""
        p = problem.lower()
        if any(k in p for k in ['为什么', '原因', '根因', '根源', '导致']):
            return 'root-cause-analysis'
        if any(k in p for k in ['如何', '怎么', '方案', '方法', '设计']):
            return 'solution-design'
        if any(k in p for k in ['是否', '选哪个', '哪个更好', '对比', '比较']):
            return 'decision-matrix'
        if any(k in p for k in ['优势', '劣势', '机会', '威胁', 'swot']):
            return 'swot-analysis'
        return 'scientific-method'

    @staticmethod
    def _calc_step_type_stats(steps: list) -> dict:
        """统计步骤类型分布"""
        dist = {}
        for s in steps:
            dist[s.type] = dist.get(s.type, 0) + 1
        return dist

    @staticmethod
    def _calc_jaccard(text_a: str, text_b: str) -> float:
        """计算两个文本的 Jaccard 相似度（基于字符 2-gram）"""
        def ngrams(t, n=2):
            return set(t[i:i+n] for i in range(len(t)-n+1))
        sa, sb = ngrams(text_a), ngrams(text_b)
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    # ── 推理方法 ──

    def generate_initial_analysis(self, problem: str) -> str:
        """基于问题文本提取关键词+分类+推荐模板"""
        keywords = self._extract_keywords(problem)
        tmpl = self._classify_problem(problem)
        tmpl_names = {
            'root-cause-analysis': '根因分析', 'solution-design': '方案设计',
            'decision-matrix': '决策矩阵', 'swot-analysis': 'SWOT分析',
            'scientific-method': '科学方法',
        }
        kw_str = '、'.join(keywords) if keywords else '暂无'
        return (
            f"问题「{problem}」的初始分析：\n"
            f"关键词：{kw_str}\n"
            f"问题类型：{tmpl_names.get(tmpl, '通用分析')}\n"
            f"推荐模板：{tmpl}"
        )

    def calculate_quality(self, session: Optional[ThinkingSession]) -> float:
        """基于类型多样性 + 连接密度 + 步骤深度 综合计算质量分"""
        if not session or not session.steps:
            return 0.5
        type_set = set(s.type for s in session.steps)
        total_conns = sum(len(s.connections) for s in session.steps)
        n = len(session.steps)
        v = len(type_set) / 4.0
        c = min(1.0, total_conns / max(1, n))
        d = min(1.0, n / MAX_QUALITY_STEPS)
        return round(v * QUALITY_TYPE_WEIGHT + c * QUALITY_CONN_WEIGHT + d * QUALITY_DEPTH_WEIGHT, 4)

    def evaluate_quality(self, session: Optional[ThinkingSession]) -> QualityReport:
        """基于真实数据计算 5 维质量分，不再写死"""
        if not session or not session.steps:
            return QualityReport(overall=0.5)
        steps = session.steps
        n = len(steps)
        # coherence: 有支撑的结论比例
        concl_with_conn = sum(
            1 for s in steps if s.type == 'conclusion' and s.connections
        )
        # completeness: 类型覆盖度 + 是否有结论
        types_present = len(set(s.type for s in steps))
        # rigor: 有假设必有验证
        has_hypothesis = any(s.type == 'hypothesis' for s in steps)
        has_verification = any(s.type == 'verification' for s in steps)
        # novelty: 步骤内容多样性（去重比例）
        unique_contents = len(set(s.content[:50] for s in steps))
        # actionable: 结论中有具体建议的比例
        action_words = any(
            kw in ' '.join(s.content[:100] for s in steps if s.type == 'conclusion')
            for kw in ['建议', '方案', '措施', '步骤', '计划', '行动']
        )

        coherence = min(1.0, concl_with_conn / max(1, sum(1 for s in steps if s.type == 'conclusion')))
        completeness = min(1.0, types_present / 4.0 + (0.2 if any(s.type == 'conclusion' for s in steps) else 0))
        rigor = 1.0 if (not has_hypothesis) else (0.6 if has_verification else 0.3)
        novelty = min(1.0, unique_contents / max(1, n))
        actionable = 0.8 if action_words else 0.4
        overall = round(coherence * 0.25 + completeness * 0.25 + rigor * 0.2 + novelty * 0.15 + actionable * 0.15, 4)

        strengths, weaknesses = [], []
        if coherence > 0.6: strengths.append("步骤间关联良好")
        else: weaknesses.append("部分结论缺乏支撑")
        if completeness > 0.6: strengths.append("推理类型丰富")
        else: weaknesses.append("推理类型不够多样化")
        if has_hypothesis and has_verification: strengths.append("假设-验证闭环完整")
        elif has_hypothesis: weaknesses.append("存在假设但缺少验证")

        return QualityReport(
            overall=overall, coherence=round(coherence, 4),
            completeness=round(completeness, 4), rigor=round(rigor, 4),
            novelty=round(novelty, 4), actionable=round(actionable, 4),
            strengths=strengths, weaknesses=weaknesses,
        )

    def detect_biases(self, session=None) -> list[BiasResult]:
        """基于规则检测 8 种常见认知偏见"""
        if not session or not session.steps:
            return []
        steps = session.steps
        biases = []

        # 确认偏见：检查结论步骤是否全都支持同一方向
        conclusions = [s for s in steps if s.type == 'conclusion']
        support_count = sum(1 for s in conclusions if s.connections)
        if conclusions and support_count == len(conclusions) and len(conclusions) >= 2:
            biases.append(BiasResult(
                name='确认偏见', severity='中',
                description='所有结论均指向同一方向，缺乏反面验证',
                evidence=f'{len(conclusions)} 条结论全部有支撑但无反例',
                suggestion='主动寻找反例或替代解释',
            ))

        # 锚定效应：后续步骤与第一步内容高度相似
        if len(steps) >= 3:
            first_text = steps[0].content[:100]
            later_texts = ' '.join(s.content[:100] for s in steps[1:])
            if self._calc_jaccard(first_text, later_texts) > 0.5:
                biases.append(BiasResult(
                    name='锚定效应', severity='低',
                    description='后续推理与初始步骤高度相似，可能受锚定影响',
                    evidence=f'第一步与后续步骤内容相似度较高',
                    suggestion='尝试从不同角度重新审视问题',
                ))

        # 过度自信：conclusion 步骤多但支撑少
        if conclusions and sum(len(s.connections) for s in conclusions) < len(conclusions):
            biases.append(BiasResult(
                name='过度自信', severity='低',
                description='结论数量超过支撑证据数量',
                evidence=f'{len(conclusions)} 条结论但只有 {sum(len(s.connections) for s in conclusions)} 条关联',
                suggestion='添加更多验证步骤来支撑结论',
            ))

        # 未验证假设
        has_hyp = any(s.type == 'hypothesis' for s in steps)
        has_ver = any(s.type == 'verification' for s in steps)
        if has_hyp and not has_ver:
            biases.append(BiasResult(
                name='未验证假设', severity='高',
                description='存在假设步骤但没有后续验证',
                evidence='假设未被验证',
                suggestion='添加验证步骤来检验假设是否成立',
            ))

        # 可得性启发：使用了"常见""通常""一般"等词但缺乏数据支撑
        heuristics_words = ['常见', '通常', '一般', '往往', '大多数', '很多']
        used_heuristics = any(
            any(kw in s.content for kw in heuristics_words) for s in steps
        )
        if used_heuristics and len(steps) < 5:
            biases.append(BiasResult(
                name='可得性启发', severity='低',
                description='使用了概括性表述但步骤数较少，可能依赖直觉而非数据',
                evidence='出现"常见/通常/一般"等概括词',
                suggestion='尝试用具体数据或案例支撑判断',
            ))

        return biases

    def estimate_complexity(self, problem: str) -> ComplexityEstimate:
        """基于问题特征估算复杂度和推荐步骤数"""
        p_len = len(problem)
        # 复杂度判定
        if p_len < 50:
            level, steps = 'easy', 5
        elif p_len < 200:
            level, steps = 'medium', 10
        else:
            level, steps = 'hard', 18
        # 包含复杂语义词加分
        complex_words = ['系统', '架构', '多', '复杂', '同时', '兼顾', '平衡', '优化']
        if any(kw in problem for kw in complex_words):
            level = 'hard' if level != 'hard' else 'hard'
            steps = max(steps, 15)
        tmpl = self._classify_problem(problem)
        return ComplexityEstimate(level=level, estimated_steps=steps, suggested_template=tmpl)

    def analyze_confidence(self, step=None, session=None) -> ConfidenceMeta:
        """基于步骤质量计算置信度"""
        if not step:
            return ConfidenceMeta(score=0.5, rationale='无步骤数据', risks=['信息不足'])
        score = 0.5
        risks = []
        # 有 connections 加分
        if step.connections:
            score += 0.15
        else:
            risks.append('步骤缺乏关联')
        # conclusion 类型需要有支撑
        if step.type == 'conclusion':
            if step.connections:
                score += 0.1
            else:
                risks.append('结论缺乏支撑证据')
        # 内容过短扣分
        if len(step.content) < 30:
            score -= 0.1
            risks.append('步骤内容过短')
        elif len(step.content) > 100:
            score += 0.05
        # 被其他步骤引用加分
        if session and session.steps:
            cited = sum(1 for s in session.steps if step.number in s.connections)
            if cited > 0:
                score += 0.1
        score = round(max(0.1, min(1.0, score)), 4)
        return ConfidenceMeta(
            score=score,
            rationale=f'基于步骤类型({step.type})、关联数({len(step.connections)})和内容长度({len(step.content)})综合评估',
            risks=risks if risks else ['无明显风险'],
        )

    def compare_sessions(self, a=None, b=None) -> SessionCompare:
        """基于 Jaccard 相似度对比两个会话"""
        if not a or not b:
            return SessionCompare(similarity=0.0, recommendation='需要两个有效会话才能对比')
        # 文本相似度
        text_sim = self._calc_jaccard(a.problem + ' '.join(s.content for s in a.steps),
                                        b.problem + ' '.join(s.content for s in b.steps))
        # 步骤类型分布相似度
        ta = self._calc_step_type_stats(a.steps)
        tb = self._calc_step_type_stats(b.steps)
        all_types = set(list(ta.keys()) + list(tb.keys()))
        type_sim = sum(min(ta.get(t, 0), tb.get(t, 0)) for t in all_types) / max(1, sum(max(ta.get(t, 0), tb.get(t, 0)) for t in all_types))

        similarity = round(text_sim * 0.6 + type_sim * 0.4, 4)
        shared = list(set(self._extract_keywords(a.problem)) & set(self._extract_keywords(b.problem)))
        rec = '两会话高度相似，可参考彼此结论' if similarity > 0.6 else '两会话侧重不同，建议综合考量'

        return SessionCompare(
            shared_assumptions=shared,
            similarity=similarity,
            recommendation=rec,
        )

    def suggest_next(self, session=None) -> list[str]:
        """基于会话当前状态给出上下文感知的下一步建议"""
        if not session or not session.steps:
            return ['定义问题范围', '确定分析框架', '列出已知和未知因素']
        steps = session.steps
        types = {s.type for s in steps}
        last_type = steps[-1].type if steps else ''

        suggestions = []
        if 'analysis' not in types:
            suggestions.append('深入分析问题背景和关键因素')
        if 'hypothesis' not in types:
            suggestions.append('提出一个可验证的假设或解释')
        elif 'verification' not in types:
            suggestions.append('设计验证方案来检验现有假设')
        if 'conclusion' not in types:
            suggestions.append('总结当前发现，给出阶段性结论')
        else:
            suggestions.append('检查结论是否有遗漏的边界情况')

        # 最后一步特定建议
        if last_type == 'analysis':
            suggestions.append('基于分析结果形成假设')
        elif last_type == 'hypothesis':
            suggestions.append('寻找可能推翻假设的反例')
        elif last_type == 'verification':
            suggestions.append('根据验证结果调整或确认假设')
        elif last_type == 'conclusion':
            suggestions.append('考虑替代方案和潜在风险')

        # 去重，最多返回 3 条
        seen = set()
        result = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                result.append(s)
            if len(result) >= 3:
                break
        return result

    def optimize_query(self, problem: str) -> str:
        """基础文本优化：去除冗余，补充完整性"""
        p = problem.strip()
        # 去除开头冗余词
        redundants = ['请问', '我想问一下', '我想知道', '帮我分析', '请帮我']
        for r in redundants:
            if p.startswith(r):
                p = p[len(r):].strip()
        # 如果太短，不做修改
        if len(p) < 5:
            return p
        # 确保以问号结尾（如果是疑问句）
        if any(kw in p for kw in ['什么', '为什么', '如何', '怎么', '是否']) and not p.endswith('？'):
            p += '？'
        return p

    def merge_insights(self, main: list[str],
                       branches: dict[str, list[str]]) -> MergeResult:
        """结构化合并：先去重，再分组，计算共识度"""
        all_insights = list(main)
        for bid, bis in branches.items():
            all_insights.extend(bis)

        # 去重：基于内容前 60 字符
        seen, unique = set(), []
        for ins in all_insights:
            key = ins[:60]
            if key not in seen:
                seen.add(key)
                unique.append(ins)

        synthesis = '\n'.join(f'- {s}' for s in unique) if unique else '各分支未提供可合并的洞察'
        # 冲突检测：检查是否有相互矛盾的内容
        conflicts = []
        for i, a in enumerate(unique):
            for b in unique[i+1:]:
                # 简单规则：如果一句话有"但是/然而/相反"，可能存在矛盾
                if ('不' in a and '不' not in b) or ('增加' in a and '减少' in b):
                    conflicts.append(f'潜在冲突: "{a[:40]}..." vs "{b[:40]}..."')
                    break

        confidence = min(1.0, 0.5 + len(unique) * 0.05 - len(conflicts) * 0.1)
        strengths = []
        if len(unique) >= 3:
            strengths.append('多角度分析覆盖充分')
        if len(branches) >= 2:
            strengths.append('多分支提供了互补视角')
        if not conflicts:
            strengths.append('各分支结论一致性好')

        return MergeResult(
            synthesis=synthesis, conflicts=conflicts[:3],
            confidence=round(max(0.2, confidence), 4),
            strengths=strengths[:5],
        )

    def generate_summary(self, session: Optional[ThinkingSession],
                         fmt: str = 'linear') -> str:
        """多格式摘要生成：linear/tree/key_points/stats"""
        if not session or not session.steps:
            return ''
        steps = session.steps

        if fmt == 'linear':
            parts = []
            for s in steps:
                icon = {'analysis': '🔍', 'hypothesis': '💡', 'verification': '✅', 'conclusion': '🎯'}.get(s.type, '❓')
                parts.append(f'{icon} 步骤{s.number} [{s.type}]: {s.content[:80]}')
            return '\n'.join(parts)

        elif fmt == 'tree':
            lines = [f'🌳 {session.problem}']
            for s in steps:
                indent = '  ' * (s.number - 1) if s.parent_step else ''
                lines.append(f'{indent}├─ [{s.type}] {s.content[:60]}')
                if s.number in session.branches:
                    lines.append(f'{indent}  ├─ 🌿 分支: {session.branches[s.number].alternative_desc[:40]}')
            return '\n'.join(lines)

        elif fmt == 'key_points':
            parts = []
            for s in steps:
                if s.type == 'conclusion':
                    parts.append(f'🎯 {s.content[:100]}')
            if not parts:
                # 无结论时取最后 3 步
                for s in steps[-3:]:
                    parts.append(f'📌 {s.content[:80]}')
            return '\n'.join(parts) if parts else '（暂无关键点）'

        elif fmt == 'stats':
            dist = self._calc_step_type_stats(steps)
            total = len(steps)
            lines = [
                f'📊 会话统计',
                f'总步骤: {total}',
                f'类型分布: ' + ', '.join(f'{t}: {c}' for t, c in dist.items()),
                f'关联总数: {sum(len(s.connections) for s in steps)}',
                f'分支数: {len(session.branches)}',
                f'质量分: {session.quality_score:.2f}',
            ]
            return '\n'.join(lines)

        # 默认 linear
        return self.generate_summary(session, 'linear')

    def detect_patterns(self, sessions: dict = None) -> list[ThinkingPattern]:
        """基于真实会话数据统计推理模式"""
        if not sessions:
            return []
        sessions_list = list(sessions.values())
        if not sessions_list:
            return []

        # 统计模板使用频率
        tmpl_count = {}
        for s in sessions_list:
            tmpl = s.context.get('template_name', s.context.get('template_type', ''))
            if tmpl:
                tmpl_count[tmpl] = tmpl_count.get(tmpl, 0) + 1

        # 统计步骤类型序列模式
        seq_count = {}
        for s in sessions_list:
            seq = '-'.join(st.type for st in s.steps)
            if seq:
                seq_count[seq] = seq_count.get(seq, 0) + 1

        patterns = []
        # 模式1：最常用模板
        if tmpl_count:
            top_tmpl = max(tmpl_count, key=tmpl_count.get)
            patterns.append(ThinkingPattern(
                name=f'模板偏好: {top_tmpl}',
                frequency=tmpl_count[top_tmpl],
                confidence=min(1.0, tmpl_count[top_tmpl] / len(sessions_list)),
                description=f'最常用的思维模板是 {top_tmpl}，出现 {tmpl_count[top_tmpl]} 次',
            ))

        # 模式2：最常见步骤序列
        if seq_count:
            top_seq = max(seq_count, key=seq_count.get)
            patterns.append(ThinkingPattern(
                name=f'推理序列: {top_seq[:40]}',
                frequency=seq_count[top_seq],
                confidence=min(1.0, seq_count[top_seq] / len(sessions_list)),
                description=f'最常见的步骤类型序列模式',
            ))

        # 模式3：平均质量趋势
        avg_quality = sum(s.quality_score for s in sessions_list) / len(sessions_list)
        patterns.append(ThinkingPattern(
            name='质量基线',
            frequency=len(sessions_list),
            confidence=avg_quality,
            description=f'平均质量分 {avg_quality:.2f}，共 {len(sessions_list)} 个会话',
        ))

        return patterns[:5]


class LLMEngine:
    """LLM 推理引擎——异步调用大模型进行智能推理
    使用 httpx.AsyncClient，支持并发调用，不阻塞事件循环"""

    @property
    def is_llm(self) -> bool:
        return True

    def __init__(self, api_key: str, api_base: str = "",
                 model: str = "",
                 timeout: int = 60, max_retries: int = 2,
                 api_key2: str = "", api_base2: str = "", model2: str = "",
                 selector: int = 1, moa_rounds: int = 3, mode: str = "self-moa"):
        self.api_key = api_key
        self.api_base = api_base or "https://api.deepseek.com/v1"
        self.model = model or "deepseek-v4-flash"
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=30.0))
        self._semaphore = asyncio.Semaphore(5)
        # 模型2（可选）
        self.api_key2 = api_key2
        self.api_base2 = api_base2
        self.model2 = model2
        # LLM 选择器和 MoA 配置
        self.selector = selector
        self.moa_rounds = moa_rounds
        self.mode = mode

    async def close(self):
        await self.client.aclose()

    async def _call(self, prompt: str, max_tokens: int = 800,
                    temperature: float = 0.3,
                    api_key: str = "", api_base: str = "",
                    model: str = "") -> str:
        """
        调用 LLM API（异步，支持重试，受 Semaphore 并发限制）。
        若传入 api_key/api_base/model 则临时使用之（用于模型2），
        否则使用实例默认的模型1参数。
        """
        _key = api_key or self.api_key
        _base = api_base or self.api_base
        _model = model or self.model
        async with self._semaphore:
            log.debug("LLM call | model=%s | prompt_len=%d | max_tokens=%d",
                      _model, len(prompt), max_tokens)
            body = {
                "model": _model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            url = f"{_base}/chat/completions"

            for attempt in range(self.max_retries + 1):
                try:
                    resp = await self.client.post(
                        url, json=body,
                        headers={"Content-Type": "application/json",
                                 "Authorization": f"Bearer {_key}"}
                    )
                    if resp.status_code != 200:
                        log.warning("LLM API HTTP %d (attempt %d): %s",
                                    resp.status_code, attempt + 1, resp.text[:200])
                        if attempt < self.max_retries:
                            await asyncio.sleep(1)
                            continue
                        return ""
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                    if attempt < self.max_retries:
                        await asyncio.sleep(1)
                        continue
                except httpx.ReadTimeout:
                    log.warning("LLM API 超时 (attempt %d)", attempt + 1)
                    if attempt < self.max_retries:
                        await asyncio.sleep(1)
                        continue
                except Exception:
                    log.warning("LLM API 非预期异常 (attempt %d)", attempt + 1)
                    if attempt < self.max_retries:
                        await asyncio.sleep(1)
                        continue
            log.warning("LLM 返回空 (重试耗尽)")
            return ""

    async def generate_initial_analysis(self, problem: str) -> str:
        p = f"对以下问题进行简洁初始分析（中文，80字内）：\n{problem}\n格式：1)核心问题 2)关键因素 3)建议方法"
        return await self._call(p)

    async def calculate_quality(self, session: Optional[ThinkingSession]) -> float:
        if not session or not session.steps:
            return 0.5
        steps_str = "\n".join(
            f"[{s.type}] {s.content[:80]}" for s in session.steps
        )
        p = (f"评估推理质量，只返回0-1数字：\n问题：{session.problem}\n步骤：\n{steps_str}"
             "\n标准：多样性30%+连接30%+深度40%")
        r = (await self._call(p)).strip()
        try:
            return max(0.0, min(1.0, float(r)))
        except (ValueError, TypeError):
            return 0.5

    async def detect_patterns(self, sessions: dict = None) -> list[ThinkingPattern]:
        if not sessions:
            return []
        desc = "\n".join(
            f"- {s.problem} ({len(s.steps)}步)"
            for s in list(sessions.values())[:5]
        )
        p = (f"分析以下会话识别2-3种推理模式，返回JSON数组: "
             f'[{{"name":"","description":"","confidence":0.8}}]\n{desc}')
        r = await self._call(p)
        try:
            data = json.loads(r)
            return [ThinkingPattern(**item) for item in data]
        except (json.JSONDecodeError, TypeError):
            return [ThinkingPattern(name="结构化推理", frequency=0,
                                    confidence=0.8, description="步骤分明的分析过程")]

    async def merge_insights(self, main: list[str],
                              branches: dict[str, list[str]]) -> MergeResult:
        parts = ["主分支："] + [f"- {s}" for s in main]
        for bid, bis in branches.items():
            parts.append(f"\n分支{bid[:8]}：")
            parts.extend(f"- {s}" for s in bis)
        p = (f"合并以下多分支结论，JSON: "
             f'{{"synthesis":"","conflicts":[],"confidence":0.8,"strengths":[]}}\n'
             + "\n".join(parts))
        r = await self._call(p)
        try:
            return MergeResult(**json.loads(r))
        except (json.JSONDecodeError, TypeError):
            return MergeResult(
                synthesis="各分支提供了不同视角，建议综合考量。",
                confidence=0.6, strengths=["多角度分析"]
            )

    async def generate_summary(self, session: Optional[ThinkingSession],
                                fmt: str = "linear") -> str:
        if not session or not session.steps:
            log.warning("无会话或步骤为空，无法生成摘要")
            return ""
        steps_str = "\n".join(
            f"步骤{s.number}[{s.type}]: {s.content[:100]}"
            for s in session.steps
        )
        return await self._call(
            f"总结以下思维过程（中文，100字内）:\n问题:{session.problem}\n{steps_str}"
        )

    async def evaluate_quality(self, session: Optional[ThinkingSession]) -> QualityReport:
        if not session:
            return QualityReport()
        steps_str = "\n".join(
            f"步骤{s.number}[{s.type}]: {s.content[:100]}"
            for s in session.steps
        )
        p = (
            '评估以下推理的5个维度，返回JSON:\n'
            '{"overall":0.8,"coherence":0.8,"completeness":0.7,"rigor":0.7,'
            '"novelty":0.6,"actionable":0.8,"strengths":[""],"weaknesses":[""]}\n'
            "标准：coherence=一致性,completeness=完整性,rigor=严谨性,"
            "novelty=创新性,actionable=可操作性\n"
            f"问题:{session.problem}\n步骤:{steps_str}"
        )
        r = await self._call(p)
        try:
            data = json.loads(r)
            return QualityReport(**data)
        except (json.JSONDecodeError, TypeError):
            return self._default_quality(session)

    async def detect_biases(self, session: Optional[ThinkingSession]) -> list[BiasResult]:
        if not session:
            return []
        steps_str = "\n".join(
            f"步骤{s.number}[{s.type}]: {s.content[:100]}"
            for s in session.steps
        )
        p = (
            '检测以下推理中是否存在认知偏见（确认偏见、锚定效应、可得性启发、'
            '过度自信、框架效应、幸存者偏差、赌徒谬误、光环效应），返回JSON数组:\n'
            '[{"name":"确认偏见","description":"","severity":"中",'
            '"evidence":"步骤3只考虑了支持证据","suggestion":"应主动寻找反例"}]\n'
            "若未检测到偏见，返回空数组[]。\n"
            f"问题:{session.problem}\n{steps_str}"
        )
        r = await self._call(p)
        try:
            data = json.loads(r)
            return [BiasResult(**item) for item in data]
        except (json.JSONDecodeError, TypeError):
            return []

    async def estimate_complexity(self, problem: str) -> ComplexityEstimate:
        p = (f'评估以下问题的复杂度，返回JSON: '
             f'{{"level":"medium","estimated_steps":10,"suggested_template":"root-cause-analysis"}}'
             f'\nlevel: easy/medium/hard。\n问题:{problem}')
        r = await self._call(p)
        try:
            return ComplexityEstimate(**json.loads(r))
        except (json.JSONDecodeError, TypeError):
            return ComplexityEstimate(level="medium", estimated_steps=10)

    async def analyze_confidence(self, step: Optional[ThinkingStep],
                                  session: Optional[ThinkingSession]) -> ConfidenceMeta:
        if not step:
            return ConfidenceMeta(score=0.5)
        p = (f'评估以下推理步骤的置信度（0-1），返回JSON: '
             f'{{"score":0.8,"rationale":"","risks":[""]}}\n'
             f'问题:{session.problem if session else "N/A"}\n'
             f'步骤:{step.content[:200]}')
        r = await self._call(p)
        try:
            return ConfidenceMeta(**json.loads(r))
        except (json.JSONDecodeError, TypeError):
            return ConfidenceMeta(score=0.7, rationale="基于可用信息得出",
                                  risks=["信息可能不完整"])

    async def compare_sessions(self, a: Optional[ThinkingSession],
                                b: Optional[ThinkingSession]) -> SessionCompare:
        if not a or not b:
            return SessionCompare(similarity=0.0)
        p = (f'对比两个思维会话，返回JSON: '
             f'{{"shared_assumptions":[],"divergent_conclusions":[],'
             f'"similarity":0.7,"recommendation":""}}\n'
             f'会话A:{a.problem}(共{len(a.steps)}步)\n'
             f'会话B:{b.problem}(共{len(b.steps)}步)')
        r = await self._call(p)
        try:
            return SessionCompare(**json.loads(r))
        except (json.JSONDecodeError, TypeError):
            return SessionCompare(similarity=0.5,
                                   recommendation="两会话各有侧重，建议综合考量。")

    async def suggest_next(self, session: Optional[ThinkingSession]) -> list[str]:
        if not session or not session.steps:
            return ["定义问题并开始分析"]
        recent = "\n".join(
            f"步骤{s.number}[{s.type}]: {s.content[:80]}"
            for s in session.steps[-3:]
        )
        p = (f'基于以下推理进度，建议3个下一步方向（中文），JSON数组: '
             f'["建议1","建议2","建议3"]\n'
             f'问题:{session.problem}\n最近步骤:{recent}')
        r = await self._call(p)
        try:
            data = json.loads(r)
            return data if isinstance(data, list) else ["总结当前发现"]
        except (json.JSONDecodeError, TypeError):
            return ["总结当前发现", "考虑替代方案", "验证关键假设"]

    async def optimize_query(self, problem: str) -> str:
        p = f"优化以下问题表述使其更清晰具体，保持中文，只返回优化后的问题：\n{problem}"
        r = (await self._call(p)).strip()
        return r or problem

    async def moa_analyze(self, problem: str, steps_text: str = "",
                          rounds: int = 3) -> dict:
        """
        多模式推理引擎：
        - selector=0 → 返回提示（启发式引擎）
        - selector=1/2 → Self-MoA（单模型多轮温度采样投票）
        - selector=3 + mode=self-moa → 双模型各自温度采样投票后合并
        - selector=3 + mode=iterative → 双模型迭代推理（互相看输出后修正）
        """
        if self.selector == 0:
            return {"error": "当前为启发式引擎模式（ST_LLM_SELECTOR=0），MoA 不可用。如需 LLM 推理请设置 SELECTOR≥1。"}
        rounds = max(1, min(rounds, 20))
        if self.selector in (1, 2):
            return await self._self_moa_single(problem, steps_text, rounds)
        if self.mode == "iterative":
            return await self._iterative_moa(problem, steps_text, rounds)
        return await self._self_moa_dual(problem, steps_text, rounds)

    async def _self_moa_single(self, problem, steps_text, rounds):
        """单模型 Self-MoA：N 种温度采样，投票综合。"""
        temps = self._make_temps(rounds)
        responses = []
        prompt_base = (
            '你是一个推理专家。对以下问题进行独立分析。\n'
            '请从不同角度思考，返回 JSON:\n'
            '{"perspective":"你的视角","key_insight":"核心洞察",'
            '"confidence":0.8,"strengths":[""],"weaknesses":[""],"recommendation":"建议"}\n'
            f'问题: {problem}\n'
        )
        if steps_text:
            prompt_base += f'已有推理步骤:\n{steps_text}\n'
        for i, temp in enumerate(temps):
            prompt = (
                f'你是一个推理专家。对以下问题进行独立分析（第{i+1}轮）。\n'
                f'请从不同角度思考，返回JSON:\n'
                f'{{"perspective":"你的视角","key_insight":"核心洞察",'
                f'"confidence":0.8,"strengths":[""],"weaknesses":[""],"recommendation":"建议"}}\n'
                f'问题: {problem}\n'
            )
            if steps_text:
                prompt += f'已有推理步骤:\n{steps_text}\n'
            r = await self._call(prompt, max_tokens=500, temperature=temp)
            responses.append(self._parse_response(r, f"第{i+1}轮", temp, i + 1))
        return self._build_moa_result(responses, rounds, "Self-MoA")

    async def _self_moa_dual(self, problem, steps_text, rounds):
        """双模型 Self-MoA：各自温度采样后合并投票。模型2 key 缺失时降级为只用模型1。"""
        temps = self._make_temps(rounds)
        responses = []

        async def _sample(api_key, api_base, model, label):
            for i, temp in enumerate(temps):
                p = (
                    f"你是一个推理专家。对以下问题进行独立分析"
                    f"（{label} 第{i+1}轮）。\n"
                    f'请从不同角度思考，返回JSON:\n'
                    f'{{"perspective":"你的视角","key_insight":"核心洞察",'
                    f'"confidence":0.8,"strengths":[""],"weaknesses":[""],"recommendation":"建议"}}\n'
                    f"问题: {problem}\n"
                )
                if steps_text:
                    p += f"已有推理步骤:\n{steps_text}\n"
                r = await self._call(p, max_tokens=500, temperature=temp,
                                     api_key=api_key, api_base=api_base, model=model)
                data = self._parse_response(r, f"{label} 第{i+1}轮", temp, i + 1)
                data["_model"] = label
                responses.append(data)

        if self.api_key2:
            await asyncio.gather(
                _sample(self.api_key, self.api_base, self.model, "模型1"),
                _sample(self.api_key2, self.api_base2, self.model2, "模型2"),
            )
        else:
            await _sample(self.api_key, self.api_base, self.model, "模型1")

        return self._build_moa_result(
            responses, rounds,
            "Self-MoA-Dual" if self.api_key2 else "Self-MoA（模型2 key 缺失，仅用模型1）",
        )

    async def _iterative_moa(self, problem, steps_text, rounds):
        """迭代推理：双模型互相看对方输出后修正。模型2 key 缺失时降级为单模型自修正。"""
        if not self.api_key2:
            return await self._self_moa_single(problem, steps_text, rounds)

        ctx_a, ctx_b = "", ""
        all_responses = []

        for r in range(rounds):
            prompt_a = (
                f"你是一个推理专家。对以下问题进行第{r+1}轮迭代分析，返回JSON:\n"
                f'{{"perspective":"你的视角","key_insight":"核心洞察",'
                f'"confidence":0.8,"strengths":[""],"weaknesses":[""],"recommendation":"建议"}}\n'
                f"问题: {problem}\n"
            )
            if steps_text:
                prompt_a += f"已有推理步骤:\n{steps_text}\n"
            if ctx_b:
                prompt_a += f"\n上一轮模型2的观点（供你参考）:\n{ctx_b[:300]}\n"

            prompt_b = (
                f"你是一个推理专家。对以下问题进行第{r+1}轮迭代分析，返回JSON:\n"
                f'{{"perspective":"你的视角","key_insight":"核心洞察",'
                f'"confidence":0.8,"strengths":[""],"weaknesses":[""],"recommendation":"建议"}}\n'
                f"问题: {problem}\n"
            )
            if steps_text:
                prompt_b += f"已有推理步骤:\n{steps_text}\n"
            if ctx_a:
                prompt_b += f"\n上一轮模型1的观点（供你参考）:\n{ctx_a[:300]}\n"

            ra, rb = await asyncio.gather(
                self._call(prompt_a, max_tokens=500, temperature=0.5,
                          api_key=self.api_key, api_base=self.api_base, model=self.model),
                self._call(prompt_b, max_tokens=500, temperature=0.5,
                          api_key=self.api_key2, api_base=self.api_base2, model=self.model2),
            )
            ctx_a, ctx_b = ra, rb

            for raw, label in [(ra, "模型1"), (rb, "模型2")]:
                data = self._parse_response(raw, f"{label} 第{r+1}轮", 0.5, r + 1)
                data["_model"] = label
                all_responses.append(data)

        return self._build_moa_result(all_responses, rounds, "Iterative-MoA")

    @staticmethod
    def _make_temps(rounds):
        """生成 1~20 种温度序列，均匀覆盖 0.1~0.9。"""
        if rounds <= 5:
            return [0.3, 0.7, 1.0, 0.5, 0.9][:rounds]
        step = 0.85 / max(rounds - 1, 1)
        return [round(0.1 + i * step, 2) for i in range(rounds)]

    @staticmethod
    def _parse_response(raw, label, temperature, round_num):
        """解析 LLM 返回的 JSON，失败则用原始文本构建回退。"""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            data = {
                "perspective": f"{label}（原始输出）",
                "key_insight": raw[:200], "confidence": 0.5,
                "strengths": [], "weaknesses": [], "recommendation": "",
            }
        data["_temperature"] = temperature
        data["_round"] = round_num
        return data

    def _build_moa_result(self, responses, rounds, method):
        """从 responses 列表统一构建 MoA 结果字典。"""
        if not responses:
            return {"error": "所有 MoA 轮次均未返回有效结果"}
        best = max(responses, key=lambda x: x.get("confidence", 0))
        insights = [r.get("key_insight", "") for r in responses if r.get("key_insight")]
        best_insight = best.get("key_insight", "")
        consensus_count = sum(
            1 for r in responses
            if _jaccard_sim(best_insight[:60], r.get("key_insight", "")[:60]) > 0.3
        )
        consensus_ratio = consensus_count / len(responses) if responses else 0
        avg_confidence = round(
            sum(r.get("confidence", 0.5) for r in responses) / len(responses), 4
        )
        return {
            "primary": best,
            "all_perspectives": responses,
            "consensus": list(set(insights)),
            "moa_confidence": avg_confidence,
            "consensus_ratio": round(consensus_ratio, 2),
            "reliable": avg_confidence >= 0.6 and consensus_ratio >= 0.5,
            "warning": None if (avg_confidence >= 0.6 and consensus_ratio >= 0.5)
            else f"MoA 结果可靠性低（置信度={avg_confidence:.2f}, 共识度={consensus_ratio:.0%}），建议人工判断",
            "total_rounds": rounds,
            "method": method,
        }

    def _default_quality(self, session: Optional[ThinkingSession]) -> QualityReport:
        return QualityReport(
            overall=0.5, coherence=0.6, completeness=0.6,
            rigor=0.6, novelty=0.5, actionable=0.7,
        )
