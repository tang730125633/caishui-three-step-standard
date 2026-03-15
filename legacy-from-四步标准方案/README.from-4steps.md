# 财税通自动化 - 四步标准方案

> **项目定位**: 已验证可运行的四步自动化流程，从零开始配置财税通系统
> **适用对象**: AI Assistant / OpenClaw / 自动化开发者
> **最后验证**: 2026-03-14（全部跑通）

---

## 📌 经验复盘索引
- `./2026-03-16-关键卡点复盘-多值拆分与防重策略.md`（重点：可见范围多值拆分统一、模板名称防重重试）

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Edge 浏览器调试模式
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9222

# 登录财税通系统 https://cst.uf-tree.com
```

### 2. 获取 Token

```bash
cd utils
python get_token.py
# Token 会自动保存到各步骤的 config.json 中
```

### 3. 按顺序执行四个步骤

```bash
# Step 1: 添加员工
cd step-01-添加员工
python caishui_add_staff_api.py

# Step 2: 添加费用模板
cd step-02-添加费用模板
python add_fee_templates.py

# Step 3: 流程配置（角色+人员关联）
cd step-03-单据角色与人员授权
python 3a-添加费用角色.py

# Step 4: 创建单据模板
cd step-04-创建单据模板
python scripts/01_process_groups.py --excel ./example_templates.xlsx
python scripts/02_create_templates.py --excel ./example_templates.xlsx
```

---

## 📁 项目结构

```
财税通自动化-四步标准方案/
│
├── README.md                          ← 本文件（总入口）
├── requirements.txt                   ← Python依赖
│
├── step-01-添加员工/                  ← ✅ 已验证可用
│   ├── README.md                      ← 详细教学文档
│   ├── caishui_add_staff_api.py       ← API方式（推荐，0.8秒/人）
│   ├── caishui_add_staff.py           ← 浏览器方式（备用）
│   ├── config.json                    ← 配置（Token/部门映射）
│   └── employees_example.csv          ← 示例数据
│
├── step-02-添加费用模板/              ← ✅ 已验证可用
│   ├── README.md                      ← 详细教学文档
│   ├── add_fee_templates.py           ← 核心代码
│   ├── config.json                    ← 配置
│   └── 费用模板示例.xlsx              ← 示例数据
│
├── step-03-单据角色与人员授权/        ← ✅ 已验证可用（原"三步闭环"）
│   ├── README.md                      ← 三步闭环详解
│   ├── 3a-添加费用角色.py             ← 创建角色组+子角色
│   ├── 3b-绑定人员授权.py             ← 人员与角色关联（待添加）
│   ├── 费用科目配置表.xlsx            ← Excel模板（第三步核心配置）
│   ├── api_summary.md                 ← API文档大全
│   ├── 科目配置表_已更新.xlsx         ← 实际配置数据
│   └── 成功案例/                      ← 真实运行记录
│
├── step-04-创建单据模板/              ← ✅ 成功案例（2026-03-14）
│   ├── README.md                      ← 总入口 + 快速开始
│   ├── example_templates.xlsx         ← ⭐ 示例Excel模板
│   │
│   ├── docs/                          ← 📚 详细教学文档
│   │   ├── 01-环境准备.md              ← Edge启动+Token获取
│   │   ├── 02-接口文档.md              ← API详细说明
│   │   ├── 03-分组处理逻辑.md          ← 分组存在性判断
│   │   ├── 04-完整执行流程.md          ← 端到端执行步骤
│   │   └── 07-快速参考手册.md          ← 字段和ID速查
│   │
│   ├── scripts/                       ← 🐍 执行脚本
│   │   ├── get_token.py               ← Token获取工具
│   │   ├── 01_process_groups.py       ← 分组处理（检查/创建）
│   │   └── 02_create_templates.py     ← 创建模板（完整版）
│   │
│   ├── config/                        ← ⚙️ 配置（自动生成）
│   ├── output/                        ← 📤 输出（自动生成）
│   │
│   └── success-cases/                 ← ✅ 成功案例
│       └── 案例1-单据模板自动化/        ← 5个模板全部成功记录
│
└── utils/                             ← 公共工具
    ├── get_token.py                   ← Token获取
    └── auto_config_helper.py          ← 配置辅助
