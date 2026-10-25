"""Kiểm tra kịch bản biến cố một sprint (lam_viec/mo_phong/kich_ban_S<n>.json) trước khi sinh số liệu.

Định dạng kịch bản: references/kich_ban.md. Mã kiểm tra:
KB01 thiếu lý do hoặc trường bắt buộc, KB02 loại biến cố hoặc mã sprint không hợp lệ, KB03 mã gói không phải gói lá, gói chưa đến lịch
hoặc đã hoàn thành, KB04 thành viên không có hoặc không được huy động trong sprint, KB05 rủi ro không có trong sổ (ngoài sổ thiếu tên),
trạng thái không hợp lệ, đã xảy ra mà thiếu hành động ứng phó, KB06 ngày sai dạng, ngoài sprint hoặc không phải ngày làm việc,
KB07 mốc không có trong lịch hoặc đã ghi, KB08 chi phí khác sai khoản mục, số tiền, loại, KB09 nghiệm thu thiếu mã yêu cầu RFP, hạng mục
Mẫu 01A hoặc kết quả, KB10 vấn đề sai trường, giá trị, điều kiện đóng, KB11 mã yêu cầu thay đổi không có trong sổ thay đổi và không khai báo
trong kịch bản, hoặc đã có trong sổ với tiêu đề, ngày khác (biến cố cr đã được danh_gia ghi vào sổ với cùng tiêu đề và ngày thì sinh lại
bình thường khi --lam-lai), KB12 biến cố không liên kết tới gói, rủi ro, vấn đề hoặc yêu cầu thay đổi, KB13 mốc cut over sau ngày cut over hợp đồng
mà không có yêu cầu thay đổi đã phê duyệt kèm phụ lục, KB14 biến cố vượt mức vừa phải (cảnh báo), KB15 lỗi sai mức hoặc số lượng.
"""
import re

import mp_chung as C

LOAI = ('goi', 'nghi', 'huy_dong', 'rui_ro', 'loi', 'van_de', 'chi_phi', 'nghiem_thu', 'moc', 'retro', 'cr')
TT_RR = ('Đang theo dõi', 'Đã kích hoạt ứng phó', 'Đã xảy ra', 'Đã đóng')
UU_TIEN = ('Cao', 'Trung bình', 'Thấp')
LOAI_VD = ('Phạm vi', 'Tiến độ', 'Chi phí', 'Chất lượng', 'Nhân sự', 'Kỹ thuật', 'Chủ đầu tư', 'Hợp đồng', 'Khác')
TT_VD = ('Mở', 'Đang xử lý', 'Chuyển cấp', 'Đã đóng')
MAU_LIEN_KET = re.compile(r'^(RR\d+|VD\d+|CR\d+|M\d+|S\d+|L\d+|NT\d+|\d+(\.\d+)*)$')


