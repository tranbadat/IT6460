"""Quy ước dùng chung của các script HSMT: tham số Chủ đầu tư bắt buộc, dấu chờ, sổ phát hiện, cách kết luận.

- Tham số bắt buộc còn null: lap_khung.py giữ câu mẫu kèm dấu [Chủ đầu tư quyết định ...],
  verify_hsmt.py ghi TS01 và kết luận cho_nguoi_dung (chưa hoàn tất, chờ người dùng).
- Sổ phát hiện <thu_muc_lam_viec>/so_phat_hien.json: chay_quy_trinh.py ghi_nhan cập nhật cuối mỗi vòng
  (sau lớp B), chay_quy_trinh.py giai_trinh ghi giải trình. verify_hsmt.py chỉ đọc sổ và mang
  các phát hiện còn mở của vòng trước sang vòng đang kiểm tra (PH01).
Kết luận: chua_dat khi còn lỗi chưa giải trình; cho_nguoi_dung khi không còn lỗi nhưng còn tham số chờ
Chủ đầu tư hoặc phát hiện mở của vòng trước; dat khi không còn mục nào.
"""
import hashlib, json, os, re

TEN_SO = 'so_phat_hien.json'
DAU_CHO = 'Chủ đầu tư quyết định'  # dấu chờ trong HSMT có dạng [Chủ đầu tư quyết định ...]
MA_TINH_LAI = ('TS01', 'PH01')  # tính lại mỗi lần kiểm tra, không ghi vào sổ

BEN = {'chu_dau_tu': 'Chủ đầu tư cung cấp', 'nha_thau': 'Nhà thầu cung cấp, chi phí tính trong giá dự thầu'}
HA_TANG = (('may_chu', 'Máy chủ vận hành hệ thống'),
           ('duong_truyen', 'Đường truyền kết nối internet và kết nối tới hệ thống hiện có'),
           ('phan_mem_nen', 'Phần mềm nền (hệ điều hành, hệ quản trị cơ sở dữ liệu, máy chủ ứng dụng) và bản quyền'),
           ('moi_truong_kiem_thu', 'Môi trường phát triển và kiểm thử hệ thống'))
DO_PHI_CHUC_NANG = ('nha_thau_de_xuat',)  # hoặc đối tượng {so_nguoi_dung_dong_thoi, ty_le_san_sang_phan_tram}
# phan_dinh.thoi_han_ha_tang: ngày dd/mm Chủ đầu tư bàn giao, tinh_gia_tri.py tính ngày đầy đủ
THOI_HAN_HA_TANG = (('moi_truong_thu_he_thong_hien_co', 'môi trường thử của hệ thống hiện có'),
                    ('ha_tang_van_hanh_chinh_thuc', 'hạ tầng vận hành chính thức (máy chủ, đường truyền, phần mềm nền do Chủ đầu tư cung cấp)'),
                    ('thay_doi_he_thong_hien_co', 'thay đổi phía hệ thống hiện có do Chủ đầu tư thực hiện'))
# phan_dinh.cau_hinh_ha_tang: 'nha_thau_de_xuat' hoặc {may_chu, duong_truyen, phan_mem_nen: cấu hình do Chủ đầu tư nêu}
CAU_HINH_HA_TANG = ('nha_thau_de_xuat',)
HA_TANG_CHU_DAU_TU = ('may_chu', 'duong_truyen', 'phan_mem_nen')
KIEM_THU_VAN_HANH = {'ha_tang_chinh_thuc': 'Thực hiện trên hạ tầng vận hành chính thức',
                     'moi_truong_kiem_thu': 'Thực hiện trên môi trường kiểm thử do nhà thầu cung cấp'}
THAY_DOI_HE_THONG = {'chu_dau_tu': 'Chủ đầu tư thực hiện, nhà thầu chịu trách nhiệm phía hệ thống mới',
                     'nha_thau': 'Nhà thầu thực hiện, chi phí tính trong giá dự thầu'}
