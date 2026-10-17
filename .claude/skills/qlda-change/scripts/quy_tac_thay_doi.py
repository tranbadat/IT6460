"""Quy tắc dùng chung của qlda-change, do tinh_bang_thay_doi.py và yeu_cau_thay_doi.py import (không chạy trực tiếp).

- nap_phan_loai: nạp references/phan_loai.json, giải thời hạn theo dữ liệu dự án, kiểm tra cấu hình.
- vai_ban: người giữ từng vai của ban kiểm soát thay đổi (quản trị dự án, đại diện nhà thầu, đầu mối và người có thẩm quyền của Chủ đầu tư).
- kiem_tra_ky_phu_luc: mức đòi phụ lục hợp đồng phải có người ký được ở cả hai bên.
- cham_diem: điểm tác động 1 đến 10 và mức theo ngưỡng định lượng và điều kiện hợp đồng.
- moc_bi_anh_huong: ước tính mốc gắn đợt thanh toán bị dời khi gói tăng thời lượng.
- he_so_gia: hệ số từ chi phí nội bộ sang giá đề nghị Chủ đầu tư.
Mã kiểm tra TD01 đến TD11. Lỗi thì script gọi dừng, cảnh báo thì in.
"""
import datetime as dt
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

DUONG_DAN_PL = os.path.join(HERE, '..', 'references', 'phan_loai.json')
TEP_THEO = {'chi_tieu': 'dau_vao/chi_tieu_ky_thuat.json', 'du_an': 'dau_vao/du_an.json'}
NGUONG = (('md', 'md_toi_da', 'MD tăng {} MD', 'md'), ('chi_phi', 'chi_phi_toi_da', 'chi phí nội bộ {} đồng', 'tien'),
          ('tieu_hao_du_tru', 'tieu_hao_du_tru_toi_da', 'tiêu hao dự trữ {} ngày', 'so'),
          ('cham_cut_over', 'ngay_cham_cut_over_toi_da', 'chậm cut over {} ngày', 'so'))


def _gia_tri_theo(theo):
    """'chi_tieu#khoa' hoặc 'du_an#khoa' -> giá trị trong dau_vao, None khi chưa có."""
    bd, _, k = theo.partition('#')
    try:
        return loi.lay(loi.doc_json(TEP_THEO[bd]), k)
    except (KeyError, FileNotFoundError):
        return None


def _giai_thoi_han(m, cb):
    """Thời hạn đánh giá, quyết định của một mức: lấy theo dữ liệu dự án khi có khóa _theo, ngược lại dùng giá trị trong tệp."""
    m2 = dict(m)
    for k in ('thoi_han_danh_gia', 'thoi_han_quyet_dinh'):
        theo = m.get(k + '_theo')
        if not theo:
            continue
        v = _gia_tri_theo(theo)
        if v is None:
            cb.append(f'TD03 Mức {m["ten"]}: chưa có {theo}, tạm dùng {m[k + "_ngay"]} ngày. Đề nghị bổ sung vào dau_vao')
        else:
            m2[k + '_ngay'] = int(v)
            m2[k + '_nguon'] = theo
    return m2


def nap_phan_loai():
    """Trả (pl, loi_ds, canh_bao). pl là bản mới đã giải thời hạn, mức sắp theo điểm tăng dần."""
    goc = json.load(open(DUONG_DAN_PL, encoding='utf-8'))
    loi_ds, cb = [], []
    muc = sorted((_giai_thoi_han(m, cb) for m in goc['muc']), key=lambda m: m['diem'][0])
    td = goc['thang_diem']
    dai = [m['diem'] for m in muc]
    if len(muc) != 3 or dai[0][0] != td['tu'] or dai[-1][1] != td['den'] or any(a[1] + 1 != b[0] for a, b in zip(dai, dai[1:])):
        loi_ds.append(f'TD01 Phân loại phải có ba mức với khoảng điểm liên tục từ {td["tu"]} đến {td["den"]}, hiện có {dai}')
    if goc.get('cut_over_co_dinh'):
        for m in muc[:-1]:
            if (m.get('ngay_cham_cut_over_toi_da') or 0) > 0:
                loi_ds.append(f'TD02 Cut over là ngày cố định nhưng mức {m["ten"]} cho phép chậm cut over {m["ngay_cham_cut_over_toi_da"]} ngày, đặt bằng 0')
    cam_ket = _gia_tri_theo('chi_tieu#thoi_han_danh_gia_thay_doi_ngay')
    for m in muc:
        if cam_ket is not None and m['thoi_han_danh_gia_ngay'] > int(cam_ket):
            loi_ds.append(f'TD04 Mức {m["ten"]}: thời hạn đánh giá {m["thoi_han_danh_gia_ngay"]} ngày dài hơn cam kết {cam_ket} ngày '
                          '(dau_vao/chi_tieu_ky_thuat.json thoi_han_danh_gia_thay_doi_ngay)')
    ma_muc = {m['ma'] for m in muc}
    loi_ds += [f'TD01 Điều kiện {d["ma"]} gắn mức không có: {d["muc"]}' for d in goc['dieu_kien'] if d['muc'] not in ma_muc]
    return dict(goc, muc=muc, cam_ket_danh_gia_ngay=cam_ket), loi_ds, cb


