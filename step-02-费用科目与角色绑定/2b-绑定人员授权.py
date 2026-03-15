#!/usr/bin/env python3
"""
绑定人员授权 - Step 3b
功能: 将员工与单据角色进行绑定授权

前置条件:
    1. 必须先运行 3a-添加费用角色.py 创建角色组/子角色
    2. Edge浏览器已启动调试模式
    3. 已获取有效Token

用法:
    python 3b-绑定人员授权.py

    或指定配置文件:
    python 3b-绑定人员授权.py --config ./config.json

数据流程:
    1. 读取 费用科目配置表.xlsx（或 科目配置表_已更新.xlsx）
    2. 获取已创建的角色列表
    3. 获取员工列表（nickName -> userId）
    4. 根据Excel中的"适配人员"列，将员工ID与角色ID绑定
    5. 调用 API: /api/member/role/add/relation
"""

import requests
import json
import time
import pandas as pd
import os
import sys
import argparse
from pathlib import Path

# ==================== 配置区域 ====================
BASE_URL = "https://cst.uf-tree.com"
COMPANY_ID = 7792

# 默认配置文件路径
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
EXCEL_PATH = SCRIPT_DIR / "费用科目配置表.xlsx"
# ==================================================


def load_config(config_path):
    """加载配置文件"""
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_headers(token):
    """生成请求头"""
    return {
        "x-token": token,
        "Content-Type": "application/json"
    }


# ==================== 查询接口 ====================

def get_role_tree(token):
    """
    查询完整角色树
    返回: {角色名: 角色ID}
    """
    url = f"{BASE_URL}/api/member/role/get/tree"
    params = {"companyId": COMPANY_ID}

    try:
        resp = requests.get(url, headers=get_headers(token), params=params, timeout=10)
        data = resp.json()

        if data.get("code") == 200:
            roles = {}
            for category in data.get("result", []):
                # category: 职级/职务/费用角色组
                for role in category.get("children", []):
                    roles[role["name"]] = role["id"]
            return roles
        else:
            print(f"❌ 查询角色树失败: {data.get('message')}")
            return {}
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return {}


def get_users(token):
    """
    查询员工列表
    返回: {昵称: userId}
    """
    url = f"{BASE_URL}/api/member/department/queryCompany"
    payload = {"companyId": COMPANY_ID}

    try:
        resp = requests.post(url, headers=get_headers(token), json=payload, timeout=10)
        data = resp.json()

        if data.get("code") == 200:
            users = data.get("result", {}).get("users", [])
            return {u["nickName"]: u["id"] for u in users}
        else:
            print(f"❌ 查询员工列表失败: {data.get('message')}")
            return {}
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return {}


def get_fee_templates(token):
    """
    查询费用模板列表（用于关联）
    返回: {模板名: 模板ID}
    """
    url = f"{BASE_URL}/api/bill/feeTemplate/queryFeeTemplate"
    params = {"companyId": COMPANY_ID, "status": 0}

    try:
        resp = requests.get(url, headers=get_headers(token), params=params, timeout=10)
        data = resp.json()

        if data.get("code") == 200:
            templates = data.get("result", [])
            return {t["name"]: t["id"] for t in templates}
        else:
            return {}
    except Exception as e:
        print(f"❌ 查询费用模板失败: {e}")
        return {}


# ==================== 绑定接口 ====================

def bind_role_relation(token, role_id, user_ids, fee_template_ids=None):
    """
    绑定角色关系

    Args:
        role_id: 角色ID
        user_ids: 员工ID列表 [1, 2, 3]
        fee_template_ids: 费用模板ID列表（可选）

    API: POST /api/member/role/add/relation
    """
    url = f"{BASE_URL}/api/member/role/add/relation"

    payload = {
        "roleId": role_id,
        "userIds": user_ids,
        "companyId": COMPANY_ID
    }

    if fee_template_ids:
        payload["feeTemplateIds"] = fee_template_ids

    try:
        resp = requests.post(url, headers=get_headers(token), json=payload, timeout=10)
        data = resp.json()

        if data.get("code") == 200:
            return True, "绑定成功"
        else:
            return False, data.get("message", "未知错误")
    except Exception as e:
        return False, str(e)


# ==================== Excel 处理 ====================

def read_excel(excel_path):
    """
    读取费用科目配置表

    期望列:
    - 一级科目/二级科目
    - 单据类型（作为角色名）
    - 适配人员（逗号分隔的员工名）
    """
    try:
        print(f"📖 读取Excel: {excel_path}")

        # 尝试不同的sheet名称
        sheet_names = ["正式填写表", "Sheet1", "科目配置"]
        df = None

        for sheet in sheet_names:
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet)
                print(f"   成功读取Sheet: {sheet}")
                break
            except:
                continue

        if df is None:
            # 默认读取第一个sheet
            df = pd.read_excel(excel_path)
            print(f"   读取第一个Sheet")

        print(f"   数据行数: {len(df)}")
        print(f"   列名: {list(df.columns)}")

        return df

    except Exception as e:
        print(f"❌ Excel读取失败: {e}")
        return None


def parse_adapt_users(adapt_str):
    """
    解析适配人员字段
    支持: 顿号、逗号、分号分隔
    """
    if pd.isna(adapt_str):
        return []

    # 统一替换为逗号，然后分割
    adapt_str = str(adapt_str)
    adapt_str = adapt_str.replace("，", ",").replace("、", ",").replace("；", ";")

    users = [u.strip() for u in adapt_str.split(",") if u.strip()]
    return users


