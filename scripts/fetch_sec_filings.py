#!/usr/bin/env python3
"""
SEC EDGAR 文件查询（信号分类）。
支持按公司、表单类型、时间范围检索，自动标记高/中/低信号优先级。
"""

import argparse
import gzip
import json
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta, timezone

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
USER_AGENT = "Qianding-Research qd-research@openclaw.ai"
REQUEST_DELAY = 0.15

HIGH_SIGNAL_ITEMS = {
    "1.01": "签署重大协议", "1.02": "终止重大协议",
    "2.01": "完成资产收购/处置", "2.05": "退出/处置成本",
    "4.02": "不再依赖此前财报（红旗）", "5.01": "控制权变更",
    "5.02": "董事/高管变动",
}
MEDIUM_SIGNAL_ITEMS = {
    "2.02": "经营业绩与财务状况", "2.03": "新增直接财务义务",
    "3.01": "退市通知", "7.01": "Regulation FD 披露",
}

CIK_SUFFIX_RE = re.compile(r"\s*\(CIK\s+\d+\)\s*$", re.IGNORECASE)


def fetch_filings(query, form_type=None, hours=48, max_results=20, raw_query=False):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(hours=hours)
    params = {
        "dateRange": "custom",
        "startdt": start_date.strftime("%Y-%m-%d"),
        "enddt": end_date.strftime("%Y-%m-%d"),
        "from": "0",
        "size": str(min(max_results, 100)),
    }
    if raw_query:
        params["q"] = f'"{query}"'
    else:
        params["entityName"] = query
    if form_type:
        params["forms"] = form_type

    url = f"{EDGAR_SEARCH_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/json",
    })

    def _read(resp):
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8"))

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return _read(resp)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            time.sleep(2)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return _read(resp)
        raise


def parse_filings(data):
    hits = data.get("hits", {}).get("hits", [])
    filings = []
    for hit in hits:
        src = hit.get("_source", {})
        hit_id = hit.get("_id", "")
        display_names = src.get("display_names", [])
        entity_name = CIK_SUFFIX_RE.sub("", display_names[-1]).strip() if display_names else "Unknown"
        form = src.get("root_form") or src.get("file_type") or "Unknown"
        file_date = src.get("file_date", "")
        file_desc = src.get("file_description", "")
        adsh = src.get("adsh", "")
        if not adsh and ":" in hit_id:
            adsh = hit_id.split(":")[0]
        ciks = src.get("ciks", [])
        items_list = re.findall(r'\b(\d+\.\d{2})\b', file_desc) if form == "8-K" and file_desc else []

        signal = "LOW"
        if form == "8-K":
            for item in items_list:
                if item in HIGH_SIGNAL_ITEMS:
                    signal = "HIGH"; break
                if item in MEDIUM_SIGNAL_ITEMS and signal != "HIGH":
                    signal = "MEDIUM"
        elif form in ("S-1", "S-1/A", "425", "SC 13D"):
            signal = "HIGH"
        elif form in ("10-K", "10-Q"):
            signal = "MEDIUM"

        filing_url = ""
        if adsh and ciks:
            clean_adsh = adsh.replace("-", "")
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{ciks[0]}/{clean_adsh}/{adsh}-index.htm"

        filings.append({
            "entity": entity_name, "form": form, "date": file_date,
            "description": file_desc, "signal": signal,
            "items": items_list, "url": filing_url, "ciks": ciks,
            "adsh": adsh,
        })
    return filings


def get_annual_report_link(company_name, years_back=5):
    hours = years_back * 365 * 24
    try:
        data = fetch_filings(company_name, form_type="10-K", hours=hours, max_results=20)
    except Exception as e:
        print(f"EDGAR 查询失败: {e}", file=sys.stderr)
        return []

    filings = parse_filings(data)
    filings.sort(key=lambda f: f["date"], reverse=True)

    results = []
    for f in filings:
        if f["adsh"] and f["ciks"]:
            clean = f["adsh"].replace("-", "")
            index_url = f["url"]
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{f['ciks'][0]}/{clean}"
            results.append({
                "year": f["date"][:4], "filing_date": f["date"],
                "entity": f["entity"], "index_url": index_url,
                "documents_url": doc_url,
            })
    return results


def main():
    parser = argparse.ArgumentParser(description="SEC EDGAR 文件查询")
    parser.add_argument("company", help="公司名称或股票代码")
    parser.add_argument("--form-type", type=str, help="文件类型 (8-K, 10-K, 10-Q)")
    parser.add_argument("--hours", type=int, default=48, help="回溯时间（小时）")
    parser.add_argument("--query", action="store_true", help="全文搜索模式")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--annual-reports", "-a", action="store_true", help="获取年报链接（过去5年）")
    parser.add_argument("--max-results", type=int, default=20)
    args = parser.parse_args()

    if args.annual_reports:
        reports = get_annual_report_link(args.company, years_back=5)
        if args.json:
            print(json.dumps(reports, indent=2))
        else:
            if not reports:
                print(f"未找到 {args.company} 的 10-K 年报")
            else:
                print(f"\n{'='*60}")
                print(f" {args.company} — 10-K 年报链接")
                print(f"{'='*60}\n")
                for r in reports:
                    print(f"  📄 FY {r['year']} (filed {r['filing_date']})")
                    print(f"     Index: {r['index_url']}")
                    print(f"     Docs:  {r['documents_url']}")
                    print()
        return

    try:
        data = fetch_filings(args.company, form_type=args.form_type, hours=args.hours,
                             max_results=args.max_results, raw_query=args.query)
    except Exception as e:
        print(f"查询失败: {e}", file=sys.stderr)
        sys.exit(1)

    filings = parse_filings(data)
    filings.sort(key=lambda f: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(f["signal"], 3), f["date"]), reverse=False)
    from itertools import groupby
    sorted_f = []
    for _, group in groupby(filings, key=lambda f: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(f["signal"], 3)):
        chunk = list(group)
        chunk.sort(key=lambda f: f["date"], reverse=True)
        sorted_f.extend(chunk)

    if args.json:
        print(json.dumps(sorted_f, indent=2, ensure_ascii=False))
    else:
        if not sorted_f:
            print(f"过去 {args.hours} 小时内未找到 {args.company} 的文件")
        else:
            for f in sorted_f:
                emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "⚪"}.get(f["signal"], "⚪")
                print(f"{emoji} [{f['form']}] {f['entity']} — {f['date']}")
                if f.get("items"):
                    items_desc = ", ".join(HIGH_SIGNAL_ITEMS.get(i, MEDIUM_SIGNAL_ITEMS.get(i, i)) for i in f["items"])
                    print(f"   Items: {items_desc}")
                if f.get("description"):
                    print(f"   {f['description']}")
                if f.get("url"):
                    print(f"   🔗 {f['url']}")
                print()


if __name__ == "__main__":
    main()
