"""Kiểm tra và chuẩn hóa WBS (lớp A cho dữ liệu WBS).

Dùng: python kiem_tra_wbs.py <wbs_nhap.json>
Kiểm tra: mã phân cấp, quy tắc 100% (tính khối lượng mục cha), gói lá có MD, loại công việc, sản phẩm,
thời lượng tối thiểu, phụ thuộc (tồn tại, không vòng), hạng mục Mẫu 01A (mọi hạng mục được phủ), truy vết yêu cầu RFP,
nghiệp vụ bán hàng thông dụng, cỡ gói 2 đến 14 MD (cảnh báo), văn phong tên gói, gói sửa lỗi của kiểm thử phân hệ.
Căn cứ ước lượng (dau_vao/uoc_luong.json, thiếu thì cảnh báo): mỗi nhóm mức 1 có can_cu_uoc_luong, tổng nhóm trong
dung_sai_nhom, tổng toàn bộ bằng tong_md. Đối chiếu tổng với trung bình quy_mo_md của hợp đồng tương tự (nha_thau.json).
Đạt thì ghi du_lieu/wbs.json (đã tính khối lượng mục cha, ma trận truy vết, khối can_cu_uoc_luong), đăng ký phiên bản, ghi nhật ký.
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
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
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
NV = json.load(open(os.path.join(HERE, '..', 'references', 'nghiep_vu_ban_hang.json'), encoding='utf-8'))['nghiep_vu']
UL = loi.doc_json('dau_vao/uoc_luong.json', {})  # căn cứ ước lượng của nhóm; thiếu thì chỉ cảnh báo để dữ liệu cũ vẫn chạy
NT = loi.doc_json('dau_vao/nha_thau.json', {})
DUNG_SAI_TONG_MD = 0.5  # sai lệch làm tròn cho phép giữa tổng WBS và tong_md
NGUONG_LECH_TUONG_TU = 0.25  # tổng lệch trung bình hợp đồng tương tự quá ngưỡng này thì cần giai_trinh_tuong_tu
MAU_KIEM_THU_PHAN_HE = r'kiểm thử phân hệ'
MAU_SUA_LOI = r'sửa lỗi|khắc phục lỗi|kiểm thử lại'
F = []


def add(ma, mo_ta, vi_tri='', muc_do='loi', cach_sua='can_nguoi_dung'):
    F.append({'ma': ma, 'muc_do': muc_do, 'nhom': 'wbs', 'vi_tri': vi_tri, 'mo_ta': mo_ta, 'cach_sua': cach_sua, 'de_xuat': ''})


def chuan(s):
    """Chuỗi chuẩn hóa NFC, chữ thường, để so khớp từ khóa tiếng Việt."""
    return unicodedata.normalize('NFC', str(s)).lower()


def so_nguyen_duong(v):
    """Số nguyên dương (chấp nhận 5.0), không hợp lệ thì None."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0 or float(v) != int(v):
        return None
    return int(v)


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
    if 'thoi_luong_toi_thieu' in g:
        tl = so_nguyen_duong(g['thoi_luong_toi_thieu'])
        if tl is None:
            add('W19', 'thoi_luong_toi_thieu phải là số nguyên dương (ngày làm việc)', m)
        else:
            g['thoi_luong_toi_thieu'] = tl
for g in goi:
    if g['ma'] in co_con and g.get('md') not in (None, ''):
        add('W17', 'Mục cha không ghi md (script tự tính theo quy tắc 100%)', g['ma'], 'canh_bao', 'tu_dong')
    if g['ma'] in co_con and 'thoi_luong_toi_thieu' in g:
        add('W19', 'Chỉ gói lá ghi thoi_luong_toi_thieu', g['ma'])

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

# nghiệp vụ bán hàng thông dụng: phải nằm ở gói, khong_can_goi hoặc gia_dinh_ngoai_pham_vi
van_ban = chuan(' '.join(f'{g.get("ten", "")} {g.get("san_pham", "")}' for g in goi) + ' ' + ' '.join(map(str, w.get('gia_dinh_ngoai_pham_vi', [])))
                + ' ' + ' '.join(str(x.get('ly_do', '')) for x in w.get('khong_can_goi', [])))