# ==================== 主流程 ====================

def main():
    parser = argparse.ArgumentParser(description="绑定人员授权")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="配置文件路径")
    parser.add_argument("--excel", default=str(EXCEL_PATH), help="Excel文件路径")
    args = parser.parse_args()

    print("=" * 70)
    print("🔗 绑定人员授权 - Step 3b")
    print("=" * 70)

    # 1. 加载Token
    config_path = Path(args.config)
    config = load_config(config_path)

    if not config or not config.get("token"):
        print(f"\n❌ 未找到Token，请先运行 get_token.py 获取Token")
        print(f"   配置文件: {config_path}")
        return 1

    token = config["token"]
    print(f"\n✅ Token已加载: {token[:30]}...")

    # 2. 读取Excel
    excel_path = Path(args.excel)
    if not excel_path.exists():
        print(f"\n❌ Excel文件不存在: {excel_path}")
        print(f"请确认文件路径正确")
        return 1

    df = read_excel(excel_path)
    if df is None:
        return 1

    # 3. 查询基础数据
    print("\n🔍 查询基础数据...")

    print("   查询角色树...")
    roles = get_role_tree(token)
    print(f"   找到 {len(roles)} 个角色")

    print("   查询员工列表...")
    users = get_users(token)
    print(f"   找到 {len(users)} 个员工")

    # 4. 处理每一行
    print("\n" + "=" * 70)
    print("📝 开始绑定人员授权")
    print("=" * 70)

    results = {
        "success": [],
        "failed": [],
        "skipped": []
    }

    # 查找关键列（模糊匹配）
    role_col = None
    user_col = None

    for col in df.columns:
        col_str = str(col).lower()
        if "单据" in col_str or "角色" in col_str or "类型" in col_str:
            role_col = col
        if "人员" in col_str or "适配" in col_str or "员工" in col_str:
            user_col = col

    if not role_col:
        print(f"⚠️ 未找到'单据类型'列，尝试使用第二列")
        role_col = df.columns[1] if len(df.columns) > 1 else None

    if not user_col:
        print(f"⚠️ 未找到'适配人员'列，尝试使用第三列")
        user_col = df.columns[2] if len(df.columns) > 2 else None

    print(f"\n使用列:")
    print(f"   角色列: {role_col}")
    print(f"   人员列: {user_col}")

    for idx, row in df.iterrows():
        # 获取角色名
        role_name = str(row.get(role_col, "")).strip() if role_col else ""
        if not role_name or role_name == "nan":
            continue

        # 获取适配人员
        adapt_users_str = row.get(user_col, "") if user_col else ""
        adapt_users = parse_adapt_users(adapt_users_str)

        print(f"\n[{idx+1}/{len(df)}] 角色: {role_name}")
        print(f"   适配人员: {adapt_users}")

        # 查找角色ID
        if role_name not in roles:
            print(f"   ⚠️ 角色未找到: {role_name}")
            print(f"      可用角色: {list(roles.keys())[:10]}...")
            results["skipped"].append({
                "role": role_name,
                "reason": "角色不存在"
            })
            continue

        role_id = roles[role_name]
        print(f"   ✅ 角色ID: {role_id}")

        # 查找员工ID
        user_ids = []
        missing_users = []

        for user_name in adapt_users:
            if user_name in users:
                user_ids.append(users[user_name])
                print(f"   ✅ 员工匹配: {user_name} -> ID: {users[user_name]}")
            else:
                missing_users.append(user_name)
                print(f"   ⚠️ 员工未找到: {user_name}")

        if missing_users:
            print(f"   缺失员工: {missing_users}")

        if not user_ids:
            print(f"   ⏭️ 跳过: 没有有效的员工")
            results["skipped"].append({
                "role": role_name,
                "reason": "无有效员工"
            })
            continue

        # 绑定关系
        print(f"   🔗 绑定 {len(user_ids)} 个员工到角色 {role_name}...")
        success, message = bind_role_relation(token, role_id, user_ids)

        if success:
            print(f"   ✅ 绑定成功")
            results["success"].append({
                "role": role_name,
                "role_id": role_id,
                "users": adapt_users,
                "user_ids": user_ids
            })
        else:
            print(f"   ❌ 绑定失败: {message}")
            results["failed"].append({
                "role": role_name,
                "error": message
            })

        # 短暂延迟，避免请求过快
        time.sleep(0.3)

    # 5. 输出汇总
    print("\n" + "=" * 70)
    print("📊 绑定结果汇总")
    print("=" * 70)

    success_count = len(results["success"])
    failed_count = len(results["failed"])
    skipped_count = len(results["skipped"])

    print(f"总计处理: {success_count + failed_count + skipped_count} 个角色")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {failed_count}")
    print(f"⏭️ 跳过: {skipped_count}")

    if results["failed"]:
        print("\n❌ 失败详情:")
        for item in results["failed"]:
            print(f"   - {item['role']}: {item['error']}")

    if results["success"]:
        print("\n✅ 成功绑定:")
        for item in results["success"]:
            print(f"   - {item['role']}: {len(item['users'])} 人")

    print("\n" + "=" * 70)

    # 保存结果
    output_file = SCRIPT_DIR / "binding_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": int(time.time()),
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"💾 结果已保存: {output_file}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
