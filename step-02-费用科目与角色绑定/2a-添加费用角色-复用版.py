#!/usr/bin/env python3
import json
import requests
import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://cst.uf-tree.com"
EXCEL_PATH = Path('/Users/tang/Desktop/自动添加员工项目/三步闭环/科目配置表_已更新.xlsx')


def parse_multi(s):
    return [x.strip() for x in str(s).replace('，', ',').replace('、', ',').replace(';', ',').replace('；', ',').split(',') if x.strip()]


def get_auth():
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp('http://127.0.0.1:9223')
        page = None
        for c in b.contexts:
            for pg in c.pages:
                if 'uf-tree.com' in pg.url:
                    page = pg
                    break
            if page:
                break
        auth = page.evaluate("""() => {
            const v = localStorage.getItem('vuex');
            if (v) {
                const d = JSON.parse(v);
                return {token:d.user?.token, companyId:d.user?.company?.id, userId:d.user?.id};
            }
            return null;
        }""")
        b.close()
    if not auth or not auth.get('token'):
        raise RuntimeError('未获取到有效认证')
    return auth


def main():
    print('='*70)
    print('🚀 Step3 复用版（不重复创建二级科目）')
    print('='*70)

    df = pd.read_excel(EXCEL_PATH)
    auth = get_auth()
    token, company_id = auth['token'], auth['companyId']
    headers = {'x-token': token, 'Content-Type': 'application/json'}

    # 1) 查询费用模板，构建一级/二级映射（复用 Step2 结果）
    resp = requests.get(f'{BASE_URL}/api/bill/feeTemplate/queryFeeTemplate', headers=headers, params={'companyId': company_id, 'status': 1, 'pageSize': 1000}, timeout=15)
    templates = resp.json().get('result', []) if resp.status_code == 200 else []
    parent_map = {t.get('name'): t.get('id') for t in templates if t.get('parentId') == -1 and t.get('name')}
    # 从树 children 构建二级映射
    child_map = {}
    for p in templates:
        pid = p.get('id')
        for c in p.get('children', []) or []:
            cname, cid = c.get('name'), c.get('id')
            if pid and cname and cid:
                child_map[(pid, cname)] = cid

    # 叠加 Step2 输出映射（优先使用）
    mapping_file = Path(__file__).parent / 'fee_template_mapping.from_step2.json'
    if mapping_file.exists():
        try:
            m = json.loads(mapping_file.read_text(encoding='utf-8'))
            for it in m.get('items', []):
                pid = it.get('parentId')
                name = it.get('secondaryName')
                fid = it.get('feeTemplateId')
                if pid and name and fid:
                    child_map[(pid, name)] = fid
            print(f"✅ 已加载 Step2 映射: {mapping_file}")
        except Exception as e:
            print(f"⚠️ Step2映射读取失败: {e}")

    print(f'✅ 一级科目映射: {len(parent_map)}')
    print(f'✅ 二级科目映射: {len(child_map)}')

    # 2) 创建/复用角色组
    rg = requests.post(f'{BASE_URL}/api/member/role/add/group', headers=headers, json={'companyId': company_id, 'name': '费用角色组'}, timeout=15).json()
    if rg.get('code') == 200 and rg.get('result'):
        print(f"✅ 角色组创建成功: {rg.get('result')}")
    else:
        print(f"ℹ️ 角色组复用: {rg.get('message')}")

    # 拉角色树，拿费用角色组现有角色
    tree = requests.get(f'{BASE_URL}/api/member/role/get/tree', headers=headers, params={'companyId': company_id}, timeout=15).json().get('result', [])
    role_map = {}
    for cat in tree:
        if cat.get('name') == '费用角色组':
            for r in cat.get('children', []) or []:
                if r.get('name') and r.get('id'):
                    role_map[r['name']] = r['id']

    # 3) 创建缺失的单据类型角色（已存在则复用）
    doc_types = [x for x in df['归属单据类型'].dropna().unique().tolist() if str(x).strip()]
    for dt in doc_types:
        if dt in role_map:
            continue
        add = requests.post(f'{BASE_URL}/api/member/role/add', headers=headers, json={
            'companyId': company_id,
            'name': dt,
            'dataType': 'FEE_TYPE'
        }, timeout=15).json()
        # 无论成功与否都刷新一次树复用
        tree2 = requests.get(f'{BASE_URL}/api/member/role/get/tree', headers=headers, params={'companyId': company_id}, timeout=15).json().get('result', [])
        for cat in tree2:
            if cat.get('name') == '费用角色组':
                for r in cat.get('children', []) or []:
                    if r.get('name') and r.get('id'):
                        role_map[r['name']] = r['id']

    # 4) 用户映射
    users = requests.post(f'{BASE_URL}/api/member/department/queryCompany', headers=headers, json={'companyId': company_id}, timeout=15).json().get('result', {}).get('users', [])
    user_map = {u.get('nickName'): u.get('id') for u in users if u.get('nickName') and u.get('id')}

    # 5) 逐行绑定
    ok, fail = 0, 0
    failures = []
    for idx, row in df.iterrows():
        primary = str(row.get('一级科目类型', '')).strip()
        secondary = str(row.get('二级科目类型', '')).strip()
        doc_type = str(row.get('归属单据类型', '')).strip()
        people = parse_multi(row.get('单据适配人员', ''))

        parent_id = parent_map.get(primary)
        fee_id = child_map.get((parent_id, secondary)) if parent_id else None
        role_id = role_map.get(doc_type)
        user_ids = [user_map[p] for p in people if p in user_map]

        missing = []
        if not parent_id: missing.append(f'一级科目不存在:{primary}')
        if not fee_id: missing.append(f'二级科目不存在:{secondary}')
        if not role_id: missing.append(f'角色不存在:{doc_type}')
        if not user_ids: missing.append(f'人员未匹配:{people}')

        if missing:
            fail += 1
            failures.append({'row': idx+1, 'reason': ';'.join(missing)})
            print(f"[{idx+1}] ❌ 缺少必要信息: {';'.join(missing)}")
            continue

        payload = {'roleId': role_id, 'userIds': user_ids, 'feeTemplateIds': [fee_id], 'companyId': company_id}
        r = requests.post(f'{BASE_URL}/api/member/role/add/relation', headers=headers, json=payload, timeout=15).json()
        if r.get('code') == 200:
            ok += 1
            print(f'[{idx+1}] ✅ 关联成功')
        else:
            fail += 1
            msg = r.get('message', '未知错误')
            failures.append({'row': idx+1, 'reason': msg})
            print(f'[{idx+1}] ❌ {msg}')

    print('\n' + '='*70)
    print(f'结果: 成功 {ok} / 失败 {fail}')
    print('='*70)

    out = {
        'ok': ok,
        'fail': fail,
        'failures': failures,
        'companyId': company_id,
    }
    out_path = Path(__file__).parent / 'execution_result_reuse.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'💾 保存: {out_path}')


if __name__ == '__main__':
    main()
