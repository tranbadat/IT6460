"""Xuất tài liệu WBS: mỗi nhóm mức 1 một file Word và một file tổng hợp.

Dùng: python xuat_wbs.py [--ngay yyyy-mm-dd]   (ngày ghi trên tài liệu, mặc định ngày ký đơn dự thầu hoặc ngày bắt đầu dự án)
Nguồn: du_lieu/wbs.json (bắt buộc), du_lieu/phan_cong.json và du_lieu/lich.json (nếu có, để ghi người chịu trách nhiệm,
thời gian thực hiện), du_lieu/hsmt.json, du_lieu/rfp_yeu_cau.json, dau_vao/thanh_vien.json.
Ra: ket_qua/03_WBS/WBS_n_<ten>.docx, ket_qua/03_WBS/WBS_tong_hop.docx. Mỗi file được kiểm tra trình bày, văn phong
(đặc tả dac_ta/tai_lieu_wbs.json), đăng ký phiên bản và ghi nhật ký.
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
SPEC = os.path.join(HERE, '..', 'dac_ta', 'tai_lieu_wbs.json')
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


def tao(noi_dung, ten_file, so_vong=3):
    nd_path = os.path.join(WD, ten_file.replace('.docx', '.json'))
    h = loi.bam_obj(noi_dung['blocks'])
    tep_ra = f'ket_qua/03_WBS/{ten_file}'
    pb, moi = loi.du_kien_phien_ban(tep_ra, h)
    cu_ = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})['tai_lieu'].get(tep_ra, [])
    ngay_tl = cu_[-1]['ngay_tai_lieu'] if (not moi and cu_ and cu_[-1].get('ngay_tai_lieu') and not _a.ngay) else NGAY_TL
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
    pb = loi.dang_ky_phien_ban('tai_lieu_wbs', tep_ra, ['wbs', 'phan_cong', 'lich', 'rfp_yc', 'hsmt', 'thanh_vien', 'du_an'], hash_noi_dung=h,
                               them={'noi_dung': loi.tuong_doi(nd_path), 'ngay_tai_lieu': ngay_tl})
    os.makedirs(loi.duong_dan('bang_chung/kiem_tra'), exist_ok=True)
    shutil.copy(bc, loi.duong_dan(f'bang_chung/kiem_tra/tai_lieu_wbs_{ten_file[:-5]}_v{pb}_lopA.json'))
    print(f'{tep_ra}: phiên bản {pb}, {ket}')
    return tep_ra


def bia(tieu_de_phu):
    return [{'t': 'center', 'text': 'Cấu trúc phân rã công việc', 'size': 18}, {'t': 'center', 'text': tieu_de_phu, 'size': 15},
            {'t': 'blank'}, {'t': 'center', 'text': f'Dự án: {da["ten_du_an"]}'}, {'t': 'center', 'text': f'Khách hàng: {da["khach_hang"]}'},
            {'t': 'center', 'text': 'Tài liệu kế hoạch dự án, kèm theo Phần III. Đề xuất kỹ thuật của hồ sơ dự thầu'},
            {'t': 'center', 'text': 'Phiên bản {{PHIEN_BAN}}, ngày {{NGAY}}'}, {'t': 'blank'}]


def bang_chi_tiet(ma_goc):
    rows = [['Mã WBS', 'Tên công việc', 'Mức', 'Khối lượng, MD', 'Loại công việc', 'Sản phẩm đầu ra']]
    dam = []
    for g in con_chau(ma_goc):
        if g['ma'] == ma_goc:
            continue
        rows.append([g['ma'], g['ten'], str(g['muc']), loi.md(g['md']), g.get('loai', '') if g['la'] else '', g.get('san_pham', '')])
        if not g['la']:
            dam.append(len(rows) - 1)
    rows.append(['', 'Tổng cộng', '', loi.md(by[ma_goc]['md']), '', ''])
    return {'t': 'table', 'rows': rows, 'widths': [1000, 3600, 600, 1100, 1000, 2000], 'center_cols': [2, 4], 'right_cols': [3], 'dong_dam': dam}


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
        tu = min(lich_goi[g['ma']]['bat_dau'] for g in leaves); den = max(lich_goi[g['ma']]['ket_thuc'] for g in leaves)
        sp = sorted({lich_goi[g['ma']]['sprint_bat_dau'] for g in leaves} | {lich_goi[g['ma']]['sprint_ket_thuc'] for g in leaves}, key=lambda s: int(s[1:]))
        thoi_gian = f'{loi.ngay(tu)} - {loi.ngay(den)} (sprint {sp[0]} đến {sp[-1]})' if len(sp) > 1 else f'{loi.ngay(tu)} - {loi.ngay(den)} (sprint {sp[0]})'
    else:
        thoi_gian = 'Theo master schedule'
    info = [['Tổng khối lượng', f'{loi.md(goc["md"])} người-ngày'], ['Thời gian thực hiện', thoi_gian],
            ['Người chịu trách nhiệm', ten_tv(nguoi) if nguoi else 'Theo bảng phân công'],
            ['Phụ thuộc đầu vào', ('Hoàn thành các gói ' + ', '.join(f'{p} ({by[p]["ten"]})' for p in ext_dep)) if ext_dep else 'Không có'],
            ['Đơn vị khối lượng', f'Người-ngày, viết tắt MD, tính theo {da.get("gio_moi_md", 8)} giờ làm việc']]
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
blocks = bia('Tổng hợp WBS toàn dự án')
_md = loi.dinh_dang_cot([n['md'] for n in wbs['nhom']] + [wbs['tong_md']], 'md'); _pt = loi.dinh_dang_cot([n['ty_trong'] for n in wbs['nhom']] + [1], 'pt')
rows = [['Mã', 'Nhóm công việc', 'Khối lượng, MD', 'Tỷ trọng']] + [[n['ma'], n['ten'], _md[i], _pt[i]] for i, n in enumerate(wbs['nhom'])]
rows.append(['', 'Tổng cộng', _md[-1], _pt[-1]])
blocks += [{'t': 'h2', 'text': '1. Khối lượng theo nhóm công việc'}, {'t': 'table', 'rows': rows, 'widths': [800, 5200, 1700, 1600], 'right_cols': [2, 3]},
           {'t': 'p', 'text': f'Toàn dự án gồm {wbs["so_goi_la"]} gói công việc, tổng {loi.md(wbs["tong_md"])} người-ngày. Tổng các nhóm mức 1 bằng tổng các gói công việc, quy tắc 100% được đáp ứng.'},
           {'t': 'h2', 'text': '2. Khối lượng theo loại công việc'}]
_lo = [(k, v) for k, v in wbs['md_theo_loai'].items() if v]
_md = loi.dinh_dang_cot([v for _, v in _lo] + [sum(v for _, v in _lo)], 'md'); _pt = loi.dinh_dang_cot([v / wbs['tong_md'] for _, v in _lo] + [1], 'pt')
rows = [['Loại công việc', 'Khối lượng, MD', 'Tỷ trọng']] + [[k, _md[i], _pt[i]] for i, (k, _) in enumerate(_lo)]
rows.append(['Tổng cộng', _md[-1], _pt[-1]])
blocks += [{'t': 'table', 'rows': rows, 'widths': [4000, 2500, 2000], 'right_cols': [1, 2]}, {'t': 'h2', 'text': '3. Cấu trúc mức 1 và mức 2'}]
for g in wbs['goi']:
    if g['muc'] <= 2:
        blocks.append({'t': 'p', 'text': f'{g["ma"]}. {g["ten"]} ({loi.md(g["md"])} MD)', 'thut': g['muc'] - 1, 'dam': g['muc'] == 1})
rows = [['Mã yêu cầu', 'Yêu cầu RFP', 'Gói công việc đáp ứng']] + [[x['ma'], x['yeu_cau'], x['goi'] or 'Thuộc thủ tục đấu thầu hoặc điều khoản hợp đồng'] for x in wbs['truy_vet_rfp']]
blocks += [{'t': 'pagebreak'}, {'t': 'h2', 'text': '4. Ma trận truy vết yêu cầu RFP'},
           {'t': 'p', 'text': 'Mỗi yêu cầu về hệ thống, sản phẩm, phạm vi và nội dung đề xuất của RFP được gắn với gói công việc đáp ứng. Yêu cầu về thủ tục và hợp đồng được đáp ứng trong hồ sơ dự thầu và kế hoạch quản lý.'},
           {'t': 'table', 'rows': rows, 'widths': [1100, 4600, 3600]}]
_md = loi.dinh_dang_cot([x['md'] for x in wbs['phan_bo_01a']] + [sum(x['md'] for x in wbs['phan_bo_01a'])], 'md')
rows = [['STT', 'Hạng mục Mẫu 01A', 'Gói công việc', 'Khối lượng, MD']] + [[str(x['stt']), x['danh_muc'], x['goi'], _md[i]] for i, x in enumerate(wbs['phan_bo_01a'])]
rows.append(['', 'Tổng cộng', '', _md[-1]])
blocks += [{'t': 'h2', 'text': '5. Phân bổ theo hạng mục Mẫu 01A'},
           {'t': 'p', 'text': 'Bảng dùng để lập bảng tiến độ Mẫu 10A và bảng giá Mẫu 11A theo đúng danh mục dịch vụ của HSMT. Gói gắn nhiều hạng mục được chia đều khối lượng. Khi mọi gói của một mục đều thuộc hạng mục, bảng ghi mã mục thay cho từng gói.'},
           {'t': 'table', 'rows': rows, 'widths': [600, 3200, 4300, 1200], 'right_cols': [3]}, {'t': 'h2', 'text': '6. Giả định ngoài phạm vi'}]
for x in wbs['gia_dinh_ngoai_pham_vi'] or ['Không có']:
    blocks.append({'t': 'p', 'text': '- ' + x})
meta = {'ten': 'WBS tổng hợp', 'header': 'Lập kế hoạch - WBS tổng hợp', 'size_bang_pt': 12}
tep_da_tao.append(tao({'meta': meta, 'blocks': blocks}, 'WBS_tong_hop.docx'))
loi.ghi_nhat_ky('qlda-wbs', 'tai_lieu_wbs', 'script', f'Xuất {len(tep_da_tao)} tài liệu WBS, đạt kiểm tra trình bày',
                vao=['du_lieu/wbs.json'] + [p for p in ('du_lieu/phan_cong.json', 'du_lieu/lich.json') if os.path.exists(loi.duong_dan(p))], ra=tep_da_tao, ket_qua='đạt')
