#!/usr/bin/env python3
"""
process_excel.py
处理 Excel 中的单据模板分组

功能:
1. 读取 Excel 正式填写表
2. 筛选 "是否创建" = "是" 的行
3. 提取并去重分组名称
4. 检查分组是否存在（queryTemplateTree）
5. 不存在则创建（createTemplateGroup）
6. 输出分组 ID 映射表

硬约束:
- 浏览器: Edge (端口 9223)
- Token 来源: Edge localStorage.vuex
"""

import argparse
import json
import os
import time
import sys
from pathlib import Path

import pandas as pd
import requests

# 添加父目录到路径以导入共享模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ========== 硬约束配置 ==========
BASE_URL = "https://cst.uf-tree.com"
COMPANY_ID = 7792
CONFIG_FILE = Path(__file__).parent.parent / "config" / "config.json"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
# ================================


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_headers(token):
    """生成请求头"""
    return {
        "x-token": token,
        "Content-Type": "application/json"
    }


def query_template_tree(token):
    """查询单据模板树"""
    url = f"{BASE_URL}/api/bill/template/queryTemplateTree"
    headers = get_headers(token)
    params = {
        "companyId": COMPANY_ID,
        "t": int(time.time() * 1000)
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        data = resp.json()
        
        if data.get("success") == True and data.get("code") == 200:
            return data.get("result", [])
        else:
            print(f"❌ 查询失败: {data.get('message')}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def create_template_group(token, name):
    """创建单据模板分组"""
    url = f"{BASE_URL}/api/bill/template/createTemplateGroup"
    headers = get_headers(token)
    payload = {
        "name": name,
        "companyId": COMPANY_ID
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        data = resp.json()
        
        if (data.get("success") == True and 
            data.get("code") == 200 and 
            data.get("message") == "处理成功"):
            return True, None
        else:
            return False, data.get('message')
    except Exception as e:
        return False, str(e)


def read_excel(excel_path, sheet_name="正式填写表"):
    """
    读取 Excel 文件
    
    返回:
        DataFrame 或 None
    """
    try:
        print(f"📖 读取 Excel: {excel_path}")
        print(f"   Sheet: {sheet_name}")
        
        # 读取指定 sheet
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        
        print(f"   原始数据: {len(df)} 行")
        
        # 找到表头行（通常是第2行，索引1）
        # 表头包含: 序号, 是否创建, 单据分组, 单据模板名称, 单据大类, 可见范围类型, 可见范围对象, 备注
        header_row = None
        for idx, row in df.iterrows():
            if '是否创建' in str(row.values):
                header_row = idx
                break
        
        if header_row is None:
            print("❌ 未找到表头行（应包含'是否创建'列）")
            return None
        
        # 重新读取，使用正确的表头行
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row)
        
        print(f"   解析完成: {len(df)} 行数据")
        return df
        
    except Exception as e:
        print(f"❌ Excel 读取失败: {e}")
        return None


def process_groups(token, excel_path, sheet_name="正式填写表"):
    """
    处理分组逻辑（主函数）
    
    流程:
    1. 读取 Excel
    2. 筛选待创建行
    3. 提取唯一分组名
    4. 检查/创建分组
    5. 返回映射表
    """
    # 1. 读取 Excel
    df = read_excel(excel_path, sheet_name)
    if df is None:
        return None
    
    # 2. 筛选 "是否创建" = "是" 的行
    if '是否创建' not in df.columns:
        print(f"❌ Excel 格式错误: 未找到'是否创建'列")
        print(f"   可用列: {list(df.columns)}")
        return None
    
    df_create = df[df['是否创建'] == '是'].copy()
    print(f"\n📊 筛选结果: {len(df_create)} 行待创建")
    
    if len(df_create) == 0:
        print("⚠️ 没有需要创建的数据")
        return {}
    
    # 3. 提取唯一分组名
    if '单据分组' not in df_create.columns:
        print(f"❌ Excel 格式错误: 未找到'单据分组'列")
        return None
    
    group_names = df_create['单据分组'].dropna().drop_duplicates().tolist()
    print(f"📋 唯一分组: {group_names}")
    
    # 4. 查询现有分组
    print(f"\n🔍 查询现有分组...")
    existing_groups = query_template_tree(token)
    if existing_groups is None:
        print("❌ 无法获取现有分组列表")
        return None
    
    # 建立名称到ID的映射
    existing_map = {g.get("name"): g.get("id") for g in existing_groups}
    print(f"   系统中已有 {len(existing_map)} 个分组")
    
    # 5. 处理每个分组
    result = {
        "group_map": {},  # 名称到ID的映射
        "processed": [],   # 处理详情
        "errors": []       # 错误记录
    }
    
    for group_name in group_names:
        print(f"\n📝 处理分组: {group_name}")
        
        if group_name in existing_map:
            # 分组已存在
            group_id = existing_map[group_name]
            result["group_map"][group_name] = group_id
            result["processed"].append({
                "name": group_name,
                "id": group_id,
                "action": "existing",
                "status": "success"
            })
            print(f"   ✅ 已存在，ID: {group_id}")
        else:
            # 分组不存在，需要创建
            print(f"   ⏳ 不存在，准备创建...")
            success, error = create_template_group(token, group_name)
            
            if success:
                # 再次查询获取新ID
                time.sleep(0.5)  # 等待数据同步
                new_groups = query_template_tree(token)
                if new_groups:
                    new_map = {g.get("name"): g.get("id") for g in new_groups}
                    if group_name in new_map:
                        group_id = new_map[group_name]
                        result["group_map"][group_name] = group_id
                        result["processed"].append({
                            "name": group_name,
                            "id": group_id,
                            "action": "created",
                            "status": "success"
                        })
                        print(f"   ✅ 创建成功，ID: {group_id}")
                    else:
                        result["errors"].append({
                            "name": group_name,
                            "error": "创建后无法获取ID"
                        })
                        print(f"   ⚠️ 创建成功但无法获取ID")
            else:
                result["errors"].append({
                    "name": group_name,
                    "error": error
                })
                print(f"   ❌ 创建失败: {error}")
    
    return result


def save_result(result):
    """保存处理结果"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "group_result.json"
    
    # 添加元数据
    result["metadata"] = {
        "timestamp": int(time.time()),
        "company_id": COMPANY_ID,
        "base_url": BASE_URL
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(description="处理 Excel 单据模板分组")
    parser.add_argument("--excel", required=True, help="Excel 文件路径")
    parser.add_argument("--sheet", default="正式填写表", help="Sheet 名称")
    args = parser.parse_args()
    
    print("=" * 60)
    print("📊 Excel 分组处理")
    print("=" * 60)
    
    # 加载 Token
    config = load_config()
    if not config or not config.get("token"):
        print("\n❌ 未找到 Token，请先运行:")
        print("   python3 scripts/get_token.py")
        return False
    
    token = config["token"]
    print(f"\n✅ 已加载 Token: {token[:30]}...")
    
    # 检查 Excel 文件
    excel_path = Path(args.excel)
    if not excel_path.exists():
        print(f"\n❌ Excel 文件不存在: {excel_path}")
        return False
    
    # 处理分组
    result = process_groups(token, excel_path, args.sheet)
    
    if result is None:
        return False
    
    # 保存结果
    output_file = save_result(result)
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("📋 处理摘要")
    print("=" * 60)
    print(f"分组总数: {len(result['group_map'])}")
    print(f"已存在: {sum(1 for p in result['processed'] if p['action'] == 'existing')}")
    print(f"新创建: {sum(1 for p in result['processed'] if p['action'] == 'created')}")
    print(f"错误: {len(result['errors'])}")
    
    print(f"\n分组映射表:")
    for name, id in result['group_map'].items():
        print(f"   {name} -> {id}")
    
    print("\n" + "=" * 60)
    print("✅ 处理完成")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
