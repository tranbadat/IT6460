"""Hàm dùng chung của skill qlda-risk: tiền tác động tự tính, mức tác động suy ra, quy đổi ma trận 3x3.

Nguyên tắc 2 của AGENTS.md: agent chỉ khai MD, ngày, loại công việc, gói và mốc liên kết; mọi số tiền do các hàm ở đây tính.
Tiền tác động = MD x đơn giá ngày của loại công việc + phạt chậm theo E-ĐKC 15 + khoản tiền thêm có lý do.
Phạt chậm: gói gắn ngày cut over (ghim, lich.json khong_som_hon) phạt toàn bộ số ngày chậm, gói trên đường găng phạt phần vượt
dự trữ đến cut over, gói khác không phạt. Cơ sở phạt là giá trị đợt thanh toán gắn mốc cut over, tối đa theo phat_toi_da_phan_tram.
E-ĐKC 15 phạt theo ngày lịch: số ngày làm việc chậm được quy đổi sang ngày lịch theo lịch dự án (loi.ngay_lam_viec, nghỉ thứ Bảy,
Chủ nhật và ngay_nghi của du_an.json), bằng số ngày từ ngày cut over đến ngày làm việc thứ n sau ngày cut over
(thang_do.json khóa phat_cham_quy_doi_ngay_lich).
"""
import datetime as _dt
import json
import math
import os

import loi

THU_MUC = os.path.dirname(os.path.abspath(__file__))
CUA_SO_QUY_DOI_NGAY = 400  # số ngày lịch sau cut over dùng lập danh sách ngày làm việc để quy đổi ngày chậm


def doc_thang_do():
    with open(os.path.join(THU_MUC, '..', 'references', 'thang_do.json'), encoding='utf-8') as f:
        return json.load(f)


def gia_co_so(dg, hsmt):
    """Giá dùng tính tỷ lệ chi phí và phạt: giá chào mục tiêu (dau_vao/don_gia.json, cach_tinh_gia muc_tieu), hoặc giá gói thầu
    (du_lieu/hsmt.json) khi giá chào chỉ có sau bước cost estimate. Trả về (giá, tên dùng trong tài liệu)."""
    if dg.get('cach_tinh_gia') == 'muc_tieu' and dg.get('gia_chao_muc_tieu'):
        return float(dg['gia_chao_muc_tieu']), 'giá chào'
    return float(hsmt['tien']['gia_goi_thau']), 'giá gói thầu'


def moc_cut_over(lich):
    return next((m for m in lich['moc'] if 'cut over' in m['ten'].lower()), None)


def thuoc_tap(goi, tap):
    """Gói thuộc tập khi trùng mã hoặc là mục cha của một gói trong tập."""
    return any(x == goi or x.startswith(goi + '.') for x in tap)


def ngay_lam_viec_sau(da, moc):
    """Ngày làm việc sau ngày moc theo lịch dự án, dùng loi.ngay_lam_viec trên cửa sổ bắt đầu ngay sau moc."""
    d0 = _dt.date.fromisoformat(str(moc)[:10])
    cua_so = dict(da, ngay_bat_dau=(d0 + _dt.timedelta(days=1)).isoformat(),
                  ngay_cut_over=(d0 + _dt.timedelta(days=CUA_SO_QUY_DOI_NGAY)).isoformat(), cut_over_la_ngay_lam_viec=True)
    return loi.ngay_lam_viec(cua_so)


def quy_doi_ngay_lich(n, bc):
    """Ngày lịch từ ngày cut over đến ngày làm việc thứ n sau đó (phần lẻ của n trừ theo tỷ lệ). Không quy đổi thì trả về n."""
    n = float(n or 0)
    if n <= 0 or not bc.get('ngay_lich') or not bc.get('ngay_cut'):
        return n
    k = math.ceil(n)
    ds = bc['ngay_sau_cut']
    if k > len(ds):
        return n * 7 / 5  # ngoài cửa sổ: xấp xỉ năm ngày làm việc mỗi tuần
    return float((ds[k - 1] - bc['ngay_cut']).days) - (k - n)


