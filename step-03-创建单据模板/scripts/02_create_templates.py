#!/usr/bin/env python3
"""
单据模板批量创建脚本 - 通用版
功能: 读取Excel并批量创建单据模板（分组+模板+可见范围）

用法:
    python 02_create_templates.py --excel ./example_templates.xlsx [--sheet "正式填写表"]

前置条件:
    1. Edge浏览器已启动调试模式（端口9222）
    2. 已登录财税通系统
    3. 已运行 get_token.py 获取Token
"""

import requests
import json
import time
import pandas as pd
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# ==================== 配置区域 ====================
BASE_URL = "https://cst.uf-tree.com"
COMPANY_ID = 7792

# Token从配置文件加载（相对路径，可在任何机器运行）
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "config.json"
# ==================================================

def load_token():
    """从配置文件加载Token"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("token", "")
    return ""

def get_headers(token):
    """生成请求头"""
    return {
        "x-token": token,
        "Content-Type": "application/json"
    }

# ==================== 查询接口 ====================

def get_groups(token):
    """查询分组树"""
    url = f"{BASE_URL}/api/bill/template/queryTemplateTree"
    params = {"companyId": COMPANY_ID, "t": int(time.time() * 1000)}
    resp = requests.get(url, headers=get_headers(token), params=params, timeout=10)
    data = resp.json()
    if data.get("code") == 200:
        return {g["name"]: g["id"] for g in data.get("result", [])}
    return {}

def get_roles(token):
    """查询角色树（默认排除费用角色组，仅返回可用于可见范围的角色）"""
    url = f"{BASE_URL}/api/member/role/get/tree"
    params = {"companyId": COMPANY_ID}
    resp = requests.get(url, headers=get_headers(token), params=params, timeout=10)
    data = resp.json()
    roles = {}
    if data.get("code") == 200:
        for category in data.get("result", []):
            category_name = category.get("name", "")
            # 费用角色组不参与单据模板可见范围对象选择
            if "费用角色" in category_name:
                continue
            for role in category.get("children", []):
                roles[role["name"]] = role["id"]
    return roles

def get_users(token):
    """查询员工列表"""
    url = f"{BASE_URL}/api/member/department/queryCompany"
    payload = {"companyId": COMPANY_ID}
    resp = requests.post(url, headers=get_headers(token), json=payload, timeout=10)
    data = resp.json()
    if data.get("code") == 200:
        return {u["nickName"]: u["id"] for u in data.get("result", {}).get("users", [])}
    return {}

def get_departments(token):
    """查询部门列表"""
    url = f"{BASE_URL}/api/member/department/queryDepartments"
    params = {"companyId": COMPANY_ID}
    resp = requests.get(url, headers=get_headers(token), params=params, timeout=10)
    data = resp.json()
    if data.get("code") == 200:
        return {d["title"]: d["id"] for d in data.get("result", [])}
    return {}

# ==================== 创建接口 ====================

def create_group(token, name):
    """创建分组"""
    url = f"{BASE_URL}/api/bill/template/createTemplateGroup"
    payload = {"name": name, "companyId": COMPANY_ID}
    resp = requests.post(url, headers=get_headers(token), json=payload, timeout=10)
    return resp.json()

def create_template(token, payload):
    """创建模板"""
    url = f"{BASE_URL}/api/bill/template/createTemplate"
    resp = requests.post(url, headers=get_headers(token), json=payload, timeout=10)
    return resp.json()


def with_unique_suffix(name, batch_tag="B1"):
    ts = datetime.now().strftime('%H%M%S')
    return f"{name}_{batch_tag}_{ts}"

# ==================== 主流程 ====================

def read_excel(excel_path, sheet_name="正式填写表"):
    """读取Excel文件"""
    try:
        # 先读取原始数据查找表头行
        df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

        header_row = None
        for idx, row in df_raw.iterrows():
            if '是否创建' in str(row.values):
                header_row = idx
                break

        if header_row is None:
            print("❌ 未找到表头行（应包含'是否创建'列）")
            return None

        # 使用正确的表头行重新读取
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row)
        return df
    except Exception as e:
        print(f"❌ Excel读取失败: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="批量创建单据模板")
    parser.add_argument("--excel", required=True, help="Excel文件路径")
    parser.add_argument("--sheet", default="正式填写表", help="Sheet名称")
    parser.add_argument("--batch-tag", default="B1", help="名称防重后缀标签，如 B1/B2")
    args = parser.parse_args()

    print("=" * 70)
    print("🚀 单据模板批量创建")
    print("=" * 70)

    # 1. 加载Token
    token = load_token()
    if not token:
        print("\n❌ 未找到Token，请先运行: python3 get_token.py")
        return
    print(f"\n✅ Token已加载: {token[:30]}...")

    # 2. 检查Excel文件
    excel_path = Path(args.excel)
    if not excel_path.exists():
        print(f"\n❌ Excel文件不存在: {excel_path}")
        print("请确认文件路径正确，或使用相对路径如: ./example_templates.xlsx")
        return

    # 3. 读取Excel
    print(f"\n📖 读取Excel: {excel_path}")
    df = read_excel(excel_path, args.sheet)
    if df is None:
        return

    if '是否创建' not in df.columns:
        print(f"❌ Excel格式错误: 未找到'是否创建'列")
        print(f"   可用列: {list(df.columns)}")
        return

    df_create = df[df["是否创建"] == "是"].copy()
    print(f"   待创建模板数: {len(df_create)}")

    if len(df_create) == 0:
        print("⚠️ 没有需要创建的数据（'是否创建'列没有标记为'是'的行）")
        return

    # 4. 查询基础数据
    print("\n🔍 查询基础数据...")
    groups = get_groups(token)
    print(f"   分组: {len(groups)} 个")

    roles = get_roles(token)
    print(f"   角色: {len(roles)} 个")

    users = get_users(token)
    print(f"   员工: {len(users)} 个")

    departments = get_departments(token)
    print(f"   部门: {len(departments)} 个")

    # 5. type映射
    type_map = {
        "报销单": "EXPENSE",
        "借款单": "LOAN",
        "申请单": "REQUISITION",
        "批量付款单": "PAYMENT",
        "计提单": "ACCRUAL"
    }

    # 6. 处理每一行
    results = []

    for idx, row in df_create.iterrows():
        print(f"\n{'='*70}")
        print(f"📝 处理 [{idx+1}/{len(df_create)}]: {row['单据模板名称']}")
        print(f"{'='*70}")

        # 6.1 处理分组
        group_name = row["单据分组（一级目录）"]
        if group_name in groups:
            group_id = groups[group_name]
            print(f"   ✅ 分组已存在: {group_name} (ID: {group_id})")
        else:
            print(f"   ⏳ 创建分组: {group_name}")
            result = create_group(token, group_name)
            if result.get("code") == 200:
                print(f"   ✅ 分组创建成功")
                time.sleep(0.5)  # 等待同步
                groups = get_groups(token)
                group_id = groups.get(group_name)
                if group_id:
                    print(f"   ✅ 获取分组ID: {group_id}")
                else:
                    print(f"   ⚠️ 无法获取新分组ID")
                    results.append({
                        "name": row["单据模板名称"],
                        "status": "失败",
                        "error": "无法获取分组ID"
                    })
                    continue
            else:
                print(f"   ❌ 分组创建失败: {result.get('message')}")
                results.append({
                    "name": row["单据模板名称"],
                    "status": "失败",
                    "error": "分组创建失败"
                })
                continue

        # 6.2 type转换
        template_type = type_map.get(row["单据大类（二级目录）"], "EXPENSE")

        # 6.3 处理可见范围
        visible_type = row["可见范围类型"]
        visible_target = row["可见范围对象"]

        role_ids = []
        department_ids = []
        user_ids = []

        if visible_type == "角色":
            # 支持多值：中文逗号/英文逗号/顿号/分号
            role_names = [x.strip() for x in str(visible_target).replace('，', ',').replace('、', ',').replace(';', ',').replace('；', ',').split(',') if x.strip()]
            for role_name in role_names:
                if role_name in roles:
                    role_ids.append(roles[role_name])
                    print(f"   ✅ 角色匹配: {role_name} -> ID: {roles[role_name]}")
                else:
                    print(f"   ⚠️ 角色未找到: {role_name}")
            if not role_ids:
                print(f"      可用角色: {list(roles.keys())[:8]}...")

        elif visible_type == "部门":
            # 支持多值：中文逗号/英文逗号/顿号/分号
            dep_names = [x.strip() for x in str(visible_target).replace('，', ',').replace('、', ',').replace(';', ',').replace('；', ',').split(',') if x.strip()]
            for dep_name in dep_names:
                if dep_name in departments:
                    department_ids.append(departments[dep_name])
                    print(f"   ✅ 部门匹配: {dep_name} -> ID: {departments[dep_name]}")
                else:
                    print(f"   ⚠️ 部门未找到: {dep_name}")
            if not department_ids:
                print(f"      可用部门: {list(departments.keys())[:8]}...")

        elif visible_type == "员工":
            # 支持多值：中文逗号/英文逗号/顿号/分号
            employee_names = [name.strip() for name in str(visible_target).replace('，', ',').replace('、', ',').replace(';', ',').replace('；', ',').split(',') if name.strip()]
            for emp_name in employee_names:
                if emp_name in users:
                    user_ids.append(users[emp_name])
                    print(f"   ✅ 员工匹配: {emp_name} -> ID: {users[emp_name]}")
                else:
                    print(f"   ⚠️ 员工未找到: {emp_name}")

        # 6.4 组装Payload
        payload = {
            "applyRelateFlag": True,
            "applyRelateNecessary": False,
            "businessType": "PRIVATE",
            "companyId": COMPANY_ID,
            "componentJson": [],
            "departmentIds": department_ids,
            "feeIds": [],
            "feeScopeFlag": False,
            "groupId": group_id,
            "icon": "md-pricetag",
            "iconColor": "#4c7cc3",
            "loanIds": [],
            "name": row["单据模板名称"],
            "payFlag": True,
            "requestScope": False,
            "requisitionIds": [],
            "roleIds": role_ids,
            "status": "ACTIVE",
            "type": template_type,
            "userIds": user_ids,
            "userScopeFlag": True,
            "workFlowId": 12791
        }

        # 申请单特殊处理
        if template_type == "REQUISITION":
            payload["applyContentType"] = "TEXT"

        print(f"   📦 Payload组装完成")

        # 6.5 发送创建请求
        print(f"   📡 发送createTemplate请求...")
        result = create_template(token, payload)

        if result.get("code") == 200 and result.get("success"):
            template_id = result.get("result", {}).get("id")
            print(f"   ✅ 模板创建成功! ID: {template_id}")
            results.append({
                "name": row["单据模板名称"],
                "status": "成功",
                "id": template_id
            })
        else:
            error_msg = result.get("message", "未知错误")
            # 名称重复时自动加后缀重试一次
            if "名称重复" in str(error_msg):
                new_name = with_unique_suffix(str(payload.get("name", "模板")), args.batch_tag)
                payload["name"] = new_name
                print(f"   ♻️ 检测到重名，改名重试: {new_name}")
                retry = create_template(token, payload)
                if retry.get("code") == 200 and retry.get("success"):
                    template_id = retry.get("result", {}).get("id")
                    print(f"   ✅ 重试成功! ID: {template_id}")
                    results.append({
                        "name": new_name,
                        "status": "成功",
                        "id": template_id,
                        "retry": True
                    })
                    continue
                else:
                    error_msg = retry.get("message", error_msg)

            print(f"   ❌ 创建失败: {error_msg}")
            results.append({
                "name": row["单据模板名称"],
                "status": "失败",
                "error": error_msg
            })

    # 7. 输出汇总
    print(f"\n{'='*70}")
    print("📊 执行结果汇总")
    print(f"{'='*70}")

    success_count = sum(1 for r in results if r["status"] == "成功")
    fail_count = len(results) - success_count

    print(f"总计: {len(results)} 个模板")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print()

    for r in results:
        emoji = "✅" if r["status"] == "成功" else "❌"
        print(f"{emoji} {r['name']}: {r['status']}")
        if "id" in r:
            print(f"      模板ID: {r['id']}")
        if "error" in r:
            print(f"      错误: {r['error']}")

    print(f"\n{'='*70}")

    # 返回状态码供外部判断
    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
