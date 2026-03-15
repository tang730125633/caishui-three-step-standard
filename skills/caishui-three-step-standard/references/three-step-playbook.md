# Three-Step Playbook

## A. Before Running

1. Confirm user target Excel path
2. Confirm Edge CDP is available on 9223
3. Confirm user is logged in `https://cst.uf-tree.com`

## B. Guardrails

- Guardrail 1: primary subjects must exist in system
- Guardrail 2: visibility type/object must match

If any guardrail fails:
- Stop execution
- Return concrete mismatch list
- Ask user to fix Excel, then rerun

## C. Step Intent Contract

- Step1 = employee import only
- Step2 = fee+role+binding only
- Step3 = template creation only

Never duplicate Step2 logic inside Step3.

## D. Reporting Contract

For each round, always produce:
- precheck report JSON(s)
- step1/step2/step3 logs
- one merged execution report JSON
- one markdown recap (`001-第N轮成功复盘.md`)

## E. Human-facing Status Style

- Be concise and operational
- Highlight blockers first
- Separate “hard failure” vs “skip/reuse” clearly
- Provide next action in one sentence
