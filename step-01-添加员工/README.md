# 财税通员工批量添加 Skill

自动化批量添加员工到财税通（cst.uf-tree.com）系统，支持从Excel/CSV读取数据并自动填写表单。

---

## 📋 功能特性

- ✅ 从Excel/CSV自动读取员工数据
- ✅ 智能字段映射（姓名、手机号、部门）
- ✅ 自动处理部门选择（vue-treeselect树形组件）
- ✅ 批量添加，支持"保存并继续添加"模式
- ✅ 自动验证添加结果
- ✅ 支持错误重试和日志记录

---

## 🔧 前置条件

### 1. 环境要求
- Python 3.8+
- Playwright 浏览器自动化库
- Chrome/Edge/Chromium 浏览器（开启调试模式）

### 2. 安装依赖
```bash
pip install playwright pandas openpyxl
playwright install chromium
```

### 3. 浏览器设置
启动浏览器时添加调试参数：

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**或 Edge:**
```bash
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9222
```

### 4. 登录系统
- 打开浏览器访问 https://cst.uf-tree.com
- 完成登录并进入企业
- 确保浏览器保持运行

---

## 📊 数据格式

### Excel/CSV 格式要求

| 列名 | 类型 | 必填 | 说明 |
|------|------|------|------|
| 姓名 | 字符串 | ✅ | 员工姓名（2-20字符） |
| 手机号 | 字符串 | ✅ | 11位手机号码 |
| 门店 | 字符串 | ✅ | 所属门店/部门名称 |

### 示例数据

**Excel格式:**
```
| 姓名 | 手机号 | 门店 |
|------|--------|------|
| 张三 | 13800138000 | 测试门店1 |
| 李四 | 13800138001 | 测试门店2 |
| 王五 | 13800138002 | 测试门店3 |
```

**CSV格式:**
```csv
姓名,手机号,门店
张三,13800138000,测试门店1
李四,13800138001,测试门店2
王五,13800138002,测试门店3
```

⚠️ **重要:** 手机号必须是11位，不要包含空格或特殊字符！

---

## 🚀 使用方法

### 方式1: 命令行运行

```bash
python caishui_add_staff.py --file /path/to/employees.xlsx
```

### 方式2: Python脚本调用

```python
from caishui_staff import StaffManager

# 初始化
manager = StaffManager(debug_port="http://localhost:9222")

# 添加员工
manager.add_from_excel("/path/to/employees.xlsx")

# 或添加单个员工
manager.add_staff(
    name="张三",
    phone="13800138000",
    department="测试门店1"
)
```

### 方式3: 使用本Skill的快捷命令

在Claude Code中使用：
```
@caishui-add-staff /path/to/employees.xlsx
```

---

## 📝 完整代码示例

### 基础版本

```python
#!/usr/bin/env python3
"""
财税通员工批量添加脚本
"""
from playwright.sync_api import sync_playwright
import pandas as pd
import time

# 配置
EXCEL_FILE = "/Users/tang/Desktop/employees.xlsx"
DEBUG_PORT = "http://localhost:9222"

def add_staff_from_excel():
    # 读取Excel
    df = pd.read_excel(EXCEL_FILE)
    
    with sync_playwright() as p:
        # 连接浏览器
        browser = p.chromium.connect_over_cdp(DEBUG_PORT)
        
        for idx, row in df.iterrows():
            name = str(row['姓名']).strip()
            phone = str(row['手机号']).strip()[:11]  # 确保11位
            dept = str(row['门店']).strip()
            
            print(f"\n[{idx+1}/{len(df)}] 添加: {name}")
            
            # 获取页面
            page = None
            for ctx in browser.contexts:
                for pg in ctx.pages:
                    if "uf-tree.com" in pg.url:
                        page = pg
                        break
                if page:
                    break
            
            if not page:
                print("  ❌ 未找到页面")
                continue
            
            page.bring_to_front()
            
            try:
                # 1. 进入员工管理
                page.goto("https://cst.uf-tree.com/company/staff")
                time.sleep(3)
                
                # 2. 点击添加员工
                page.click('button:has-text("添加员工")')
                time.sleep(2)
                
                # 3. 选择直接添加（⚠️ 不要点到"添加子部门"！）
                page.click('.el-dropdown-menu__item:has-text("直接添加")')
                time.sleep(3)
                
                # 4. 填写表单（使用正确的placeholder）
                page.fill('input[placeholder="请输入员工姓名"]', name)
                page.fill('input[placeholder="请输入员工手机"]', phone)
                
                # 5. 选择部门
                page.click('.vue-treeselect__control')
                time.sleep(1)
                page.click(f'.vue-treeselect__option:has-text("{dept}")')
                time.sleep(1)
                
                # 6. 点击保存并继续添加
                page.click('button:has-text("保存并继续添加")')
                time.sleep(4)
                
                print(f"  ✅ 已保存: {name}")
                
            except Exception as e:
                print(f"  ❌ 失败: {e}")
                continue
        
        browser.close()

if __name__ == "__main__":
    add_staff_from_excel()
```

