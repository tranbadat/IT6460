"""Kiểm tra và tính toán sổ đăng ký rủi ro (bước rui_ro).

Dùng: python kiem_tra_rui_ro.py <rui_ro_nhap.json>
Tính: điểm = xác suất x tác động (thang 1 đến 5), mức (cao, trung bình, thấp), EMV theo MD và tiền, ma trận 5x5,
tổng dự phòng đề xuất. Kiểm tra: đủ trường, người phụ trách là thành viên, liên kết WBS và mốc hợp lệ,
rủi ro mức cao có kế hoạch ứng phó, dấu hiệu nhận biết và người phụ trách, đủ nhóm rủi ro bắt buộc,
mốc cut over có rủi ro liên kết, gói trên đường găng có rủi ro tiến độ.
Đạt thì ghi du_lieu/rui_ro.json, đăng ký phiên bản, ghi nhật ký. Mã thoát 0 đạt, 1 còn lỗi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

src = sys.argv[1]
rr = json.load(open(src, encoding='utf-8'))
tv = {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']}
wbs = loi.doc_json('du_lieu/wbs.json'); by = {g['ma']: g for g in wbs['goi']}
lich = loi.doc_json('du_lieu/lich.json')
moc = {m['ma']: m for m in lich['moc']}
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references', 'thang_do.json'), encoding='utf-8'))
F = []
add = lambda ma, mo, vt='', md='loi': F.append({'ma': ma, 'muc_do': md, 'nhom': 'rui_ro', 'vi_tri': vt, 'mo_ta': mo, 'cach_sua': 'can_nguoi_dung', 'de_xuat': ''})
BAT_BUOC = ['ma', 'ten', 'nhom', 'nguyen_nhan', 'tac_dong_mo_ta', 'xac_suat', 'tac_dong', 'xac_suat_pt', 'chien_luoc', 'bien_phap_phong_ngua',
            'ke_hoach_ung_pho', 'dau_hieu', 'nguoi_phu_trach']
ds = rr.get('rui_ro', [])
ma_seen = set()
for r in ds:
    m = r.get('ma', '?')
    if m in ma_seen:
        add('R01', 'Mã rủi ro trùng', m)
    ma_seen.add(m)
    for k in BAT_BUOC:
        if r.get(k) in (None, '', []):
            add('R02', f'Thiếu trường {k}', m)
    if r.get('nhom') not in CFG['nhom']:
        add('R03', f'Nhóm {r.get("nhom")} không thuộc {list(CFG["nhom"])}', m)
    if r.get('chien_luoc') not in CFG['chien_luoc']:
        add('R04', f'Chiến lược {r.get("chien_luoc")} không thuộc {list(CFG["chien_luoc"])}', m)
    for k in ('xac_suat', 'tac_dong'):
        if not isinstance(r.get(k), int) or not 1 <= r[k] <= 5:
            add('R05', f'{k} phải là số nguyên 1 đến 5', m)
    if not isinstance(r.get('xac_suat_pt'), (int, float)) or not 0 < r['xac_suat_pt'] < 1:
        add('R06', 'xac_suat_pt phải trong khoảng (0, 1)', m)
    if r.get('nguoi_phu_trach') not in tv:
        add('R07', f'Người phụ trách {r.get("nguoi_phu_trach")} không phải thành viên', m)
    for g in r.get('lien_ket_wbs', []):
        if g not in by:
            add('R08', f'Liên kết WBS {g} không có', m)
    for mm in r.get('lien_ket_moc', []):
        if mm not in moc:
            add('R09', f'Liên kết mốc {mm} không có', m)
    if r.get('tac_dong_md') is None and r.get('tac_dong_tien') is None:
        add('R10', 'Cần ước lượng tác động theo MD hoặc tiền để tính EMV', m)
    try:
        xs, td = int(r['xac_suat']), int(r['tac_dong'])
        r['diem'] = xs * td
        r['muc'] = next(k for k, (a, b) in CFG['muc'].items() if a <= r['diem'] <= b)
        r['muc_ten'] = CFG['ten_muc'][r['muc']]
        r['xs_khop'] = abs(r['xac_suat_pt'] - CFG['xac_suat_pt'][str(xs)]) <= CFG['dung_sai_xac_suat']
        if not r['xs_khop']:
            add('R11', f'xac_suat_pt {r["xac_suat_pt"]} không khớp mức xác suất {xs} của thang đo', m, 'canh_bao')
    except Exception:
        continue
    r['emv_md'] = round(r['xac_suat_pt'] * float(r.get('tac_dong_md') or 0), 2)
    r['emv_tien'] = round(r['xac_suat_pt'] * float(r.get('tac_dong_tien') or 0))
    r['emv_ngay'] = round(r['xac_suat_pt'] * float(r.get('tac_dong_ngay') or 0), 2)
    r.setdefault('trang_thai', 'Đang theo dõi')
    r['ho_ten_phu_trach'] = tv.get(r.get('nguoi_phu_trach'), {}).get('ho_ten', '')
    r['nhom_ten'] = CFG['nhom'].get(r.get('nhom'), '')
    _lk = ([('Gói ' + ', '.join(r['lien_ket_wbs']))] if r.get('lien_ket_wbs') else []) + ([('Mốc ' + ', '.join(r['lien_ket_moc']))] if r.get('lien_ket_moc') else [])
    r['lien_ket_hien_thi'] = '. '.join(_lk) or 'Không có'
    r['chien_luoc_ten'] = CFG['chien_luoc'].get(r.get('chien_luoc'), '')
    if r['muc'] == 'cao' and (len(str(r.get('ke_hoach_ung_pho', ''))) < 20 or not r.get('dau_hieu')):
        add('R12', 'Rủi ro mức cao cần kế hoạch ứng phó cụ thể và dấu hiệu nhận biết', m)

if len(ds) < CFG['so_luong_toi_thieu']:
    add('R20', f'Sổ rủi ro có {len(ds)} rủi ro, tối thiểu {CFG["so_luong_toi_thieu"]}')
for n in CFG['nhom_bat_buoc']:
    if not any(r.get('nhom') == n for r in ds):
        add('R21', f'Thiếu rủi ro nhóm {CFG["nhom"][n]}', n)
cut = [m for m in lich['moc'] if 'cut over' in m['ten'].lower()]
if cut and not any(cut[0]['ma'] in r.get('lien_ket_moc', []) for r in ds):
    add('R22', f'Chưa có rủi ro liên kết mốc cut over {cut[0]["ma"]}', cut[0]['ma'])
gang = set(lich.get('duong_gang', []))
if gang and not any(set(r.get('lien_ket_wbs', [])) & {g for x in gang for g in [x] + [x.rsplit('.', 1)[0]]} for r in ds if r.get('nhom') == 'tien_do'):
    add('R23', 'Chưa có rủi ro tiến độ liên kết với gói trên đường găng', '', 'canh_bao')

loi_ = [f for f in F if f['muc_do'] == 'loi']
for f in F:
    print(f"[{f['muc_do']}] {f['ma']} {f['vi_tri']}: {f['mo_ta']}")
ma_tran = [[sum(1 for r in ds if r.get('xac_suat') == xs and r.get('tac_dong') == td) for td in range(1, 6)] for xs in range(5, 0, -1)]
tom = {'so_rui_ro': len(ds), 'so_cao': sum(1 for r in ds if r.get('muc') == 'cao'), 'so_trung_binh': sum(1 for r in ds if r.get('muc') == 'trung_binh'),
       'so_thap': sum(1 for r in ds if r.get('muc') == 'thap'), 'tong_emv_md': round(sum(r.get('emv_md', 0) for r in ds), 2),
       'tong_emv_tien': round(sum(r.get('emv_tien', 0) for r in ds)), 'tong_emv_ngay': round(sum(r.get('emv_ngay', 0) for r in ds), 2)}
print(f'{tom["so_rui_ro"]} rủi ro: {tom["so_cao"]} cao, {tom["so_trung_binh"]} trung bình, {tom["so_thap"]} thấp. EMV {tom["tong_emv_md"]:g} MD, '
      f'{loi.tien(tom["tong_emv_tien"])} đồng. Kết luận: {"dat" if not loi_ else "chua_dat"} ({len(loi_)} lỗi, {len(F) - len(loi_)} cảnh báo)')
loi.ghi_json('lam_viec/rui_ro/bao_cao_kiem_tra.json', {'ket_luan': 'dat' if not loi_ else 'chua_dat', 'so_loi': len(loi_), 'so_canh_bao': len(F) - len(loi_), 'phat_hien': F})
if loi_:
    sys.exit(1)
ds.sort(key=lambda r: (-r['diem'], r['ma']))
ma_tran_rows = [{'xac_suat': str(5 - i), **{f'td{j + 1}': str(v) if v else '' for j, v in enumerate(row)}} for i, row in enumerate(ma_tran)]
out = {'thang_do': CFG, 'danh_sach': ds, 'tong_hop': tom, 'ma_tran': ma_tran_rows,
       'theo_nhom': [{'nhom': CFG['nhom'][n], 'so': sum(1 for r in ds if r['nhom'] == n), 'emv_tien': round(sum(r['emv_tien'] for r in ds if r['nhom'] == n))} for n in CFG['nhom']
                     if any(r['nhom'] == n for r in ds)],
       'nguong': rr.get('nguong', {}), 'quy_trinh_ghi_chu': rr.get('ghi_chu', '')}
loi.ghi_json('du_lieu/rui_ro.json', out)
loi.hoan_tat_buoc('rui_ro', f'Kiểm tra sổ rủi ro: {tom["so_rui_ro"]} rủi ro, EMV {loi.tien(tom["tong_emv_tien"])} đồng')
print('Đã ghi du_lieu/rui_ro.json')
