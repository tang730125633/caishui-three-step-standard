# 财税通三步闭环 API 接口文档

> **生成日期**: 2026-03-11  
> **版本**: v1.0  
> **基础URL**: `https://cst.uf-tree.com`

---

## 📋 接口清单

| 步骤 | 接口名称 | 方法 | 端点 |
|------|---------|------|------|
| 1 | 添加二级科目 | POST | `/api/bill/feeTemplate/addFeeTemplate` |
| 1 | 获取一级科目详情 | GET | `/api/bill/feeTemplate/getFeeTemplateById` |
| 1 | 查询费用模板列表 | GET | `/api/bill/feeTemplate/queryFeeTemplate` |
| 2 | 创建角色组 | POST | `/api/member/role/add/group` |
| 2 | 创建子角色 | POST | `/api/member/role/add` |
| 3 | 获取员工列表 | POST | `/api/member/department/queryCompany` |
| 3 | 保存角色关系 | POST | `/api/member/role/add/relation` |

---

## 第一步：添加二级科目

### 1.1 添加二级科目

**URL**: `POST /api/bill/feeTemplate/addFeeTemplate`

**Headers**:
```
x-token: {从浏览器获取的token}
Content-Type: application/json
```

**请求体模板**:
```json
{
  "userId": 14939,
  "companyId": 7792,
  "name": "机器设备",
  "parentId": 22062,
  "icon": "md-plane",
  "iconColor": "#4c7cc3",
  "status": "1",
  "parentFlag": "0",
  "defaultFlag": false,
  "forceShare": 0,
  "shareDepPermission": 2,
  "applyJson": [...父级applyJson...],
  "feeJson": [...父级feeJson...]
}
```

**关键字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `userId` | Integer | 是 | 当前用户ID |
| `companyId` | Integer | 是 | 公司ID |
| `name` | String | 是 | 二级科目名称 |
| `parentId` | Integer | 是 | 父级（一级科目）ID |
| `parentFlag` | String | 是 | "0"表示二级科目 |
| `applyJson` | Array | 是 | **必须继承父级** |
| `feeJson` | Array | 是 | **必须继承父级** |

**成功响应示例**:
```json
{
  "code": 200,
  "message": "成功",
  "result": 28042
}
```

---

### 1.2 获取一级科目详情

**URL**: `GET /api/bill/feeTemplate/getFeeTemplateById`

**Headers**:
```
x-token: {token}
```

**Query参数**:
```
id: 22062
companyId: 7792
```

**成功响应示例**:
```json
{
  "code": 200,
  "result": {
    "id": 22062,
    "name": "固定资产",
    "parentId": -1,
    "parentFlag": "1",
    "status": "1",
    "applyJson": [{"name":"amount","label":"申请金额"}],
    "feeJson": [{"name":"invoice","label":"发票"}],
    "icon": "md-plane",
    "iconColor": "#4c7cc3"
  }
}
```

---

### 1.3 查询费用模板列表

**URL**: `GET /api/bill/feeTemplate/queryFeeTemplate`

**Headers**:
```
x-token: {token}
```

**Query参数**:
```
companyId: 7792
status: 1
pageSize: 1000
```

**成功响应示例**:
```json
{
  "code": 200,
  "result": [
    {
      "id": 22062,
      "name": "固定资产",
      "parentId": -1,
      "parentFlag": "1"
    },
    {
      "id": 28042,
      "name": "机器设备",
      "parentId": 22062,
      "parentFlag": "0"
    }
  ]
}
```

---

## 第二步：创建角色体系

### 2.1 创建角色组（父节点）

**URL**: `POST /api/member/role/add/group`

**Headers**:
```
x-token: {token}
Content-Type: application/json
```

**请求体模板**:
```json
{
  "companyId": 7792,
  "name": "费用角色组"
}
```

**成功响应示例**:
```json
{
  "code": 200,
  "message": "成功",
  "result": 22164
}
```
**注意**: `result` 返回的是新创建的父节点ID，后续创建子角色需要用到！

---

### 2.2 创建子角色

**URL**: `POST /api/member/role/add`

**Headers**:
```
x-token: {token}
Content-Type: application/json
```

**请求体模板**:
```json
{
  "companyId": 7792,
  "name": "采购付款单",
  "_parentId": 22164,
  "parentId": 22164,
  "dataType": "FEE_TYPE"
}
```

**关键字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `_parentId` | Integer | 是 | 父节点ID（**必须带下划线**） |
| `parentId` | Integer | 是 | 父节点ID（不带下划线） |
| `dataType` | String | 是 | 固定值 `"FEE_TYPE"` |
| `name` | String | 是 | 角色名称（单据类型） |

