"""Tính các bảng của master plan: mục tiêu SMART và phê duyệt của điều lệ dự án, các bên liên quan, thuê ngoài,
huy động vị trí bổ sung, bảo hành, lịch rà soát, việc kết thúc dự án. Kiểm tra đặc tả có đủ mục bắt buộc
(9 kế hoạch con, thay đổi, cấu hình, rà soát, kết thúc).

Dùng: python tinh_bang_ke_hoach.py      (chay.py chuan_bi ke_hoach_tong_the tự gọi, sau qlda-change/scripts/tinh_bang_thay_doi.py)
Ra: du_lieu/ke_hoach_bang.json
Kiểm tra: KH01 đến KH06. Lỗi thì dừng, cảnh báo thì in.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import calendar, datetime as dt, json, os, re, sys  # noqa: E401
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

CFG = json.load(open(os.path.join(HERE, '..', 'references', 'ke_hoach.json'), encoding='utf-8'))
SPEC = json.load(open(os.path.join(HERE, '..', 'dac_ta', 'ke_hoach_tong_the.json'), encoding='utf-8'))
hsmt = loi.doc_json('du_lieu/hsmt.json'); lich = loi.doc_json('du_lieu/lich.json'); cp = loi.doc_json('du_lieu/chi_phi.json')
pc = loi.doc_json('du_lieu/phan_cong.json'); nt = loi.doc_json('dau_vao/nha_thau.json'); da = loi.du_an()
ct = loi.doc_json('dau_vao/chi_tieu_ky_thuat.json', {}); tdb = loi.doc_json('du_lieu/thay_doi_bang.json', {})
tv = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']
VAI = tdb.get('vai_ban', {})
CUT = lich['cut_over']
NGAY_HH = loi.ngay_hien_hanh()
# phụ lục hợp đồng đã ký (CR đã áp dụng): giá hợp đồng sau phụ lục, phê duyệt phiên bản sau thay đổi, đường cơ sở sau thay đổi
PHU_LUC = [dict(c['phu_luc'], ma_cr=c['ma']) for c in loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []}).get('yeu_cau', [])
           if c.get('phu_luc') and (c.get('ap_dung') or {}).get('da_ghi')]
loi_ds, canh_bao = [], []


def kiem_tra_muc_bat_buoc():
    """KH01: đặc tả phải có tiêu đề cho mọi mục bắt buộc khai báo trong kiem_tra.muc_bat_buoc."""
    mbb = SPEC.get('kiem_tra', {}).get('muc_bat_buoc')
    if not mbb:
        return ['KH01 Đặc tả ke_hoach_tong_the.json chưa khai báo kiem_tra.muc_bat_buoc']
    td = [str(kb[k]).lower() for kb in SPEC['khoi'] for k in ('h1', 'h2') if k in kb]
    cum = lambda m: [m] if isinstance(m, str) else ([m['tieu_de']] if isinstance(m['tieu_de'], str) else m['tieu_de'])
    return [f'KH01 Đặc tả thiếu mục bắt buộc {m.get("ten", m) if isinstance(m, dict) else m} (tiêu đề chứa: {", ".join(cum(m))})'
            for m in mbb if not any(p.lower() in t for t in td for p in cum(m))]


def ten(vai):
    return VAI[vai]['ho_ten'] if vai in VAI else ''


def nhan_vai(vai):
    v = VAI.get(vai, {}).get('vai', vai)
    return v[:1].lower() + v[1:]


def cong_thang(ngay, n):
    d = dt.date.fromisoformat(ngay)
    y, m = divmod(d.month - 1 + n, 12)
    return dt.date(d.year + y, m + 1, min(d.day, calendar.monthrange(d.year + y, m + 1)[1])).isoformat()


# ---------------------------------------------------------------- điều lệ dự án
def bang_muc_tieu():
    nx = {k: ten(v) for k, v in CFG['nguoi_xac_nhan'].items()}
    ng = da.get('nguong_canh_bao', {})
    n01a = len(hsmt['mau_01a'])
    rows = [['Bàn giao đủ sản phẩm theo Mẫu số 01A', 'Số hạng mục Mẫu số 01A được nghiệm thu', f'{n01a}/{n01a} hạng mục', loi.ngay(CUT), nx['pham_vi']],
            ['Đưa hệ thống vào vận hành đúng ngày cut over', 'Ngày cut over thực tế', f'Không muộn hơn {loi.ngay(CUT)}', loi.ngay(CUT), nx['cut_over']]]
    for m in lich['moc']:
        if m.get('dot_thanh_toan') and str(m.get('can_cu', ''))[:1].isdigit():
            han = m.get('han') or m['ngay']
            rows.append([f'Đạt mốc {m["ma"]}: {m["ten"]}', f'Ngày ký biên bản mốc, căn cứ thanh toán Đợt {m["dot_thanh_toan"]}', f'Không muộn hơn {loi.ngay(han)}',
                         loi.ngay(han), nx['moc'], tinh_trang_moc(m, han)])
    rows.append(['Giữ tiến độ theo kế hoạch sprint', 'SPI lũy kế cuối mỗi sprint', f'Từ {loi.so(ng.get("spi_vang", 0.95), 2)} trở lên',
                 f'Cuối mỗi sprint đến {loi.ngay(CUT)}', nx['spi']])
    rows.append(['Thực hiện trong đường cơ sở chi phí', 'Chi phí nhân công thực tế lũy kế so với BAC, CPI lũy kế',
                 f'Không vượt {loi.tien(cp["A"])} đồng, CPI từ {loi.so(ng.get("cpi_vang", 0.95), 2)} trở lên', loi.ngay(CUT), nx['chi_phi']])
    han_cl = (da.get('uat') or {}).get('den') or CUT
    rows += [[f'{c["ma"]}: {c["yeu_cau_hsmt"]}', c['cach_kiem_chung'], c['chi_tieu'], loi.ngay(han_cl), nx['chat_luong']] for c in ct.get('chi_tieu', [])]
    bh = ct.get('bao_hanh', {})
    thang = bh.get('thoi_han_thang') or hsmt['hop_dong'].get('bao_hanh_thang')
    muc = '. '.join(f'{x["muc"]}: ' + (f'phản hồi {x["phan_hoi_gio"]} giờ, ' if x.get('phan_hoi_gio') else '') + f'khắc phục {x["khac_phuc"]}'
                    for x in bh.get('muc_loi', []))
    rows.append(['Khắc phục sai sót trong thời hạn bảo hành', 'Thời gian phản hồi và khắc phục lỗi theo mức', muc or 'Theo HSMT',
                 f'{thang} tháng từ {loi.ngay(CUT)}', nx['bao_hanh']])
    if not any(len(r) == 6 and r[5].startswith('Đạt') for r in rows):  # chưa mốc nào đạt (kế hoạch lập trước thực hiện): không có cột tình trạng
        return {'cot': ['Mục tiêu', 'Chỉ số, cách đo', 'Ngưỡng', 'Hạn', 'Người xác nhận'], 'dong': [r[:5] for r in rows],
                'widths': [2300, 2300, 2200, 1200, 1300], 'center_cols': [3]}
    rows = [r if len(r) == 6 else r + [''] for r in rows]
    return {'cot': ['Mục tiêu', 'Chỉ số, cách đo', 'Ngưỡng', 'Hạn', 'Người xác nhận', f'Tình trạng đến {loi.ngay(NGAY_HH)}'], 'dong': rows,
            'widths': [2000, 2000, 2000, 1050, 1150, 1100], 'center_cols': [3]}


def tinh_trang_moc(m, han):
    """Tình trạng của mục tiêu mốc tại ngày lập: đã đạt (đúng hạn hoặc trễ, số ngày làm việc trễ) hoặc chưa đến hạn."""
    if m['ngay'] > NGAY_HH:
        return 'Chưa đến mốc'
    tre = loi.ngay_lam_viec_giua(loi.ngay_lam_viec(da), han, m['ngay']) if han and m['ngay'] > han else 0
    return f'Đạt {loi.ngay(m["ngay"])}' + (f', trễ {tre} ngày làm việc so với hạn, hồ sơ thanh toán Đợt {m["dot_thanh_toan"]} lập từ ngày đạt' if tre else ', đúng hạn')


def bang_phe_duyet():
    moc_kh = next((m for m in lich['moc'] if 'kế hoạch' in m['ten'].lower()), None)
    tg_cdt = f'Mốc {moc_kh["ma"]}, {loi.ngay(moc_kh["ngay"])}' if moc_kh else f'Họp khởi động, {loi.ngay(lich["ngay_bat_dau"])}'
    rows = [['Người lập', da.get('nguoi_lap', ''), loi.ngay(lich['ngay_bat_dau'])],
            ['Phê duyệt phía nhà thầu', VAI.get('dai_dien_nt', {}).get('ten', ''), loi.ngay(lich['ngay_bat_dau'])],
            ['Xác nhận phía Chủ đầu tư', VAI.get('tham_quyen_cdt', VAI.get('dau_moi_cdt', {})).get('ten', ''), tg_cdt]]
    for x in PHU_LUC:  # phiên bản sau yêu cầu thay đổi được phê duyệt cùng phụ lục hợp đồng
        rows += [[f'Phê duyệt phiên bản sau {x["ma_cr"]}, phía nhà thầu', VAI.get('dai_dien_nt', {}).get('ten', ''), loi.ngay(x['ngay'])],
                 [f'Xác nhận phía Chủ đầu tư theo phụ lục hợp đồng {x.get("so", "")}', VAI.get('tham_quyen_cdt', VAI.get('dau_moi_cdt', {})).get('ten', ''),
                  loi.ngay(x['ngay'])]]
    return {'cot': ['Vai trò', 'Họ tên, chức danh', 'Thời điểm'], 'dong': rows, 'widths': [2300, 4800, 2200], 'center_cols': [2]}


# ---------------------------------------------------------------- các bên liên quan
def bang_ben_lien_quan():
    bn = pc.get('ben_ngoai', [])
    if len(bn) <= 1:
        canh_bao.append(f'KH02 Dữ liệu bên liên quan phía Chủ đầu tư chỉ có {len(bn)} dòng (phan_cong ben_ngoai). Bảng lấy thêm từ HSMT, nhà thầu, '
                        'thành viên. Đề nghị nhóm bổ sung bên liên quan vào lam_viec/giao_viec/phan_cong_nhap.json (ben_ngoai)')
    rows = []
    for k in ('tham_quyen_cdt', 'dau_moi_cdt', 'dai_dien_nt', 'qtda'):
        if k not in VAI:
            continue
        b = dict(CFG['ben_lien_quan'][k], **{x: y for e in bn if e.get('ten') == VAI[k]['ten'] for x, y in e.items()
                                              if x in ('vai_tro', 'anh_huong', 'quan_tam', 'cach_tham_gia')})
        rows.append([VAI[k]['ten'], VAI[k]['ben'], b['vai_tro'], b['anh_huong'], b['quan_tam'], b['cach_tham_gia']])
    da_co = {r[0] for r in rows}
    for e in bn:
        if e.get('ten') not in da_co:
            rows.append([e['ten'], 'Chủ đầu tư', e.get('vai_tro', ''), e.get('anh_huong', 'Chưa đánh giá'), e.get('quan_tam', 'Chưa đánh giá'),
                         e.get('cach_tham_gia', 'Theo kế hoạch họp')])
    n_nhom = sum(1 for t in tv if t.get('loai') != 'bo_sung'); n_bs = len(tv) - n_nhom
    d = CFG['ben_lien_quan']['nhom']
    rows.append([f'Nhóm thực hiện: {n_nhom} thành viên nòng cốt, {n_bs} vị trí bổ sung', 'Nhà thầu', d['vai_tro'], d['anh_huong'], d['quan_tam'], d['cach_tham_gia']])
    return {'cot': ['Bên liên quan', 'Bên', 'Vai trò', 'Ảnh hưởng', 'Quan tâm', 'Cách tham gia'], 'dong': rows,
            'widths': [2100, 1000, 2000, 900, 900, 2400], 'center_cols': [1, 3, 4]}


# ---------------------------------------------------------------- mua sắm, thuê ngoài, huy động
def bang_thue_ngoai():
    hd = hsmt['hop_dong']; e = hsmt.get('e_dkct', {})
    ntp = nt.get('nha_thau_phu') or []
    rows = [['Nhà thầu phụ', 'Không sử dụng nhà thầu phụ theo E-HSDT' if not ntp else ', '.join(str(x.get('ten', x)) if isinstance(x, dict) else str(x) for x in ntp),
             f'Mục 6.1, 6.2 E-ĐKCT, tối đa {hd.get("nha_thau_phu_toi_da_phan_tram", "")}% giá hợp đồng']]
    if e.get('E-ĐKC 6.4'):
        rows.append(['Thuê ngoài', re.sub(r'\s+', ' ', e['E-ĐKC 6.4']).strip(), 'Mục 6.4 E-ĐKCT'])
    else:
        canh_bao.append('KH03 HSMT không có Mục 6.4 E-ĐKCT về thuê ngoài, kiểm tra du_lieu/hsmt.json')
    return {'cot': ['Nội dung', 'Quy định', 'Căn cứ'], 'dong': rows, 'widths': [1700, 5400, 2200]}


def bang_huy_dong():
    sp = {s['so']: s for s in lich['sprint']}
    rows, thieu = [], []
    for t in tv:
        if t.get('loai') != 'bo_sung':
            continue
        s = sp.get(t.get('tu_sprint') or 1, lich['sprint'][0])
        co = bool(t.get('trinh_do')) and t.get('so_nam_kinh_nghiem') is not None
        thieu += [] if co else [t['ho_ten']]
        # trình độ ghi theo yêu cầu khi huy động (khóa _nguon_trinh_do) chưa phải hồ sơ cá nhân
        tt = ('Đã có yêu cầu tối thiểu, hồ sơ cá nhân bổ sung trước sprint huy động' if co and t.get('_nguon_trinh_do')
              else 'Đã có' if co else 'Chưa có trình độ, kinh nghiệm')
        rows.append([t['ho_ten'], t.get('chuc_danh', ''), s['ma'], loi.ngay(s['tu']), tt])
    if thieu:
        canh_bao.append(f'KH06 {len(thieu)} vị trí bổ sung chưa có trình độ, kinh nghiệm trong dau_vao/thanh_vien.json: {", ".join(thieu)}')
    return {'cot': ['Người dự kiến', 'Vị trí', 'Huy động từ', 'Ngày bắt đầu', 'Hồ sơ năng lực'], 'dong': rows,
            'widths': [2000, 3100, 1100, 1300, 1800], 'center_cols': [2, 3]}


def kiem_tra_khoan_b():
    if len(cp.get('chi_phi_khac', [])) <= 1:
        canh_bao.append('KH03 Khoản B chưa có danh mục chi tiết (dau_vao/don_gia.json chi_phi_khac chỉ có một dòng), kế hoạch mua sắm chỉ nêu được tổng. '
                        'Đề nghị nhóm tách môi trường, công cụ, bảo hành, dự phòng rồi chạy lại cost estimate')


# ---------------------------------------------------------------- chất lượng, rà soát, kết thúc
def bang_bao_hanh():
    rows = [[x['muc'], f'{x["phan_hoi_gio"]} giờ' if x.get('phan_hoi_gio') else 'Trong thời hạn khắc phục', x['khac_phuc']]
            for x in ct.get('bao_hanh', {}).get('muc_loi', [])]
    return {'cot': ['Mức lỗi', 'Thời gian phản hồi', 'Thời hạn khắc phục'], 'dong': rows, 'widths': [3100, 3100, 3100], 'center_cols': [0, 1, 2]}


def thanh_phan(m):
    return ', '.join([nhan_vai(v) for v in m['vai'] if v in VAI] + ([m['them']] if m.get('them') else []))


def bang_ra_soat():
    c = CFG['ra_soat']
    rows = [(s['den'], c['sprint']['noi_dung'].format(**s), thanh_phan(c['sprint']), c['sprint']['dau_ra']) for s in lich['sprint']]
    rows += [(m['ngay'], c['moc']['noi_dung'].format(**m), thanh_phan(c['moc']), c['moc']['dau_ra']) for m in lich['moc'] if m['ngay'] > lich['ngay_bat_dau']]
    kt = lich.get('ngay_dong_du_an') or ct.get('bao_hanh', {}).get('ho_tro_tang_cuong', {}).get('den') or CUT  # ngày đóng dự án của giai đoạn Kết thúc
    rows.append((kt, c['ket_thuc']['noi_dung'], thanh_phan(c['ket_thuc']), c['ket_thuc']['dau_ra']))
    return {'cot': ['Thời điểm', 'Hoạt động rà soát', 'Thành phần', 'Đầu ra'],
            'dong': [[loi.ngay(r[0])] + list(r[1:]) for r in sorted(rows, key=lambda r: r[0])], 'widths': [1200, 3300, 2400, 2400], 'center_cols': [0]}


def bang_ket_thuc():
    hd = hsmt['hop_dong']; e = hsmt.get('e_dkct', {}); bh = ct.get('bao_hanh', {})
    thang = bh.get('thoi_han_thang') or hd.get('bao_hanh_thang')
    rows = [(m['ngay'], f'Đạt mốc {m["ma"]}: {m["ten"]}', loi.ngay(m['ngay']), f'Đợt {m["dot_thanh_toan"]}, Mục 13.1 E-ĐKCT' if m.get('dot_thanh_toan') else 'Lịch dự án')
            for m in lich['moc'] if m['ngay'] >= CUT]
    so_pl = {x['ma_cr']: x.get('so', '') for x in PHU_LUC}
    rows += [(t['ngay'], f'Hồ sơ thanh toán Đợt {t["dot"]}, {loi.tien(t["so_tien"])} đồng', f'Dự kiến nhận {loi.ngay(t["ngay"])}',
              f'Phụ lục hợp đồng {so_pl.get(t["ma_cr"], "")}' if t.get('ma_cr') else 'Mục 13.1 E-ĐKCT')
             # đợt có ngày nhận sau cut over (cả đợt của phụ lục có sự kiện trước cut over như Đợt 6 gắn M9) theo dõi khi đóng dự án, từ 1.2.4
             for t in cp.get('thanh_toan', []) if max(t.get('ngay_su_kien', ''), t.get('ngay', '')) >= CUT]
    ht = bh.get('ho_tro_tang_cuong')
    if ht:
        rows.append((ht['tu'], 'Hỗ trợ tăng cường sau cut over', f'{loi.ngay(ht["tu"])} đến {loi.ngay(ht["den"])}', 'Cam kết bảo hành của nhà thầu'))
        dong = lich.get('ngay_dong_du_an') or ht['den']
        rows.append((dong, 'Rà soát kết thúc dự án, báo cáo tổng kết, đánh giá, bài học kinh nghiệm',
                     f'Ngày đóng dự án {loi.ngay(dong)}' if lich.get('ngay_dong_du_an') else f'Sau {loi.ngay(ht["den"])}', 'Lịch rà soát'))
    het_bh = cong_thang(CUT, int(thang))
    rows.append((het_bh, f'Bảo hành, bảo lãnh bảo hành {hd.get("bao_lanh_bao_hanh_phan_tram", "")}% giá hợp đồng', f'{loi.ngay(CUT)} đến {loi.ngay(het_bh)}',
                 f'{thang} tháng theo HSMT'))
    n = re.search(r'trong vòng (\d+) ngày', e.get('E-ĐKC 5.4', ''))
    # hiệu lực bảo đảm thực hiện: theo phụ lục hợp đồng gần nhất có gia hạn (bao_dam_thuc_hien_den, qlda-change từ 1.4.6), không có thì theo HSMT
    pl_bd = next((x for x in reversed(PHU_LUC) if x.get('bao_dam_thuc_hien_den')), None)
    hl_bd = pl_bd['bao_dam_thuc_hien_den'] if pl_bd else hsmt.get('thoi_han', {}).get('hieu_luc_bao_dam_thuc_hien_den', '')
    rows.append((het_bh, f'Nhận lại bảo đảm thực hiện hợp đồng {hd.get("bao_dam_thuc_hien_phan_tram", "")}% giá hợp đồng',
                 (f'Trong {n.group(1)} ngày sau khi hoàn thành nghĩa vụ hợp đồng' if n else 'Sau khi hoàn thành nghĩa vụ hợp đồng')
                 + f', bảo đảm có hiệu lực đến {loi.ngay(hl_bd) if pl_bd else ngay_chu(hl_bd)}', 'Mục 5.2, 5.4 E-ĐKCT' + (f', phụ lục hợp đồng {pl_bd["so"]}' if pl_bd else '')))
    return {'cot': ['Việc', 'Thời điểm', 'Căn cứ'], 'dong': [list(r[1:]) for r in sorted(rows, key=lambda r: r[0])],
            'widths': [4300, 2900, 2100], 'center_cols': [1]}


def ngay_chu(v):
    """Ngày viết dạng 'dd tháng mm năm yyyy' (nguyên văn HSMT) -> dd/mm/yyyy, giá trị khác giữ nguyên."""
    m = re.fullmatch(r'\s*(\d{1,2}) tháng (\d{1,2}) năm (\d{4})\s*', str(v or ''))
    return f'{int(m.group(1)):02d}/{int(m.group(2)):02d}/{m.group(3)}' if m else v


def bang_cam_ket_cdt():
    rows = [[x['ma'], x['noi_dung'], loi.ngay(x['han']) if x.get('han') else 'Theo nội dung cam kết'] for x in da.get('cam_ket_chu_dau_tu', [])]
    return {'cot': ['Mã', 'Cam kết của Chủ đầu tư (giả định của kế hoạch)', 'Hạn'], 'dong': rows, 'widths': [800, 6400, 2100], 'center_cols': [0, 2]}


def emv():
    """Tổng EMV theo triệu đồng kèm khoảng khi sổ rủi ro có, ngược lại theo đồng. Có rủi ro đã xảy ra hoặc đã đóng thì nêu thêm EMV còn lại."""
    th = loi.doc_json('du_lieu/rui_ro.json', {}).get('tong_hop', {})
    if all(k in th for k in ('tong_emv_trieu', 'tong_emv_trieu_thap', 'tong_emv_trieu_cao')):
        s_ = f'{loi.so(th["tong_emv_trieu"], 0)} triệu đồng, khoảng từ {loi.so(th["tong_emv_trieu_thap"], 0)} đến {loi.so(th["tong_emv_trieu_cao"], 0)} triệu đồng'
        if th.get('so_da_xay_ra') or th.get('so_da_dong'):
            s_ += (f'. EMV còn lại của {th.get("so_con_mo", 0)} rủi ro chưa xảy ra, chưa đóng là {loi.so(th.get("tong_emv_trieu_con_lai", 0), 0)} triệu đồng')
        return s_
    return f'{loi.tien(th.get("tong_emv_tien", cp.get("tong_emv_rui_ro", 0)))} đồng'


def bang_duong_co_so():
    """Đường cơ sở đã lập (du_lieu/phien_ban.json): BL1 khi ký hợp đồng, BLn sau yêu cầu thay đổi kèm phụ lục."""
    pl = {x['ma_cr']: x for x in PHU_LUC}
    rows = [[x['ma'], x.get('ten', ''), loi.ngay(x['ngay']), 'Ký hợp đồng' if x.get('hop_dong') else
             (f'Yêu cầu thay đổi {x["ma_cr"]}' + (f', phụ lục hợp đồng {pl[x["ma_cr"]].get("so", "")}' if x['ma_cr'] in pl else '')
              if x.get('ma_cr') else 'Quyết định của nhóm'), str(len(x.get('tai_lieu', {})))]
            for x in loi.doc_json('du_lieu/phien_ban.json', {}).get('duong_co_so', [])]
    return {'cot': ['Mã', 'Đường cơ sở', 'Ngày', 'Căn cứ', 'Số tài liệu'], 'dong': rows, 'widths': [700, 3600, 1200, 3000, 800], 'center_cols': [0, 2, 4]}


loi_ds += kiem_tra_muc_bat_buoc()
loi_ds += [f'KH05 Chưa có vai {k} trong du_lieu/thay_doi_bang.json, chạy qlda-change/scripts/tinh_bang_thay_doi.py trước' for k in ('qtda', 'dai_dien_nt') if k not in VAI]
if not ct.get('chi_tieu'):
    loi_ds.append('KH04 dau_vao/chi_tieu_ky_thuat.json chưa có danh sách chi_tieu, tiêu chí nghiệm thu không lập được. Đề nghị điều phối viên bổ sung')
if loi_ds:
    loi.thoat_loi('\n- '.join([''] + loi_ds))
kiem_tra_khoan_b()
DCS_HIEN_HANH = (loi.doc_json('du_lieu/phien_ban.json', {}).get('duong_co_so') or [{}])[-1].get('ma', '')  # rỗng khi chưa ký hợp đồng
out = {'muc_tieu': bang_muc_tieu(), 'phe_duyet': bang_phe_duyet(), 'ben_lien_quan': bang_ben_lien_quan(), 'thue_ngoai': bang_thue_ngoai(),
       'huy_dong': bang_huy_dong(), 'bao_hanh': bang_bao_hanh(), 'ra_soat': bang_ra_soat(), 'ket_thuc': bang_ket_thuc(), 'cam_ket_cdt': bang_cam_ket_cdt(),
       'emv': emv(), 'duong_co_so': bang_duong_co_so(),
       'nhan_gia': 'Giá hợp đồng sau phụ lục' if PHU_LUC else ('Giá hợp đồng' if loi.da_ky_hop_dong() else 'Giá hợp đồng dự kiến'),
       'phu_luc_goc': ''.join(f', phụ lục hợp đồng {x.get("so", "")}' for x in PHU_LUC),
       'duong_co_so_hien_hanh': DCS_HIEN_HANH,
       'cau_duong_co_so': (f'Các đường cơ sở đã lập theo sổ phiên bản, đường cơ sở hiện hành là {DCS_HIEN_HANH}:' if DCS_HIEN_HANH
                           else 'Đến ngày lập kế hoạch chưa đặt đường cơ sở.'),
       'so_ben_ngoai': len(pc.get('ben_ngoai', [])), 'so_khoan_b': len(cp.get('chi_phi_khac', []))}
for c in canh_bao:
    print('CẢNH BÁO: ' + c)
loi.ghi_json('du_lieu/ke_hoach_bang.json', out)
print(f'Đã tính bảng master plan: {len(out["muc_tieu"]["dong"])} mục tiêu, {len(out["ben_lien_quan"]["dong"])} bên liên quan, '
      f'{len(out["ra_soat"]["dong"])} lần rà soát')
