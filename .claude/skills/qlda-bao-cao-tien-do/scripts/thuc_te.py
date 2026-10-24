"""Thư viện dùng chung về chi phí lương và dữ liệu thực tế: cách trả lương, MD công việc và ngày huy động theo người,
chi phí lương, chi phí khác thực tế, kiểm tra ô CSV.

Dùng bởi qlda-cost-estimate/scripts/tinh_chi_phi.py, tinh_tien_do.py, qlda-tong-ket/scripts/tong_hop_ket_thuc.py,
qlda-bang-luong/scripts/chia_luong.py, để bốn bước tính chi phí lương cùng một cơ sở.
- Cách trả lương (dau_vao/don_gia.json cach_tra_luong, nhóm quyết định): cong_suc trả theo MD công việc (kế hoạch là MD giao theo
  lich.json phan_bo, thực tế là MD nhật ký), ngày sẵn sàng không tính lương; huy_dong và ket_hop trả theo ngày huy động.
  Phần chia theo đóng góp của ket_hop lấy từ khoản C, không tính vào chi phí lương kế hoạch.
- Nguồn huy động cùng nguồn với cost estimate: du_lieu/lich.json phan_bo[].quy là MD huy động của từng người trong từng sprint
  (lap_lich.py tính bằng loi.quy_thoi_gian theo ty_le, tu_sprint, den_sprint; tinh_chi_phi.py dùng phan_cong.json tai[].quy là tổng
  của cùng số liệu). Lịch không có quy thì tính lại bằng loi.quy_thoi_gian.
- Cắt theo ngày: sprint kết thúc trước ngày cắt tính đủ, sprint đang chạy tính theo tỷ lệ ngày làm việc đã qua trên số ngày của sprint.
- Chi phí lương theo huy động = MD huy động x lương tham chiếu tháng / ngày làm việc mỗi tháng x hệ số bảo hiểm (như tinh_chi_phi.py).
- chi_phi_thuc_te.csv có cột loai không bắt buộc: da_chi (mặc định khi trống) hoặc cam_ket (nghĩa vụ đã cam kết chưa chi, ví dụ bảo hành).
"""
import datetime as dt
import re

import loi

D = dt.date.fromisoformat
KY_KET_THUC = 'KT'  # mã kỳ giai đoạn Kết thúc sau cut over, cùng mã với lich.json phan_bo (lap_lich.py MA_KET_THUC)
TEP_MO_PHONG = 'du_lieu/mo_phong.json'  # số liệu thực tế do qlda-mo-phong sinh
LOAI_CHI_PHI = ('da_chi', 'cam_ket')
CACH_TRA_LUONG = {'huy_dong': 'trả theo ngày huy động', 'cong_suc': 'trả theo công sức (MD công việc)',
                  'ket_hop': 'trả theo ngày huy động, cộng phần chia theo tỷ trọng đóng góp'}
CO_SO_LUONG = {'cong_suc': 'MD công việc (kế hoạch là MD giao, thực tế là MD nhật ký)', 'huy_dong': 'ngày huy động, gồm cả ngày sẵn sàng không ghi công',
               'ket_hop': 'ngày huy động, gồm cả ngày sẵn sàng không ghi công'}


def cach_tra_luong(dg):
    """Cách trả lương hợp lệ trong don_gia.json, None khi thiếu hoặc sai."""
    c = dg.get('cach_tra_luong')
    return c if c in CACH_TRA_LUONG else None


def thong_bao_thieu_cach(ma=''):
    return (f'{ma + ": " if ma else ""}dau_vao/don_gia.json chưa khai báo cach_tra_luong hoặc giá trị không hợp lệ. Nhóm chọn một trong: '
            + '; '.join(f'{k} ({v})' for k, v in CACH_TRA_LUONG.items()) + '. Đây là quyết định của nhóm, điều phối viên bổ sung rồi chạy lại.')


def theo_huy_dong(cach):
    return cach in ('huy_dong', 'ket_hop')
MAU_SO = re.compile(r'^-?\d+(\.\d+)?$')


def la_ngay(v):
    try:
        D(str(v))
        return True
    except ValueError:
        return False