def lap_boi_canh(lich, hsmt, dg, pc, tv, da=None, ngay_lich=True):
    """Các tham số tính tiền và mức tác động, đọc một lần từ dữ liệu dự án.
    ngay_lich: quy đổi ngày làm việc chậm sang ngày lịch khi tính phạt (thang_do.json phat_cham_quy_doi_ngay_lich)."""
    hd = hsmt['hop_dong']
    gia, nguon_gia = gia_co_so(dg, hsmt)
    cut = moc_cut_over(lich) or {}
    pt_dot = {int(x['dot']): float(x['phan_tram']) / 100 for x in hd['thanh_toan']}
    dot_cut = cut.get('dot_thanh_toan')
    co_so_phat = pt_dot.get(int(dot_cut), 0.0) * gia if dot_cut not in (None, '') else 0.0
    ngay_dg = {k: float(v['don_gia_tron_goi_thang']) / float(dg['md_moi_mm']) for k, v in dg['loai_cong_viec'].items()}
    ngay_cut = cut.get('ngay') or lich.get('cut_over')
    da = da or loi.du_an()
    return {'ngay_lich': ngay_lich, 'ngay_cut': _dt.date.fromisoformat(str(ngay_cut)[:10]) if ngay_cut else None,
            'ngay_sau_cut': ngay_lam_viec_sau(da, ngay_cut) if ngay_cut and ngay_lich else [],
            'gia': gia, 'nguon_gia': nguon_gia, 'don_gia_ngay': ngay_dg, 'pt_dot': pt_dot, 'co_so_phat': co_so_phat,
            'phat_ngay': float(hd.get('phat_cham_tien_do_phan_tram_ngay') or 0) / 100, 'phat_toi_da': float(hd.get('phat_toi_da_phan_tram', 100)) / 100,
            'du_tru': float(lich.get('du_tru_den_cut_over_ngay') or 0), 'gang': set(lich.get('duong_gang', [])),
            'ghim': set(lich.get('khong_som_hon') or {}), 'moc': {m['ma']: m for m in lich['moc']}, 'cut': cut.get('ma'),
            'dot_cut': dot_cut, 'dg': dg, 'pc': pc, 'tv': tv}


def ngay_tre_cut_over(r, bc):
    """Số ngày chậm làm lùi cut over theo gói liên kết: gói ghim thì toàn bộ, gói trên đường găng thì phần vượt dự trữ."""
    if r.get('loai', 'de_doa') == 'co_hoi':
        return 0.0
    wbs, ngay = r.get('lien_ket_wbs', []), float(r.get('tac_dong_ngay') or 0)
    if any(thuoc_tap(g, bc['ghim']) for g in wbs):
        return ngay
    if any(thuoc_tap(g, bc['gang']) for g in wbs):
        return max(0.0, ngay - bc['du_tru'])
    return 0.0


def tren_gang_hoac_cut_over(r, bc):
    """Rủi ro liên kết gói trên đường găng, gói ghim hoặc mốc cut over: EMV thời gian của nó tiêu thụ dự trữ đến cut over."""
    wbs = r.get('lien_ket_wbs', [])
    return (any(thuoc_tap(g, bc['gang'] | bc['ghim']) for g in wbs) or bc['cut'] in r.get('lien_ket_moc', []))


def tien_them(r, bc):
    """Khoản tiền thêm: số do agent khai (kèm lý do) hoặc công thức {cach_tinh, ...}. Trả về (số tiền, lỗi hoặc None)."""
    tt = r.get('tien_them')
    if tt in (None, '', 0):
        return 0.0, None
    if isinstance(tt, (int, float)):
        return float(tt), None
    if not isinstance(tt, dict):
        return 0.0, 'tien_them phải là số hoặc {"cach_tinh": ...}'
    ct = tt.get('cach_tinh')
    if ct == 'chenh_luong_bo_sung':
        dg = bc['dg']
        ngay = lambda t: float(dg['luong_tham_chieu_thang'][t['vai_tro']]['luong']) * float(dg['he_so_bao_hiem']) / float(dg['ngay_lam_viec_moi_thang'])
        # cơ sở tính: MD công việc giao khi trả lương theo công sức, quỹ huy động khi trả theo huy động (hoặc khai co_so: md_giao, quy)
        co_so = tt.get('co_so') or ('md_giao' if dg.get('cach_tra_luong') == 'cong_suc' else 'quy')
        tong = sum(float(x[co_so]) * ngay(bc['tv'][x['id']]) for x in bc['pc']['tai']
                   if bc['tv'].get(x['id'], {}).get('loai') == 'bo_sung' and bc['tv'][x['id']].get('vai_tro') in dg['luong_tham_chieu_thang'])
        return float(tt.get('ty_le', 0)) * tong, None
    if ct == 'chi_phi_von':
        ty_le = sum(bc['pt_dot'].get(int(d), 0.0) for d in tt.get('dot', []))
        return ty_le * bc['gia'] * float(tt.get('lai_suat_nam', 0)) * float(tt.get('so_thang', 0)) / 12, None
    return 0.0, f'tien_them.cach_tinh "{ct}" không thuộc chenh_luong_bo_sung, chi_phi_von'


