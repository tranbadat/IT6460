"""Xuất tài liệu WBS: mỗi nhóm mức 1 một file Word và một file tổng hợp.

Dùng: python xuat_wbs.py [--ngay yyyy-mm-dd]   (ngày ghi trên tài liệu, mặc định ngày ký đơn dự thầu hoặc ngày bắt đầu dự án)
Nguồn: du_lieu/wbs.json (bắt buộc), du_lieu/phan_cong.json và du_lieu/lich.json (nếu có, để ghi người chịu trách nhiệm,
thời gian thực hiện), du_lieu/hsmt.json, du_lieu/rfp_yeu_cau.json, dau_vao/thanh_vien.json.
Ra: ket_qua/03_WBS/WBS_n_<ten>.docx, ket_qua/03_WBS/WBS_tong_hop.docx. Mỗi file được kiểm tra trình bày, văn phong
(đặc tả dac_ta/tai_lieu_wbs.json), đăng ký phiên bản và ghi nhật ký.
Tệp tổng hợp có mục Căn cứ ước lượng khi wbs.json có khối can_cu_uoc_luong (kiem_tra_wbs.py lập từ dau_vao/uoc_luong.json).
Ngày tài liệu: --ngay nếu có, giữ ngày đặt bằng --ngay ở phiên bản trước khi nội dung không đổi, còn lại theo ngày ký đơn hiện hành.
Lời căn cứ ước lượng, giả định ngoài phạm vi, giải trình hợp đồng tương tự (dữ liệu nhập) được thay tham chiếu dữ liệu {wbs#...}, {lich#...},
{da#...}, {cr#CRxx....}, {nhom#<mã nhóm>.md}, {cc#<mã nhóm>.md_muc_tieu}, {buoc#<số bước>....}, {ct#...} (chỉ tiêu kỹ thuật), {kl#truoc_cr}
(tổng tại hồ sơ dự thầu) bằng loi.giai_bieu_thuc để số liệu theo dữ liệu hiện hành. Yêu cầu thay đổi có phụ lục (du_lieu/thay_doi.json): bìa ghi
căn cứ là phụ lục và đường cơ sở hiện hành thay cho hồ sơ dự thầu, thông tin chung của nhóm có dòng Yêu cầu thay đổi (gói mới, gói tăng MD),
tệp tổng hợp có bảng truy vết yêu cầu thay đổi và ghi bước ước lượng theo phiếu yêu cầu thay đổi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json
import os
import shutil
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
LOI = os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts')
sys.path.insert(0, LOI)
import loi  # noqa: E402

import argparse  # noqa: E402
import itertools  # noqa: E402
import datetime as _dt  # noqa: E402
_ap = argparse.ArgumentParser(); _ap.add_argument('--ngay', help='ngày ghi trên tài liệu, yyyy-mm-dd (khi cập nhật theo yêu cầu thay đổi)')
_a = _ap.parse_args()
if _a.ngay:
    try:
        _dt.date.fromisoformat(_a.ngay)
    except ValueError:
        loi.thoat_loi(f'--ngay phải theo dạng yyyy-mm-dd, nhận được "{_a.ngay}"')
# WBS kèm theo hồ sơ dự thầu: mặc định ngày ký đơn dự thầu, chưa có thì ngày bắt đầu dự án
NGAY_TL = loi.ngay(_a.ngay or loi.doc_json('dau_vao/nha_thau.json', {}).get('ngay_ky_don') or loi.du_an()['ngay_bat_dau'])

wbs = loi.doc_json('du_lieu/wbs.json')
da = loi.du_an()
pc = loi.doc_json('du_lieu/phan_cong.json', {})
lich = loi.doc_json('du_lieu/lich.json', {})
tv = {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json', {'thanh_vien': []})['thanh_vien']}
by = {g['ma']: g for g in wbs['goi']}
giao = {x['ma']: x for x in pc.get('giao_viec', [])}
tn = {x['ma']: x for x in pc.get('trach_nhiem', [])}
lich_goi = {x['ma']: x for x in lich.get('goi', [])}
CR_PL = [c for c in loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []}).get('yeu_cau', [])
         if c.get('phu_luc') and (c.get('ap_dung') or {}).get('da_ghi')]  # yêu cầu thay đổi đã ký phụ lục và áp dụng vào dữ liệu
_CC = wbs.get('can_cu_uoc_luong') or {}
NGUON_TC = {'wbs': wbs, 'lich': lich, 'da': da, 'cr': {c['ma']: c for c in CR_PL}, 'nhom': {n['ma']: n for n in wbs['nhom']},
            'cc': {x['ma']: x for x in _CC.get('theo_nhom', [])}, 'buoc': {str(b['buoc']): b for b in _CC.get('cac_buoc', [])},
            'ct': loi.doc_json('dau_vao/chi_tieu_ky_thuat.json', {}),
            'kl': {'truoc_cr': round(wbs['tong_md'] - sum(float(c.get('md_tang') or 0) for c in CR_PL), 2)}}  # tổng tại hồ sơ dự thầu
BL_HH = (loi.doc_json('du_lieu/phien_ban.json', {}).get('duong_co_so') or [{}])[-1].get('ma', '')
SPEC = os.path.join(HERE, '..', 'dac_ta', 'tai_lieu_wbs.json')


def bt(s):
    """Thay tham chiếu dữ liệu trong lời văn của dữ liệu nhập (căn cứ, giả định, giải trình)."""
    loi_ = []
    out = loi.giai_bieu_thuc(str(s or ''), NGUON_TC, loi_)
    if loi_:
        loi.thoat_loi('Tham chiếu không giải được trong lời văn WBS: ' + ', '.join(map(str, loi_[:6])))
    return out


def cr_cua_nhom(ma):
    """[(CR, [(mã gói, MD tăng, mới)])] của các yêu cầu thay đổi có gói thuộc nhóm mức 1 ma."""
    out = []
    for c in CR_PL:
        g = [(x['ma'], float(x['md_tang']), bool(x.get('moi'))) for x in c.get('chi_tiet_goi', []) if x['ma'].split('.')[0] == ma]
        if g:
            out.append((c, sorted(g, key=lambda x: loi.khoa_ma(x[0]))))
    return out


def mo_ta_cr(c, g):
    moi = [m for m, _, mo in g if mo]
    tang = [f'{m} tăng {loi.md(d)} MD' for m, d, mo in g if not mo]
    return (f'{c["ma"]} {c["tieu_de"][:1].lower() + c["tieu_de"][1:]}, phụ lục hợp đồng {c["phu_luc"].get("so", "")} ngày {loi.ngay(c["phu_luc"].get("ngay"))}: '
            + '; '.join(x for x in ((f'{len(moi)} gói mới {moi[0]} đến {moi[-1]}' if len(moi) > 1 else (f'gói mới {moi[0]}' if moi else '')),
                                   ', '.join(tang)) if x))
OUT = loi.duong_dan('ket_qua/03_WBS')
WD = loi.duong_dan('lam_viec/tai_lieu_wbs')
os.makedirs(OUT, exist_ok=True); os.makedirs(WD, exist_ok=True)


def khong_dau(s):
    s = unicodedata.normalize('NFD', s.replace('đ', 'd').replace('Đ', 'D'))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return '_'.join(''.join(c if c.isalnum() else ' ' for c in s).split())


def ten_tv(i):
    return tv.get(i, {}).get('ho_ten', i)


def con_chau(ma):
    return [g for g in wbs['goi'] if g['ma'] == ma or g['ma'].startswith(ma + '.')]


def la_cua(ma):
    return [g for g in con_chau(ma) if g['la']]


def ngay_tai_lieu(tep_ra, h_khoi):
    """(ngày ghi trên tài liệu, có do --ngay đặt không).
    --ngay thì dùng ngày đó. Phiên bản trước có ngày do --ngay đặt (cập nhật theo yêu cầu thay đổi) và nội dung không đổi thì giữ ngày cũ.
    Còn lại theo ngày ký đơn hiện hành, nên đổi ngày ký đơn thì tài liệu đổi ngày theo dù nội dung không đổi."""
    if _a.ngay:
        return NGAY_TL, True
    cu_ = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})['tai_lieu'].get(tep_ra, [])
    if cu_ and cu_[-1].get('ngay_theo_tham_so') and cu_[-1].get('hash_khoi', cu_[-1]['hash']) == h_khoi:
        return cu_[-1]['ngay_tai_lieu'], True
    return NGAY_TL, False


def tao(noi_dung, ten_file, so_vong=3):
    nd_path = os.path.join(WD, ten_file.replace('.docx', '.json'))
    tep_ra = f'ket_qua/03_WBS/{ten_file}'
    h_khoi = loi.bam_obj(noi_dung['blocks'])
    ngay_tl, theo_tham_so = ngay_tai_lieu(tep_ra, h_khoi)
    h = loi.bam_obj({'khoi': noi_dung['blocks'], 'ngay': ngay_tl})  # đổi ngày tài liệu cũng là đổi nội dung
    pb, moi = loi.du_kien_phien_ban(tep_ra, h)
    noi_dung['meta'].update({'phien_ban': pb, 'ngay': ngay_tl})
    loi.ghi_json(nd_path, noi_dung)
    tmp = os.path.join(WD, ten_file)
    r = subprocess.run([sys.executable, os.path.join(LOI, 'build_docx.py'), nd_path, tmp], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        loi.thoat_loi(r.stderr)
    bc = os.path.join(WD, ten_file.replace('.docx', '_kiem_tra.json'))
    r = subprocess.run([sys.executable, os.path.join(LOI, 'kiem_tra_tai_lieu.py'), SPEC, tmp, '--json', bc], capture_output=True, text=True, encoding='utf-8', errors='replace')
    ket = r.stdout.strip().splitlines()[-1]
    if r.returncode:
        print(r.stdout); loi.thoat_loi(f'{ten_file} chưa đạt kiểm tra trình bày: {ket}')
    shutil.copy(tmp, loi.duong_dan(tep_ra))
    pb = loi.dang_ky_phien_ban('tai_lieu_wbs', tep_ra, ['wbs', 'phan_cong', 'lich', 'rfp_yc', 'hsmt', 'thanh_vien', 'du_an', 'nha_thau', 'uoc_luong'],
                               hash_noi_dung=h, them={'noi_dung': loi.tuong_doi(nd_path), 'ngay_tai_lieu': ngay_tl,
                                                      'ngay_theo_tham_so': theo_tham_so, 'hash_khoi': h_khoi})
    os.makedirs(loi.duong_dan('bang_chung/kiem_tra'), exist_ok=True)
    shutil.copy(bc, loi.duong_dan(f'bang_chung/kiem_tra/tai_lieu_wbs_{ten_file[:-5]}_v{pb}_lopA.json'))
    print(f'{tep_ra}: phiên bản {pb}, {ket}')
    return tep_ra


def cau(s):
    """Chuỗi thành câu: bỏ khoảng trắng, thêm dấu chấm cuối nếu thiếu."""
    s = str(s or '').strip()
    return s if not s or s[-1] in '.!?' else s + '.'


def van_ban_can_cu(v):
    """can_cu_uoc_luong của nhóm mức 1 (chuỗi hoặc {kich_thuoc, cach_phan_ra}) thành (kích thước, cách phân rã)."""
    if isinstance(v, dict):
        return cau(bt(v.get('kich_thuoc'))), cau(bt(v.get('cach_phan_ra')))
    return '', cau(bt(v))


def bia(tieu_de_phu):
    return [{'t': 'center', 'text': 'Cấu trúc phân rã công việc', 'size': 18}, {'t': 'center', 'text': tieu_de_phu, 'size': 15},
            {'t': 'blank'}, {'t': 'center', 'text': f'Dự án: {da["ten_du_an"]}'}, {'t': 'center', 'text': f'Khách hàng: {da["khach_hang"]}'},
            {'t': 'center', 'text': ('Tài liệu kế hoạch dự án, đường cơ sở ' + BL_HH + ''.join(f', cập nhật theo yêu cầu thay đổi {c["ma"]}, phụ lục hợp đồng '
                                                                                       f'{c["phu_luc"].get("so", "")}' for c in CR_PL))
             if loi.da_ky_hop_dong() and BL_HH else 'Tài liệu kế hoạch dự án, kèm theo Phần III. Đề xuất kỹ thuật của hồ sơ dự thầu'},
            {'t': 'center', 'text': 'Phiên bản {{PHIEN_BAN}}, ngày {{NGAY}}'}, {'t': 'blank'}]


CO_GIAI_DOAN = bool(lich_goi) and all('giai_doan_hien_thi' in x for x in lich_goi.values())  # lịch có giai đoạn dự án


def bang_chi_tiet(ma_goc):
    """Bảng chi tiết của một nhóm mức 1. Khi có lịch: cột Giai đoạn, sprint ghi sprint của gói phát triển và tên giai đoạn
    (Khởi động, Suốt dự án, Kết thúc) của gói quản lý dự án thay cho sprint."""
    rows = [['Mã WBS', 'Tên công việc', 'Mức', 'Khối lượng, MD', 'Loại công việc'] + (['Giai đoạn, sprint'] if CO_GIAI_DOAN else []) + ['Sản phẩm đầu ra']]
    dam = []
    for g in con_chau(ma_goc):
        if g['ma'] == ma_goc:
            continue
        gd_ = [lich_goi.get(g['ma'], {}).get('giai_doan_hien_thi', '')] if CO_GIAI_DOAN else []
        rows.append([g['ma'], g['ten'], str(g['muc']), loi.md(g['md']), g.get('loai', '') if g['la'] else ''] + gd_ + [g.get('san_pham', '')])
        if not g['la']:
            dam.append(len(rows) - 1)
    rows.append(['', 'Tổng cộng', '', loi.md(by[ma_goc]['md']), ''] + ([''] if CO_GIAI_DOAN else []) + [''])
    if CO_GIAI_DOAN:
        return {'t': 'table', 'rows': rows, 'widths': [900, 3000, 600, 1000, 900, 1200, 1700], 'center_cols': [2, 4, 5], 'right_cols': [3], 'dong_dam': dam}
    return {'t': 'table', 'rows': rows, 'widths': [1000, 3600, 600, 1100, 1000, 2000], 'center_cols': [2, 4], 'right_cols': [3], 'dong_dam': dam}


def thoi_gian_nhom(leaves):
    """Thời gian thực hiện của nhóm mức 1 theo lịch: sprint với gói phát triển, giai đoạn với gói quản lý dự án."""
    tu = min(lich_goi[g['ma']]['bat_dau'] for g in leaves); den = max(lich_goi[g['ma']]['ket_thuc'] for g in leaves)
    gd_ = {lich_goi[g['ma']].get('giai_doan', 'thuc_hien') for g in leaves}
    if gd_ != {'thuc_hien'}:
        ten = [loi.GIAI_DOAN[k] for k in ('khoi_dong', 'xuyen_suot', 'thuc_hien', 'ket_thuc') if k in gd_]
        noi = ', '.join(ten[:-1]) + ' và ' + ten[-1] if len(ten) > 1 else ten[0]
        return f'{loi.ngay(tu)} - {loi.ngay(den)} (giai đoạn {noi})'
    khoa_sp = lambda s: (not s[1:].isdigit(), int(s[1:]) if s[1:].isdigit() else 0, s)
    sp = sorted({lich_goi[g['ma']]['sprint_bat_dau'] for g in leaves} | {lich_goi[g['ma']]['sprint_ket_thuc'] for g in leaves}, key=khoa_sp)
    return f'{loi.ngay(tu)} - {loi.ngay(den)} (sprint {sp[0]} đến {sp[-1]})' if len(sp) > 1 else f'{loi.ngay(tu)} - {loi.ngay(den)} (sprint {sp[0]})'


tep_da_tao = []
for n in wbs['nhom']:
    ma = n['ma']
    goc = by[ma]
    leaves = la_cua(ma)
    ext_dep = sorted({p for g in leaves for p in g.get('phu_thuoc', []) if not p.startswith(ma + '.')}, key=loi.khoa_ma)
    nguoi = tn.get(ma, {}).get('A')
    if not nguoi and giao:
        md_nguoi = {}
        for g in leaves:
            r = giao.get(g['ma'], {}).get('R')
            if r:
                md_nguoi[r] = md_nguoi.get(r, 0) + float(g['md'])
        nguoi = max(md_nguoi, key=md_nguoi.get) if md_nguoi else None
    if lich_goi and all(g['ma'] in lich_goi for g in leaves):
        thoi_gian = thoi_gian_nhom(leaves)
    else:
        thoi_gian = 'Theo master schedule'
    info = [['Tổng khối lượng', f'{loi.md(goc["md"])} người-ngày'], ['Thời gian thực hiện', thoi_gian],
            ['Người chịu trách nhiệm', ten_tv(nguoi) if nguoi else 'Theo bảng phân công'],
            ['Phụ thuộc đầu vào', ('Hoàn thành các gói ' + ', '.join(f'{p} ({by[p]["ten"]})' for p in ext_dep)) if ext_dep else 'Không có'],
            ['Đơn vị khối lượng', f'Người-ngày, viết tắt MD, tính theo {da.get("gio_moi_md", 8)} giờ làm việc']]
    if goc.get('can_cu_uoc_luong'):
        info.insert(1, ['Căn cứ ước lượng', ' '.join(x for x in van_ban_can_cu(goc['can_cu_uoc_luong']) if x)])
    for c, g in cr_cua_nhom(ma):
        info.insert(2, ['Yêu cầu thay đổi', cau(mo_ta_cr(c, g))])
    blocks = bia(f'{goc["ten"]}, mã WBS {ma}')
    blocks += [{'t': 'h2', 'text': '1. Thông tin chung'}, {'t': 'table', 'rows': info, 'widths': [3000, 6300]},
               {'t': 'h2', 'text': '2. Sơ đồ WBS dạng cây phân cấp'},
               {'t': 'p', 'text': 'Sơ đồ dùng để trao đổi với Chủ đầu tư. Bảng chi tiết ở mục 3 dùng để ước lượng, giao việc và theo dõi tiến độ.'}]
    for g in con_chau(ma):
        blocks.append({'t': 'p', 'text': f'{g["ma"]}. {g["ten"]}' + ('' if g['la'] else ''), 'thut': g['muc'] - 1, 'dam': not g['la']})
    con2 = [g for g in wbs['goi'] if g['cha'] == ma]
    blocks += [{'t': 'pagebreak'}, {'t': 'h2', 'text': '3. Bảng chi tiết'},
               {'t': 'p', 'text': 'Mỗi gói công việc gắn với một sản phẩm kiểm tra được, có khối lượng ước lượng được và giao được cho một người.'},
               bang_chi_tiet(ma), {'t': 'h2', 'text': '4. Kiểm tra quy tắc 100%'},
               {'t': 'p', 'text': f'Tổng khối lượng các hạng mục mức 2, {" cộng ".join(loi.md(g["md"]) for g in con2)}, bằng {loi.md(goc["md"])} người-ngày, '
                                  f'khớp với khối lượng khai báo ở mức 1. Kết luận: cân bằng.'}]
    meta = {'ten': f'WBS {ma} - {goc["ten"]}', 'header': f'Lập kế hoạch - WBS {ma}, {goc["ten"]}', 'size_bang_pt': 12}
    tep_da_tao.append(tao({'meta': meta, 'blocks': blocks}, f'WBS_{ma}_{khong_dau(goc["ten"])}.docx'))

# ---- tổng hợp
def chu_thuong_dau(s):
    s = str(s or '').strip()
    return s[:1].lower() + s[1:]


def bang_buoc(cc):
    _md = loi.dinh_dang_cot([b['md'] for b in cc['cac_buoc']], 'md')
    rows = [['Bước', 'Nội dung', 'Khối lượng, MD']] + [[str(b['buoc']), b['noi_dung'], _md[i]] for i, b in enumerate(cc['cac_buoc'])]
    return {'t': 'table', 'rows': rows, 'widths': [800, 6800, 1700], 'center_cols': [0], 'right_cols': [2]}


def bang_theo_nhom(cc):
    tn_ = cc['theo_nhom']
    _mt = loi.dinh_dang_cot([x['md_muc_tieu'] for x in tn_] + [cc['tong_md_muc_tieu']], 'md')
    _wb = loi.dinh_dang_cot([x['md_wbs'] for x in tn_] + [cc['tong_md_wbs']], 'md')
    _cl = loi.dinh_dang_cot([x['chenh_lech'] for x in tn_] + [cc['chenh_lech_tong']], 'md')
    _pt = loi.dinh_dang_cot([x['ty_le_chenh'] for x in tn_], 'pt') or [''] * len(tn_)
    rows = [['Mã', 'Nhóm công việc', 'Ước lượng, MD', 'WBS, MD', 'Chênh lệch, MD', 'Tỷ lệ chênh lệch']]
    rows += [[x['ma'], x['ten'], _mt[i], _wb[i], _cl[i], _pt[i]] for i, x in enumerate(tn_)]
    rows.append(['', 'Tổng cộng', _mt[-1], _wb[-1], _cl[-1], ''])
    return {'t': 'table', 'rows': rows, 'widths': [600, 3700, 1300, 1200, 1300, 1200], 'right_cols': [2, 3, 4, 5]}


def bang_can_cu_nhom(cc):
    rows = [['Mã', 'Kích thước', 'Cách phân rã từ tổng nhóm']]
    for x in cc['theo_nhom']:
        kt, pr = van_ban_can_cu(x.get('can_cu'))
        rows.append([x['ma'], kt, pr])
    return {'t': 'table', 'rows': rows, 'widths': [600, 3200, 5500]}


def doan_tuong_tu(cc):
    lech = cc['ty_le_lech_trung_binh']
    huong = 'cao hơn' if lech > 0 else 'thấp hơn'
    muc = 'trong' if abs(lech) <= cc['nguong_lech_tuong_tu'] else 'vượt'
    s = (f'Tổng khối lượng WBS {loi.md(cc["tong_md_wbs"])} người-ngày {huong} {loi.pt(abs(lech))} so với quy mô trung bình '
         f'{loi.md(cc["trung_binh_tuong_tu_md"])} người-ngày của các hợp đồng tương tự, {muc} ngưỡng {loi.pt(cc["nguong_lech_tuong_tu"])} cần giải trình.')
    return s + (' ' + cau(bt(cc['giai_trinh_tuong_tu'])) if cc.get('giai_trinh_tuong_tu') else '')


def bang_tuong_tu(cc):
    hd = cc['hop_dong_tuong_tu']
    _qm = loi.dinh_dang_cot([x['quy_mo_md'] for x in hd] + [cc['trung_binh_tuong_tu_md']], 'md')
    _tl = loi.dinh_dang_cot([x['ty_le_so_voi_wbs'] for x in hd] + [cc['trung_binh_tuong_tu_md'] / cc['tong_md_wbs']], 'pt')
    rows = [['Hợp đồng', 'Chủ đầu tư', 'Hoàn thành', 'Quy mô, MD', 'So với tổng WBS']]
    rows += [[x['ten'], x['chu_dau_tu'], loi.ngay(x['ngay_hoan_thanh']), _qm[i], _tl[i]] for i, x in enumerate(hd)]
    rows.append(['Trung bình', '', '', _qm[-1], _tl[-1]])
    return {'t': 'table', 'rows': rows, 'widths': [3600, 2300, 1200, 1100, 1100], 'center_cols': [2], 'right_cols': [3, 4]}


def muc_can_cu(cc, tieu_de):
    """Mục Căn cứ ước lượng: phương pháp, các bước, bảng theo nhóm, căn cứ từng nhóm, đối chiếu hợp đồng tương tự, khoảng sai số."""
    quy_mo = ', '.join(x for x in (f'{cc["so_chuc_nang"]} chức năng' if cc.get('so_chuc_nang') else '',
                                   f'{cc["so_dau_viec_phi_chuc_nang"]} đầu việc phi chức năng' if cc.get('so_dau_viec_phi_chuc_nang') else '') if x)
    out = [tieu_de, {'t': 'p', 'text': cau(cc['phuong_phap'])},
           {'t': 'p', 'text': f'Loại ước lượng là {chu_thuong_dau(cc["loai_uoc_luong"])}' + (f', quy mô gồm {quy_mo}.' if quy_mo else '.')}]
    if cc.get('cac_buoc'):
        out += [{'t': 'p', 'text': 'Các bước ước lượng như sau.'}, bang_buoc(cc)]
        b_cr = [b for b in cc['cac_buoc'] if b.get('ma_cr')]
        if b_cr:
            out.append({'t': 'p', 'text': ' '.join(f'Bước {b["buoc"]} là ước lượng theo phiếu yêu cầu thay đổi {b["ma_cr"]} sau ký hợp đồng'
                                                   + (f', ghi nhận bằng phụ lục hợp đồng {b["phu_luc"]}' if b.get('phu_luc') else '') + '.' for b in b_cr)})
    khop = 'bằng tổng ước lượng' if abs(cc['chenh_lech_tong']) < 1e-9 else f'chênh lệch {loi.md(cc["chenh_lech_tong"])} người-ngày do làm tròn'
    out += [{'t': 'p', 'text': f'Tổng ước lượng {loi.md(cc["tong_md_muc_tieu"])} người-ngày được phân rã cho các nhóm công việc mức 1, '
                               f'dung sai mỗi nhóm {loi.pt(cc["dung_sai_nhom"] or 0)}. Tổng WBS {loi.md(cc["tong_md_wbs"])} người-ngày, {khop}.'},
            bang_theo_nhom(cc), {'t': 'p', 'text': 'Căn cứ ước lượng của từng nhóm công việc như sau.'}, bang_can_cu_nhom(cc)]
    if cc.get('hop_dong_tuong_tu'):
        out += [{'t': 'p', 'text': 'Đối chiếu với các hợp đồng tương tự nhà thầu đã thực hiện như sau.'}, bang_tuong_tu(cc),
                {'t': 'p', 'text': doan_tuong_tu(cc)}]
    ss = cc['khoang_sai_so']
    if ss.get('md_duoi') is not None:
        tren = loi.pt(ss['tren'])
        out.append({'t': 'p', 'text': f'Khoảng sai số của loại ước lượng này từ {loi.pt(ss["duoi"])} đến {"+" if ss["tren"] > 0 else ""}{tren}, '
                                      f'tương ứng {loi.md(ss["md_duoi"])} đến {loi.md(ss["md_tren"])} người-ngày.'})
    return out


blocks = bia('Tổng hợp WBS toàn dự án')
_dem_muc = itertools.count(1)


def tieu_de_muc(ten):
    """Tiêu đề mục đánh số tự động (mục Căn cứ ước lượng chỉ có khi wbs.json có can_cu_uoc_luong)."""
    return {'t': 'h2', 'text': f'{next(_dem_muc)}. {ten}'}


_md = loi.dinh_dang_cot([n['md'] for n in wbs['nhom']] + [wbs['tong_md']], 'md'); _pt = loi.dinh_dang_cot([n['ty_trong'] for n in wbs['nhom']] + [1], 'pt')
rows = [['Mã', 'Nhóm công việc', 'Khối lượng, MD', 'Tỷ trọng']] + [[n['ma'], n['ten'], _md[i], _pt[i]] for i, n in enumerate(wbs['nhom'])]
rows.append(['', 'Tổng cộng', _md[-1], _pt[-1]])
blocks += [tieu_de_muc('Khối lượng theo nhóm công việc'), {'t': 'table', 'rows': rows, 'widths': [800, 5200, 1700, 1600], 'right_cols': [2, 3]},
           {'t': 'p', 'text': f'Toàn dự án gồm {wbs["so_goi_la"]} gói công việc, tổng {loi.md(wbs["tong_md"])} người-ngày. Tổng các nhóm mức 1 bằng tổng các gói công việc, quy tắc 100% được đáp ứng.'},
           tieu_de_muc('Khối lượng theo loại công việc')]
_lo = [(k, v) for k, v in wbs['md_theo_loai'].items() if v]
_md = loi.dinh_dang_cot([v for _, v in _lo] + [sum(v for _, v in _lo)], 'md'); _pt = loi.dinh_dang_cot([v / wbs['tong_md'] for _, v in _lo] + [1], 'pt')
rows = [['Loại công việc', 'Khối lượng, MD', 'Tỷ trọng']] + [[k, _md[i], _pt[i]] for i, (k, _) in enumerate(_lo)]
rows.append(['Tổng cộng', _md[-1], _pt[-1]])
blocks.append({'t': 'table', 'rows': rows, 'widths': [4000, 2500, 2000], 'right_cols': [1, 2]})
if wbs.get('can_cu_uoc_luong'):
    blocks += muc_can_cu(wbs['can_cu_uoc_luong'], tieu_de_muc('Căn cứ ước lượng'))
blocks.append(tieu_de_muc('Cấu trúc mức 1 và mức 2'))
for g in wbs['goi']:
    if g['muc'] <= 2:
        blocks.append({'t': 'p', 'text': f'{g["ma"]}. {g["ten"]} ({loi.md(g["md"])} MD)', 'thut': g['muc'] - 1, 'dam': g['muc'] == 1})
rows = [['Mã yêu cầu', 'Yêu cầu RFP', 'Gói công việc đáp ứng']] + [[x['ma'], x['yeu_cau'], x['goi'] or 'Thuộc thủ tục đấu thầu hoặc điều khoản hợp đồng'] for x in wbs['truy_vet_rfp']]
blocks += [{'t': 'pagebreak'}, tieu_de_muc('Ma trận truy vết yêu cầu RFP'),
           {'t': 'p', 'text': 'Mỗi yêu cầu về hệ thống, sản phẩm, phạm vi và nội dung đề xuất của RFP được gắn với gói công việc đáp ứng. Yêu cầu về thủ tục và hợp đồng được đáp ứng trong hồ sơ dự thầu và kế hoạch quản lý.'},
           {'t': 'table', 'rows': rows, 'widths': [1100, 4600, 3600]}]
if CR_PL:  # truy vết yêu cầu thay đổi đã ký phụ lục tới gói công việc
    rows = [['Yêu cầu thay đổi', 'Phụ lục hợp đồng', 'Gói công việc', 'MD tăng']]
    for c in CR_PL:
        for x in sorted(c.get('chi_tiet_goi', []), key=lambda x: loi.khoa_ma(x['ma'])):
            rows.append([c['ma'], f'{c["phu_luc"].get("so", "")}, {loi.ngay(c["phu_luc"].get("ngay"))}',
                         f'{x["ma"]} {x["ten"]}' + (' (gói mới)' if x.get('moi') else ' (tăng khối lượng)'), loi.md(x['md_tang'])])
    blocks += [tieu_de_muc('Truy vết yêu cầu thay đổi'),
               {'t': 'p', 'text': 'Gói công việc thêm mới hoặc tăng khối lượng theo yêu cầu thay đổi đã được phê duyệt và ghi nhận bằng phụ lục hợp đồng.'},
               {'t': 'table', 'rows': rows, 'widths': [1300, 2300, 4700, 1000], 'center_cols': [0], 'right_cols': [3]}]
_md = loi.dinh_dang_cot([x['md'] for x in wbs['phan_bo_01a']] + [sum(x['md'] for x in wbs['phan_bo_01a'])], 'md')
rows = [['STT', 'Hạng mục Mẫu 01A', 'Gói công việc', 'Khối lượng, MD']] + [[str(x['stt']), x['danh_muc'], x['goi'], _md[i]] for i, x in enumerate(wbs['phan_bo_01a'])]
rows.append(['', 'Tổng cộng', '', _md[-1]])
blocks += [tieu_de_muc('Phân bổ theo hạng mục Mẫu 01A'),
           {'t': 'p', 'text': 'Bảng dùng để lập bảng tiến độ Mẫu 10A và bảng giá Mẫu 11A theo đúng danh mục dịch vụ của HSMT. Gói gắn nhiều hạng mục được chia đều khối lượng. Khi mọi gói của một mục đều thuộc hạng mục, bảng ghi mã mục thay cho từng gói.'},
           {'t': 'table', 'rows': rows, 'widths': [600, 3200, 4300, 1200], 'right_cols': [3]}, tieu_de_muc('Giả định ngoài phạm vi')]
for x in wbs['gia_dinh_ngoai_pham_vi'] or ['Không có']:
    blocks.append({'t': 'p', 'text': '- ' + bt(x)})
meta = {'ten': 'WBS tổng hợp', 'header': 'Lập kế hoạch - WBS tổng hợp', 'size_bang_pt': 12}
tep_da_tao.append(tao({'meta': meta, 'blocks': blocks}, 'WBS_tong_hop.docx'))
loi.ghi_nhat_ky('qlda-wbs', 'tai_lieu_wbs', 'script', f'Xuất {len(tep_da_tao)} tài liệu WBS, đạt kiểm tra trình bày',
                vao=['du_lieu/wbs.json'] + [p for p in ('du_lieu/phan_cong.json', 'du_lieu/lich.json') if os.path.exists(loi.duong_dan(p))], ra=tep_da_tao, ket_qua='đạt')
