"""
Sequential Thinking MCP — 9 种思维模板定义
路径: Core/Templates.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

提供 9 种结构化思维模板，每种模板包含：
- type: 模板标识符
- name: 中文名称
- description: 模板描述
- steps: 推荐的推理步骤列表
- when_to_use: 适用场景说明
"""

# 全部 9 种思维模板
TEMPLATES = {
    "scientific-method": {
        "type": "scientific-method",
        "name": "科学方法",
        "description": "通过观察、假设和测试来系统性解决问题",
        "steps": [
            "对问题进行观察",
            "基于观察提出问题",
            "形成可测试的假设",
            "根据假设做出预测",
            "通过分析或实验检验预测",
            "分析结果",
            "得出结论",
            "沟通发现",
        ],
        "when_to_use": "调查因果关系或测试理论时使用",
    },
    "five-whys": {
        "type": "five-whys",
        "name": "五问法",
        "description": "通过反复追问「为什么」找到根本原因",
        "steps": [
            "清晰陈述问题",
            "问：为什么会发生？基于事实回答",
            "再问：为什么？",
            "第三次问：为什么？",
            "第四次问：为什么？",
            "第五次问：为什么？",
            "识别揭示的根因",
            "针对根因制定对策",
        ],
        "when_to_use": "需要找到问题的根本原因时使用",
    },
    "root-cause-analysis": {
        "type": "root-cause-analysis",
        "name": "根因分析",
        "description": "结构化识别问题底层原因并防止复发",
        "steps": [
            "清晰定义问题及其影响",
            "收集关于问题发生时间和方式的数据",
            "识别人、流程、技术各方面的可能因素",
            "分析因果链以隔离最可能的根因",
            "用数据或实验验证根因",
            "制定针对确认根因的纠正措施",
            "实施纠正计划（含责任人和时间表）",
            "监控结果确保问题已解决",
        ],
        "when_to_use": "问题反复出现或有重大影响且必须防止复发时使用",
    },
    "decision-matrix": {
        "type": "decision-matrix",
        "name": "决策矩阵",
        "description": "根据多个标准对选项进行加权评估",
        "steps": [
            "列出所有待评估选项",
            "确定评估标准",
            "为每个标准分配权重",
            "对每个选项按每个标准打分",
            "计算加权分数",
            "汇总各选项加权总分",
            "比较总分确定最佳选项",
            "回顾并验证决策",
        ],
        "when_to_use": "在多个备选方案中做选择且有多因素需考虑时使用",
    },
    "swot-analysis": {
        "type": "swot-analysis",
        "name": "SWOT 分析",
        "description": "分析优势、劣势、机会和威胁",
        "steps": [
            "识别内部优势",
            "识别内部劣势",
            "识别外部机会",
            "识别外部威胁",
            "分析优势-机会策略",
            "分析劣势-机会策略",
            "分析优势-威胁策略",
            "分析劣势-威胁策略",
            "制定行动计划",
        ],
        "when_to_use": "评估项目、产品或战略决策时使用",
    },
    "pros-cons": {
        "type": "pros-cons",
        "name": "利弊分析",
        "description": "简单列出优缺点进行对比",
        "steps": [
            "清晰陈述决策或选项",
            "列出所有正面因素（利）",
            "列出所有负面因素（弊）",
            "考虑每个利弊的重要程度",
            "权衡利弊",
            "考虑否决因素",
            "做出决策",
        ],
        "when_to_use": "对正反两方面清晰的直接决策使用",
    },
    "first-principles": {
        "type": "first-principles",
        "name": "第一性原理",
        "description": "将问题分解到基本真理再向上推理",
        "steps": [
            "识别当前假设",
            "将问题分解到基本真理",
            "质疑每个假设：这一定正确吗？",
            "区分事实和假设",
            "从基本真理出发",
            "向上推理创造新方案",
            "挑战常规方法",
            "综合新的理解",
        ],
        "when_to_use": "常规思维无法解决问题或需要创新时使用",
    },
    "fishbone": {
        "type": "fishbone",
        "name": "鱼骨图（石川图）",
        "description": "按多类别进行因果分析",
        "steps": [
            "定义问题（鱼头）",
            "识别主要类别：人员、流程、设备、材料、环境、管理",
            "为每个类别找出可能原因",
            "对每个原因追问「为什么」",
            "深挖到根因",
            "确定最可能的根因",
            "用数据验证",
            "制定解决方案",
        ],
        "when_to_use": "分析有多个潜在原因的复杂问题时使用",
    },
    "pareto-analysis": {
        "type": "pareto-analysis",
        "name": "帕累托分析（80/20法则）",
        "description": "从众多因素中识别关键的少数",
        "steps": [
            "列出所有问题或原因",
            "测量每个的影响或频率",
            "按影响降序排列",
            "计算累计百分比",
            "识别导致80%影响的前20%因素",
            "聚焦关键少数",
            "制定针对性方案",
            "监控效果",
        ],
        "when_to_use": "需要优先处理哪些问题或改进时使用",
    },
}


def get_template(template_id: str) -> dict | None:
    """
    根据模板 ID 获取模板定义
    
    Args:
        template_id: 模板标识符，如 "root-cause-analysis"
    
    Returns:
        模板字典，不存在时返回 None
    """
    return TEMPLATES.get(template_id)


def get_all_templates() -> dict:
    """
    获取全部模板定义
    
    Returns:
        包含所有模板的字典
    """
    return TEMPLATES