def tinh_tien(r, bc):
    """Tiền tác động tự tính và các thành phần. Trả về dict, khóa loi khi không tính được."""
    md, loai = float(r.get('tac_dong_md') or 0), r.get('loai_cong_viec')
    out = {'ngay_phat': 0.0, 'ngay_phat_lich': 0.0, 'tien_phat': 0.0, 'tien_nhan_cong': 0.0, 'tien_them': 0.0, 'tien': None, 'loi': None}
    if md and loai not in bc['don_gia_ngay']:
        out['loi'] = f'loai_cong_viec "{loai}" không thuộc {list(bc["don_gia_ngay"])} của dau_vao/don_gia.json'
        return out
    them, loi_them = tien_them(r, bc)
    if loi_them:
        out['loi'] = loi_them
        return out
    ngay_phat = ngay_tre_cut_over(r, bc)
    ngay_lich = quy_doi_ngay_lich(ngay_phat, bc)
    phat = min(ngay_lich * bc['phat_ngay'], bc['phat_toi_da']) * bc['co_so_phat']
    nhan_cong = md * bc['don_gia_ngay'].get(loai, 0.0)
    return dict(out, ngay_phat=ngay_phat, ngay_phat_lich=round(ngay_lich, 2), tien_phat=round(phat), tien_nhan_cong=round(nhan_cong),
                tien_them=round(them), tien=round(nhan_cong + phat + them), phat_toi_da=ngay_lich * bc['phat_ngay'] >= bc['phat_toi_da'] > 0)


def muc_theo_nguong(gia_tri, nguong):
    """Mức lớn nhất có ngưỡng nhỏ hơn hoặc bằng giá trị; dưới mọi ngưỡng là mức 1."""
    return max([1] + [int(k) for k, v in nguong.items() if gia_tri >= v])


def moc_cham(r, bc):
    """Mốc liên kết bị chậm theo tac_dong_ngay: mốc cut over chỉ khi vượt dự trữ, mốc khác khi có ngày chậm."""
    ngay = float(r.get('tac_dong_ngay') or 0)
    ds = []
    for m in r.get('lien_ket_moc', []):
        if m not in bc['moc']:
            continue
        han_cho = bc['du_tru'] if m == bc['cut'] else 0.0
        if ngay > han_cho:
            ds.append(m)
    return ds


def suy_muc_tac_dong(r, bc, tien, cfg, phat_toi_da=False):
    """Mức tác động suy từ ngày chậm, tỷ lệ chi phí trên giá và các cờ. Trả về (mức, danh sách căn cứ).
    phat_toi_da: tiền phạt đã chạm mức tối đa của E-ĐKC 15, coi như vi phạm hợp đồng."""
    ng = cfg['nguong_tac_dong']
    ngay = float(r.get('tac_dong_ngay') or 0)
    ty_le = float(tien or 0) / bc['gia'] if bc['gia'] else 0.0
    co_hoi = r.get('loai', 'de_doa') == 'co_hoi'
    can_cu = [(muc_theo_nguong(ngay, ng['ngay_tu']), f'{"sớm" if co_hoi else "chậm"} {loi.so(ngay, 1).rstrip("0").rstrip(",")} ngày'),
              (muc_theo_nguong(ty_le, ng['ty_le_chi_phi_tu']), f'{"lợi ích" if co_hoi else "chi phí"} bằng {loi.pt(ty_le, 2)} {bc["nguon_gia"]}')]
    if not co_hoi:
        cham = moc_cham(r, bc)
        if bc['cut'] in cham or ngay_tre_cut_over(r, bc) > 0:
            can_cu.append((ng['co']['cut_over'], cfg['ten_co']['cut_over']))
        tt = [m for m in cham if bc['moc'][m].get('dot_thanh_toan') not in (None, '') and m != bc['cut']]
        if tt:
            can_cu.append((ng['co']['moc_thanh_toan'], f'{cfg["ten_co"]["moc_thanh_toan"]} {" và ".join(tt)}'))
        if r.get('vi_pham_hop_dong') or phat_toi_da:
            can_cu.append((ng['co']['vi_pham_hop_dong'], cfg['ten_co']['vi_pham_hop_dong']))
    muc = max(m for m, _ in can_cu)
    return muc, [f'{t} (mức {m})' for m, t in can_cu]


def hang_3x3(xs, td, cfg):
    q = cfg['quy_doi_3x3']
    return q['hang'][q['muc'][str(xs)]][q['muc'][str(td)]]


def lien_ket_hien_thi(r, bc):
    """Gói và mốc liên kết, mốc kèm ngày dự kiến theo master schedule."""
    moc = [f'{m} ({loi.ngay(bc["moc"][m]["ngay"])})' if m in bc['moc'] else m for m in r.get('lien_ket_moc', [])]
    lk = (['Gói ' + ', '.join(r['lien_ket_wbs'])] if r.get('lien_ket_wbs') else []) + (['Mốc ' + ', '.join(moc)] if moc else [])
    return '. '.join(lk) or 'Không có'
