"""Kiểm tra nhất quán dữ liệu thực tế (sinh bằng mô phỏng hoặc nhập tay) với kế hoạch đã duyệt dùng tại thời điểm ghi.

Kế hoạch của từng sprint: lam_viec/mo_phong/lich_S<n>.json (bản lịch dùng khi sinh sprint đó), không có thì lấy du_lieu/lich.json.
Mã kiểm tra (tiếp sau dãy KB của kich_ban.py):
MP01 tổng MD một người một ngày vượt tỷ lệ tham gia (thanh_vien.json ty_le, thường 1 MD), MP02 ghi công vào gói chưa đến lịch (trước
ngày bắt đầu kế hoạch), MP03 ghi công khi gói tiền nhiệm chưa hoàn thành, MP04 ghi công sau ngày gói đạt 100%, MP05 MD theo người trong
sprint vượt quỹ huy động hoặc ghi công trong sprint không được huy động, MP06 lỗi Đã đóng thiếu ngày đóng hoặc ngày đóng trước ngày phát
hiện, MP07 người ghi công không có trong phân công của gói (cảnh báo), MP08 ghi công vào ngày không phải ngày làm việc, MP09 tỷ lệ hoàn
thành giảm, MP10 mốc ghi đạt trước khi gói căn cứ hoàn thành, MP11 rủi ro đã xảy ra chưa có vấn đề liên kết trong sổ (cảnh báo),
MP12 mã thành viên hoặc mã gói không có.
"""
import os

import mp_chung as C

loi = C.loi


class BoKeHoach:
    """Ngữ cảnh kế hoạch theo sprint, dùng bản lịch đã lưu khi sinh sprint đó."""

    def __init__(self):
        self.hien_hanh = C.NguCanh()
        self._cache = {}

    def cua_sprint(self, sp):
        p = f'{C.THU_MUC_LV}/lich_{sp}.json'
        if not sp or not os.path.exists(loi.duong_dan(p)):
            return self.hien_hanh
        if sp not in self._cache:
            self._cache[sp] = C.NguCanh(loi.doc_json(p))
        return self._cache[sp]

    def cua_ngay(self, d):
        return self.cua_sprint(self.hien_hanh.sprint_cua_ngay(d))


def kiem_tra(bang, kh=None):
    """bang: {tên tệp: danh sách dòng} (đủ các tệp trong mp_chung.COT). Trả về danh sách phát hiện."""
    kh = kh or BoKeHoach()
    ctx = kh.hien_hanh
    F = []
    add = lambda ma, mo, md='loi': F.append({'ma': ma, 'muc_do': md, 'mo_ta': mo})  # noqa: E731
    nk = bang['nhat_ky_cong_viec']
    xong = {}
    pt = {}
    for r in sorted(bang['hoan_thanh'], key=lambda r: r['ngay_cap_nhat']):
        v = float(r['phan_tram'] or 0)
        if r['ma_goi'] in pt and v < pt[r['ma_goi']] - 1e-9:
            add('MP09', f'hoan_thanh.csv: tỷ lệ của {r["ma_goi"]} giảm từ {pt[r["ma_goi"]]:g} xuống {v:g} ngày {r["ngay_cap_nhat"]}')
        pt[r['ma_goi']] = max(v, pt.get(r['ma_goi'], 0))
        if v >= 100 and r['ma_goi'] not in xong:
            xong[r['ma_goi']] = r['ngay_cap_nhat']
    _kiem_nhat_ky(nk, xong, kh, add)
    _kiem_quy(nk, kh, add)
    _kiem_loi(bang['loi'], add)
    for r in bang['moc_thuc_te']:
        m = ctx.moc.get(r['ma_moc'])
        if not m:
            continue
        chua = [g for g in kh.cua_ngay(r['ngay_dat']).ma_can_cu_moc(m) if xong.get(g, '9999') > r['ngay_dat']]
        if chua:
            add('MP10', f'mốc {r["ma_moc"]} ghi đạt ngày {r["ngay_dat"]} khi gói căn cứ chưa hoàn thành: {", ".join(chua[:8])}')
    vd_rr = {m for v in bang['so_van_de'] for m in str(v.get('ma_rui_ro', '')).replace(',', ';').split(';') if m.strip()}
    vd_rr = {m.strip() for m in vd_rr}
    for m in sorted({r['ma_rui_ro'] for r in bang['theo_doi_rui_ro'] if r['trang_thai'] == 'Đã xảy ra'} - vd_rr):
        add('MP11', f'rủi ro {m} đã xảy ra nhưng chưa có vấn đề nào trong so_van_de.csv ghi ma_rui_ro {m} (tín hiệu T25 của báo cáo tiến độ)', 'canh_bao')
    return F


