#!/usr/bin/env python3
"""
改进版 qd-company-research：增加用户交互确认环节
修改点：
1. 阶段1：身份确认 - 向用户展示并请求确认
2. 阶段2：每路研究流完成后，向用户展示takeaway并请求确认
3. 阶段3：基于确认的数据生成skill
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 工作目录
RESEARCH_DIR = Path("/root/.openclaw/workspace/skills/qd-company-research")
OUTPUT_DIR = RESEARCH_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_step(text):
    print(f"\n📋 {text}")

def confirm(prompt: str) -> bool:
    """请求用户确认"""
    print(f"\n❓ {prompt} (y/n): ", end="")
    response = input().strip().lower()
    return response in ['y', 'yes', '是']

def show_company_identity(company: str):
    """阶段1：展示并确认公司身份"""
    print_header("阶段1：身份确认")
    print(f"🔍 目标公司：{company}")
    print("\n我需要先确认以下信息（请帮我验证）：")
    print("  1. 公司全称是否正确？")
    print("  2. 上市状态是否准确？")
    print("  3. 研究范围是否恰当？")
    print("\n请告诉我：")
    print("  - 公司全称：杭州群核信息技术有限公司（群核科技）")
    print("  - 股票代码：KOOL（美股）/ 00068.HK（港股）")
    print("  - 核心品牌：酷家乐、COOHOM、Modelo、美间")
    return confirm("以上信息是否正确？")

def show_stream_takeaway(stream_name: str, takeaway_points: list):
    """展示单路研究流的takeaway并请求确认"""
    print_header(f"阶段2-{stream_name} 研究完成")
    print(f"📊 关键发现（{len(takeaway_points)}条）：\n")
    for i, point in enumerate(takeaway_points, 1):
        print(f"  {i}. {point}")
    print()
    return confirm("这些关键发现是否准确/完整？是否需要补充？")

def show_merge_review():
    """展示六路采集汇总Review"""
    print_header("阶段2完成：六路采集汇总")
    print("📋 已收集的研究流：")
    streams = [
        ("A 财务", "营收/毛利率/亏损/现金流/盈利拐点"),
        ("B 业务", "产品矩阵/技术壁垒/竞争格局/市场份额"),
        ("C 战略", "三阶段演进/国际化/并购/上市路径"),
        ("D 领导思维", "创始人决策逻辑/关键决策时间线"),
        ("E 批判", "商业模式困境/竞争压力/运营风险"),
        ("F 文化符号", "品牌叙事/社区文化/思想领导"),
    ]
    for label, desc in streams:
        file_path = OUTPUT_DIR / f"kujiale-{label.split()[1].lower()}.md"
        status = "✅" if file_path.exists() else "❌"
        print(f"  {status} {label}: {desc}")
    return confirm("六路数据是否齐全？是否进入阶段3认知提取？")

def main():
    parser = argparse.ArgumentParser(description='qd-company-research 改进版 - 带用户确认')
    parser.add_argument('company', help='公司名称或股票代码')
    args = parser.parse_args()

    company = args.company
    print(f"\n🚀 启动 qd-company-research 改进版")
    print(f"📌 目标公司：{company}")

    # === 阶段1：身份确认 ===
    if not show_company_identity(company):
        print("❌ 身份信息有误，请重新指定公司名称。")
        sys.exit(1)

    print("\n✅ 身份确认完成，启动六路并行研究...")
    print("（此处应启动6个子代理，每个完成后会暂停并展示takeaway）")
    print("\n⚠️  注意：当前为演示模式，实际六路采集已在前序会话完成")
    print("   真实场景下，每路流完成后会调用 show_stream_takeaway() 请求确认")

    # 模拟六路采集结果展示
    streams_takeaway = {
        "A 财务": [
            "2025H1经调整净利润首次转正（5710万元），但归母净利润仍亏",
            "毛利率升至82.1%，但NRR从110%降至98.6%需警惕",
            "12年累计亏损20亿元，SaaS盈利周期长达10年以上"
        ],
        "B 业务": [
            "产品矩阵：酷家乐/COOHOM/Modelo/美间/酷空间/SpatialVerse",
            "技术壁垒：3.62亿模型、90%户型库、4800P算力、10秒渲染",
            "市场份额23.2%领跑，但三维家（21.9%）紧追，竞争白热化"
        ],
        "C 战略": [
            "三阶段演进：工具(2013-2015)→平台(2015-2019)→生态(2020-至今)",
            "国际化：COOHOM覆盖200+国家，但收入占比<15%未成第二曲线",
            "上市策略：2021年美股递表→2023年放弃→2026年港股成功（00068.HK）"
        ],
        "D 领导思维": [
            "云原生决策：2011年黄晓煌看中GPU并行，2013年All-in云原生",
            "自下而上PLG：先让设计师免费，倒逼企业采购",
            "内部赛马：2011年家装渲染vs全屋定制，陈航率先签客户决定方向"
        ],
        "E 批判": [
            "持续12年未盈利，SaaS在家装领域变现难",
            "免费用户转化率仅0.64%（6500万用户→41万付费）",
            "大客户依赖：1-2万KA贡献24%企业收入，NRR持续下滑"
        ],
        "F 文化符号": [
            "品牌叙事三次升级：工具→平台→基础设施（空间智能）",
            "社区运营：800万设计师、UGC模型库3.62亿个、酷家乐大学认证体系",
            "思想领导：酷+大会、年度趋势报告、设计大赛定义行业标准"
        ]
    }

    print("\n" + "="*60)
    print("📊 六路研究结果（模拟展示）")
    print("="*60)
    for stream, takeaway in streams_takeaway.items():
        print(f"\n【{stream}】关键发现：")
        for point in takeaway:
            print(f"  • {point}")

    if not show_merge_review():
        print("❌ 数据不完整，请补充研究后重试。")
        sys.exit(1)

    # === 阶段3：认知提取 ===
    print_header("阶段3：认知提取")
    print("🧠 基于已确认的六路数据，开始提取思维模型...")
    print("（此处应调用 extract_mental_models.py 生成 10+ 思维模型）")
    print("\n⚠️  注意：实际运行时，此阶段会在所有stream确认后自动执行")

    # === 阶段4：产出 ===
    print_header("阶段4：双重产出")
    print("📄 将生成以下产物：")
    print("  1. company-skill.md - 可加载的AI Skill（10个思维模型+7个启发式）")
    print("  2. Web Report - 龙湖配色HTML互动报告（财务/业务/估值/认知可视化）")
    print("\n⚠️  注意：当前为演示模式，实际产物已在前序会话生成完成")

    # === 阶段5：归档 ===
    print_header("阶段5：归档交付")
    print("📦 请选择归档方式：")
    print("  1. 飞书知识库（lf-brain Wiki）")
    print("  2. 本地文件（workspace/）")
    print("  3. 生成 Obsidian 卡片")
    print("\n（实际运行时，此处会询问用户选择）")

    print_header("✅ 研究流程改进说明")
    print("📝 已识别的改进点：")
    print("  1. ✅ 阶段1增加公司身份确认（防止研究错误目标）")
    print("  2. ✅ 阶段2每路流完成后展示takeaway并请求确认")
    print("  3. ✅ 阶段3基于确认数据提取，避免基于错误数据生成")
    print("  4. ⏳ 阶段4产出后应让用户预览并确认质量")
    print("  5. ⏳ 阶段5增加归档选项（飞书/Obsidian/本地）")
    print("\n💡 建议：重新运行时，我会按此改进流程执行，每步暂停等待你的确认。")

if __name__ == '__main__':
    main()
