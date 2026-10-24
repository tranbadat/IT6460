"""Chế độ lập lại lịch từ một ngày (sau yêu cầu thay đổi, cập nhật tiến độ), do lap_lich.py import (không chạy trực tiếp).

Khai báo: moc_nhap.json khóa lap_lai_tu {"ngay": "yyyy-mm-dd", "lich_goc": "<lịch trước khi lập lại>", "ma_cr": "CRxx"}, hoặc tham số
--tu-ngay yyyy-mm-dd [--lich-goc <tệp>] của lap_lich.py (mặc định lịch gốc là du_lieu/lich.json). Nên lưu lịch gốc thành tệp riêng
(qlda-change ap_dung lưu lam_viec/thay_doi/CRxx/lich_truoc_cr.json) để chạy lại nhiều lần cho cùng kết quả.
Trạng thái gói lá thường (không dàn trải) tại ngày lập lại:
- Tỷ lệ đã làm: dau_vao/thuc_te/hoan_thanh.csv (mới nhất đến trước ngày lập lại), thiếu thì theo lịch gốc (gói xong trước ngày là
  1, chưa bắt đầu là 0, đang làm theo tỷ lệ ngày đã qua).
- Ngày thực tế: nhật ký công việc (dau_vao/thuc_te/nhat_ky_cong_viec.csv) cho ngày bắt đầu, ngày kết thúc của gói đã xong; thiếu thì
  ngày của lịch gốc.
- Gói đã xong giữ ngày, phần MD tăng sau lập lại (MD hiện tại lớn hơn MD gốc) xếp như phần làm lại. Gói đang làm giữ ngày bắt đầu,
  chỉ xếp phần MD còn lại từ ngày lập lại. Gói chưa bắt đầu và gói mới không bắt đầu trước ngày lập lại.
"""
import datetime as dt

NGUONG_MD = 0.05  # phần MD còn lại nhỏ hơn mức này coi như xong


def _ngay_thuc_te(loi, ngay):
    """mã gói -> (ngày đầu, ngày cuối) có ghi MD trong nhật ký công việc, trước ngày lập lại."""
    out = {}
    for r in loi.doc_csv('dau_vao/thuc_te/nhat_ky_cong_viec.csv'):
        d, m = r.get('ngay', ''), r.get('ma_goi', '')
        try:
            co_md = float(r.get('md') or 0) > 0
        except ValueError:
            co_md = False
        if m and d and d < ngay and co_md:
            a, b = out.get(m, (d, d))
            out[m] = (min(a, d), max(b, d))
    return out


def _ty_le_thuc_te(loi, ngay):
    tt = {}
    for r in sorted(loi.doc_csv('dau_vao/thuc_te/hoan_thanh.csv'), key=lambda r: r.get('ngay_cap_nhat', '')):
        if r.get('ngay_cap_nhat', '') < ngay and r.get('ma_goi'):
            try:
                tt[r['ma_goi']] = min(1.0, max(0.0, float(r['phan_tram']) / 100))
            except ValueError:
                continue
    return tt


def _phan_nguoi(g, nguoi, s, f, i0, p_goi):
    """MD đã làm và khoảng đã làm của từng người. Lịch gốc có phan_chi_so (khoảng làm của từng người) thì tính theo khoảng đó,
    thiếu thì chia theo tỷ lệ của cả gói."""
    pn, pc = g.get('phan_nguoi') or {}, g.get('phan_chi_so') or {}
    tong = sum(float(pn.get(p, 0)) for p in nguoi)
    out = {}
    for p in nguoi:
        md_p = float(pn.get(p, 0)) if tong else float(g.get('md') or 0) / len(nguoi)
        a, b = pc.get(p, (s, f))
        ty_le = p_goi if p not in pc or p_goi >= 1 else (1.0 if b < i0 else 0.0 if a >= i0 else (i0 - a) / (b - a + 1))
        out[p] = (md_p, md_p * ty_le, a, min(b, i0 - 1))
    return out


