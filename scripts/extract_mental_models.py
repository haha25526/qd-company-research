#!/usr/bin/env python3
"""
从六路研究流的 cognitive.md 提取思维模型，应用三重验证，生成 company-skill.md。
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

STREAM_INFO = {
    'financials': {'name': 'A 财务'},
    'business': {'name': 'B 业务'},
    'strategy': {'name': 'C 战略'},
    'stream_D': {'name': 'D 领导思维'},
    'stream_E': {'name': 'E 批判视角'},
    'stream_F': {'name': 'F 文化符号'},
}


def load_cognitive_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding='utf-8')


def extract_models(content: str, stream: str) -> list:
    models = []
    title_pattern = re.compile(r'^(#{1,3})\s+(.+?)$', re.MULTILINE)
    headings = [(m.start(), m.group(2)) for m in title_pattern.finditer(content)]

    for i, (start_pos, title) in enumerate(headings):
        end_pos = headings[i + 1][0] if i + 1 < len(headings) else len(content)
        block = content[start_pos:end_pos]

        skip = ['来源', '证据', '核心', '验证', 'confidence', '应用提示']
        if any(sk in title.lower() for sk in skip):
            continue

        core_match = re.search(r'\*\*(.+?)\*\*', block)
        core = core_match.group(1).strip() if core_match else title.strip()

        evidence_match = re.search(r'来源证据[：:]\s*(.+)', block)
        evidence = evidence_match.group(1).strip() if evidence_match else ""

        verification = {
            'cross_domain': bool(re.search(r'\[✅跨域\]|跨域', block, re.IGNORECASE)),
            'predictive': bool(re.search(r'\[✅预测\]|预测', block, re.IGNORECASE)),
            'exclusive': bool(re.search(r'\[✅排他\]|排他', block, re.IGNORECASE)),
        }

        conf_match = re.search(r'confidence[：:]\s*(high|medium|low)', block, re.IGNORECASE)
        confidence = conf_match.group(1).lower() if conf_match else 'medium'

        contradictions = re.findall(r'contradiction[：:]\s*(.+)', block, re.IGNORECASE)
        urls = re.findall(r'https?://[^\s\)]+', block)

        models.append({
            'title': title.strip(), 'core': core, 'evidence': evidence,
            'verification': verification, 'confidence': confidence,
            'contradictions': contradictions, 'stream': stream,
            'stream_name': STREAM_INFO[stream]['name'], 'source_urls': urls,
        })
    return models


def cross_domain_verification(models: list) -> list:
    for m in models:
        matches = 0
        for other in models:
            if m['stream'] == other['stream']:
                continue
            t_words = set(re.findall(r'\w+', m['title'].lower()))
            o_words = set(re.findall(r'\w+', other['title'].lower()))
            if len(t_words & o_words) >= 2:
                matches += 1
        if matches > 0:
            m['verification']['cross_domain'] = True
            m['cross_domain_notes'] = f"在 {matches} 个其他 Stream 中发现相似表述"
    return models


def predictive_validation(models: list, company: str, research_dir: Path) -> list:
    strategy_file = next(research_dir.glob(f"*{company}*strategy*.md"), None)
    if not strategy_file:
        for m in models:
            m['verification']['predictive'] = False
            m['predictive_notes'] = "未找到可测试的历史决策"
        return models

    content = strategy_file.read_text(encoding='utf-8')
    decision_pattern = re.compile(r'^(#{1,4})\s+(\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?)?\s*(.+?)$', re.MULTILINE)
    decisions = []
    for m in decision_pattern.finditer(content):
        title = m.group(3).strip()
        if len(title) > 10:
            decisions.append({'date': m.group(2) or "", 'title': title})

    for m in models:
        evidence_lower = m['evidence'].lower()
        matched = sum(1 for d in decisions if d['title'] and
                      any(w in evidence_lower for w in re.findall(r'\w+', d['title'].lower()) if len(w) > 2))
        if matched >= 1:
            m['verification']['predictive'] = True
            m['predictive_notes'] = f"能解释 {matched} 个历史决策"
        else:
            m['verification']['predictive'] = False
            m['predictive_notes'] = "未找到直接证据支撑"
    return models


def check_exclusivity(models: list) -> list:
    generic_phrases = ['客户至上', '追求卓越', '持续创新', '以人为本', 'customer first', 'excellence', 'innovation']
    for m in models:
        core_lower = m['core'].lower()
        m['verification']['exclusive'] = not any(gp in core_lower for gp in generic_phrases)
    return models


def get_verification_icon(verification: dict) -> str:
    icons = []
    if verification.get('cross_domain'): icons.append('✅跨域')
    if verification.get('predictive'): icons.append('✅预测')
    if verification.get('exclusive'): icons.append('✅排他')
    return ' '.join(icons) if icons else '⚠️未验证'


def generate_skill_md(company: str, models: list, research_dir: Path) -> str:
    lines = ["---",
             f"name: {company}-perspective",
             f"description: {company} 的认知操作系统 —— 基于公开信息的思维模型提取",
             "version: 4.0-extracted",
             "source: qd-company-research",
             f"date: {datetime.now().strftime('%Y-%m-%d')}",
             "---", "", f"# {company} 认知操作系统", ""]

    # Mental Models
    lines.append("## 🧠 Mental Models（思维模型）\n")
    for m in models:
        if '思维模型' not in m['title'] and '启发式' not in m['title']:
            continue
        lines.append(f"### {m['title']}")
        lines.append(f"- **核心**: {m['core']}")
        lines.append(f"- **来源证据**: [{get_verification_icon(m['verification'])}] {m['evidence'] or '见来源文件'}")
        if m.get('predictive_notes'):
            lines.append(f"- **预测验证**: {m['predictive_notes']}")
        lines.append(f"- **排他性**: {'✅ 独特' if m['verification']['exclusive'] else '⚠️ 通用'}")
        lines.append(f"- **confidence**: {m['confidence']}\n")

    # Decision Heuristics
    lines.append("## ⚡ Decision Heuristics（决策启发式）\n")
    for m in models:
        if '启发式' in m['title'] or any(k in m['title'] for k in ['规则', '原则']):
            lines.append(f"### \"{m['core']}\"")
            lines.append(f"- **触发条件**: 待补充")
            lines.append(f"- **行动原则**: {m['core']}")
            lines.append(f"- **来源证据**: {m['evidence']}")
            if m['contradictions']:
                lines.append(f"- **反例**: {', '.join(m['contradictions'])}")
            lines.append(f"- **confidence**: {m['confidence']}\n")

    # Values & Anti-patterns
    lines.append("## 🛑 Values & Anti-patterns（价值观与禁忌）\n")
    for m in models:
        if any(kw in m['title'] for kw in ['不做', '禁忌', '价值观', '底线', 'anti-pattern']):
            lines.append(f"### {m['title']}")
            lines.append(f"- **表现**: {m['core']}")
            lines.append(f"- **来源证据**: {m['evidence']}\n")

    # Honest Limits
    lines.append("## 📉 Honest Limits（诚实的局限）\n")
    for m in models:
        if any(kw in m['title'] for kw in ['局限', '无法', '过时', '边界']):
            lines.append(f"### {m['title']}")
            lines.append(f"- **说明**: {m['core']}\n")

    # Qianding Mapping
    lines.append("## 🎯 千丁启示（Qianding Mapping）\n")
    lines.append("### 可借鉴的思维模型\n")
    for m in models[:3]:
        lines.append(f"1. **{m['title']}** → 千丁可学习：{m['core']}")
    lines.append("\n### 风险对照\n（待人工补充）\n")

    # Evidence Table
    lines.append("## 📚 证据链\n\n| # | 模型名称 | 跨域 | 预测 | 排他 | Confidence |\n|---|---------|------|------|------|-----------|\n")
    for idx, m in enumerate(models, 1):
        cross_icon = "✅" if m['verification']['cross_domain'] else "❌"
        pred_icon = "✅" if m['verification']['predictive'] else "❌"
        excl_icon = "✅" if m['verification']['exclusive'] else "❌"
        lines.append(f"| {idx} | {m['title'][:10]} | {cross_icon} | {pred_icon} | {excl_icon} | {m['confidence']} |\n")

    # Usage
    lines.append("\n## 🔄 使用方式\n\n```bash\n")
    lines.append(f"\\load {company}-perspective.md\n```\n\n")
    lines.append(f"**提问示例**:\n- Use {company}'s perspective: 如果面临 AI 颠覆，他们会如何应对？\n")
    lines.append(f"- Based on {company}'s mental models: 我们该不该进入这个新市场？\n")

    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(description='从 cognitive.md 提取思维模型，生成 company-skill.md')
    parser.add_argument('research_dir', help='research 目录路径')
    parser.add_argument('--company', required=True, help='公司名称')
    parser.add_argument('--output', help='输出文件路径')
    args = parser.parse_args()

    research_dir = Path(args.research_dir)
    company = args.company

    all_models = []
    for stream_key in STREAM_INFO.keys():
        cog_file = research_dir / f"{company}_{stream_key}_cognitive.md"
        if cog_file.exists():
            content = load_cognitive_file(cog_file)
            models = extract_models(content, stream_key)
            all_models.extend(models)
            print(f"✅  {STREAM_INFO[stream_key]['name']}: {len(models)} 个思维模型")
        else:
            print(f"⚠️  {STREAM_INFO[stream_key]['name']}: 文件不存在")

    if not all_models:
        print("❌ 未提取到任何思维模型")
        sys.exit(1)

    print(f"\n📊 总计: {len(all_models)} 个思维模型/启发式")

    all_models = cross_domain_verification(all_models)
    all_models = predictive_validation(all_models, company, research_dir)
    all_models = check_exclusivity(all_models)

    passed = [m for m in all_models if sum(m['verification'].values()) >= 2]
    print(f"✅ 通过验证（≥2项）: {len(passed)} / {len(all_models)}")

    output_path = Path(args.output or research_dir / f"{company}_skill.md")
    output_path.write_text(generate_skill_md(company, all_models, research_dir), encoding='utf-8')
    print(f"\n✅ Skill 已生成: {output_path}")


if __name__ == '__main__':
    main()
