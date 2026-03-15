#!/usr/bin/env python3
"""
添加费用模板 - 兼容入口

此脚本为兼容入口，实际逻辑在 scripts/add_fee_templates.py
建议新用户使用: python scripts/add_fee_templates.py
"""

import sys
import os

# 将 scripts 目录添加到路径
script_dir = os.path.join(os.path.dirname(__file__), "scripts")
sys.path.insert(0, script_dir)

# 导入并执行主脚本
exec(open(os.path.join(script_dir, "add_fee_templates.py")).read())