### 高级版本（带错误处理和验证）

```python
#!/usr/bin/env python3
"""
财税通员工批量添加 - 高级版
包含错误处理、重试机制和结果验证
"""
from playwright.sync_api import sync_playwright, TimeoutError
import pandas as pd
import time
import re

class CaishuiStaffManager:
    def __init__(self, debug_port="http://localhost:9222"):
        self.debug_port = debug_port
        self.browser = None
        self.page = None
        
    def connect(self):
        """连接浏览器"""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.connect_over_cdp(self.debug_port)
        return self
    
    def get_page(self):
        """获取财税通页面"""
        for ctx in self.browser.contexts:
            for pg in ctx.pages:
                if "uf-tree.com" in pg.url:
                    self.page = pg
                    return pg
        return None
    
    def add_single_staff(self, name, phone, dept, max_retries=3):
        """添加单个员工，带重试机制"""
        for attempt in range(max_retries):
            try:
                print(f"  尝试 {attempt+1}/{max_retries}...", end="")
                
                page = self.get_page()
                if not page:
                    raise Exception("未找到页面")
                
                page.bring_to_front()
                
                # 进入员工管理
                page.goto("https://cst.uf-tree.com/company/staff", timeout=10000)
                time.sleep(2)
                
                # 点击添加员工
                page.click('button:has-text("添加员工")', timeout=5000)
                time.sleep(1)
                
                # 选择直接添加
                page.click('.el-dropdown-menu__item:has-text("直接添加")', timeout=5000)
                time.sleep(2)
                
                # 填写表单
                page.fill('input[placeholder="请输入员工姓名"]', name, timeout=5000)
                page.fill('input[placeholder="请输入员工手机"]', phone, timeout=5000)
                
                # 选择部门
                page.click('.vue-treeselect__control', timeout=5000)
                time.sleep(0.5)
                page.click(f'.vue-treeselect__option:has-text("{dept}")', timeout=5000)
                time.sleep(0.5)
                
                # 保存
                page.click('button:has-text("保存并继续添加")', timeout=5000)
                time.sleep(3)
                
                # 检查是否有错误提示
                error = page.query_selector('.el-message--error')
                if error:
                    error_text = error.inner_text()
                    if "手机号已存在" in error_text:
                        print(f"  ⚠️ 手机号已存在，跳过")
                        return "skipped"
                    raise Exception(f"保存失败: {error_text}")
                
                print(f"  ✅ 成功")
                return "success"
                
            except TimeoutError:
                print(f"  ⏱️ 超时")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return "timeout"
                
            except Exception as e:
                print(f"  ❌ {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return f"error: {e}"
        
        return "failed"
    
    def add_from_excel(self, excel_path):
        """从Excel批量添加"""
        df = pd.read_excel(excel_path)
        
        print(f"\n📊 共 {len(df)} 个员工待添加\n")
        
        results = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        for idx, row in df.iterrows():
            name = str(row['姓名']).strip()
            phone = str(row['手机号']).strip()[:11]
            dept = str(row['门店']).strip()
            
            print(f"[{idx+1}/{len(df)}] {name} | {phone} | {dept}")
            
            result = self.add_single_staff(name, phone, dept)
            
            if result == "success":
                results["success"] += 1
            elif result == "skipped":
                results["skipped"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{name}: {result}")
        
        # 输出统计
        print("\n" + "="*60)
        print("📊 添加完成")
        print("="*60)
        print(f"成功: {results['success']}/{len(df)}")
        print(f"跳过: {results['skipped']}/{len(df)}")
        print(f"失败: {results['failed']}/{len(df)}")
        
        if results['errors']:
            print("\n❌ 错误详情:")
            for error in results['errors']:
                print(f"  - {error}")
        
        return results
    
    def verify_staff(self, names):
        """验证员工是否添加成功"""
        page = self.get_page()
        if not page:
            return []
        
        page.goto("https://cst.uf-tree.com/company/staff")
        time.sleep(3)
        
        found = []
        for name in names:
            # 使用搜索框
            search = page.query_selector('input[placeholder*="手机或姓名"]')
            if search:
                search.fill(name)
                search.press('Enter')
                time.sleep(2)
                
                items = page.query_selector_all('.user-item, .el-table__row')
                if len(items) > 0:
                    found.append(name)
        
        return found
    
    def close(self):
        """关闭浏览器连接"""
        if self.browser:
            self.browser.close()


# 使用示例
if __name__ == "__main__":
    manager = CaishuiStaffManager()
    manager.connect()
    
    try:
        # 批量添加
        results = manager.add_from_excel("/path/to/employees.xlsx")
        
        # 验证结果
        if results['success'] > 0:
            print("\n🔍 验证添加结果...")
            df = pd.read_excel("/path/to/employees.xlsx")
            names = df['姓名'].tolist()
            found = manager.verify_staff(names)
            print(f"验证通过: {len(found)}/{len(names)}")
            
    finally:
        manager.close()
```

