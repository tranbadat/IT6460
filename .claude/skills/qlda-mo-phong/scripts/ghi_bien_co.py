"""Chuyển biến cố của kịch bản thành dòng dữ liệu thực tế (rủi ro, lỗi, vấn đề, hành động, chi phí khác, nghiệm thu, mốc, họp cải tiến)
và áp dụng việc đã hẹn từ sprint trước (lỗi đóng, hành động xong, vấn đề đóng, rủi ro đóng khi đến ngày).

Việc hẹn ngày sau sprint hiện tại được lưu trong du_lieu/mo_phong.json cho_xu_ly, sprint chứa ngày đó sẽ ghi. Bảng CSV chỉ phản ánh
những gì đã xảy ra đến ngày cuối sprint đã sinh, nên báo cáo tiến độ từng kỳ đọc đúng trạng thái tại kỳ đó.
"""
import re

import mp_chung as C

THU_TU_HEN = {'xong_hanh_dong': 0, 'dong_loi': 1, 'dong_rui_ro': 2, 'dong_van_de': 3}


class GhiBienCo:
    def __init__(self, ctx, ma_sp, bang, cho_xu_ly, rng, xong):
        """bang: {tên tệp: dòng} sẽ được thay bằng bản mới (không sửa danh sách gốc); xong: {gói: date} sau khi mô phỏng công."""
        self.ctx, self.sp, self.rng, self.xong = ctx, ma_sp, rng, xong
        self.bang = {k: [dict(r) for r in v] for k, v in bang.items()}
        self.ngay = ctx.ngay_sprint(ma_sp)
        self.tu, self.den = self.ngay[0].isoformat(), self.ngay[-1].isoformat()
        self.hen = [dict(x) for x in cho_xu_ly]
        self.cfg = C.cau_hinh()
        self.F, self.retro, self.cr = [], [], []
        self.dem = {k: 0 for k in C.COT}

    def add(self, ma, mo_ta, md='loi'):
        self.F.append({'ma': ma, 'muc_do': md, 'vi_tri': self.sp, 'mo_ta': mo_ta})

    def them(self, ten, row):
        self.bang[ten].append({c: row.get(c, '') for c in C.COT[ten]}); self.dem[ten] += 1

    def tim(self, ten, ma):
        return next((r for r in self.bang[ten] if r.get('ma') == ma), None)

    def hen_ngay(self, ngay, loai, ma, **them):
        if ngay <= self.den:
            self.ap_dung_hen(dict(them, ngay=ngay, loai=loai, ma=ma))
        else:
            self.hen.append(dict(them, ngay=ngay, loai=loai, ma=ma))

    # ------------------------------------------------------------ việc hẹn từ sprint trước
    def ap_dung_cho_xu_ly(self):
        den_han = sorted([x for x in self.hen if x['ngay'] <= self.den], key=lambda x: (x['ngay'], THU_TU_HEN[x['loai']]))
        self.hen = [x for x in self.hen if x['ngay'] > self.den]
        for x in den_han:
            self.ap_dung_hen(x)

    def ap_dung_hen(self, x):
        if x['loai'] == 'dong_loi':
            r = self.tim('loi', x['ma'])
            if r and r['trang_thai'] != 'Đã đóng':
                r.update(trang_thai='Đã đóng', ngay_dong=x['ngay'])
        elif x['loai'] == 'xong_hanh_dong':
            r = self.tim('hanh_dong', x['ma'])
            if r and r['trang_thai'] not in ('Hoàn thành', 'Hủy'):
                r.update(trang_thai='Hoàn thành', ngay_xong=x['ngay'], bang_chung=x.get('bang_chung', ''))
        elif x['loai'] == 'dong_van_de':
            r = self.tim('so_van_de', x['ma'])
            con = [h['ma'] for h in self.bang['hanh_dong'] if h['ma_van_de'] == x['ma'] and h['trang_thai'] not in ('Hoàn thành', 'Hủy')]
            if con:
                self.add('KB10', f'không đóng được {x["ma"]} ngày {x["ngay"]}: hành động {", ".join(con)} chưa hoàn thành'); return
            if r:
                r.update(trang_thai='Đã đóng', ngay_dong=x['ngay'], ket_qua=x.get('ket_qua', ''), nguoi_dong=x.get('nguoi_dong', ''))
        elif x['loai'] == 'dong_rui_ro':
            self.them('theo_doi_rui_ro', {'ngay': x['ngay'], 'ma_rui_ro': x['ma'], 'trang_thai': 'Đã đóng', 'hanh_dong': x.get('hanh_dong', ''),
                                          'ghi_chu': x.get('ghi_chu', '')})

    # ------------------------------------------------------------ biến cố
    def b_rui_ro(self, e):
        m = e['ma_rui_ro']; rr = self.ctx.ma_rr.get(m, {})
        ghi_chu = e.get('ten') if m not in self.ctx.ma_rr else e.get('ghi_chu', '')
        if e.get('ngay_kich_hoat'):
            self.them('theo_doi_rui_ro', {'ngay': e['ngay_kich_hoat'], 'ma_rui_ro': m, 'trang_thai': 'Đã kích hoạt ứng phó',
                                          'hanh_dong': e.get('hanh_dong_kich_hoat') or e.get('hanh_dong', ''), 'ma_cr': e.get('ma_cr', ''),
                                          'ghi_chu': ghi_chu}); ghi_chu = ''
        tt = e.get('trang_thai', 'Đã xảy ra')
        md = float(e.get('md_tac_dong') or 0)
        tien = e.get('chi_phi_tac_dong')
        if tien in (None, '') and tt == 'Đã xảy ra':
            tien = round(md * self.ctx.don_gia_md.get(rr.get('loai_cong_viec'), 0))
        self.them('theo_doi_rui_ro', {'ngay': e['ngay'], 'ma_rui_ro': m, 'trang_thai': tt, 'hanh_dong': e.get('hanh_dong', ''),
                                      'md_tac_dong': md if tt == 'Đã xảy ra' else '', 'chi_phi_tac_dong': float(tien) if tt == 'Đã xảy ra' else '',
                                      'ma_cr': e.get('ma_cr', ''), 'ghi_chu': ghi_chu})
        if e.get('ngay_dong'):
            self.hen_ngay(e['ngay_dong'], 'dong_rui_ro', m, hanh_dong=e.get('hanh_dong_dong', 'Điều kiện đóng đạt'), ghi_chu='')

    def b_loi(self, e):
        g = e['ma_goi']
        bd = max(self.tu, self.ctx.goi[g]['bat_dau'])
        ngay_co = [d for d in self.ngay if d.isoformat() >= bd] or self.ngay
        sua = dict(self.cfg['ngay_sua_loi_mac_dinh'], **(e.get('ngay_sua') or {}))
        con_mo = dict(e.get('con_mo') or {})
        for muc in C.MUC_LOI:
            for i in range(int((e.get('so_loi') or {}).get(muc, 0))):
                ma = C.tiep_ma([r['ma'] for r in self.bang['loi']], 'L')
                d = e.get('ngay_phat_hien') or self.rng.choice(ngay_co).isoformat()
                self.them('loi', {'ma': ma, 'ngay_phat_hien': d, 'muc_do': muc, 'ma_goi': g, 'trang_thai': 'Mở',
                                  'mo_ta': e.get('mo_ta') or f'Lỗi phát hiện khi kiểm thử gói {g}'})
                if con_mo.get(muc, 0) > 0:
                    con_mo[muc] -= 1; continue
                self.hen_ngay(self.ctx.cong_ngay_lam_viec(d, int(sua[muc])).isoformat(), 'dong_loi', ma)

    def b_van_de(self, e):
        r = self.tim('so_van_de', e.get('ma')) if e.get('ma') else None
        if r is None:
            ma = e.get('ma') or C.tiep_ma([x['ma'] for x in self.bang['so_van_de']], 'VD')
            self.them('so_van_de', {'ma': ma, 'ngay_ghi_nhan': e['ngay_ghi_nhan'], 'nguoi_bao': e.get('nguoi_bao', ''), 'mo_ta': e['mo_ta'],
                                    'loai': e.get('phan_loai', ''), 'uu_tien': e['uu_tien'], 'ma_rui_ro': e.get('ma_rui_ro', ''),
                                    'ma_cr': e.get('ma_cr', ''), 'nguoi_phu_trach': e['nguoi_phu_trach'], 'han': e.get('han', ''), 'trang_thai': 'Mở'})
            r = self.bang['so_van_de'][-1]
        else:
            for k in ('han', 'uu_tien', 'nguoi_phu_trach', 'ma_cr', 'ma_rui_ro'):
                if e.get(k):
                    r[k] = e[k]
        for h in e.get('hanh_dong') or []:
            self.hanh_dong(r['ma'], h)
        co_hd = any(h['ma_van_de'] == r['ma'] for h in self.bang['hanh_dong'])
        if r['trang_thai'] != 'Đã đóng':
            r['trang_thai'] = e.get('trang_thai') if e.get('trang_thai') in ('Chuyển cấp', 'Mở', 'Đang xử lý') else ('Đang xử lý' if co_hd else 'Mở')
        if e.get('ngay_dong'):
            self.hen_ngay(e['ngay_dong'], 'dong_van_de', r['ma'], ket_qua=e.get('ket_qua', ''), nguoi_dong=e.get('nguoi_dong', ''))

    def hanh_dong(self, ma_vd, h):
        r = self.tim('hanh_dong', h.get('ma')) if h.get('ma') else None
        if r is None:
            ma = h.get('ma') or C.tiep_ma([x['ma'] for x in self.bang['hanh_dong']], 'HD')
            self.them('hanh_dong', {'ma': ma, 'ma_van_de': ma_vd, 'viec': h['viec'], 'nguoi': h['nguoi'], 'han': h['han'],
                                    'trang_thai': h.get('trang_thai', 'Đang thực hiện')})
            r = self.bang['hanh_dong'][-1]
        if h.get('ngay_xong'):
            self.hen_ngay(h['ngay_xong'], 'xong_hanh_dong', r['ma'], bang_chung=h.get('bang_chung', ''))

    def b_chi_phi(self, e):
        self.them('chi_phi_thuc_te', {'ngay': e['ngay'], 'khoan_muc': e['khoan_muc'], 'so_tien': float(e['so_tien']),
                                      'ghi_chu': e.get('ghi_chu', ''), 'loai': e.get('loai_chi', 'da_chi')})

    def b_nghiem_thu(self, e):
        ma = e.get('ma') or C.tiep_ma([r['ma'] for r in self.bang['nghiem_thu']], 'NT')
        self.them('nghiem_thu', {'ma': ma, 'tieu_chi': e['tieu_chi'], 'hang_muc': e['hang_muc'], 'ket_qua': e['ket_qua'], 'ngay': e['ngay'],
                                 'nguoi_xac_nhan': e['nguoi_xac_nhan'], 'ghi_chu': e.get('ghi_chu', '')})

    def b_moc(self, e):
        m = self.ctx.moc[e['ma_moc']]
        can_cu = self.ctx.ma_can_cu_moc(m)
        chua = [g for g in can_cu if g not in self.xong or self.xong[g].isoformat() > e['ngay_dat']]
        if chua:
            som = max((self.xong[g] for g in can_cu if g in self.xong), default=None)
            goi_y = (f'ngày sớm nhất đủ điều kiện {som.isoformat()}' if not [g for g in can_cu if g not in self.xong]
                     else 'gói căn cứ chưa hoàn thành trong sprint, ghi mốc ở sprint sau')
            self.add('KB07', f'mốc {e["ma_moc"]} ngày {e["ngay_dat"]}: gói căn cứ chưa hoàn thành ({", ".join(chua[:6])}), {goi_y}'); return
        self.them('moc_thuc_te', {'ma_moc': e['ma_moc'], 'ngay_dat': e['ngay_dat'], 'ghi_chu': e.get('ghi_chu', '')})

    def b_retro(self, e):
        for i, y in enumerate(e.get('y') or [], 1):
            lk = ', '.join(y.get('lien_ket') or [])
            nd = y['noi_dung'].strip().rstrip('.')
            self.retro.append(f'- R-{self.sp}-{i:02d} ({y["loai"]}): {nd}.' + (f' Liên kết: {lk}.' if lk else ''))

    def b_cr(self, e):
        self.cr.append({k: e.get(k) for k in ('ma_cr', 'ngay', 'tieu_de', 'mo_ta', 'ly_do', 'nguon', 'nguoi_de_xuat', 'goi_moi', 'goi_thay_doi',
                                              'ma_rui_ro', 'nhan_dinh_ban_dau') if e.get(k) not in (None, '')})

    def b_huy_dong(self, e):
        """Huy động bổ sung chỉ đổi quỹ của sprint (mp_chung.huy_dong_them), lưu trong kịch bản của du_lieu/mo_phong.json."""
        return None

    def chay(self, bien_co):
        self.ap_dung_cho_xu_ly()
        for e in bien_co:
            f = getattr(self, 'b_' + e['loai'], None)
            if f:
                f(e)
        return self


