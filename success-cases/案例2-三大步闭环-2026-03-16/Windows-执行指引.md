# Windows 执行指引（OpenClaw + 财税通三步闭环）

> 目标：让 Windows 新手能 10 分钟内完成可执行环境准备。

---

## 1. 你需要准备什么

1. 已安装 Microsoft Edge
2. 已安装 Python 3（建议 3.10+）
3. 能运行 OpenClaw（桌面版或 CLI）
4. 能访问财税通并登录企业账号

---

## 2. 在 Windows 启动 Edge 调试模式（关键）

### PowerShell 命令

```powershell
# 先关闭已打开的 Edge（可选）
taskkill /F /IM msedge.exe

# 启动带 CDP 端口的 Edge
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9223 --no-first-run --no-default-browser-check
```

如果你是 64 位安装路径，也可能是：
`C:\Program Files\Microsoft\Edge\Application\msedge.exe`

### 验证端口

浏览器访问：
- `http://127.0.0.1:9223/json/version`
- `http://127.0.0.1:9223/json/list`

看到 JSON 表示成功。

---

## 3. 登录财税通并确认 token 可读取

1. 在刚启动的 Edge 中打开 `https://cst.uf-tree.com`
2. 登录企业账号
3. 保持页面不关闭

脚本会从 `localStorage.vuex` 读取：
- `user.token`
- `user.company.id`
- `user.id`

---

## 4. 三步执行建议（Windows）

### Step1 添加员工
- 输入来源：`01_添加员工`
- 目标：新增员工并得到可查询 userId

### Step2 费用科目+角色绑定（核心）
- 输入来源：`02_费用科目配置`
- 注意事项：
  - 一级费用科目要做 `forward fill`
  - 子角色创建必须传 `_parentId + parentId + dataType=FEE_TYPE`
  - 二级科目重复时应复用，不算失败

### Step3 创建单据模板
- 输入来源：`03_单据表`
- 只做模板创建，不重复 Step2 行为

---

## 5. 常见错误与排查顺序

### 错误 A：未找到财税通页面
排查：
1. Edge 是否用 `--remote-debugging-port=9223` 启动
2. 是否在该窗口登录了财税通
3. `http://127.0.0.1:9223/json/list` 是否可访问

### 错误 B：role/add 返回“输入参数异常”
排查：
1. 是否传了 `_parentId`
2. 是否传了 `parentId`
3. parentId 是否来自 `role/get/tree` 的“费用角色组”节点

### 错误 C：一级科目出现 NaN
排查：
1. Sheet2 是否存在合并单元格
2. 读取后是否执行了 `一级费用科目.ffill()`

### 错误 D：模板可见范围为空
排查：
1. 可见范围对象是否多值拆分（`， , 、 ; ；`）
2. 角色/部门/员工是否命中查询结果

---

## 6. 给 Windows 新手的执行口令（简版）

1. 启动 Edge(9223)
2. 登录财税通
3. 跑三步流程（严格边界）
4. 看日志：Step2 先绿，再看 Step3

只要 Step2 成功，Step3 基本就稳。