def kiem_tra_can_cu(pl, hsmt):
    """Cảnh báo khi điều khoản E-ĐKCT dùng làm căn cứ phân loại không còn trong HSMT."""
    e = hsmt.get('e_dkct', {})
    return [f'TD09 Điều kiện {d["ma"]}: HSMT không còn điều khoản {k}, kiểm tra lại căn cứ trong phan_loai.json'
            for d in pl['dieu_kien'] for k in d.get('khoa_hsmt', []) if k not in e]


# ---------------------------------------------------------------- ban kiểm soát thay đổi
def _quan_tri_du_an(pc, tv):
    vt = next((x for x in pc.get('vi_tri_chu_chot', []) if x.get('vi_tri') == 'Quản trị dự án' and x.get('thanh_vien')), None)
    ids = vt['thanh_vien'] if vt else [x['A'] for x in pc.get('trach_nhiem', []) if x.get('muc') == 1][:1]
    i = next((x for x in ids if x in tv), None)
    if not i:
        return None
    return {'id': i, 'ho_ten': tv[i]['ho_ten'], 'ten': f'{tv[i]["ho_ten"]}, {tv[i].get("chuc_danh", "")}'.rstrip(', '), 'ben': 'Nhà thầu',
            'ky_phu_luc': False, 'nguon': 'Phân công, vị trí nhân sự chủ chốt'}


def _ben_cdt(pc, hsmt, cb):
    """Đầu mối và người có thẩm quyền của Chủ đầu tư: ưu tiên phan_cong ben_ngoai, thiếu thì lấy theo HSMT (Mục 4.1, 1.3 E-ĐKCT)."""
    bn = pc.get('ben_ngoai', [])
    cdt = hsmt['goi_thau']['chu_dau_tu']
    e = hsmt.get('e_dkct', {})
    out = {}
    ky = next((b for b in bn if b.get('ky_hop_dong')), None)
    dm = next((b for b in bn if b is not ky and (b.get('id') == 'cdt' or 'đầu mối' in (b.get('vai_tro', '') + b.get('ten', '')).lower())), None)
    if dm:
        ht = re.search(r'đầu mối\s+(.+)$', dm['ten'])
        out['dau_moi_cdt'] = {'ten': dm['ten'], 'ho_ten': ht.group(1).strip() if ht else dm['ten'], 'ben': 'Chủ đầu tư', 'ky_phu_luc': False,
                              'nguon': 'Phân công, bên ngoài'}
    else:
        m = re.search(r'người nhận\s+([^,]+),\s*([^,]+)', e.get('E-ĐKC 4.1', ''))
        if m:
            out['dau_moi_cdt'] = {'ten': f'{m.group(1).strip()}, {m.group(2).strip()}', 'ho_ten': m.group(1).strip(), 'ben': 'Chủ đầu tư',
                                  'ky_phu_luc': False, 'nguon': 'HSMT, Mục 4.1 E-ĐKCT'}
        else:
            cb.append('TD07 Chưa xác định được đầu mối Chủ đầu tư (phan_cong ben_ngoai, HSMT Mục 4.1 E-ĐKCT), cần bổ sung')
    if ky:
        out['tham_quyen_cdt'] = {'ten': ky['ten'], 'ho_ten': ky['ten'], 'ben': 'Chủ đầu tư', 'ky_phu_luc': True, 'nguon': 'Phân công, bên ngoài'}
        return out
    m = re.search(r'đại diện:\s*([^.;]+)', e.get('E-ĐKC 1.3', ''))
    if m:
        cv = m.group(1).strip()
        out['tham_quyen_cdt'] = {'ten': f'{cv} {cdt} (họ tên ghi khi hoàn thiện hợp đồng theo Mục 1.3 E-ĐKCT)', 'ho_ten': f'{cv} {cdt}',
                                 'ben': 'Chủ đầu tư', 'ky_phu_luc': True, 'nguon': 'HSMT, Mục 1.3 E-ĐKCT', 'thieu_ho_ten': True}
        cb.append(f'TD07 Chưa có họ tên người có thẩm quyền của Chủ đầu tư, đang ghi theo chức danh {cv} trong HSMT. '
                  'Cần bổ sung vào phan_cong ben_ngoai (ky_hop_dong: true) khi có')
    else:
        cb.append('TD07 Chưa xác định được người có thẩm quyền của Chủ đầu tư (phan_cong ben_ngoai ky_hop_dong, HSMT Mục 1.3 E-ĐKCT), cần bổ sung')
    return out


