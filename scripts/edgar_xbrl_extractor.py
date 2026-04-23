#!/usr/bin/env python3
"""
SEC EDGAR XBRL 财务数据提取。
支持多年度 10-K 文件，输出 JSON/CSV。
"""

import argparse
import csv
import json
import os
import sys

try:
    sys.path.insert(0, '/usr/local/lib/python3.11/site-packages')
    import edgar
    HAS_EDGARTOOLS = True
except ImportError:
    HAS_EDGARTOOLS = False

USER_AGENT = "Qianding Research <qd-research@openclaw.ai>"
OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/downloads/{company}-reports/")


def ensure_edgartools():
    if not HAS_EDGARTOOLS:
        print("错误: 需要安装 edgartools — pip install edgartools", file=sys.stderr)
        sys.exit(1)
    edgar.set_identity(USER_AGENT)


def extract_financials(ticker, years=1, output_csv=None, output_json=None, section=None, download=False):
    ensure_edgartools()
    try:
        company = edgar.Company(ticker)
    except Exception as e:
        print(f"找不到公司: {ticker} ({e})", file=sys.stderr)
        sys.exit(1)

    filings = company.get_filings(form='10-K')
    filing_list = list(filings)[:years]

    if not filing_list:
        print("未找到 10-K 文件")
        return {}

    all_data = {}
    for filing in filing_list:
        fy = filing.period_of_report or filing.filing_date
        filing_data = {
            "company": company.name, "ticker": ticker,
            "cik": str(company.cik), "fiscal_year": fy,
            "filing_date": filing.filing_date, "form": filing.form,
            "accession_no": filing.accession_no, "url": filing.url,
        }

        if download:
            out_dir = OUTPUT_DIR.format(company=ticker.lower().replace("-", "_"))
            os.makedirs(out_dir, exist_ok=True)
            try:
                filing.save(out_dir)
            except Exception:
                pass

        try:
            xbrl = filing.xbrl()
            if xbrl:
                for stmt_accessor in ['income_statement', 'balance_sheet', 'cashflow_statement']:
                    try:
                        stmt = getattr(xbrl, stmt_accessor)()
                        if stmt:
                            df = stmt.to_dataframe()
                            key = stmt_accessor.replace('_', ' ').title()
                            filing_data[key] = df.to_dict('records')
                    except Exception:
                        pass
            else:
                try:
                    text = filing.text
                    if text:
                        filing_data["full_text"] = text[:5000]
                except Exception:
                    pass
        except Exception:
            try:
                text = filing.text
                if text:
                    filing_data["full_text"] = text[:5000]
            except:
                pass

        if section:
            try:
                sections = filing.sections
                if sections and section in sections:
                    filing_data[f"section_{section}"] = sections[section]
            except Exception:
                pass

        all_data[fy] = filing_data

    if output_json:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"已保存 JSON: {output_json}")

    if output_csv:
        rows = []
        for fy, data in all_data.items():
            row = {"fiscal_year": fy, "filing_date": data.get("filing_date", ""),
                   "accession_no": data.get("accession_no", ""), "url": data.get("url", "")}
            for stmt_key in ['Income Statement', 'Balance Sheet', 'Cashflow Statement']:
                stmt_data = data.get(stmt_key, [])
                if isinstance(stmt_data, list):
                    for item in stmt_data:
                        label = str(item.get('label', ''))
                        for k, v in item.items():
                            if k not in ('label', 'concept', 'taxonomy', 'level', 'units') and v is not None:
                                col_name = f"{stmt_key[:3]}_{label}_{k}".replace(" ", "_")[:50]
                                row[col_name] = v
            rows.append(row)

        if rows:
            fieldnames = list(rows[0].keys())
            with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(rows)
            print(f"已保存 CSV: {output_csv}")

    return all_data


def main():
    parser = argparse.ArgumentParser(description="SEC EDGAR XBRL 财务数据提取")
    parser.add_argument("ticker", help="股票代码（如 ECL、AAPL）")
    parser.add_argument("--years", "-n", type=int, default=1, help="获取最近 N 年 10-K（默认1）")
    parser.add_argument("--download", "-d", action="store_true", help="同时下载原始文件")
    parser.add_argument("--section", "-s", type=str, help="提取特定 section（如 7 = MD&A）")
    parser.add_argument("--csv", action="store_true", help="输出 CSV")
    parser.add_argument("--json", "-j", action="store_true", help="输出 JSON")
    parser.add_argument("--output", "-o", help="输出文件路径")
    args = parser.parse_args()

    output_json = args.output if args.output and args.json else (args.output if args.json else None)
    output_csv = args.output if args.output and args.csv else (args.output if args.csv else None)

    extract_financials(
        ticker=args.ticker, years=args.years,
        output_csv=output_csv, output_json=output_json,
        section=args.section, download=args.download,
    )


if __name__ == "__main__":
    main()
