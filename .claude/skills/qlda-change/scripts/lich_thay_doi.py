"""Đưa gói mới và gói thay đổi của một yêu cầu thay đổi (CR) vào lịch thật, do yeu_cau_thay_doi.py import (không chạy trực tiếp).

Dùng lap_lich.py của qlda-master-schedule ở chế độ lập lại từ ngày CR (moc_nhap lap_lai_tu, scripts/lap_lai.py) trên bản sao dữ liệu
trong thư mục tạm (biến môi trường QLDA_GOC), không ghi đè du_lieu/lich.json:
- Gói đã xong trước ngày CR giữ ngày thực tế hoặc ngày kế hoạch của du_lieu/lich.json, gói đang làm giữ ngày bắt đầu và chỉ xếp phần MD
  còn lại, phần còn lại và gói mới xếp từ ngày CR có ràng buộc nguồn lực.
- Gói mới và phần làm lại của gói đã xong không bắt đầu trước ngày bắt đầu phần thay đổi (cam kết tạm CR_BAT_DAU): ngay_bat_dau của
  phiếu, thiếu thì hạn quyết định của mức lớn tính từ ngày CR (công việc ngoài phạm vi chỉ làm sau khi có quyết định).
- Gói thay đổi tăng MD và thêm phụ thuộc them_phu_thuoc, gói có khoảng ngày cố định được thêm người hỗ trợ khi cần
  (nhan_su_thay_doi.de_xuat_ho_tro_thay_doi). Gói mới thêm vào WBS, giao việc theo nhan_su_thay_doi.de_xuat_giao.
- Thử lùi cut over k ngày làm việc: ràng buộc không sớm hơn, khoảng kiểm thử chấp nhận và mốc ngày cố định từ ngày CR trở đi dời k ngày.
  Bố cục sprint giữ theo du_an.json, lap_lich.py dùng ngày làm việc mở rộng sau cut over.
- k là số nhỏ nhất làm lịch khả thi: kết thúc không quá cut over mới, gói ghim bắt đầu đúng ngày ghim, gói kiểm thử chấp nhận trong
  khoảng. Lặp k += phần vượt đến khi không còn vượt. Gói kiểm thử chấp nhận tăng MD vượt số ngày của khoảng uat thì khoảng kéo dài
  thêm e ngày (uat_keo_dai), các ngày sau khoảng dời k + e. Cut over lùi k + e ngày.
- Số ngày lùi theo phụ thuộc: cùng cách lặp với đường găng có ràng buộc ngày, không giới hạn nguồn lực. Phần chênh là do nguồn lực.
- Số ngày chậm: dự trữ đến cut over của bản sao không có CR trừ dự trữ của bản sao có CR, cùng ngày CR và k = 0. Tiêu hao dự trữ là
  phần chậm nằm trong dự trữ, phần còn lại làm lùi cut over.
- Khả năng theo quỹ: MD còn lại (gồm CR) chia tổng tốc độ còn lại của nhóm, để so với số ngày lùi.
- Ngày lập lại (ngay_lap_lai): ngày CR, hoặc ngày làm việc kế tiếp khi đã có số liệu thực tế của chính ngày CR (nhật ký công việc,
  hoàn thành, ví dụ CR nêu ở demo cuối sprint). lap_lai.py chỉ lấy số liệu trước ngày lập lại, nên lập lại từ ngày CR sẽ bỏ số liệu
  của ngày đó. ap_dung dùng cùng ngày này cho lap_lai_tu của moc_nhap.json.
Lỗi dừng TD18 (không dựng hoặc không lập được lịch mô phỏng), TD21 (phương án thêm nhân sự không hợp lệ).
"""
import datetime as dt
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-master-schedule', 'scripts'))
import loi  # noqa: E402
import lap_lai  # noqa: E402
import nhan_su_thay_doi as ns  # noqa: E402