```

---

## 📋 四个步骤详解

### Step 1: 添加员工
- **功能**: 从 Excel 批量添加员工到系统
- **方式**: API方式（推荐）或浏览器自动化
- **速度**: 0.8秒/人（API方式）
- **关键**: 部门名称 → departmentId 映射
- **文档**: `step-01-添加员工/README.md`

### Step 2: 添加费用模板
- **功能**: 批量添加二级费用科目
- **特点**: 自动继承父级配置（applyJson/feeJson/icon/iconColor）
- **关键 API**: `addFeeTemplate`
- **文档**: `step-02-添加费用模板/README.md`

### Step 3: 单据角色与人员授权
- **功能**: 创建单据角色并授权给指定人员
- **包含**:
  - (a) **创建单据角色**: 以单据类型命名（如"采购付款单"）
  - (b) **人员授权**: 将适配人员与单据角色绑定
- **关键 API**: `add/group`, `add`, `add/relation`
- **核心文件**: `费用科目配置表.xlsx`（角色+人员映射关系）
- **文档**: `step-03-单据角色与人员授权/README.md`
- **成功案例**: 包含2个完整实践案例

### Step 4: 创建单据模板
- **功能**: 批量创建单据模板（分组+模板+可见范围）
- **验证状态**: ✅ **2026-03-14 成功案例**（5个模板全部成功）
- **包含**:
  - (a) **分组处理**: 检查/创建 Excel 中的分组
  - (b) **模板创建**: 创建单据模板并配置可见范围
- **关键**: 角色/部门/员工 → ID 映射
- **核心文件**: `example_templates.xlsx`（单据模板配置表）
- **文档**: `step-04-创建单据模板/README.md`
- **教学文档**: `step-04-创建单据模板/docs/`
- **成功案例**: `step-04-创建单据模板/success-cases/`

---

## ⚙️ 配置说明

每个步骤文件夹内都有独立的 `config.json`：

```json
{
  "token": "从浏览器获取的x-token",
  "company_id": 7792,
  "base_url": "https://cst.uf-tree.com",
  "browser": {
    "host": "127.0.0.1",
    "port": 9222,
    "type": "Edge"
  },
  "department_map": {
    "测试门店1": 9151,
    "测试门店2": 9152
  }
}
```

### 端口灵活切换

**优先级**: CLI参数 > config.json > 环境变量 > 默认值(9222)

```bash
# 方式1: 修改 config.json
vim config.json  # 修改 browser.port

# 方式2: 命令行参数
python scripts/get_token.py --port 9223

# 方式3: 环境变量
export CAISHUI_BROWSER_PORT=9223
python scripts/get_token.py
```

**获取 Token**:
```bash
cd utils
python get_token.py
```

---

## ✅ 验证状态

| 步骤 | 状态 | 验证日期 | 备注 |
|------|------|----------|------|
| Step 1 添加员工 | ✅ 可用 | 2026-03-13 | API方式测试通过 |
| Step 2 添加费用模板 | ✅ 可用 | 2026-03-13 | Excel读取正常 |
| Step 3 流程配置 | ✅ 可用 | 2026-03-13 | 所有API可访问 |
| Step 4 创建单据模板 | ✅ **成功** | 2026-03-14 | 5个模板全部创建成功 |

---

## ⚠️ 重要提示

1. **Token 有效期**: 约30分钟，过期需重新获取
2. **浏览器调试**: 统一使用端口 **9222**
3. **执行顺序**: 必须按 Step 1 → 2 → 3 → 4 顺序执行
4. **数据备份**: 建议在执行前备份现有数据

---

## 📚 原项目位置

本项目是从以下原项目整理而来：

- `caishui-add-staff` → `step-01-添加员工/`
- `caishui-fee-template-skill` → `step-02-添加费用模板/`
- `caishui-three-step-closure-skill` → `step-03-流程配置/`
- `单据模板试验/单据模板试验成功案例1/` → `step-04-创建单据模板/`

**原项目位置**: `/Users/tang/Desktop/自动添加员工项目/`

---

## 🎯 给其他 AI 的提示

如果你是接手这个项目的 AI：

1. **先读**: 本文件了解整体流程
2. **再读**: 每个步骤的 README.md 了解细节
3. **检查**: config.json 中的 Token 是否有效
4. **运行**: 按顺序执行四个步骤
5. **问题**: 查看各步骤 README 中的"常见问题"章节

---

*整理日期: 2026-03-15*
*整理方式: 仅移动文件位置，代码原封不动*
