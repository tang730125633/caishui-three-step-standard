#!/usr/bin/env python3
"""
前置检查：Step3 可见范围类目与对象一致性检查

规则：
1) 类目=角色 -> 对象必须是角色名（不能是员工/部门）
2) 类目=员工 -> 对象必须是员工昵称（不能是角色/部门）
3) 类目=部门 -> 对象必须是部门名（不能是角色/员工）

用法：
  python precheck_visibility_scope.py --excel /path/to/批量表_2.xlsx

退出码：
  0: 检查通过
  2: 检查失败（存在不匹配）
"""

import argparse
import json
from pathlib import Path

import pandas as pd
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://cst.uf-tree.com"
CDP_URL = "http://127.0.0.1:9223"


def parse_multi(v):
    if v is None:
        return []
    s = str(v).strip()
    if not s or s.lower() in ("nan", "none"):
        return []
    for ch in ["，", ",", "、", ";", "；", "|", "/"]:
        s = s.replace(ch, ",")
    return [x.strip() for x in s.split(",") if x.strip()]


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


def read_sheet3(excel_path: Path):
    raw = pd.read_excel(excel_path, sheet_name="03_单据表", header=None)
    header_row = None
    for i, row in raw.iterrows():
        if any(str(v).strip() == "是否创建" for v in row.values):
            header_row = i
            break
    if header_row is None:
        raise RuntimeError("未在 Sheet3 找到表头（是否创建）")

    df = pd.read_excel(excel_path, sheet_name="03_单据表", header=header_row)
    required = ["是否创建", "单据模板名称", "可见范围类型", "可见范围对象"]
    for c in required:
        if c not in df.columns:
            raise RuntimeError(f"Sheet3 缺少必需列: {c}")

    df_exec = df[df["是否创建"].astype(str).str.strip() == "是"].copy()
    return df_exec


def fetch_ref_sets(token: str, company_id: int):
    headers = {"x-token": token, "Content-Type": "application/json"}

    # 角色（排除费用角色组）
    role_tree = requests.get(
        f"{BASE_URL}/api/member/role/get/tree",
        headers=headers,
        params={"companyId": company_id},
        timeout=20,
    ).json().get("result", [])

    role_set = set()
    for cat in role_tree:
        cat_name = str(cat.get("name", ""))
        if "费用角色" in cat_name:
            continue
        for r in cat.get("children", []) or []:
            name = r.get("name")
            if name:
                role_set.add(name)

    # 员工
    users = requests.post(
        f"{BASE_URL}/api/member/department/queryCompany",
        headers=headers,
        json={"companyId": company_id},
        timeout=20,
    ).json().get("result", {}).get("users", [])
    user_set = {u.get("nickName") for u in users if u.get("nickName")}

    # 部门
    deps = requests.get(
        f"{BASE_URL}/api/member/department/queryDepartments",
        headers=headers,
        params={"companyId": company_id},
        timeout=20,
    ).json().get("result", [])
    dep_set = {d.get("title") for d in deps if d.get("title")}

    return role_set, user_set, dep_set


def classify_mismatch(vtype, obj, role_set, user_set, dep_set):
    """返回 (ok, reason)"""
    if vtype == "角色":
        if obj in role_set:
            return True, ""
        hints = []
        if obj in user_set:
            hints.append("该对象是员工")
        if obj in dep_set:
            hints.append("该对象是部门")
        return False, "角色类目未命中角色" + (f"（{'；'.join(hints)}）" if hints else "")

    if vtype == "员工":
        if obj in user_set:
            return True, ""
        hints = []
        if obj in role_set:
            hints.append("该对象是角色")
        if obj in dep_set:
            hints.append("该对象是部门")
        return False, "员工类目未命中员工" + (f"（{'；'.join(hints)}）" if hints else "")

    if vtype == "部门":
        if obj in dep_set:
            return True, ""
        hints = []
        if obj in role_set:
            hints.append("该对象是角色")
        if obj in user_set:
            hints.append("该对象是员工")
        return False, "部门类目未命中部门" + (f"（{'；'.join(hints)}）" if hints else "")

    return False, f"未知可见范围类型: {vtype}"


def main():
    parser = argparse.ArgumentParser(description="Step3 可见范围一致性检查")
    parser.add_argument("--excel", required=True, help="三步闭环 Excel 路径（含 Sheet3）")
    parser.add_argument("--out", default="", help="输出 JSON 报告路径（可选）")
    args = parser.parse_args()

    excel_path = Path(args.excel)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel 不存在: {excel_path}")

    auth = get_auth_from_browser()
    token = auth["token"]
    company_id = auth["companyId"]

    df = read_sheet3(excel_path)
    role_set, user_set, dep_set = fetch_ref_sets(token, company_id)

    failures = []
    pass_count = 0

    for idx, row in df.iterrows():
        row_no = int(idx + 1)
        name = str(row.get("单据模板名称", "")).strip()
        vtype = str(row.get("可见范围类型", "")).strip()
        objs = parse_multi(row.get("可见范围对象", ""))

        if not objs:
            failures.append({
                "row": row_no,
                "template": name,
                "visibleType": vtype,
                "object": "",
                "reason": "可见范围对象为空"
            })
            continue

        for obj in objs:
            ok, reason = classify_mismatch(vtype, obj, role_set, user_set, dep_set)
            if ok:
                pass_count += 1
            else:
                failures.append({
                    "row": row_no,
                    "template": name,
                    "visibleType": vtype,
                    "object": obj,
                    "reason": reason,
                })

    report = {
        "companyId": company_id,
        "excelPath": str(excel_path),
        "rowsToCreate": int(len(df)),
        "roleCount": len(role_set),
        "userCount": len(user_set),
        "departmentCount": len(dep_set),
        "passCount": pass_count,
        "failCount": len(failures),
        "failures": failures,
        "canContinue": len(failures) == 0,
    }

    print("=" * 72)
    print("前置检查：可见范围类目与对象一致性")
    print("=" * 72)
    print(f"公司ID: {company_id}")
    print(f"待创建模板行数: {len(df)}")
    print(f"角色数: {len(role_set)} | 员工数: {len(user_set)} | 部门数: {len(dep_set)}")

    if failures:
        print(f"\n❌ 检查失败：发现 {len(failures)} 个不匹配项")
        for i, f in enumerate(failures[:20], 1):
            print(f"  {i}. 行{f['row']} 模板[{f['template']}] {f['visibleType']} -> {f['object']} | {f['reason']}")
        if len(failures) > 20:
            print(f"  ... 其余 {len(failures)-20} 项见 JSON 报告")
        print("\n⛔ 请先修正 Excel 的可见范围类型/对象，再执行 Step3。")
    else:
        print("\n✅ 检查通过：可见范围类型与对象匹配正确，可继续 Step3。")

    out_path = Path(args.out) if args.out else excel_path.parent / "precheck_visibility_scope.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 报告已保存: {out_path}")

    raise SystemExit(0 if report["canContinue"] else 2)


if __name__ == "__main__":
    main()