def vai_ban(pc, tv, nt, hsmt):
    """Trả (vai, loi_ds, canh_bao). vai: {mã vai: {ten, ho_ten, ben, ky_phu_luc, nguon}}."""
    loi_ds, cb, out = [], [], {}
    qt = _quan_tri_du_an(pc, tv)
    if qt:
        out['qtda'] = qt
    else:
        loi_ds.append('TD05 Không xác định được quản trị dự án (phan_cong vi_tri_chu_chot hoặc người A của nhóm WBS mức 1)')
    if nt.get('dai_dien'):
        out['dai_dien_nt'] = {'ten': f'{nt["dai_dien"]}, {nt.get("chuc_vu_dai_dien", "")}'.rstrip(', '), 'ho_ten': nt['dai_dien'], 'ben': 'Nhà thầu',
                              'ky_phu_luc': True, 'nguon': 'Thông tin nhà thầu'}
    else:
        loi_ds.append('TD06 dau_vao/nha_thau.json chưa có dai_dien (người đại diện ký hợp đồng của nhà thầu). Đề nghị điều phối viên bổ sung')
    out.update(_ben_cdt(pc, hsmt, cb))
    return out, loi_ds, cb


def kiem_tra_ky_phu_luc(pl, vai):
    """Mức đòi phụ lục hợp đồng phải có người ký được của cả nhà thầu và Chủ đầu tư trong số vai có thẩm quyền ở mức đó."""
    loi_ds = []
    for m in pl['muc']:
        if not m.get('phu_luc_hop_dong'):
            continue
        for ben in ('Nhà thầu', 'Chủ đầu tư'):
            if not any(v['ben'] == ben and v['ky_phu_luc'] for k, v in vai.items() if k in m['tham_quyen']):
                loi_ds.append(f'TD08 Mức {m["ten"]} đòi phụ lục hợp đồng nhưng ban kiểm soát thay đổi không có người ký được phía {ben} '
                              'có thẩm quyền ở mức này (kiểm tra nha_thau.json dai_dien, phan_cong ben_ngoai, tham_quyen trong phan_loai.json)')
    return loi_ds


# ---------------------------------------------------------------- chấm điểm tác động
def _diem_chi_so(v, t1, t2):
    """Điểm 1-10 của một chỉ số so với ngưỡng mức thấp t1 và mức trung bình t2."""
    if v is None or v <= 0:
        return 1
    if t1 is not None and t1 > 0 and v <= t1:
        return 1 + min(2, math.ceil(2 * v / t1))
    lo = t1 or 0
    if t2 is not None and v <= t2:
        return 4 + min(3, int(4 * (v - lo) / (t2 - lo))) if t2 > lo else 4
    t2 = t2 or 0
    return 8 + min(2, int((v - t2 - 1e-9) / (t2 or 1)))


def cham_diem(chi_so, dieu_kien, pl):
    """chi_so: {md, chi_phi, tieu_hao_du_tru, cham_cut_over}. dieu_kien: mã điều kiện áp dụng. Trả (điểm, mức, lý do)."""
    thap, tb = pl['muc'][0], pl['muc'][1]
    diem, ly_do = [1], []
    for k, khoa, ten, f in NGUONG:
        d = _diem_chi_so(chi_so.get(k), thap.get(khoa), tb.get(khoa))
        diem.append(d)
        if d > thap['diem'][1]:
            muc_vuot = thap if d <= tb['diem'][1] else tb
            ly_do.append(ten.format(loi.DINH_DANG[f](chi_so[k])) + f' vượt ngưỡng mức {muc_vuot["ten"].lower()}')
    dk = {d['ma']: d for d in pl['dieu_kien']}
    theo_muc = {}
    for ma in dieu_kien:
        theo_muc.setdefault(dk[ma]['muc'], []).append(dk[ma]['ten'])
        ly_do.append(dk[ma]['ten'][:1].lower() + dk[ma]['ten'][1:])
    n_lon = len(theo_muc.get(pl['muc'][-1]['ma'], []))
    if n_lon:
        diem.append(pl['muc'][-1]['diem'][0] - 1 + min(3, n_lon))
    if theo_muc.get(tb['ma']):
        diem.append(tb['diem'][0])
    d = min(max(diem), pl['thang_diem']['den'])
    muc = next(m for m in pl['muc'] if m['diem'][0] <= d <= m['diem'][1])
    return d, muc, ly_do


