#!/usr/bin/env python3
"""
前置检查：Excel 一级费用科目是否已存在于系统

用途：
- 在执行 Step2/Step3 前先做硬性拦截
- 若一级科目缺失，明确提示“不可继续执行”

用法：
  python precheck_primary_subjects.py --excel /path/to/批量表_2.xlsx
"""

import argparse
import json
from pathlib import Path

import pandas as pd
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://cst.uf-tree.com"
CDP_URL = "http://127.0.0.1:9223"


def get_auth_from_browser():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "uf-tree.com" in pg.url:
                    page = pg
                    break
            if page:
                break

        if not page:
            browser.close()
            raise RuntimeError("未找到已登录财税通页面（请确认 Edge 9223 + 已登录）")

        auth = page.evaluate(
            """() => {
              const v = localStorage.getItem('vuex');
              if (!v) return null;
              try {
                const d = JSON.parse(v);
                return {
                  token: d.user?.token,
                  companyId: d.user?.company?.id,
                  userId: d.user?.id
                };
              } catch (e) {
                return null;
              }
            }"""
        )
        browser.close()

    if not auth or not auth.get("token"):
        raise RuntimeError("获取 token 失败（请重新登录财税通）")
    return auth


def read_sheet2_primary_subjects(excel_path: Path):
    # 自动识别表头行（包含“是否执行”）
    raw = pd.read_excel(excel_path, sheet_name="02_费用科目配置", header=None)
    header_row = None
    for i, row in raw.iterrows():
        if any(str(v).strip() == "是否执行" for v in row.values):
            header_row = i
            break

    if header_row is None:
        raise RuntimeError("未在 Sheet2 找到表头（是否执行）")

    df = pd.read_excel(excel_path, sheet_name="02_费用科目配置", header=header_row)

    for col in ["一级费用科目", "是否执行"]:
        if col not in df.columns:
            raise RuntimeError(f"Sheet2 缺少必需列: {col}")

    # 处理合并单元格导致的空值
    df["一级费用科目"] = (
        df["一级费用科目"]
        .astype(str)
        .str.strip()
        .replace({"": None, "nan": None, "None": None})
        .ffill()
    )

    df_exec = df[df["是否执行"].astype(str).str.strip() == "是"].copy()
    subjects = sorted({str(x).strip() for x in df_exec["一级费用科目"].dropna().tolist() if str(x).strip()})

    return subjects, len(df_exec)


def fetch_system_primary_subjects(token: str, company_id: int):
    resp = requests.get(
        f"{BASE_URL}/api/bill/feeTemplate/queryFeeTemplate",
        headers={"x-token": token},
        params={"companyId": company_id, "status": 1, "pageSize": 1000},
        timeout=20,
    )
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"queryFeeTemplate 失败: {data.get('message')}")

    primary = sorted(
        {
            t.get("name")
            for t in data.get("result", [])
            if t.get("parentId") == -1 and t.get("name")
        }
    )
    return primary


def main():
    parser = argparse.ArgumentParser(description="前置检查：一级费用科目是否存在")
    parser.add_argument("--excel", required=True, help="三步闭环 Excel 路径（含 Sheet2）")
    parser.add_argument("--out", default="", help="输出 JSON 报告路径（可选）")
    args = parser.parse_args()

    excel_path = Path(args.excel)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel 不存在: {excel_path}")

    auth = get_auth_from_browser()
    token = auth["token"]
    company_id = auth["companyId"]

    excel_subjects, rows = read_sheet2_primary_subjects(excel_path)
    system_subjects = fetch_system_primary_subjects(token, company_id)

    system_set = set(system_subjects)
    missing = [s for s in excel_subjects if s not in system_set]

    report = {
        "companyId": company_id,
        "excelPath": str(excel_path),
        "sheet2RowsToExecute": rows,
        "excelPrimarySubjects": excel_subjects,
        "systemPrimarySubjectsCount": len(system_subjects),
        "missingPrimarySubjects": missing,
        "canContinue": len(missing) == 0,
    }

    print("=" * 72)
    print("前置检查：一级费用科目存在性")
    print("=" * 72)
    print(f"公司ID: {company_id}")
    print(f"Sheet2 待执行行数: {rows}")
    print(f"Excel 一级科目数: {len(excel_subjects)}")
    print(f"系统一级科目数: {len(system_subjects)}")

    if missing:
        print("\n❌ 检查失败：以下一级科目尚未在系统中创建：")
        for i, name in enumerate(missing, 1):
            print(f"  {i}. {name}")
        print("\n⛔ 请先在系统中创建以上一级科目，再执行 Step2/Step3。")
    else:
        print("\n✅ 检查通过：Excel 中一级科目均已存在，可继续执行 Step2/Step3。")

    out_path = Path(args.out) if args.out else excel_path.parent / "precheck_primary_subjects.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 报告已保存: {out_path}")

    # 返回码用于自动化拦截
    raise SystemExit(0 if report["canContinue"] else 2)


if __name__ == "__main__":
    main()
