"""Giao việc gói mới, phương án thêm nhân sự và kết luận cần thêm người của một yêu cầu thay đổi, do lich_thay_doi.py import.

- de_xuat_giao: người thực hiện theo phiếu hoặc phương án thêm nhân sự; thiếu thì xếp thử theo thời gian (ngày rảnh của từng người sau
  phần việc của lịch gốc, thứ tự phụ thuộc của gói mới), chọn người cùng năng lực xong sớm nhất, thêm người hỗ trợ khi làm gói xong sớm hơn.
- de_xuat_ho_tro_thay_doi: gói thay đổi có khoảng ngày cố định (kiểm thử chấp nhận) mà MD tăng vượt sức người đang làm: thêm người hỗ trợ.
Giao việc là đề xuất, nhóm quyết định (ghi R, ho_tro trong phiếu hoặc phương án để thay).
- ket_luan_nhan_su: cần thêm người khi số ngày lùi lớn hơn số ngày theo phụ thuộc (người làm bận), khi chuỗi dài nhất có gói một người
  làm từ SO_MD_NEN_TACH MD, hoặc có gói xếp sau thời gian tham gia của người làm (L05).
- doc_them_nguoi: đọc tệp phương án thêm nhân sự (TD21).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

TOC_DO_TOI_THIEU = 0.05  # như lap_lich.py: phần thời gian tối thiểu mỗi ngày cho gói thường
NGUONG_HO_TRO = 4  # gói mới từ số MD này được đề xuất người hỗ trợ khi có người cùng năng lực còn quỹ
SO_MD_NEN_TACH = 4  # gói một người làm từ số MD này trên chuỗi dài nhất được gợi ý thêm người hỗ trợ
NGUONG_NUT_THAT = 0.9  # người dùng từ tỷ lệ này quỹ thời gian còn lại sau ngày CR được coi là nút thắt
GIAI_DOAN_KET_THUC = 'ket_thuc'


def thoat(ma, msg):
    loi.thoat_loi(f'{ma} {msg}')


def tai_sau_cr(lich_goc, i_cr):
    """MD kế hoạch của từng người từ ngày CR trở đi (phần gói nằm sau ngày CR, chia đều theo ngày). Trả (gói thường, gói dàn trải)."""
    tai, loe = {}, {}
    for g in lich_goc['goi']:
        if not g.get('la') or 'chi_so_bat_dau' not in g or g['chi_so_ket_thuc'] < i_cr or g.get('giai_doan') == GIAI_DOAN_KET_THUC:
            continue
        s, f = g['chi_so_bat_dau'], g['chi_so_ket_thuc']
        phan = (f - max(s, i_cr) + 1) / (f - s + 1)
        dich_ = loe if g.get('dan_trai') else tai
        for p, md in (g.get('phan_nguoi') or {}).items():
            dich_[p] = dich_.get(p, 0.0) + float(md) * phan
    return tai, loe


def quy_sau_cr(tv, sprints, i_cr, n):
    """Số MD khả dụng của một người từ ngày CR đến cut over gốc."""
    a = i_cr
    if tv.get('tu_sprint') not in (None, ''):
        s = next((s for s in sprints if s['so'] == int(tv['tu_sprint'])), None)
        a = max(a, s['chi_so_dau'] if s else n)
    b = n - 1
    if tv.get('den_sprint') not in (None, ''):
        s = next((s for s in sprints if s['so'] == int(tv['den_sprint'])), None)
        b = min(b, s['chi_so_cuoi'] if s else b)
    return max(0, b - a + 1) * float(tv.get('ty_le', 1))


class TaiNguoi:
    """Tải, quỹ và tốc độ còn lại sau ngày CR của từng người, cập nhật khi giao thêm gói."""

    def __init__(self, tvs, lich_goc, i_cr, da):
        sprints, n = loi.danh_sach_sprint(da), len(loi.ngay_lam_viec(da))
        self.tai, self.loe = tai_sau_cr(lich_goc, i_cr)
        so_ngay = max(1, n - i_cr)
        self.quy = {t['id']: quy_sau_cr(t, sprints, i_cr, n) for t in tvs}
        self.toc_do = {t['id']: max(TOC_DO_TOI_THIEU, min(float(t.get('ty_le', 1)), self.quy[t['id']] / so_ngay) - self.loe.get(t['id'], 0) / so_ngay)
                       for t in tvs}
        self.thu_tu = [t['id'] for t in tvs]

    def diem(self, p, md):
        """Số ngày để người p xong tải còn lại cộng md (nhỏ là xong sớm)."""
        return ((self.tai.get(p, 0) + md) / self.toc_do[p], self.thu_tu.index(p))

    def con_quy(self, p):
        return self.quy[p] - self.loe.get(p, 0) - self.tai.get(p, 0)

    def giao(self, nguoi, md):
        for p in nguoi:
            self.tai[p] = self.tai.get(p, 0) + md / len(nguoi)


def _bat_dau_tham_gia(tv, sprints, n):
    if tv.get('tu_sprint') in (None, ''):
        return 0
    s = next((s for s in sprints if s['so'] == int(tv['tu_sprint'])), None)
    return s['chi_so_dau'] if s else n


def _ranh_tu(tvs, lich_goc, i_cr, sprints, n):
    """Ngày (chỉ số) mỗi người xong phần gói thường của lịch gốc nằm sau ngày CR, không sớm hơn ngày tham gia."""
    out = {t['id']: max(i_cr, _bat_dau_tham_gia(t, sprints, n)) for t in tvs}
    for g in lich_goc['goi']:
        if not g.get('la') or g.get('dan_trai') or 'chi_so_ket_thuc' not in g or g.get('giai_doan') == GIAI_DOAN_KET_THUC:
            continue
        for p in g.get('nguoi', []):
            b = (g.get('phan_chi_so') or {}).get(p, [g['chi_so_bat_dau'], g['chi_so_ket_thuc']])[1]
            if p in out and b >= i_cr:
                out[p] = max(out[p], b + 1)
    return out


def _thu_tu_topo(goi_moi, truoc=()):
    """Thứ tự theo phụ thuộc, trong cùng một lượt gói có mã trong truoc (người làm cố định) xếp trước."""
    ma = {g['ma'] for g in goi_moi}
    xong, out, con = set(), [], list(goi_moi)
    while con:
        san = [g for g in con if all(p in xong or p not in ma for p in g.get('phu_thuoc', []))] or con[:1]
        san.sort(key=lambda g: g['ma'] not in truoc)
        for g in san:
            out.append(g); xong.add(g['ma']); con.remove(g)
    return out


def de_xuat_giao(goi_moi, tvs, lich_goc, i_cr, da, giao_them, i_bd=None, goi_co_dinh=()):
    """Trả [{ma, R, ho_tro, nguon, ly_do}] cho gói mới. Người thực hiện theo phiếu hoặc phương án; thiếu thì xếp thử theo thời gian:
    gói theo thứ tự phụ thuộc bắt đầu sau gói trước và ngày bắt đầu phần thay đổi, chọn người cùng năng lực xong sớm nhất (ngày rảnh
    sau phần việc của lịch gốc, tốc độ còn lại sau gói dàn trải), rồi thêm người hỗ trợ khi làm gói xong sớm hơn (tối đa một người với
    gói từ NGUONG_HO_TRO MD, hai người từ 2 x NGUONG_HO_TRO MD). Quỹ sau cut over gốc do lap_lich.py kiểm tra (L05, L06). goi_co_dinh: gói hiện có phải chờ gói mới
    (gói thay đổi có them_phu_thuoc), người làm giữ nguyên, được xếp thử cùng để biết ngày rảnh của người làm."""
    tn = TaiNguoi(tvs, lich_goc, i_cr, da)
    sprints, n = loi.danh_sach_sprint(da), len(loi.ngay_lam_viec(da))
    ranh = _ranh_tu(tvs, lich_goc, i_cr, sprints, n)
    xong = {g['ma']: g['chi_so_ket_thuc'] for g in lich_goc['goi'] if g.get('la') and 'chi_so_ket_thuc' in g}
    bd0 = max(i_cr, i_bd or i_cr)
    out = {}
    co_dinh = {g['ma'] for g in goi_co_dinh}
    for g in _thu_tu_topo(list(goi_moi) + list(goi_co_dinh), co_dinh):
        md, gt = float(g['md']), giao_them.get(g['ma'], {})
        tmin = int(g.get('thoi_luong_toi_thieu') or 0)
        es = max([bd0] + [xong.get(p, bd0 - 1) + 1 for p in g.get('phu_thuoc', [])])

        def ket_thuc(ds):
            a = max([es] + [ranh[p] for p in ds])
            return a, a + max(tmin, math.ceil(md / sum(tn.toc_do[p] for p in ds) - 1e-9)) - 1
        if g['ma'] in co_dinh:
            a, b = ket_thuc(g['nguoi'])
            for p in g['nguoi']:
                ranh[p] = b + 1
            xong[g['ma']] = b
            continue
        r, ho_tro = gt.get('R') or g.get('R'), list(gt.get('ho_tro', g.get('ho_tro', [])))
        nguon, ly_do = ('phương án thêm nhân sự' if gt.get('R') else 'phiếu'), ''
        ung = [t['id'] for t in tvs if g['loai'] in t.get('loai_cong_viec', [])]
        if not ung:
            ung, ly_do = list(tn.thu_tu), f'Không thành viên nào khai báo loại {g["loai"]}, đề xuất người xong sớm nhất'
        if not r:
            r = min(ung, key=lambda p: (ket_thuc([p])[1], -tn.toc_do[p], tn.thu_tu.index(p)))
            nguon = 'đề xuất theo năng lực, ngày rảnh và quỹ còn lại sau ngày CR'
            if not ho_tro and md >= NGUONG_HO_TRO and not tmin:
                for _ in range(1 if md < 2 * NGUONG_HO_TRO else 2):
                    ds = [r] + ho_tro
                    tot = [p for p in ung if p not in ds and ket_thuc(ds + [p])[1] < ket_thuc(ds)[1]]
                    if not tot:
                        break
                    ho_tro.append(min(tot, key=lambda p: (ket_thuc(ds + [p])[1], tn.thu_tu.index(p))))
        a, b = ket_thuc([r] + ho_tro)
        for p in [r] + ho_tro:
            ranh[p] = b + 1
        xong[g['ma']] = b
        tn.giao([r] + ho_tro, md)
        out[g['ma']] = {'ma': g['ma'], 'R': r, 'ho_tro': ho_tro, 'nguon': nguon, 'ly_do': ly_do}
    return [out[g['ma']] for g in goi_moi]


def de_xuat_ho_tro_thay_doi(goi_thay_doi, lich_goc, tvs, da, i_cr, giao_them, loai_goi):
    """Gói thay đổi có khoảng ngày cố định (kiểm thử chấp nhận, thời lượng tối thiểu) mà MD sau thay đổi vượt sức người đang làm trong
    khoảng đó: đề xuất thêm người hỗ trợ cùng năng lực còn nhiều quỹ nhất để không phải kéo dài khoảng. Trả {mã: {ma, ho_tro, nguon}}."""
    tn = TaiNguoi(tvs, lich_goc, i_cr, da)
    lg = {g['ma']: g for g in lich_goc['goi']}
    loai = {t['id']: t.get('loai_cong_viec', []) for t in tvs}
    out = {}
    for x in goi_thay_doi:
        g = lg.get(x['ma'])
        if not g or x['ma'] in giao_them or not float(x.get('md_tang', 0)):
            continue
        cua_so = max([rb.get('so_ngay', 0) for rb in g.get('rang_buoc') or [] if rb.get('loai') in ('uat', 'thoi_luong_toi_thieu')] + [0])
        if not cua_so:
            continue
        nguoi = list(g.get('nguoi', []))
        can = (float(g['md']) + float(x['md_tang'])) / cua_so
        them = []
        while sum(tn.toc_do.get(p, 0) for p in nguoi + them) < can - 1e-9:
            ung = [p for p in tn.thu_tu if p not in nguoi + them and loai_goi.get(x['ma']) in loai[p]]
            if not ung:
                break
            them.append(max(ung, key=lambda p: (tn.con_quy(p), -tn.thu_tu.index(p))))
        if them:
            tn.giao(them, float(x['md_tang']))
            out[x['ma']] = {'ma': x['ma'], 'ho_tro': [p for p in nguoi if p != g.get('R')] + them, 'them': them,
                            'nguon': f'thêm người để xong {loi.so(float(g["md"]) + float(x["md_tang"]), 2)} MD trong {cua_so} ngày của khoảng cố định'}
    return out


def tai_nguoi(nhap, tvs, i_cr, n_cut, trong_gang):
    """MD sau ngày CR, quỹ đến cut over mới, tỷ lệ sử dụng của từng người trong lịch mô phỏng."""
    tv = {t['id']: t for t in tvs}
    md = {}
    for g in nhap['goi']:
        if g.get('la') and g.get('trang_thai_lap_lai') != 'da_xong' and g.get('giai_doan') != GIAI_DOAN_KET_THUC and 'chi_so_ket_thuc' in g:
            for p, v in (g.get('phan_nguoi') or {}).items():
                md[p] = md.get(p, 0.0) + float(v)
    out = []
    for p, v in md.items():
        q = max(0, n_cut - i_cr) * float(tv.get(p, {}).get('ty_le', 1))
        out.append({'id': p, 'ho_ten': tv.get(p, {}).get('ho_ten', p), 'md': round(v, 2), 'quy': round(q, 2), 'ty_le': round(v / q, 4) if q else 0})
    return sorted(out, key=lambda x: -x['ty_le'])


def chuoi_dai_nhat(nhap, trong_gang):
    """Chuỗi gói quyết định ngày kết thúc: từ gói xong muộn nhất, lần ngược theo gói đứng trước xong muộn nhất (bỏ gói đã xong)."""
    la = {g['ma']: g for g in nhap['goi'] if trong_gang(g) and 'chi_so_ket_thuc' in g and g.get('trang_thai_lap_lai') != 'da_xong'}
    if not la:
        return []
    m = max(la, key=lambda x: (la[x]['chi_so_ket_thuc'], x))
    out = [m]
    while True:
        truoc = [p for p in la[m].get('phu_thuoc', []) if p in la and p not in out]
        if not truoc:
            return out[::-1]
        m = max(truoc, key=lambda x: la[x]['chi_so_ket_thuc'])
        out.append(m)


def goi_nen_ho_tro(nhap, chuoi, ma_moi):
    """Gói trên chuỗi dài nhất do một người làm, từ SO_MD_NEN_TACH MD, ưu tiên gói của CR: nên thêm người hỗ trợ."""
    lg = {g['ma']: g for g in nhap['goi']}
    ds = [lg[m] for m in chuoi if not any(rb.get('loai') in ('uat', 'phe_duyet') for rb in lg[m].get('rang_buoc') or [])
          and len(lg[m].get('nguoi', [])) == 1 and float(lg[m]['md']) >= SO_MD_NEN_TACH]
    ds.sort(key=lambda g: (g['ma'] not in ma_moi, -float(g['md'])))
    return [f'{g["ma"]} ({g["nguoi"][0]}, {loi.so(float(g["md"]), 2)} MD)' for g in ds[:5]]


def ket_luan_nhan_su(k, k_pt, tai, canh_bao, ho_tro, co_them):
    nut = [x for x in tai if x['ty_le'] >= NGUONG_NUT_THAT]
    ten = ', '.join(f'{x["ho_ten"]} {x["ty_le"]:.0%}' for x in nut[:4])
    keo = [f['mo_ta'] for f in canh_bao if f['ma'] == 'L05']
    goi_y = f'. Gói trên chuỗi dài nhất do một người làm, thêm người hỗ trợ sẽ rút ngắn: {", ".join(ho_tro)}' if ho_tro else ''
    thu = ' ngoài phương án này' if co_them else ', thử phương án bằng --them-nguoi'
    if not k:
        kl, can = 'Không cần thêm người: lịch hấp thụ phần thay đổi trong dự trữ đến cut over', False
    elif k_pt < k:
        kl = (f'Nguồn lực là nút thắt: với cách giao việc này, theo phụ thuộc chỉ cần lùi {k_pt} ngày, {k - k_pt} ngày còn lại do người làm bận'
              + (f' (người dùng từ {NGUONG_NUT_THAT:.0%} quỹ: {ten})' if ten else '') + goi_y + f'. Cần thêm người{thu}')
        can = True
    elif ho_tro:
        kl, can = f'Chậm do chuỗi phụ thuộc với cách giao việc này{goi_y}. Cần thêm người nếu muốn giảm số ngày lùi{thu}', True
    else:
        kl, can = 'Chậm do chuỗi phụ thuộc và ngày ghim, thêm người không rút ngắn được ngày cut over', False
    if keo:
        kl += '. Có gói xếp sau thời gian tham gia của người làm, cần kéo dài huy động: ' + '; '.join(keo[:3])
        can = True
    return can, kl


def doc_them_nguoi(p, tvs, dg):
    """Tệp phương án thêm nhân sự: {"thanh_vien": [...dòng như thanh_vien.json], "giao_viec": [{ma, R, ho_tro}]}."""
    if not p:
        return None
    try:
        x = json.load(open(loi.duong_dan(p), encoding='utf-8'))
    except (OSError, ValueError) as e:
        thoat('TD21', f'Không đọc được tệp phương án thêm nhân sự {p}: {e}')
    ids = {t['id'] for t in tvs}
    loi_ds = []
    for t in x.get('thanh_vien', []):
        if not t.get('id') or t['id'] in ids:
            loi_ds.append(f'thành viên {t.get("id")} thiếu mã hoặc trùng mã trong thanh_vien.json')
        if not t.get('ho_ten') or not t.get('loai_cong_viec'):
            loi_ds.append(f'thành viên {t.get("id")} thiếu ho_ten hoặc loai_cong_viec')
        if t.get('vai_tro') not in dg.get('luong_tham_chieu_thang', {}):
            loi_ds.append(f'thành viên {t.get("id")}: vai_tro {t.get("vai_tro")} chưa có lương tham chiếu trong don_gia.json')
        ids.add(t.get('id'))
    for g in x.get('giao_viec', []):
        for p_ in [g.get('R')] + list(g.get('ho_tro', [])):
            if p_ and p_ not in ids:
                loi_ds.append(f'giao việc {g.get("ma")}: {p_} không có trong thành viên')
    if not x.get('thanh_vien') and not x.get('giao_viec'):
        loi_ds.append('cần thanh_vien hoặc giao_viec')
    if loi_ds:
        thoat('TD21', 'Phương án thêm nhân sự không hợp lệ: ' + '; '.join(loi_ds))
    return {'tep': loi.tuong_doi(loi.duong_dan(p)), 'thanh_vien': x.get('thanh_vien', []), 'giao_viec': x.get('giao_viec', [])}
