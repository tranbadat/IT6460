"""Phần dùng chung của skill qlda-mo-phong: đường dẫn, đọc và ghi CSV dữ liệu thực tế, ngữ cảnh kế hoạch hiện hành.

Dùng bởi mo_phong_sprint.py, kich_ban.py, mo_phong_lich.py, kiem_tra_mo_phong.py, chu_trinh.py.
Định dạng các tệp dữ liệu thực tế: qlda-bao-cao-tien-do/references/nhap_lieu.md.
"""
import csv
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

D = dt.date.fromisoformat
SKILL = 'qlda-mo-phong'
THU_MUC_TT = 'dau_vao/thuc_te'
THU_MUC_LV = 'lam_viec/mo_phong'
TEP_MO_PHONG = 'du_lieu/mo_phong.json'
CAU_HINH = os.path.join(HERE, '..', 'references', 'cau_hinh.json')
GHI_CHU_MO_PHONG = ('Số liệu mô phỏng: dữ liệu thực tế trong dau_vao/thuc_te/ do script qlda-mo-phong/scripts/mo_phong_sprint.py sinh '
                    'từ kịch bản biến cố từng sprint (lam_viec/mo_phong/kich_ban_S<n>.json) theo kế hoạch đã duyệt hiện hành, '
                    'không phải số liệu đo được của dự án thật.')

# Cột của từng tệp CSV, cùng thứ tự với mẫu trong dau_vao/thuc_te/ (nhap_lieu.md).
COT = {
    'nhat_ky_cong_viec': ['ngay', 'thanh_vien', 'ma_goi', 'md', 'ghi_chu'],
    'hoan_thanh': ['ngay_cap_nhat', 'ma_goi', 'phan_tram', 'ghi_chu'],
    'moc_thuc_te': ['ma_moc', 'ngay_dat', 'ghi_chu'],
    'loi': ['ma', 'ngay_phat_hien', 'muc_do', 'ma_goi', 'trang_thai', 'ngay_dong', 'mo_ta'],
    'theo_doi_rui_ro': ['ngay', 'ma_rui_ro', 'trang_thai', 'hanh_dong', 'md_tac_dong', 'chi_phi_tac_dong', 'ma_cr', 'ghi_chu'],
    'so_van_de': ['ma', 'ngay_ghi_nhan', 'nguoi_bao', 'mo_ta', 'loai', 'uu_tien', 'ma_rui_ro', 'ma_cr', 'nguoi_phu_trach', 'han',
                  'trang_thai', 'ket_qua', 'nguoi_dong', 'ngay_dong'],
    'hanh_dong': ['ma', 'ma_van_de', 'viec', 'nguoi', 'han', 'trang_thai', 'bang_chung', 'ngay_xong'],
    'chi_phi_thuc_te': ['ngay', 'khoan_muc', 'so_tien', 'ghi_chu', 'loai'],
    'nghiem_thu': ['ma', 'tieu_chi', 'hang_muc', 'ket_qua', 'ngay', 'nguoi_xac_nhan', 'ghi_chu'],
}
TEP_RETRO = f'{THU_MUC_TT}/retro.md'
KY_KET_THUC = 'KT'  # kỳ giai đoạn Kết thúc sau cut over, cùng mã với phan_bo của lap_lich.py và kỳ KT của tinh_tien_do.py
MUC_LOI = ('Nghiêm trọng', 'Cao', 'Trung bình', 'Thấp')


def tep_csv(ten):
    return f'{THU_MUC_TT}/{ten}.csv'


def tat_ca_tep():
    """Mọi tệp dữ liệu thực tế do mô phỏng ghi (đường dẫn tương đối)."""
    return [tep_csv(t) for t in COT] + [TEP_RETRO]


def doc_bang(ten):
    """Đọc một tệp CSV thành danh sách dict theo cột chuẩn (thiếu cột thì để trống)."""
    return [{c: r.get(c, '') for c in cot_tep(ten)} for r in loi.doc_csv(tep_csv(ten))]


def cot_tep(ten):
    """Cột của tệp hiện có (giữ cột nhóm thêm), không có tệp thì theo mẫu chuẩn."""
    p = loi.duong_dan(tep_csv(ten))
    if os.path.exists(p):
        with open(p, encoding='utf-8-sig') as f:
            dau = next(csv.reader(f), None)
        if dau:
            return [c.strip() for c in dau if c.strip()]
    return list(COT[ten])


