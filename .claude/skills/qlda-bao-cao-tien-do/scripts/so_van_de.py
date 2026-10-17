"""Sổ vấn đề và hành động: kiểm tra dữ liệu, trạng thái tại ngày báo cáo, đối chiếu tín hiệu tự động với sổ.

Đầu vào: dau_vao/thuc_te/so_van_de.csv (ma, ngay_ghi_nhan, nguoi_bao, mo_ta, loai, uu_tien, ma_rui_ro, ma_cr, nguoi_phu_trach, han,
         trang_thai, ket_qua, nguoi_dong, ngay_dong), dau_vao/thuc_te/hanh_dong.csv (ma, ma_van_de, viec, nguoi, han, trang_thai,
         bang_chung, ngay_xong). Cách ghi: references/nhap_lieu.md.
Dùng bởi tinh_tien_do.py; kết quả ghi trong du_lieu/tien_do/<ky>.json (van_de, hanh_dong, van_de_tong_hop, van_de_phat_hien),
tổng kết đọc lại từ đó. Lập lại kỳ cũ: vấn đề ghi nhận sau ngày báo cáo bị bỏ qua, vấn đề hoặc hành động đóng sau ngày báo cáo
được coi là chưa đóng tại ngày đó.
Mã kiểm tra (tiếp dãy T của tinh_tien_do.py): T13 thiếu trường bắt buộc hoặc ngày sai dạng, T14 mã trùng, T15 ưu tiên hoặc trạng thái
không hợp lệ, T16 loại ngoài danh mục (cảnh báo), T17 mã rủi ro không có trong sổ rủi ro hay theo_doi_rui_ro.csv, T18 mã yêu cầu
thay đổi không có trong thay_doi.json, T19 hành động trỏ tới vấn đề không có trong sổ, T20 điều kiện đóng không đạt, T21 ngày không
nhất quán, T22 quá hạn tại ngày báo cáo (cảnh báo), T23 vấn đề chưa đóng chưa có hành động (cảnh báo), T24 người phụ trách không phải
thành viên (cảnh báo), T25 tín hiệu tự động chưa có vấn đề tương ứng trong sổ (cảnh báo).
"""
import re

import loi
from thuc_te import kiem_tra_o

UU_TIEN = ('Cao', 'Trung bình', 'Thấp')
TT_VAN_DE = ('Mở', 'Đang xử lý', 'Chuyển cấp', 'Đã đóng')
TT_HANH_DONG = ('Chưa thực hiện', 'Đang thực hiện', 'Hoàn thành', 'Hủy')
LOAI = ('Phạm vi', 'Tiến độ', 'Chi phí', 'Chất lượng', 'Nhân sự', 'Kỹ thuật', 'Chủ đầu tư', 'Hợp đồng', 'Khác')
TEP_VD, TEP_HD = 'so_van_de.csv', 'hanh_dong.csv'
BB_VD = ('ma', 'ngay_ghi_nhan', 'mo_ta', 'uu_tien', 'nguoi_phu_trach', 'trang_thai')
BB_HD = ('ma', 'ma_van_de', 'viec', 'nguoi', 'han', 'trang_thai')


def tach_ma(v):
    return [x for x in re.split(r'[,;\s]+', v or '') if x]


def _kiem_tra_cau_truc(vd, hd, add):
    for m in kiem_tra_o(vd, TEP_VD, cot_ngay=('ngay_ghi_nhan', 'han', 'ngay_dong'), bat_buoc=BB_VD) + \
            kiem_tra_o(hd, TEP_HD, cot_ngay=('han', 'ngay_xong'), bat_buoc=BB_HD):
        add('T13', m)
    for tep, ds in ((TEP_VD, vd), (TEP_HD, hd)):
        dem = {}
        for r in ds:
            dem[r.get('ma', '')] = dem.get(r.get('ma', ''), 0) + 1
        for m, n in dem.items():
            if m and n > 1:
                add('T14', f'{tep}: mã {m} xuất hiện {n} lần, mỗi mã một dòng (cập nhật dòng cũ thay vì thêm dòng mới)')
    for i, r in enumerate(vd, 2):
        for cot, hop_le in (('uu_tien', UU_TIEN), ('trang_thai', TT_VAN_DE)):
            if r.get(cot) and r[cot] not in hop_le:
                add('T15', f'{TEP_VD} dòng {i}, cột {cot}: "{r[cot]}" không thuộc {", ".join(hop_le)}')
        if r.get('loai') and r['loai'] not in LOAI:
            add('T16', f'{TEP_VD} dòng {i}, cột loai: "{r["loai"]}" ngoài danh mục {", ".join(LOAI)}', 'canh_bao')
    for i, r in enumerate(hd, 2):
        if r.get('trang_thai') and r['trang_thai'] not in TT_HANH_DONG:
            add('T15', f'{TEP_HD} dòng {i}, cột trang_thai: "{r["trang_thai"]}" không thuộc {", ".join(TT_HANH_DONG)}')