**成功响应示例**:
```json
{
  "code": 200,
  "message": "成功",
  "result": 22165
}
```

---

## 第三步：配置费用类型和人员

### 3.1 获取员工列表

**URL**: `POST /api/member/department/queryCompany`

**Headers**:
```
x-token: {token}
Content-Type: application/json
```

**请求体模板**:
```json
{
  "companyId": 7792
}
```

**成功响应示例**:
```json
{
  "code": 200,
  "result": {
    "users": [
      {
        "id": 13961,
        "nickName": "韩老师"
      },
      {
        "id": 14824,
        "nickName": "张总"
      }
    ]
  }
}
```

**映射规则**: 使用 `nickName` 作为匹配键，使用 `id` 作为员工ID

---

### 3.2 保存角色关系（绑定费用类型和人员）

**URL**: `POST /api/member/role/add/relation`

**Headers**:
```
x-token: {token}
Content-Type: application/json
```

**请求体模板**:
```json
{
  "roleId": 22165,
  "userIds": [13961, 14824],
  "feeTemplateIds": [28042, 28043],
  "companyId": 7792
}
```

**关键字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `roleId` | Integer | 是 | 角色ID |
| `userIds` | Array | 是 | 员工ID列表（可多个） |
| `feeTemplateIds` | Array | 是 | 费用模板ID列表（可多个） |
| `companyId` | Integer | 是 | 公司ID |

**成功响应示例**:
```json
{
  "code": 200,
  "message": "成功"
}
```

---

## 🔐 认证信息获取

### 从浏览器获取 Token 和 Company ID

**方法**: 通过 Chrome DevTools Protocol (CDP)

**Python 示例**:
```python
import json
import requests
import websocket

CDP_PORT = "9223"

# 1. 获取页面列表
resp = requests.get(f"http://localhost:{CDP_PORT}/json/list", timeout=10)
pages = resp.json()

# 2. 找到财税通页面
ws_url = None
for page in pages:
    if "cst.uf-tree.com" in page.get("url", ""):
        ws_url = page["webSocketDebuggerUrl"]
        break

# 3. 连接WebSocket获取Token
ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)
ws.send(json.dumps({
    "id": 1,
    "method": "Runtime.evaluate",
    "params": {"expression": "localStorage.getItem('vuex')", "returnByValue": True}
}))

token = None
company_id = None
user_id = None

for _ in range(10):
    resp = ws.recv()
    data = json.loads(resp)
    if data.get("id") == 1:
        value = data.get("result", {}).get("result", {}).get("value")
        if value:
            parsed = json.loads(value)
            token = parsed["user"]["token"]
            company_id = parsed["user"]["company"]["id"]
            user_id = parsed["user"].get("id", 14939)
        break

ws.close()
print(f"Token: {token}")
print(f"Company ID: {company_id}")
print(f"User ID: {user_id}")
```

---

## ⚠️ 关键注意事项

1. **继承机制**: 二级科目必须继承一级科目的 `applyJson` 和 `feeJson` 字段
2. **ID 映射**: 不要猜测ID，必须通过 API 查询获取
3. **字段格式**: `_parentId` 必须带下划线，`parentId` 不带下划线
4. **匹配键**: 员工匹配使用 `nickName`，不要使用 `name`

---

**文档版本**: v1.0  
**最后更新**: 2026-03-11

---

## 附录：单据模板自动化接口（新增）

> 以下接口用于单据模板批量创建，与三步闭环独立

### 接口清单

| 接口名称 | 方法 | 端点 | 用途 |
|---------|------|------|------|
| createTemplateGroup | POST | `/api/bill/template/createTemplateGroup` | 创建单据分组 |
| queryTemplateTree | GET | `/api/bill/template/queryTemplateTree` | 查询分组树、获取groupId |
| createTemplate | POST | `/api/bill/template/createTemplate` | 创建单据模板（主接口） |
| queryTemplate | POST | `/api/bill/template/queryTemplate` | 查询模板详情（核对结果） |
| queryDepartments | GET | `/api/member/department/queryDepartments` | 部门名称→departmentId |
| getRoleTree | GET | `/api/member/role/get/tree` | 查询完整角色树 |

---

### A.1 创建单据分组

**URL**: `POST /api/bill/template/createTemplateGroup`

**Headers**:
```
x-token: {token}
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "报销及付款单据1",
  "companyId": 7792
}
```

