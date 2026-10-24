"""Tính các bảng của kế hoạch quản lý thay đổi: phân loại, điều kiện, thẩm quyền và thời hạn, ban kiểm soát thay đổi,
ma trận lan truyền theo sơ đồ phụ thuộc, mẫu phiếu yêu cầu thay đổi, nhánh đóng, quy tắc dùng dự phòng, hạng mục cấu hình, sổ thay đổi.

Dùng: python tinh_bang_thay_doi.py      (chay.py chuan_bi ke_hoach_thay_doi và ke_hoach_tong_the tự gọi)
Ra: du_lieu/thay_doi_bang.json
Kiểm tra: TD01 đến TD09 (quy_tac_thay_doi.py). Lỗi thì dừng, cảnh báo thì in.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json, os, subprocess, sys  # noqa: E401
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import quy_tac_thay_doi as qt  # noqa: E402
loi = qt.loi

PL, loi_ds, canh_bao = qt.nap_phan_loai()
MAU = json.load(open(os.path.join(HERE, '..', 'references', 'mau_phieu_cr.json'), encoding='utf-8'))
cp = loi.doc_json('du_lieu/chi_phi.json'); pc = loi.doc_json('du_lieu/phan_cong.json'); hsmt = loi.doc_json('du_lieu/hsmt.json')
lich = loi.doc_json('du_lieu/lich.json'); wbs = loi.doc_json('du_lieu/wbs.json'); nt = loi.doc_json('dau_vao/nha_thau.json')
tv = {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']}
so = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})

VAI, l2, c2 = qt.vai_ban(pc, tv, nt, hsmt)
loi_ds += l2 + qt.kiem_tra_ky_phu_luc(PL, VAI)
canh_bao += c2 + qt.kiem_tra_can_cu(PL, hsmt)
for c in canh_bao:
    print('CẢNH BÁO: ' + c)
if loi_ds:
    loi.thoat_loi('\n- '.join([''] + loi_ds))


def nguong(v, fn):
    return 'Trên ngưỡng mức trung bình' if v is None else fn(v)


def chu_thuong_dau(s):
    return s[:1].lower() + s[1:]


def bang_phan_loai():
    return {'cot': ['Mức', 'Điểm tác động', 'MD tăng tối đa', 'Chi phí nội bộ tối đa, đồng', 'Tiêu hao dự trữ tối đa, ngày', 'Chậm cut over tối đa, ngày', 'Phạm vi áp dụng'],
            'dong': [[m['ten'], f'{m["diem"][0]}-{m["diem"][1]}', nguong(m['md_toi_da'], loi.md), nguong(m['chi_phi_toi_da'], loi.tien),
                      nguong(m['tieu_hao_du_tru_toi_da'], str), nguong(m['ngay_cham_cut_over_toi_da'], str), m['pham_vi']] for m in PL['muc']],
            'widths': [900, 900, 1000, 1300, 1100, 1000, 3100], 'center_cols': [0, 1, 2, 3, 4, 5]}


def thoi_han_quyet_dinh(m):
    s = f'{m["thoi_han_quyet_dinh_ngay"]} ngày làm việc sau khi có đánh giá'
    return (f'Họp ban kiểm soát thay đổi trong {m["hop_ban_trong_ngay"]} ngày làm việc từ khi nhận yêu cầu, quyết định ' + chu_thuong_dau(s)
            if m.get('hop_ban_trong_ngay') else s)


def bang_tham_quyen():
    return {'cot': ['Mức', 'Người phê duyệt', 'Thời hạn đánh giá', 'Thời hạn quyết định', 'Văn bản'],
            'dong': [[m['ten'], m['nguoi_phe_duyet'], f'{m["thoi_han_danh_gia_ngay"]} ngày làm việc từ khi tiếp nhận', thoi_han_quyet_dinh(m),
                      m['van_ban']] for m in PL['muc']], 'widths': [900, 2600, 1500, 2000, 2300], 'center_cols': [0]}


def bang_dieu_kien():
    ten_muc = {m['ma']: m['ten'] for m in PL['muc']}
    return {'cot': ['Điều kiện', 'Mức tối thiểu', 'Căn cứ', 'Cách xác định'],
            'dong': [[d['ten'], ten_muc[d['muc']], d['can_cu'], 'Công cụ của nhóm tính từ lịch' if d.get('tu_dong') else 'Người đánh giá khai báo, quản trị dự án xác nhận']
                     for d in PL['dieu_kien']], 'widths': [3600, 1100, 2300, 2300], 'center_cols': [1]}


def tham_quyen_cua(vai):
    return '. '.join(f'{m["ten"]}: {chu_thuong_dau(m["tham_quyen"][vai])}' for m in PL['muc'] if vai in m['tham_quyen'])


def bang_ccb():
    rows = []
    for k, ten_vai in PL['vai_ban'].items():
        if k in VAI:
            v = VAI[k]
            rows.append([v['ten'], v['ben'], ten_vai + (', chủ trì' if k == 'qtda' else '') + (', ký phụ lục hợp đồng' if v['ky_phu_luc'] else ''),
                         tham_quyen_cua(k)])
    da = {VAI['qtda']['id']}
    for x in pc.get('trach_nhiem', []):  # người chịu trách nhiệm nhóm WBS mức 1: tham dự, đánh giá tác động
        if x.get('muc') == 1 and x['A'] not in da and x['A'] in tv:
            da.add(x['A'])
            rows.append([f'{tv[x["A"]]["ho_ten"]}, {tv[x["A"]].get("chuc_danh", "")}', 'Nhà thầu', 'Tham dự khi thay đổi thuộc nhóm công việc phụ trách',
                         'Đánh giá tác động, không quyết định'])
    return {'cot': ['Thành viên', 'Bên', 'Vai trò trong ban', 'Thẩm quyền theo mức'], 'dong': rows, 'widths': [2500, 1100, 2200, 3500], 'center_cols': [1]}


def bang_lan_truyen():
    nut = [('wbs', 'Phạm vi, WBS'), ('phan_cong', 'Giao việc'), ('thanh_vien', 'Thành viên, quỹ thời gian'), ('lich', 'Lịch, mốc'), ('don_gia', 'Đơn giá'),
           ('rui_ro', 'Sổ rủi ro'), ('du_an', 'Lịch làm việc, ngày nghỉ')]
    rows = []
    for n, ten in nut:
        r = subprocess.run([sys.executable, os.path.join(loi.THU_MUC_LOI, 'scripts', 'chay.py'), 'anh_huong', n, '--json'], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', cwd=loi.GOC)
        ds = json.loads(r.stdout)['anh_huong']
        rows.append([ten, ', '.join(b['ten'] for b in ds if not b['khoa']), ', '.join(b['ten'] for b in ds if b['khoa']) or 'Không'])
    return {'cot': ['Thay đổi ở', 'Tài liệu phải cập nhật (theo thứ tự)', 'Đường cơ sở đấu thầu bị ảnh hưởng'], 'dong': rows, 'widths': [1900, 5600, 1800]}


def bang_mau_phieu():
    return {'cot': ['Phần', 'Trường thông tin', 'Người ghi'], 'dong': [[x['phan'], x['ten'], x['nguoi_dien']] for x in MAU['truong']],
            'widths': [1300, 5000, 3000], 'center_cols': [0]}


def bang_dong():
    return {'cot': ['Kết quả quyết định', 'Điều kiện đóng yêu cầu', 'Người đóng'], 'dong': [[x['ket_qua'], x['dieu_kien'], x['nguoi']] for x in PL['dong']],
            'widths': [1700, 5800, 1800], 'center_cols': [0]}


def bang_du_phong():
    ten = {k: f'{ten_vai} {VAI[k]["ho_ten"]}' if k in VAI else ten_vai for k, ten_vai in PL['vai_ban'].items()}
    dp = f'{loi.tien(cp["du_phong_hien_co"])} đồng' + (', nằm trong khoản chi phí khác' if cp.get('cach_tinh_du_phong') == 'nam_trong_chi_phi_khac' else '')
    th = loi.doc_json('du_lieu/rui_ro.json', {}).get('tong_hop', {})
    emv = (f'{loi.so(th["tong_emv_trieu"], 0)} triệu đồng, khoảng từ {loi.so(th["tong_emv_trieu_thap"], 0)} đến {loi.so(th["tong_emv_trieu_cao"], 0)} triệu đồng'
           if all(k in th for k in ('tong_emv_trieu', 'tong_emv_trieu_thap', 'tong_emv_trieu_cao')) else f'{loi.tien(cp["tong_emv_rui_ro"])} đồng')
    rows = [['Dự phòng hiện có', dp], ['Tổng EMV của sổ rủi ro', emv]]
    if th.get('so_da_xay_ra') or th.get('so_da_dong'):
        rows.append(['EMV còn lại (rủi ro chưa xảy ra, chưa đóng)', f'{loi.so(th.get("tong_emv_trieu_con_lai", 0), 0)} triệu đồng của {th.get("so_con_mo", 0)} rủi ro, '
                     f'{th.get("so_da_xay_ra", 0) + th.get("so_da_dong", 0)} rủi ro đã xảy ra hoặc đã đóng'])
    rows += [[x['noi_dung'], x['quy_dinh'].format_map(ten)] for x in PL['du_phong']['quy_tac']]
    return {'cot': ['Nội dung', 'Quy định'], 'dong': rows, 'widths': [2300, 7000]}


def bao_dong_truoc(dich, truoc):
    """Các gói lá đứng trước (kể cả chính) các gói đích theo phụ thuộc trong WBS."""
    kq, hang = set(dich), list(dich)
    while hang:
        for p in truoc.get(hang.pop(), []):
            if p not in kq:
                kq.add(p)
                hang.append(p)
    return kq


def moc_va_bao_dong():
    """[(mốc, tập gói lá phải xong trước mốc)] theo ngày. Mốc cut over có ngày cố định bao mọi gói, mốc khởi động bỏ qua."""
    la = {g['ma']: g for g in wbs['goi'] if g.get('la')}
    truoc = {m: [p if isinstance(p, str) else p.get('ma') for p in g.get('phu_thuoc', [])] for m, g in la.items()}
    out = []
    for m in sorted(lich['moc'], key=lambda m: (m['ngay'], loi.khoa_ma(m['ma'][1:]))):
        cc = str(m.get('can_cu', ''))
        if cc[:1].isdigit():
            out.append((m, bao_dong_truoc([g for c in cc.split(',') for g in la if g == c.strip() or g.startswith(c.strip() + '.')], truoc)))
        elif m['ngay'] == lich['cut_over']:
            out.append((m, set(la)))
    return out


def bang_cau_hinh():
    """Hạng mục cấu hình theo Mẫu 01A: nhóm WBS tạo ra, mốc đặt đường cơ sở (mốc sớm nhất mà các gói phải xong trước nó chiếm
    từ một nửa MD của hạng mục), người phụ trách (người thực hiện gói lớn nhất). Không tính gói thuộc nhóm quản lý dự án."""
    lg = {g['ma']: g for g in lich['goi'] if g.get('la')}
    nhom_qldt = {g['ma'].split('.')[0] for g in wbs['goi'] if g.get('la') and g.get('loai') == 'PM'}
    pm = min((g for g in wbs['goi'] if g.get('la') and g.get('loai') == 'PM'), key=lambda g: loi.khoa_ma(g['ma']), default={'cha': ''})
    rows = [['Kế hoạch dự án: WBS, master schedule, cost estimate (đường cơ sở phạm vi, tiến độ, chi phí)', pm['cha'], 'Ký hợp đồng', VAI['qtda']['ho_ten']]]
    mbd = moc_va_bao_dong()
    cr_ap = [c for c in so['yeu_cau'] if c.get('phu_luc') and (c.get('ap_dung') or {}).get('da_ghi') and c.get('goi_moi')]
    goi_cr = {g['ma'] for c in cr_ap for g in c['goi_moi']}  # gói mới của CR có đường cơ sở riêng theo phụ lục
    for h in hsmt['mau_01a']:
        goi = [g for g in wbs['goi'] if g.get('la') and h['stt'] in g.get('hang_muc_01a', []) and g['ma'].split('.')[0] not in nhom_qldt
               and g['ma'] not in goi_cr]
        tong = sum(float(g['md']) for g in goi)
        if not goi or not tong:
            continue
        m = next((m for m, bd in mbd if sum(float(g['md']) for g in goi if g['ma'] in bd) >= tong / 2), mbd[-1][0])
        chinh = max(goi, key=lambda g: (float(g['md']), loi.khoa_ma(g['ma'])))
        nhom = sorted({g['cha'] for g in goi}, key=loi.khoa_ma)
        rows.append([f'{h["stt"]}. {h["danh_muc"]}', ', '.join(nhom), f'{m["ma"]}, {loi.ngay(m["ngay"])}', lg.get(chinh['ma'], {}).get('ho_ten_R', '')])
    for c in cr_ap:
        gm = [g['ma'] for g in c['goi_moi'] if g['ma'] in lg]
        xn = next((m for m in gm if 'xác nhận' in lg[m].get('ten', '').lower()), '')
        chinh = max(gm, key=lambda m: (float(lg[m].get('md') or 0), loi.khoa_ma(m)), default='')
        rows.append([f'Phần thay đổi {c["ma"]}: {c["tieu_de"]}', ', '.join(sorted({m.rsplit('.', 1)[0] for m in gm}, key=loi.khoa_ma)),
                     f'Phụ lục {c["phu_luc"].get("so", "")}, {loi.ngay(c["phu_luc"].get("ngay"))}' + (f'; đặc tả tại gói {xn}, {loi.ngay(lg[xn]["ket_thuc"])}' if xn else ''),
                     lg.get(chinh, {}).get('ho_ten_R', '')])
    return {'cot': ['Hạng mục cấu hình', 'Nhóm WBS tạo ra', 'Đường cơ sở tại mốc', 'Người phụ trách'], 'dong': rows,
            'widths': [4100, 1800, 1700, 1700], 'center_cols': [1, 2]}


def so_thay_doi():
    return [{'ma': c['ma'], 'tieu_de': c['tieu_de'], 'ngay': c['ngay_de_xuat'], 'md_tang': c['md_tang'], 'chi_phi_tang': c['chi_phi_tang'],
             'gia_de_nghi': c.get('gia_de_nghi'), 'ngay_cham': c['ngay_cham'], 'ngay_cham_cut_over': c.get('ngay_cham_cut_over', 0),
             'tieu_hao_du_tru': c.get('tieu_hao_du_tru', 0), 'diem_tac_dong': c.get('diem_tac_dong'), 'muc_ten': c['muc_ten'],
             'trang_thai': c['trang_thai'], 'van_ban': c.get('van_ban', ''), 'phu_luc_so': (c.get('phu_luc') or {}).get('so', ''),
             'gia_hop_dong_sau': (c.get('phu_luc') or {}).get('gia_hop_dong_sau'),
             'ma_rui_ro': ', '.join(rui_ro_cua(c)) or 'Không'} for c in so['yeu_cau']]


def rui_ro_cua(c):
    """Rủi ro liên kết CR: mã rủi ro của phiếu và rủi ro trong sổ ghi lien_ket_cr là mã CR (rủi ro mới phát sinh từ CR)."""
    ds = loi.doc_json('du_lieu/rui_ro.json', {'danh_sach': []}).get('danh_sach', [])
    return list(dict.fromkeys(list(c.get('ma_rui_ro', [])) + sorted(r['ma'] for r in ds if c['ma'] in (r.get('lien_ket_cr') or []))))


cr = so_thay_doi()
loi.ghi_json('du_lieu/thay_doi_bang.json', {
    'phan_loai': bang_phan_loai(), 'tham_quyen': bang_tham_quyen(), 'dieu_kien': bang_dieu_kien(), 'ccb': bang_ccb(), 'lan_truyen': bang_lan_truyen(),
    'mau_phieu': bang_mau_phieu(), 'nhanh_dong': bang_dong(), 'du_phong': bang_du_phong(), 'cau_hinh': bang_cau_hinh(), 'so_thay_doi': cr, 'so_cr': len(cr),
    'vai_ban': {k: {'ten': v['ten'], 'ho_ten': v['ho_ten'], 'ben': v['ben'], 'vai': PL['vai_ban'].get(k, '')} for k, v in VAI.items()},
    'don_gia_md_binh_quan': round(cp['A'] / cp['tong_md']), 'don_gia_de_nghi_md_binh_quan': round(cp['gia_chao'] / cp['tong_md']),
    'he_so_gia': round(cp['gia_chao'] / cp['A'], 4), 'can_cu_gia_de_nghi': PL['gia_de_nghi']['can_cu'], 'mo_ta_gia_de_nghi': qt.he_so_gia(PL, cp, wbs)[1],
    'thoi_han_danh_gia_cam_ket_ngay': PL.get('cam_ket_danh_gia_ngay'), 'cut_over_co_dinh': bool(PL.get('cut_over_co_dinh')),
    'thang_diem': PL['thang_diem']['cach_tinh'], 'trang_thai': ', '.join(PL['trang_thai'])})
print(f'Đã tính bảng thay đổi: {len(PL["muc"])} mức, ban kiểm soát {len(VAI)} vai, {len(cr)} yêu cầu thay đổi trong sổ')