doc_them_nguoi = ns.doc_them_nguoi
LAP_LICH = os.path.join(loi.THU_MUC_SKILLS, 'qlda-master-schedule', 'scripts', 'lap_lich.py')
TEP_MOC = 'lam_viec/lich/moc_nhap.json'
TEP_NHAP = 'lam_viec/lich/lich_du_thao.json'
TEP_LICH_GOC = 'lam_viec/lich/lich_goc_cr.json'
MA_CK_BAT_DAU = 'CR_BAT_DAU'
SO_VONG_TOI_DA = 15
GIAI_DOAN_KET_THUC = 'ket_thuc'  # gói giai đoạn Kết thúc của lap_lich.py bắt đầu sau cut over, không làm lùi cut over
HE_SO_MO_RONG = 3  # số ngày làm việc mở rộng sau cut over, bằng cách lap_lich.py mở rộng (N x 3)


def thoat(ma, msg):
    loi.thoat_loi(f'{ma} {msg}')


# ---------------------------------------------------------------- ngày
def ngay_mo_rong(da):
    """(ngày làm việc đến cut over, ngày làm việc mở rộng) như lap_lich.py."""
    days = loi.ngay_lam_viec(da)
    nghi = {dt.date.fromisoformat(x) for x in da.get('ngay_nghi', [])}
    ext, d = list(days), days[-1]
    while len(ext) < len(days) * HE_SO_MO_RONG:
        d += dt.timedelta(days=1)
        if d.weekday() < 5 and d not in nghi:
            ext.append(d)
    return days, ext


def chi_so_tu(ext, ngay):
    d = dt.date.fromisoformat(str(ngay)[:10])
    return next((i for i, x in enumerate(ext) if x >= d), len(ext) - 1)


def chi_so_den(ext, ngay):
    d = dt.date.fromisoformat(str(ngay)[:10])
    return max((i for i, x in enumerate(ext) if x <= d), default=0)


def dich(ext, ngay, k):
    """Ngày làm việc thứ k sau ngày (ISO), k = 0 giữ nguyên."""
    return ngay if not k else ext[min(len(ext) - 1, chi_so_tu(ext, ngay) + k)].isoformat()


def dich_theo_uat(ext, ngay, k, e, uat_den):
    """Ngày gắn cut over dời k ngày, ngày sau khoảng uat gốc dời thêm e ngày kéo dài của khoảng."""
    return dich(ext, ngay, k + e if uat_den and ngay > uat_den else k)


def so_ngay_giua(ext, a, b):
    return loi.ngay_lam_viec_giua(ext, a, b) if a and b else 0


def ngay_lap_lai(ngay_cr, ext):
    """Ngày lập lại lịch của CR: ngày làm việc sau ngày CR khi đã có số liệu thực tế ghi đúng ngày CR, còn lại là ngày CR."""
    co = any(r.get('ngay') == ngay_cr and _so(r.get('md')) > 0 for r in loi.doc_csv('dau_vao/thuc_te/nhat_ky_cong_viec.csv')) or \
        any(r.get('ngay_cap_nhat') == ngay_cr for r in loi.doc_csv('dau_vao/thuc_te/hoan_thanh.csv'))
    return dich(ext, ngay_cr, 1) if co else ngay_cr


def _so(v):
    try:
        return float(v or 0)
    except ValueError:
        return 0.0


def trong_gang(g):
    """Gói lá tính vào ngày kết thúc trước cut over: không dàn trải, không thuộc giai đoạn Kết thúc (làm sau cut over)."""
    return g.get('la') and not g.get('dan_trai') and g.get('giai_doan') != GIAI_DOAN_KET_THUC


