#!/usr/bin/env python3
"""
质量检查工具：营收、利润、业务分部、来源标注、千丁关联、思维模型、验证覆盖、不确定性。
"""

import sys
import re
from pathlib import Path


def check_revenue_data(content: str) -> tuple[bool, str]:
    found = sum(1 for p in [r'营收|revenue', r'\d+\.?\d*\s*[亿万千]?\s*(?:元|USD|RMB|HKD)'] if re.search(p, content, re.IGNORECASE))
    return found >= 2, f"营收数据 {'✅' if found >= 2 else '❌'}"


def check_profit_data(content: str) -> tuple[bool, str]:
    found = bool(re.search(r'净利润|net income|利润率|margin', content, re.IGNORECASE))
    return found, f"利润数据 {'✅' if found else '❌'}"


def check_segment_data(content: str) -> tuple[bool, str]:
    found = bool(re.search(r'分部|segment|业务线|板块', content, re.IGNORECASE))
    return found, f"业务分部 {'✅' if found else '❌'}"


def check_source_citations(content: str) -> tuple[bool, str]:
    urls = re.findall(r'https?://[^\s\)]+', content)
    has_cite = bool(re.search(r'来源|source|招股书|年报|10-K|SEC', content, re.IGNORECASE))
    passed = len(urls) >= 3 or has_cite
    return passed, f"来源标注: {len(urls)} 个URL {'✅' if passed else '❌'}"


def check_qianding_correlation(content: str) -> tuple[bool, str]:
    found = bool(re.search(r'千丁|qianding|启示|关联', content, re.IGNORECASE))
    return found, f"千丁关联 {'✅' if found else '❌'}"


def check_cognitive_models(content: str) -> tuple[bool, str]:
    has_section = bool(re.search(r'##\s*Mental Models|思维模型', content, re.IGNORECASE))
    model_cnt = len(re.findall(r'^(?:#{1,3})\s+.+?$', content, re.MULTILINE))
    passed = has_section and model_cnt >= 3
    return passed, f"思维模型: {model_cnt} 个 {'✅' if passed else '❌'}"


def check_verification_status(content: str) -> tuple[bool, str]:
    cross = len(re.findall(r'\[✅跨域\]|跨域', content, re.IGNORECASE))
    pred = len(re.findall(r'\[✅预测\]|预测', content, re.IGNORECASE))
    excl = len(re.findall(r'\[✅排他\]|排他', content, re.IGNORECASE))
    total = len(re.findall(r'^(?:#{1,3})\s+.+?$', content, re.MULTILINE))
    if total == 0:
        return True, "验证状态: 无模型需检查"
    ratio = (cross + pred + excl) / total if total > 0 else 0
    passed = ratio >= 0.5
    return passed, f"验证覆盖率: {cross}跨域/{pred}预测/{excl}排他 {'✅' if passed else '❌'}"


def check_uncertainty_marking(content: str) -> tuple[bool, str]:
    has_limits = bool(re.search(r'##\s*Honest Limits|诚实的局限', content, re.IGNORECASE))
    uncertainty_cnt = len(re.findall(r'不确定|无法判断|未知|过时|局限性|boundary|limit', content, re.IGNORECASE))
    passed = has_limits or uncertainty_cnt >= 2
    return passed, f"不确定性标注: {'✅' if passed else '❌'}"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 quality_check.py <文件路径>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding='utf-8')
    is_skill = file_path.stem.endswith('_skill') or 'skill' in file_path.name.lower()

    checks = [
        ("营收数据", check_revenue_data),
        ("利润数据", check_profit_data),
        ("业务分部", check_segment_data),
        ("来源标注", check_source_citations),
        ("千丁关联", check_qianding_correlation),
    ]
    if is_skill:
        checks.extend([
            ("思维模型提取", check_cognitive_models),
            ("验证状态覆盖", check_verification_status),
            ("不确定性标注", check_uncertainty_marking),
        ])

    print(f"质量检查: {file_path.name}")
    print("=" * 60)

    passed_cnt = 0
    for name, fn in checks:
        passed, detail = fn(content)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:<16} {status}  {detail}")
        if passed:
            passed_cnt += 1

    print("=" * 60)
    print(f"结果: {passed_cnt}/{len(checks)} 通过")

    if passed_cnt >= len(checks) - 1:
        print("🎉 基本通过，可交付")
    else:
        print("❌ 建议补充调研")
    sys.exit(0 if passed_cnt >= len(checks) - 1 else 1)


if __name__ == '__main__':
    main()