# ---------------------------------------------------------------- mốc gắn đợt thanh toán
def _chi_so_ngay(days, ngay):
    """Chỉ số ngày làm việc cuối cùng không muộn hơn ngày (ISO)."""
    return loi.ngay_lam_viec_giua(days, days[0], ngay) if days else 0


def _cham_den(them, dich, truoc, lg, lf_moc):
    """Số ngày gói tăng thời lượng đẩy mốc quá chỉ số lf_moc: duyệt ngược theo phụ thuộc, tính kết thúc muộn nhất của gói đứng trước."""
    lf, hang = {g: lf_moc for g in dich}, list(dich)
    while hang:
        g = hang.pop()
        ls = lf[g] - (lg[g]['chi_so_ket_thuc'] - lg[g]['chi_so_bat_dau'])
        for p in truoc.get(g, []):
            if p in lg and ls - 1 < lf.get(p, 10 ** 9):
                lf[p] = ls - 1
                hang.append(p)
    return max([n - max(0, lf[g] - lg[g]['chi_so_ket_thuc']) for g, n in them.items() if g in lf] + [0])


def moc_bi_anh_huong(them, wbs, lich, days):
    """them: {mã gói lá: số ngày làm việc tăng}. Trả [{ma, ten, dot, ngay_doi, vuot_han}] cho mốc gắn đợt thanh toán bị ảnh hưởng.
    Mốc có ngày cố định (M0, cut over) không xét ở đây, chậm cut over tính riêng."""
    lg = {g['ma']: g for g in lich['goi'] if g.get('la') and 'chi_so_ket_thuc' in g}
    truoc = {g['ma']: [p if isinstance(p, str) else p.get('ma') for p in g.get('phu_thuoc', [])] for g in wbs['goi'] if g.get('la')}
    out = []
    for m in lich['moc']:
        cc = str(m.get('can_cu', ''))
        if not m.get('dot_thanh_toan') or not re.match(r'^\d', cc):
            continue
        dich = [g for c in cc.split(',') for g in lg if g == c.strip() or g.startswith(c.strip() + '.')]
        if not dich:
            continue
        doi = _cham_den(them, dich, truoc, lg, _chi_so_ngay(days, m['ngay']))
        vuot = _cham_den(them, dich, truoc, lg, _chi_so_ngay(days, m.get('han') or m['ngay']))
        if doi or vuot:
            out.append({'ma': m['ma'], 'ten': m['ten'], 'dot': m['dot_thanh_toan'], 'ngay_doi': doi, 'vuot_han': vuot})
    return out


# ---------------------------------------------------------------- giá đề nghị, ngày
def he_so_gia(pl, cp, wbs):
    """Trả (hàm mã gói -> hệ số, mô tả căn cứ). Hệ số nhân chi phí nội bộ ra giá đề nghị Chủ đầu tư."""
    cach = pl.get('gia_de_nghi', {}).get('can_cu', 'gia_du_thau')
    if not cp.get('A') or not cp.get('gia_chao'):
        loi.thoat_loi('TD11 chi_phi.json thiếu A hoặc gia_chao, chạy lại bước chi_phi trước khi tính giá đề nghị')
    chung = cp['gia_chao'] / cp['A']
    if cach == 'gia_du_thau':
        return (lambda ma: chung), f'theo đơn giá suy từ giá dự thầu, bằng chi phí nội bộ nhân hệ số {loi.so(chung, 3)} (giá dự thầu chia khoản nhân công)'
    if cach == 'mau_11a':
        hs = {x['stt']: x['thanh_tien'] / x['chi_phi_a'] for x in cp.get('mau_11a', []) if x.get('chi_phi_a')}
        hm = {g['ma']: g.get('hang_muc_01a', []) for g in wbs['goi']}

        def f(ma):
            ds = [hs[h] for h in hm.get(ma, []) if h in hs]
            return sum(ds) / len(ds) if ds else chung
        return f, 'theo đơn giá của hạng mục Mẫu số 11A chứa gói, gói không gắn hạng mục dùng hệ số giá dự thầu chia khoản nhân công'
    loi.thoat_loi(f'TD11 phan_loai.json gia_de_nghi.can_cu phải là gia_du_thau hoặc mau_11a, hiện là {cach}')


def cong_ngay_lam_viec(ngay, n, da):
    """Ngày làm việc thứ n sau ngày (ISO), trừ thứ Bảy, Chủ nhật và ngày nghỉ của dự án."""
    nghi = {dt.date.fromisoformat(x) for x in da.get('ngay_nghi', [])}
    d, dem = dt.date.fromisoformat(ngay[:10]), 0
    while dem < n:
        d += dt.timedelta(days=1)
        if d.weekday() < 5 and d not in nghi:
            dem += 1
    return d.isoformat()
