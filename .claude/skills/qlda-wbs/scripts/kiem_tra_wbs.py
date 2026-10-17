"""Kiểm tra và chuẩn hóa WBS (lớp A cho dữ liệu WBS).

Dùng: python kiem_tra_wbs.py <wbs_nhap.json>
Kiểm tra: mã phân cấp, quy tắc 100% (tính khối lượng mục cha), gói lá có MD, loại công việc, sản phẩm,
phụ thuộc (tồn tại, không vòng), hạng mục Mẫu 01A (mọi hạng mục được phủ), truy vết yêu cầu RFP,
cỡ gói 2 đến 14 MD (cảnh báo), văn phong tên gói.
Đạt thì ghi du_lieu/wbs.json (đã tính khối lượng mục cha, ma trận truy vết), đăng ký phiên bản, ghi nhật ký.
Báo cáo: lam_viec/wbs/bao_cao_kiem_tra_wbs.json. Mã thoát 0 đạt, 1 còn lỗi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

src = sys.argv[1]
w = json.load(open(src, encoding='utf-8'))
hsmt = loi.doc_json('du_lieu/hsmt.json')
rfp = loi.doc_json('du_lieu/rfp_yeu_cau.json')
try:
    LOAI = set(loi.doc_json('dau_vao/don_gia.json')['loai_cong_viec'].keys())
except FileNotFoundError:
    LOAI = {'PM', 'BA', 'QA', 'DEV', 'DEVOPS'}
VP = json.load(open(os.path.join(loi.THU_MUC_LOI, 'references', 'van_phong.json'), encoding='utf-8'))
F = []


def add(ma, mo_ta, vi_tri='', muc_do='loi', cach_sua='can_nguoi_dung'):
    F.append({'ma': ma, 'muc_do': muc_do, 'nhom': 'wbs', 'vi_tri': vi_tri, 'mo_ta': mo_ta, 'cach_sua': cach_sua, 'de_xuat': ''})


goi = w.get('goi', [])
by = {}
for g in goi:
    m = str(g.get('ma', ''))
    if not re.fullmatch(r'\d+(\.\d+)*', m):
        add('W01', 'Mã không đúng dạng n, n.m, n.m.k', m); continue
    if m in by:
        add('W02', 'Mã trùng', m)
    by[m] = g
    if int(g.get('muc', 0)) != m.count('.') + 1:
        add('W03', f'Mức {g.get("muc")} không khớp số cấp của mã', m)
    if '.' in m and m.rsplit('.', 1)[0] not in by and m.rsplit('.', 1)[0] not in [x['ma'] for x in goi]:
        add('W04', 'Không có mục cha', m)
    if not str(g.get('ten', '')).strip():
        add('W05', 'Thiếu tên', m)
co_con = {m.rsplit('.', 1)[0] for m in by if '.' in m}
la = [g for m, g in by.items() if m not in co_con]
la_ma = {g['ma'] for g in la}

for g in la:
    m = g['ma']
    try:
        v = float(g.get('md'))
        if v <= 0:
            raise ValueError
    except (TypeError, ValueError):
        add('W10', 'Gói lá thiếu khối lượng md hợp lệ', m); continue
    if v < 2 or v > 14:
        add('W11', f'Gói {v:g} MD nằm ngoài khoảng 2 đến 14 MD, xem lại cách phân rã', m, 'canh_bao')
    if g.get('loai') not in LOAI:
        add('W12', f'Loại công việc {g.get("loai")} không thuộc {sorted(LOAI)}', m)
    if not str(g.get('san_pham', '')).strip():
        add('W13', 'Gói lá thiếu sản phẩm đầu ra', m, 'canh_bao')
    for p in g.get('phu_thuoc', []):
        if p not in la_ma:
            add('W14', f'Phụ thuộc {p} không phải gói lá có trong WBS', m)
    hm = g.get('hang_muc_01a', [])
    hm = hm if isinstance(hm, list) else [hm]
    hm = [int(x) if str(x).strip().isdigit() else x for x in hm]  # chấp nhận "5" như 5
    g['hang_muc_01a'] = hm
    if not hm:
        add('W15', 'Gói lá chưa gắn hạng mục Mẫu 01A', m)
    if not g.get('nguon'):
        add('W16', 'Gói lá chưa ghi nguồn yêu cầu (RFP hoặc HSMT)', m, 'canh_bao')
for g in goi:
    if g['ma'] in co_con and g.get('md') not in (None, ''):
        add('W17', 'Mục cha không ghi md (script tự tính theo quy tắc 100%)', g['ma'], 'canh_bao', 'tu_dong')

# vòng phụ thuộc
dep = {g['ma']: [p for p in g.get('phu_thuoc', []) if p in la_ma] for g in la}
mau = {}


def dfs(u, path):
    mau[u] = 1
    for v in dep.get(u, []):
        if mau.get(v) == 1:
            add('W18', 'Vòng phụ thuộc: ' + ' -> '.join(path + [u, v]), u)
        elif not mau.get(v):
            dfs(v, path + [u])
    mau[u] = 2


for u in dep:
    if not mau.get(u):
        dfs(u, [])

# Mẫu 01A
so_01a = {h['stt'] for h in hsmt['mau_01a']}
phu = {}
for g in la:
    for h in g.get('hang_muc_01a', []):
        if h not in so_01a:
            add('W20', f'Hạng mục Mẫu 01A số {h} không có trong HSMT', g['ma'])
        phu.setdefault(h, []).append(g['ma'])
for h in hsmt['mau_01a']:
    if h['stt'] not in phu:
        add('W21', f'Hạng mục Mẫu 01A số {h["stt"]} ({h["danh_muc"]}) chưa có gói nào', str(h['stt']))

# truy vết RFP
ma_rfp = {y['ma']: y for y in rfp['yeu_cau']}
khong_can = {x['ma']: x.get('ly_do', '') for x in w.get('khong_can_goi', [])}
truy_vet = {}
for g in la:
    for n in g.get('nguon', []):
        if re.fullmatch(r'R\d+', str(n)):
            if n not in ma_rfp:
                add('W30', f'Mã yêu cầu {n} không có trong rfp_yeu_cau.json', g['ma'])
            truy_vet.setdefault(n, []).append(g['ma'])
for y in rfp['yeu_cau']:
    if y['nhom'] in ('he_thong', 'san_pham', 'pham_vi', 'de_xuat', 'chinh_sach') and y['ma'] not in truy_vet:
        if y['ma'] in khong_can:
            if not khong_can[y['ma']].strip():
                add('W31', f'{y["ma"]} ghi không cần gói nhưng thiếu lý do', y['ma'])
        else:
            add('W32', f'Yêu cầu {y["ma"]} ({y["dien_giai"]}) chưa có gói đáp ứng', y['ma'])

# văn phong tên gói
for g in goi:
    for item in VP['tu_thay_the'] + VP['tu_can_xem']:
        if re.search(item['mau'], g.get('ten', '')):
            add('W40', f'Tên gói có từ không phù hợp: {re.search(item["mau"], g["ten"]).group(0)}', g['ma'], 'loi' if item in VP['tu_thay_the'] else 'canh_bao')
    if re.search('[–—]', g.get('ten', '')):
        add('W41', 'Tên gói có gạch dài', g['ma'], 'loi', 'tu_dong')

# quy tắc 100%: tính mục cha từ dưới lên
for m in sorted(by, key=lambda x: -x.count('.')):
    if m in co_con:
        con = [by[c] for c in by if c.rsplit('.', 1)[0] == m and '.' in c]
        by[m]['md'] = round(sum(float(c.get('md') or 0) for c in con), 2)
        by[m]['so_muc_con'] = len(con)
tong = round(sum(float(by[m].get('md') or 0) for m in by if '.' not in m), 2)
tong_la = round(sum(float(g.get('md') or 0) for g in la), 2)
if abs(tong - tong_la) > 1e-6:
    add('W50', f'Tổng mức 1 ({tong}) khác tổng gói lá ({tong_la})')

loi_ = [f for f in F if f['muc_do'] == 'loi']
bc = {'tep': loi.tuong_doi(src), 'ket_luan': 'dat' if not loi_ else 'chua_dat', 'so_loi': len(loi_), 'so_canh_bao': len(F) - len(loi_),
      'tong_md': tong, 'so_goi_la': len(la), 'phat_hien': F}
loi.ghi_json('lam_viec/wbs/bao_cao_kiem_tra_wbs.json', bc)
for f in F:
    print(f"[{f['muc_do']}] {f['ma']} {f['vi_tri']}: {f['mo_ta']}")
print(f'Tổng {tong:g} MD, {len(la)} gói lá, {len([m for m in by if "." not in m])} nhóm mức 1. Kết luận: {bc["ket_luan"]} ({len(loi_)} lỗi, {len(F) - len(loi_)} cảnh báo)')
if loi_:
    sys.exit(1)

goi_sorted = sorted(by.values(), key=lambda g: loi.khoa_ma(g['ma']))
for g in goi_sorted:
    g['la'] = g['ma'] not in co_con
    g['cha'] = g['ma'].rsplit('.', 1)[0] if '.' in g['ma'] else ''
nhom = [{'ma': g['ma'], 'ten': g['ten'], 'md': g['md'], 'ty_trong': g['md'] / tong} for g in goi_sorted if g['muc'] == 1]


def gon_ma(ds):
    """Thay các gói lá bằng mục cha khi mọi gói lá của mục cha đều có trong danh sách."""
    ds = set(ds); kq = set(ds)
    for c in sorted({g['cha'] for g in goi_sorted if g['la'] and g['cha']}, key=lambda m: -m.count('.')):
        con = {g['ma'] for g in goi_sorted if g['la'] and g['ma'].startswith(c + '.')}
        if con and con <= ds:
            kq = (kq - con) | {c}; ds = ds | {c}
    # bỏ mục con khi mục cha đã có
    kq = {m for m in kq if not any(m.startswith(x + '.') for x in kq if x != m)}
    return ', '.join(sorted(kq, key=lambda m: [int(x) if x.isdigit() else x for x in m.split('.')]))
md_01a = loi.lam_tron_tong([sum(float(by[c]['md']) / len(by[c]['hang_muc_01a']) for c in phu.get(h['stt'], [])) for h in hsmt['mau_01a']])
out = {
    'tong_md': tong, 'so_goi_la': len(la), 'goi': goi_sorted, 'nhom': nhom,
    'truy_vet_rfp': [{'ma': y['ma'], 'yeu_cau': y['dien_giai'], 'goi': ', '.join(truy_vet.get(y['ma'], [])) or ('Không cần gói: ' + khong_can.get(y['ma'], '') if y['ma'] in khong_can else '')}
                     for y in rfp['yeu_cau']],
    'phan_bo_01a': [{'stt': h['stt'], 'danh_muc': h['danh_muc'], 'goi': gon_ma(phu.get(h['stt'], [])),
                     'md': md_01a[i]} for i, h in enumerate(hsmt['mau_01a'])],
    'khong_can_goi': w.get('khong_can_goi', []), 'gia_dinh_ngoai_pham_vi': w.get('gia_dinh_ngoai_pham_vi', []),
    'md_theo_loai': {k: round(sum(float(g['md']) for g in la if g.get('loai') == k), 2) for k in sorted(LOAI)},
}
loi.ghi_json('du_lieu/wbs.json', out)
loi.hoan_tat_buoc('wbs', f'Kiểm tra và chuẩn hóa WBS: {tong:g} MD, {len(la)} gói lá', chi_tiet={'tong_md': tong, 'canh_bao': len(F) - len(loi_)})
print('Đã ghi du_lieu/wbs.json')