def _kiem_nhat_ky(nk, xong, kh, add):
    ngay_nguoi, dau = {}, {}
    for i, r in enumerate(nk, 2):
        ctx = kh.cua_ngay(r['ngay'])
        try:
            d = C.D(r['ngay']); m = float(r['md'])
        except ValueError:
            add('MP12', f'nhat_ky_cong_viec.csv dòng {i}: ngày hoặc MD không hợp lệ'); continue
        p, g = r['thanh_vien'], r['ma_goi']
        if p not in ctx.tv or g not in ctx.goi:
            add('MP12', f'nhat_ky_cong_viec.csv dòng {i}: {"thành viên " + p if p not in ctx.tv else "gói " + g} không có trong kế hoạch'); continue
        if d not in ctx.days:
            add('MP08', f'nhat_ky_cong_viec.csv dòng {i}: {r["ngay"]} không phải ngày làm việc')
        ngay_nguoi[(p, r['ngay'])] = ngay_nguoi.get((p, r['ngay']), 0) + m
        x = ctx.goi[g]
        if r['ngay'] < x['bat_dau']:
            add('MP02', f'nhat_ky_cong_viec.csv dòng {i}: {p} ghi công gói {g} ngày {r["ngay"]}, gói chưa đến lịch (bắt đầu kế hoạch {x["bat_dau"]})')
        if g in xong and r['ngay'] > xong[g]:
            add('MP04', f'nhat_ky_cong_viec.csv dòng {i}: {p} ghi công gói {g} ngày {r["ngay"]}, sau ngày gói đạt 100% ({xong[g]})')
        if p not in (x.get('phan_nguoi') or {}):
            add('MP07', f'nhat_ky_cong_viec.csv dòng {i}: {p} không có trong phân công gói {g}', 'canh_bao')
        dau[g] = min(dau.get(g, r['ngay']), r['ngay'])
    for (p, d), m in sorted(ngay_nguoi.items()):
        tl = float(kh.hien_hanh.tv[p].get('ty_le', 1.0))
        if m > tl + 1e-6:
            add('MP01', f'{p} ghi {m:g} MD ngày {d}, vượt {tl:g} MD mỗi ngày')
    for g, d in sorted(dau.items(), key=lambda kv: loi.khoa_ma(kv[0])):
        ctx = kh.cua_ngay(d)
        for tn in ctx.goi[g].get('phu_thuoc', []):
            chua = [la for la in ctx.la_cua(tn) if xong.get(la, '9999') >= d]
            if chua:
                add('MP03', f'gói {g} bắt đầu ghi công ngày {d} khi gói tiền nhiệm {", ".join(chua)} chưa hoàn thành trước ngày đó')


def _kiem_quy(nk, kh, add):
    theo = {}
    for r in nk:
        sp = kh.hien_hanh.sprint_cua_ngay(r['ngay'])
        try:
            theo[(r['thanh_vien'], sp)] = theo.get((r['thanh_vien'], sp), 0) + float(r['md'])
        except ValueError:
            continue
    for (p, sp), m in sorted(theo.items(), key=lambda kv: (kv[0][1] or '', kv[0][0])):
        q = kh.cua_sprint(sp).quy.get((p, sp), 0)
        if m > q + 1e-6:
            add('MP05', f'{p} ghi {m:g} MD trong {sp}, vượt quỹ huy động {q:g} MD (lich.json phan_bo)' if q else
                f'{p} ghi {m:g} MD trong {sp} nhưng không được huy động trong sprint này')


def _kiem_loi(bug, add):
    for r in bug:
        if r['muc_do'] not in C.MUC_LOI:
            add('MP06', f'loi.csv: {r["ma"]} có mức "{r["muc_do"]}" không hợp lệ')
        if r['trang_thai'] == 'Đã đóng' and not r['ngay_dong']:
            add('MP06', f'loi.csv: {r["ma"]} Đã đóng nhưng thiếu ngay_dong')
        elif r['ngay_dong'] and r['ngay_dong'] < r['ngay_phat_hien']:
            add('MP06', f'loi.csv: {r["ma"]} có ngày đóng {r["ngay_dong"]} trước ngày phát hiện {r["ngay_phat_hien"]}')
        elif r['trang_thai'] == 'Mở' and r['ngay_dong']:
            add('MP06', f'loi.csv: {r["ma"]} còn Mở nhưng đã ghi ngay_dong', 'canh_bao')