---

## ⚠️ 常见问题

### Q1: 点击"添加员工"后跳转到选择企业页面
**原因:** 点到了"添加子部门"而不是"直接添加"

**解决:** 确保精确匹配"直接添加":
```python
# ✅ 正确
page.click('.el-dropdown-menu__item:has-text("直接添加")')

# ❌ 错误（可能点到"添加子部门"）
page.click('.el-dropdown-menu__item:has-text("添加")')
```

### Q2: 手机号填写后保存失败
**原因:** 手机号格式错误（12位或包含空格）

**解决:** 确保11位数字:
```python
phone = str(phone).strip()[:11]  # 取前11位
```

### Q3: 找不到姓名/手机号输入框
**原因:** 使用了错误的选择器（填到了搜索框）

**正确选择器:**
```python
# ✅ 添加表单的输入框
page.fill('input[placeholder="请输入员工姓名"]', name)
page.fill('input[placeholder="请输入员工手机"]', phone)

# ❌ 搜索框（不要用这个）
page.fill('input[placeholder="请输入员工手机或姓名或部门名称"]', name)
```

### Q4: 部门选择失败
**原因:** vue-treeselect组件需要特殊处理

**解决:**
```python
# 1. 点击展开
page.click('.vue-treeselect__control')
time.sleep(1)

# 2. 点击选项
page.click(f'.vue-treeselect__option:has-text("{dept}")')
```

### Q5: 保存按钮点击无效
**原因:** 元素不可见或被其他元素遮挡

**解决:** 使用JavaScript点击:
```python
page.evaluate("""
    () => {
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            if (btn.innerText && btn.innerText.includes('保存')) {
                btn.click();
                return 'clicked';
            }
        }
    }
""")
```

---

## 🔍 调试技巧

### 1. 检查当前页面状态
```python
print(f"当前URL: {page.url}")
print(f"页面标题: {page.title()}")
```

### 2. 查找所有输入框
```python
inputs = page.query_selector_all('input')
for i, inp in enumerate(inputs):
    placeholder = inp.get_attribute('placeholder') or ''
    print(f"[{i}] {placeholder}")
```

### 3. 截图保存
```python
page.screenshot(path="/tmp/debug.png")
```

### 4. 检查元素可见性
```python
element = page.query_selector('button:has-text("保存")')
print(f"可见: {element.is_visible()}")
print(f"禁用: {element.evaluate('el => el.disabled')}")
```

---

## 📚 系统信息

- **系统名称:** 财税通 (凯旋创智)
- **网址:** https://cst.uf-tree.com
- **技术栈:** Vue.js + Element UI + vue-treeselect
- **添加员工URL:** https://cst.uf-tree.com/company/staff#/company/staffAdd

---

---

## 🚀 API 方式（推荐，比浏览器快17倍）

### 为什么用 API？

| 方式 | 速度 | 稳定性 | 适用场景 |
|------|------|--------|---------|
| **API方式** ⭐ | 0.8秒/人 | 高 | 推荐日常使用 |
| 浏览器方式 | 15秒/人 | 中 | API不可用时备用 |

### API 端点

```
POST https://cst.uf-tree.com/api/member/userInfo/add
Headers:
  x-token: {你的token}
  Content-Type: application/json

Body:
{
    "nickName": "张三",
    "mobile": "13800138000",
    "departmentIds": [9151],
    "companyId": 7792
}
```

