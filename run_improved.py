#!/usr/bin/env python3
"""
qd-company-research 通用入口。

当前职责：
1. 确认目标公司身份与研究目录。
2. 检查已有六路研究文件和 cognitive 文件。
3. 调用 merge_research.py 生成阶段性 Review。
4. 调用 extract_mental_models.py 生成公司认知 Skill。

不负责自动采集资料、生成 Web Report、写入飞书或 Obsidian。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_DIR = Path(__file__).resolve().parent
DEFAULT_RESEARCH_DIR = REPO_DIR / "output"

STREAMS = {
    "financials": "A 财务",
    "business": "B 业务",
    "strategy": "C 战略",
    "stream_D": "D 领导思维",
    "stream_E": "E 批判视角",
    "stream_F": "F 文化符号",
}


def print_header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def confirm(prompt: str, assume_yes: bool = False) -> bool:
    if assume_yes:
        print(f"{prompt} yes")
        return True
    response = input(f"{prompt} (y/n): ").strip().lower()
    return response in {"y", "yes", "是"}


def run_command(args: list[str]) -> int:
    print(f"\n$ {' '.join(args)}")
    sys.stdout.flush()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(args, cwd=REPO_DIR, env=env)
    return completed.returncode


def expected_files(company: str, research_dir: Path) -> tuple[list[Path], list[Path]]:
    raw_files = [research_dir / f"{company}_{key}.md" for key in STREAMS]
    cognitive_files = [research_dir / f"{company}_{key}_cognitive.md" for key in STREAMS]
    return raw_files, cognitive_files


def show_file_status(company: str, research_dir: Path) -> tuple[list[Path], list[Path]]:
    raw_files, cognitive_files = expected_files(company, research_dir)
    missing_raw = [path for path in raw_files if not path.exists()]
    missing_cognitive = [path for path in cognitive_files if not path.exists()]

    print_header("研究文件检查")
    for key, label in STREAMS.items():
        raw_path = research_dir / f"{company}_{key}.md"
        cog_path = research_dir / f"{company}_{key}_cognitive.md"
        raw_status = "OK" if raw_path.exists() else "MISSING"
        cog_status = "OK" if cog_path.exists() else "MISSING"
        print(f"{label:<10} raw={raw_status:<7} cognitive={cog_status:<7}")

    return missing_raw, missing_cognitive


def show_identity(args: argparse.Namespace, research_dir: Path) -> None:
    print_header("身份确认")
    print(f"公司标识: {args.company}")
    print(f"公司全称: {args.full_name or '未提供'}")
    print(f"股票代码/上市地: {args.ticker or '未提供'}")
    print(f"业务范围: {args.scope or '未提供'}")
    print(f"研究目录: {research_dir}")
    print("\n未提供的信息不会被自动猜测；后续输出只基于研究目录中的文件。")


def main() -> int:
    parser = argparse.ArgumentParser(description="qd-company-research 通用执行入口")
    parser.add_argument("company", help="公司文件名前缀，例如 apple 或 kujiale")
    parser.add_argument("--full-name", help="公司全称，用于人工确认")
    parser.add_argument("--ticker", help="股票代码/上市地，用于人工确认")
    parser.add_argument("--scope", help="研究范围，用于人工确认")
    parser.add_argument(
        "--research-dir",
        type=Path,
        default=DEFAULT_RESEARCH_DIR,
        help="研究文件目录，默认使用仓库 output/",
    )
    parser.add_argument("--output", type=Path, help="生成的 skill 文件路径")
    parser.add_argument("--yes", action="store_true", help="跳过交互确认")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="允许缺失部分研究流，仍尝试生成阶段性产物",
    )
    parser.add_argument(
        "--review-only",
        action="store_true",
        help="只生成 Review，不进入认知提取",
    )
    args = parser.parse_args()

    research_dir = args.research_dir.expanduser().resolve()
    output_path = (args.output or research_dir / f"{args.company}_skill.md").expanduser().resolve()

    if not research_dir.exists():
        print(f"研究目录不存在，已创建: {research_dir}")
        research_dir.mkdir(parents=True, exist_ok=True)

    show_identity(args, research_dir)
    if not confirm("以上身份和目录是否确认？", args.yes):
        print("已停止。请补充公司信息或修正研究目录后重试。")
        return 1

    missing_raw, missing_cognitive = show_file_status(args.company, research_dir)
    if missing_raw:
        print("\n缺失原始研究文件:")
        for path in missing_raw:
            print(f"  - {path.name}")
    if missing_cognitive:
        print("\n缺失认知提取文件:")
        for path in missing_cognitive:
            print(f"  - {path.name}")

    if (missing_raw or missing_cognitive) and not args.allow_missing:
        print("\n文件不齐，默认不继续生成最终 Skill。")
        print("补齐文件后重试，或使用 --allow-missing 生成阶段性产物。")
        return 1

    print_header("阶段性 Review")
    review_code = run_command([
        sys.executable,
        str(REPO_DIR / "scripts" / "merge_research.py"),
        str(research_dir),
        "--company",
        args.company,
    ])
    if review_code != 0:
        return review_code

    if args.review_only:
        print("\nReview-only 模式完成。")
        return 0

    if not confirm("是否进入认知提取并生成 Skill？", args.yes):
        print("已停止在 Review 阶段。")
        return 0

    print_header("认知提取")
    return run_command([
        sys.executable,
        str(REPO_DIR / "scripts" / "extract_mental_models.py"),
        str(research_dir),
        "--company",
        args.company,
        "--output",
        str(output_path),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