# ---------------------------------------------------------------- bản sao dữ liệu
def dung_wbs(wbs, cr):
    """WBS có mục mới, gói mới, gói thay đổi cộng MD và phụ thuộc thêm; MD mục cha tính lại."""
    thay = {x['ma']: x for x in cr.get('goi_thay_doi', [])}
    goi = []
    for g in wbs['goi']:
        x = thay.get(g['ma'])
        goi.append(dict(g, md=float(g['md']) + float(x.get('md_tang', 0)), phu_thuoc=list(dict.fromkeys(g.get('phu_thuoc', []) + x.get('them_phu_thuoc', []))))
                   if x else dict(g))
    for m in cr.get('muc_moi', []):
        goi.append({'ma': m['ma'], 'ten': m['ten'], 'muc': m['ma'].count('.') + 1, 'la': False, 'cha': m['ma'].rsplit('.', 1)[0] if '.' in m['ma'] else ''})
    for g in cr.get('goi_moi', []):
        g2 = {k: g[k] for k in ('ma', 'ten', 'loai', 'cha', 'thoi_luong_toi_thieu') if k in g}
        goi.append(dict(g2, md=float(g['md']), phu_thuoc=list(g.get('phu_thuoc', [])), muc=g['ma'].count('.') + 1, la=True))
    md_la = {g['ma']: float(g['md']) for g in goi if g.get('la')}
    goi = [g if g.get('la') else dict(g, md=round(sum(v for m, v in md_la.items() if m.startswith(g['ma'] + '.')), 2)) for g in goi]
    return dict(wbs, goi=goi, tong_md=round(sum(md_la.values()), 2))


def dung_phan_cong(pc, giao_moi, giao_them):
    gv = [dict(x, **{k: v for k, v in giao_them.get(x['ma'], {}).items() if k in ('R', 'ho_tro')}) for x in pc['giao_viec']]
    gv += [{'ma': x['ma'], 'R': x['R'], 'ho_tro': x['ho_tro'], 'dan_trai': False, 'tu_sprint': None, 'den_sprint': None, 'ly_do': x['ly_do']} for x in giao_moi]
    return dict(pc, giao_viec=gv)


def dung_moc(moc_nhap, ngay_cr, ext, k, e, uat_den, goi_sau_qd):
    """moc_nhap của bản sao: lập lại từ ngày CR, dời ràng buộc gắn cut over k (sau khoảng uat gốc k + e) ngày, gói sau quyết định."""
    ksh = {m: dich_theo_uat(ext, d, k, e, uat_den) if d >= ngay_cr else d for m, d in (moc_nhap.get('khong_som_hon') or {}).items()}
    moc = [dict(m, ngay=dich_theo_uat(ext, m['ngay'], k, e, uat_den)) if m.get('ngay') and m['ngay'] >= ngay_cr else dict(m)
           for m in moc_nhap.get('moc', [])]
    bn = dict(moc_nhap.get('dau_vao_ben_ngoai') or {}, **{MA_CK_BAT_DAU: goi_sau_qd})
    return dict(moc_nhap, khong_som_hon=ksh, moc=moc, dau_vao_ben_ngoai=bn, lap_lai_tu={'ngay': ngay_cr, 'lich_goc': TEP_LICH_GOC})


def dung_du_an(da, ngay_cr, ngay_bd, ext, k, e=0):
    """du_an của bản sao: khoảng uat dời k ngày và kéo dài thêm e ngày, cam kết tạm ngày bắt đầu phần thay đổi."""
    uat = dict(da.get('uat') or {})
    if uat.get('tu') and uat['tu'] >= ngay_cr:
        uat = {**uat, 'tu': dich(ext, uat['tu'], k), 'den': dich(ext, uat['den'], k + e)}
    ck = [c for c in da.get('cam_ket_chu_dau_tu', []) if c.get('ma') != MA_CK_BAT_DAU]
    ck.append({'ma': MA_CK_BAT_DAU, 'noi_dung': 'Ngày bắt đầu phần thay đổi (bản sao mô phỏng)', 'han': ngay_bd})
    return dict(da, uat=uat, cam_ket_chu_dau_tu=ck)