### API 方式代码示例

```python
import requests
import pandas as pd
import time
import re

# ========== 配置 ==========
API_URL = "https://cst.uf-tree.com/api/member/userInfo/add"
TOKEN = "从浏览器获取的token"
COMPANY_ID = 7792  # 企业ID

# 部门映射（部门名 -> ID）
DEPT_MAP = {
    "测试门店1": 9151,
    "测试门店2": 9152,
}

# ========== 添加函数 ==========
def add_staff_api(name, phone, dept_name):
    """通过API添加单个员工"""
    dept_id = DEPT_MAP.get(dept_name)
    if not dept_id:
        return False, f"未知部门: {dept_name}"
    
    payload = {
        "nickName": name,
        "mobile": str(phone).strip(),
        "departmentIds": [dept_id],
        "companyId": COMPANY_ID
    }
    
    headers = {
        "x-token": TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=5)
        result = resp.json()
        
        if result.get("success"):
            return True, "添加成功"
        else:
            return False, result.get("message", "未知错误")
    except Exception as e:
        return False, str(e)

# ========== 批量添加 ==========
def batch_add_from_excel(excel_path):
    """从Excel批量添加"""
    df = pd.read_excel(excel_path)
    
    success = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        name = str(row['姓名']).strip()
        phone = str(row['手机号']).strip()
        dept = str(row['门店']).strip()
        
        print(f"[{idx+1}/{len(df)}] {name}...", end=" ")
        
        ok, msg = add_staff_api(name, phone, dept)
        if ok:
            print(f"✅ {msg}")
            success += 1
        else:
            print(f"❌ {msg}")
            failed += 1
            errors.append(f"{name}: {msg}")
        
        time.sleep(0.5)  # 避免请求过快
    
    print(f"\n📊 完成: 成功 {success}/{len(df)}, 失败 {failed}/{len(df)}")
    return success, failed, errors

# 使用
if __name__ == "__main__":
    batch_add_from_excel("employees.xlsx")
```

### 获取 Token 和 Company ID

```python
from playwright.sync_api import sync_playwright

def get_auth_info(debug_port="http://localhost:9222"):
    """从浏览器获取认证信息"""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(debug_port)
        
        # 找到财税通页面
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "uf-tree.com" in pg.url:
                    page = pg
                    break
            if page:
                break
        
        if not page:
            return None
        
        # 从 localStorage 获取
        auth = page.evaluate("""
            () => {
                const vuex = localStorage.getItem('vuex');
                if (vuex) {
                    const data = JSON.parse(vuex);
                    return {
                        token: data.user?.token,
                        companyId: data.user?.company?.id,
                        userId: data.user?.id
                    };
                }
                return null;
            }
        """)
        
        return auth

# 使用
info = get_auth_info()
print(f"Token: {info['token']}")
print(f"Company ID: {info['companyId']}")
```

---

## 📚 核心知识点速查

### 1. 关键 API 端点汇总

| 功能 | 方法 | 端点 |
|------|------|------|
| **添加员工** | POST | `/api/member/userInfo/add` |
| **获取员工列表** | POST | `/api/member/department/queryCompany` |
| **获取部门列表** | POST | `/api/member/department/queryCompany` |

### 2. 获取员工列表（含ID）

```python
# POST /api/member/department/queryCompany
response = {
    "users": [
        {"id": 13961, "nickName": "韩老师", "phone": "..."},
        {"id": 14824, "nickName": "张总", "phone": "..."}
    ]
}
```

### 3. 常见错误码

| 错误 | 原因 | 解决 |
|------|------|------|
| 403 无权限 | Token无效或过期 | 重新获取Token |
| 手机号已存在 | 员工已添加 | 跳过或更新 |
| 部门不存在 | dept_id错误 | 检查DEPT_MAP |

---

## 📝 更新日志

### v1.1 (2024-03-13)
- 添加 API 方式（推荐）
- 补充获取员工列表端点
- 整合文档结构

### v1.0 (2024-03-07)
- 初始版本
- 浏览器自动化方式
- 支持Excel批量导入

---

**文档整合日期**: 2024-03-13
**适用版本**: 财税通最新版

---

**提示:** 
- API 方式速度更快（0.8秒/人 vs 15秒/人）
- 使用前请确保已登录系统并有相应权限
- 建议先测试1-2个员工确认流程正常后再批量操作