ma_da_xu_ly = set(khong_can) | {str(n) for g in la for n in g.get('nguon', [])}
for nv in NV:
    if nv['ma'] in ma_da_xu_ly or any(chuan(k) in van_ban for k in nv['tu_khoa']):
        continue
    add('W33', f'Nghiệp vụ {nv["ten"]} chưa nằm ở gói, khong_can_goi hoặc gia_dinh_ngoai_pham_vi', nv['ma'], 'canh_bao')

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

# kiểm thử phân hệ phải có gói sửa lỗi, kiểm thử lại
for g in by.values():
    if g['ma'].count('.') == 1 and re.search(MAU_KIEM_THU_PHAN_HE, chuan(g.get('ten', ''))):
        con_la = [x for x in la if x['ma'].startswith(g['ma'] + '.')]
        if not any(re.search(MAU_SUA_LOI, chuan(x.get('ten', ''))) for x in con_la):
            add('W65', 'Mục kiểm thử phân hệ chưa có gói sửa lỗi, kiểm thử lại (tên gói có cụm sửa lỗi hoặc khắc phục lỗi)', g['ma'], 'canh_bao')

# căn cứ ước lượng
muc1 = [by[m] for m in sorted(by, key=loi.khoa_ma) if '.' not in m]


def co_can_cu(v):
    """can_cu_uoc_luong hợp lệ: chuỗi không rỗng hoặc {kich_thuoc, cach_phan_ra} có cach_phan_ra."""
    if isinstance(v, dict):
        return bool(str(v.get('cach_phan_ra', '')).strip())
    return bool(str(v or '').strip())


def kiem_can_cu():
    if not UL:
        add('W60', 'Chưa có dau_vao/uoc_luong.json, bỏ qua kiểm tra căn cứ ước lượng. Đề nghị nhóm bổ sung căn cứ ước lượng', 'dau_vao/uoc_luong.json', 'canh_bao')
        return
    muc_tieu = UL.get('tong_theo_nhom', {})
    ds = float(UL.get('dung_sai_nhom', 0))
    for g in muc1:
        if not co_can_cu(g.get('can_cu_uoc_luong')):
            add('W61', 'Nhóm mức 1 thiếu can_cu_uoc_luong (kích thước, cách phân rã từ tổng nhóm theo phương pháp)', g['ma'])
        if g['ma'] not in muc_tieu:
            add('W63', 'Nhóm mức 1 không có trong tong_theo_nhom của uoc_luong.json', g['ma'])
            continue
        mt, md_g = float(muc_tieu[g['ma']]['md']), float(g.get('md') or 0)
        if abs(md_g - mt) > ds * mt + 1e-9:
            add('W63', f'Nhóm {md_g:g} MD lệch {(md_g - mt) / mt:+.1%} so với mục tiêu {mt:g} MD, vượt dung sai {ds:.0%}', g['ma'])
    for ma in sorted(set(muc_tieu) - {g['ma'] for g in muc1}, key=loi.khoa_ma):
        add('W63', f'Nhóm {ma} ({muc_tieu[ma].get("ten", "")}) có trong uoc_luong.json nhưng không có trong WBS', ma)
    if abs(tong - float(UL.get('tong_md', 0))) > DUNG_SAI_TONG_MD:
        add('W62', f'Tổng WBS {tong:g} MD lệch tong_md {float(UL.get("tong_md", 0)):g} MD của uoc_luong.json quá {DUNG_SAI_TONG_MD:g} MD')


def md_hop_dong(h):
    """quy_mo_md dương của một hợp đồng tương tự, không có thì None."""
    try:
        v = float(h.get('quy_mo_md'))
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def doi_chieu_tuong_tu():
    """Hợp đồng tương tự có quy_mo_md (nha_thau.json): quy mô, tỷ lệ so với tổng WBS, trung bình và mức lệch."""
    ds = [h for h in NT.get('hop_dong_tuong_tu', []) if md_hop_dong(h)]
    tb = sum(md_hop_dong(h) for h in ds) / len(ds) if ds else None
    return {'hop_dong': [{'ten': h.get('ten', ''), 'chu_dau_tu': h.get('chu_dau_tu', ''), 'ngay_hoan_thanh': h.get('ngay_hoan_thanh', ''),
                          'quy_mo_md': md_hop_dong(h), 'ty_le_so_voi_wbs': round(md_hop_dong(h) / tong, 4) if tong else None} for h in ds],
            'trung_binh_md': round(tb, 2) if tb else None, 'ty_le_lech_trung_binh': round((tong - tb) / tb, 4) if tb else None}