THUE_GTGT = ('khong_chiu_thue', 'chiu_thue')  # chinh_sach.thue_gtgt_goi_thau, ghi chú (6) Bảng số 01
# Đoạn quy phạm Mục 2.2 Chương III Mẫu 5A (huong_dan_chuong3 của mau5a_cau_truc.json), chép nguyên văn theo cụm mở đầu
DOAN_2_2_NHAN_SU = ('Trường hợp E-HSMT có yêu cầu về nhân sự chủ chốt', 'Trường hợp nhân sự chủ chốt mà nhà thầu kê khai',
                    'Yêu cầu về nhân sự chủ chốt được số hóa')
DOAN_2_2_C = 'c) Trường hợp nhà thầu trúng thầu'
LIEN_HE_CDT = (('dia_chi', 'địa chỉ'), ('dien_thoai', 'điện thoại'), ('fax', 'fax'), ('so_tai_khoan', 'số tài khoản'), ('ma_so_thue', 'mã số thuế'))

# (đường dẫn trong tham_so_chu_dau_tu.json, vị trí trong HSMT)
THAM_SO_BAT_BUOC = (
    *[(f'chu_dau_tu.{k}', f'E-BDL 5.1 (c), 7.5, 38.1, E-ĐKC 1.3, 4.1, {ten} của Chủ đầu tư') for k, ten in LIEN_HE_CDT],
    ('chinh_sach.thue_gtgt_goi_thau', 'Bảng số 01 dòng 3, thuế GTGT trong giá gói thầu (ghi chú (6))'),
    ('chinh_sach.hop_dong_tuong_tu_cong_gop', 'Bảng số 01 dòng 4, cho cộng gộp hạng mục tương tự hay không (ghi chú (11))'),
    ('chinh_sach.phat_khong_huy_dong_nhan_su_phan_tram_ngay', 'E-ĐKC 15, tỷ lệ phạt mỗi ngày không huy động nhân sự chủ chốt'),
    ('chinh_sach.gia_han_khi_chu_dau_tu_cung_cap_cham', 'E-ĐKC 18 (e) và Chương V mục 3.5, lùi mốc khi Chủ đầu tư cung cấp chậm'),
    ('chinh_sach.phat_khac_phuc_sai_sot_phan_tram', 'E-ĐKC 15, tỷ lệ phạt khi không kịp thời khắc phục sai sót'),
    ('chinh_sach.boi_thuong_thiet_hai', 'E-ĐKC 15, cách bồi thường thiệt hại'),
    *[(f'phan_dinh.ha_tang_ben_cung_cap.{k}', f'Chương V mục 3.5, {ten.lower()}') for k, ten in HA_TANG],
    ('phan_dinh.thong_tin_he_thong_hien_co', 'Chương V mục 3.5, thông tin và giao diện của hệ thống hiện có'),
    ('phan_dinh.dieu_kien_do_phi_chuc_nang', 'Chương V mục 3.5, điều kiện đo các yêu cầu phi chức năng'),
    *[(f'phan_dinh.thoi_han_ha_tang.{k}', f'Chương V mục 3.5, thời hạn bàn giao {ten}') for k, ten in THOI_HAN_HA_TANG],
    ('phan_dinh.kiem_thu_van_hanh_tren', 'Chương V mục 3.5, môi trường kiểm thử vận hành'),
    ('phan_dinh.cau_hinh_ha_tang', 'Chương V mục 3.5, cấu hình máy chủ, đường truyền, phần mềm nền do Chủ đầu tư cung cấp'),
    ('phan_dinh.thay_doi_he_thong_hien_co', 'Chương V mục 3.5, bên thực hiện thay đổi phía hệ thống hiện có'),
)