def _kiem_tra_lien_ket(vd, hd, ma_rr, ma_cr, add):
    for i, r in enumerate(vd, 2):
        for m in tach_ma(r.get('ma_rui_ro')):
            if m not in ma_rr:
                add('T17', f'{TEP_VD} dòng {i}: mã rủi ro {m} của {r["ma"]} không có trong du_lieu/rui_ro.json hay theo_doi_rui_ro.csv')
        for m in tach_ma(r.get('ma_cr')):
            if m not in ma_cr:
                add('T18', f'{TEP_VD} dòng {i}: mã yêu cầu thay đổi {m} của {r["ma"]} không có trong du_lieu/thay_doi.json')
    co = {r.get('ma') for r in vd}
    for i, h in enumerate(hd, 2):
        if h.get('ma_van_de') and h['ma_van_de'] not in co:
            add('T19', f'{TEP_HD} dòng {i}: hành động {h["ma"]} trỏ tới vấn đề {h["ma_van_de"]} không có trong {TEP_VD}')


def _kiem_tra_dong(vd, hd, theo_vd, add):
    """Điều kiện đóng: vấn đề đóng khi mọi hành động đã hoàn thành (hoặc hủy) trước ngày đóng, có người đóng, ngày đóng, kết quả."""
    for i, r in enumerate(vd, 2):
        if r.get('trang_thai') != 'Đã đóng':
            if r.get('ngay_dong'):
                add('T21', f'{TEP_VD} dòng {i}: {r["ma"]} chưa đóng nhưng đã ghi ngay_dong', 'canh_bao')
            continue
        thieu = [c for c in ('nguoi_dong', 'ngay_dong', 'ket_qua') if not r.get(c)]
        if thieu:
            add('T20', f'{TEP_VD} dòng {i}: {r["ma"]} Đã đóng nhưng thiếu {", ".join(thieu)}')
        hs = theo_vd.get(r['ma'], [])
        con = [h['ma'] for h in hs if h.get('trang_thai') not in ('Hoàn thành', 'Hủy')]
        if con:
            add('T20', f'{TEP_VD} dòng {i}: {r["ma"]} Đã đóng nhưng hành động {", ".join(con)} chưa hoàn thành')
        nd = r.get('ngay_dong', '')
        if nd and r.get('ngay_ghi_nhan') and nd < r['ngay_ghi_nhan']:
            add('T21', f'{TEP_VD} dòng {i}: {r["ma"]} có ngày đóng {loi.ngay(nd)} trước ngày ghi nhận')
        muon = [h['ma'] for h in hs if h.get('trang_thai') == 'Hoàn thành' and nd and h.get('ngay_xong', '') > nd]
        if muon:
            add('T20', f'{TEP_VD} dòng {i}: {r["ma"]} đóng ngày {loi.ngay(nd)} trước khi hoàn thành hành động {", ".join(muon)}')
    for i, h in enumerate(hd, 2):
        if h.get('trang_thai') == 'Hoàn thành' and not h.get('ngay_xong'):
            add('T20', f'{TEP_HD} dòng {i}: hành động {h["ma"]} Hoàn thành nhưng thiếu ngay_xong')


def _ten(p, ho_ten):
    return ho_ten.get(p, p)


