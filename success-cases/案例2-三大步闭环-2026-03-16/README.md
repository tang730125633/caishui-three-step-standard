# 案例2：三大步闭环（2026-03-16）

> 这是“纠偏后”的标准案例：**流程只有 3 步，不是 4 步**。

---

## 0. 先看结论（给新人）

- ✅ Step1 成功：8/8
- ✅ Step2 成功：25/25
- ✅ Step3 成功：8/8
- ✅ 这是一个可复用的完整闭环案例

最终报告：`执行报告-修复重跑.json`

---

## 1. 最终正确流程（严格边界）

### Step1：添加员工（Sheet: `01_添加员工`）
只做员工导入：姓名、手机号、部门。

### Step2：业务处理核心（Sheet: `02_费用科目配置`）
只做 3 件事：
1. 根据一级科目创建/复用二级科目
2. 创建/复用“费用角色组”与子角色（子角色名=归属单据类型）
3. 将“单据适配人员”绑定到子角色，并关联二级科目

### Step3：创建单据模板（Sheet: `03_单据表`）
只做模板创建（分组 + 模板 + 可见范围）。

> ⚠️ Step3 不允许重复做 Step2 的动作（不再创建二级科目、不再创建费用角色组）

---

## 2. 输入文件

- `批量表_2.xlsx`
  - Sheet1: `01_添加员工`
  - Sheet2: `02_费用科目配置`
  - Sheet3: `03_单据表`

---

## 2.5 前置拦截（强烈建议先执行）

在跑 Step2/Step3 前，先检查 Excel 中一级费用科目是否已在系统存在：

```bash
python /Users/tang/Desktop/财税通自动化三大步标准方案/step-02-费用科目与角色绑定/scripts/precheck_primary_subjects.py \
  --excel "/Users/tang/Desktop/财税通自动化三大步标准方案/success-cases/案例2-三大步闭环-2026-03-16/批量表_2.xlsx"
```

- 通过（exit code=0）：继续执行
- 不通过（exit code=2）：先补齐一级科目，否则后续必失败

## 2.6 可见范围一致性检查（Step3 前强制）

在创建单据模板前，先校验 Sheet3 的“可见范围类型/对象”是否匹配：

```bash
python /Users/tang/Desktop/财税通自动化三大步标准方案/step-03-创建单据模板/scripts/precheck_visibility_scope.py \
  --excel "/Users/tang/Desktop/财税通自动化三大步标准方案/success-cases/案例2-三大步闭环-2026-03-16/批量表_2.xlsx"
```

规则：
- 角色类目：对象必须是角色（不能写员工/部门）
- 员工类目：对象必须在公司员工列表存在（不能写角色/部门）
- 部门类目：对象必须是部门名称（不能写角色/员工）

不通过（exit code=2）时，必须先修 Excel 再继续。

## 3. 浏览器 Token 获取（最小可行步骤）

> OpenClaw 的脚本需要从已登录浏览器会话拿 token。

### 3.1 启动带调试端口的 Edge

macOS:
```bash
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9223
```

Windows（PowerShell）:
```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9223
```

### 3.2 登录财税通

在该 Edge 窗口里登录：`https://cst.uf-tree.com`

### 3.3 验证调试端口

浏览器访问：
- `http://127.0.0.1:9223/json/version`
- `http://127.0.0.1:9223/json/list`

能返回 JSON 即正常。

### 3.4 脚本自动读取 token

本案例脚本通过 CDP（9223）读取 `localStorage.vuex` 中的：
- `user.token`
- `user.company.id`
- `user.id`

> 如果提示“未找到已登录页面”，通常是：
> 1) 端口不对；2) 该浏览器窗口没登录财税通；3) 被公司策略拦截调试端口。

---

## 4. 本案例关键修复点（必须理解）

### 修复 A：Sheet2 一级费用科目 forward fill

原因：`02_费用科目配置` 有合并单元格，后续行会读成空值/NaN。

做法：对 `一级费用科目` 先 `ffill()` 再执行业务过滤。

### 修复 B：子角色创建必须带 parentId + _parentId

创建子角色接口 `/api/member/role/add` 必须带：
- `parentId`
- `_parentId`
- `dataType=FEE_TYPE`

父ID来源：`/api/member/role/get/tree` 里匹配“费用角色组”节点。

### 修复 C：Step3 与 Step2 完全解耦

Step3 只创建单据模板，不再创建二级科目/费用角色组。

---

## 5. 已确认接口（案例2使用）

1. `POST /api/bill/template/createTemplateGroup`
2. `GET /api/bill/template/queryTemplateTree`
3. `POST /api/bill/template/createTemplate`
4. `POST /api/bill/template/queryTemplate`
5. `POST /api/member/department/queryCompany`
6. `GET /api/member/department/queryDepartments`
7. `GET /api/member/role/get/tree`
8. `GET /api/bill/feeTemplate/queryFeeTemplate`

---

## 6. 结果产物

- 原始日志：
  - `step1.log`
  - `step2.log`
  - `step2_bind.log`
  - `step3_group.log`
  - `step3_template.log`
- 修复重跑日志：
  - `step2_corrected.log`
  - `step3_corrected.log`
- 报告：
  - `执行报告.md`（首轮）
  - `执行报告-修复重跑.json`（最终）
- 映射：
  - `fee_template_mapping.from_step2.corrected.json`

---

## 7. Windows 上跑 OpenClaw 的建议

请直接看：`Windows-执行指引.md`

内容包括：
- Windows 启动 Edge + CDP
- OpenClaw 命令行执行建议
- 常见错误与排查顺序

---

## 8. 一句话给新人

先保证 **Token 可读**，再按 **Step1→Step2→Step3** 执行；
**Step2 是核心，Step3 不要越界重复做 Step2 的事**。
