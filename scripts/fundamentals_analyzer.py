#!/usr/bin/env python3
"""
基本面分析工具（商业模式视角）。
分析支撑估值的结构性原因：经常性收入、利润率、ROIC、增长、现金流。
"""

import argparse
import json
import sys


def analyze_valuation_premium(m):
    insights = []
    recurring = m.get("recurring_revenue_pct", 0)
    if recurring >= 80:
        insights.append({"signal": f"经常性收入占比 {recurring}%", "meaning": "收入高度可预测，客户粘性极强。", "strength": "strong"})
    elif recurring >= 50:
        insights.append({"signal": f"经常性收入占比 {recurring}%", "meaning": "收入有一定可预测性。", "strength": "moderate"})

    om = m.get("operating_margin", 0)
    if om > 0.20:
        insights.append({"signal": f"营业利润率 {om:.0%}", "meaning": "高于行业平均的盈利能力。",
                         "strength": "strong" if om > 0.25 else "moderate"})

    gm = m.get("gross_margin", 0)
    if gm > 0.50:
        insights.append({"signal": f"毛利率 {gm:.0%}", "meaning": "高毛利说明产品有差异化。", "strength": "strong"})

    roic = m.get("roic", 0)
    if roic > 0.15:
        insights.append({"signal": f"ROIC {roic:.0%}", "meaning": "资本配置效率极高。",
                         "strength": "strong" if roic > 0.20 else "moderate"})

    rev_cagr = m.get("revenue_cagr_5y", 0)
    if rev_cagr > 0.10:
        insights.append({"signal": f"营收5年CAGR {rev_cagr:.0%}", "meaning": "市场认为增长可持续。",
                         "strength": "strong" if rev_cagr > 0.15 else "moderate"})

    fcf_margin = m.get("fcf_margin", 0)
    if fcf_margin > 0.10:
        insights.append({"signal": f"FCF利润率 {fcf_margin:.0%}", "meaning": "利润质量高（赚的是真钱）。",
                         "strength": "strong" if fcf_margin > 0.15 else "moderate"})

    strong = sum(1 for i in insights if i["strength"] == "strong")
    moderate = sum(1 for i in insights if i["strength"] == "moderate")

    if strong >= 3:
        explanation = "多项强信号叠加，市场高估值有充分基本面支撑。"
    elif strong >= 1 and moderate >= 2:
        explanation = "基本面质量中上，溢价主要来自确定性。"
    elif moderate >= 2:
        explanation = "部分指标支撑溢价，需关注增长可持续性。"
    else:
        explanation = "估值溢价缺乏足够基本面支撑，需警惕。"

    return {
        "company": m.get("company", "Unknown"),
        "ticker": m.get("ticker", ""),
        "valuation_judgment": [
            f"P/E {m.get('pe_trailing', 0):.0f}x" if m.get('pe_trailing') else "",
            f"P/S {m.get('ps', 0):.1f}x" if m.get('ps') else "",
            f"EV/EBITDA {m.get('ev_ebitda', 0):.0f}x" if m.get('ev_ebitda') else "",
        ],
        "premium_signals": insights,
        "premium_explanation": explanation,
        "strong_signal_count": strong,
        "moderate_signal_count": moderate,
        "questions_to_investigate": [
            "这家公司的护城河，千丁能复制吗？",
            "这家公司从 X 亿到 Y 亿的关键跃迁是什么？千丁在哪个阶段？",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="基本面分析工具")
    parser.add_argument("--input", "-i", help="输入 JSON 文件（含 metrics 字段）")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    metrics = data.get("metrics", {})
    metrics["company"] = data.get("company", "Unknown")
    metrics["ticker"] = data.get("ticker", "")

    result = analyze_valuation_premium(metrics)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"已保存: {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n{'='*60}")
        print(f" {result['company']} ({result['ticker']}) — 为什么市场给这个估值？")
        print(f"{'='*60}")
        for j in filter(None, result.get("valuation_judgment", [])):
            print(f"  💰 {j}")
        print()
        for sig in result.get("premium_signals", []):
            emoji = {"strong": "🟢", "moderate": "🟡"}.get(sig["strength"], "⚪")
            print(f"  {emoji} {sig['signal']} — {sig['meaning']}")
        print(f"\n  📌 总结：{result['premium_explanation']}")
        print(f"\n  ❓ 值得深挖的问题：")
        for i, q in enumerate(result.get("questions_to_investigate", []), 1):
            print(f"     {i}. {q}")


if __name__ == "__main__":
    main()