def md5_tep(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def vong_cua_word(p):
    """(vòng, md5 nội dung nguồn) build_hsmt.py ghi vào thuộc tính version, identifier của tệp Word. Chuỗi rỗng nếu không có."""
    import docx
    cp = docx.Document(p).core_properties
    return (cp.version or '').strip(), (cp.identifier or '').strip()


def lay(d, duong_dan):
    """Giá trị theo đường dẫn a.b.c, None khi thiếu khóa hoặc null."""
    for k in duong_dan.split('.'):
        if not isinstance(d, dict) or d.get(k) is None:
            return None
        d = d[k]
    return d


def tham_so_thieu(ts):
    return [(k, vt) for k, vt in THAM_SO_BAT_BUOC if lay(ts, k) is None]


def dau_cho(noi_dung=''):
    return f'[{DAU_CHO}{": " + noi_dung if noi_dung else ""}]'


# ---------------- Hạng mục Mẫu số 01A gắn từng đợt thanh toán (E-ĐKC 13.1)
# Quy ước viết: mỗi dòng "- Đợt n: ..." của đợt gắn sản phẩm nêu "(hạng mục 1, 2 và 4 Mẫu số 01A)" hoặc "(hạng mục 5 đến 9 Mẫu số 01A)"
MAU_HANG_MUC = re.compile(r'hạng mục ((?:\d+|,|\s|và|đến)+?)\s*(?:của\s+)?Mẫu số 01A', re.I)


def mo_rong_so(chuoi):
    """'1, 2 và 4' -> [1, 2, 4]; '5 đến 7' -> [5, 6, 7]."""
    tok, out, i = re.findall(r'\d+|đến', chuoi), [], 0
    while i < len(tok):
        if tok[i] != 'đến' and i + 2 < len(tok) and tok[i + 1] == 'đến' and tok[i + 2] != 'đến':
            out += list(range(int(tok[i]), int(tok[i + 2]) + 1)); i += 3
        else:
            out += [int(tok[i])] if tok[i] != 'đến' else []; i += 1
    return out


def hang_muc_theo_dot(van_13_1):
    """{đợt: [STT hạng mục Mẫu số 01A]} đọc từ văn bản Mục 13.1 E-ĐKCT."""
    out = {}
    for m in re.finditer(r'Đợt (\d+):(.*?)(?=Đợt \d+:|$)', van_13_1, re.S):
        out[int(m.group(1))] = [s for g in MAU_HANG_MUC.finditer(m.group(2)) for s in mo_rong_so(g.group(1))]
    return out


# ---------------- Sổ phát hiện

def lop(f):
    return 'B' if f['ma'].startswith('MH') else 'A'


def khoa(f):
    gon = lambda s: re.sub(r'\s+', ' ', str(s or '')).strip()
    return f"{f['ma']}|{gon(f.get('mo_ta'))[:160]}|{gon(f.get('vi_tri'))[:80]}"


def doc_so(wd):
    p = os.path.join(wd, TEN_SO)
    if not os.path.exists(p):
        return {'vong': 0, 'phat_hien': []}
    return json.load(open(p, encoding='utf-8'))


def ghi_so(wd, so):
    json.dump(so, open(os.path.join(wd, TEN_SO), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def can_ghi_so(f):
    # lớp B ghi mọi phát hiện; lớp A ghi lỗi và phát hiện cần người dùng
    if f['ma'] in MA_TINH_LAI:
        return False
    return lop(f) == 'B' or f['muc_do'] == 'loi' or f.get('cach_sua') == 'can_nguoi_dung'


def mang_sang(phat_hien, so):
    """Danh sách mới: đánh dấu phát hiện mới trùng mục mở hoặc đã giải trình trong sổ, thêm PH01 cho mục lớp B còn mở."""
    theo_khoa = {x['khoa']: x for x in so['phat_hien'] if x['trang_thai'] in ('mo', 'giai_trinh')}
    out = []
    for f in phat_hien:
        x = theo_khoa.get(khoa(f))
        if x is None:
            out.append(dict(f))
        elif x['trang_thai'] == 'giai_trinh':
            out.append({**f, 'id_so': x['id'], 'giai_trinh': x['giai_trinh']})
        else:
            out.append({**f, 'id_so': x['id'], 'mang_sang': True})
    for x in so['phat_hien']:
        if x['trang_thai'] == 'mo' and x['lop'] == 'B':
            out.append(dict(ma='PH01', muc_do=x['muc_do'], nhom='phat_hien_mo', vi_tri=x.get('vi_tri', ''), id_so=x['id'],
                            mo_ta=f"Phát hiện {x['id']} ({x['ma']}) của vòng {x['vong_phat_hien']} chưa đóng: {x['mo_ta']}",
                            cach_sua='can_nguoi_dung', de_xuat='Khắc phục rồi để lớp B xác nhận đóng, hoặc ghi giải trình bằng chay_quy_trinh.py giai_trinh'))
    return out


def chan(f):
    """Phát hiện làm HSMT chưa hoàn tất."""
    if f.get('giai_trinh'):
        return False
    return f['muc_do'] == 'loi' or f['ma'] in MA_TINH_LAI or bool(f.get('mang_sang'))


def ket_luan(phat_hien):
    c = [f for f in phat_hien if chan(f)]
    if any(f['muc_do'] == 'loi' for f in c):
        return 'chua_dat'
    return 'cho_nguoi_dung' if c else 'dat'


def ket_luan_lop_a(phat_hien):
    """Chỉ xét lỗi mới của lớp A, dùng cho vòng tạo, sửa tự động trong hoan_thien."""
    moi = [f for f in phat_hien if f['ma'] not in MA_TINH_LAI and lop(f) == 'A' and not f.get('giai_trinh')]
    return 'chua_dat' if any(f['muc_do'] == 'loi' for f in moi) else 'dat'


def _dong(x, vong, ghi_chu):
    return {**x, 'trang_thai': 'da_dong', 'vong_dong': vong, 'ghi_chu_dong': ghi_chu}


def hop_nhat(so, bao_cao):
    """Sổ mới sau một vòng: đóng mục được lớp B xác nhận, đóng mục lớp A không còn, thêm phát hiện mới. Trả (sổ, lỗi)."""
    vong = so['vong'] + 1
    dong = {x.get('id'): (x.get('ghi_chu') or '').strip() for x in bao_cao.get('dong_phat_hien', [])}
    hien = {khoa(f) for f in bao_cao.get('phat_hien', []) if f['ma'] not in MA_TINH_LAI}
    mo = {x['id'] for x in so['phat_hien'] if x['trang_thai'] == 'mo'}
    loi = [f'dong_phat_hien: {i} không phải phát hiện đang mở' for i in dong if i not in mo]
    loi += [f'dong_phat_hien: {i} thiếu ghi_chu cách đã xác nhận' for i, g in dong.items() if i in mo and not g]
    items = []
    for x in so['phat_hien']:
        if x['trang_thai'] == 'mo' and dong.get(x['id']):
            items.append(_dong(x, vong, dong[x['id']]))
        elif x['trang_thai'] == 'mo' and x['lop'] == 'A' and x['khoa'] not in hien:
            items.append(_dong(x, vong, f'Lớp A vòng {vong} không còn phát hiện'))
        else:
            items.append(x)
    da_co = {x['khoa'] for x in items if x['trang_thai'] in ('mo', 'giai_trinh')}
    n = len(items)
    for f in bao_cao.get('phat_hien', []):
        k = khoa(f)
        if not can_ghi_so(f) or k in da_co:
            continue
        n += 1
        da_co.add(k)
        items.append({'id': f'PH{n:03d}', 'lop': lop(f), 'khoa': k, 'vong_phat_hien': vong, 'trang_thai': 'mo',
                      **{t: f.get(t, '') for t in ('ma', 'muc_do', 'nhom', 'vi_tri', 'mo_ta', 'cach_sua', 'de_xuat')}})
    return {'vong': vong, 'phat_hien': items}, loi


def ket_luan_vong(so, bao_cao):
    """Kết luận cuối vòng: tham số chờ Chủ đầu tư (TS01) cộng mọi mục còn mở trong sổ."""
    ts01 = [f for f in bao_cao.get('phat_hien', []) if f['ma'] == 'TS01']
    mo = [{**x, 'mang_sang': True} for x in so['phat_hien'] if x['trang_thai'] == 'mo']
    return ket_luan(ts01 + mo), ts01, mo
