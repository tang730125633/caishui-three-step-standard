# Step 4: 创建单据模板

> **功能**: 批量创建财税通单据模板（分组 + 模板 + 可见范围）
> **验证状态**: ✅ **2026-03-14 成功案例**（5个模板全部创建成功）
> **难度**: ⭐⭐⭐ 中等（有完整教学文档）

---

## 📋 什么是"单据模板"？

在财税通系统中，单据模板是员工提交报销/借款/申请时使用的表单。

```
单据模板分组（一级）
├── 单据模板（二级）
│   ├── 可见范围: 谁可以使用这个模板
│   ├── 审批流程: 提交后谁审批
│   └── 表单字段: 需要填写哪些信息
```

### 示例

| 分组 | 模板名称 | 类型 | 可见范围 |
|-----|---------|------|---------|
| 报销及付款单据 | 员工报销单 | 报销单 | 部门: 测试门店1 |
| 报销及付款单据 | 采购付款单 | 批量付款单 | 角色: 部门经理 |
| 借款类单据 | 备用金借款 | 借款单 | 员工: 张三, 李四 |

---

## 🚀 快速开始

### 前置条件

1. **Edge 浏览器已启动调试模式**
   ```bash
   /Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9222
   ```

2. **已登录财税通系统** (https://cst.uf-tree.com)

3. **已获取 Token**
   ```bash
   cd scripts
   python get_token.py
   ```

### 执行步骤

```bash
# 1. 处理分组（检查/创建 Excel 中的分组）
python scripts/01_process_groups.py --excel ./example_templates.xlsx

# 2. 创建单据模板（完整流程）
python scripts/02_create_templates.py --excel ./example_templates.xlsx
```

---

## 📁 项目结构

```
step-04-创建单据模板/
│
├── README.md                    ← 本文件（总入口）
├── example_templates.xlsx       ← ⭐ 示例 Excel 模板
│
├── docs/                        ← 📚 详细教学文档
│   ├── 01-环境准备.md           ← Edge启动 + Token获取
│   ├── 02-接口文档.md           ← API详细说明
│   ├── 03-分组处理逻辑.md        ← 分组存在性判断
│   ├── 04-完整执行流程.md        ← 端到端执行步骤
│   └── 07-快速参考手册.md        ← 字段和ID速查
│
├── scripts/                     ← 🐍 执行脚本
│   ├── get_token.py             ← Token获取工具
│   ├── 01_process_groups.py     ← 分组处理
│   └── 02_create_templates.py   ← 创建模板（完整版）
│
├── config/                      ← ⚙️ 配置（自动生成）
│   └── config.json              ← Token保存位置
│
├── output/                      ← 📤 输出（自动生成）
│   └── group_result.json        ← 分组处理结果
│
└── success-cases/               ← ✅ 成功案例
    └── 案例1-单据模板自动化/      ← 5个模板全部成功记录
        ├── README.md
        ├── create_templates.py
        └── example_templates.xlsx
```

---

## 📊 Excel 数据格式

`example_templates.xlsx` 必须包含以下列：

| 列名 | 必填 | 说明 | 示例 |
|-----|------|------|------|
| 是否创建 | ✅ | 标记"是"才处理 | 是 |
| 单据分组（一级目录） | ✅ | 分组名称 | 报销及付款单据1 |
| 单据大类（二级目录） | ✅ | 单据类型 | 报销单/借款单/申请单 |
| 单据模板名称 | ✅ | 模板名称 | 员工报销单 |
| 可见范围类型 | ✅ | 角色/部门/员工 | 角色 |
| 可见范围对象 | ✅ | 具体对象 | 部门经理 |

### 单据类型映射

| Excel 填写 | API 枚举值 | 说明 |
|-----------|-----------|------|
| 报销单 | EXPENSE | 费用报销 |
| 借款单 | LOAN | 借款申请 |
| 申请单 | REQUISITION | 通用申请 |
| 批量付款单 | PAYMENT | 批量付款 |
| 计提单 | ACCRUAL | 费用计提 |

### 可见范围说明

| 类型 | 查询接口 | 匹配字段 | 示例 |
|-----|---------|---------|------|
| 角色 | `/api/member/role/get/tree` | children[].name | 部门经理 → 18294 |
| 部门 | `/api/member/department/queryDepartments` | result[].title | 测试门店1 → 9151 |
| 员工 | `/api/member/department/queryCompany` | users[].nickName | 李君英 → 10749 |

---

## 🔗 核心 API 流程

### 阶段 1: 分组处理

```
1. queryTemplateTree    → 查询现有分组
2. createTemplateGroup  → 创建不存在的分组
3. queryTemplateTree    → 再次查询获取新分组ID
```

### 阶段 2: 模板创建

```
1. queryCompany         → 获取员工列表（nickName → userId）
2. queryDepartments     → 获取部门列表（title → departmentId）
3. getRoleTree          → 获取角色列表（name → roleId）
4. createTemplate       → 创建单据模板
5. queryTemplate        → 验证创建结果
```

---

## ⚠️ 常见问题

### Q1: Token 过期
**现象**: API 返回 `登陆失效`
**解决**: 重新运行 `python scripts/get_token.py`

### Q2: 角色找不到
**现象**: 提示"限制可见范围情况下，需选择限制的范围"
**原因**: 使用了错误的角色查询方式
**解决**: 必须使用 `/api/member/role/get/tree` 查询完整角色树

### Q3: 申请单创建失败
**现象**: 提示"请确认是否选择申请内容"
**解决**: 在 Payload 中添加 `"applyContentType": "TEXT"`

### Q4: 分组创建后找不到 ID
**现象**: createTemplateGroup 成功但 queryTemplateTree 找不到
**原因**: 系统数据同步延迟
**解决**: 添加短暂延迟后再次查询

---

## ✅ 验证方式

创建成功后，在财税通系统中查看：
1. 进入「单据设置」→「单据模板」
2. 检查分组是否存在
3. 检查模板是否在正确的分组下
4. 检查可见范围是否正确

---

## 📚 学习路径

如果你是接手这个项目的 AI：

1. **先读**: 本文件了解整体流程
2. **再读**: `docs/01-环境准备.md` 检查环境
3. **细读**: `docs/04-完整执行流程.md` 了解执行步骤
4. **参考**: `success-cases/案例1/` 查看真实成功案例
5. **运行**: 从 `scripts/get_token.py` 开始

---

## 🎯 成功案例

详见 `success-cases/案例1-单据模板自动化/`

**执行记录**: 2026-03-14 成功创建 5 个单据模板
- 测试三级目录1 → ID: 7014
- 测试三级目录2 → ID: 7012
- 测试三级目录3 → ID: 7013
- 测试三级目录4 → ID: 7018
- 测试三级目录5 → ID: 7016

---

## 📞 关联步骤

- **Step 1**: 添加员工 → 获取 userId
- **Step 2**: 添加费用模板 → 获取费用模板体系
- **Step 3**: 单据角色与人员授权 → 获取 roleId
- **Step 4**: 创建单据模板（本步骤）

---

*整理日期: 2026-03-15*
*原项目位置: `/Users/tang/Desktop/自动添加员工项目/单据模板试验/`*
