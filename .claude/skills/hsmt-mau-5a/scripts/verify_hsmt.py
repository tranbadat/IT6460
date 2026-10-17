"""Kiểm tra độc lập file HSMT (vai Kiểm tra, lớp A).

Dùng: python3 verify_hsmt.py <HSMT.docx> --lam-viec <thu_muc_lam_viec> [--mau Mau_5A.docx] [--json bao_cao.json]
Thư mục làm việc cần có: mau5a_cau_truc.json, mau5a_fixed.json, rfp_yeu_cau.json, gia_tri_tinh.json, tham_so_chu_dau_tu.json.
Chỉ đọc file Word đầu ra và các nguồn chuẩn. Không đọc khung, bản soạn hay nội dung trung gian của bên tạo.
Mọi giá trị kỳ vọng lấy từ nguồn chuẩn, không ghi cứng trong script.
Mã thoát: 0 đạt, 1 còn lỗi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse, json, os, re, sys, zipfile
import docx

ap = argparse.ArgumentParser()
ap.add_argument('hsmt'); ap.add_argument('--lam-viec', required=True); ap.add_argument('--mau'); ap.add_argument('--json')
a = ap.parse_args()
J = lambda n: json.load(open(os.path.join(a.lam_viec, n), encoding='utf-8'))
ct, fixed, rfp, gv, ts = J('mau5a_cau_truc.json'), J('mau5a_fixed.json'), J('rfp_yeu_cau.json'), J('gia_tri_tinh.json'), J('tham_so_chu_dau_tu.json')

x = zipfile.ZipFile(a.hsmt).read('word/document.xml').decode('utf-8')
t = ' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', x))
d = docx.Document(a.hsmt)
N = lambda s: re.sub(r'\s+', ' ', s).strip()
norm = lambda s: re.sub('[\u2013\u2014]', '-', re.sub(r'\s+', '', s))
findings = []

# Phần do bên lập soạn (bỏ Chương I, Chương VI, Mục 1 Chương III là nguyên văn mẫu)
FIXED_FIRST = ('1. Phạm vi gói thầu', '1. Định nghĩa')
own, in_muc1 = [], False
for p in d.paragraphs:
    s0 = p.text.strip()
    if s0.startswith('Mục 1. Đánh giá tính hợp lệ'):
        in_muc1 = True; own.append(s0); continue
    if s0.startswith('Mục 2. Tiêu chuẩn đánh giá về năng lực'):
        in_muc1 = False
    if not in_muc1:
        own.append(s0)
tables = []
for tb in d.tables:
    rows = [[N(c.text) for c in r.cells] for r in tb.rows]
    tables.append(rows)
    if not tb.rows[0].cells[0].text.strip().startswith(FIXED_FIRST):
        own += [c for r in rows for c in r]
t_own = ' '.join(own)
t_own_low = t_own.lower()


def add(ma, nhom, mo_ta, vi_tri='', cach_sua='can_nguoi_dung', de_xuat='', muc_do='loi'):
    findings.append(dict(ma=ma, muc_do=muc_do, nhom=nhom, vi_tri=vi_tri, mo_ta=mo_ta, cach_sua=cach_sua, de_xuat=de_xuat))


def ctx(m, w=50, src=None):
    src = t if src is None else src
    return src[max(0, m.start() - w): m.end() + w]


def find_table(pred):
    for rows in tables:
        try:
            if pred(rows): return rows
        except Exception: pass
    return None


# 1. Pháp lý
for m in re.finditer(r'24/2024', t):
    add('PL01', 'phap_ly', 'Viện dẫn Nghị định 24/2024 đã hết hiệu lực', ctx(m), 'tu_dong', 'Thay bằng Nghị định số 214/2025/NĐ-CP')
if 'đặt cọc' in t_own: add('PL02', 'phap_ly', 'Đấu thầu qua mạng không dùng đặt cọc')
if re.search(r'\d+ bản (in|giấy)|bản in', t_own): add('PL03', 'phap_ly', 'Mẫu 5A chỉ cho nộp một bộ E-HSDT qua Hệ thống')
for key in ('luat', 'nghi_dinh', 'thong_tu'):
    so = re.search(r'số (\S+)', ts['can_cu_phap_ly'][key]).group(1)
    if so not in t: add('PL04', 'phap_ly', 'Thiếu căn cứ ' + so)

# 2. Chỗ giữ chỗ và dấu vết của mẫu chưa điền
for pat, mo in ((r'<<SOẠN', 'Còn chỗ giữ chỗ chưa soạn'), (r'_{3,}', 'Còn ký hiệu ___ của mẫu'), (r'\[(ghi|nêu|Hệ thống)', 'Còn hướng dẫn trong ngoặc vuông của mẫu'), (r'\w\(\d\)', 'Còn ký hiệu chú thích (n) của mẫu')):
    for m in re.finditer(pat, t_own):
        add('CT00', 'cau_truc', mo, ctx(m, 40, t_own))

# 3. Cấu trúc theo Mẫu 5A
for key in ['Chương I. Chỉ dẫn nhà thầu', 'Chương II. Bảng dữ liệu đấu thầu', 'Chương III. Tiêu chuẩn đánh giá E-HSDT',
            'Chương IV. Biểu mẫu mời thầu và dự thầu', 'Chương V. Yêu cầu về kỹ thuật', 'Chương VI. Điều kiện chung của hợp đồng',
            'Chương VII. Điều kiện cụ thể của hợp đồng', 'Phần 4. Biểu mẫu hợp đồng', 'Bảng số 01', 'Bảng số 02', 'Mẫu số 01A',
            'Mục 3. Tiêu chuẩn đánh giá về kỹ thuật', 'Mục 4. Tiêu chuẩn đánh giá về tài chính', 'Mục 5. Phương án kỹ thuật thay thế', 'Mục 6. Trường hợp gói thầu chia']:
    if key not in t: add('CT01', 'cau_truc', 'Thiếu ' + key)
firsts = {norm(r[0]) for rows in tables for r in rows if r}
for it in ct['e_bdl'] + ct['e_dkct']:
    if norm(it['ma']) not in firsts: add('CT02', 'cau_truc', 'Thiếu mục so với Mẫu 5A: ' + it['ma'])
for r in ct['chuong4_bieu_mau']:
    if r and r[0].isdigit():
        ma = re.match(r'(Mẫu số \w+)\.', r[1]).group(1)
        if ma + '.' not in t: add('CT03', 'cau_truc', 'Danh mục Chương IV thiếu ' + ma)
for f in ct['phan4']:
    if f['ma'] + '.' not in t: add('CT03', 'cau_truc', 'Phần 4 thiếu ' + f['ma'])
# Bảng 01: các cột cố định của mẫu (nhà thầu độc lập, liên danh, tài liệu) phải giữ nguyên
b01_mau = [r for r in ct['bang01'] if r and r[0] in ('1', '2', '3', '4')]
b01 = find_table(lambda rows: rows[0][0] == 'TT' and 'Liên danh' in ' '.join(rows[0]))
if not b01:
    add('CT04', 'cau_truc', 'Không tìm thấy Bảng số 01')
else:
    for rm in b01_mau:
        rr = next((r for r in b01 if r[0] == rm[0]), None)
        if not rr: add('CT04', 'cau_truc', f'Bảng số 01 thiếu dòng {rm[0]}'); continue
        if rr[3:7] != rm[3:7]:
            add('CT05', 'cau_truc', f'Bảng số 01 dòng {rm[0]} lệch cột cố định của mẫu: {rr[3:7]} thay vì {rm[3:7]}', rm[1])

# 4. Nguyên văn
have = norm(t)
for name, key in (('Chương I', 'c1'), ('Chương VI', 'c6')):
    miss = [s for l, r in fixed[key] for s in l + r if norm(s) not in have]
    if miss: add('NV01', 'nguyen_van', f'{name} lệch nguyên văn mẫu ở {len(miss)} đoạn', miss[0][:120], 'tu_dong', 'Chạy lại build_hsmt.py với mau5a_fixed.json')
miss = [s for s in fixed['muc1'] if norm(s) not in have]
if miss: add('NV01', 'nguyen_van', f'Mục 1 Chương III lệch nguyên văn mẫu ở {len(miss)} đoạn', miss[0][:120], 'tu_dong')

# 5. Số liệu theo giá trị đã tính và tham số
L, T, NL, TH, HD, KT = gv['lich'], gv['tien'], gv['nang_luc'], gv['thoi_han'], gv['hop_dong'], gv['ky_thuat']
for k in ('phat_hanh', 'dong_thau', 'han_nha_thau_de_nghi_lam_ro', 'han_chu_dau_tu_tra_loi', 'hop_dong_hieu_luc_du_kien', 'cut_over'):
    if L[k] not in t_own: add('SL01', 'so_lieu', f'Thiếu mốc {k} = {L[k]}')
if L.get('hoi_nghi_tien_dau_thau') and L['hoi_nghi_tien_dau_thau']['ngay'] not in t_own: add('SL01', 'so_lieu', 'Thiếu ngày hội nghị tiền đấu thầu')
for k, v in T.items():
    if v + ' đồng' not in t_own: add('SL02', 'so_lieu', f'Không tìm thấy {k} = {v} đồng')
for k in ('moc_lich_su_hop_dong', 'moc_hop_dong_tuong_tu'):
    if 'Từ ngày ' + NL[k] not in t_own: add('SL03', 'so_lieu', f'Mốc {k} phải là {NL[k]}')
for m in re.finditer(r'Từ ngày (\d{2} tháng \d{2} năm \d{4}) đến thời điểm đóng thầu', t_own):
    if m.group(1) not in (NL['moc_lich_su_hop_dong'], NL['moc_hop_dong_tuong_tu']):
        add('SL03', 'so_lieu', 'Mốc năng lực không khớp giá trị đã tính', m.group(0))
if f"≥ {TH['hieu_luc_hsdt_ngay']} ngày" not in t_own: add('SL04', 'so_lieu', 'Hiệu lực E-HSDT không khớp')
if f"≥ {TH['hieu_luc_bao_dam_du_thau_ngay']} ngày" not in t_own: add('SL04', 'so_lieu', 'Hiệu lực bảo đảm dự thầu không khớp')
if TH['hieu_luc_bao_dam_thuc_hien_den'] not in t_own: add('SL04', 'so_lieu', 'Hiệu lực bảo đảm thực hiện hợp đồng không khớp')
if f"Giá trị bảo đảm thực hiện hợp đồng: {HD['bao_dam_thuc_hien_phan_tram']}%" not in t_own: add('SL05', 'so_lieu', 'Bảo đảm thực hiện hợp đồng không khớp tham số')
if f"{HD['nha_thau_phu_toi_da_phan_tram']}% giá dự thầu" not in t_own: add('SL05', 'so_lieu', 'Tỷ lệ nhà thầu phụ không khớp tham số')
if HD['tam_ung_phan_tram'] and f"Tạm ứng: {HD['tam_ung_phan_tram']}%" not in t_own: add('SL06', 'so_lieu', 'Mục 12.1 không khớp tỷ lệ tạm ứng')
m = re.search(r'E-ĐKC 13\.1(.*?)E-ĐKC 13\.2', t_own)
if m:
    pct = [int(v) for v in re.findall(r'Đợt \d+: (\d+)%', m.group(1))]
    ky_vong = [x['phan_tram'] for x in HD['thanh_toan']]
    if pct != ky_vong: add('SL06', 'so_lieu', f'Các đợt thanh toán {pct} khác tham số {ky_vong}')
else:
    add('SL06', 'so_lieu', 'Không tìm thấy Mục 13.1 E-ĐKCT')
b02 = find_table(lambda rows: rows[0][:2] == ['STT', 'Vị trí công việc'])
if b02:
    have02 = [(r[1], r[2]) for r in b02[1:]]
    want02 = [(x['vi_tri'], str(x['so_luong'])) for x in ts['nhan_su_chu_chot']]
    if have02 != want02: add('SL07', 'so_lieu', f'Bảng số 02 {have02} khác tham số {want02}')
bkt = find_table(lambda rows: rows[0][:2] == ['STT', 'Tiêu chí tổng quát'])
if bkt:
    rows = [r for r in bkt[1:] if r[0]]
    if [int(r[2]) for r in rows] != KT['trong_so'] or [int(r[3]) for r in rows] != KT['diem_toi_thieu']:
        add('SL08', 'so_lieu', 'Điểm tiêu chí kỹ thuật không khớp giá trị đã tính')
    if any(re.search(r'giá dự thầu|chi phí ước tính', r[1], re.I) for r in rows):
        add('SL09', 'so_lieu', 'Tiêu chí kỹ thuật không được chấm giá')

# 6. Yêu cầu RFP
for yc in rfp['yeu_cau']:
    thieu = [k for k in yc['tu_khoa_kiem_tra'] if k.lower() not in t_own_low]
    if thieu:
        add('RF01', 'rfp', f"Yêu cầu {yc['ma']} chưa thể hiện: thiếu {thieu}", yc['nguyen_van'][:100], 'can_nguoi_dung', 'Soạn bổ sung tại ' + yc['vi_tri_hsmt'])
# Sản phẩm bàn giao của RFP được kiểm tra qua từ khóa của các yêu cầu nhóm san_pham.

# 7. Định dạng
if re.search(r'<w:b/>|<w:b w:val="(1|true)"/>', x): add('DD01', 'dinh_dang', 'Có chữ in đậm', cach_sua='tu_dong', de_xuat='Chạy lại build_hsmt.py')
if re.search(r'<w:caps/>|<w:caps w:val="(1|true)"/>', x): add('DD02', 'dinh_dang', 'Có chữ viết hoa toàn bộ', cach_sua='tu_dong')
for m in re.finditer('[\u2013\u2014]', t_own): add('DD03', 'dinh_dang', 'Có gạch dài', ctx(m, 30, t_own), 'tu_dong', 'Đổi thành gạch ngang đơn')
fonts = set(re.findall(r'w:ascii="([^"]+)"', x)) - {'Times New Roman'}
if fonts: add('DD04', 'dinh_dang', 'Có font khác Times New Roman: ' + ', '.join(fonts), cach_sua='tu_dong')
for m in re.finditer(r'[“”"]', t_own): add('DD05', 'dinh_dang', 'Có ngoặc kép, kiểm tra có dùng để nhấn mạnh không', ctx(m, 30, t_own), muc_do='canh_bao')

# 8. Văn phong
STYLE = {r'(?<!chủ )\b[Cc]hốt\b': None, r'\bxong\b': None, r'chạy được': 'hoạt động được', r'dùng được': 'có thể sử dụng',
         r'lỗi chặn': 'lỗi nghiêm trọng làm gián đoạn vận hành', r'đóng lỗi': 'khắc phục dứt điểm lỗi',
         r'go-live': 'đưa hệ thống vào vận hành', r'\brồi\b': None, r'dưới đây là': None, r'[→✓✔•]': None}
for pat, rep in STYLE.items():
    for m in re.finditer(pat, t_own):
        add('VP01', 'van_phong', 'Từ hoặc ký hiệu không phù hợp văn phong: ' + m.group(0), ctx(m, 40, t_own),
            'tu_dong' if rep else 'can_nguoi_dung', rep or 'Chọn cách diễn đạt trang trọng theo ngữ cảnh')
for s in own:
    if s.count(';') > 3:
        add('VP02', 'van_phong', f'Câu có {s.count(";")} dấu chấm phẩy', s[:100], 'can_nguoi_dung', 'Tách câu hoặc dùng từ nối', 'canh_bao')

loi = [f for f in findings if f['muc_do'] == 'loi']
report = {'file': os.path.basename(a.hsmt), 'ket_luan': 'dat' if not loi else 'chua_dat', 'so_loi': len(loi),
          'so_canh_bao': len(findings) - len(loi), 'phat_hien': findings}
if a.json:
    json.dump(report, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for f in findings:
    print(f"[{f['muc_do']}] {f['ma']} {f['nhom']}: {f['mo_ta']} | {f['vi_tri'][:90]} | {f['cach_sua']}")
print(f"Kết luận: {report['ket_luan']} ({report['so_loi']} lỗi, {report['so_canh_bao']} cảnh báo)")
sys.exit(0 if not loi else 1)
