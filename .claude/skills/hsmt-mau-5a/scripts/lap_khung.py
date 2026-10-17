"""Bước 4. Lập khung HSMT.

Dùng: python3 lap_khung.py <mau5a_cau_truc.json> <tham_so_chu_dau_tu.json> <rfp_yeu_cau.json> <gia_tri_tinh.json> <hsmt_khung.json>

Khung có đủ cấu trúc theo Mẫu 5A. Các mục cơ học (tên, số liệu, mục Hệ thống trích xuất, cột cố định của mẫu)
được điền sẵn. Các mục cần diễn đạt nội dung từ RFP để dạng <<SOẠN:ID>> và mô tả trong khóa "can_soan"
(hướng dẫn của mẫu, nguồn dữ liệu, dạng kết quả). Agent Soạn thảo chỉ viết file ban_soan.json cho các ID này.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json, re, sys

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


def S(id_, huong_dan, nguon, dang='doan', mau_goc=''):
    can_soan[id_] = {'huong_dan': huong_dan, 'nguon': nguon, 'dang': dang, 'mau_goc': mau_goc}
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
for t in ['Mô tả tóm tắt', 'Phần 1. Thủ tục đấu thầu', '    Chương I. Chỉ dẫn nhà thầu', '    Chương II. Bảng dữ liệu đấu thầu',
          '    Chương III. Tiêu chuẩn đánh giá E-HSDT', '    Chương IV. Biểu mẫu mời thầu và dự thầu', 'Phần 2. Yêu cầu về kỹ thuật',
          '    Chương V. Yêu cầu về kỹ thuật', 'Phần 3A. Điều kiện hợp đồng', '    Chương VI. Điều kiện chung của hợp đồng',
          '    Chương VII. Điều kiện cụ thể của hợp đồng', 'Phần 4. Biểu mẫu hợp đồng']:
    p(t)
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
    return ([f"Bảo đảm cạnh tranh trong đấu thầu theo quy định như sau: Nhà thầu tham dự thầu không có cổ phần hoặc vốn góp trên 30% với: {CDT}, {cdt['dia_chi']}.",
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
    'E-CDNT 7.5': (f"Hội nghị tiền đấu thầu: Có. Thời gian: {hn['gio']}, ngày {hn['ngay']}. Địa điểm: <<SOẠN:DIA_DIEM_HOI_NGHI>>. Người chịu trách nhiệm tổ chức: {NGUOI_LH}, email {EMAIL}." if hn else 'Hội nghị tiền đấu thầu: Không.'),
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
    'E-CDNT 34.1': f"Tỷ lệ tăng khối lượng tối đa là: {cs['ty_le_tang_giam_khoi_luong_phan_tram']}%. Tỷ lệ giảm khối lượng tối đa là: {cs['ty_le_tang_giam_khoi_luong_phan_tram']}%.",
    'E-CDNT 34.2': 'Tùy chọn mua thêm: ' + ('có áp dụng.' if cs['mua_them'] else 'không áp dụng.'),
    'E-CDNT 38.1': [f"- Người có thẩm quyền: {cdt['nguoi_co_tham_quyen']}.", f"+ Địa chỉ: {cdt['dia_chi']}.",
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
yeu_cau = {
    '1': f"Từ ngày {nl['moc_lich_su_hop_dong']} đến thời điểm đóng thầu, nhà thầu không có từ 02 hợp đồng trở lên (cung cấp dịch vụ phi tư vấn) không hoàn thành do lỗi của nhà thầu.",
    '2': f"Đã thực hiện nghĩa vụ kê khai thuế và nộp thuế của năm tài chính gần nhất so với thời điểm đóng thầu (năm {nl['nam_tai_chinh_gan_nhat']}).",
    '3': f"Áp dụng. Doanh thu bình quân hằng năm (không bao gồm thuế VAT) của {len(nl['cac_nam_doanh_thu']):02d} năm tài chính gần nhất so với thời điểm đóng thầu (các năm {', '.join(map(str, nl['cac_nam_doanh_thu']))}) tối thiểu là {tien['doanh_thu_binh_quan_toi_thieu']} đồng, xác định theo cách tính đối với gói thầu có thời gian thực hiện dưới 12 tháng với hệ số k bằng {str(nl['he_so_k']).replace('.', ',')}.",
    '4': f"Áp dụng. Từ ngày {nl['moc_hop_dong_tuong_tu']} đến thời điểm đóng thầu, nhà thầu đã hoàn thành tối thiểu 01 hợp đồng tương tự với tư cách là nhà thầu chính, thành viên liên danh hoặc nhà thầu phụ, có giá trị tối thiểu {tien['hop_dong_tuong_tu_toi_thieu']} đồng ({nl['ty_le_hop_dong_tuong_tu']}% giá gói thầu), hoặc có các hạng mục công việc tương tự trong các hợp đồng khác nhau với tổng giá trị tối thiểu {tien['hop_dong_tuong_tu_toi_thieu']} đồng theo hướng dẫn của Mẫu số 5A. Hợp đồng tương tự là hợp đồng {cs['dinh_nghia_hop_dong_tuong_tu']}.",
}
b01_rows = [['TT', 'Mô tả', 'Yêu cầu', 'Nhà thầu độc lập', 'Liên danh: tổng các thành viên', 'Liên danh: từng thành viên', 'Tài liệu cần nộp']]
for r in data_rows:
    mo_ta = re.sub(r'\(\d\)', '', r[1]).strip()
    b01_rows.append([r[0], mo_ta, yeu_cau[r[0]], r[3], r[4], r[5], r[6]])  # các cột liên danh, tài liệu: lấy nguyên từ mẫu
table(b01_rows, [560, 1450, 2950, 1150, 1150, 1250, 1090])
h2('2.2. Tiêu chuẩn đánh giá về nhân sự chủ chốt và thiết bị chủ yếu')
p('a) Nhân sự chủ chốt. ' + S('NHAN_SU_LY_DO', 'Một đến hai câu nêu lý do gói thầu cần nhân sự chủ chốt, căn cứ tính chất công việc trong RFP (xây dựng hệ thống, tích hợp hệ thống hiện có). Câu tiếp theo nêu nhân sự có thể thuộc biên chế hoặc do nhà thầu huy động, kê khai theo Mẫu số 06A, 06B, 06C và phải chứng minh khả năng huy động.',
                                 ['rfp_yeu_cau.json: he_thong, pham_vi', 'mau5a_cau_truc.json: huong_dan_chuong3']))
p('Bảng số 02. Yêu cầu về nhân sự chủ chốt (webform trên Hệ thống)')
table([[re.sub(r'\(\d\)$', '', c) for c in ct['bang02'][0]]] + [[str(i + 1), x['vi_tri'], str(x['so_luong']), x['kinh_nghiem'][0].upper() + x['kinh_nghiem'][1:], 'Không yêu cầu'] for i, x in enumerate(ts['nhan_su_chu_chot'])],
      [600, 2400, 900, 3800, 1900], [0, 2])
p('b) Thiết bị chủ yếu: ' + ('theo yêu cầu của Chủ đầu tư.' if cs['thiet_bi_chu_yeu'] else 'không yêu cầu, do gói thầu không cần thiết bị đặc chủng.'))
h2('Mục 3. Tiêu chuẩn đánh giá về kỹ thuật')
p(f"Áp dụng phương pháp chấm điểm theo thang điểm 100. Mức điểm yêu cầu tối thiểu về kỹ thuật là {kt['tong_toi_thieu']} điểm, bằng {kt['tong_toi_thieu']}% tổng số điểm tối đa. Mỗi tiêu chí tổng quát phải đạt tối thiểu mức điểm nêu tại bảng dưới đây. Tiêu chuẩn đánh giá được xây dựng trên các sản phẩm đầu ra nêu tại Chương V. Đề xuất kỹ thuật của nhà thầu trình bày đủ các nội dung nêu tại mục 4 Chương V.")
kt_rows = [['STT', 'Tiêu chí tổng quát', 'Điểm tối đa', 'Điểm tối thiểu']]
for i, (w, m) in enumerate(zip(kt['trong_so'], kt['diem_toi_thieu'])):
    kt_rows.append([str(i + 1), S(f'TIEU_CHI_{i + 1}', f'Tên và phạm vi tiêu chí tổng quát thứ {i + 1} (trọng số {w} điểm). Năm tiêu chí phải phủ đủ các nội dung đề xuất của RFP, sắp theo thứ tự: (1) hiểu biết mục tiêu và giải pháp kỹ thuật tổng thể, nêu các yêu cầu phi chức năng của RFP; (2) phạm vi, sản phẩm đầu ra, phương pháp và bảo đảm chất lượng; (3) kế hoạch, tiến độ đến ngày cut over, tổ chức, nhân sự, kế hoạch họp; (4) vai trò, trách nhiệm, quản lý thay đổi, rủi ro, bảo hành; (5) điều kiện khác, đề nghị của nhà thầu, đề xuất khác có lợi, thông tin về kết quả thực hiện hợp đồng theo Điều 19 và Điều 20 của Nghị định số 214/2025/NĐ-CP. Không đưa giá vào tiêu chí kỹ thuật.', ['rfp_yeu_cau.json: noi_dung_de_xuat, yeu_cau nhóm chinh_sach']), str(w), str(m)])
kt_rows.append(['', 'Tổng cộng', '100', str(kt['tong_toi_thieu'])])
table(kt_rows, [600, 6000, 1500, 1500], [0, 2, 3])
p(f"E-HSDT đạt yêu cầu về kỹ thuật khi tổng điểm kỹ thuật không thấp hơn {kt['tong_toi_thieu']} điểm và từng tiêu chí tổng quát không thấp hơn mức điểm tối thiểu.")
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
      ('3. Yêu cầu kỹ thuật của gói thầu', 'C5_3', 'Các đoạn đánh số 3.1 mô hình hệ thống mới (chức năng, cơ sở dữ liệu, hệ thống liên quan, giữ tên tiếng Anh của RFP trong ngoặc), 3.2 phạm vi (nêu rõ phạm vi theo RFP và phần ngoài phạm vi), 3.3 sản phẩm đầu ra (đủ các sản phẩm bàn giao của RFP), 3.4 yêu cầu phi chức năng.'),
      ('4. Giải pháp và phương pháp luận', 'C5_4', 'Nêu nhà thầu chuẩn bị đề xuất gồm (1) giải pháp và phương pháp luận, (2) kế hoạch công tác theo hướng dẫn của mẫu, và phải trình bày đủ các nội dung đề xuất RFP yêu cầu. Chi phí ước tính kèm lý do trình bày trong đề xuất tài chính theo Mẫu số 11A, không chấm điểm kỹ thuật. Viết thành các câu ngắn, hạn chế dấu chấm phẩy.'),
      ('5. Quy định về kiểm tra, nghiệm thu sản phẩm', 'C5_5', 'Quy trình bàn giao, kiểm tra theo đặc tả, thông báo kết quả, kiểm tra đạt là chấp nhận sản phẩm, biên bản nghiệm thu là căn cứ thanh toán theo Mục 13.1 E-ĐKCT.')]
for tieu_de, id_, hd_ in c5:
    h2(tieu_de)
    p(S(id_, hd_, ['rfp_yeu_cau.json', 'mau5a_cau_truc.json: huong_dan_chuong5', 'gia_tri_tinh.json: lich'], 'danh_sach_doan'))
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
so_vn = lambda v: str(v).replace('.', ',')


def dkc_15():
    # Nguyên văn Mục 15 E-ĐKCT của Mẫu 5A. Tỷ lệ phạt khắc phục sai sót và cách bồi thường là lựa chọn của chủ đầu tư.
    pkss, bt = cs.get('phat_khac_phuc_sai_sot_phan_tram'), cs.get('boi_thuong_thiet_hai')
    phat = (f"1. Phạt vi phạm hợp đồng: Áp dụng. Trừ trường hợp bất khả kháng theo quy định tại Mục 16 E-ĐKC, nếu Nhà thầu không thực hiện một phần hay toàn bộ nội dung công việc theo đúng thời hạn đã nêu trong hợp đồng thì Chủ đầu tư có thể khấu trừ vào giá hợp đồng một khoản tiền phạt tương ứng với {so_vn(cs['phat_cham_tien_do_phan_tram_ngay'])}%/ngày giá trị công việc chậm thực hiện cho đến khi nội dung công việc đó được thực hiện. "
            f"Chủ đầu tư sẽ khấu trừ đến {so_vn(cs['phat_toi_da_phan_tram'])}% giá trị phần hợp đồng bị vi phạm. Khi đạt đến mức phạt tối đa, Chủ đầu tư có thể xem xét chấm dứt hợp đồng theo quy định tại Mục 19 E-ĐKC.")
    if pkss is None:
        canh_bao.append('Thiếu tham số chinh_sach.phat_khac_phuc_sai_sot_phan_tram: E-ĐKC 15 chưa có tỷ lệ phạt khi không kịp thời khắc phục sai sót')
    else:
        phat += f" Trường hợp không kịp thời khắc phục sai sót theo thông báo của Chủ đầu tư, Nhà thầu có trách nhiệm nộp tiền phạt thực hiện hợp đồng tương ứng với {so_vn(pkss)}% chi phí cần thiết để khắc phục sai sót."
    if bt is None:
        canh_bao.append('Thiếu tham số chinh_sach.boi_thuong_thiet_hai: E-ĐKC 15 chưa chọn cách bồi thường thiệt hại')
        boi = '2. Bồi thường thiệt hại: Áp dụng theo quy định của pháp luật dân sự.'
    elif bt == 'toan_bo_thiet_hai_thuc_te':
        boi = '2. Bồi thường thiệt hại: Áp dụng. Bồi thường thiệt hại trên cơ sở toàn bộ thiệt hại thực tế.'
    else:
        boi = f'2. Bồi thường thiệt hại: Áp dụng. Bồi thường thiệt hại trên cơ sở một mức xác định: {bt}.'
    return ['Vừa áp dụng phạt vi phạm hợp đồng vừa áp dụng bồi thường thiệt hại.', phat, boi]


dkct_auto = {
    'E-ĐKC 1.3': f"Chủ đầu tư: {CDT}, {cdt['dia_chi']}; đại diện: {cdt['nguoi_dai_dien']}. Số tài khoản, mã số thuế, điện thoại được ghi khi hoàn thiện hợp đồng.",
    'E-ĐKC 1.11': 'Nhà thầu: nhà thầu trúng thầu. Tên, địa chỉ, số tài khoản, mã số thuế được ghi khi hoàn thiện hợp đồng.',
    'E-ĐKC 4.1': f"Các thông báo gửi về Chủ đầu tư theo địa chỉ: người nhận {NGUOI_LH}, địa chỉ {cdt['dia_chi']}, e-mail {EMAIL}.",
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
    'E-ĐKC 18 (e)': 'Các trường hợp khác: không có.',
    'E-ĐKC 21.2': f"Thời gian nhà thầu thực hiện việc thay thế nhân sự: {cs['thay_the_nhan_su_ngay']:02d} ngày kể từ ngày nhận được yêu cầu thay thế nhân sự của Chủ đầu tư.",
    'E-ĐKC 22.2': [f"- Thời gian để tiến hành hòa giải: tối đa {cs['hoa_giai_toi_da_ngay']} ngày.",
                   f"- Giải quyết tranh chấp: nếu hòa giải không thành, một trong hai bên gửi yêu cầu giải quyết tới {cs['co_quan_giai_quyet_tranh_chap']}. Chi phí giải quyết tranh chấp do bên có lỗi chịu theo phán quyết."],
}
dkct_soan = {
    'E-ĐKC 1.5': ('Địa điểm cung cấp dịch vụ: nơi nhà thầu làm việc và nơi hệ thống được triển khai, theo RFP.', ['rfp_yeu_cau.json: dia_diem, he_thong']),
    'E-ĐKC 2.2 (i)': ('Các tài liệu khác là một phần của hợp đồng, gắn với các yêu cầu RFP về đặc tả và thay đổi đặc tả.', ['rfp_yeu_cau.json: nhóm hop_dong, san_pham']),
    'E-ĐKC 6.4': ('Yêu cầu khác về nhà thầu phụ, chuyển yêu cầu thuê ngoài của RFP thành điều khoản.', ['rfp_yeu_cau.json: nhóm hop_dong']),
    'E-ĐKC 12.1': (f"Tạm ứng {hd['tam_ung_phan_tram']}% giá hợp đồng, điều kiện cấp, hồ sơ tạm ứng, bảo lãnh tiền tạm ứng theo Mẫu số 16 Phần 4 nếu tham số yêu cầu, cách thu hồi vào thanh toán theo Mục 13.1 và thời hạn hiệu lực bảo lãnh tạm ứng." if hd['tam_ung_phan_tram'] else 'Ghi: Tạm ứng: không áp dụng.', ['tham_so_chu_dau_tu.json: chinh_sach.tam_ung_phan_tram, bao_lanh_tam_ung', 'gia_tri_tinh.json: hop_dong']),
    'E-ĐKC 13.1': ('Phương thức thanh toán (chuyển khoản), số đợt, mỗi đợt một dòng bắt đầu bằng "- Đợt n: x% giá hợp đồng" kèm sự kiện kích hoạt theo tham số, diễn đạt gắn với sản phẩm của RFP. Đợt bảo hành nêu giá trị bảo lãnh bảo hành và hiệu lực đến hết thời hạn trách nhiệm đối với sai sót. Dòng cuối: hồ sơ thanh toán và thời hạn thanh toán. Tổng các đợt bằng 100%.', ['gia_tri_tinh.json: hop_dong.thanh_toan', 'tham_so_chu_dau_tu.json: chinh_sach.thanh_toan_trong_ngay, bao_lanh_bao_hanh_phan_tram']),
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