def _dong_hd(h, ngay_bc, ho_ten):
    tt = 'Đang thực hiện' if h['trang_thai'] == 'Hoàn thành' and h.get('ngay_xong', '') > ngay_bc else h['trang_thai']
    qua = tt not in ('Hoàn thành', 'Hủy') and h['han'] < ngay_bc
    return {'ma': h['ma'], 'ma_van_de': h['ma_van_de'], 'viec': h['viec'], 'nguoi': _ten(h['nguoi'], ho_ten), 'han': h['han'],
            'trang_thai': tt, 'trang_thai_hien_thi': tt + (', quá hạn' if qua else ''), 'qua_han': qua,
            'bang_chung': h.get('bang_chung', ''), 'ngay_xong': h.get('ngay_xong', '') if tt == 'Hoàn thành' else ''}


def _dong_vd(r, hs, ngay_bc, tu_ngay, ho_ten):
    tt = 'Đang xử lý' if r['trang_thai'] == 'Đã đóng' and r.get('ngay_dong', '') > ngay_bc else r['trang_thai']
    dong = tt == 'Đã đóng'
    qua = not dong and bool(r.get('han')) and r['han'] < ngay_bc
    return {'ma': r['ma'], 'ngay_ghi_nhan': r['ngay_ghi_nhan'], 'nguoi_bao': r.get('nguoi_bao', ''), 'mo_ta': r['mo_ta'],
            'loai': r.get('loai', ''), 'uu_tien': r['uu_tien'], 'ma_rui_ro': r.get('ma_rui_ro', ''), 'ma_cr': r.get('ma_cr', ''),
            'lien_ket': ', '.join(tach_ma(r.get('ma_rui_ro')) + tach_ma(r.get('ma_cr'))), 'phu_trach': _ten(r['nguoi_phu_trach'], ho_ten),
            'han': r.get('han', ''), 'trang_thai': tt, 'trang_thai_hien_thi': tt + (', quá hạn' if qua else ''), 'qua_han': qua,
            'so_hanh_dong': len(hs), 'so_hanh_dong_xong': sum(1 for h in hs if h['trang_thai'] in ('Hoàn thành', 'Hủy')),
            'ket_qua': r.get('ket_qua', '') if dong else '', 'nguoi_dong': _ten(r.get('nguoi_dong', ''), ho_ten) if dong else '',
            'ngay_dong': r.get('ngay_dong', '') if dong else '', 'dong_trong_ky': dong and r.get('ngay_dong', '') >= tu_ngay}


def lap_so(ngay_bc, tu_ngay, tv, ma_rr, ma_cr):
    """Kiểm tra sổ và lập bảng tại ngày ngay_bc (yyyy-mm-dd); tu_ngay là ngày đầu kỳ.
    tv: {id: thành viên}; ma_rr, ma_cr: tập mã rủi ro, yêu cầu thay đổi hợp lệ. Trả về (kết quả, danh sách phát hiện)."""
    F = []
    add = lambda ma, mo, md='loi': F.append({'ma': ma, 'muc_do': md, 'mo_ta': mo})  # noqa: E731
    vd = loi.doc_csv('dau_vao/thuc_te/so_van_de.csv'); hd = loi.doc_csv('dau_vao/thuc_te/hanh_dong.csv')
    rong = {'van_de': [], 'hanh_dong': [], 'van_de_tong_hop': tong_hop([], [])}
    _kiem_tra_cau_truc(vd, hd, add)
    if any(f['muc_do'] == 'loi' for f in F):
        return rong, F
    theo_vd = {}
    for h in hd:
        theo_vd.setdefault(h['ma_van_de'], []).append(h)
    _kiem_tra_lien_ket(vd, hd, ma_rr, ma_cr, add)
    _kiem_tra_dong(vd, hd, theo_vd, add)
    ho_ten = {k: v['ho_ten'] for k, v in tv.items()}
    ten_tv = set(ho_ten.values())
    ds_vd, ds_hd = [], []
    for r in sorted(vd, key=lambda r: loi.khoa_ma(r['ma'])):
        if r['ngay_ghi_nhan'] > ngay_bc:
            continue
        if r['nguoi_phu_trach'] not in ho_ten and r['nguoi_phu_trach'] not in ten_tv:
            add('T24', f'{r["ma"]}: người phụ trách "{r["nguoi_phu_trach"]}" không phải mã hay họ tên trong thanh_vien.json, giữ nguyên', 'canh_bao')
        hs = sorted(theo_vd.get(r['ma'], []), key=lambda h: loi.khoa_ma(h['ma']))
        x = _dong_vd(r, hs, ngay_bc, tu_ngay, ho_ten)
        ds_vd.append(x); ds_hd += [_dong_hd(h, ngay_bc, ho_ten) for h in hs]
        if x['qua_han']:
            add('T22', f'Vấn đề {x["ma"]} quá hạn {loi.ngay(x["han"])}, trạng thái {x["trang_thai"]}', 'canh_bao')
        if x['trang_thai'] != 'Đã đóng' and not hs:
            add('T23', f'Vấn đề {x["ma"]} chưa đóng và chưa có hành động trong {TEP_HD}', 'canh_bao')
    for h in ds_hd:
        if h['qua_han']:
            add('T22', f'Hành động {h["ma"]} của {h["ma_van_de"]} quá hạn {loi.ngay(h["han"])}, trạng thái {h["trang_thai"]}', 'canh_bao')
    bc = [x for x in ds_vd if x['trang_thai'] != 'Đã đóng' or x['dong_trong_ky']]  # vấn đề đưa vào báo cáo kỳ
    ma_bc = {x['ma'] for x in bc}
    return {'van_de': bc, 'hanh_dong': [h for h in ds_hd if h['ma_van_de'] in ma_bc], 'van_de_tong_hop': tong_hop(ds_vd, ds_hd)}, F