kiem_can_cu()
tt = doi_chieu_tuong_tu()
giai_trinh = str(w.get('giai_trinh_tuong_tu', '')).strip()
if tt['trung_binh_md'] is None:
    add('W64', 'nha_thau.json chưa có hợp đồng tương tự ghi quy_mo_md, chưa đối chiếu được tổng khối lượng', 'dau_vao/nha_thau.json', 'canh_bao')
elif abs(tt['ty_le_lech_trung_binh']) > NGUONG_LECH_TUONG_TU and not giai_trinh:
    add('W64', f'Tổng {tong:g} MD lệch {tt["ty_le_lech_trung_binh"]:+.1%} so với trung bình {tt["trung_binh_md"]:g} MD của hợp đồng tương tự, '
               f'quá {NGUONG_LECH_TUONG_TU:.0%} mà chưa có giai_trinh_tuong_tu', '', 'canh_bao')

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


def lap_can_cu():
    """Khối can_cu_uoc_luong của wbs.json: phương pháp, khoảng sai số quy ra MD, các bước, bảng theo nhóm, đối chiếu tương tự."""
    if not UL:
        return None
    ss = UL.get('khoang_sai_so', {})
    muc_tieu = UL.get('tong_theo_nhom', {})
    theo_nhom = []
    for n in nhom:
        mt = muc_tieu.get(n['ma'], {}).get('md')
        theo_nhom.append({'ma': n['ma'], 'ten': n['ten'], 'md_muc_tieu': mt, 'md_wbs': n['md'],
                          'chenh_lech': round(n['md'] - mt, 2) if mt is not None else None,
                          'ty_le_chenh': round((n['md'] - mt) / mt, 4) if mt else None, 'can_cu': by[n['ma']].get('can_cu_uoc_luong')})
    sai_so = {'duoi': ss.get('duoi'), 'tren': ss.get('tren')}
    if ss.get('duoi') is not None and ss.get('tren') is not None:
        sai_so.update(md_duoi=round(tong * (1 + float(ss['duoi'])), 2), md_tren=round(tong * (1 + float(ss['tren'])), 2))
    return {'phuong_phap': UL.get('phuong_phap', ''), 'loai_uoc_luong': UL.get('loai_uoc_luong', ''), 'nguon': UL.get('nguon', ''),
            'so_chuc_nang': UL.get('so_chuc_nang'), 'so_dau_viec_phi_chuc_nang': UL.get('so_dau_viec_phi_chuc_nang'),
            'khoang_sai_so': sai_so, 'cac_buoc': UL.get('cac_buoc', []), 'tong_md_muc_tieu': UL.get('tong_md'), 'tong_md_wbs': tong,
            'chenh_lech_tong': round(tong - float(UL.get('tong_md', 0)), 2), 'dung_sai_nhom': UL.get('dung_sai_nhom'), 'theo_nhom': theo_nhom,
            'hop_dong_tuong_tu': tt['hop_dong'], 'trung_binh_tuong_tu_md': tt['trung_binh_md'], 'ty_le_lech_trung_binh': tt['ty_le_lech_trung_binh'],
            'nguong_lech_tuong_tu': NGUONG_LECH_TUONG_TU, 'giai_trinh_tuong_tu': giai_trinh}



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
    'can_cu_uoc_luong': lap_can_cu(),
}
loi.ghi_json('du_lieu/wbs.json', out)
loi.hoan_tat_buoc('wbs', f'Kiểm tra và chuẩn hóa WBS: {tong:g} MD, {len(la)} gói lá', chi_tiet={'tong_md': tong, 'canh_bao': len(F) - len(loi_)})
print('Đã ghi du_lieu/wbs.json')