def ghi_bang(ten, rows):
    """Ghi lại toàn bộ tệp CSV (UTF-8, xuống dòng LF, ô có dấu phẩy đặt trong ngoặc kép)."""
    cot = cot_tep(ten)
    p = loi.duong_dan(tep_csv(ten))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(cot)
        for r in rows:
            w.writerow([so_csv(r.get(c, '')) for c in cot])


def so_csv(v):
    """Số theo quy ước nhập liệu: dấu chấm thập phân, không phân cách hàng nghìn, bỏ số 0 thừa."""
    if isinstance(v, bool) or v is None:
        return '' if v is None else str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f'{v:.4f}'.rstrip('0').rstrip('.')
    return str(v)


def cau_hinh():
    return loi.doc_json(CAU_HINH)


HD_HIEN_TAI = {}  # huy động bổ sung của sprint đang sinh, {(thành viên, sprint): MD}, mo_phong_sprint.py gán trước khi tạo ngữ cảnh


def huy_dong_them():
    """Huy động bổ sung thực tế {(thành viên, sprint): MD}: biến cố huy_dong trong kịch bản đã lưu ở du_lieu/mo_phong.json
    và của sprint đang sinh (HD_HIEN_TAI). Từ 1.0.5."""
    out = {}
    for x in loi.doc_json('du_lieu/mo_phong.json', {}).get('sprint', []):
        for e in (x.get('kich_ban_noi_dung') or {}).get('bien_co', []):
            if e.get('loai') == 'huy_dong' and x.get('ma') not in {k[1] for k in HD_HIEN_TAI}:
                k = (e.get('thanh_vien'), x.get('ma'))
                out[k] = out.get(k, 0.0) + float(e.get('so_md') or 0)
    for k, m in HD_HIEN_TAI.items():
        out[k] = out.get(k, 0.0) + m
    return out