def kiem_tra_o(rows, tep, cot_ngay=(), cot_so=(), bat_buoc=()):
    """Kiểm tra định dạng ô của một tệp CSV đã đọc bằng loi.doc_csv. Trả về danh sách thông báo 'tệp dòng i, cột c: ...'."""
    sai = []
    for i, r in enumerate(rows, 2):
        sai += [f'{tep} dòng {i}, cột {c}: bỏ trống' for c in bat_buoc if not r.get(c)]
        sai += [f'{tep} dòng {i}, cột {c}: "{r[c]}" không đúng dạng yyyy-mm-dd' for c in cot_ngay if r.get(c) and not la_ngay(r[c])]
        sai += [f'{tep} dòng {i}, cột {c}: "{r[c]}" không phải số (dấu chấm thập phân, không dấu phân cách hàng nghìn)'
                for c in cot_so if r.get(c) and not MAU_SO.match(r[c])]
    return sai


# ---------------------------------------------------------------- huy động
def quy_sprint(lich, tvs):
    """{(id, sprint): MD huy động} theo lich.phan_bo[].quy; lịch không có quy thì tính bằng loi.quy_thoi_gian."""
    pb = lich.get('phan_bo', [])
    if pb and all('quy' in x for x in pb):
        out = {}
        for x in pb:
            k = (x['thanh_vien'], x['sprint'])
            out[k] = out.get(k, 0.0) + float(x['quy'] or 0)
        return out
    return {(t['id'], s): q for t in tvs for s, q in loi.quy_thoi_gian(t, lich['sprint']).items()}


def _ngay_ky_ket_thuc(lich, da):
    """Ngày làm việc (date) của giai đoạn Kết thúc: từ ngày đầu giai đoạn ket_thuc trong lich.json (giai_doan) đến ngay_dong_du_an
    (không có thì ngày cuối giai đoạn), trừ thứ Bảy, Chủ nhật và ngày nghỉ của du_an.json. Lịch không có giai đoạn này thì rỗng."""
    k = next((x for x in lich.get('giai_doan') or [] if x.get('ma') == 'ket_thuc'), None)
    if not k or not k.get('tu'):
        return []
    den = D(lich.get('ngay_dong_du_an') or k.get('den') or k['tu'])
    nghi = set(da.get('ngay_nghi', []))
    d, ds = D(k['tu']), []
    while d <= den:
        if d.weekday() < 5 and d.isoformat() not in nghi:
            ds.append(d)
        d += dt.timedelta(days=1)
    return ds


def ky_ket_thuc(lich, da=None):
    """Kỳ KT {ma, ten, tu, den, so_ngay} của giai đoạn Kết thúc sau cut over, lịch không có giai đoạn này thì None."""
    ds = _ngay_ky_ket_thuc(lich, da or loi.du_an())
    if not ds:
        return None
    return {'ma': KY_KET_THUC, 'ten': 'Kết thúc', 'tu': ds[0].isoformat(), 'den': ds[-1].isoformat(), 'so_ngay': len(ds)}


def cac_ky(lich, da=None):
    """Các kỳ của lịch theo thứ tự thời gian: sprint, sau đó kỳ KT khi lịch có giai đoạn Kết thúc."""
    kt = ky_ket_thuc(lich, da)
    return list(lich['sprint']) + ([kt] if kt else [])


def ngay_lam_viec_du_an(da, lich):
    """Ngày làm việc của dự án: từ ngày bắt đầu đến cut over (loi.ngay_lam_viec), cộng ngày làm việc của giai đoạn Kết thúc đến
    ngay_dong_du_an khi lịch có giai đoạn này. Dùng cho kiểm tra ngày nhật ký, PV, huy động và báo cáo kỳ KT."""
    days = loi.ngay_lam_viec(da)
    return days + [d for d in _ngay_ky_ket_thuc(lich, da) if not days or d > days[-1]]


def ty_le_sprint_da_qua(lich, days, den):
    """{kỳ: tỷ lệ ngày làm việc của kỳ (sprint, kỳ KT) đã qua tính đến ngày den}."""
    out = {}
    for s in cac_ky(lich):
        a, b = D(s['tu']), D(s['den'])
        n = int(s.get('so_ngay') or 0) or sum(1 for d in days if a <= d <= b) or 1
        out[s['ma']] = min(1.0, sum(1 for d in days if a <= d <= min(b, den)) / n)
    return out


def md_huy_dong(lich, tvs, days, den=None):
    """Trả về ({id: MD huy động}, {(id, sprint): MD huy động}) tính đến ngày den (date), den None là cả dự án."""
    q = quy_sprint(lich, tvs)
    tl = ty_le_sprint_da_qua(lich, days, den) if den else None
    theo_sp = {k: v * (tl.get(k[1], 0.0) if tl is not None else 1.0) for k, v in q.items()}
    tong = {}
    for (p, _), v in theo_sp.items():
        tong[p] = tong.get(p, 0.0) + v
    return tong, theo_sp