def tong_hop(ds_vd, ds_hd):
    mo = [x for x in ds_vd if x['trang_thai'] != 'Đã đóng']
    return {'tong': len(ds_vd), 'so_mo': len(mo), 'so_mo_uu_tien_cao': sum(1 for x in mo if x['uu_tien'] == 'Cao'),
            'so_qua_han': sum(1 for x in mo if x['qua_han']), 'so_dong': len(ds_vd) - len(mo),
            'so_dong_trong_ky': sum(1 for x in ds_vd if x['dong_trong_ky']), 'so_hanh_dong': len(ds_hd),
            'so_hanh_dong_chua_xong': sum(1 for h in ds_hd if h['trang_thai'] not in ('Hoàn thành', 'Hủy')),
            'so_hanh_dong_qua_han': sum(1 for h in ds_hd if h['qua_han'])}


def _khop(tin_hieu, ds_vd):
    kieu, ma = tin_hieu['khop']
    if kieu == 'rui_ro':
        return [x['ma'] for x in ds_vd if ma in tach_ma(x['ma_rui_ro'])]
    if kieu == 'loai':
        return [x['ma'] for x in ds_vd if x['loai'] == ma and x['trang_thai'] != 'Đã đóng']
    mau = re.compile(r'(?<![\w.])' + re.escape(ma) + r'(?![\w]|\.\d)')
    return [x['ma'] for x in ds_vd if mau.search(x['mo_ta'])]


def doi_chieu_tin_hieu(tin_hieu, ds_vd):
    """Gắn vấn đề trong sổ tương ứng với từng tín hiệu tự động (gói chậm, chỉ số dưới ngưỡng, rủi ro đã xảy ra, mốc quá hạn).
    Khớp: rủi ro theo ma_rui_ro, chỉ số theo loại vấn đề đang mở, gói và mốc theo mã nêu trong mô tả. Trả về (bảng, phát hiện)."""
    out, chua = [], []
    for t in tin_hieu:
        ma_vd = _khop(t, ds_vd)
        out.append({'nguon': t['nguon'], 'noi_dung': t['noi_dung'], 'van_de_trong_so': ', '.join(ma_vd) or 'Chưa ghi sổ'})
        if not ma_vd:
            chua.append(t['noi_dung'].split(':')[0])
    F = [{'ma': 'T25', 'muc_do': 'canh_bao', 'mo_ta': f'{len(chua)} tín hiệu chưa có vấn đề tương ứng trong {TEP_VD}: {"; ".join(chua)}. '
          'Ghi vào sổ nếu cần theo dõi xử lý'}] if chua else []
    return out, F


def tap_ma_hop_le(rr, tdrr, so_td):
    """Tập mã rủi ro (sổ và rủi ro phát sinh trong theo_doi_rui_ro.csv) và mã yêu cầu thay đổi hợp lệ cho liên kết."""
    return {r['ma'] for r in rr.get('danh_sach', [])} | set(tdrr), {c['ma'] for c in so_td.get('yeu_cau', [])}