**成功响应**:
```json
{
  "code": 200,
  "success": true,
  "message": "处理成功",
  "result": null
}
```

**注意**: 创建成功后需再次调用 queryTemplateTree 获取新分组ID

---

### A.2 查询单据模板树

**URL**: `GET /api/bill/template/queryTemplateTree`

**Query参数**:
```
companyId: 7792
t: {毫秒时间戳}
```

**成功响应**:
```json
{
  "code": 200,
  "result": [
    {
      "id": 4487,
      "name": "付款报销单",
      "children": [
        {
          "id": 4201,
          "name": "员工报销单",
          "groupId": 4487,
          "type": "报销单",
          "status": 1
        }
      ]
    }
  ]
}
```

---

### A.3 创建单据模板（主接口）

**URL**: `POST /api/bill/template/createTemplate`

**Headers**:
```
x-token: {token}
Content-Type: application/json
```

**完整请求体模板**:
```json
{
  "applyRelateFlag": true,
  "applyRelateNecessary": false,
  "businessType": "PRIVATE",
  "companyId": 7792,
  "componentJson": [...],
  "departmentIds": [9151],
  "feeIds": [],
  "feeScopeFlag": false,
  "groupId": 4489,
  "icon": "md-pricetag",
  "iconColor": "#4c7cc3",
  "loanIds": [],
  "name": "员工报销单",
  "payFlag": true,
  "requestScope": false,
  "requisitionIds": [],
  "roleIds": [],
  "status": "ACTIVE",
  "type": "EXPENSE",
  "userIds": [10749],
  "userScopeFlag": true,
  "workFlowId": 12791,
  "applyContentType": "TEXT"
}
```

**关键字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `groupId` | Integer | 是 | 分组ID |
| `type` | String | 是 | 单据类型枚举：EXPENSE/LOAN/REQUISITION/PAYMENT/ACCRUAL |
| `name` | String | 是 | 模板名称 |
| `workFlowId` | Integer | 是 | 审批流ID（12791=通用审批） |
| `departmentIds` | Array | 三选一 | 部门可见范围 |
| `roleIds` | Array | 三选一 | 角色可见范围 |
| `userIds` | Array | 三选一 | 员工可见范围 |
| `applyContentType` | String | 条件 | 申请单必填，值如"TEXT" |

**成功响应**:
```json
{
  "code": 200,
  "success": true,
  "result": {
    "id": 7014,
    "name": "员工报销单",
    "type": "EXPENSE",
    "groupId": 4489,
    ...
  }
}
```

---

### A.4 查询模板详情

**URL**: `POST /api/bill/template/queryTemplate`

**Headers**:
```
x-token: {token}
Content-Type: application/json
```

**请求体**:
```json
{
  "companyId": 7792,
  "templateId": 7014
}
```

**用途**: 创建后核对模板是否存在

---

### A.5 查询部门列表

**URL**: `GET /api/member/department/queryDepartments`

**Query参数**:
```
companyId: 7792
```

**成功响应**:
```json
{
  "code": 200,
  "result": [
    {
      "id": 9151,
      "title": "测试门店1"
    },
    {
      "id": 9152,
      "title": "测试门店2"
    }
  ]
}
```

**映射规则**: 使用 `title` 匹配部门名称，使用 `id` 作为departmentId

---

### A.6 查询角色树（完整角色体系）

**URL**: `GET /api/member/role/get/tree`

**Query参数**:
```
companyId: 7792
```

**成功响应**:
```json
{
  "code": 200,
  "result": [
    {
      "name": "职级",
      "id": 18288,
      "children": [
        {"name": "普通职员", "id": 18289},
        {"name": "店长", "id": 22209}
      ]
    },
    {
      "name": "职务",
      "id": 18292,
      "children": [
        {"name": "部门经理", "id": 18294},
        {"name": "出纳", "id": 18296}
      ]
    },
    {
      "name": "费用角色组",
      "id": 22221,
      "children": [
        {"name": "采购付款单", "id": 22222}
      ]
    }
  ]
}
```

**重要**: 这才是查询可见范围角色的正确接口，不是从员工数据中提取！

---

### A.7 type枚举值映射

| 中文（Excel） | 枚举值（Payload） |
|-------------|------------------|
| 报销单 | `EXPENSE` |
| 借款单 | `LOAN` |
| 申请单 | `REQUISITION` |
| 批量付款单 | `PAYMENT` |
| 计提单 | `ACCRUAL` |

---

**新增接口版本**: v1.1  
**新增日期**: 2026-03-14  
**关联项目**: 单据模板试验成功案例1