def md_cong_viec_sprint(lich):
    """{(id, sprint): MD công việc kế hoạch} theo lich.phan_bo[].md."""
    out = {}
    for x in lich.get('phan_bo', []):
        k = (x['thanh_vien'], x['sprint'])
        out[k] = out.get(k, 0.0) + float(x['md'] or 0)
    return out


def md_cong_viec(lich, days=None, den=None, tong_wbs=None):
    """{id: MD công việc kế hoạch} tính đến ngày den (None là cả dự án). Có tong_wbs thì làm tròn sao cho tổng bằng tổng WBS."""
    tl = ty_le_sprint_da_qua(lich, days, den) if den else None
    tong = {}
    for (p, s), v in md_cong_viec_sprint(lich).items():
        tong[p] = tong.get(p, 0.0) + v * (tl.get(s, 0.0) if tl is not None else 1.0)
    if tong_wbs is None or not tong or not sum(tong.values()):
        return tong
    he_so = float(tong_wbs) / sum(tong.values())
    return dict(zip(tong, loi.lam_tron_tong([v * he_so for v in tong.values()])))


def luong_ngay(dg, tvs):
    """{id: lương ngày chưa gồm bảo hiểm}; vai trò thiếu lương tham chiếu thì None."""
    return {t['id']: loi.don_gia_ngay_vai_tro(dg, t['vai_tro']) for t in tvs}


def chi_phi_luong(md, lng, hs):
    """Chi phí doanh nghiệp {id: MD x lương ngày x hệ số bảo hiểm}, chưa làm tròn."""
    return {p: v * (lng.get(p) or 0) * hs for p, v in md.items()}


def chi_phi_luong_ke_hoach(cach, lich, tvs, dg, days, tong_wbs):
    """{id: chi phí lương kế hoạch cả dự án} theo cách trả lương, cùng cách tính với cost estimate."""
    hs = float(dg.get('he_so_bao_hiem', 1.0))
    md = md_huy_dong(lich, tvs, days)[0] if theo_huy_dong(cach) else md_cong_viec(lich, tong_wbs=tong_wbs)
    return chi_phi_luong(md, luong_ngay(dg, tvs), hs)


def chi_phi_luong_luy_ke(cach, lich, tvs, dg, days, den, tong_wbs):
    """Chi phí lương kế hoạch lũy kế đến ngày den theo cách trả lương (đường cơ sở chi phí lương theo thời gian, cùng cơ sở với
    cost estimate): MD giao (cong_suc, tổng bằng tổng WBS) hoặc MD huy động theo người, sprint, sprint đang chạy tính theo tỷ lệ ngày."""
    tl = ty_le_sprint_da_qua(lich, days, den)
    lng = luong_ngay(dg, tvs); hs = float(dg.get('he_so_bao_hiem', 1.0))
    if theo_huy_dong(cach):
        md, he_so = quy_sprint(lich, tvs), 1.0
    else:
        md = md_cong_viec_sprint(lich)
        he_so = float(tong_wbs) / sum(md.values()) if tong_wbs and sum(md.values()) else 1.0
    return sum(v * he_so * tl.get(s, 0.0) * (lng.get(p_) or 0) * hs for (p_, s), v in md.items())


def ev_luong(ev_md, khoi_luong_ke_hoach, chi_phi_ke_hoach):
    """EV nhân sự theo thời điểm thu được: tìm thời điểm kế hoạch có khối lượng lũy kế bằng EV (MD), trả chi phí lương kế hoạch lũy kế
    tại thời điểm đó (nội suy tuyến tính trong ngày). khoi_luong_ke_hoach, chi_phi_ke_hoach: giá trị lũy kế cuối mỗi ngày làm việc.
    EV bằng toàn bộ khối lượng thì trả toàn bộ chi phí kế hoạch (lương kỳ KT trải đến ngày đóng dự án, sau ngày gói Kết thúc xong)."""
    if khoi_luong_ke_hoach and ev_md >= khoi_luong_ke_hoach[-1] - 1e-9:
        return chi_phi_ke_hoach[-1]
    w0, c0 = 0.0, 0.0
    for w, c in zip(khoi_luong_ke_hoach, chi_phi_ke_hoach):
        if w >= ev_md - 1e-9:
            return c0 + (c - c0) * ((ev_md - w0) / (w - w0) if w > w0 else 1.0)
        w0, c0 = w, c
    return c0