class NguCanh:
    """Kế hoạch hiện hành và danh mục dùng để sinh và kiểm tra dữ liệu mô phỏng."""

    def __init__(self, lich=None):
        self.da = loi.du_an()
        self.lich = lich or loi.doc_json('du_lieu/lich.json')
        self.wbs = loi.doc_json('du_lieu/wbs.json')
        self.tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']
        self.tv = {t['id']: t for t in self.tvs}
        self.dg = loi.doc_json('dau_vao/don_gia.json')
        self.rr = loi.doc_json('du_lieu/rui_ro.json', {'danh_sach': []})
        self.ma_rr = {r['ma']: r for r in self.rr['danh_sach']}
        self.so_td = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})
        self.ma_cr = {c['ma'] for c in self.so_td.get('yeu_cau', [])}
        self.hsmt = loi.doc_json('du_lieu/hsmt.json', {'mau_01a': []})
        self.rfp = {y['ma'] for y in loi.doc_json('du_lieu/rfp_yeu_cau.json', {'yeu_cau': []})['yeu_cau']}
        self.days = [d for d in loi.ngay_lam_viec(self.da)]
        self.sprint = {s['ma']: s for s in self.lich['sprint']}
        kt = self._ky_ket_thuc()
        if kt:  # kỳ KT: giai đoạn Kết thúc sau cut over (loi.giai_doan_du_an), gói Kết thúc của lịch xếp trong kỳ này
            self.days += [d for d in loi.ngay_lam_viec_sau(self.da, self.days[-1], kt['so_ngay'])]  # ngày làm việc tới ngày đóng dự án
            self.sprint[KY_KET_THUC] = kt
        self.goi = {g['ma']: g for g in self.lich['goi'] if g.get('la')}
        self.moc = {m['ma']: m for m in self.lich['moc']}
        self.quy, md_kt = {}, {}
        for x in self.lich.get('phan_bo', []):
            k = (x['thanh_vien'], x['sprint'])
            self.quy[k] = self.quy.get(k, 0.0) + float(x.get('quy') if x.get('quy') is not None else x.get('md') or 0)
            if x['sprint'] == KY_KET_THUC:
                md_kt[x['thanh_vien']] = md_kt.get(x['thanh_vien'], 0.0) + float(x.get('md') or 0)
        self.quy_ke_hoach = dict(self.quy)
        for k, m in huy_dong_them().items():  # huy động bổ sung thực tế theo kịch bản (từ 1.0.5)
            self.quy[k] = self.quy.get(k, 0.0) + m
        for p, m in md_kt.items():  # lịch ghi quỹ kỳ KT bằng 0 (L28 của lap_lich.py): người có việc Kết thúc được làm đủ ngày của kỳ
            if m > 0 and kt:
                self.quy[(p, KY_KET_THUC)] = max(self.quy.get((p, KY_KET_THUC), 0.0), kt['so_ngay'] * float(self.tv.get(p, {}).get('ty_le', 1.0)))
        self.chi_phi_khac = {c['ma'] for c in self.dg.get('chi_phi_khac', [])} | {c['ten'] for c in self.dg.get('chi_phi_khac', [])}
        md_mm = float(self.dg.get('md_moi_mm', 20))
        self.don_gia_md = {k: float(v['don_gia_tron_goi_thang']) / md_mm for k, v in self.dg.get('loai_cong_viec', {}).items()}

    def _ky_ket_thuc(self):
        """Kỳ KT {ma, tu, den, so_ngay}: giai đoạn Kết thúc sau cut over theo lich.json (giai_doan mã ket_thuc, ngay_dong_du_an),
        lịch cũ không có thì theo loi.giai_doan_du_an khi có gói xếp sau cut over; không có giai đoạn này thì None."""
        cut = self.days[-1].isoformat() if self.days else ''
        k = next((x for x in self.lich.get('giai_doan') or [] if x.get('ma') == 'ket_thuc'), None)
        if not k and hasattr(loi, 'giai_doan_du_an') and any(g.get('la') and g['bat_dau'] > cut for g in self.lich['goi']):
            k = loi.giai_doan_du_an(self.da)[0]['ket_thuc']
        if not k:
            return None
        den = self.lich.get('ngay_dong_du_an') or k['den']
        ds = [d for d in loi.ngay_lam_viec_sau(self.da, self.days[-1], 400) if d.isoformat() <= den]
        if not ds:
            return None
        return {'ma': KY_KET_THUC, 'tu': ds[0].isoformat(), 'den': ds[-1].isoformat(), 'so_ngay': len(ds)}

    def ngay_sprint(self, ma):
        s = self.sprint[ma]
        return [d for d in self.days if D(s['tu']) <= d <= D(s['den'])]

    def sprint_cua_ngay(self, d):
        d = d if isinstance(d, dt.date) else D(d)
        return next((s['ma'] for s in self.sprint.values() if D(s['tu']) <= d <= D(s['den'])), None)

    def la_cua(self, ma):
        """Các gói lá thuộc mã (chính nó nếu là lá)."""
        return [m for m in self.goi if m == ma or m.startswith(ma + '.')]

    def cong_ngay_lam_viec(self, d, n):
        """Ngày làm việc thứ n sau ngày d (n = 0 là chính d hoặc ngày làm việc kế tiếp)."""
        d = d if isinstance(d, dt.date) else D(d)
        sau = [x for x in self.days if x >= d]
        if not sau:
            return d + dt.timedelta(days=n)
        return sau[min(n, len(sau) - 1)] if n < len(sau) else sau[-1] + dt.timedelta(days=n - len(sau) + 1)

    def la_ben_ngoai(self, v):
        """Người ngoài nhóm (Chủ đầu tư, đơn vị khác) ghi bằng tên đơn vị, không phải mã thành viên."""
        return bool(v) and v not in self.tv and not v.isidentifier()

    def ma_can_cu_moc(self, m):
        """Mã gói WBS căn cứ của mốc (can_cu dạng '7.2, 1.3.2'), mốc ngày cố định thì rỗng."""
        out = []
        for x in str(m.get('can_cu', '')).replace(';', ',').split(','):
            x = x.strip()
            if x and x[0].isdigit():
                out += self.la_cua(x)
        return out


def tiep_ma(ds, tien_to, do_dai=2):
    """Mã kế tiếp dạng VD01, HD01, L01, NT01 theo các mã đã có."""
    so = [int(x[len(tien_to):]) for x in ds if str(x).startswith(tien_to) and str(x)[len(tien_to):].isdigit()]
    return f'{tien_to}{(max(so) + 1 if so else 1):0{do_dai}d}'
