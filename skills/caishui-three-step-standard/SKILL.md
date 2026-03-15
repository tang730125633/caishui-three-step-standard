---
name: caishui-three-step-standard
description: Build, execute, and iterate the Caishui 3-step automation workflow (Step1 employee import, Step2 fee-subject+role binding, Step3 template creation) with strict prechecks and reproducible success-case archiving. Use when users ask to run new rounds, generate batch Excel files, enforce step boundaries, or convert legacy 4-step materials into the standardized 3-step process.
---

# Caishui Three-Step Standard

Execute the 财税通自动化三大步标准方案 with deterministic guardrails and reusable artifacts.

## Project Root Convention

Set project root before running commands:

```bash
export PROJECT_ROOT="/path/to/caishui-three-step-standard"
```

All commands below use `$PROJECT_ROOT` (no machine-specific absolute paths).

## Core Boundary (must enforce)

- Step1: Add employees (Sheet `01_添加员工`) only.
- Step2: Handle fee-subject + role logic (Sheet `02_费用科目配置`) only:
  - Reuse/create secondary fee subjects
  - Reuse/create fee role group + child roles (from `归属单据类型`)
  - Bind users + fee subjects
- Step3: Create bill templates (Sheet `03_单据表`) only.
- Never let Step3 recreate Step2 resources.

## Mandatory Prechecks Before Execution

Run both checks before Step2/Step3:

1. Primary subject existence check
```bash
python "$PROJECT_ROOT/step-02-费用科目与角色绑定/scripts/precheck_primary_subjects.py" --excel "<excel_path>"
```
- Exit 0: continue
- Exit 2: stop and ask user to create missing primary subjects

2. Visibility scope consistency check
```bash
python "$PROJECT_ROOT/step-03-创建单据模板/scripts/precheck_visibility_scope.py" --excel "<excel_path>"
```
- Exit 0: continue
- Exit 2: stop and request Excel correction

## Execution Order

1. Validate browser/session auth (Edge CDP 9223 + logged in cst.uf-tree.com)
2. Run precheck #1 and #2
3. Run Step1
4. Run Step2
5. Run Step3
6. Write reports/logs into the target success-case folder

## Standard Failure Handling

- Step1: treat “该用户已在本企业 / 已存在 / 重复” as skip, not fatal fail.
- Step2:
  - Apply forward-fill on `一级费用科目` (merged-cell Excel layouts)
  - For `role/add`, always include `_parentId`, `parentId`, `dataType=FEE_TYPE`
  - Resolve parent role group ID from `GET /api/member/role/get/tree` (`费用角色组`)
- Step3:
  - Parse multi-value scope objects with `， , 、 ; ； | /`
  - Retry once on template-name duplication with suffix `_R{round}_{HHMMSS}`

## Round Iteration Pattern

When user asks “start next round”:
1. Create a new case folder under `$PROJECT_ROOT/success-cases/案例N-三大步闭环-YYYY-MM-DD/`
2. Clone previous round Excel into `批量表_N.xlsx`
3. Update round tag in names (`R3` -> `R4`, etc.) to avoid collisions
4. Run prechecks + import flow
5. Generate summary docs in current case folder

Use `scripts/create_next_round.py` to bootstrap round folders quickly.

## References

- Use `references/source-map.md` for folder mapping and migration notes.
- Use `references/three-step-playbook.md` for operational checklist and response patterns.