def du_phong_khoan_b(cfg, B):
    """Dự phòng rủi ro nằm trong khoản B theo du_phong_rui_ro.so_tien: trống hoặc null là cả khoản B, 0 là không có dự phòng,
    số từ 0 đến B là phần dự phòng. Trả về (số tiền, đã tách khỏi B, thông báo lỗi)."""
    v = cfg.get('so_tien')
    if v in (None, ''):
        return float(B), False, ''
    try:
        v = float(v)
    except (TypeError, ValueError):
        return float(B), False, f'du_phong_rui_ro.so_tien "{v}" không phải số'
    if not 0 <= v <= float(B):
        return float(B), False, f'du_phong_rui_ro.so_tien {loi.tien(v)} đồng phải từ 0 đến khoản B ({loi.tien(B)} đồng)'
    return v, True, ''


def doi_chieu_cost_estimate(cp, chi_phi_ca_du_an, cach=None):
    """Thông báo khi chi phí lương kế hoạch cả dự án lệch tong_chi_phi_nguoi của cost estimate, rỗng khi khớp."""
    ce = cp.get('tong_chi_phi_nguoi')
    if ce is None:
        return 'du_lieu/chi_phi.json chưa có tong_chi_phi_nguoi (đối chiếu lương theo người), lập lại cost estimate'
    if cach and cp.get('cach_tra_luong') and cp['cach_tra_luong'] != cach:
        return f'Cost estimate lập theo cách trả lương {cp["cach_tra_luong"]}, don_gia.json hiện là {cach}. Lập lại cost estimate'
    tong = sum(chi_phi_ca_du_an.values())
    if abs(tong - float(ce)) > len(chi_phi_ca_du_an) + 1:  # cost estimate làm tròn từng người
        return (f'Chi phí lương kế hoạch tính từ lịch hiện hành ({loi.tien(tong)} đồng) khác cost estimate '
                f'({loi.tien(ce)} đồng). Lập lại cost estimate theo lịch hiện hành')
    return ''


# ---------------------------------------------------------------- chi phí khác thực tế
def doc_chi_phi_thuc_te():
    """Đọc và kiểm tra dau_vao/thuc_te/chi_phi_thuc_te.csv. Trả về (dòng hợp lệ, thông báo lỗi, có cột loai)."""
    rows = loi.doc_csv('dau_vao/thuc_te/chi_phi_thuc_te.csv')
    tep = 'chi_phi_thuc_te.csv'
    sai = kiem_tra_o(rows, tep, cot_ngay=('ngay',), cot_so=('so_tien',), bat_buoc=('ngay', 'so_tien'))
    sai += [f'{tep} dòng {i}, cột loai: "{r["loai"]}" chỉ nhận da_chi hoặc cam_ket'
            for i, r in enumerate(rows, 2) if r.get('loai') and r['loai'] not in LOAI_CHI_PHI]
    if sai:
        return [], sai, False
    co_loai = any('loai' in r for r in rows)
    ok = [dict(r, so_tien=float(r['so_tien']), loai=r.get('loai') or 'da_chi') for r in rows]
    return ok, [], co_loai


def tong_chi_phi_khac(ds, den=None, loai='da_chi'):
    """Tổng chi phí khác theo loại, tính đến ngày den (date) nếu có."""
    return sum(x['so_tien'] for x in ds if x['loai'] == loai and (den is None or D(x['ngay']) <= den))


# ---------------------------------------------------------------- số liệu mô phỏng
def mo_phong():
    """Nội dung du_lieu/mo_phong.json khi số liệu thực tế do qlda-mo-phong sinh, rỗng khi không có."""
    mp = loi.doc_json(TEP_MO_PHONG, {})
    return mp if (mp.get('so_lieu_mo_phong') or mp.get('_ghi_chu')) else {}


def can_cu_mo_phong(chu_the='báo cáo'):
    """Đoạn căn cứ khi số liệu thực tế là số liệu mô phỏng, rỗng khi không có du_lieu/mo_phong.json. Đoạn dẫn chiếu {mo_phong#_ghi_chu}
    để lap_khung.py (khối doan_ds) giải từ bí danh nguồn tùy chọn mo_phong của đặc tả, không chép lời văn của tệp vào dữ liệu."""
    mp = mo_phong()
    if not mp:
        return []
    return [f'Số liệu thực tế trong {chu_the} là số liệu mô phỏng.' + (' {mo_phong#_ghi_chu}' if mp.get('_ghi_chu') else '')]