class KiemTra:
    def __init__(self, ctx, ma_sp, kb, trang_thai):
        """trang_thai: {'xong': {mã gói: ngày hoàn thành}, 'vd': mã vấn đề đã có, 'moc': mốc đã ghi, 'rr_xay_ra': số rủi ro đã xảy ra}."""
        self.ctx, self.sp, self.kb, self.tt = ctx, ma_sp, kb, trang_thai
        self.F = []
        self.ngay = ctx.ngay_sprint(ma_sp) if ma_sp in ctx.sprint else []
        self.tu = self.ngay[0].isoformat() if self.ngay else ''
        self.den = self.ngay[-1].isoformat() if self.ngay else ''
        self.cfg = C.cau_hinh()['muc_vua_phai']
        self.cr_kb = {e.get('ma_cr') for e in kb.get('bien_co', []) if e.get('loai') == 'cr' and e.get('ma_cr')}
        self.vd_kb = {e.get('ma') for e in kb.get('bien_co', []) if e.get('loai') == 'van_de' and e.get('ma')}

    def add(self, ma, mo_ta, vt, md='loi'):
        self.F.append({'ma': ma, 'muc_do': md, 'vi_tri': vt, 'mo_ta': mo_ta})

    # ------------------------------------------------------------ kiểm tra chung
    def ngay_trong_sprint(self, v, vt, cot, bat_buoc=True, chi_lam_viec=True):
        if not v:
            if bat_buoc:
                self.add('KB01', f'thiếu {cot}', vt)
            return False
        try:
            d = C.D(str(v))
        except ValueError:
            self.add('KB06', f'{cot} "{v}" không đúng dạng yyyy-mm-dd', vt)
            return False
        if not (self.tu <= d.isoformat() <= self.den):
            self.add('KB06', f'{cot} {v} ngoài sprint {self.sp} ({self.tu} đến {self.den})', vt)
            return False
        if chi_lam_viec and d not in self.ngay:
            self.add('KB06', f'{cot} {v} không phải ngày làm việc', vt)
            return False
        return True

    def ngay_hop_le(self, v, vt, cot):
        """Ngày bất kỳ (hạn, ngày dự kiến xong ở sprint sau) chỉ cần đúng dạng."""
        try:
            C.D(str(v))
            return True
        except ValueError:
            self.add('KB06', f'{cot} "{v}" không đúng dạng yyyy-mm-dd', vt)
            return False

    def goi_dang_lam(self, ma, vt, cho_phep_xong=False):
        g = self.ctx.goi.get(ma)
        if not g:
            self.add('KB03', f'mã gói {ma} không phải gói lá trong lịch hiện hành', vt)
            return False
        if g['bat_dau'] > self.den:
            self.add('KB03', f'gói {ma} chưa đến lịch: bắt đầu kế hoạch {g["bat_dau"]}, sau ngày cuối sprint {self.den}', vt)
            return False
        if not cho_phep_xong and ma in self.tt['xong']:
            self.add('KB03', f'gói {ma} đã hoàn thành ngày {self.tt["xong"][ma]}, không còn phát sinh công', vt)
            return False
        return True

    def thanh_vien(self, p, vt, cot='thanh_vien', ben_ngoai=False, huy_dong=False):
        if not p:
            self.add('KB01', f'thiếu {cot}', vt)
            return False
        if p in self.ctx.tv:
            if huy_dong and not self.ctx.quy.get((p, self.sp)):
                self.add('KB04', f'{p} không được huy động trong sprint {self.sp}', vt)
                return False
            return True
        if ben_ngoai and self.ctx.la_ben_ngoai(p):
            return True
        self.add('KB04', f'{cot} "{p}" không phải mã thành viên trong thanh_vien.json' + (' hay tên đơn vị bên ngoài' if ben_ngoai else ''), vt)
        return False

    def cr(self, ma, vt):
        if ma and ma not in self.ctx.ma_cr and ma not in self.cr_kb:
            self.add('KB11', f'mã yêu cầu thay đổi {ma} không có trong du_lieu/thay_doi.json và không khai báo bằng biến cố cr', vt)

    def lien_ket(self, e, vt, md='loi'):
        ma = [e.get(k) for k in ('ma_goi', 'ma_rui_ro', 'ma_van_de', 'ma_cr') if e.get(k)] + list(e.get('lien_ket') or [])
        if not ma:
            self.add('KB12', 'biến cố chưa liên kết tới gói, rủi ro, vấn đề hoặc yêu cầu thay đổi (ma_goi, ma_rui_ro, ma_van_de, ma_cr hoặc lien_ket)', vt, md)
        for x in e.get('lien_ket') or []:
            self.kiem_ma_lien_ket(str(x), vt)

    def kiem_ma_lien_ket(self, x, vt):
        if not MAU_LIEN_KET.match(x):
            self.add('KB12', f'mã liên kết "{x}" không đúng dạng (RRxx, VDxx, CRxx, Mx, Sx, Lxx, NTxx hoặc mã gói WBS)', vt)
        elif x.startswith('RR') and x not in self.ctx.ma_rr:
            self.add('KB12', f'mã rủi ro liên kết {x} không có trong sổ rủi ro', vt)
        elif x.startswith('VD') and x not in self.tt['vd'] and x not in self.vd_kb:
            self.add('KB12', f'mã vấn đề liên kết {x} chưa có trong sổ vấn đề và kịch bản', vt)
        elif x.startswith('CR'):
            self.cr(x, vt)
        elif x[0].isdigit() and not self.ctx.la_cua(x):
            self.add('KB12', f'mã gói liên kết {x} không có trong WBS', vt)

    # ------------------------------------------------------------ từng loại biến cố
    def k_goi(self, e, vt):
        if self.goi_dang_lam(e.get('ma_goi', ''), vt):
            t = float(e.get('ty_le_md') or 0); n = int(e.get('so_ngay_tre') or 0)
            if not t and not n:
                self.add('KB01', 'biến cố gói cần ty_le_md (vượt dương, hụt âm) hoặc so_ngay_tre', vt)
            if t > self.cfg['ty_le_md_toi_da'] or t < self.cfg['ty_le_md_toi_thieu']:
                self.add('KB14', f'ty_le_md {t:g} ngoài mức vừa phải ({self.cfg["ty_le_md_toi_thieu"]:g} đến {self.cfg["ty_le_md_toi_da"]:g})', vt, 'canh_bao')
            if n < 0 or n > self.cfg['so_ngay_tre_toi_da']:
                self.add('KB14', f'so_ngay_tre {n} ngoài 0 đến {self.cfg["so_ngay_tre_toi_da"]} ngày', vt, 'canh_bao')

    def k_nghi(self, e, vt):
        if self.thanh_vien(e.get('thanh_vien'), vt, huy_dong=True):
            n = int(e.get('so_ngay') or 0)
            if n <= 0 or n > len(self.ngay):
                self.add('KB01', f'so_ngay {n} phải từ 1 đến {len(self.ngay)}', vt)
            elif n > self.cfg['so_ngay_nghi_toi_da']:
                self.add('KB14', f'nghỉ {n} ngày, vượt mức vừa phải {self.cfg["so_ngay_nghi_toi_da"]} ngày', vt, 'canh_bao')
            if e.get('tu_ngay'):
                self.ngay_trong_sprint(e['tu_ngay'], vt, 'tu_ngay')
        self.lien_ket(e, vt)

    def k_huy_dong(self, e, vt):
        """Huy động bổ sung thực tế theo nhu cầu (từ 1.0.5): thêm so_md vào quỹ của thành viên trong sprint, không vượt số ngày làm việc
        của sprint nhân tỷ lệ tham gia. Cách trả lương theo công sức chỉ tính MD thực làm, theo huy động thì phần thêm làm tăng lương."""
        p = e.get('thanh_vien')
        if p not in self.ctx.tv:
            self.add('KB04', f'thành viên {p} không có trong thanh_vien.json', vt); return
        try:
            m = float(e.get('so_md') or 0)
        except (TypeError, ValueError):
            m = 0
        tran = len(self.ngay) * float(self.ctx.tv[p].get('ty_le', 1.0)) - float(self.ctx.quy_ke_hoach.get((p, self.sp), 0))
        if m <= 0 or m > tran + 1e-9:
            self.add('KB01', f'so_md {m:g} phải lớn hơn 0 và không vượt {tran:g} MD (ngày làm việc của sprint trừ quỹ kế hoạch)', vt)
        self.lien_ket(e, vt)

    def k_rui_ro(self, e, vt):
        m = e.get('ma_rui_ro', '')
        if not m:
            self.add('KB01', 'thiếu ma_rui_ro', vt)
        elif m not in self.ctx.ma_rr and not e.get('ten'):
            self.add('KB05', f'rủi ro {m} không có trong sổ rủi ro; rủi ro phát sinh ngoài sổ phải ghi ten', vt)
        tt = e.get('trang_thai', 'Đã xảy ra')
        if tt not in TT_RR:
            self.add('KB05', f'trạng thái "{tt}" không thuộc {", ".join(TT_RR)}', vt)
        if tt == 'Đã xảy ra' and not e.get('hanh_dong'):
            self.add('KB05', 'rủi ro đã xảy ra phải ghi hanh_dong ứng phó (KPI K12)', vt)
        self.ngay_trong_sprint(e.get('ngay'), vt, 'ngay')
        if e.get('ngay_kich_hoat'):
            self.ngay_trong_sprint(e['ngay_kich_hoat'], vt, 'ngay_kich_hoat')
        if e.get('ngay_dong'):
            self.ngay_hop_le(e['ngay_dong'], vt, 'ngay_dong')
        if float(e.get('md_tac_dong') or 0) or int(e.get('ngay_tac_dong') or 0):
            mg = e.get('ma_goi') or self.goi_mac_dinh_rr(m)
            if not mg:
                self.add('KB03', f'rủi ro {m} có tác động MD hoặc ngày nhưng không xác định được gói chịu tác động, ghi ma_goi', vt)
            else:
                self.goi_dang_lam(mg, vt)
        rr = self.ctx.ma_rr.get(m, {})
        for k, gh in (('md_tac_dong', 'tac_dong_md'), ('ngay_tac_dong', 'tac_dong_ngay')):
            if rr.get(gh) is not None and float(e.get(k) or 0) > float(rr[gh]):
                self.add('KB14', f'{k} {e.get(k)} vượt mức tác động đã đánh giá của {m} ({gh} {rr[gh]})', vt, 'canh_bao')
        self.cr(e.get('ma_cr'), vt)

    def goi_mac_dinh_rr(self, m):
        """Gói chịu tác động mặc định: gói lá đầu tiên trong liên kết WBS của rủi ro còn chưa hoàn thành và đã đến lịch."""
        for x in self.ctx.ma_rr.get(m, {}).get('lien_ket_wbs', []):
            for la in self.ctx.la_cua(x):
                if la not in self.tt['xong'] and self.ctx.goi[la]['bat_dau'] <= self.den:
                    return la
        return ''

    def k_loi(self, e, vt):
        self.goi_dang_lam(e.get('ma_goi', ''), vt, cho_phep_xong=True)
        sl = e.get('so_loi') or {}
        if not isinstance(sl, dict) or not sl:
            self.add('KB15', 'so_loi phải là {mức: số lỗi}', vt)
        for k, v in (sl.items() if isinstance(sl, dict) else []):
            if k not in C.MUC_LOI:
                self.add('KB15', f'mức lỗi "{k}" không thuộc {", ".join(C.MUC_LOI)}', vt)
            if not isinstance(v, int) or v < 0:
                self.add('KB15', f'số lỗi mức {k} phải là số nguyên không âm', vt)
        if e.get('ngay_phat_hien'):
            self.ngay_trong_sprint(e['ngay_phat_hien'], vt, 'ngay_phat_hien')
        if e.get('md_sua') and e.get('ma_goi') in self.tt['xong']:
            self.add('KB03', f'gói {e["ma_goi"]} đã hoàn thành, md_sua phải ghi vào gói đang làm (gói kiểm thử, khắc phục lỗi)', vt)

    def k_van_de(self, e, vt):
        cap_nhat = e.get('ma') in self.tt['vd']
        if not cap_nhat:
            for k in ('mo_ta', 'uu_tien', 'nguoi_phu_trach'):
                if not e.get(k):
                    self.add('KB10', f'vấn đề mới thiếu {k}', vt)
            self.ngay_trong_sprint(e.get('ngay_ghi_nhan'), vt, 'ngay_ghi_nhan')
            if e.get('ma') and not re.match(r'^VD\d+$', e['ma']):
                self.add('KB10', f'mã vấn đề "{e["ma"]}" phải dạng VDxx', vt)
        if e.get('uu_tien') and e['uu_tien'] not in UU_TIEN:
            self.add('KB10', f'uu_tien "{e["uu_tien"]}" không thuộc {", ".join(UU_TIEN)}', vt)
        if e.get('phan_loai') and e['phan_loai'] not in LOAI_VD:
            self.add('KB10', f'phan_loai "{e["phan_loai"]}" không thuộc {", ".join(LOAI_VD)}', vt)
        if e.get('trang_thai') and e['trang_thai'] not in TT_VD:
            self.add('KB10', f'trang_thai "{e["trang_thai"]}" không thuộc {", ".join(TT_VD)}', vt)
        for k in ('nguoi_phu_trach', 'nguoi_bao', 'nguoi_dong'):
            if e.get(k):
                self.thanh_vien(e[k], vt, k, ben_ngoai=True)
        for k in ('han',):
            if e.get(k):
                self.ngay_hop_le(e[k], vt, k)
        for m in tach_ma(e.get('ma_rui_ro')):
            if m not in self.ctx.ma_rr:
                self.add('KB12', f'mã rủi ro {m} không có trong sổ rủi ro', vt)
        for m in tach_ma(e.get('ma_cr')):
            self.cr(m, vt)
        hd = e.get('hanh_dong') or []
        for i, h in enumerate(hd, 1):
            v2 = f'{vt}, hành động {i}'
            for k in ('viec', 'nguoi', 'han'):
                if not h.get(k) and not (cap_nhat and h.get('ma')):
                    self.add('KB10', f'hành động thiếu {k}', v2)
            if h.get('nguoi'):
                self.thanh_vien(h['nguoi'], v2, 'nguoi', ben_ngoai=True)
            if h.get('ngay_xong'):
                self.ngay_hop_le(h['ngay_xong'], v2, 'ngay_xong')
                if not h.get('bang_chung'):
                    self.add('KB10', 'hành động có ngay_xong phải ghi bang_chung', v2)
        if e.get('ngay_dong'):
            if self.ngay_hop_le(e['ngay_dong'], vt, 'ngay_dong'):
                for k in ('ket_qua', 'nguoi_dong'):
                    if not e.get(k):
                        self.add('KB10', f'vấn đề có ngay_dong phải ghi {k}', vt)
                muon = [h.get('ma') or h.get('viec', '')[:30] for h in hd if not h.get('ngay_xong') or h['ngay_xong'] > e['ngay_dong']]
                if muon and not cap_nhat:
                    self.add('KB10', f'vấn đề đóng ngày {e["ngay_dong"]} nhưng hành động chưa xong trước ngày đó: {"; ".join(muon)}', vt)
                if not hd and not cap_nhat:
                    self.add('KB10', 'vấn đề đóng phải có ít nhất một hành động đã hoàn thành', vt)
        if not cap_nhat and not (e.get('ma_rui_ro') or e.get('ma_cr') or e.get('lien_ket') or re.search(r'\b\d+\.\d+(\.\d+)*\b|\bM\d\b', e.get('mo_ta', ''))):
            self.add('KB12', 'vấn đề cần liên kết: mã gói hoặc mốc trong mo_ta, ma_rui_ro, ma_cr hoặc lien_ket', vt)

    def k_chi_phi(self, e, vt):
        self.ngay_trong_sprint(e.get('ngay'), vt, 'ngay', chi_lam_viec=False)
        if e.get('khoan_muc') not in self.ctx.chi_phi_khac:
            self.add('KB08', f'khoan_muc "{e.get("khoan_muc")}" không có trong chi_phi_khac của don_gia.json ({", ".join(sorted(self.ctx.chi_phi_khac))})', vt)
        try:
            if float(e.get('so_tien')) <= 0:
                raise ValueError
        except (TypeError, ValueError):
            self.add('KB08', 'so_tien phải là số dương', vt)
        if e.get('loai_chi', 'da_chi') not in ('da_chi', 'cam_ket'):
            self.add('KB08', 'loai_chi chỉ nhận da_chi hoặc cam_ket', vt)
        self.lien_ket(e, vt)

    def k_nghiem_thu(self, e, vt):
        m = re.match(r'^(R\d+)\b', e.get('tieu_chi', ''))
        if not m or m.group(1) not in self.ctx.rfp:
            self.add('KB09', 'tieu_chi phải bắt đầu bằng mã yêu cầu RFP có trong du_lieu/rfp_yeu_cau.json (ví dụ "R06 Tìm kiếm ...")', vt)
        if str(e.get('hang_muc', '')) not in {str(x['stt']) for x in self.ctx.hsmt.get('mau_01a', [])}:
            self.add('KB09', f'hang_muc "{e.get("hang_muc")}" không phải số thứ tự hạng mục Mẫu 01A', vt)
        if e.get('ket_qua') not in ('Đạt', 'Không đạt'):
            self.add('KB09', 'ket_qua chỉ nhận Đạt hoặc Không đạt', vt)
        if e.get('ma') and not re.match(r'^NT\d+$', e['ma']):
            self.add('KB09', f'mã nghiệm thu "{e["ma"]}" phải dạng NTxx', vt)
        self.ngay_trong_sprint(e.get('ngay'), vt, 'ngay')
        if not e.get('nguoi_xac_nhan'):
            self.add('KB01', 'thiếu nguoi_xac_nhan', vt)

    def k_moc(self, e, vt):
        m = e.get('ma_moc', '')
        if m not in self.ctx.moc:
            self.add('KB07', f'mốc {m} không có trong du_lieu/lich.json', vt); return
        if m in self.tt['moc']:
            self.add('KB07', f'mốc {m} đã ghi đạt trong moc_thuc_te.csv', vt)
        self.ngay_trong_sprint(e.get('ngay_dat'), vt, 'ngay_dat', chi_lam_viec=False)
        cut = self.ctx.lich['cut_over']
        la_cut = self.ctx.moc[m]['ngay'] == cut or 'cut over' in self.ctx.moc[m]['ten'].lower()
        if la_cut and str(e.get('ngay_dat', '')) > cut and not self.co_cr_phu_luc():
            self.add('KB13', f'mốc cut over {m} đạt ngày {e.get("ngay_dat")} sau ngày cut over {cut} mà chưa có yêu cầu thay đổi đã phê duyệt kèm phụ lục hợp đồng', vt)
        if not e.get('ghi_chu'):
            self.add('KB01', 'mốc đạt phải ghi ghi_chu (biên bản, căn cứ)', vt)

    def co_cr_phu_luc(self):
        return any(c.get('phu_luc_hop_dong') and c.get('trang_thai') in ('Đã phê duyệt', 'Đã thực hiện', 'Đã đóng') for c in self.ctx.so_td.get('yeu_cau', []))

    def k_retro(self, e, vt):
        if self.sp == C.KY_KET_THUC:
            self.add('KB02', 'họp cải tiến ghi theo sprint (mã R-Sx-nn), kỳ KT ghi bài học ở bước qlda-bai-hoc', vt); return
        y = e.get('y') or []
        if not y:
            self.add('KB01', 'họp cải tiến cần danh sách y, mỗi ý có loai (tốt, cần cải thiện, hành động) và noi_dung', vt)
        loai = {x.get('loai') for x in y}
        for i, x in enumerate(y, 1):
            if x.get('loai') not in ('tốt', 'cần cải thiện', 'hành động') or not x.get('noi_dung'):
                self.add('KB01', f'ý {i}: loai phải là tốt, cần cải thiện hoặc hành động, có noi_dung', vt)
            for k in x.get('lien_ket') or []:
                self.kiem_ma_lien_ket(str(k), f'{vt}, ý {i}')
            if not (x.get('lien_ket') or e.get('lien_ket')):
                self.add('KB12', f'ý {i} chưa có lien_ket (mã gói, rủi ro, vấn đề, lỗi, sprint)', vt, 'canh_bao')
        if y and not {'tốt', 'cần cải thiện'} <= loai:
            self.add('KB01', 'họp cải tiến cần ít nhất một ý tốt và một ý cần cải thiện', vt, 'canh_bao')

    def k_cr(self, e, vt):
        for k in ('ma_cr', 'tieu_de', 'mo_ta', 'nguon'):
            if not e.get(k):
                self.add('KB01', f'yêu cầu thay đổi thiếu {k}', vt)
        self.ngay_trong_sprint(e.get('ngay'), vt, 'ngay', chi_lam_viec=False)
        for i, g in enumerate(e.get('goi_moi') or [], 1):
            for k in ('ten', 'md', 'loai', 'cha'):
                if not g.get(k):
                    self.add('KB01', f'gói mới {i} thiếu {k}', vt)
        if not (e.get('goi_moi') or e.get('goi_thay_doi')):
            self.add('KB12', 'yêu cầu thay đổi chưa nêu goi_moi hoặc goi_thay_doi, agent Đánh giá thay đổi sẽ phải tự xác định', vt, 'canh_bao')
        so_ = self.ctx.so_td.get('yeu_cau', [])
        da_co = next((c for c in so_ if c.get('ma') == e.get('ma_cr')), None)
        # sinh lại sprint (--lam-lai) sau khi yeu_cau_thay_doi.py danh_gia đã ghi CR từ chính biến cố này: cùng tiêu đề và ngày đề xuất
        cung_bien_co = bool(da_co) and da_co.get('tieu_de') == e.get('tieu_de') and da_co.get('ngay_de_xuat') == e.get('ngay')
        cr_kb = [x.get('ma_cr') for x in self.kb.get('bien_co', []) if x.get('loai') == 'cr' and x.get('ma_cr') not in {c.get('ma') for c in so_}]
        du_kien = f'CR{len(so_) + cr_kb.index(e.get("ma_cr")) + 1:02d}' if e.get('ma_cr') in cr_kb else ''
        if da_co and not cung_bien_co:
            self.add('KB11', f'mã {e["ma_cr"]} đã có trong du_lieu/thay_doi.json với tiêu đề hoặc ngày khác, biến cố cr chỉ dùng cho yêu cầu mới', vt)
        elif du_kien and e.get('ma_cr') != du_kien:
            self.add('KB11', f'yeu_cau_thay_doi.py danh_gia sẽ cấp mã {du_kien} (theo số CR trong sổ), không phải {e["ma_cr"]}; '
                     'dùng đúng mã để liên kết vấn đề, rủi ro không lệch', vt, 'canh_bao')

    # ------------------------------------------------------------ chạy
    def chay(self):
        kb = self.kb
        if kb.get('sprint') != self.sp:
            self.add('KB02', f'kịch bản ghi sprint "{kb.get("sprint")}", lệnh chạy cho {self.sp}', 'kich_ban')
        if self.sp not in self.ctx.sprint:
            self.add('KB02', f'sprint {self.sp} không có trong du_lieu/lich.json', 'kich_ban'); return self.F
        ds = kb.get('bien_co')
        if not isinstance(ds, list):
            self.add('KB01', 'thiếu danh sách bien_co', 'kich_ban'); return self.F
        for i, e in enumerate(ds, 1):
            vt = f'bien_co[{i}] {e.get("loai", "?")}'
            if e.get('loai') not in LOAI:
                self.add('KB02', f'loại "{e.get("loai")}" không thuộc {", ".join(LOAI)}', vt); continue
            if not str(e.get('ly_do', '')).strip():
                self.add('KB01', 'mỗi biến cố phải có ly_do', vt)
            getattr(self, 'k_' + e['loai'])(e, vt)
        so_rr = self.tt['rr_xay_ra'] | {e.get('ma_rui_ro') for e in ds if e.get('loai') == 'rui_ro' and e.get('trang_thai', 'Đã xảy ra') == 'Đã xảy ra'}
        if len(so_rr) > self.cfg['rui_ro_xay_ra_toi_da']:
            self.add('KB14', f'{len(so_rr)} rủi ro đã xảy ra từ đầu dự án ({", ".join(sorted(so_rr))}), vượt mức nhóm quyết định '
                     f'{self.cfg["rui_ro_xay_ra_toi_thieu"]} đến {self.cfg["rui_ro_xay_ra_toi_da"]}', 'kich_ban', 'canh_bao')
        return self.F


def tach_ma(v):
    return [x for x in re.split(r'[,;\s]+', v or '') if x]


def kiem_tra(ctx, ma_sp, kb, trang_thai):
    return KiemTra(ctx, ma_sp, kb, trang_thai).chay()