# ---------------------------------------------------------------- chạy lap_lich.py
def chay_lap_lich(du_lieu, thu_muc):
    """Ghi bản sao vào thu_muc, chạy lap_lich.py với QLDA_GOC = thu_muc, trả bản lịch dự thảo."""
    if os.path.isdir(thu_muc):
        shutil.rmtree(thu_muc)
    for p, obj in du_lieu.items():
        dst = os.path.join(thu_muc, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    env = dict(os.environ, QLDA_GOC=thu_muc, PYTHONUTF8='1')
    r = subprocess.run([sys.executable, LAP_LICH, TEP_MOC], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=thu_muc, env=env)
    p = os.path.join(thu_muc, TEP_NHAP)
    if not os.path.exists(p):
        thoat('TD18', 'Không lập được lịch mô phỏng bằng lap_lich.py: ' + (r.stdout + r.stderr).strip()[-1500:])
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def do_vuot(nhap, ext, n, k):
    """Số ngày lịch vượt khi cut over lùi k ngày: kết thúc sau cut over mới, gói ghim bắt đầu muộn, kiểm thử chấp nhận quá khoảng."""
    la = [g for g in nhap['goi'] if trong_gang(g) and 'chi_so_ket_thuc' in g]
    v = [max([g['chi_so_ket_thuc'] for g in la] or [0]) - (n - 1 + k)]
    for g in la:
        for rb in g.get('rang_buoc') or []:
            if rb.get('loai') == 'khong_som_hon':
                v.append(g['chi_so_bat_dau'] - chi_so_tu(ext, rb['ngay']))
            elif rb.get('loai') == 'uat':
                v.append(g['chi_so_ket_thuc'] - chi_so_den(ext, rb['den']))
    return max(0, max(v))


def vuot_phu_thuoc(nhap, ext, n, k_nhap, k, i0):
    """Như do_vuot nhưng theo đường găng có ràng buộc ngày, không giới hạn nguồn lực, với cut over lùi k ngày.
    Gói đã xong giữ ngày, gói đang làm xếp phần còn lại từ ngày lập lại i0 với thời lượng của lịch mô phỏng."""
    la = {g['ma']: g for g in nhap['goi'] if trong_gang(g) and 'thoi_luong' in g}
    lech = k - k_nhap
    ef, v = {}, []

    def tinh(m):
        if m in ef:
            return ef[m]
        g = la[m]
        tt = g.get('trang_thai_lap_lai')
        if tt == 'da_xong':
            ef[m] = g['chi_so_ket_thuc']
            return ef[m]
        lb = [i0]
        for rb in g.get('rang_buoc') or []:
            if rb.get('loai') == 'khong_som_hon':
                lb.append(chi_so_tu(ext, rb['ngay']) + lech)
            elif rb.get('loai') == 'uat':
                lb.append(chi_so_tu(ext, rb['tu']) + lech)
            elif rb.get('loai') == 'cam_ket' and rb.get('han'):
                lb.append(chi_so_tu(ext, rb['han']))
        es = max(lb + [tinh(p) + 1 for p in g.get('phu_thuoc', []) if p in la])
        dur = g['chi_so_ket_thuc'] - max(g['chi_so_bat_dau'], i0) + 1 if tt in ('dang_lam', 'lam_lai') else int(g['thoi_luong'])
        ef[m] = es + max(1, dur) - 1
        for rb in g.get('rang_buoc') or []:
            if rb.get('loai') == 'khong_som_hon':
                v.append(es - (chi_so_tu(ext, rb['ngay']) + lech))
            elif rb.get('loai') == 'uat':
                v.append(ef[m] - (chi_so_den(ext, rb['den']) + lech))
        return ef[m]
    for m in la:
        tinh(m)
    v.append(max(ef.values() or [0]) - (n - 1 + k))
    return max(0, max(v))


def uat_them(nhap):
    """Số ngày khoảng kiểm thử chấp nhận phải kéo dài khi MD của gói kiểm thử chấp nhận vượt số ngày của khoảng."""
    return max([g.get('thoi_luong_theo_md', 0) - rb['so_ngay'] for g in nhap['goi'] for rb in g.get('rang_buoc') or [] if rb.get('loai') == 'uat'] + [0])


def lap_k(chay, ext, n):
    """k nhỏ nhất (lặp k += phần vượt) và số ngày kéo dài khoảng uat e. Cut over lùi k + e ngày. Trả (k, e, bản lịch dự thảo, số vòng)."""
    k = e = 0
    for vong in range(1, SO_VONG_TOI_DA + 1):
        nhap = chay(k, e)
        if uat_them(nhap) > e:
            e = uat_them(nhap)
            continue
        v = do_vuot(nhap, ext, n, k + e)
        if not v:
            return k, e, nhap, vong
        k += v
    thoat('TD18', f'Lịch mô phỏng không hội tụ sau {SO_VONG_TOI_DA} vòng (cut over lùi hơn {k} ngày), kiểm tra phụ thuộc của gói mới')


def uat_moi(nhap):
    rb = next((rb for g in nhap['goi'] for rb in g.get('rang_buoc') or [] if rb.get('loai') == 'uat'), None)
    return {'tu': rb['tu'], 'den': rb['den']} if rb else {}


def k_theo_phu_thuoc(nhap, ext, n, k_nhap, i0):
    k = 0
    for _ in range(SO_VONG_TOI_DA * 4):
        v = vuot_phu_thuoc(nhap, ext, n, k_nhap, k, i0)
        if not v:
            return k
        k += v
    return k


def moc_thay_doi(nhap, lich_goc, ext, ngay_cr, k, cut_goc):
    """Mốc từ ngày CR trở đi: ngày cũ, ngày mới, số ngày dời, vượt hạn, hạn đề xuất cho phụ lục. Mốc ngày cố định lấy chính ngày đó làm hạn.
    Hạn đề xuất của mốc vượt hạn: mốc gắn cut over (hạn từ ngày cut over) dời theo số ngày cut over lùi, mốc giữa kỳ lấy ngày dự kiến mới."""
    goc = {m['ma']: m for m in lich_goc.get('moc', [])}
    out = []
    for m in nhap.get('moc', []):
        g = goc.get(m['ma'])
        if not g or g['ngay'] < ngay_cr:
            continue
        han = g.get('han') or (g['ngay'] if g.get('can_cu') == 'Ngày cố định' else '')
        doi, vuot = so_ngay_giua(ext, g['ngay'], m['ngay']), max(0, so_ngay_giua(ext, han, m['ngay'])) if han else 0
        gan = bool(han) and han >= cut_goc
        han_dx = (max(dich(ext, han, k), m['ngay']) if gan else m['ngay']) if vuot else han
        out.append({'ma': m['ma'], 'ten': m['ten'], 'dot': g.get('dot_thanh_toan', ''), 'ngay_cu': g['ngay'], 'ngay_moi': m['ngay'], 'han': han,
                    'ngay_doi': max(0, doi), 'vuot_han': vuot, 'han_de_xuat': han_dx, 'gan_cut_over': gan})
    return out


def cam_ket_thay_doi(nhap, ngay_cr, ext, k):
    """Cam kết của Chủ đầu tư có hạn sau ngày CR mà gói nhận đầu vào bắt đầu từ hạn dời k ngày trở đi: đề xuất dời hạn k ngày (giữ
    thời gian chuẩn bị của Chủ đầu tư so với cut over mới, không làm lịch chậm thêm)."""
    out = []
    for c in nhap.get('cam_ket_chu_dau_tu', []):
        if c['ma'] == MA_CK_BAT_DAU or not c.get('han') or c['han'] < ngay_cr or not c.get('bat_dau_som_nhat') or not k:
            continue
        moi = dich(ext, c['han'], k)
        if c['bat_dau_som_nhat'] >= moi:
            out.append({'ma': c['ma'], 'noi_dung': c.get('noi_dung', ''), 'han_truoc': c['han'], 'han_moi': moi, 'bat_dau_som_nhat': c['bat_dau_som_nhat']})
    return out


class MoPhong:
    """Dữ liệu chung của một lần đánh giá: lịch gốc, ngày CR, phần đã làm, ngày mở rộng."""

    def __init__(self, cr, ngay_cr, ngay_bd, thu_muc_luu):
        self.cr, self.ngay_cr, self.ngay_bd, self.luu = cr, ngay_cr, max(ngay_bd, ngay_cr), thu_muc_luu
        self.da = loi.du_an()
        self.wbs, self.pc = loi.doc_json('du_lieu/wbs.json'), loi.doc_json('du_lieu/phan_cong.json')
        self.lich = loi.doc_json('du_lieu/lich.json')
        self.tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']
        self.moc_nhap, self.hsmt = loi.doc_json(TEP_MOC), loi.doc_json('du_lieu/hsmt.json')
        self.nt = loi.doc_json('dau_vao/nha_thau.json', {})
        if not all('chi_so_bat_dau' in g for g in self.lich['goi'] if g.get('la')):
            thoat('TD18', 'du_lieu/lich.json thiếu chỉ số ngày của gói lá, chạy lại bước lich')
        self.days, self.ext = ngay_mo_rong(self.da)
        self.n = len(self.days)
        gv = {x['ma']: x for x in self.pc['giao_viec']}
        loe = {m for m, x in gv.items() if x.get('dan_trai')}
        self.i_cr, self.tt = lap_lai.trang_thai(loi, self.lich, ngay_cr, lambda d: chi_so_tu(self.ext, d), lambda d: chi_so_den(self.ext, d),
                                                {g['ma']: (float(g['md']), [gv[g['ma']]['R']] + gv[g['ma']].get('ho_tro', []))
                                                 for g in self.wbs['goi'] if g.get('la') and g['ma'] in gv}, loe)
        self.tmp = tempfile.mkdtemp(prefix='qlda_cr_')

    def goi_sau_qd(self, cr):
        """Gói chỉ làm sau quyết định: gói mới và gói thay đổi đã xong trước ngày CR (phần làm lại)."""
        lam_lai = [x['ma'] for x in cr.get('goi_thay_doi', []) if self.tt.get(x['ma'], {}).get('loai') == 'da_xong' and float(x.get('md_tang', 0)) > 0]
        return [g['ma'] for g in cr.get('goi_moi', [])] + lam_lai

    def goi_cho_goi_moi(self, giao_them):
        """Gói thay đổi phải chờ gói mới (them_phu_thuoc), không có khoảng ngày cố định: người làm, MD sau thay đổi, phụ thuộc."""
        lg, by = {g['ma']: g for g in self.lich['goi']}, {g['ma']: g for g in self.wbs['goi']}
        out = []
        for x in self.cr.get('goi_thay_doi', []):
            g = lg.get(x['ma'])
            if not g or not x.get('them_phu_thuoc') or any(rb.get('loai') in ('uat', 'khong_som_hon') for rb in g.get('rang_buoc') or []):
                continue
            nguoi = [giao_them.get(x['ma'], {}).get('R') or g['R']] + list(giao_them.get(x['ma'], {}).get('ho_tro', g.get('nguoi', [])[1:]))
            out.append({'ma': x['ma'], 'md': float(by[x['ma']]['md']) + float(x.get('md_tang', 0)), 'nguoi': nguoi,
                        'phu_thuoc': list(by[x['ma']].get('phu_thuoc', [])) + list(x['them_phu_thuoc']),
                        'thoi_luong_toi_thieu': by[x['ma']].get('thoi_luong_toi_thieu')})
        return out

    def du_lieu(self, cr, k, tvs, giao_moi, giao_them, e=0):
        uat_den = (self.da.get('uat') or {}).get('den', '')
        return {'du_lieu/wbs.json': dung_wbs(self.wbs, cr), 'du_lieu/phan_cong.json': dung_phan_cong(self.pc, giao_moi, giao_them),
                'dau_vao/thanh_vien.json': {'thanh_vien': tvs}, 'dau_vao/du_an.json': dung_du_an(self.da, self.ngay_cr, self.ngay_bd, self.ext, k, e),
                'dau_vao/nha_thau.json': self.nt, 'du_lieu/hsmt.json': self.hsmt, TEP_LICH_GOC: self.lich,
                TEP_MOC: dung_moc(self.moc_nhap, self.ngay_cr, self.ext, k, e, uat_den, self.goi_sau_qd(cr))}

    def kha_nang(self, tvs, giao_moi):
        """MD còn lại sau ngày CR (gói thường trước cut over, gồm CR), tốc độ còn lại của nhóm, số ngày tối thiểu theo quỹ."""
        tn = ns.TaiNguoi(tvs, self.lich, self.i_cr, self.da)
        lg = {g['ma']: g for g in self.lich['goi']}
        md = 0.0
        for g in dung_wbs(self.wbs, self.cr)['goi']:
            x = lg.get(g['ma'], {})
            if g.get('la') and not x.get('dan_trai') and x.get('giai_doan') != GIAI_DOAN_KET_THUC:
                md += max(0.0, float(g['md']) - self.tt.get(g['ma'], {}).get('da_lam', 0.0))
        toc = sum(tn.toc_do.values())
        return {'md_con_lai': round(md, 2), 'md_moi_ngay': round(toc, 2), 'so_ngay_theo_quy': math.ceil(md / toc) if toc else None,
                'so_ngay_den_cut_over_goc': self.n - self.i_cr}

    def phuong_an(self, ten, them=None):
        tvs = self.tvs + (them or {}).get('thanh_vien', [])
        giao_them = {g['ma']: g for g in (them or {}).get('giao_viec', [])}
        ht_thay = ns.de_xuat_ho_tro_thay_doi(self.cr.get('goi_thay_doi', []), self.lich, tvs, self.da, self.i_cr, giao_them,
                                             {g['ma']: g.get('loai') for g in self.wbs['goi']})
        giao_them = dict(ht_thay, **giao_them)
        giao_moi = ns.de_xuat_giao(self.cr.get('goi_moi', []), tvs, self.lich, self.i_cr, self.da, giao_them, chi_so_tu(self.ext, self.ngay_bd),
                                   self.goi_cho_goi_moi(giao_them))
        chay = lambda k, e=0, cr=self.cr: chay_lap_lich(self.du_lieu(cr, k, tvs, giao_moi, giao_them, e), os.path.join(self.tmp, ten))  # noqa: E731
        k, e, nhap, vong = lap_k(chay, self.ext, self.n)
        k_pt = k_theo_phu_thuoc(nhap, self.ext, self.n, k + e, self.i_cr)
        du_tru_cr = chay(0, 0)['du_tru_den_cut_over_ngay'] if k or e else nhap['du_tru_den_cut_over_ngay']
        if k or e:
            nhap = chay(k, e)
        tai = ns.tai_nguoi(nhap, tvs, self.i_cr, self.n + k + e, trong_gang)
        cb = [f for f in nhap['kiem_tra']['phat_hien'] if f['ma'] in ('L05', 'L06')]
        chuoi = ns.chuoi_dai_nhat(nhap, trong_gang)
        ho_tro = ns.goi_nen_ho_tro(nhap, chuoi, {g['ma'] for g in self.cr.get('goi_moi', [])} | {x['ma'] for x in self.cr.get('goi_thay_doi', [])})
        can, kl = ns.ket_luan_nhan_su(k + e, k_pt, tai, cb, ho_tro, bool(them))
        p_luu = os.path.join(self.luu, f'lich_mo_phong_{ten}.json')
        loi.ghi_json(p_luu, nhap)
        lg = {g['ma']: g for g in nhap['goi']}
        ma_cr = [x['ma'] for x in self.cr.get('goi_thay_doi', [])] + [g['ma'] for g in self.cr.get('goi_moi', [])]
        tom_tat = lambda m: {'ma': m, 'ten': lg[m]['ten'], 'md': lg[m]['md'], 'bat_dau': lg[m]['bat_dau'], 'ket_thuc': lg[m]['ket_thuc'],  # noqa: E731
                             'nguoi': lg[m].get('nguoi', [])}
        return {'phuong_an': ten, 'cut_over_goc': self.days[-1].isoformat(), 'cut_over_moi': self.ext[self.n - 1 + k + e].isoformat(),
                'ngay_lui_cut_over': k + e, 'ngay_lui_theo_phu_thuoc': k_pt, 'uat_keo_dai': e, 'uat_moi': uat_moi(nhap), 'ngay_do_nguon_luc': k + e - k_pt,
                'du_tru_cr_k0': du_tru_cr, 'ket_thuc_moi': nhap['ket_thuc_du_kien'], 'so_vong': vong,
                'moc': moc_thay_doi(nhap, self.lich, self.ext, self.ngay_cr, k + e, self.days[-1].isoformat()),
                'cam_ket': cam_ket_thay_doi(nhap, self.ngay_cr, self.ext, k), 'giao_viec_de_xuat': giao_moi, 'ho_tro_goi_thay_doi': list(ht_thay.values()), 'kha_nang': self.kha_nang(tvs, giao_moi),
                'goi': [tom_tat(m) for m in ma_cr if m in lg], 'chuoi_dai_nhat': [tom_tat(m) for m in chuoi],
                'goi_nen_ho_tro': ho_tro, 'tai_nguoi': tai, 'canh_bao_lich': [f['mo_ta'] for f in cb], 'can_them_nguoi': can, 'ket_luan_nhan_su': kl,
                'them_nguoi': them, 'lich_mo_phong': loi.tuong_doi(p_luu)}

    def du_tru_tham_chieu(self):
        """Dự trữ đến cut over của bản sao không có CR (cùng ngày CR), để tính tiêu hao dự trữ do CR."""
        cr0 = {k: v for k, v in self.cr.items() if k not in ('goi_moi', 'goi_thay_doi', 'muc_moi')}
        nhap = chay_lap_lich(self.du_lieu(cr0, 0, self.tvs, [], {}), os.path.join(self.tmp, 'tham_chieu'))
        return nhap['du_tru_den_cut_over_ngay'], do_vuot(nhap, self.ext, self.n, 0)


def danh_gia_lich(cr, ma, ngay_cr, ngay_bd, them_ds=()):
    """Đánh giá lịch của CR. them_ds: các phương án thêm nhân sự. Trả {ngay_cr, ngay_bat_dau_thay_doi, phan_da_lam, du_tru_tham_chieu,
    ngay_cham, tieu_hao_du_tru, hien_tai, them_nguoi | them_nguoi_1, them_nguoi_2...}."""
    ngay_ll = ngay_lap_lai(ngay_cr, ngay_mo_rong(loi.du_an())[1])
    mp = MoPhong(cr, ngay_ll, ngay_bd, loi.duong_dan(f'lam_viec/thay_doi/{ma}'))
    ten_them = ['them_nguoi'] if len(them_ds) == 1 else [f'them_nguoi_{i}' for i in range(1, len(them_ds) + 1)]
    try:
        du_tru_0, vuot_0 = mp.du_tru_tham_chieu()
        out = {'hien_tai': mp.phuong_an('hien_tai')}
        for t_, x in zip(ten_them, them_ds):
            out[t_] = mp.phuong_an(t_, x)
    finally:
        shutil.rmtree(mp.tmp, ignore_errors=True)
    nguon = sorted({v['nguon'] for v in mp.tt.values()})
    ht = out['hien_tai']
    return dict(out, ngay_cr=ngay_cr, ngay_lap_lai=ngay_ll, ngay_bat_dau_thay_doi=mp.ngay_bd, phan_da_lam='theo ' + ' và '.join(nguon) if nguon else '',
                so_goi_da_xong=sum(1 for v in mp.tt.values() if v['loai'] == 'da_xong'), so_goi_dang_lam=sum(1 for v in mp.tt.values() if v['loai'] != 'da_xong'),
                goi_da_xong=sorted((m for m, v in mp.tt.items() if v['loai'] == 'da_xong'), key=loi.khoa_ma),
                du_tru_tham_chieu=du_tru_0, cut_over_lui_khong_co_cr=vuot_0, phuong_an=['hien_tai'] + ten_them[:len(them_ds)],
                ngay_cham=max(0, du_tru_0 - ht['du_tru_cr_k0']), tieu_hao_du_tru=max(0, min(du_tru_0, du_tru_0 - ht['du_tru_cr_k0'])))
