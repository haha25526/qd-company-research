#!/usr/bin/env python3
"""
合并六路研究流结果，生成 Review 检查点摘要。
统计各流来源数、关键发现、认知提取进度、数据缺口。
"""

import sys
import re
import argparse
from pathlib import Path

STREAMS = {
    'financials': 'A 财务', 'business': 'B 业务', 'strategy': 'C 战略',
    'stream_D': 'D 领导思维', 'stream_E': 'E 批判视角', 'stream_F': 'F 文化符号',
}

COG_SUFFIX = {
    'financials': 'financials_cognitive', 'business': 'business_cognitive',
    'strategy': 'strategy_cognitive', 'stream_D': 'stream_D_cognitive',
    'stream_E': 'stream_E_cognitive', 'stream_F': 'stream_F_cognitive',
}


def count_sources(content: str) -> dict:
    urls = set(re.findall(r'https?://[^\s\)]+', content))
    primary = len(re.findall(r'一手|primary|公司公告|年报|财报|招股书|10-K|SEC', content, re.IGNORECASE))
    secondary = len(re.findall(r'二手|secondary|分析师|媒体|报道', content, re.IGNORECASE))
    return {'url_count': len(urls), 'primary': primary, 'secondary': secondary}


def key_findings(content: str, max_items: int = 3) -> list:
    headings = re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
    if headings:
        return headings[:max_items]
    bolds = re.findall(r'\*\*(.+?)\*\*', content)
    if bolds:
        return bolds[:max_items]
    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
    return [l[:50] + '...' if len(l) > 50 else l for l in lines[:max_items]]


def count_models(content: str) -> int:
    models = re.findall(r'^(?:#{1,3})\s+(.+?)$', content, re.MULTILINE)
    skip = ['来源', '证据', '核心', '验证', 'confidence', '应用提示']
    return len([m for m in models if not any(sk in m.lower() for sk in skip)])


def count_verification(content: str) -> dict:
    text = content.lower()
    return {
        'cross_domain': len(re.findall(r'\[✅跨域\]|跨域', text)),
        'predictive': len(re.findall(r'\[✅预测\]|预测', text)),
        'exclusive': len(re.findall(r'\[✅排他\]|排他', text)),
    }


def find_gaps(files: dict) -> list:
    gaps = []
    fin = files.get('financials', '')
    if not re.search(r'营收|revenue', fin, re.IGNORECASE):
        gaps.append('营收数据')
    if not re.search(r'净利润|net income', fin, re.IGNORECASE):
        gaps.append('净利润数据')
    biz = files.get('business', '')
    if not re.search(r'分部|segment', biz, re.IGNORECASE):
        gaps.append('业务分部数据')
    return gaps


def main():
    parser = argparse.ArgumentParser(description='合并调研结果，生成 Review 摘要')
    parser.add_argument('research_dir', help='research 目录路径')
    parser.add_argument('--company', default='', help='公司标识')
    args = parser.parse_args()

    rdir = Path(args.research_dir)
    if not rdir.exists():
        print(f"❌ 目录不存在: {rdir}")
        sys.exit(1)

    files, rows = {}, []
    total_urls = total_primary = total_secondary = 0
    missing, cognitive_progress = [], []

    for key, label in STREAMS.items():
        base_pat = f"{args.company}_{key}" if args.company else f"*{key}*"
        raw_file = next(rdir.glob(f"{base_pat}.md"), None)
        cog_suffix = COG_SUFFIX.get(key, f"{key}_cognitive")
        cog_pat = f"{args.company}_{cog_suffix}.md" if args.company else f"*{cog_suffix}.md"
        cog_file = next(rdir.glob(cog_pat), None)

        if not raw_file:
            missing.append(label)
            rows.append(f"│ {label:<12} │ {'❌ 缺失':<8} │ {'—':<24} │ {'—':<12} │")
            continue

        content = files[key] = raw_file.read_text(encoding='utf-8')
        stats = count_sources(content)
        findings = key_findings(content)
        total_urls += stats['url_count']
        total_primary += stats['primary']
        total_secondary += stats['secondary']

        findings_str = ', '.join(findings) if findings else '—'
        if len(findings_str) > 40:
            findings_str = findings_str[:37] + '...'

        cog_col = '—'
        if cog_file and cog_file.exists():
            cog_content = cog_file.read_text(encoding='utf-8')
            model_cnt = count_models(cog_content)
            v = count_verification(cog_content)
            parts = [f"{model_cnt}模型"]
            if v['cross_domain']: parts.append(f"{v['cross_domain']}跨域")
            if v['predictive']: parts.append(f"{v['predictive']}预测")
            if v['exclusive']: parts.append(f"{v['exclusive']}排他")
            cog_col = '\n'.join(parts)
            cognitive_progress.append(f"{label}: {'/'.join(parts)}")

        rows.append(f"│ {label:<12} │ {stats['url_count']:<8} │ {findings_str:<24} │ {cog_col:<18} │")

    gaps = find_gaps(files)

    print("┌──────────────┬──────────┬──────────────────────────┬──────────────────┐")
    print("│ Stream       │ 来源数   │ 关键发现                  │ 认知提取进度      │")
    print("├──────────────┼──────────┼──────────────────────────┼──────────────────┤")
    for r in rows:
        print(r)
    print("├──────────────┼──────────┼──────────────────────────┼──────────────────┤")

    ratio = f"{total_primary}/{total_primary + total_secondary}" if (total_primary + total_secondary) > 0 else "未标记"
    print(f"│ 总计         │ {total_urls:<8} │ 一手占比: {ratio:<15} │ {'—':<18} │")
    if gaps:
        print(f"│ 数据缺失     │ {len(gaps)}项      │ {', '.join(gaps[:2]):<24} │ {'—':<18} │")
    if missing:
        print(f"│ 信息不足维度  │ {len(missing)}个      │ {', '.join(missing):<24} │ {'—':<18} │")
    print("└──────────────┴──────────┴──────────────────────────┴──────────────────┘")

    if cognitive_progress:
        print("\n🧠 认知提取进度:")
        for p in cognitive_progress:
            print(f"  {p}")

    if total_urls < 5:
        print("\n⚠️ 总来源数 <5，建议补充调研")


if __name__ == '__main__':
    main()