def trang_thai(loi, lich_goc, ngay, chi_so_tu, chi_so_den, goi_hien_tai, loe):
    """goi_hien_tai: {mã: (MD hiện tại, [người])}. Trả (chỉ số ngày lập lại, {mã: {loai: da_xong | dang_lam | lam_lai, bat_dau, ket_thuc,
    da_lam, con_lai, nguoi: {người: (MD đã làm, đầu, cuối, MD còn lại)}, nguon}}) cho gói lá thường đã bắt đầu trước ngày lập lại.
    Gói không có trong kết quả là chưa bắt đầu."""
    i0 = chi_so_tu(ngay)
    tt, nk = _ty_le_thuc_te(loi, ngay), _ngay_thuc_te(loi, ngay)
    out = {}
    for g in lich_goc.get('goi', []):
        m = g['ma']
        if not g.get('la') or g.get('dan_trai') or m in loe or m not in goi_hien_tai or not g.get('bat_dau'):
            continue
        s, f = chi_so_tu(g['bat_dau']), chi_so_den(g['ket_thuc'])
        if m in tt:
            p, nguon = tt[m], 'thực tế'
        else:
            p, nguon = (1.0 if f < i0 else 0.0 if s >= i0 else (i0 - s) / (f - s + 1)), 'kế hoạch'
        if p <= 0:
            continue
        if m in nk:
            s = chi_so_tu(nk[m][0])
            if p >= 1:
                f = chi_so_den(nk[m][1])
        s, f = min(s, i0 - 1), min(f, i0 - 1)
        md_now, nguoi = goi_hien_tai[m]
        pn = _phan_nguoi(g, nguoi, s, f, i0, p)
        if nguon == 'thực tế':  # tỷ lệ thực tế của cả gói chia đều cho từng người theo MD, trong khoảng làm thực tế của gói
            # (gói làm muộn hơn khoảng kế hoạch thì khoảng kế hoạch của từng người không còn đúng, dùng ngày trong nhật ký)
            b_tt = min(max(chi_so_den(nk[m][1]) if m in nk else f, s), i0 - 1)
            pn = {q: (v[0], v[0] * p, s, b_tt) for q, v in pn.items()}
        md_goc = float(g.get('md') or 0)
        he_so = md_now / md_goc if md_goc else 1.0  # MD tăng của gói chia theo phần của từng người
        nguoi_out = {q: (v[1], max(v[2], s) if v[1] else s, v[3], max(0.0, v[0] * he_so - v[1])) for q, v in pn.items()}
        da_lam = sum(v[0] for v in nguoi_out.values())
        con = sum(v[3] for v in nguoi_out.values())
        loai = 'da_xong' if con < NGUONG_MD else ('dang_lam' if p < 1 else 'lam_lai')
        out[m] = {'loai': loai, 'bat_dau': s, 'ket_thuc': f, 'da_lam': da_lam, 'con_lai': 0.0 if loai == 'da_xong' else con,
                  'nguoi': nguoi_out, 'nguon': nguon}
    return i0, out


def kiem_tra_ngay(ngay):
    dt.date.fromisoformat(ngay)
    return ngay


def toc_do_ngay(tv, gv, la, sprints, n):
    """Tốc độ mỗi ngày của từng người cho gói không dàn trải, dùng chung cho lap_lich.py và qlda-phan-cong/kiem_tra_giao_viec.py
    (MD từng người của gói chưa bắt đầu chia theo tốc độ này, nên tải theo người khớp phân bổ của lịch): ty_le trừ MD việc dàn trải
    (chia đều cho người thực hiện và hỗ trợ) chia số ngày tham gia (tu_sprint, den_sprint của thanh_vien.json trong n ngày làm việc).
    Trả {người: tốc độ chưa chặn dưới}, lap_lich.py cảnh báo L04 và chặn dưới."""
    loe = {p: 0.0 for p in tv}
    for g in la:
        x = gv.get(g['ma'])
        if x and x.get('dan_trai'):
            ng = [x['R']] + x.get('ho_tro', [])
            for p in ng:
                loe[p] += float(g['md']) / len(ng)

    def chi_so(p, khoa, dau):
        v = tv[p].get(khoa)
        if v in (None, ''):
            return 0 if dau else n - 1
        s = next((s for s in sprints if s['so'] == int(v)), None)
        return (s['chi_so_dau'] if dau else s['chi_so_cuoi']) if s else (n if dau else n - 1)
    return {p: float(tv[p].get('ty_le', 1)) - loe[p] / max(1, min(n - 1, chi_so(p, 'den_sprint', False)) - chi_so(p, 'tu_sprint', True) + 1) for p in tv}
