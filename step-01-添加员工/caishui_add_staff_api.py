#!/usr/bin/env python3
"""
财税通员工批量添加 - API版本
使用HTTP API直接添加，速度比浏览器自动化快10倍

使用方法:
    python caishui_add_staff_api.py <excel_file_path>
    
示例:
    python caishui_add_staff_api.py /Users/tang/Desktop/employees.xlsx

配置:
    在脚本中修改以下变量:
    - TOKEN: x-token (从登录后获取)
    - COMPANY_ID: 企业ID (需要询问开发人员)
    - DEPARTMENT_MAP: 部门名称到ID的映射
"""

import requests
import pandas as pd
import json
import sys
import time
from typing import Dict, List, Tuple

# ==================== 配置区域 ====================
import json
import os

def load_config():
    """加载配置文件"""
    config_paths = [
        "config.json",  # 当前目录
        os.path.expanduser("~/.caishui/config.json"),  # 用户目录
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    
    return None

# 尝试加载配置文件
config = load_config()

if config:
    # 从配置文件读取
    TOKEN = config.get("token", "")
    COMPANY_ID = config.get("company_id")
    BASE_URL = config.get("base_url", "https://cst.uf-tree.com")
    DEPARTMENT_MAP = config.get("department_map", {})
    print("✅ 已从 config.json 加载配置")
else:
    # 使用默认配置（需要手动修改）
    print("⚠️ 未找到 config.json，使用默认配置")
    print("  请运行: python auto_config_helper.py 生成配置")
    print("  或手动修改脚本中的配置")
    
    TOKEN = "your_token_here"
    COMPANY_ID = None
    BASE_URL = "https://cst.uf-tree.com"
    DEPARTMENT_MAP = {}

# ==================================================


class CaishuiAPI:
    """财税通API客户端"""
    
    def __init__(self, token: str, company_id=None):
        self.token = token
        self.company_id = company_id
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.department_map = {}  # 部门名称到ID的映射
        
        # 设置默认请求头
        self.session.headers.update({
            "x-token": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://cst.uf-tree.com",
            "Referer": "https://cst.uf-tree.com/"
        })
        
        if company_id:
            self.session.headers["x-company-id"] = str(company_id)
    
    def fetch_departments(self) -> Dict[str, int]:
        """
        从API获取部门列表，建立名称到ID的映射
        
        Returns:
            Dict[部门名称, 部门ID]
        """
        print("🔍 正在获取部门列表...")
        
        # 尝试多个可能的部门API端点
        endpoints = [
            "/api/member/department/list",
            "/api/company/department/list",
            "/api/department/list",
            "/api/organization/department/list"
        ]
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    # 解析部门数据
                    departments = self._parse_departments(data)
                    if departments:
                        self.department_map = departments
                        print(f"✅ 成功获取 {len(departments)} 个部门")
                        
                        # 显示部门列表
                        print("\n📋 部门列表:")
                        for name, dept_id in departments.items():
                            print(f"  - {name}: {dept_id}")
                        
                        return departments
                        
            except Exception as e:
                print(f"  尝试 {endpoint} 失败: {e}")
                continue
        
        # 如果API获取失败，使用手动配置的映射
        if DEPARTMENT_MAP:
            print("⚠️ API获取失败，使用手动配置的部门映射")
            self.department_map = DEPARTMENT_MAP
            return DEPARTMENT_MAP
        
        print("❌ 无法获取部门列表，请检查：")
        print("  1. TOKEN是否有效")
        print("  2. COMPANY_ID是否正确")
        print("  3. 或者在DEPARTMENT_MAP中手动配置部门映射")
        return {}
    
    def _parse_departments(self, data) -> Dict[str, int]:
        """解析API返回的部门数据"""
        departments = {}
        
        # 处理不同的响应格式
        if not isinstance(data, dict):
            return departments
        
        # 获取数据列表
        dept_list = None
        if 'data' in data:
            dept_list = data['data']
        elif 'list' in data:
            dept_list = data['list']
        elif 'result' in data:
            dept_list = data['result']
        
        if not isinstance(dept_list, list):
            return departments
        
        # 遍历部门列表
        for dept in dept_list:
            if not isinstance(dept, dict):
                continue
            
            # 获取部门ID
            dept_id = dept.get('id') or dept.get('departmentId') or dept.get('deptId')
            
            # 获取部门名称
            name = dept.get('name') or dept.get('departmentName') or dept.get('deptName')
            
            if dept_id and name:
                departments[name] = int(dept_id)
            
            # 处理子部门（如果有）
            children = dept.get('children') or dept.get('childList')
            if isinstance(children, list):
                for child in children:
                    child_id = child.get('id') or child.get('departmentId')
                    child_name = child.get('name') or child.get('departmentName')
                    if child_id and child_name:
                        departments[child_name] = int(child_id)
        
        return departments
    
    def add_staff(self, name: str, mobile: str, department_ids: List[int], 
                  email: str = "", remark: str = "") -> Tuple[bool, str]:
        """
        添加单个员工
        
        Args:
            name: 员工姓名
            mobile: 手机号（11位）
            department_ids: 部门ID列表，如 [11487]
            email: 邮箱（可选）
            remark: 备注（可选）
            
        Returns:
            (success: bool, message: str)
        """
        url = f"{self.base_url}/api/member/userInfo/add"
        
        data = {
            "nickName": name,
            "mobile": mobile,
            "departmentIds": department_ids,
            "companyId": self.company_id  # 必须在body中
        }
        
        if email:
            data["email"] = email
        if remark:
            data["remark"] = remark
        
        try:
            response = self.session.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("success") or result.get("code") == 200:
                return True, "添加成功"
            else:
                return False, result.get("message", "未知错误")
                
        except requests.exceptions.Timeout:
            return False, "请求超时"
        except requests.exceptions.RequestException as e:
            return False, f"请求异常: {str(e)}"
        except json.JSONDecodeError:
            return False, "响应解析失败"
    
    def batch_add_from_excel(self, excel_path: str, 
                             name_col: str = "姓名",
                             phone_col: str = "手机号", 
                             dept_col: str = "门店",
                             auto_fetch_depts: bool = True) -> Dict:
        """
        从Excel批量添加员工
        
        Args:
            excel_path: Excel文件路径
            name_col: 姓名列名
            phone_col: 手机号列名
            dept_col: 部门列名
            
        Returns:
            统计结果字典
        """
        # 步骤1: 获取部门映射
        if auto_fetch_depts or not DEPARTMENT_MAP:
            self.fetch_departments()
        else:
            self.department_map = DEPARTMENT_MAP
            print(f"📋 使用手动配置的部门映射（共{len(DEPARTMENT_MAP)}个部门）")
        
        if not self.department_map:
            print("❌ 无法获取部门映射，无法继续")
            return {"success": 0, "failed": 0, "errors": ["无法获取部门映射"]}
        
        # 读取Excel
        try:
            df = pd.read_excel(excel_path)
            print(f"\n📊 读取到 {len(df)} 个员工")
        except Exception as e:
            print(f"❌ 读取Excel失败: {e}")
            return {"success": 0, "failed": 0, "errors": [str(e)]}
        
        # 显示预览
        print("\n" + "="*60)
        print("📋 员工数据预览")
        print("="*60)
        for idx, row in df.iterrows():
            name = str(row[name_col]).strip()
            phone = str(row[phone_col]).strip()
            dept = str(row[dept_col]).strip()
            
            # 检查部门是否存在
            dept_status = "✅" if dept in self.department_map else "❌未知"
            print(f"{idx+1:2d}. {name:8s} | {phone} | {dept} {dept_status}")
        
        # 确认
        print("\n" + "="*60)
        confirm = input("确认添加以上员工? (y/n): ")
        if confirm.lower() != "y":
            print("已取消")
            return {"success": 0, "failed": 0, "errors": []}
        
        # 开始添加
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        print("\n" + "="*60)
        print("🚀 开始批量添加")
        print("="*60)
        
        for idx, row in df.iterrows():
            name = str(row[name_col]).strip()
            phone = str(row[phone_col]).strip()
            dept_name = str(row[dept_col]).strip()
            
            # 处理手机号（确保11位）
            phone = phone[:11]
            
            print(f"\n[{idx+1}/{len(df)}] {name}", end=" ")
            
            # 获取部门ID（从映射中查找）
            if dept_name not in self.department_map:
                print(f"❌ 未知部门: {dept_name}")
                print(f"   可用的部门: {list(self.department_map.keys())}")
                results["failed"] += 1
                results["errors"].append(f"{name}: 未知部门 {dept_name}")
                continue
            
            dept_id = self.department_map[dept_name]
            
            # 调用API添加
            success, message = self.add_staff(
                name=name,
                mobile=phone,
                department_ids=[dept_id]
            )
            
            if success:
                print(f"✅ {message}")
                results["success"] += 1
            else:
                print(f"❌ {message}")
                results["failed"] += 1
                results["errors"].append(f"{name}: {message}")
            
            # 短暂延迟，避免请求过快
            time.sleep(0.5)
        
        # 输出统计
        print("\n" + "="*60)
        print("📊 添加完成")
        print("="*60)
        print(f"成功: {results['success']}/{len(df)}")
        print(f"失败: {results['failed']}/{len(df)}")
        
        if results['errors']:
            print("\n❌ 错误详情:")
            for error in results['errors'][:10]:  # 只显示前10个错误
                print(f"  - {error}")
        
        return results


def check_config():
    """检查配置是否完整"""
    errors = []
    
    if not TOKEN or TOKEN == "your_token_here":
        errors.append("TOKEN 未设置")
    
    # COMPANY_ID 是可选的，如果API需要会自动获取或提示
    # DEPARTMENT_MAP 也是可选的，会自动从API获取
    
    if errors:
        print("="*60)
        print("⚠️ 配置不完整")
        print("="*60)
        print("\n请修改脚本中的以下配置:\n")
        for error in errors:
            print(f"  ❌ {error}")
        print("\n在脚本的 '配置区域' 部分修改这些值")
        return False
    
    return True


def main():
    """主函数"""
    # 检查配置
    if not check_config():
        sys.exit(1)
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python caishui_add_staff_api.py <excel_file_path>")
        print("示例: python caishui_add_staff_api.py /Users/tang/Desktop/employees.xlsx")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    
    # 初始化API客户端
    api = CaishuiAPI(TOKEN, COMPANY_ID)
    
    # 执行批量添加
    results = api.batch_add_from_excel(excel_file)
    
    # 输出最终结果
    print("\n" + "="*60)
    if results['failed'] == 0:
        print("🎉 全部添加成功！")
    else:
        print(f"⚠️ 部分添加失败 ({results['failed']}个)")
    print("="*60)


if __name__ == "__main__":
    main()
