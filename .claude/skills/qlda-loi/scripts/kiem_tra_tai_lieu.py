"""Kiểm tra độc lập một tài liệu Word (vai Kiểm tra, lớp A), dùng chung cho mọi skill.

Dùng: python kiem_tra_tai_lieu.py <dac_ta.json> <tai_lieu.docx> [--json bao_cao.json]
Chỉ đọc file Word, đặc tả và dữ liệu nguồn chuẩn khai báo trong đặc tả. Không đọc khung hay bản soạn.
Mã thoát: 0 đạt, 1 còn lỗi.

Đặc tả, khóa kiem_tra:
  gia_tri: [{"mo_ta":..., "bt": "{lich#cut_over|ngay}"}]          giá trị phải có trong tài liệu
  ma_phai_co: [{"nguon": "rr#danh_sach", "truong": "ma", "loc": {...}, "mo_ta": ...}]   mọi mã phải được nhắc
  tu_khoa: ["cụm từ" hoặc tham chiếu]                                   cụm từ phải có
  cam: ["cụm từ không được xuất hiện"]
  cho_phep_dam: true|false                                              cho phép in đậm (mục cha WBS)
  doc_hieu: [tiêu chí cho lớp B]                                        không kiểm ở đây
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse
import json
import os
import re
import sys
import zipfile

import docx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loi  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('dac_ta'); ap.add_argument('docx'); ap.add_argument('--json')
a = ap.parse_args()
spec = json.load(open(a.dac_ta, encoding='utf-8'))
kt = spec.get('kiem_tra', {})
nguon_paths = dict(spec.get('nguon', {})); nguon_paths.setdefault('da', 'dau_vao/du_an.json')
nguon = loi.nap_nguon(nguon_paths)
G = lambda s: loi.giai_bieu_thuc(s, nguon)

x = zipfile.ZipFile(a.docx).read('word/document.xml').decode('utf-8')
d = docx.Document(a.docx)
N = lambda s: re.sub(r'\s+', ' ', s).strip()
paras = [N(p.text) for p in d.paragraphs]
heads = [N(p.text) for p in d.paragraphs if p.style is not None and p.style.name.startswith('Heading')]  # không tính dòng mục lục
cells = [N(c.text) for tb in d.tables for r in tb.rows for c in r.cells]
t = ' '.join(paras + cells)
t_low = t.lower()
findings = []


def add(ma, nhom, mo_ta, vi_tri='', cach_sua='can_nguoi_dung', de_xuat='', muc_do='loi'):
    findings.append(dict(ma=ma, muc_do=muc_do, nhom=nhom, vi_tri=vi_tri[:160], mo_ta=mo_ta, cach_sua=cach_sua, de_xuat=de_xuat))


def ctx(m, w=50):
    return t[max(0, m.start() - w): m.end() + w]


# 1. Dấu vết chưa hoàn thiện
for pat, mo in ((r'<<SOẠN', 'Còn chỗ giữ chỗ chưa soạn'), (r'\{[a-z_0-9]+#[^}]*\}', 'Còn tham chiếu dữ liệu chưa giải'),
                (r'\{\{[A-Z_]+\}\}', 'Còn biến chưa thay (phiên bản, ngày)'), (r'_{3,}', 'Còn ký hiệu ___'),
                (r'\[(ghi|nêu|điền)', 'Còn hướng dẫn trong ngoặc vuông'), (r'(?i)\b(TODO|TBD|lorem)\b', 'Còn ghi chú nháp')):
    for m in re.finditer(pat, t):
        add('CT00', 'cau_truc', mo, ctx(m), 'can_nguoi_dung', 'Soạn bổ sung hoặc kiểm tra dữ liệu nguồn')

# 2. Tiêu đề theo đặc tả
for kb in spec.get('khoi', []):
    for lv in ('h1', 'h2', 'h3'):
        if lv in kb:
            tieu_de = N(G(kb[lv]))
            if tieu_de not in heads:
                add('CT01', 'cau_truc', 'Thiếu tiêu đề mục: ' + tieu_de, '', 'tu_dong', 'Chạy lại lap_khung.py và build_docx.py')

# 3. Giá trị phải khớp dữ liệu
for g in kt.get('gia_tri', []):
    v = N(G(g['bt']))
    if '#' in v and '{' in v:
        add('GT00', 'so_lieu', 'Không giải được tham chiếu kiểm tra: ' + g['bt'], muc_do='canh_bao'); continue
    if v.lower() not in t_low:
        add('GT01', 'so_lieu', f'{g["mo_ta"]}: không tìm thấy "{v}" (giá trị theo dữ liệu nguồn)', '', 'can_nguoi_dung',
            'Dùng tham chiếu dữ liệu trong bản soạn thay cho số viết tay, rồi tạo lại')

# 4. Mã phải được nhắc
for mp in kt.get('ma_phai_co', []):
    bd, path = mp['nguon'].split('#', 1)
    try:
        lst = loi.lay(nguon[bd], path)
    except Exception:
        add('MA00', 'cau_truc', 'Không đọc được nguồn ' + mp['nguon'], muc_do='canh_bao'); continue
    for r in lst:
        if mp.get('loc') and any(r.get(k) not in (v if isinstance(v, list) else [v]) for k, v in mp['loc'].items()):
            continue
        val = str(r.get(mp['truong'], ''))
        if val and val not in t:
            add('MA01', 'cau_truc', f'{mp.get("mo_ta", "Mã")}: thiếu {val}', val)

# 5. Cụm từ bắt buộc, cụm từ cấm
for kw in kt.get('tu_khoa', []):
    v = N(G(kw))
    if v.lower() not in t_low:
        add('TK01', 'noi_dung', f'Thiếu nội dung bắt buộc: "{v}"')
for kw in kt.get('cam', []):
    for m in re.finditer(re.escape(G(kw)), t, re.I):
        add('TK02', 'noi_dung', f'Có nội dung không được dùng: "{kw}"', ctx(m))

# 6. Định dạng
if not kt.get('cho_phep_dam') and re.search(r'<w:b/>|<w:b w:val="(1|true)"/>', x):
    add('DD01', 'dinh_dang', 'Có chữ in đậm', cach_sua='tu_dong', de_xuat='Chạy lại build_docx.py')
if re.search(r'<w:caps/>|<w:caps w:val="(1|true)"/>', x):
    add('DD02', 'dinh_dang', 'Có chữ viết hoa toàn bộ', cach_sua='tu_dong')
for m in re.finditer('[–—]', t):
    add('DD03', 'dinh_dang', 'Có gạch dài', ctx(m, 30), 'tu_dong', 'Đổi thành gạch ngang đơn')
fonts = set(re.findall(r'w:ascii="([^"]+)"', x)) - {'Times New Roman'}
if fonts:
    add('DD04', 'dinh_dang', 'Có font khác Times New Roman: ' + ', '.join(fonts), cach_sua='tu_dong')
for m in re.finditer(r'[“”"]', t):
    add('DD05', 'dinh_dang', 'Có ngoặc kép, kiểm tra có dùng để nhấn mạnh không', ctx(m, 30), muc_do='canh_bao')

# 7. Văn phong (quy tắc trong references/van_phong.md)
VP = json.load(open(os.path.join(loi.THU_MUC_LOI, 'references', 'van_phong.json'), encoding='utf-8'))
for item in VP['tu_thay_the']:
    for m in re.finditer(item['mau'], t):
        add('VP01', 'van_phong', 'Từ không phù hợp văn phong: ' + m.group(0), ctx(m, 40), 'tu_dong', item['thay'])
for item in VP['tu_can_xem']:
    for m in re.finditer(item['mau'], t):
        add('VP02', 'van_phong', 'Cách diễn đạt cần xem lại: ' + m.group(0), ctx(m, 40), 'can_nguoi_dung', item.get('goi_y', ''), 'canh_bao')
for s in paras + cells:
    if s.count(';') > VP.get('cham_phay_toi_da', 3):
        add('VP03', 'van_phong', f'Câu có {s.count(";")} dấu chấm phẩy', s[:120], 'can_nguoi_dung', 'Tách câu hoặc dùng từ nối', 'canh_bao')

# 8. Tài liệu có dùng đầu vào mới nhất không
try:
    reg = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})
    lst = reg['tai_lieu'].get(loi.tuong_doi(a.docx), [])
    if lst:
        sd = loi.so_do()
        for nut, h in lst[-1].get('vao', {}).items():
            p = loi.duong_dan_nut(sd, nut)
            vao_hien = next((x['vao'] for x in sd['buoc'] if x['id'] == lst[-1].get('buoc')), [])
            if p and nut in vao_hien and nut not in loi.nut_bien_dong(sd) and loi.bam_nut(sd, nut) != h:
                add('PB01', 'phien_ban', f'Đầu vào {nut} ({p}) đã thay đổi sau lần tạo tài liệu', '', 'tu_dong', 'Chạy lại bước để cập nhật', 'canh_bao')
except Exception:
    pass

loi_ = [f for f in findings if f['muc_do'] == 'loi']
report = {'tai_lieu': loi.tuong_doi(a.docx), 'dac_ta': spec['id'], 'thoi_gian': loi.bay_gio(),
          'ket_luan': 'dat' if not loi_ else 'chua_dat', 'so_loi': len(loi_), 'so_canh_bao': len(findings) - len(loi_),
          'phat_hien': findings, 'tieu_chi_doc_hieu': kt.get('doc_hieu', [])}
if a.json:
    loi.ghi_json(a.json, report)
for f in findings:
    print(f"[{f['muc_do']}] {f['ma']} {f['nhom']}: {f['mo_ta']} | {f['vi_tri'][:80]}")
print(f"Kết luận: {report['ket_luan']} ({report['so_loi']} lỗi, {report['so_canh_bao']} cảnh báo)")
sys.exit(0 if not loi_ else 1)
