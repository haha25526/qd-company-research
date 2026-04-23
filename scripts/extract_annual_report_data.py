#!/usr/bin/env python3
"""
从年报 PDF 提取结构化财务数据（财务亮点、业务分部、文本提及）。
"""

import argparse
import csv
import os
import re
import sys

try:
    import pdfplumber
except ImportError:
    print("需要安装 pdfplumber: pip install pdfplumber")
    sys.exit(1)


def extract_text(pdf_path: str) -> str:
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            txt = page.extract_text()
            if txt:
                parts.append(f"--- Page {i+1} ---\n{txt}")
    return "\n".join(parts)


def extract_tables(pdf_path: str) -> list:
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            for j, table in enumerate(page.extract_tables()):
                tables.append({"page": i + 1, "table_index": j, "data": table})
    return tables


def find_financial_highlights(tables: list) -> list:
    results = []
    fin_keywords = [r'net sales', r'revenue', r'operating income', r'net income',
                    r'operating cash flow', r'free cash flow', r'diluted eps',
                    r'gross profit', r'total revenue', r'segment',
                    r'营业收入', r'净利润', r'营业利润', r'经营现金流']
    for t in tables:
        data = t["data"]
        if not data or len(data) < 2:
            continue
        header = data[0]
        year_count = sum(1 for c in (header or []) if c and re.search(r'\b(20|19)\d{2}\b', str(c)))
        if year_count >= 2:
            for row in data[1:]:
                row_text = ' '.join(str(c or '') for c in (row or []))
                if any(re.search(kw, row_text, re.IGNORECASE) for kw in fin_keywords):
                    results.append({"page": t["page"], "header": header, "row": row})
                    break
    return results


def extract_segment_data(tables: list) -> list:
    results = []
    seg_keywords = [r'segment', r'division', r'business', r'net sales', r'分部', r'业务']
    for t in tables:
        data = t["data"]
        if not data or len(data) < 3:
            continue
        header_text = ' '.join(str(c or '') for c in (data[0] or []))
        if any(re.search(kw, header_text, re.IGNORECASE) for kw in seg_keywords):
            results.append({"page": t["page"], "header": data[0], "rows": data[1:]})
    return results


def find_revenue_mentions(text: str, limit: int = 20) -> list:
    patterns = [r'\$\s?([\d,]+\.?\d*)\s*(?:million|billion)', r'([\d,]+\.?\d*)\s*(?:亿美元|万元|亿元|百万)']
    findings = []
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            findings.append({"match": m.group(0), "value": m.group(1)})
            if len(findings) >= limit:
                break
    return findings


def save_csv(data: list, output_path: str):
    if not data:
        return
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
    print(f"已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="从年报 PDF 提取财务数据")
    parser.add_argument("pdf_path", help="年报 PDF 文件路径")
    parser.add_argument("--output", "-o", help="输出 CSV 路径")
    parser.add_argument("--mode", choices=["highlights", "segments", "text-search", "all"], default="all")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"文件不存在: {args.pdf_path}")
        sys.exit(1)

    if not args.output:
        base = os.path.splitext(args.pdf_path)[0]
        args.output = f"{base}_extracted.csv"

    print(f"处理: {args.pdf_path}")
    text = extract_text(args.pdf_path)
    tables = extract_tables(args.pdf_path)
    print(f"表格数: {len(tables)}")

    results = []
    if args.mode in ("highlights", "all"):
        for h in find_financial_highlights(tables):
            results.append({"type": "financial_highlight", **h, "source": args.pdf_path})
    if args.mode in ("segments", "all"):
        for s in extract_segment_data(tables):
            results.append({"type": "segment_data", **s, "source": args.pdf_path})
    if args.mode in ("text-search", "all"):
        for f in find_revenue_mentions(text):
            results.append({"type": "revenue_mention", **f})

    if results:
        save_csv(results, args.output)
    else:
        print("未找到财务数据，可能需要调整规则或手动检查。")


if __name__ == "__main__":
    main()