def moc_du_dieu_kien(ctx, xong, da_ghi, den):
    """Mốc chưa ghi mà mọi gói căn cứ đã hoàn thành đến ngày den: [(mã, ngày sớm nhất)]."""
    out = []
    for m in ctx.lich['moc']:
        cc = ctx.ma_can_cu_moc(m)
        if m['ma'] in da_ghi or not cc or any(g not in xong for g in cc):
            continue
        ngay = max(xong[g] for g in cc)
        if ngay.isoformat() <= den:
            out.append((m['ma'], ngay.isoformat()))
    return out


MAU_Y_RETRO = re.compile(r'\s*[-*]\s*R-S\d+-\d+\s*\([^)]*\)\s*:?\s*(.*)')  # cùng mẫu với qlda-bai-hoc/scripts/kiem_tra_bai_hoc.py


def _doc_retro():
    try:
        return open(C.loi.duong_dan(C.TEP_RETRO), encoding='utf-8').read().splitlines()
    except FileNotFoundError:
        return ['# Ghi chép họp cải tiến cuối sprint', '']


def _tach_muc(cu, sp):
    """(các dòng ngoài mục sp, các dòng của mục sp)."""
    ra, muc, i = [], [], 0
    while i < len(cu):
        if cu[i].strip() == f'## {sp}':
            j = i + 1
            while j < len(cu) and not cu[j].startswith('## '):
                j += 1
            muc += cu[i + 1:j]; i = j; continue
        ra.append(cu[i]); i += 1
    return ra, muc


def kiem_retro(sp):
    """Thông báo lỗi khi retro.md đã có mục sp có nội dung (ghi tay), rỗng khi ghi được."""
    _, muc = _tach_muc(_doc_retro(), sp)
    co = [x for x in muc if MAU_Y_RETRO.match(x) and MAU_Y_RETRO.match(x).group(1).strip()]
    return f'retro.md đã có mục {sp} có nội dung, chuyển nội dung đó vào biến cố retro của kịch bản rồi xóa mục' if co else ''


def ghi_retro(sp, dong):
    """Thêm mục '## S<n>' vào retro.md, thay mục mẫu rỗng cùng sprint nếu có (đã kiểm tra bằng kiem_retro)."""
    p = C.loi.duong_dan(C.TEP_RETRO)
    ra, _ = _tach_muc(_doc_retro(), sp)
    while ra and not ra[-1].strip():
        ra.pop()
    ra += ['', f'## {sp}'] + dong
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(ra) + '\n')
