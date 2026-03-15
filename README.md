# 财税通自动化三大步标准方案

> 目标：客户提交一个三 Sheet Excel，即可按三大步完成自动化执行。

## 三大步（对应三张表）
1. **Step1 添加员工**（Sheet: `01_添加员工`）
2. **Step2 费用科目与角色绑定**（Sheet: `02_费用科目配置`）
   - 添加/复用二级费用科目
   - 创建/复用费用角色组与子角色（按归属单据类型）
   - 绑定单据适配人员 + 二级费用科目
3. **Step3 创建单据模板**（Sheet: `03_单据表` / `正式填写表`）

## 本次成功经验（必须先读）
- `docs/2026-03-16-关键卡点复盘-多值拆分与防重策略.md`

## 最新成功案例（推荐入口）
- `success-cases/案例4-三大步闭环-2026-03-16/`
  - 复盘：`001-第四轮成功复盘.md`
  - 执行报告：`执行报告-第四轮.json`
  - 前置检查：`precheck_primary_subjects.json`、`precheck_visibility_scope.json`

## 首个可复用案例
- `success-cases/案例1-三大步闭环-2026-03-16/`
  - `批量表_1.xlsx`
  - `执行报告.md`
  - `raw_logs.json`

## 接口总表入口
- `step-02-费用科目与角色绑定/api_summary.md`
  - 覆盖：费用科目、角色组/子角色、人员绑定等核心接口
- `step-03-创建单据模板/README.md`
  - 覆盖：模板分组、模板创建、可见范围查询与映射

## 目录结构
- `step-01-添加员工/`
- `step-02-费用科目与角色绑定/`
- `step-03-创建单据模板/`
- `docs/`
- `success-cases/`
- `legacy-from-四步标准方案/`
- `skills/caishui-three-step-standard/`（可复用 Skill）

## Skill 用法（给小白 AI）
1. 将仓库克隆到本地，设置：
   ```bash
   export PROJECT_ROOT="/path/to/caishui-three-step-standard"
   ```
2. 优先阅读：
   - `skills/caishui-three-step-standard/SKILL.md`
   - `skills/caishui-three-step-standard/references/three-step-playbook.md`
3. 执行前先跑双前置检查：
   - 一级科目存在性检查
   - 可见范围一致性检查
4. 严格按 Step1 -> Step2 -> Step3 执行，不跨步。

## 新人 AI 避坑清单
1. 可见范围多值必须统一拆分（`， , 、 ; ；`）
2. 模板/费用科目名称重复不算失败，优先复用 ID
3. Step3 不重复创建二级科目，只复用 Step2 结果
4. 费用角色组不参与单据模板可见范围对象
5. token 失效（401）先重登，再执行
