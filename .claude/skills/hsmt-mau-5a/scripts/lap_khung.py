"""Bước 4. Lập khung HSMT.

Dùng: python3 lap_khung.py <mau5a_cau_truc.json> <tham_so_chu_dau_tu.json> <rfp_yeu_cau.json> <gia_tri_tinh.json> <hsmt_khung.json>

Khung có đủ cấu trúc theo Mẫu 5A. Các mục cơ học (tên, số liệu, mục Hệ thống trích xuất, cột cố định của mẫu)
được điền sẵn. Các mục cần diễn đạt nội dung từ RFP để dạng <<SOẠN:ID>> và mô tả trong khóa "can_soan"
(hướng dẫn của mẫu, nguồn dữ liệu, dạng kết quả). Agent Soạn thảo chỉ viết file ban_soan.json cho các ID này.
Mục 3 Chương III có bảng tiêu chí chi tiết (TIEU_CHI_CHI_TIET, ràng buộc trong khóa rang_buoc). Chương V mục 3.5 và
E-ĐKC 15 lập theo tham số; tham số bắt buộc còn trống thì giữ câu mẫu kèm dấu [Chủ đầu tư quyết định ...] (quy_uoc.py).
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quy_uoc import BEN, DOAN_2_2_C, DOAN_2_2_NHAN_SU, HA_TANG, KIEM_THU_VAN_HANH, THAY_DOI_HE_THONG, dau_cho, lay  # noqa: E402

ct = json.load(open(sys.argv[1], encoding='utf-8'))
ts = json.load(open(sys.argv[2], encoding='utf-8'))
rfp = json.load(open(sys.argv[3], encoding='utf-8'))
gv = json.load(open(sys.argv[4], encoding='utf-8'))
out = sys.argv[5]

cdt, gt, cs, lich = ts['chu_dau_tu'], ts['goi_thau'], ts['chinh_sach'], gv['lich']
tien, nl, hd, th, kt = gv['tien'], gv['nang_luc'], gv['hop_dong'], gv['thoi_han'], gv['ky_thuat']
lh = rfp['lien_he']
CDT, GOI, DUAN = cdt['ten'], gt['ten'], gt['du_an']
EMAIL = lh['email']
NGUOI_LH = f"ông {lh['ho_ten']}, Phòng Kế hoạch" if 'Planning' in lh.get('bo_phan', '') else f"{lh['ho_ten']}, {lh.get('bo_phan', '')}"
can_soan = {}
so_vn = lambda v: str(v).replace('.', ',')


def lh(k, mo_ta):
    """Thông tin liên hệ của Chủ đầu tư từ tham số chu_dau_tu, thiếu thì ghi dấu chờ."""
    v = cdt.get(k)
    return str(v).strip() if v not in (None, '') else dau_cho(mo_ta)


def so_quoc_te(s):
    # Mục 4.1 E-ĐKCT yêu cầu số có mã quốc gia: số trong nước bắt đầu bằng 0 đổi sang +84
    return '+84 ' + s[1:] if s.startswith('0') else s


DIA_CHI, DIEN_THOAI, FAX = lh('dia_chi', 'địa chỉ cụ thể'), lh('dien_thoai', 'điện thoại'), lh('fax', 'fax')
GIA_HAN = cs.get('gia_han_khi_chu_dau_tu_cung_cap_cham')  # lùi mốc khi Chủ đầu tư cung cấp chậm (E-ĐKC 18 (e), mục 3.5)


def S(id_, huong_dan, nguon, dang='doan', mau_goc='', rang_buoc=None):
    can_soan[id_] = {'huong_dan': huong_dan, 'nguon': nguon, 'dang': dang, 'mau_goc': mau_goc}
    if rang_buoc:
        can_soan[id_]['rang_buoc'] = rang_buoc
    return f'<<SOẠN:{id_}>>'


def mau(ma, bang='e_bdl'):
    for x in ct[bang]:
        if re.sub(r'\s', '', x['ma']) == re.sub(r'\s', '', ma):
            return x['noi_dung_mau']
    return ''


B = []
center = lambda text, size=13: B.append({'t': 'center', 'text': text, 'size': size})
h1 = lambda text: B.append({'t': 'h1', 'text': text})
h2 = lambda text: B.append({'t': 'h2', 'text': text})
p = lambda text: B.append({'t': 'p', 'text': text})
br = lambda: B.append({'t': 'pagebreak'})
table = lambda rows, widths, center_cols=(): B.append({'t': 'table', 'rows': rows, 'widths': widths, 'center_cols': list(center_cols)})

# ---------------- Bìa
center('Mẫu số 5A', 14)
center('Hồ sơ mời thầu', 18)
center('Dịch vụ phi tư vấn qua mạng', 15)
center('Một giai đoạn một túi hồ sơ', 15)
center('(Ban hành kèm theo Thông tư số 79/2025/TT-BTC ngày 04 tháng 8 năm 2025 của Bộ trưởng Bộ Tài chính)')
B.append({'t': 'blank'})
center('Chủ đầu tư: ' + CDT, 14)
bia_val = ['Theo E-TBMT trên Hệ thống', GOI, DUAN, lich['phat_hanh'], f'Quyết định phê duyệt E-HSMT của {CDT}, theo E-TBMT trên Hệ thống']
table([[ct['bia'][i], bia_val[i]] for i in range(len(ct['bia']))], [4300, 5300])
B.append({'t': 'blank'})
center(f"{cdt['dia_diem_ban_hanh']}, {gv['nam']}")
br()

# ---------------- Thông tin chính E-TBMT
cc = ts['can_cu_phap_ly']
hn = lich['hoi_nghi_tien_dau_thau']
center('Thông tin chính của E-TBMT', 15)
table([
    ['Nội dung', 'Thông tin'],
    ['Chủ đầu tư', CDT], ['Tên gói thầu', GOI], ['Dự án', DUAN],
    ['Căn cứ áp dụng', ('Chủ đầu tư sử dụng vốn tự có và lựa chọn áp dụng ' if gt['chu_dau_tu_tu_lua_chon_ap_dung_luat'] else 'Áp dụng ') + f"{cc['luat']}, {cc['nghi_dinh']} và {cc['thong_tu']}"],
    ['Hình thức lựa chọn nhà thầu', gt['hinh_thuc'][0].upper() + gt['hinh_thuc'][1:]],
    ['Phương thức lựa chọn nhà thầu', gt['phuong_thuc'][0].upper() + gt['phuong_thuc'][1:]],
    ['Loại hợp đồng', gt['loai_hop_dong'][0].upper() + gt['loai_hop_dong'][1:]],
    ['Giá gói thầu', f"{tien['gia_goi_thau']} đồng, đã bao gồm các loại thuế, phí và lệ phí theo quy định (nếu có)"],
    ['Thời gian thực hiện hợp đồng', f"Từ ngày hợp đồng có hiệu lực, dự kiến ngày {lich['hop_dong_hieu_luc_du_kien']}, đến hết ngày {lich['cut_over']}, tương đương khoảng {lich['so_tuan_thuc_hien']} tuần"],
    ['Phát hành E-HSMT', f"Ngày {lich['phat_hanh']}, phát hành miễn phí trên Hệ thống"],
    ['Thời gian chuẩn bị E-HSDT', f"{lich['so_ngay_chuan_bi_hsdt']} ngày, kể từ ngày phát hành E-HSMT đến thời điểm đóng thầu"],
    ['Làm rõ E-HSMT', f"Nhà thầu gửi đề nghị làm rõ qua Hệ thống chậm nhất ngày {lich['han_nha_thau_de_nghi_lam_ro']}. Chủ đầu tư trả lời trên Hệ thống chậm nhất ngày {lich['han_chu_dau_tu_tra_loi']}"],
    ['Hội nghị tiền đấu thầu', f"{hn['gio']}, ngày {hn['ngay']}, tại {S('DIA_DIEM_HOI_NGHI', 'Địa điểm tổ chức hội nghị tiền đấu thầu, lấy theo nơi RFP tổ chức thuyết trình. Chỉ ghi địa điểm, ví dụ dạng: phòng họp ..., trụ sở ...', ['rfp_yeu_cau.json: dia_diem'])}" if hn else 'Không tổ chức'],
    ['Thời điểm đóng thầu', f"{lich['gio_dong_thau']}, ngày {lich['dong_thau']}"],
    ['Thời điểm mở thầu', f"{lich['gio_mo_thau']}, ngày {lich['dong_thau']}"],
    ['Hiệu lực E-HSDT', f"≥ {th['hieu_luc_hsdt_ngay']} ngày, kể từ ngày có thời điểm đóng thầu"],
    ['Bảo đảm dự thầu', f"{tien['bao_dam_du_thau']} đồng, bằng {str(cs['ty_le_bao_dam_du_thau_phan_tram']).replace('.', ',')}% giá gói thầu. Hiệu lực ≥ {th['hieu_luc_bao_dam_du_thau_ngay']} ngày kể từ ngày có thời điểm đóng thầu"],
    ['Mốc đưa hệ thống vào vận hành (cut over)', f"Ngày {lich['cut_over']}"],
    ['Đầu mối liên hệ', f"{NGUOI_LH}, email {EMAIL}"],
], [3300, 6300])
br()

# ---------------- Mục lục, mô tả tóm tắt
center('Mục lục', 15)
# Trường mục lục có số trang, cập nhật khi mở tệp trong Word. Danh sách dưới là nội dung tạm trước khi cập nhật.
B.append({'t': 'toc', 'muc': ['Mô tả tóm tắt', 'Phần 1. Thủ tục đấu thầu', '    Chương I. Chỉ dẫn nhà thầu', '    Chương II. Bảng dữ liệu đấu thầu',
                              '    Chương III. Tiêu chuẩn đánh giá E-HSDT', '    Chương IV. Biểu mẫu mời thầu và dự thầu', 'Phần 2. Yêu cầu về kỹ thuật',
                              '    Chương V. Yêu cầu về kỹ thuật', 'Phần 3A. Điều kiện hợp đồng', '    Chương VI. Điều kiện chung của hợp đồng',
                              '    Chương VII. Điều kiện cụ thể của hợp đồng', 'Phần 4. Biểu mẫu hợp đồng']})
p('Phần 3B (thỏa thuận khung) và phụ lục các ví dụ của Mẫu số 5A không áp dụng cho gói thầu này.')
h2('Mô tả tóm tắt')
p('Phần 1. Thủ tục đấu thầu. Chương I cung cấp thông tin giúp nhà thầu chuẩn bị E-HSDT, được sử dụng mà không sửa đổi. Chương II quy định cụ thể nội dung của Chương I khi áp dụng cho gói thầu này. Chương III gồm các tiêu chuẩn đánh giá E-HSDT. Chương IV gồm các biểu mẫu mà Chủ đầu tư và nhà thầu hoàn chỉnh trên Hệ thống.')
p('Phần 2. Yêu cầu về kỹ thuật. Chương V nêu các yêu cầu về kỹ thuật của dịch vụ.')
p('Phần 3A. Điều kiện hợp đồng. Chương VI là điều kiện chung áp dụng cho mọi hợp đồng, được sử dụng mà không sửa đổi. Chương VII là điều kiện cụ thể của hợp đồng này, chi tiết hóa và bổ sung nhưng không thay thế điều kiện chung.')
p('Phần 4. Biểu mẫu hợp đồng gồm các biểu mẫu sau khi hoàn chỉnh sẽ trở thành một bộ phận cấu thành của hợp đồng.')
br()

# ---------------- Chương I
center('Phần 1. Thủ tục đấu thầu', 16)
h1('Chương I. Chỉ dẫn nhà thầu')
p('Chương này được sử dụng nguyên văn theo Mẫu số 5A ban hành kèm theo Thông tư số 79/2025/TT-BTC, không sửa đổi, và được cố định dạng tệp tin PDF trên Hệ thống. Các nội dung áp dụng cụ thể cho gói thầu được quy định tại Chương II.')
B.append({'t': 'fixed_table', 'key': 'c1', 'widths': [2300, 7300]})
br()

# ---------------- Chương II: E-BDL
pt = cs['ty_le_bao_dam_du_thau_phan_tram']
TU_VAN_5_1_C = ['Tư vấn lập thiết kế kỹ thuật, thiết kế bản vẽ thi công, dự toán', 'Tư vấn thẩm tra thiết kế kỹ thuật, thiết kế bản vẽ thi công, dự toán',
                'Tư vấn thẩm định giá', 'Tư vấn giám sát thực hiện hợp đồng, kiểm định', 'Tư vấn lập E-HSMT', 'Tư vấn thẩm định E-HSMT',
                'Tư vấn đánh giá E-HSDT', 'Tư vấn thẩm định kết quả lựa chọn nhà thầu',
                'Tư vấn quản lý dự án, quản lý hợp đồng, tư vấn khác mà các dịch vụ tư vấn này có phần công việc liên quan trực tiếp tới gói thầu']


def bdl_5_1_c():
    # Nguyên văn Mục 5.1 (c) E-BDL của Mẫu 5A, chỉ điền các chỗ trống
    tu_van = 'không có' if not gt['dung_tu_van_dau_thau'] else 'theo E-TBMT trên Hệ thống'
    return ([f"Bảo đảm cạnh tranh trong đấu thầu theo quy định như sau: Nhà thầu tham dự thầu không có cổ phần hoặc vốn góp trên 30% với: {CDT}, {DIA_CHI}.",
             '+ Trường hợp nhà thầu, chủ đầu tư là công ty mẹ, công ty con, công ty thành viên trong tập đoàn kinh tế nhà nước, tổng công ty nhà nước, nhà thầu được tham dự gói thầu của chủ đầu tư nếu sản phẩm, dịch vụ thuộc gói thầu đó thuộc ngành, nghề sản xuất, kinh doanh chính của tập đoàn kinh tế nhà nước, tổng công ty nhà nước.',
             '+ Trường hợp nhà thầu là đơn vị sự nghiệp công lập, nhà thầu tham dự thầu không cùng thuộc một cơ quan hoặc tổ chức trực tiếp quản lý với Chủ đầu tư, trừ trường hợp: nhà thầu là đơn vị sự nghiệp công lập thuộc cơ quan quản lý nhà nước có chức năng, nhiệm vụ được giao phù hợp với tính chất gói thầu của cơ quan quản lý nhà nước đó; các đơn vị sự nghiệp công lập có cùng một cơ quan trực tiếp quản lý.',
             '+ Đơn vị sự nghiệp công lập và doanh nghiệp có cùng một cơ quan trực tiếp quản lý, góp vốn khi tham dự thầu các gói thầu của nhau không phải đáp ứng quy định độc lập về pháp lý và độc lập về tài chính giữa nhà thầu với chủ đầu tư.',
             '- Nhà thầu tham dự thầu không có cổ phần hoặc vốn góp với các nhà thầu tư vấn; không cùng có cổ phần hoặc vốn góp trên 20% của một tổ chức, cá nhân khác với từng bên, cụ thể như sau:']
            + [f'+ {ten}: {tu_van}.' for ten in TU_VAN_5_1_C]  # mỗi dòng một đoạn, kết thúc bằng dấu chấm (van_phong.md)
            + ['Nhà thầu tham dự thầu không cùng thuộc một cơ quan hoặc tổ chức trực tiếp quản lý với nhà thầu tư vấn (đã nêu trên).',
               'Tỷ lệ cổ phần, vốn góp giữa các bên được xác định tại thời điểm đóng thầu và theo tỷ lệ ghi trong giấy chứng nhận đăng ký doanh nghiệp, quyết định thành lập, các giấy tờ khác có giá trị tương đương.',
               'Trường hợp nhà thầu tham dự thầu với tư cách liên danh hoặc nhà thầu tư vấn được lựa chọn với tư cách liên danh, tỷ lệ sở hữu vốn của tổ chức, cá nhân khác trong liên danh được xác định theo công thức sau:',
               'Tỷ lệ sở hữu vốn = X1 x Y1 + X2 x Y2 + ... + Xn x Yn',
               'Trong đó:',
               'Xi: Tỷ lệ sở hữu vốn của tổ chức, cá nhân khác trong thành viên liên danh thứ i.',
               'Yi: Tỷ lệ phần trăm (%) khối lượng công việc của thành viên liên danh thứ i trong thỏa thuận liên danh.',
               'n: Số thành viên tham gia trong liên danh.',
               '- Nhà thầu trong nước thuộc trường hợp quy định tại điểm g khoản 1 Điều 10 của Luật Đấu thầu khi chào thầu dịch vụ do nhà thầu đó cung cấp không phải đáp ứng quy định về bảo đảm cạnh tranh quy định tại Mục này.'])


bdl_auto = {
    'E-CDNT 1.1': f'Tên Chủ đầu tư: {CDT}.',
    'E-CDNT 1.2': [f'Tên gói thầu: {GOI}.', f'Tên dự án: {DUAN}.', 'Số lượng, số hiệu các phần thuộc gói thầu: ' + ('gói thầu không chia phần.' if not gt['chia_phan'] else 'theo E-TBMT.')],
    'E-CDNT 3': f"Nguồn vốn: {gt['nguon_von']}.",
    'E-CDNT 5.1 (c)': bdl_5_1_c(),
    'E-CDNT 7.5': (f"Hội nghị tiền đấu thầu: Có. Thời gian: {hn['gio']}, ngày {hn['ngay']}. Địa điểm: <<SOẠN:DIA_DIEM_HOI_NGHI>>. Người chịu trách nhiệm tổ chức: {NGUOI_LH}, điện thoại {DIEN_THOAI}, email {EMAIL}." if hn else 'Hội nghị tiền đấu thầu: Không.'),
    'E-CDNT 8': 'Chi phí nộp E-HSDT: theo quy định hiện hành, do Hệ thống trích xuất.',
    'E-CDNT 10.8': 'Nhà thầu phải nộp cùng với E-HSDT các tài liệu sau đây: không yêu cầu.',
    'E-CDNT 12.1': 'Nhà thầu ' + ('được phép' if cs['phuong_an_ky_thuat_thay_the'] else 'không được phép') + ' nộp đề xuất phương án kỹ thuật thay thế.',
    'E-CDNT 17.1': f"Thời hạn hiệu lực của E-HSDT là: ≥ {th['hieu_luc_hsdt_ngay']} ngày, kể từ ngày có thời điểm đóng thầu.",
    'E-CDNT 18.2': ['Nội dung bảo đảm dự thầu:',
                    f"- Giá trị bảo đảm dự thầu: {tien['bao_dam_du_thau']} đồng." + (' Do giá trị bảo đảm dự thầu nhỏ hơn 50 triệu đồng, nhà thầu thực hiện cam kết trong đơn dự thầu theo quy định tại Mục 18.8 E-CDNT.' if int(tien['bao_dam_du_thau'].replace('.', '')) < 50_000_000 else '')
                    + ' Đối với nhà thầu có tên trong danh sách nhà thầu có các hành vi quy định tại khoản 1 Điều 20 của Nghị định số 214/2025/NĐ-CP và được đăng tải trên Hệ thống mạng đấu thầu quốc gia phải thực hiện biện pháp bảo đảm dự thầu với giá trị gấp 03 lần giá trị yêu cầu nêu trên trong thời hạn 02 năm kể từ lần cuối cùng thực hiện các hành vi này.'
                    + ' Trường hợp nhà thầu liên danh, thành viên liên danh có các hành vi quy định tại khoản 1 Điều 20 của Nghị định số 214/2025/NĐ-CP như nêu trên phải thực hiện biện pháp bảo đảm dự thầu với giá trị gấp 03 lần giá trị bảo đảm dự thầu tương ứng với tỷ lệ giá trị công việc thành viên đó đảm nhận trong liên danh trong thời hạn 02 năm kể từ lần cuối cùng thực hiện hành vi này.',
                    f"- Thời gian có hiệu lực của bảo đảm dự thầu: ≥ {th['hieu_luc_bao_dam_du_thau_ngay']} ngày, kể từ ngày có thời điểm đóng thầu."],
    'E-CDNT 18.4': f"Thời gian hoàn trả hoặc giải tỏa bảo đảm dự thầu đối với nhà thầu không được lựa chọn: {th['hoan_tra_bao_dam_du_thau_ngay']} ngày, kể từ ngày kết quả lựa chọn nhà thầu được phê duyệt.",
    'E-CDNT 18.9': 'Bảo đảm dự thầu: không áp dụng.',
    'E-CDNT 27.2': f"Giá trị tối đa dành cho nhà thầu phụ: {hd['nha_thau_phu_toi_da_phan_tram']}% giá dự thầu của nhà thầu. Việc kê khai sử dụng nhà thầu phụ thực hiện theo Mẫu số 09A Chương IV.",
    'E-CDNT 28.2': ['Cách tính ưu đãi: sản phẩm đổi mới sáng tạo quy định tại khoản 4 Điều 6 của Nghị định số 214/2025/NĐ-CP là dịch vụ phi tư vấn của doanh nghiệp khởi nghiệp sáng tạo trong nước được hưởng ưu đãi như sau:',
                    'Nhà thầu không thuộc đối tượng được hưởng ưu đãi phải cộng thêm một khoản tiền bằng 7,5% giá dự thầu trừ đi giá trị giảm giá (nếu có) vào giá dự thầu trừ đi giá trị giảm giá (nếu có) của nhà thầu đó để so sánh, xếp hạng.'],
    'E-CDNT 28.8': 'Các ưu đãi khác: không có.',
    'E-CDNT 29.1': ['Phương pháp đánh giá E-HSDT là:', '- Đánh giá về năng lực và kinh nghiệm: Đạt/Không đạt.',
                    f"- Đánh giá về kỹ thuật: {cs['phuong_phap_ky_thuat']}, theo Mục 3 Chương III.", f"- Đánh giá về tài chính: phương pháp {cs['phuong_phap_tai_chinh']}, theo Mục 4 Chương III."],
    'E-CDNT 29.3 (đ)': 'Xếp hạng nhà thầu: nhà thầu có giá dự thầu sau khi trừ đi giá trị giảm giá (nếu có) thấp nhất được xếp hạng thứ nhất.',
    'E-CDNT 31.4': 'Nhà thầu có giá dự thầu sau khi trừ đi giá trị giảm giá (nếu có) thấp nhất.',
    'E-CDNT 31.5': f"Giá gói thầu để làm căn cứ xét duyệt trúng thầu: giá gói thầu được phê duyệt trong kế hoạch lựa chọn nhà thầu là {tien['gia_goi_thau']} đồng. Trường hợp dự toán của gói thầu được phê duyệt thấp hơn hoặc cao hơn giá gói thầu được phê duyệt thì dự toán này sẽ thay thế giá gói thầu để làm cơ sở xét duyệt trúng thầu.",
    'E-CDNT 34.1': f"Tỷ lệ tăng khối lượng tối đa là: {cs['ty_le_tang_giam_khoi_luong_phan_tram']}%. Tỷ lệ giảm khối lượng tối đa là: {cs['ty_le_tang_giam_khoi_luong_phan_tram']}%."
                   + (' Thay đổi đặc tả, khối lượng sau khi ký hợp đồng thực hiện theo Mục 17 E-ĐKC và Mục 17.1 E-ĐKCT.' if not cs['ty_le_tang_giam_khoi_luong_phan_tram'] else ''),
    'E-CDNT 34.2': 'Tùy chọn mua thêm: ' + ('có áp dụng.' if cs['mua_them'] else 'không áp dụng.'),
    'E-CDNT 38.1': [f"- Người có thẩm quyền: {cdt['nguoi_co_tham_quyen']}.", f"+ Địa chỉ: {DIA_CHI}, điện thoại {DIEN_THOAI}, fax {FAX}.",
                    f"+ E-mail nhận đơn kiến nghị: {EMAIL} ({NGUOI_LH.split(', ')[-1]} tiếp nhận và chuyển người có thẩm quyền).",
                    '- Bộ phận thường trực giúp việc cho Chủ tịch Hội đồng giải quyết kiến nghị: không thành lập, do gói thầu sử dụng vốn tự có của doanh nghiệp. Kiến nghị do người có thẩm quyền giải quyết.'],
}
center('Chương II. Bảng dữ liệu đấu thầu', 15) if False else h1('Chương II. Bảng dữ liệu đấu thầu')
p('Các nội dung dưới đây được nhập vào webform E-BDL trên Hệ thống.')
rows = []
for it in ct['e_bdl']:
    ma = it['ma']
    v = bdl_auto.get(ma)
    if v is None:
        v = S('BDL_' + re.sub(r'\W+', '_', ma.replace('E-CDNT', '')).strip('_'), 'Điền mục ' + ma + ' theo hướng dẫn trong ngoặc vuông của mẫu, dùng tên, email, địa chỉ trong tham số và RFP.',
              ['mau5a_cau_truc.json', 'tham_so_chu_dau_tu.json', 'rfp_yeu_cau.json'], 'danh_sach_doan', it['noi_dung_mau'])
    rows.append([ma, v])
table(rows, [2000, 7600])
br()

# ---------------- Chương III
h1('Chương III. Tiêu chuẩn đánh giá E-HSDT')
h2('Mục 1. Đánh giá tính hợp lệ của E-HSDT')
B.append({'t': 'fixed_paras', 'key': 'muc1'})
h2('Mục 2. Tiêu chuẩn đánh giá về năng lực và kinh nghiệm')
h2('2.1. Tiêu chuẩn đánh giá về năng lực và kinh nghiệm')
p('Tiêu chuẩn đánh giá năng lực và kinh nghiệm thực hiện theo quy định tại Bảng số 01 Chương này và được số hóa dưới dạng webform trên Hệ thống, sử dụng tiêu chí đạt, không đạt. Nhà thầu được đánh giá đạt tất cả nội dung quy định tại Bảng số 01 thì đáp ứng yêu cầu về năng lực và kinh nghiệm. Năng lực và kinh nghiệm của nhà thầu phụ sẽ không được xem xét khi đánh giá E-HSDT của nhà thầu. Bản thân nhà thầu phải đáp ứng các tiêu chí đánh giá về năng lực và kinh nghiệm.')
p('Trường hợp đồng tiền nêu trong các hợp đồng tương tự hoặc xác nhận thanh toán của Chủ đầu tư đối với những hợp đồng cung cấp dịch vụ phi tư vấn đã thực hiện hoặc tờ khai nộp thuế hoặc các tài liệu liên quan chứng minh năng lực, kinh nghiệm của nhà thầu không phải VND thì khi lập E-HSDT, nhà thầu phải quy đổi về VND để làm cơ sở đánh giá E-HSDT. Việc quy đổi được áp dụng tỷ giá bán ra của một ngân hàng thương mại hoạt động tại Việt Nam tại ngày ký hợp đồng tương tự đó.')
p('Trường hợp nhà thầu tham dự thầu là công ty mẹ (ví dụ như Tổng công ty) có huy động công ty con, công ty thành viên thực hiện một phần công việc của gói thầu thì nhà thầu phải kê khai cụ thể phần công việc dành cho các công ty con, công ty thành viên theo Mẫu số 09B Chương IV. Việc đánh giá kinh nghiệm thực hiện hợp đồng tương tự căn cứ vào giá trị, khối lượng công việc do công ty mẹ, công ty con, công ty thành viên đảm nhiệm trong gói thầu.')
p('Bảng số 01. Bảng tiêu chuẩn đánh giá về năng lực và kinh nghiệm (webform trên Hệ thống)')
b01 = ct['bang01']
hdr = next(r for r in b01 if len(r) >= 6 and r[0] == 'TT' and 'Tổng các thành viên liên danh' in ' '.join(r))
data_rows = [r for r in b01 if r and r[0] in ('1', '2', '3', '4')]


def yeu_cau_doanh_thu():
    # Bảng số 01 dòng 3: công thức theo ghi chú (6) Mẫu 5A, nêu căn cứ thuế GTGT của gói thầu
    th = nl.get('thue_gtgt') or {}
    if th.get('loai') == 'khong_chiu_thue':
        cc = th['can_cu']
        thue = f"Giá trị thuế GTGT bằng 0 do {cc[0].lower() + cc[1:]}."
    elif th.get('loai') == 'chiu_thue':
        thue = f"Giá trị thuế GTGT với thuế suất {so_vn(th['thue_suat_phan_tram'])}% là {th['gia_tri_thue']} đồng."
    else:
        thue = 'Giá trị thuế GTGT: ' + dau_cho('gói thầu chịu hoặc không chịu thuế GTGT, căn cứ') + '.'
    return (f"Áp dụng. Doanh thu bình quân hằng năm (không bao gồm thuế VAT) của {len(nl['cac_nam_doanh_thu']):02d} năm tài chính gần nhất so với thời điểm đóng thầu "
            f"(các năm {', '.join(map(str, nl['cac_nam_doanh_thu']))}) tối thiểu là {tien['doanh_thu_binh_quan_toi_thieu']} đồng, bằng (giá gói thầu trừ giá trị thuế GTGT) "
            f"nhân hệ số k bằng {so_vn(nl['he_so_k'])} theo cách tính đối với gói thầu có thời gian thực hiện dưới 12 tháng. {thue}")


def yeu_cau_hop_dong_tuong_tu():
    # Bảng số 01 dòng 4: chỉ cho cộng gộp hạng mục khi tham số cho phép và có giá trị từng hạng mục (ghi chú (11))
    cg = nl.get('hop_dong_tuong_tu_cong_gop')
    hm = nl.get('hang_muc_tuong_tu') or []
    if cg is True and hm:
        cong_gop = (' Nhà thầu cũng được coi là đáp ứng khi đã hoàn thành các hạng mục công việc tương tự trong các hợp đồng khác nhau với giá trị tối thiểu từng hạng mục như sau: '
                    + ', '.join(f"{x['ten']} {x['gia_tri']} đồng" for x in hm) + '.')
    elif cg is None:
        cong_gop = ' Cộng gộp hạng mục công việc tương tự từ nhiều hợp đồng: ' + dau_cho('áp dụng kèm hạng mục và giá trị từng hạng mục, hoặc không áp dụng') + '.'
    else:
        cong_gop = ''
    return (f"Áp dụng. Từ ngày {nl['moc_hop_dong_tuong_tu']} đến thời điểm đóng thầu, nhà thầu đã hoàn thành tối thiểu 01 hợp đồng tương tự với tư cách là nhà thầu chính "
            f"(độc lập hoặc thành viên liên danh) hoặc nhà thầu phụ, có giá trị tối thiểu {tien['hop_dong_tuong_tu_toi_thieu']} đồng ({nl['ty_le_hop_dong_tuong_tu']}% giá gói thầu). "
            f"Đối với hợp đồng nhà thầu tham gia với tư cách thành viên liên danh hoặc nhà thầu phụ thì chỉ tính giá trị phần việc do nhà thầu thực hiện.{cong_gop} "
            f"Hợp đồng tương tự là hợp đồng {cs['dinh_nghia_hop_dong_tuong_tu']}.")


def doan_mau_2_2(dau):
    """Đoạn quy phạm Mục 2.2 Chương III Mẫu 5A, chép nguyên văn từ mau5a_cau_truc.json."""
    x = next((x for x in ct['huong_dan_chuong3'] if x.startswith(dau)), None)
    if x is None:
        sys.exit(f'Không tìm thấy đoạn "{dau} ..." của Mục 2.2 Chương III trong mau5a_cau_truc.json. Kiểm tra lại Mẫu 5A và phan_tich_mau.py')
    return x


yeu_cau = {
    '1': f"Từ ngày {nl['moc_lich_su_hop_dong']} đến thời điểm đóng thầu, nhà thầu không có từ 02 hợp đồng trở lên (cung cấp dịch vụ phi tư vấn) không hoàn thành do lỗi của nhà thầu.",
    '2': f"Đã thực hiện nghĩa vụ kê khai thuế và nộp thuế của năm tài chính gần nhất so với thời điểm đóng thầu (năm {nl['nam_tai_chinh_gan_nhat']}).",
    '3': yeu_cau_doanh_thu(),
    '4': yeu_cau_hop_dong_tuong_tu(),
}
b01_rows = [['TT', 'Mô tả', 'Yêu cầu', 'Nhà thầu độc lập', 'Liên danh: tổng các thành viên', 'Liên danh: từng thành viên', 'Tài liệu cần nộp']]
for r in data_rows:
    mo_ta = re.sub(r'\(\d\)', '', r[1]).strip()
    b01_rows.append([r[0], mo_ta, yeu_cau[r[0]], r[3], r[4], r[5], r[6]])  # các cột liên danh, tài liệu: lấy nguyên từ mẫu
table(b01_rows, [560, 1450, 2950, 1150, 1150, 1250, 1090])
h2('2.2. Tiêu chuẩn đánh giá về nhân sự chủ chốt và thiết bị chủ yếu')
p('a) Nhân sự chủ chốt. ' + S('NHAN_SU_LY_DO', 'Một đến hai câu nêu lý do gói thầu cần nhân sự chủ chốt, căn cứ tính chất công việc trong RFP (xây dựng hệ thống, tích hợp hệ thống hiện có). Không nhắc lại các đoạn quy phạm của Mục 2.2 Mẫu 5A về chứng minh khả năng huy động, bổ sung thay thế, kê khai không trung thực, cách tính số năm kinh nghiệm, Mẫu số 06A, 06B, 06C (script chép nguyên văn ngay sau câu này).',
                                 ['rfp_yeu_cau.json: he_thong, pham_vi', 'mau5a_cau_truc.json: huong_dan_chuong3']))
for dau in DOAN_2_2_NHAN_SU:
    p(doan_mau_2_2(dau))
p('Bảng số 02. Yêu cầu về nhân sự chủ chốt (webform trên Hệ thống)')
table([[re.sub(r'\(\d\)$', '', c) for c in ct['bang02'][0]]] + [[str(i + 1), x['vi_tri'], str(x['so_luong']), x['kinh_nghiem'][0].upper() + x['kinh_nghiem'][1:], 'Không yêu cầu'] for i, x in enumerate(ts['nhan_su_chu_chot'])],
      [600, 2400, 900, 3800, 1900], [0, 2])
p('b) Thiết bị chủ yếu: ' + ('theo yêu cầu của Chủ đầu tư.' if cs['thiet_bi_chu_yeu'] else 'không yêu cầu, do gói thầu không cần thiết bị đặc chủng.'))
NS_PHAT = cs.get('phat_khong_huy_dong_nhan_su_phan_tram_ngay')  # 0: không áp dụng phạt riêng
p(doan_mau_2_2(DOAN_2_2_C) + (' Việc thay thế nhân sự chủ chốt thực hiện theo Mục 21 E-ĐKC và Mục 21.2 E-ĐKCT. Chậm thực hiện công việc do không huy động nhân sự chủ chốt bị phạt theo Mục 15 E-ĐKCT.'
                              if NS_PHAT == 0 else ' Mức phạt khi không huy động nhân sự chủ chốt theo Mục 15 E-ĐKCT.'))
h2('Mục 3. Tiêu chuẩn đánh giá về kỹ thuật')
p(f"Áp dụng phương pháp chấm điểm theo thang điểm 100. Mức điểm yêu cầu tối thiểu về kỹ thuật là {kt['tong_toi_thieu']} điểm, bằng {kt['tong_toi_thieu']}% tổng số điểm tối đa. Mỗi tiêu chí tổng quát phải đạt tối thiểu mức điểm nêu tại bảng dưới đây. Tiêu chuẩn đánh giá được xây dựng trên các sản phẩm đầu ra nêu tại Chương V. Đề xuất kỹ thuật của nhà thầu trình bày đủ các nội dung nêu tại mục 4 Chương V.")
CHU_DE_TIEU_CHI = ['hiểu biết mục tiêu và giải pháp kỹ thuật tổng thể, gồm các yêu cầu phi chức năng',
                   'phạm vi, sản phẩm đầu ra, phương pháp thực hiện và bảo đảm chất lượng',
                   'kế hoạch, tiến độ đến ngày cut over, tổ chức, nhân sự, kế hoạch họp',
                   'vai trò, trách nhiệm, quản lý thay đổi, rủi ro, bảo hành',
                   'đề xuất khác có lợi cho thành công của dự án và thông tin về kết quả thực hiện hợp đồng theo Điều 19 và Điều 20 của Nghị định số 214/2025/NĐ-CP']
kt_rows = [['STT', 'Tiêu chí tổng quát', 'Điểm tối đa', 'Điểm tối thiểu']]
for i, (w, m) in enumerate(zip(kt['trong_so'], kt['diem_toi_thieu'])):
    chu_de = f' Chủ đề: {CHU_DE_TIEU_CHI[i]}.' if i < len(CHU_DE_TIEU_CHI) else ''
    kt_rows.append([str(i + 1), S(f'TIEU_CHI_{i + 1}', f'Tên tiêu chí tổng quát thứ {i + 1} (tối đa {w} điểm), một cụm danh từ ngắn nêu phạm vi chấm, chi tiết đặt ở TIEU_CHI_CHI_TIET.{chu_de} Không đưa giá, chi phí, điều kiện hoặc đề nghị của nhà thầu đối với Chủ đầu tư vào tiêu chí kỹ thuật.', ['rfp_yeu_cau.json: noi_dung_de_xuat, yeu_cau nhóm de_xuat, chinh_sach']), str(w), str(m)])
kt_rows.append(['', 'Tổng cộng', '100', str(kt['tong_toi_thieu'])])
table(kt_rows, [600, 6000, 1500, 1500], [0, 2, 3])
p('Điểm của mỗi tiêu chí tổng quát bằng tổng điểm của các tiêu chí chi tiết thuộc tiêu chí đó, chấm theo các mức nêu tại Bảng tiêu chí chi tiết dưới đây. Tổng điểm kỹ thuật bằng tổng điểm của các tiêu chí tổng quát. Cách tính này tương đương công thức tại Mục 3.1 Chương III Mẫu số 5A, trong đó tỷ trọng của mỗi tiêu chí chi tiết bằng điểm tối đa của tiêu chí chi tiết chia cho điểm tối đa của tiêu chí tổng quát chứa nó.')
p('Tiêu chí chi tiết cơ bản được đánh dấu tại cột Tiêu chí cơ bản. Mức điểm tối thiểu chỉ quy định đối với tiêu chí chi tiết cơ bản.')
p('Bảng tiêu chí chi tiết')
CAN_PHU = [{'ma': y['ma'], 'nhom': y['nhom'], 'noi_dung': y['dien_giai'], 'tu_khoa': y['tu_khoa_kiem_tra']}
           for y in rfp['yeu_cau'] if y['nhom'] in ('de_xuat', 'chinh_sach')]
LY_DO_KHONG_TINH_DIEM = {'tai_chinh': 'chi phí, giá thuộc đề xuất tài chính (Mẫu số 11A), đánh giá theo Mục 4 Chương III',
                         'dieu_kien_nha_thau': 'điều kiện khác, đề nghị của nhà thầu đối với Chủ đầu tư, xét theo Mục 24 và Mục 25 E-CDNT, không tính điểm'}
tc_ct = S('TIEU_CHI_CHI_TIET',
          'Tiêu chí chi tiết của từng tiêu chí tổng quát (cấu trúc Mục 3, 3.1 Chương III Mẫu số 5A). Mỗi tiêu chí tổng quát có từ 3 đến 6 tiêu chí chi tiết, tổng điểm tối đa của các tiêu chí chi tiết bằng điểm tối đa của tiêu chí tổng quát. '
          'Mỗi tiêu chí chi tiết có tên, nội dung được chấm (dẫn chiếu nội dung đề xuất tại mục 4 hoặc yêu cầu tại mục 3 Chương V), điểm tối đa, đánh dấu cơ bản, và ít nhất 3 mức chấm (ví dụ đạt đủ, đạt một phần, không đạt) có điểm và mô tả, mức cao nhất bằng điểm tối đa, mức thấp nhất 0 điểm, điểm giảm dần. '
          'Chỉ tiêu chí cơ bản được có diem_toi_thieu. Mỗi mã trong rang_buoc.can_phu phải được ít nhất một tiêu chí chi tiết ghi trong phu và dùng các cụm tu_khoa của mã đó, trừ mã thuộc một lý do trong rang_buoc.ly_do_khong_tinh_diem thì ghi vào khong_tinh_diem. '
          'Không chấm giá, chi phí, điều kiện hoặc đề nghị của nhà thầu đối với Chủ đầu tư. Không chép chỉ tiêu kỹ thuật do nhà thầu cam kết. Dạng: {"tieu_chi_chi_tiet": [{"tieu_chi": 1, "ten": "", "noi_dung": "", "diem": 8, "co_ban": true, "diem_toi_thieu": 4, '
          '"muc_cham": [{"muc": "Đạt đủ", "diem": 8, "mo_ta": ""}, {"muc": "Đạt một phần", "diem": 4, "mo_ta": ""}, {"muc": "Không đạt", "diem": 0, "mo_ta": ""}], "phu": ["R15"]}], "khong_tinh_diem": [{"ma": "R16", "ly_do": "tai_chinh"}]}.',
          ['rfp_yeu_cau.json: yeu_cau nhóm de_xuat, chinh_sach', 'mau5a_cau_truc.json: huong_dan_chuong3 (Mục 3, 3.1)', 'gia_tri_tinh.json: ky_thuat'],
          'tieu_chi_chi_tiet', rang_buoc={'trong_so': kt['trong_so'], 'diem_toi_thieu': kt['diem_toi_thieu'], 'so_tieu_chi_chi_tiet': [3, 6],
                                          'so_muc_cham_toi_thieu': 3, 'can_phu': CAN_PHU, 'ly_do_khong_tinh_diem': LY_DO_KHONG_TINH_DIEM})
table([['STT', 'Tiêu chí chi tiết', 'Điểm tối đa', 'Tiêu chí cơ bản', 'Mức chấm điểm'], tc_ct], [700, 3300, 900, 1100, 3600], [0, 2, 3])
p('Điều kiện khác, đề nghị đối với Chủ đầu tư mà nhà thầu nêu trong E-HSDT không được tính điểm kỹ thuật. Các nội dung này được xem xét theo Mục 24 và Mục 25 E-CDNT về sai khác, đặt điều kiện và tính đáp ứng của E-HSDT.')
p(f"E-HSDT đạt yêu cầu về kỹ thuật khi tổng điểm kỹ thuật không thấp hơn {kt['tong_toi_thieu']} điểm, từng tiêu chí tổng quát không thấp hơn mức điểm tối thiểu và từng tiêu chí chi tiết cơ bản có quy định mức điểm tối thiểu không thấp hơn mức đó.")
h2('Mục 4. Tiêu chuẩn đánh giá về tài chính')
p('Áp dụng phương pháp giá thấp nhất. Bước 1: xác định giá dự thầu, trừ đi giá trị giảm giá (nếu có). Bước 2: xác định ưu đãi (nếu có) theo Mục 28 E-CDNT. Bước 3: xếp hạng nhà thầu, E-HSDT có giá dự thầu trừ đi giá trị giảm giá (nếu có), sau ưu đãi (nếu có) thấp nhất được xếp hạng thứ nhất. Chỉ E-HSDT đáp ứng yêu cầu về năng lực, kinh nghiệm và về kỹ thuật mới được xem xét về giá. Giá đề nghị trúng thầu không vượt giá gói thầu.')
h2('Mục 5. Phương án kỹ thuật thay thế trong E-HSDT')
p('Không áp dụng, do nhà thầu không được phép nộp phương án kỹ thuật thay thế theo Mục 12.1 E-BDL.' if not cs['phuong_an_ky_thuat_thay_the'] else 'Theo Mục 12.1 E-BDL.')
h2('Mục 6. Trường hợp gói thầu chia thành nhiều phần độc lập')
p('Không áp dụng, do gói thầu không chia phần.' if not gt['chia_phan'] else 'Theo E-TBMT.')
br()

# ---------------- Chương IV
h1('Chương IV. Biểu mẫu mời thầu và dự thầu')
h2('1. Danh mục biểu mẫu')
p('Các biểu mẫu được số hóa dưới dạng webform và sử dụng theo Mẫu số 5A ban hành kèm theo Thông tư số 79/2025/TT-BTC.')
bd_tu = int(tien['bao_dam_du_thau'].replace('.', '')) < 50_000_000


def ap_dung(ma):
    if ma == '01A': return 'Áp dụng, nội dung tại mục 2 Chương này'
    if ma in ('01B', '01C', '01D', '01E', '01G', '10B', '10C', '10D', '11B', '11C', '11D', '11E', '11G'): return 'Không áp dụng, do hợp đồng trọn gói'
    if ma == '03': return 'Áp dụng đối với nhà thầu liên danh'
    if ma in ('04A', '04B'): return 'Áp dụng khi được mời đối chiếu tài liệu hoặc khi vi phạm theo Mục 18.8 E-CDNT' if bd_tu else 'Áp dụng'
    if ma == '06D': return 'Áp dụng' if cs['thiet_bi_chu_yeu'] else 'Không áp dụng, do không yêu cầu thiết bị chủ yếu'
    if ma in ('09A',): return 'Áp dụng khi sử dụng nhà thầu phụ'
    if ma in ('09B', '12'): return 'Áp dụng khi có'
    return 'Áp dụng'


bm = [['STT', 'Biểu mẫu', 'Cách thức thực hiện', 'Trách nhiệm thực hiện', 'Áp dụng']]
for r in ct['chuong4_bieu_mau']:
    if not r or not r[0].isdigit(): continue
    ma = re.match(r'Mẫu số (\w+)\.', r[1]).group(1)
    bm.append([r[0], r[1], r[2], 'Chủ đầu tư' if r[3] == 'X' else 'Nhà thầu', ap_dung(ma)])
table(bm, [600, 3600, 1800, 1200, 2400], [0])
h2('2. Mẫu số 01A. Phạm vi cung cấp (hợp đồng trọn gói)')
B.append({'t': 'table', 'rows': [ct['mau01a_cot'][:2] + ['Mô tả dịch vụ'] + ct['mau01a_cot'][3:], S('MAU_01A', 'Các dòng của Mẫu 01A, mỗi dòng 7 ô: STT, danh mục dịch vụ, mô tả dịch vụ (dẫn chiếu mục Chương V), khối lượng (1), đơn vị tính (Gói), địa điểm thực hiện, ngày hoàn thành. Lập một hạng mục cho mỗi sản phẩm bàn giao của RFP, mỗi chức năng của hệ thống mới, việc tích hợp với hệ thống liên quan, kiểm thử hệ thống và kiểm thử vận hành, đào tạo chuyển giao và hỗ trợ cut over. Ngày hoàn thành ghi theo tiến độ được duyệt, trước ngày cut over, riêng hạng mục cut over ghi đúng ngày cut over.', ['rfp_yeu_cau.json: san_pham_ban_giao, he_thong, moc.cut_over', 'gia_tri_tinh.json: lich.cut_over'], 'dong_bang')],
          'widths': [500, 1900, 2200, 900, 800, 1800, 1500], 'center_cols': [0, 3, 4]})
br()

# ---------------- Chương V
center('Phần 2. Yêu cầu về kỹ thuật', 16)
h1('Chương V. Yêu cầu về kỹ thuật')
c5 = [('1. Giới thiệu chung về dự án và gói thầu', 'C5_1', 'Thông tin tóm tắt về dự án và gói thầu: chủ đầu tư, tên dự án, nội dung gói thầu, địa điểm thực hiện, thời gian từ ngày hợp đồng có hiệu lực đến ngày cut over. Thêm một câu về trách nhiệm bảo mật thông tin của Chủ đầu tư nêu trong E-HSMT nếu RFP có yêu cầu bảo mật.'),
      ('2. Mục tiêu công việc', 'C5_2', 'Mục tiêu dự án và chính sách phát triển trong RFP, nêu đủ từng yêu cầu chính sách với con số cụ thể.'),
      ('3. Yêu cầu kỹ thuật của gói thầu', 'C5_3', 'Các đoạn đánh số 3.1 mô hình hệ thống mới (chức năng, cơ sở dữ liệu, hệ thống liên quan, giữ tên tiếng Anh của RFP trong ngoặc, nêu chiều của từng luồng dữ liệu có trong sơ đồ RFP), 3.2 phạm vi (nêu rõ phạm vi theo RFP và phần ngoài phạm vi), 3.3 sản phẩm đầu ra (đủ các sản phẩm bàn giao của RFP. Khi phạm vi có chuyển giao, đào tạo thì nêu tài liệu bàn giao kèm theo để hạng mục chuyển giao có đối tượng nghiệm thu), 3.4 yêu cầu phi chức năng (giữ con số của RFP, điều kiện đo đã nêu tại mục 3.5 do script lập). Không viết mục 3.5.'),
      ('4. Giải pháp và phương pháp luận', 'C5_4', 'Nêu nhà thầu chuẩn bị đề xuất gồm (1) giải pháp và phương pháp luận, (2) kế hoạch công tác theo hướng dẫn của mẫu, và phải trình bày đủ các nội dung đề xuất RFP yêu cầu. Chi phí ước tính kèm lý do trình bày trong đề xuất tài chính theo Mẫu số 11A, không chấm điểm kỹ thuật. Viết thành các câu ngắn, hạn chế dấu chấm phẩy.'),
      ('5. Quy định về kiểm tra, nghiệm thu sản phẩm', 'C5_5', 'Quy trình bàn giao, kiểm tra theo đặc tả, thông báo kết quả, kiểm tra đạt là chấp nhận sản phẩm, biên bản nghiệm thu là căn cứ thanh toán theo Mục 13.1 E-ĐKCT.')]
PD, GPD = ts.get('phan_dinh') or {}, gv.get('phan_dinh') or {}


def dong_thong_tin_he_thong():
    tt = PD.get('thong_tin_he_thong_hien_co')
    ten = 'Thông tin, giao diện trao đổi dữ liệu của hệ thống hiện có'
    if not tt or not GPD.get('han_cung_cap_thong_tin_he_thong'):
        return [ten, dau_cho('tài liệu, giao diện được cung cấp và thời hạn cung cấp')]
    n = tt['thoi_han_cung_cap_ngay']
    sau = f', tức {n} ngày kể từ ngày hợp đồng có hiệu lực' if n else ', là ngày hợp đồng có hiệu lực'
    ds = tt['tai_lieu'] if isinstance(tt['tai_lieu'], list) else [tt['tai_lieu']]
    noi = ', '.join(ds[:-1]) + ' và ' + ds[-1] if len(ds) > 1 else ds[0]
    return [f"{ten} ({tt['ten']})", f"Chủ đầu tư cung cấp {noi} chậm nhất ngày {GPD['han_cung_cap_thong_tin_he_thong']}{sau}."]


def truoc_dot_dac_ta():
    dot = GPD.get('dot_xac_nhan_dac_ta')
    return f'trước khi thanh toán Đợt {dot} theo Mục 13.1 E-ĐKCT' if dot else 'khi xác nhận đặc tả yêu cầu'


def dong_dieu_kien_do():
    dk = PD.get('dieu_kien_do_phi_chuc_nang')
    ten = 'Điều kiện đo các yêu cầu phi chức năng tại mục 3.4'
    if dk is None:
        return [ten, dau_cho('quy định điều kiện đo, hoặc giao nhà thầu đề xuất và hai bên xác nhận trong đặc tả')]
    if dk == 'nha_thau_de_xuat':
        han = truoc_dot_dac_ta()
        return [ten, f'Nhà thầu đề xuất điều kiện đo trong E-HSDT (tải, số người dùng đồng thời, cách tính thời gian hoạt động liên tục, điểm đo). Hai bên xác nhận điều kiện đo trong đặc tả yêu cầu {han}.']
    return [ten, f"Thời gian phản hồi được đo với {dk['so_nguoi_dung_dong_thoi']} người dùng đồng thời. Yêu cầu hoạt động liên tục được đo bằng tỷ lệ sẵn sàng hằng tháng không thấp hơn {so_vn(dk['ty_le_san_sang_phan_tram'])}%. Nhà thầu nêu cách đo kiểm trong E-HSDT."]


HAN_HT = GPD.get('thoi_han_ha_tang') or {}
TEN_HT = (PD.get('thong_tin_he_thong_hien_co') or {}).get('ten')
CUA_HT = f' ({TEN_HT})' if TEN_HT else ''


def dong_ha_tang(k, ten):
    # máy chủ, đường truyền, phần mềm nền do Chủ đầu tư cung cấp kèm thời hạn bàn giao hạ tầng vận hành chính thức
    v = lay(PD, 'ha_tang_ben_cung_cap.' + k)
    if not v:
        return [ten, dau_cho('Chủ đầu tư hoặc nhà thầu cung cấp')]
    if v != 'chu_dau_tu' or k == 'moi_truong_kiem_thu':
        return [ten, BEN[v]]
    han = HAN_HT.get('ha_tang_van_hanh_chinh_thuc')
    han = f'chậm nhất ngày {han}' if han else 'thời hạn ' + dau_cho('ngày bàn giao hạ tầng vận hành chính thức')
    ch = PD.get('cau_hinh_ha_tang')
    if ch == 'nha_thau_de_xuat':
        return [ten, f'{BEN[v]} theo cấu hình đã thống nhất, {han}. Cấu hình tối thiểu do nhà thầu đề xuất trong E-HSDT, '
                     f'hai bên thống nhất khi xác nhận đặc tả yêu cầu {truoc_dot_dac_ta()}']
    if isinstance(ch, dict) and ch.get(k):
        return [ten, f'{BEN[v]}, {han}. Cấu hình: {ch[k]}']
    return [ten, f"{BEN[v]}, {han}. Cấu hình: " + dau_cho('cấu hình do Chủ đầu tư nêu, hoặc theo đề xuất của nhà thầu được thống nhất trong đặc tả')]


def dong_thay_doi():
    # bên thực hiện thay đổi phía hệ thống hiện có, kèm thời hạn khi Chủ đầu tư thực hiện
    ten, v = f'Thay đổi phía hệ thống hiện có{CUA_HT} để trao đổi dữ liệu với hệ thống mới', PD.get('thay_doi_he_thong_hien_co')
    if v not in THAY_DOI_HE_THONG:
        return [ten, dau_cho('Chủ đầu tư hoặc nhà thầu thực hiện')]
    if v != 'chu_dau_tu':
        return [ten, THAY_DOI_HE_THONG[v]]
    han = HAN_HT.get('thay_doi_he_thong_hien_co')
    return [ten, f"{THAY_DOI_HE_THONG[v]}. Chủ đầu tư hoàn thành thay đổi " + (f'chậm nhất ngày {han}' if han else dau_cho('thời hạn hoàn thành'))]


def dong_lua_chon(ten, khoa, gia_tri, mo_ta_cho):
    v = PD.get(khoa)
    return [ten, gia_tri[v] if v in gia_tri else dau_cho(mo_ta_cho)]


def dong_moi_truong_thu():
    han = HAN_HT.get('moi_truong_thu_he_thong_hien_co')
    return [f'Môi trường thử của hệ thống hiện có{CUA_HT}', f'Chủ đầu tư cung cấp chậm nhất ngày {han}' if han else dau_cho('thời hạn cung cấp môi trường thử')]


def phan_dinh_3_5():
    # Chương V mục 3.5: bên cung cấp và thời hạn hạ tầng, môi trường, thông tin hệ thống hiện có, bên thay đổi hệ thống hiện có,
    # môi trường kiểm thử vận hành, điều kiện đo. Lấy từ tham số nhóm phan_dinh, ngày do tinh_gia_tri.py tính.
    rows = [['STT', 'Nội dung', 'Phân định']] + [dong_ha_tang(k, ten) for k, ten in HA_TANG]
    rows += [dong_thong_tin_he_thong(), dong_moi_truong_thu(),
             dong_thay_doi(),
             dong_lua_chon('Môi trường kiểm thử vận hành và đo các yêu cầu phi chức năng', 'kiem_thu_van_hanh_tren', KIEM_THU_VAN_HANH, 'hạ tầng vận hành chính thức hoặc môi trường kiểm thử của nhà thầu'),
             dong_dieu_kien_do()]
    cham = {True: 'Trường hợp Chủ đầu tư cung cấp hoặc hoàn thành chậm so với thời hạn nêu tại bảng, các mốc liên quan được lùi tương ứng số ngày chậm theo Mục 18 (e) E-ĐKCT.',
            False: 'Việc Chủ đầu tư cung cấp chậm so với thời hạn nêu tại bảng là căn cứ để hai bên xem xét sửa đổi thời gian thực hiện hợp đồng theo Mục 17 E-ĐKC.'}
    p('3.5. Phân định trách nhiệm và giả định. Giá dự thầu trọn gói được lập trên cơ sở phân định dưới đây. '
      + cham.get(GIA_HAN, 'Xử lý khi Chủ đầu tư cung cấp chậm: ' + dau_cho('lùi mốc theo Mục 18 (e) E-ĐKCT hoặc sửa đổi hợp đồng theo Mục 17 E-ĐKC') + '.'))
    table([rows[0]] + [[str(i), *r] for i, r in enumerate(rows[1:], 1)], [600, 3800, 5200], [0])


for tieu_de, id_, hd_ in c5:
    h2(tieu_de)
    p(S(id_, hd_, ['rfp_yeu_cau.json', 'mau5a_cau_truc.json: huong_dan_chuong5', 'gia_tri_tinh.json: lich'], 'danh_sach_doan'))
    if id_ == 'C5_3':
        phan_dinh_3_5()
br()

# ---------------- Chương VI
center('Phần 3A. Điều kiện hợp đồng', 16)
h1('Chương VI. Điều kiện chung của hợp đồng')
p('Chương này được sử dụng nguyên văn theo Mẫu số 5A ban hành kèm theo Thông tư số 79/2025/TT-BTC, không sửa đổi, và được cố định dạng tệp tin PDF trên Hệ thống.')
B.append({'t': 'fixed_table', 'key': 'c6', 'widths': [2300, 7300]})
br()

# ---------------- Chương VII: E-ĐKCT
tt = hd['thanh_toan']
canh_bao = []


def dkc_15():
    # Nguyên văn Mục 15 E-ĐKCT của Mẫu 5A. Tỷ lệ phạt khắc phục sai sót và cách bồi thường là lựa chọn của chủ đầu tư.
    pkss, bt = cs.get('phat_khac_phuc_sai_sot_phan_tram'), cs.get('boi_thuong_thiet_hai')
    phat = (f"1. Phạt vi phạm hợp đồng: Áp dụng. Trừ trường hợp bất khả kháng theo quy định tại Mục 16 E-ĐKC, nếu Nhà thầu không thực hiện một phần hay toàn bộ nội dung công việc theo đúng thời hạn đã nêu trong hợp đồng thì Chủ đầu tư có thể khấu trừ vào giá hợp đồng một khoản tiền phạt tương ứng với {so_vn(cs['phat_cham_tien_do_phan_tram_ngay'])}%/ngày giá trị công việc chậm thực hiện cho đến khi nội dung công việc đó được thực hiện. "
            f"Chủ đầu tư sẽ khấu trừ đến {so_vn(cs['phat_toi_da_phan_tram'])}% giá trị phần hợp đồng bị vi phạm. Khi đạt đến mức phạt tối đa, Chủ đầu tư có thể xem xét chấm dứt hợp đồng theo quy định tại Mục 19 E-ĐKC.")
    # Tham số còn null: giữ câu mẫu, thay giá trị bằng dấu chờ để verify_hsmt.py kết luận cho_nguoi_dung
    ty_le = f'{so_vn(pkss)}%' if pkss is not None else dau_cho('tỷ lệ %')
    if pkss is None:
        canh_bao.append('Thiếu tham số chinh_sach.phat_khac_phuc_sai_sot_phan_tram: E-ĐKC 15 giữ câu mẫu kèm dấu chờ Chủ đầu tư quyết định tỷ lệ phạt khi không kịp thời khắc phục sai sót')
    phat += f" Trường hợp không kịp thời khắc phục sai sót theo thông báo của Chủ đầu tư, Nhà thầu có trách nhiệm nộp tiền phạt thực hiện hợp đồng tương ứng với {ty_le} chi phí cần thiết để khắc phục sai sót."
    ns = cs.get('phat_khong_huy_dong_nhan_su_phan_tram_ngay')
    ty_le_ns = f'{so_vn(ns)}%' if ns is not None else dau_cho('tỷ lệ %')
    phat += '' if ns == 0 else (f" Trường hợp nhân sự chủ chốt không được huy động như đề xuất trong E-HSDT mà chưa được Chủ đầu tư chấp thuận thay thế theo Mục 21 E-ĐKC, "
             f"Nhà thầu bị phạt {ty_le_ns} giá hợp đồng cho mỗi ngày không huy động. Khoản phạt này được tính chung trong mức khấu trừ tối đa {so_vn(cs['phat_toi_da_phan_tram'])}% nêu trên.")
    if bt is None:
        canh_bao.append('Thiếu tham số chinh_sach.boi_thuong_thiet_hai: E-ĐKC 15 giữ câu mẫu kèm dấu chờ Chủ đầu tư chọn cách bồi thường thiệt hại')
        boi = ('2. Bồi thường thiệt hại: Áp dụng. Bồi thường thiệt hại trên cơ sở '
               + dau_cho('toàn bộ thiệt hại thực tế, hoặc một mức xác định kèm mức bồi thường, phương thức bồi thường phù hợp với pháp luật dân sự') + '.')
    elif bt == 'toan_bo_thiet_hai_thuc_te':
        boi = '2. Bồi thường thiệt hại: Áp dụng. Bồi thường thiệt hại trên cơ sở toàn bộ thiệt hại thực tế.'
    else:
        boi = f'2. Bồi thường thiệt hại: Áp dụng. Bồi thường thiệt hại trên cơ sở một mức xác định: {bt}.'
    return ['Vừa áp dụng phạt vi phạm hợp đồng vừa áp dụng bồi thường thiệt hại.', phat, boi]


dkct_auto = {
    'E-ĐKC 1.3': f"Chủ đầu tư: {CDT}. Địa chỉ: {DIA_CHI}. Số tài khoản: {lh('so_tai_khoan', 'số tài khoản')}. Mã số thuế: {lh('ma_so_thue', 'mã số thuế')}. Điện thoại: {DIEN_THOAI}. Fax: {FAX}. E-mail: {EMAIL}. Đại diện: {cdt['nguoi_dai_dien']}.",
    'E-ĐKC 1.11': 'Nhà thầu: nhà thầu trúng thầu. Tên, địa chỉ, số tài khoản, mã số thuế được ghi khi hoàn thiện hợp đồng.',
    'E-ĐKC 4.1': f"Các thông báo gửi về Chủ đầu tư theo địa chỉ dưới đây. Người nhận: {NGUOI_LH}. Địa chỉ: {DIA_CHI}. Điện thoại: {so_quoc_te(DIEN_THOAI)}. Fax: {so_quoc_te(FAX)}. Địa chỉ email: {EMAIL}.",
    'E-ĐKC 5.2': [f"- Giá trị bảo đảm thực hiện hợp đồng: {hd['bao_dam_thuc_hien_phan_tram']}% giá hợp đồng.",
                  f"- Hiệu lực của bảo đảm thực hiện hợp đồng: kể từ ngày hợp đồng có hiệu lực cho đến hết ngày {th['hieu_luc_bao_dam_thuc_hien_den']}."],
    'E-ĐKC 5.4': f"Thời hạn hoàn trả bảo đảm thực hiện hợp đồng: trong vòng {cs['hoan_tra_bao_dam_thuc_hien_ngay']} ngày kể từ ngày nhà thầu hoàn thành các nghĩa vụ hợp đồng, sau khi hệ thống được nghiệm thu và đưa vào vận hành.",
    'E-ĐKC 6.1': 'Danh sách nhà thầu phụ: theo danh sách nhà thầu phụ nêu trong E-HSDT được Chủ đầu tư chấp thuận.',
    'E-ĐKC 6.2': f"Giá trị công việc mà nhà thầu phụ thực hiện không vượt quá: {hd['nha_thau_phu_toi_da_phan_tram']}% giá hợp đồng.",
    'E-ĐKC 10.1': f"Loại hợp đồng: {gt['loai_hop_dong']}.",
    'E-ĐKC 10.2': 'Giá hợp đồng: cố định.' if gt['loai_hop_dong'] == 'trọn gói' else 'Giá hợp đồng: theo loại hợp đồng.',
    'E-ĐKC 11': 'Điều chỉnh thuế: không được phép.',
    'E-ĐKC 13.2': 'Giảm trừ thanh toán: không áp dụng.',
    'E-ĐKC 15': dkc_15(),
    'E-ĐKC 17.4': f"Trường hợp đề xuất giải pháp tiết kiệm chi phí được Chủ đầu tư chấp thuận và giúp giảm giá hợp đồng, Chủ đầu tư thanh toán cho nhà thầu {cs['tiet_kiem_chi_phi_phan_tram']}% giá trị giảm giá hợp đồng.",
    'E-ĐKC 18 (e)': 'Các trường hợp khác: ' + {True: 'Chủ đầu tư cung cấp chậm tài liệu, hạ tầng, môi trường hoặc hoàn thành chậm thay đổi phía hệ thống hiện có so với thời hạn tại mục 3.5 Chương V thì các mốc liên quan được lùi tương ứng số ngày chậm.',
                                               False: 'không có.'}.get(GIA_HAN, dau_cho('có hoặc không lùi mốc khi Chủ đầu tư cung cấp chậm') + '.'),
    'E-ĐKC 21.2': f"Thời gian nhà thầu thực hiện việc thay thế nhân sự: {cs['thay_the_nhan_su_ngay']:02d} ngày kể từ ngày nhận được yêu cầu thay thế nhân sự của Chủ đầu tư.",
    'E-ĐKC 22.2': [f"- Thời gian để tiến hành hòa giải: tối đa {cs['hoa_giai_toi_da_ngay']} ngày.",
                   f"- Giải quyết tranh chấp: nếu hòa giải không thành, một trong hai bên gửi yêu cầu giải quyết tới {cs['co_quan_giai_quyet_tranh_chap']}. Chi phí giải quyết tranh chấp do bên có lỗi chịu theo phán quyết."],
}
dkct_soan = {
    'E-ĐKC 1.5': ('Địa điểm cung cấp dịch vụ: nơi nhà thầu làm việc và nơi hệ thống được triển khai, theo RFP.', ['rfp_yeu_cau.json: dia_diem, he_thong']),
    'E-ĐKC 2.2 (i)': ('Các tài liệu khác là một phần của hợp đồng, gắn với các yêu cầu RFP về đặc tả và thay đổi đặc tả.', ['rfp_yeu_cau.json: nhóm hop_dong, san_pham']),
    'E-ĐKC 6.4': ('Yêu cầu khác về nhà thầu phụ, chuyển yêu cầu thuê ngoài của RFP thành điều khoản.', ['rfp_yeu_cau.json: nhóm hop_dong']),
    'E-ĐKC 12.1': (f"Tạm ứng {hd['tam_ung_phan_tram']}% giá hợp đồng, điều kiện cấp, hồ sơ tạm ứng, bảo lãnh tiền tạm ứng theo Mẫu số 16 Phần 4 nếu tham số yêu cầu, cách thu hồi vào thanh toán theo Mục 13.1 và thời hạn hiệu lực bảo lãnh tạm ứng." if hd['tam_ung_phan_tram'] else 'Ghi: Tạm ứng: không áp dụng.', ['tham_so_chu_dau_tu.json: chinh_sach.tam_ung_phan_tram, bao_lanh_tam_ung', 'gia_tri_tinh.json: hop_dong']),
    'E-ĐKC 13.1': ('Phương thức thanh toán (chuyển khoản), số đợt, mỗi đợt một dòng bắt đầu bằng "- Đợt n: x% giá hợp đồng" kèm sự kiện kích hoạt theo tham số, diễn đạt gắn với sản phẩm của RFP. Đợt gắn sản phẩm nêu các hạng mục được thanh toán theo dạng (hạng mục 1, 2 và 4 Mẫu số 01A) hoặc (hạng mục 5 đến 9 Mẫu số 01A). Mỗi hạng mục của MAU_01A thuộc đúng một đợt, đợt tạm ứng và đợt bảo hành không gắn hạng mục. Mọi bảo lãnh không có biểu mẫu trong Phần 4 (ví dụ bảo lãnh bảo hành) nêu bên phát hành (ngân hàng, tổ chức tín dụng hoặc chi nhánh ngân hàng nước ngoài được thành lập theo pháp luật Việt Nam), giá trị, hiệu lực đến hết thời hạn trách nhiệm đối với sai sót và hình thức, nội dung theo mẫu được Chủ đầu tư chấp thuận. Dòng cuối: hồ sơ thanh toán và thời hạn thanh toán. Tổng các đợt bằng 100%.', ['gia_tri_tinh.json: hop_dong.thanh_toan', 'tham_so_chu_dau_tu.json: chinh_sach.thanh_toan_trong_ngay, bao_lanh_bao_hanh_phan_tram']),
    'E-ĐKC 17.1(c)': ('Nội dung khác về sửa đổi hợp đồng, chuyển yêu cầu thay đổi đặc tả của RFP thành điều khoản: thay đổi chỉ thực hiện khi hai bên thống nhất bằng văn bản.', ['rfp_yeu_cau.json: nhóm hop_dong']),
    'E-ĐKC 20.1': ('Nguyên tắc và cách thức đánh giá chất lượng theo điều khoản kiểm tra, chấp nhận và sửa lỗi của RFP. Thời hạn trách nhiệm đối với sai sót theo RFP (quy đổi ra tháng) kể từ ngày nghiệm thu, bàn giao, và việc duy trì bảo lãnh bảo hành nếu có đợt thanh toán bảo hành.', ['rfp_yeu_cau.json: nhóm hop_dong', 'tham_so_chu_dau_tu.json: chinh_sach.bao_hanh']),
}
h1('Chương VII. Điều kiện cụ thể của hợp đồng')
p('Các nội dung dưới đây được nhập vào webform E-ĐKCT trên Hệ thống, chi tiết hóa và bổ sung nhưng không thay thế điều kiện chung của hợp đồng.')
rows = []
for it in ct['e_dkct']:
    ma = it['ma']
    if ma in dkct_auto:
        rows.append([ma, dkct_auto[ma]])
    else:
        hd_, ng = dkct_soan.get(ma, ('Điền theo hướng dẫn của mẫu.', ['mau5a_cau_truc.json']))
        rows.append([ma, S('DKC_' + re.sub(r'\W+', '_', ma.replace('E-ĐKC', '')).strip('_'), hd_, ng, 'danh_sach_doan', it['noi_dung_mau'])])
rows.append(S('DKC_BO_SUNG', 'Các dòng bổ sung cho điều khoản hợp đồng của RFP không có mục tương ứng trong E-ĐKCT (ví dụ bắt đầu thực hiện ngay sau khi ký, bàn giao đúng địa điểm và thời hạn, quyền sở hữu và bản quyền, bảo mật). Mỗi dòng 2 ô: ô đầu ghi "E-ĐKC <số Điều liên quan của Chương VI> (bổ sung)", ô sau là nội dung. Không lặp nội dung đã có ở các mục khác.', ['rfp_yeu_cau.json: nhóm hop_dong, thu_tuc'], 'dong_bang'))
table(rows, [2100, 7500])
br()

# ---------------- Phần 4
center('Phần 4. Biểu mẫu hợp đồng', 16)
p('Các biểu mẫu dưới đây áp dụng theo Mẫu số 5A ban hành kèm theo Thông tư số 79/2025/TT-BTC. Bảo lãnh thực hiện hợp đồng do nhà thầu trúng thầu hoàn chỉnh trước khi hợp đồng có hiệu lực.')


def ap_dung_p4(ma):
    if ma == 'Mẫu số 14B': return 'Không áp dụng'
    if ma == 'Mẫu số 16': return 'Áp dụng, theo Mục 12.1 E-ĐKCT' if hd['tam_ung_phan_tram'] and cs['bao_lanh_tam_ung'] else 'Không áp dụng, do không có tạm ứng'
    if ma == 'Mẫu số 17': return 'Áp dụng khi có ủy quyền'
    return 'Áp dụng'


tieu_de_p4 = {'Mẫu số 13': 'Thư chấp thuận E-HSDT và trao hợp đồng', 'Mẫu số 14A': 'Hợp đồng điện tử', 'Mẫu số 14B': 'Hợp đồng điện tử (mua sắm tập trung theo thỏa thuận khung)',
              'Mẫu số 15': 'Bảo lãnh thực hiện hợp đồng', 'Mẫu số 16': 'Bảo lãnh tiền tạm ứng', 'Mẫu số 17': 'Giấy ủy quyền'}
table([['STT', 'Biểu mẫu', 'Áp dụng']] + [[str(i + 1), f"{x['ma']}. {tieu_de_p4.get(x['ma'], x['tieu_de'])}", ap_dung_p4(x['ma'])] for i, x in enumerate(ct['phan4'])], [600, 6300, 2700], [0])

meta = {'ten': 'E-HSMT ' + GOI, 'header': 'E-HSMT - Gói thầu dịch vụ phi tư vấn (Mẫu số 5A, TT 79/2025/TT-BTC)', 'font': 'Times New Roman', 'size_pt': 13,
        'page': 'A4', 'margin_twip': {'top': 1134, 'bottom': 1134, 'left': 1417, 'right': 1134}}
json.dump({'meta': meta, 'can_soan': can_soan, 'canh_bao': canh_bao, 'blocks': B}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'Đã lập khung: {len(B)} khối, {len(can_soan)} mục cần agent soạn:')
for c in canh_bao:
    print('CẢNH BÁO:', c)
for k, v in can_soan.items():
    print(f'  {k} ({v["dang"]})')
