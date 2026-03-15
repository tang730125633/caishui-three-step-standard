#!/usr/bin/env python3
"""
Bootstrap next Caishui round folder from previous success-case.

Example:
  python create_next_round.py \
    --base "/Users/tang/Desktop/财税通自动化三大步标准方案/success-cases" \
    --prev "案例4-三大步闭环-2026-03-16" \
    --next-round 5
"""

from pathlib import Path
import argparse
import re
import shutil
from datetime import datetime


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, help="success-cases directory")
    p.add_argument("--prev", required=True, help="previous case folder name")
    p.add_argument("--next-round", type=int, required=True, help="next round number, e.g. 5")
    args = p.parse_args()

    base = Path(args.base)
    prev_dir = base / args.prev
    if not prev_dir.exists():
        raise SystemExit(f"Previous case folder not found: {prev_dir}")

    today = datetime.now().strftime("%Y-%m-%d")
    next_dir = base / f"案例{args.next_round}-三大步闭环-{today}"
    next_dir.mkdir(parents=True, exist_ok=True)

    prev_excel = sorted(prev_dir.glob("批量表_*.xlsx"))
    if not prev_excel:
        raise SystemExit(f"No 批量表_*.xlsx found in {prev_dir}")
    src_excel = prev_excel[0]
    dst_excel = next_dir / f"批量表_{args.next_round}.xlsx"
    shutil.copy2(src_excel, dst_excel)

    readme = next_dir / "README.md"
    readme.write_text(
        f"# 案例{args.next_round}：三大步闭环（第{args.next_round}轮测试）\n\n"
        f"## 输入文件\n- {dst_excel.name}\n\n"
        "## 建议执行顺序\n"
        "1. precheck_primary_subjects.py\n"
        "2. precheck_visibility_scope.py\n"
        "3. Step1 -> Step2 -> Step3\n",
        encoding="utf-8",
    )

    print(next_dir)
    print(dst_excel)


if __name__ == "__main__":
    main()
