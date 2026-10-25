"""Kiểm tra và tính toán sổ đăng ký rủi ro (bước rui_ro).

Dùng: python kiem_tra_rui_ro.py <rui_ro_nhap.json>
Tính: tiền tác động (MD x đơn giá ngày của loại công việc, cộng phạt chậm E-ĐKC 15, cộng khoản tiền thêm), mức tác động suy ra
từ ngày chậm, tỷ lệ chi phí trên giá và mốc liên kết, điểm = xác suất x tác động (thang 1 đến 5), mức (cao, trung bình, thấp),
hạng A, B, C của ma trận 3x3, EMV theo MD, tiền, ngày kèm khoảng theo cận của mức xác suất, EMV thời gian của rủi ro trên đường găng
hoặc gắn cut over, ma trận 5x5 và 3x3 ghi mã rủi ro. Kiểm tra: đủ trường, người phụ trách là thành viên, liên kết WBS và mốc hợp lệ,
mức tác động khớp mức suy ra hoặc có lý do, tiền khai khớp tiền tự tính, có căn cứ xác suất, rủi ro mức cao có kế hoạch ứng phó và
dấu hiệu, đủ nhóm bắt buộc, mốc cut over có rủi ro liên kết, gói trên đường găng có rủi ro tiến độ, có cơ hội.
Trạng thái theo dõi: dau_vao/thuc_te/theo_doi_rui_ro.csv (đến ngày hiện hành, QLDA_NGAY khi mô phỏng) khi có, thiếu thì trang_thai của dữ liệu
nhập, mặc định Đang theo dõi. Rủi ro đã xảy ra hoặc đã đóng ghi ngày xảy ra, ngày đóng, tác động thực tế (MD, tiền trong CSV) và không tính
EMV còn lại (emv_*_con_lai bằng 0). tong_hop giữ tổng EMV của toàn sổ (tong_emv_*, dùng đánh giá cuối dự án) và thêm tổng EMV còn lại
(tong_emv_*_con_lai, dùng cho dự phòng của cost estimate, đánh giá dự trữ của kế hoạch rủi ro), số rủi ro theo trạng thái, tổng tác động thực tế.
Rủi ro trong CSV không có trong sổ báo R27 (cảnh báo), trạng thái ngoài danh mục báo R28.
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
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loi  # noqa: E402
import rui_ro_chung as rc  # noqa: E402

src = sys.argv[1]
rr = json.load(open(src, encoding='utf-8'))
tv = {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']}
wbs = loi.doc_json('du_lieu/wbs.json'); by = {g['ma']: g for g in wbs['goi']}
lich = loi.doc_json('du_lieu/lich.json')
moc = {m['ma']: m for m in lich['moc']}
CFG = rc.doc_thang_do()
BC = rc.lap_boi_canh(lich, loi.doc_json('du_lieu/hsmt.json'), loi.doc_json('dau_vao/don_gia.json'), loi.doc_json('du_lieu/phan_cong.json'), tv,
                     loi.du_an(), CFG.get('phat_cham_quy_doi_ngay_lich', True))
F = []
add = lambda ma, mo, vt='', md='loi': F.append({'ma': ma, 'muc_do': md, 'nhom': 'rui_ro', 'vi_tri': vt, 'mo_ta': mo, 'cach_sua': 'can_nguoi_dung', 'de_xuat': ''})
BAT_BUOC = ['ma', 'ten', 'nhom', 'nguyen_nhan', 'tac_dong_mo_ta', 'xac_suat', 'tac_dong', 'xac_suat_pt', 'can_cu_xac_suat', 'chien_luoc',
            'bien_phap_phong_ngua', 'ke_hoach_ung_pho', 'dau_hieu', 'nguoi_phu_trach']
TT = []  # bảng tính tiền và mức suy ra của từng rủi ro, ghi vào báo cáo kiểm tra
NGAY_TT = loi.ngay_hien_hanh()  # trạng thái theo dõi tính đến ngày hiện hành
if loi.du_an().get('ngay_bat_dau') and str(NGAY_TT) < loi.du_an()['ngay_bat_dau']:
    NGAY_TT = loi.du_an()['ngay_bat_dau']  # lập kế hoạch trước khi dự án bắt đầu: trạng thái tính tại ngày bắt đầu, trùng ngày tài liệu kế hoạch
TDRR, SU_KIEN_RR = loi.theo_doi_rui_ro(NGAY_TT)
DONG = ('Đã xảy ra', 'Đã đóng')  # trạng thái không còn tính EMV còn lại


def trang_thai_theo_doi(r):
    """Trạng thái, ngày xảy ra, ngày đóng, tác động thực tế của một rủi ro theo theo_doi_rui_ro.csv (đến NGAY_TT)."""
    m = r.get('ma')
    ev = [x for x in SU_KIEN_RR if x.get('ma_rui_ro') == m]
    so = lambda v: float(v) if str(v or '').strip() else 0.0  # noqa: E731
    xr = [x for x in ev if x.get('trang_thai') == 'Đã xảy ra']
    tt = TDRR[m]['trang_thai'] if m in TDRR else (r.get('trang_thai') or 'Đang theo dõi')
    return {'trang_thai': tt, 'nguon_trang_thai': f'theo dõi rủi ro đến {loi.ngay(NGAY_TT)}' if m in TDRR else 'sổ rủi ro',
            'ngay_xay_ra': xr[0]['ngay'] if xr else '', 'ngay_dong': next((x['ngay'] for x in reversed(ev) if x.get('trang_thai') == 'Đã đóng'), ''),
            'tac_dong_thuc_te_md': round(sum(so(x.get('md_tac_dong')) for x in ev), 2),
            'tac_dong_thuc_te_tien': round(sum(so(x.get('chi_phi_tac_dong')) for x in ev)),
            'hanh_dong_gan_nhat': ev[-1].get('hanh_dong', '') if ev else ''}


def kiem_truong(r, m):
    """Các kiểm tra trường, mã, liên kết (R02 đến R10, R16)."""
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
    if r.get('tac_dong_md') is None and r.get('tac_dong_tien') is None and not r.get('tien_them'):
        add('R10', 'Cần ước lượng tác động theo MD hoặc tiền để tính EMV', m)
    if r.get('loai', 'de_doa') not in CFG['loai']:
        add('R16', f'loai {r.get("loai")} không thuộc {list(CFG["loai"])}', m)


def kiem_tien(r, m):
    """Tiền tác động: tự tính (R14, R17), đối chiếu số agent khai (R15). Trả về (tiền dùng tính EMV, kết quả tự tính)."""
    khai = r.get('tac_dong_tien')
    thieu_loai = bool(float(r.get('tac_dong_md') or 0)) and not r.get('loai_cong_viec')
    tinh = rc.tinh_tien(dict(r, tac_dong_md=0) if thieu_loai else r, BC)
    if r.get('tien_them') and not str(r.get('ly_do_tien_them', '')).strip():
        add('R17', 'tien_them cần ly_do_tien_them (căn cứ của khoản tiền thêm)', m)
    if thieu_loai:
        if khai is None:
            add('R14', 'Thiếu loai_cong_viec để tính tiền tác động từ MD', m)
        else:
            add('R14', 'Chưa khai loai_cong_viec, dùng tac_dong_tien do agent khai, không đối chiếu được với tiền tự tính', m, 'canh_bao')
        tinh = dict(tinh, tien=None)
    elif tinh['loi']:
        add('R17' if 'tien_them' in tinh['loi'] else 'R14', tinh['loi'], m)
    if khai is not None and tinh['tien'] is not None and abs(float(khai) - tinh['tien']) > CFG['dung_sai_tien'] * max(tinh['tien'], 1):
        add('R15', f'tac_dong_tien khai {loi.tien(khai)} đồng lệch tiền tự tính {loi.tien(tinh["tien"])} đồng '
                   f'(nhân công {loi.tien(tinh["tien_nhan_cong"])}, phạt {loi.tien(tinh["tien_phat"])} cho {loi.so(tinh["ngay_phat_lich"], 1)} ngày lịch, tiền thêm {loi.tien(tinh["tien_them"])}), '
                   'bỏ trường tac_dong_tien để dùng số tự tính hoặc ghi lý do trong tac_dong_mo_ta', m, 'canh_bao')
    dung = float(khai) if khai is not None else float(tinh['tien'] or 0)
    return dung, tinh


def kiem_muc_tac_dong(r, m, tien, tinh):
    """Mức tác động agent chấm so với mức suy ra (R13)."""
    muc, can_cu = rc.suy_muc_tac_dong(r, BC, tien, CFG, bool(tinh.get('phat_toi_da')))
    if r['tac_dong'] != muc:
        ly_do = str(r.get('ly_do_muc_tac_dong', '')).strip()
        if not ly_do:
            add('R13', f'Mức tác động {r["tac_dong"]} khác mức suy ra {muc} ({", ".join(can_cu)}). Chấm theo mức suy ra '
                       'hoặc ghi ly_do_muc_tac_dong', m)
        else:
            add('R13', f'Mức tác động {r["tac_dong"]} khác mức suy ra {muc}, lý do: {ly_do}', m, 'canh_bao')
    return muc, can_cu


def kiem_trinh_bay(r, m):
    """Chiến lược theo loại (R18), nguyên nhân không viện dẫn số tổng hợp của sổ (R19), rủi ro còn lại và điều kiện đóng (R26)."""
    loai_ = r.get('loai', 'de_doa')
    if loai_ in CFG['loai'] and r.get('chien_luoc') in CFG['chien_luoc'] and r.get('chien_luoc') not in CFG['chien_luoc_theo_loai'].get(loai_, []):
        add('R18', f'Chiến lược {CFG["chien_luoc"][r["chien_luoc"]]} không dùng cho {CFG["loai"].get(r.get("loai", "de_doa"), "")}', m, 'canh_bao')
    nn = str(r.get('nguyen_nhan', '')).lower()
    tu = [t for t in CFG['tu_tong_hop_cam'] if t in nn]
    if tu:
        add('R19', f'Nguyên nhân viện dẫn số tổng hợp của chính sổ ({", ".join(tu)}), nêu nguyên nhân gốc của sự kiện', m, 'canh_bao')
    thieu = [k for k in ('dieu_kien_dong', 'xac_suat_con_lai', 'tac_dong_con_lai') if r.get(k) in (None, '')]
    sai = [k for k in ('xac_suat_con_lai', 'tac_dong_con_lai') if r.get(k) not in (None, '') and (not isinstance(r[k], int) or not 1 <= r[k] <= 5)]
    if thieu or sai:
        add('R26', ('Thiếu ' + ', '.join(thieu) if thieu else '') + ('; ' if thieu and sai else '') + (', '.join(sai) + ' phải là số nguyên 1 đến 5' if sai else ''), m,
            'canh_bao')


def muc_cua_diem(d):
    return next(k for k, (a, b) in CFG['muc'].items() if a <= d <= b)


def tinh_rui_ro(r, tien, tinh, muc_sr, can_cu):
    """Bản ghi mới của rủi ro cho du_lieu/rui_ro.json: điểm, mức, hạng, EMV kèm khoảng, rủi ro còn lại, hiển thị."""
    xs, td, p = int(r['xac_suat']), int(r['tac_dong']), float(r['xac_suat_pt'])
    lo, hi = CFG['xac_suat_khoang'][str(xs)]
    md, ngay = float(r.get('tac_dong_md') or 0), float(r.get('tac_dong_ngay') or 0)
    diem = xs * td
    x = dict(r, diem=diem, muc=muc_cua_diem(diem), loai=r.get('loai', 'de_doa'), tac_dong_tien=round(tien), tac_dong_tien_tu_tinh=tinh['tien'],
             tien_nhan_cong=tinh['tien_nhan_cong'], tien_phat=tinh['tien_phat'], ngay_phat=tinh['ngay_phat'],
             ngay_phat_lich=tinh['ngay_phat_lich'], tien_them_tinh=tinh['tien_them'],
             muc_tac_dong_suy_ra=muc_sr, can_cu_muc_tac_dong=f'Suy ra mức {muc_sr} theo {", ".join(can_cu)}'
             + (f'. Chấm mức {td}, lý do: {str(r.get("ly_do_muc_tac_dong", "")).strip()}' if td != muc_sr else ''),
             emv_md=round(p * md, 2), emv_tien=round(p * tien), emv_ngay=round(p * ngay, 2), emv_trieu=round(p * tien / 1e6, 1),
             emv_tien_thap=round(lo * tien), emv_tien_cao=round(hi * tien), emv_md_thap=round(lo * md, 2), emv_md_cao=round(hi * md, 2),
             emv_ngay_thap=round(lo * ngay, 2), emv_ngay_cao=round(hi * ngay, 2), tren_gang=rc.tren_gang_hoac_cut_over(r, BC),
             hang=rc.hang_3x3(xs, td, CFG))
    x['muc_ten'] = CFG['ten_muc'][x['muc']]
    x['xs_khop'] = abs(p - CFG['xac_suat_pt'][str(xs)]) <= CFG['dung_sai_xac_suat']
    x.update(trang_thai_theo_doi(r))
    con = x['trang_thai'] not in DONG  # rủi ro đã xảy ra hoặc đã đóng: tác động đã vào số liệu thực tế, không cần dự phòng nữa
    x.update({k + '_con_lai': (x[k] if con else 0) for k in ('emv_md', 'emv_tien', 'emv_ngay', 'emv_tien_thap', 'emv_tien_cao', 'emv_md_thap',
                                                            'emv_md_cao', 'emv_ngay_thap', 'emv_ngay_cao')})
    x['trang_thai_hien_thi'] = x['trang_thai'] + (f' ngày {loi.ngay(x["ngay_xay_ra"])}' if x['trang_thai'] == 'Đã xảy ra' and x['ngay_xay_ra'] else '') \
        + (f' ngày {loi.ngay(x["ngay_dong"])}' if x['trang_thai'] == 'Đã đóng' and x['ngay_dong'] else '')
    x['tac_dong_thuc_te_hien_thi'] = (f'{loi.md(x["tac_dong_thuc_te_md"])} MD, {loi.tien(x["tac_dong_thuc_te_tien"])} đồng'
                                      if x['ngay_xay_ra'] else '')
    x['ho_ten_phu_trach'] = tv.get(r.get('nguoi_phu_trach'), {}).get('ho_ten', '')
    x['nhom_ten'] = CFG['nhom'].get(r.get('nhom'), '')
    x['loai_ten'] = CFG['loai'].get(x['loai'], '')
    x['chien_luoc_ten'] = CFG['chien_luoc'].get(r.get('chien_luoc'), '')
    x['lien_ket_hien_thi'] = rc.lien_ket_hien_thi(r, BC)
    xs2, td2 = r.get('xac_suat_con_lai'), r.get('tac_dong_con_lai')
    if isinstance(xs2, int) and isinstance(td2, int) and 1 <= xs2 <= 5 and 1 <= td2 <= 5:
        d2 = xs2 * td2
        x.update(diem_con_lai=d2, muc_con_lai_ten=CFG['ten_muc'][muc_cua_diem(d2)],
                 con_lai_hien_thi=f'{xs2} x {td2} = {d2}, {CFG["ten_muc"][muc_cua_diem(d2)].lower()}, hạng {rc.hang_3x3(xs2, td2, CFG)}')
    else:
        x['con_lai_hien_thi'] = ''
    return x


def xu_ly(r):
    m = r.get('ma', '?')
    kiem_truong(r, m)
    kiem_trinh_bay(r, m)
    try:
        xs, td, p = int(r['xac_suat']), int(r['tac_dong']), float(r['xac_suat_pt'])
    except Exception:
        return None
    if not (1 <= xs <= 5 and 1 <= td <= 5):  # đã báo R05
        return None
    if abs(p - CFG['xac_suat_pt'][str(xs)]) > CFG['dung_sai_xac_suat']:
        add('R11', f'xac_suat_pt {r["xac_suat_pt"]} không khớp mức xác suất {xs} của thang đo', m, 'canh_bao')
    tien, tinh = kiem_tien(r, m)
    muc_sr, can_cu = kiem_muc_tac_dong(r, m, tien, tinh)
    x = tinh_rui_ro(r, tien, tinh, muc_sr, can_cu)
    TT.append({'ma': m, 'tac_dong': r['tac_dong'], 'muc_suy_ra': muc_sr, 'can_cu': can_cu, 'tien_dung': x['tac_dong_tien'],
               'tien_tu_tinh': tinh['tien'], 'nhan_cong': tinh['tien_nhan_cong'], 'phat': tinh['tien_phat'], 'ngay_phat': tinh['ngay_phat'],
               'ngay_phat_lich': tinh['ngay_phat_lich'],
               'tien_them': tinh['tien_them']})
    if x['muc'] == 'cao' and (len(str(r.get('ke_hoach_ung_pho', ''))) < 20 or not r.get('dau_hieu')):
        add('R12', 'Rủi ro mức cao cần kế hoạch ứng phó cụ thể và dấu hiệu nhận biết', m)
    return x


ds_nhap = rr.get('rui_ro', [])
for m_ in sorted(set(TDRR) - {r.get('ma') for r in ds_nhap}):
    add('R27', f'theo_doi_rui_ro.csv có rủi ro {m_} chưa có trong sổ, bổ sung vào dữ liệu nhập nếu là rủi ro cần theo dõi', m_, 'canh_bao')
for m_, x_ in TDRR.items():
    if x_.get('trang_thai') not in loi.TRANG_THAI_RUI_RO:
        add('R28', f'trạng thái "{x_.get("trang_thai")}" trong theo_doi_rui_ro.csv không thuộc {", ".join(loi.TRANG_THAI_RUI_RO)}', m_)
ma_seen = set()
for r in ds_nhap:
    if r.get('ma', '?') in ma_seen:
        add('R01', 'Mã rủi ro trùng', r.get('ma', '?'))
    ma_seen.add(r.get('ma', '?'))
ds = [x for x in (xu_ly(r) for r in ds_nhap) if x]
de_doa = [r for r in ds if r['loai'] != 'co_hoi']
co_hoi = [r for r in ds if r['loai'] == 'co_hoi']

if len(ds_nhap) < CFG['so_luong_toi_thieu']:
    add('R20', f'Sổ rủi ro có {len(ds_nhap)} rủi ro, tối thiểu {CFG["so_luong_toi_thieu"]}')
for n in CFG['nhom_bat_buoc']:
    if not any(r.get('nhom') == n for r in ds_nhap):
        add('R21', f'Thiếu rủi ro nhóm {CFG["nhom"][n]}', n)
if BC['cut'] and not any(BC['cut'] in r.get('lien_ket_moc', []) for r in ds_nhap):
    add('R22', f'Chưa có rủi ro liên kết mốc cut over {BC["cut"]}', BC['cut'])
gang = set(lich.get('duong_gang', []))
if gang and not any(set(r.get('lien_ket_wbs', [])) & {g for x in gang for g in [x] + [x.rsplit('.', 1)[0]]} for r in ds_nhap if r.get('nhom') == 'tien_do'):
    add('R23', 'Chưa có rủi ro tiến độ liên kết với gói trên đường găng', '', 'canh_bao')
pb_xs = Counter(r.get('xac_suat') for r in ds_nhap)
if ds_nhap and pb_xs.most_common(1)[0][1] / len(ds_nhap) > CFG['ty_le_dong_muc_xac_suat_toi_da']:
    xs_, n_ = pb_xs.most_common(1)[0]
    add('R24', f'{n_}/{len(ds_nhap)} rủi ro cùng mức xác suất {xs_}, xem lại căn cứ xác suất từng rủi ro', '', 'canh_bao')
if len(co_hoi) < CFG.get('so_co_hoi_toi_thieu', 0):
    add('R25', f'Sổ có {len(co_hoi)} cơ hội, khuyến khích tối thiểu {CFG["so_co_hoi_toi_thieu"]} (rủi ro có tác động tích cực)', '', 'canh_bao')

loi_ = [f for f in F if f['muc_do'] == 'loi']
for f in F:
    print(f"[{f['muc_do']}] {f['ma']} {f['vi_tri']}: {f['mo_ta']}")
tong = lambda k, ds_=de_doa: sum(r[k] for r in ds_)
gang_ds = [r for r in de_doa if r['tren_gang'] and r['emv_ngay'] > 0]
tom = {'so_rui_ro': len(ds), 'so_de_doa': len(de_doa), 'so_co_hoi': len(co_hoi), 'so_cao': sum(1 for r in ds if r['muc'] == 'cao'),
       'so_trung_binh': sum(1 for r in ds if r['muc'] == 'trung_binh'), 'so_thap': sum(1 for r in ds if r['muc'] == 'thap'),
       'so_hang': {h: sum(1 for r in ds if r['hang'] == h) for h in 'ABC'},
       'tong_emv_md': round(tong('emv_md'), 2), 'tong_emv_tien': round(tong('emv_tien')), 'tong_emv_ngay': round(tong('emv_ngay'), 2),
       'tong_emv_md_thap': round(tong('emv_md_thap'), 2), 'tong_emv_md_cao': round(tong('emv_md_cao'), 2),
       'tong_emv_tien_thap': round(tong('emv_tien_thap')), 'tong_emv_tien_cao': round(tong('emv_tien_cao')),
       'tong_emv_trieu': round(tong('emv_tien') / 1e6), 'tong_emv_trieu_thap': round(tong('emv_tien_thap') / 1e6),
       'tong_emv_trieu_cao': round(tong('emv_tien_cao') / 1e6),  # tài liệu khác dẫn EMV theo triệu đồng kèm khoảng
       'tong_emv_ngay_thap': round(tong('emv_ngay_thap'), 2), 'tong_emv_ngay_cao': round(tong('emv_ngay_cao'), 2),
       'tong_emv_ngay_gang': round(tong('emv_ngay', gang_ds), 2), 'tong_emv_ngay_gang_thap': round(tong('emv_ngay_thap', gang_ds), 2),
       'tong_emv_ngay_gang_cao': round(tong('emv_ngay_cao', gang_ds), 2), 'ma_gang': [r['ma'] for r in gang_ds],
       'tong_emv_tien_co_hoi': round(tong('emv_tien', co_hoi)), 'tong_emv_md_co_hoi': round(tong('emv_md', co_hoi), 2),
       'gia_co_so': BC['gia'], 'nguon_gia_co_so': BC['nguon_gia'], 'co_so_phat': round(BC['co_so_phat']),
       'ngay_trang_thai': NGAY_TT, 'so_theo_trang_thai': {t: sum(1 for r in ds if r['trang_thai'] == t) for t in loi.TRANG_THAI_RUI_RO},
       'so_da_xay_ra': sum(1 for r in ds if r['trang_thai'] == 'Đã xảy ra'), 'so_da_dong': sum(1 for r in ds if r['trang_thai'] == 'Đã đóng'),
       'so_con_mo': sum(1 for r in ds if r['trang_thai'] not in DONG),
       'tac_dong_thuc_te_md': round(sum(r['tac_dong_thuc_te_md'] for r in ds), 2), 'tac_dong_thuc_te_tien': round(sum(r['tac_dong_thuc_te_tien'] for r in ds)),
       'tong_emv_md_con_lai': round(tong('emv_md_con_lai'), 2), 'tong_emv_tien_con_lai': round(tong('emv_tien_con_lai')),
       'tong_emv_ngay_con_lai': round(tong('emv_ngay_con_lai'), 2),
       'tong_emv_tien_thap_con_lai': round(tong('emv_tien_thap_con_lai')), 'tong_emv_tien_cao_con_lai': round(tong('emv_tien_cao_con_lai')),
       'tong_emv_md_thap_con_lai': round(tong('emv_md_thap_con_lai'), 2), 'tong_emv_md_cao_con_lai': round(tong('emv_md_cao_con_lai'), 2),
       'tong_emv_trieu_con_lai': round(tong('emv_tien_con_lai') / 1e6), 'tong_emv_trieu_thap_con_lai': round(tong('emv_tien_thap_con_lai') / 1e6),
       'tong_emv_trieu_cao_con_lai': round(tong('emv_tien_cao_con_lai') / 1e6),
       'tong_emv_ngay_gang_con_lai': round(tong('emv_ngay_con_lai', gang_ds), 2), 'tong_emv_ngay_gang_thap_con_lai': round(tong('emv_ngay_thap_con_lai', gang_ds), 2),
       'tong_emv_ngay_gang_cao_con_lai': round(tong('emv_ngay_cao_con_lai', gang_ds), 2),
       'ma_da_xay_ra': [r['ma'] for r in ds if r['ngay_xay_ra']],
       'phan_bo_xac_suat': {str(k): pb_xs.get(k, 0) for k in range(1, 6)}}
print(f'{tom["so_rui_ro"]} rủi ro ({tom["so_co_hoi"]} cơ hội): {tom["so_cao"]} cao, {tom["so_trung_binh"]} trung bình, {tom["so_thap"]} thấp; '
      f'hạng A {tom["so_hang"]["A"]}, B {tom["so_hang"]["B"]}, C {tom["so_hang"]["C"]}. EMV {tom["tong_emv_md"]:g} MD, '
      f'{loi.trieu(tom["tong_emv_tien"], 0)} triệu đồng (khoảng {loi.trieu(tom["tong_emv_tien_thap"], 0)} đến {loi.trieu(tom["tong_emv_tien_cao"], 0)}), '
      f'EMV thời gian trên đường găng hoặc cut over {loi.so(tom["tong_emv_ngay_gang"], 1)} ngày, dự trữ {loi.so(BC["du_tru"], 0)} ngày. '
      f'Trạng thái đến {loi.ngay(NGAY_TT)}: {tom["so_da_xay_ra"]} đã xảy ra, {tom["so_da_dong"]} đã đóng, EMV còn lại '
      f'{loi.trieu(tom["tong_emv_tien_con_lai"], 0)} triệu đồng. '
      f'Kết luận: {"dat" if not loi_ else "chua_dat"} ({len(loi_)} lỗi, {len(F) - len(loi_)} cảnh báo)')
loi.ghi_json('lam_viec/rui_ro/bao_cao_kiem_tra.json', {'ket_luan': 'dat' if not loi_ else 'chua_dat', 'so_loi': len(loi_), 'so_canh_bao': len(F) - len(loi_),
                                                     'phat_hien': F, 'tinh_toan': TT})
if loi_:
    sys.exit(1)
ds.sort(key=lambda r: (-r['diem'], r['ma']))
o = lambda xs, td: [r['ma'] for r in de_doa if r['xac_suat'] == xs and r['tac_dong'] == td]
ma_tran_rows = [{'xac_suat': str(xs), **{f'td{td}': str(len(o(xs, td))) if o(xs, td) else '' for td in range(1, 6)}} for xs in range(5, 0, -1)]
ma_tran_ma = [{'xac_suat': str(xs), **{f'td{td}': ', '.join(o(xs, td)) for td in range(1, 6)}} for xs in range(5, 0, -1)]
q = CFG['quy_doi_3x3']
o3 = lambda a, b: [r['ma'] for r in de_doa if q['muc'][str(r['xac_suat'])] == a and q['muc'][str(r['tac_dong'])] == b]
ma_tran_3x3 = [{'xac_suat': a, **{b: {'hang': q['hang'][a][b], 'ma': o3(a, b)} for b in ('cao', 'trung_binh', 'thap')}} for a in ('cao', 'trung_binh', 'thap')]
out = {'thang_do': CFG, 'danh_sach': ds, 'tong_hop': tom, 'ma_tran': ma_tran_rows, 'ma_tran_ma': ma_tran_ma, 'ma_tran_3x3': ma_tran_3x3,
       'theo_nhom': [{'nhom': CFG['nhom'][n], 'so': sum(1 for r in ds if r['nhom'] == n), 'emv_tien': round(sum(r['emv_tien'] for r in de_doa if r['nhom'] == n))}
                     for n in CFG['nhom'] if any(r['nhom'] == n for r in ds)],
       'nguong': rr.get('nguong', {}), 'quy_trinh_ghi_chu': rr.get('ghi_chu', ''),
       # họ tên người phụ trách theo thứ tự thành viên, để tài liệu dẫn danh sách từ sổ thay cho viết tay (từ 1.2.3)
       'nguoi_phu_trach': [t['ho_ten'] for k, t in tv.items() if any(r.get('nguoi_phu_trach') == k for r in ds)]}
loi.ghi_json('du_lieu/rui_ro.json', out)
loi.hoan_tat_buoc('rui_ro', f'Kiểm tra sổ rủi ro: {tom["so_rui_ro"]} rủi ro, EMV {loi.trieu(tom["tong_emv_tien"], 0)} triệu đồng')
print('Đã ghi du_lieu/rui_ro.json')
