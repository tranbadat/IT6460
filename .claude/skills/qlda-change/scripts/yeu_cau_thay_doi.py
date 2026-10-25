"""Ghi, đánh giá tác động, ra quyết định, áp dụng, ghi nhận kết quả kiểm tra và đóng yêu cầu thay đổi (CR). Sổ thay đổi: du_lieu/thay_doi.json.

Dùng:
  python yeu_cau_thay_doi.py danh_gia <cr_nhap.json> [--them-nguoi <tệp json> ...]
      Đánh giá CR do agent hoặc người dùng lập:
      {"ma": "CR03" (tùy chọn), "tieu_de", "mo_ta", "ly_do", "nguoi_de_xuat", "ngay": "yyyy-mm-dd", "nguon": "chủ đầu tư | nhà thầu | rủi ro RRxx",
       "noi_bo": false, "dieu_kien": ["doi_pham_vi"], "ma_rui_ro": ["RR01"], "can_cu_hsmt": "Mục 17.1(a) E-ĐKC",
       "nhan_dinh_ban_dau": "...", "rui_ro_moi": "...", "ngay_bat_dau": "yyyy-mm-dd" (tùy chọn),
       "goi_thay_doi": [{"ma": "7.3.1", "md_tang": 3, "them_phu_thuoc": ["9.3.3"]}],
       "muc_moi": [{"ma": "9", "ten": "...", "can_cu_uoc_luong": {...}}, {"ma": "9.1", "ten": "..."}],
       "goi_moi": [{"ma": "9.1.1", "ten": "...", "md": 6, "loai": "BA", "cha": "9.1", "san_pham": "...", "phu_thuoc": ["2.1.7"],
                    "hang_muc_01a": [9], "nguon": ["R12"], "thoi_luong_toi_thieu": 5, "R": "K", "ho_tro": []}],
       "nut_thay_doi": ["..."] (tùy chọn, nút sơ đồ phụ thuộc ngoài các nút công cụ tự xác định)}
      noi_bo: true chỉ khi là thay đổi nội bộ của nhà thầu, không đổi cam kết với Chủ đầu tư (mới được xếp mức nhỏ).
      dieu_kien: điều kiện người đánh giá khai báo trong references/phan_loai.json (cham_dac_ta, doi_pham_vi, doi_gia, cam_ket_cdt).
      Tính: MD tăng, chi phí nội bộ (MD x đơn giá loại công việc), giá đề nghị Chủ đầu tư. Đưa gói mới và gói thay đổi vào lịch thật bằng
      lap_lich.py trên bản sao (scripts/lich_thay_doi.py): ngày kết thúc mới, số ngày cut over phải lùi, mốc gắn đợt thanh toán bị dời,
      tiêu hao dự trữ, khả năng theo quỹ, chuỗi dài nhất, có cần thêm người. --them-nguoi (lặp được) thử phương án nhân sự
      ({"thanh_vien": [...], "giao_viec": [{ma, R, ho_tro}]}), mỗi tệp một phương án them_nguoi (hoặc them_nguoi_1, them_nguoi_2...).
      Điểm tác động 1-10, mức, người phê duyệt, hạn đánh giá và quyết định, tài liệu phải cập nhật (gồm dữ liệu nguồn như uoc_luong.json),
      tài liệu khóa, cần phụ lục hợp đồng. Ghi CR trạng thái Chờ phê duyệt.
  python yeu_cau_thay_doi.py quyet_dinh <ma_cr> --ket-qua "Đã phê duyệt|Từ chối|Hoãn" --nguoi "<người quyết định>" [--ngay yyyy-mm-dd]
      [--van-ban "<số, ngày văn bản thống nhất hoặc phụ lục>"] (bắt buộc khi phê duyệt mức lớn) [--xem-lai yyyy-mm-dd] (bắt buộc khi hoãn)
      [--phuong-an hien_tai|them_nguoi|them_nguoi_n] [--ghi-chu ...]
  python yeu_cau_thay_doi.py ap_dung <ma_cr> [--ghi] [--so-phu-luc "..."] [--ngay-phu-luc yyyy-mm-dd] [--gia <đồng>] [--cut-over yyyy-mm-dd] [--gia-han-bao-dam yyyy-mm-dd]
      [--dot-thanh-toan <tệp json>] [--ngay ...]
      Chỉ sau quyết định Đã phê duyệt. Sinh đề xuất thay đổi dữ liệu nguồn trong lam_viec/thay_doi/<ma_cr>/de_xuat/ (scripts/ap_dung_thay_doi.py),
      ghi phụ lục hợp đồng (số, ngày, giá điều chỉnh, cut over mới, mốc thanh toán điều chỉnh) và thứ tự chạy lại các bước. --ghi áp thẳng vào tệp.
      Mặc định: số phụ lục theo --van-ban của quyết định, ngày theo ngày quyết định, giá theo giá đề nghị, cut over theo kết quả đánh giá.
      Đề xuất dời mọi ngày phụ thuộc cut over trong dau_vao (hỗ trợ tăng cường của chi_tieu_ky_thuat.json, giai đoạn Kết thúc khai báo ngày),
      cảnh báo TD25 khi hiệu lực bảo đảm thực hiện của HSMT sớm hơn ngày đóng dự án mới.
      --dot-thanh-toan: đợt thanh toán riêng của phần giá điều chỉnh [{"dot", "su_kien", "phan_tram_gia_dieu_chinh", "moc", "nguon"}].
  python yeu_cau_thay_doi.py phu_luc <ma_cr> --dot-thanh-toan <tệp json> [--ngay yyyy-mm-dd] [--nguoi ...] [--ghi-chu ...]
      Ghi đợt thanh toán riêng của phần giá điều chỉnh cho phụ lục của CR đã áp dụng (theo quyết định hai bên). Các đợt gốc tính trên giá
      hợp đồng ban đầu, đợt đã thu trước ngày phụ lục không tính lại (qlda-cost-estimate). Chạy lại chi_phi và các bước sau.
  python yeu_cau_thay_doi.py thuc_hien <ma_cr> --kiem-tra "<kết quả kiểm tra đạt, biên bản>" --nguoi "<người kiểm tra>" [--ngay yyyy-mm-dd]
  python yeu_cau_thay_doi.py dong <ma_cr> --ghi-chu "<đã cập nhật tài liệu nào | lý do đã thông báo>" [--ngay yyyy-mm-dd] [--nguoi ...] [--bo-qua-kiem-tra]
      CR đã thực hiện: chỉ đóng khi dữ liệu nguồn đã áp dụng, mọi tài liệu trong tai_lieu_cap_nhat có phiên bản sau quyết định, dùng đầu vào
      mới, và CR có phụ lục hoặc mức lớn đã có đường cơ sở sau thay đổi (so_phien_ban.py duong_co_so BLn --cr <ma_cr>). Báo cáo theo kỳ (anh_chup) không chặn đóng CR. CR từ chối hoặc hoãn đóng với ghi chú lý do đã thông báo người đề xuất.
  --ngay là ngày theo lịch dự án (biên bản họp, email phê duyệt), mặc định là ngày chạy lệnh. Thời gian xử lý CR tính từ ngày đề xuất đến ngày này.
  python yeu_cau_thay_doi.py danh_sach
Kiểm tra: TD10 đến TD25 (lỗi dừng, cảnh báo in).
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse, datetime as dt, json, os, re, subprocess, sys  # noqa: E401
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import quy_tac_thay_doi as qt  # noqa: E402
import lich_thay_doi as ltd  # noqa: E402
import ap_dung_thay_doi as adt  # noqa: E402
loi = qt.loi

ap = argparse.ArgumentParser()
ap.add_argument('lenh'); ap.add_argument('doi_tuong', nargs='?'); ap.add_argument('--ket-qua'); ap.add_argument('--nguoi', default=''); ap.add_argument('--ghi-chu', default='')
ap.add_argument('--ngay'); ap.add_argument('--van-ban', default=''); ap.add_argument('--xem-lai'); ap.add_argument('--kiem-tra', default='')
ap.add_argument('--bo-qua-kiem-tra', action='store_true'); ap.add_argument('--them-nguoi', action='append', default=[]); ap.add_argument('--phuong-an', default='hien_tai')
ap.add_argument('--ghi', action='store_true'); ap.add_argument('--so-phu-luc'); ap.add_argument('--ngay-phu-luc'); ap.add_argument('--gia', type=int)
ap.add_argument('--cut-over'); ap.add_argument('--dot-thanh-toan'); ap.add_argument('--gia-han-bao-dam')
a = ap.parse_args()
NGAY = a.ngay or loi.bay_gio()[:10]
for d_ in (a.ngay, a.xem_lai, a.ngay_phu_luc, a.cut_over):
    if d_:
        dt.date.fromisoformat(d_)
so = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})
NUT_SO_THAY_DOI = 'thay_doi'  # sổ thay đổi đổi theo chính vòng đời CR (thực hiện, đóng), không coi là đầu vào cũ khi đóng CR
NUT_NGUON = {'uoc_luong': 'dau_vao/uoc_luong.json', 'du_an': 'dau_vao/du_an.json', 'don_gia': 'dau_vao/don_gia.json', 'thanh_vien': 'dau_vao/thanh_vien.json',
             'chi_tieu': 'dau_vao/chi_tieu_ky_thuat.json'}
NGUON_NHAP = {'wbs': 'lam_viec/wbs/wbs_nhap.json', 'giao_viec': 'lam_viec/giao_viec/phan_cong_nhap.json', 'lich': 'lam_viec/lich/moc_nhap.json'}


def nap_quy_tac():
    pl, loi_ds, cb = qt.nap_phan_loai()
    for c in cb:
        print('CẢNH BÁO: ' + c)
    if loi_ds:
        loi.thoat_loi('\n- '.join([''] + loi_ds))
    return pl


def lich_su(cr, trang_thai, ghi_chu, nguoi=None):
    cr['lich_su'].append({'ngay': NGAY, 'ghi_luc': loi.bay_gio(), 'trang_thai': trang_thai, 'nguoi': a.nguoi if nguoi is None else nguoi, 'ghi_chu': ghi_chu})


# ---------------------------------------------------------------- đánh giá
def kiem_tra_phieu(cr, wbs, dg, tv):
    """Lỗi TD22 của phiếu: gói thay đổi, mục mới, gói mới (mã, mục cha, loại, phụ thuộc, người)."""
    by = {g['ma']: g for g in wbs['goi']}
    moi = {m['ma'] for m in cr.get('muc_moi', [])} | {g.get('ma') for g in cr.get('goi_moi', [])}
    loi_ds = []
    for x in cr.get('goi_thay_doi', []):
        if not by.get(x['ma'], {}).get('la'):
            loi_ds.append(f'Gói {x["ma"]} không phải gói lá của WBS')
        for p in x.get('them_phu_thuoc', []):
            if p not in by and p not in moi:
                loi_ds.append(f'Gói {x["ma"]}: phụ thuộc thêm {p} không có trong WBS hoặc gói mới')
    for m in cr.get('muc_moi', []) + cr.get('goi_moi', []):
        cha = m['ma'].rsplit('.', 1)[0] if '.' in str(m.get('ma', '')) else ''
        if not re.fullmatch(r'\d+(\.\d+)*', str(m.get('ma', ''))) or m['ma'] in by:
            loi_ds.append(f'Mã mới {m.get("ma")} sai dạng hoặc đã có trong WBS')
        elif cha and cha not in by and cha not in moi:
            loi_ds.append(f'Mục mới {m["ma"]} có mục cha {cha} không tồn tại')
    for x in cr.get('goi_moi', []):
        if x.get('loai') not in dg['loai_cong_viec']:
            loi_ds.append(f'Gói mới {x.get("ma")} thiếu loại công việc hợp lệ')
        if not x.get('ten') or not float(x.get('md') or 0) > 0:
            loi_ds.append(f'Gói mới {x.get("ma")} thiếu tên hoặc MD')
        for p in x.get('phu_thuoc', []):
            if p not in by and p not in moi:
                loi_ds.append(f'Gói mới {x["ma"]}: phụ thuộc {p} không có trong WBS hoặc gói mới')
        for p in [x.get('R')] + list(x.get('ho_tro', [])):
            if p and p not in tv:
                loi_ds.append(f'Gói mới {x["ma"]}: {p} không có trong thanh_vien.json (người mới khai báo bằng --them-nguoi)')
    if loi_ds:
        loi.thoat_loi('TD22 Phiếu yêu cầu thay đổi chưa hợp lệ:\n- ' + '\n- '.join(loi_ds))


def tinh_goi(cr, wbs, dg, he_so):
    """MD, chi phí nội bộ, giá đề nghị theo gói. Trả (tổng, chi tiết)."""
    by = {g['ma']: g for g in wbs['goi']}
    rate = lambda loai: dg['loai_cong_viec'][loai]['don_gia_tron_goi_thang'] / dg['md_moi_mm']  # noqa: E731
    tong, chi_tiet = {'md': 0.0, 'chi_phi': 0.0, 'gia': 0.0}, []
    for x in cr.get('goi_thay_doi', []):
        g, d = by[x['ma']], float(x['md_tang'])
        cp_ = d * rate(g['loai'])
        tong = {'md': tong['md'] + d, 'chi_phi': tong['chi_phi'] + cp_, 'gia': tong['gia'] + cp_ * he_so(x['ma'])}
        chi_tiet.append({'ma': x['ma'], 'ten': g['ten'], 'loai': g['loai'], 'md_tang': d, 'moi': False, 'them_phu_thuoc': x.get('them_phu_thuoc', [])})
    for x in cr.get('goi_moi', []):
        cp_ = float(x['md']) * rate(x['loai'])
        tong = {'md': tong['md'] + float(x['md']), 'chi_phi': tong['chi_phi'] + cp_, 'gia': tong['gia'] + cp_ * he_so(x.get('cha', ''))}
        chi_tiet.append({'ma': x['ma'], 'ten': x['ten'], 'loai': x['loai'], 'md_tang': float(x['md']), 'moi': True, 'them_phu_thuoc': []})
    return tong, chi_tiet


def dieu_kien_cr(cr, pl, cham_cut_over, moc):
    """Điều kiện áp dụng: khai báo của người đánh giá cộng điều kiện công cụ tính từ lịch."""
    dk = {d['ma']: d for d in pl['dieu_kien']}
    khai = list(cr.get('dieu_kien', []))
    sai = [x for x in khai if x not in dk or dk[x].get('tu_dong')]
    if sai:
        loi.thoat_loi(f'TD10 dieu_kien không hợp lệ: {", ".join(sai)}. Người đánh giá chỉ khai báo: '
                      + ', '.join(d['ma'] for d in pl['dieu_kien'] if not d.get('tu_dong')))
    tu_dong = [('cham_cut_over', cham_cut_over > 0 and pl.get('cut_over_co_dinh')), ('cham_moc_thanh_toan', any(m['vuot_han'] for m in moc)),
               ('doi_ngay_moc_thanh_toan', any(m['ngay_doi'] for m in moc) and not any(m['vuot_han'] for m in moc)),
               ('cam_ket_cdt', not cr.get('noi_bo'))]
    return list(dict.fromkeys(khai + [k for k, co in tu_dong if co]))


def nut_thay_doi(cr, tong, pa, them):
    """Nút sơ đồ phụ thuộc bị đổi: dữ liệu nguồn công cụ tự xác định cộng nut_thay_doi của phiếu."""
    nut = list(cr.get('nut_thay_doi') or [])
    if tong['md']:
        nut.append('uoc_luong')  # thêm MD thì căn cứ ước lượng đổi, kéo theo wbs và các bước sau
    if pa['ngay_lui_cut_over'] or cr.get('goi_moi'):
        nut.append('du_an')
    if pa['ngay_lui_cut_over'] and ((loi.doc_json('dau_vao/chi_tieu_ky_thuat.json', {}).get('bao_hanh') or {}).get('ho_tro_tang_cuong') or {}).get('tu'):
        nut.append('chi_tieu')  # khoảng hỗ trợ tăng cường sau cut over dời theo cut over mới
    if tong['gia'] and not cr.get('noi_bo'):
        nut.append('don_gia')
    if them:
        nut.append('thanh_vien')
    return list(dict.fromkeys(nut or ['wbs']))


def tai_lieu_anh_huong(nut):
    """Bước bị ảnh hưởng (bắc cầu) của các nút, sắp theo thứ tự trong sơ đồ phụ thuộc, kèm cờ khóa, ảnh chụp theo kỳ, đã tạo."""
    sd = loi.so_do(); thu_tu = {b['id']: i for i, b in enumerate(sd['buoc'])}; buoc = {b['id']: b for b in sd['buoc']}
    tl = {}
    for n in nut:
        r = subprocess.run([sys.executable, os.path.join(loi.THU_MUC_LOI, 'scripts', 'chay.py'), 'anh_huong', n, '--json'], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', cwd=loi.GOC)
        try:
            ds = json.loads(r.stdout)['anh_huong']
        except (ValueError, KeyError):
            loi.thoat_loi(f'Không xác định được tài liệu ảnh hưởng của nút {n}: {r.stdout.strip()[-300:]}')
        for b in ds:
            tl.setdefault(b['buoc'], dict(b, anh_chup=bool(buoc[b['buoc']].get('anh_chup'))))
    return sorted(tl.values(), key=lambda b: thu_tu.get(b['buoc'], 999))


def nguon_cap_nhat(cr, nut):
    """Dữ liệu nguồn phải sửa (tệp đầu vào trong sơ đồ và tệp nhập của bước), đặt đầu danh sách tài liệu phải cập nhật."""
    out = [f'{NUT_NGUON[n]} (dữ liệu nguồn' + (', khi chọn phương án thêm người)' if n == 'thanh_vien' and not cr.get('nut_thay_doi') else ')')
           for n in nut if n in NUT_NGUON]
    if cr.get('goi_moi') or cr.get('goi_thay_doi'):
        out.append(f'{NGUON_NHAP["wbs"]} (dữ liệu nguồn)')
    if cr.get('goi_moi'):
        out.append(f'{NGUON_NHAP["giao_viec"]} (dữ liệu nguồn)')
    if 'du_an' in nut:
        out.append(f'{NGUON_NHAP["lich"]} (dữ liệu nguồn)')
    return out


def nguoi_phe_duyet(muc, vai):
    ten = [vai[k]['ho_ten'] for k in muc['tham_quyen'] if k in vai]
    return muc['nguoi_phe_duyet'] + (f' ({", ".join(ten)})' if ten else '')


def kiem_tra_rui_ro(cr):
    rr = {r['ma'] for r in loi.doc_json('du_lieu/rui_ro.json', {'danh_sach': []})['danh_sach']}
    for m in cr.get('ma_rui_ro', []):
        if m not in rr:
            print(f'CẢNH BÁO: TD17 Mã rủi ro {m} không có trong sổ rủi ro')


def chon_ma(cr):
    ma = cr.get('ma') or cr.get('ma_cr') or f'CR{len(so["yeu_cau"]) + 1:02d}'
    if not re.fullmatch(r'CR\d{2,}', ma) or any(c['ma'] == ma for c in so['yeu_cau']):
        loi.thoat_loi(f'TD22 Mã yêu cầu thay đổi {ma} sai dạng CRnn hoặc đã có trong sổ')
    return ma


def ngay_bat_dau_mac_dinh(cr, pl, da, ngay_dx):
    """Phần thay đổi có gói mới chỉ làm sau quyết định: mặc định hạn quyết định của mức lớn tính từ ngày CR."""
    if cr.get('ngay_bat_dau'):
        return cr['ngay_bat_dau']
    if not cr.get('goi_moi'):
        return ngay_dx
    lon = pl['muc'][-1]
    return qt.cong_ngay_lam_viec(qt.cong_ngay_lam_viec(ngay_dx, lon['thoi_han_danh_gia_ngay'], da), lon['thoi_han_quyet_dinh_ngay'], da)


def danh_gia():
    pl = nap_quy_tac()
    cr = json.load(open(a.doi_tuong, encoding='utf-8'))
    wbs = loi.doc_json('du_lieu/wbs.json'); dg = loi.doc_json('dau_vao/don_gia.json')
    pc = loi.doc_json('du_lieu/phan_cong.json'); tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']
    cp = loi.doc_json('du_lieu/chi_phi.json'); da = loi.du_an()
    them_ds = [ltd.doc_them_nguoi(p, tvs, dg) for p in a.them_nguoi]
    them = {'thanh_vien': [t for x in them_ds for t in x['thanh_vien']]} if them_ds else None
    kiem_tra_phieu(cr, wbs, dg, {t['id'] for t in tvs + (them or {}).get('thanh_vien', [])})
    ma = chon_ma(cr)
    he_so, can_cu_gia = qt.he_so_gia(pl, cp, wbs)
    tong, chi_tiet = tinh_goi(cr, wbs, dg, he_so)
    kiem_tra_rui_ro(cr)
    ngay_dx = cr.get('ngay', loi.bay_gio()[:10])
    lt = ltd.danh_gia_lich(dict(cr, ma=ma), ma, ngay_dx, ngay_bat_dau_mac_dinh(cr, pl, da, ngay_dx), them_ds)
    pa = lt['hien_tai']
    # kiểm tra ngày cut over trên đúng dữ liệu đề xuất của bước áp dụng, để số ngày lùi của đánh giá và áp dụng khớp nhau (từ 1.4.6)
    if pa['ngay_lui_cut_over'] or cr.get('goi_moi'):
        kt = adt.kiem_tra_cut_over(dict(cr, ma=ma, ngay_de_xuat=ngay_dx, lich_thay_doi=lt_luu(lt), phu_luc_hop_dong=True, gia_de_nghi=round(tong['gia'])),
                                   pa, lt['ngay_bat_dau_thay_doi'],
                                   qt.vai_ban(pc, {t['id']: t for t in tvs}, loi.doc_json('dau_vao/nha_thau.json'), loi.doc_json('du_lieu/hsmt.json'))[0])
        pa.update(cut_over_kiem_tra=kt['cut_over'], ngay_lui_cut_over_kiem_tra=kt['ngay_lui'], lui_them_kiem_tra=kt['them'],
                  loi_kiem_tra_ap_dung=kt['loi_con_lai'])
        for m in pa['moc']:  # mốc giữa kỳ vượt hạn: ngày dự kiến và hạn đề xuất theo lịch kiểm tra (mốc gắn cut over dời theo phần chênh khi áp dụng)
            d = kt['moc'].get(m['ma'])
            if d and m['vuot_han'] and not m['gan_cut_over'] and d > m['han_de_xuat']:
                m.update(ngay_moi=d, han_de_xuat=d, vuot_han=max(m['vuot_han'], ltd.so_ngay_giua(ltd.ngay_mo_rong(da)[1], m['han'], d)))
    lui = pa.get('ngay_lui_cut_over_kiem_tra', pa['ngay_lui_cut_over'])
    moc = [m for m in pa['moc'] if m['dot']]
    dk = dieu_kien_cr(cr, pl, lui, moc)
    diem, muc, ly_do = qt.cham_diem({'md': tong['md'], 'chi_phi': tong['chi_phi'], 'tieu_hao_du_tru': lt['tieu_hao_du_tru'],
                                     'cham_cut_over': lui}, dk, pl)
    vai, _, _ = qt.vai_ban(pc, {t['id']: t for t in tvs}, loi.doc_json('dau_vao/nha_thau.json'), loi.doc_json('du_lieu/hsmt.json'))
    phu_luc = muc.get('phu_luc_hop_dong', False) and any(d.get('phu_luc') for d in pl['dieu_kien'] if d['ma'] in dk)
    KY_HD = loi.da_ky_hop_dong()  # trước khi ký hợp đồng, HSMT và HSDT chưa khóa
    nut = nut_thay_doi(cr, tong, pa, them)
    tl = tai_lieu_anh_huong(nut)
    han_dg = qt.cong_ngay_lam_viec(ngay_dx, muc['thoi_han_danh_gia_ngay'], da)
    lg = {g['ma']: g for g in pa['goi']}
    chi_tiet = [dict(x, bat_dau=lg.get(x['ma'], {}).get('bat_dau', ''), ket_thuc=lg.get(x['ma'], {}).get('ket_thuc', ''),
                     nguoi=lg.get(x['ma'], {}).get('nguoi', [])) for x in chi_tiet]
    rec = {'ma': ma, 'tieu_de': cr['tieu_de'], 'mo_ta': cr.get('mo_ta', ''), 'ly_do': cr.get('ly_do', ''), 'nguon': cr.get('nguon', ''),
           'nguoi_de_xuat': cr.get('nguoi_de_xuat', ''), 'ngay_de_xuat': ngay_dx, 'noi_bo': bool(cr.get('noi_bo')), 'dieu_kien': dk,
           'ma_rui_ro': cr.get('ma_rui_ro', []), 'can_cu_hsmt': cr.get('can_cu_hsmt', ''), 'nhan_dinh_ban_dau': cr.get('nhan_dinh_ban_dau', ''),
           'rui_ro_moi': cr.get('rui_ro_moi', ''), 'md_tang': round(tong['md'], 2), 'chi_phi_tang': round(tong['chi_phi']), 'chi_phi_noi_bo': round(tong['chi_phi']),
           'gia_de_nghi': round(tong['gia']), 'can_cu_gia_de_nghi': can_cu_gia, 'ngay_cham': lt['ngay_cham'], 'tieu_hao_du_tru': lt['tieu_hao_du_tru'],
           'ngay_cham_cut_over': lui, 'cut_over_moi': pa.get('cut_over_kiem_tra') or pa['cut_over_moi'], 'ket_thuc_moi': pa['ket_thuc_moi'],
           'can_them_nguoi': pa['can_them_nguoi'], 'ket_luan_nhan_su': pa['ket_luan_nhan_su'],
           'moc_anh_huong': [m for m in pa['moc'] if m['ngay_doi'] or m['vuot_han']], 'chi_tiet_goi': chi_tiet,
           'muc_moi': cr.get('muc_moi', []), 'goi_moi': cr.get('goi_moi', []), 'goi_thay_doi': cr.get('goi_thay_doi', []), 'lich_thay_doi': lt_luu(lt),
           'diem_tac_dong': diem, 'ly_do_muc': ly_do, 'muc': muc['ma'], 'muc_ten': muc['ten'],
           'nguoi_phe_duyet_theo_quy_dinh': nguoi_phe_duyet(muc, vai), 'han_danh_gia_ngay': muc['thoi_han_danh_gia_ngay'], 'han_danh_gia': han_dg,
           'han_quyet_dinh': qt.cong_ngay_lam_viec(han_dg, muc['thoi_han_quyet_dinh_ngay'], da),
           'han_hop_ban': qt.cong_ngay_lam_viec(ngay_dx, muc['hop_ban_trong_ngay'], da) if muc.get('hop_ban_trong_ngay') else '',
           'nut_thay_doi': nut,
           'tai_lieu_cap_nhat': nguon_cap_nhat(cr, nut) + [f'{b["buoc"]} ({b["ten"]})' for b in tl if b['da_tao'] and not b['anh_chup'] and not (b['khoa'] and KY_HD)],
           'tai_lieu_theo_ky': [f'{b["buoc"]} ({b["ten"]})' for b in tl if b['da_tao'] and b['anh_chup']],
           'tai_lieu_khoa': [f'{b["buoc"]} ({b["ten"]})' for b in tl if b['khoa'] and KY_HD],
           'phu_luc_hop_dong': phu_luc, 'van_ban_yeu_cau': 'Phụ lục hợp đồng' if phu_luc else muc['van_ban'],
           'trang_thai': 'Chờ phê duyệt', 'lich_su': [  # từ 1.4.7: tiếp nhận, phân loại sơ bộ, đánh giá do quản trị dự án của nhà thầu
               {'ngay': ngay_dx, 'ghi_luc': loi.bay_gio(), 'trang_thai': tt_, 'nguoi': (vai.get('qtda') or {}).get('ho_ten', ''), 'ghi_chu': gc_}
               for tt_, gc_ in (('Mới', f'Tiếp nhận đề nghị của {cr.get("nguoi_de_xuat", "")}, cấp mã và lập phiếu'),
                                ('Đang đánh giá', f'Phân loại sơ bộ mức {muc["ten"].lower()}, đánh giá tác động'),
                                ('Chờ phê duyệt', 'Hoàn thành đánh giá tác động bằng công cụ của nhóm, trình người có thẩm quyền'))]}
    so['yeu_cau'].append(rec)
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{ma}.danh_gia', 'script', f'Đánh giá {ma}: {rec["tieu_de"]}', vao=[a.doi_tuong], ra=['du_lieu/thay_doi.json'],
                    ket_qua=rec['muc_ten'], chi_tiet={k: rec[k] for k in ('md_tang', 'chi_phi_noi_bo', 'gia_de_nghi', 'tieu_hao_du_tru', 'ngay_cham_cut_over',
                                                                          'cut_over_moi', 'can_them_nguoi', 'diem_tac_dong')})
    in_ket_qua(rec)


def lt_luu(lt):
    """Kết quả đưa vào lịch lưu trong sổ: bỏ tải từng người dài, giữ người tải cao nhất."""
    out = dict(lt)
    for k in lt['phuong_an']:
        out[k] = dict(out[k], tai_nguoi=out[k]['tai_nguoi'][:6])
    return out


def in_phuong_an(pa):
    print(f'  Phương án {pa["phuong_an"]}: kết thúc dự kiến {loi.ngay(pa["ket_thuc_moi"])}, cut over {loi.ngay(pa["cut_over_goc"])} lùi '
          f'{pa["ngay_lui_cut_over"]} ngày làm việc thành {loi.ngay(pa["cut_over_moi"])} (theo phụ thuộc {pa["ngay_lui_theo_phu_thuoc"]} ngày, '
          f'do nguồn lực {pa["ngay_do_nguon_luc"]} ngày' + (f', khoảng UAT kéo dài {pa["uat_keo_dai"]} ngày' if pa['uat_keo_dai'] else '')
          + f'). {pa["ket_luan_nhan_su"]}.')
    if pa.get('cut_over_kiem_tra'):
        print(f'    Kiểm tra trên dữ liệu đề xuất của bước áp dụng: cut over {loi.ngay(pa["cut_over_kiem_tra"])}, lùi {pa["ngay_lui_cut_over_kiem_tra"]} ngày làm việc'
              + (f' (thêm {pa["lui_them_kiem_tra"]} ngày so với mô phỏng)' if pa.get('lui_them_kiem_tra') else ', khớp mô phỏng')
              + ('. Lịch còn lỗi: ' + '; '.join(pa['loi_kiem_tra_ap_dung']) if pa.get('loi_kiem_tra_ap_dung') else '') + '.')
    kn = pa['kha_nang']
    print(f'    Khả năng theo quỹ: {loi.so(kn["md_con_lai"], 2)} MD còn lại (gồm CR) chia {loi.so(kn["md_moi_ngay"], 2)} MD mỗi ngày của nhóm là '
          f'{kn["so_ngay_theo_quy"]} ngày làm việc, so với {kn["so_ngay_den_cut_over_goc"]} ngày từ ngày CR đến cut over gốc.')
    print('    Chuỗi dài nhất: ' + ' -> '.join(f'{g["ma"]} ({", ".join(g["nguoi"])}, {loi.ngay(g["bat_dau"])}-{loi.ngay(g["ket_thuc"])})'
                                           for g in pa['chuoi_dai_nhat']))
    for g in pa['goi']:
        print(f'    {g["ma"]} {g["ten"]}: {loi.ngay(g["bat_dau"])} đến {loi.ngay(g["ket_thuc"])} ({", ".join(g["nguoi"])})')


def in_ket_qua(rec):
    lt = rec['lich_thay_doi']
    print(f'{rec["ma"]}: tăng {rec["md_tang"]:g} MD, chi phí nội bộ {loi.tien(rec["chi_phi_noi_bo"])} đồng, giá đề nghị Chủ đầu tư {loi.tien(rec["gia_de_nghi"])} đồng '
          f'({rec["can_cu_gia_de_nghi"]}).')
    print(f'Lịch tính từ ngày {loi.ngay(lt.get("ngay_lap_lai") or lt["ngay_cr"])} ({lt["so_goi_da_xong"]} gói đã xong, {lt["so_goi_dang_lam"]} gói đang làm, {lt["phan_da_lam"]}), '
          f'phần thay đổi bắt đầu từ {loi.ngay(lt["ngay_bat_dau_thay_doi"])}. Chậm {rec["ngay_cham"]} ngày, tiêu hao dự trữ {rec["tieu_hao_du_tru"]} ngày '
          f'(dự trữ đến cut over không có CR {lt["du_tru_tham_chieu"]} ngày).')
    if lt['cut_over_lui_khong_co_cr']:
        print(f'CẢNH BÁO: Không có CR lịch đã cần lùi cut over {lt["cut_over_lui_khong_co_cr"]} ngày (tiến độ thực tế), số ngày lùi gồm cả phần này')
    for k in lt['phuong_an']:
        if lt.get(k):
            in_phuong_an(lt[k])
    if len(lt['phuong_an']) > 1:
        ds = [(k, lt[k]['ngay_lui_cut_over']) for k in lt['phuong_an']]
        print('  So sánh phương án (số ngày cut over lùi): ' + ', '.join(f'{k} {v}' for k, v in ds)
              + ('. Thêm người theo các phương án không rút ngắn cut over: chuỗi dài nhất bị giới hạn bởi phụ thuộc, thời gian Chủ đầu tư xác nhận '
                 'và khoảng kiểm thử chấp nhận, không bởi số người' if all(v >= ds[0][1] for _, v in ds[1:]) else ''))
    for m in rec['moc_anh_huong']:
        print(f'  Mốc {m["ma"]}' + (f' (Đợt {m["dot"]})' if m['dot'] else '') + f': {loi.ngay(m["ngay_cu"])} thành {loi.ngay(m["ngay_moi"])}, dời {m["ngay_doi"]} ngày, '
              f'vượt hạn {m["vuot_han"]} ngày' + (f', hạn đề xuất {loi.ngay(m["han_de_xuat"])}' if m['han_de_xuat'] != m['han'] else ''))
    print(f'Điểm tác động {rec["diem_tac_dong"]}, mức {rec["muc_ten"]}' + (f' do: {"; ".join(rec["ly_do_muc"])}' if rec['ly_do_muc'] else '') + '.')
    print(f'Phê duyệt: {rec["nguoi_phe_duyet_theo_quy_dinh"]}. Hạn đánh giá {loi.ngay(rec["han_danh_gia"])}, hạn quyết định {loi.ngay(rec["han_quyet_dinh"])}'
          + (f', họp ban trước {loi.ngay(rec["han_hop_ban"])}' if rec['han_hop_ban'] else '') + f'. Văn bản: {rec["van_ban_yeu_cau"]}.')
    print('Tài liệu phải cập nhật nếu phê duyệt: ' + '; '.join(rec['tai_lieu_cap_nhat']))
    if rec['tai_lieu_theo_ky']:
        print('Báo cáo theo kỳ ghi nhận ở kỳ tiếp theo, không tạo lại: ' + '; '.join(rec['tai_lieu_theo_ky']))
    if rec['tai_lieu_khoa']:
        print('Không sửa (đường cơ sở đấu thầu): ' + '; '.join(rec['tai_lieu_khoa']) + ('. Cần phụ lục hợp đồng.' if rec['phu_luc_hop_dong'] else '. Ghi nhận trong biên bản thỏa thuận.'))


# ---------------------------------------------------------------- quyết định, áp dụng, thực hiện, đóng
def quyet_dinh(cr):
    if a.ket_qua not in ('Đã phê duyệt', 'Từ chối', 'Hoãn'):
        loi.thoat_loi('--ket-qua phải là Đã phê duyệt, Từ chối hoặc Hoãn')
    if cr['trang_thai'] not in ('Chờ phê duyệt', 'Hoãn'):
        loi.thoat_loi(f'TD12 {cr["ma"]} đang ở trạng thái {cr["trang_thai"]}, chỉ quyết định yêu cầu chờ phê duyệt hoặc đã hoãn')
    if NGAY < cr['ngay_de_xuat']:
        loi.thoat_loi(f'Ngày quyết định {NGAY} trước ngày đề xuất {cr["ngay_de_xuat"]}, dùng --ngay theo lịch dự án')
    if a.ket_qua == 'Đã phê duyệt' and (cr.get('phu_luc_hop_dong') or cr['muc'] == 'lon') and not a.van_ban.strip():
        loi.thoat_loi(f'TD13 {cr["ma"]} mức {cr["muc_ten"]} cần --van-ban: số, ngày của văn bản đã ký ({cr.get("van_ban_yeu_cau", "văn bản thống nhất hoặc phụ lục hợp đồng").lower()})')
    if a.ket_qua == 'Hoãn' and (not a.xem_lai or a.xem_lai < NGAY):
        loi.thoat_loi('TD14 Hoãn cần --xem-lai yyyy-mm-dd (ngày xem xét lại, không trước ngày quyết định)')
    if a.ket_qua == 'Đã phê duyệt' and not (cr.get('lich_thay_doi') or {}).get(a.phuong_an) and cr.get('lich_thay_doi'):
        loi.thoat_loi(f'TD19 {cr["ma"]} không có phương án {a.phuong_an}. Phương án thêm nhân sự cần đánh giá với --them-nguoi')
    cr.update({'trang_thai': a.ket_qua, 'nguoi_quyet_dinh': a.nguoi, 'ngay_quyet_dinh': NGAY, 'van_ban': a.van_ban.strip() or cr.get('van_ban', ''),
               'ngay_xem_lai': a.xem_lai or '', 'dem_phien_ban_khi_quyet_dinh': loi.doc_json('du_lieu/phien_ban.json', {}).get('dem', 0)})
    if a.ket_qua == 'Đã phê duyệt' and cr.get('lich_thay_doi'):
        cr['phuong_an_chon'] = a.phuong_an
    if cr.get('han_quyet_dinh'):
        cr['quyet_dinh_dung_han'] = NGAY <= cr['han_quyet_dinh']
        if not cr['quyet_dinh_dung_han']:
            print(f'CẢNH BÁO: TD16 {cr["ma"]} quyết định ngày {loi.ngay(NGAY)}, quá hạn {loi.ngay(cr["han_quyet_dinh"])}')
    lich_su(cr, a.ket_qua, a.ghi_chu)
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{cr["ma"]}.quyet_dinh', 'nguoi_dung', f'{a.ket_qua} {cr["ma"]}: {a.ghi_chu}', ra=['du_lieu/thay_doi.json'], ket_qua=a.ket_qua)
    print(f'{cr["ma"]}: {a.ket_qua}.')
    if a.ket_qua == 'Đã phê duyệt':
        print(f'Tiếp theo: yeu_cau_thay_doi.py ap_dung {cr["ma"]} (xem đề xuất), rồi ap_dung {cr["ma"]} --ghi, chạy lại theo thứ tự in ra. '
              'Sau khi kiểm tra đạt, chạy thuc_hien rồi dong.')
    elif a.ket_qua == 'Hoãn':
        print(f'Xem xét lại ngày {loi.ngay(a.xem_lai)}: quyết định lại bằng quyet_dinh, hoặc dong khi hai bên thống nhất không thực hiện.')
    else:
        print('Thông báo lý do từ chối cho người đề xuất, sau đó dong kèm --ghi-chu.')


def ap_dung(cr):
    vai, _, _ = qt.vai_ban(loi.doc_json('du_lieu/phan_cong.json'), {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']},
                           loi.doc_json('dau_vao/nha_thau.json'), loi.doc_json('du_lieu/hsmt.json'))
    pl, rec = adt.ap_dung(cr, a, NGAY, vai)
    cr['phu_luc'] = pl
    cr['ap_dung'] = rec
    loi.ghi_json('du_lieu/thay_doi.json', so)
    ra = [x['tep'] for x in rec['tep']] if a.ghi else [x['de_xuat'] for x in rec['tep']]
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{cr["ma"]}.ap_dung', 'script', f'Áp dụng {cr["ma"]} vào dữ liệu nguồn' + (' (ghi thẳng)' if a.ghi else ' (đề xuất)'),
                    ra=['du_lieu/thay_doi.json'] + ra, chi_tiet={'phu_luc': pl, 'tep': [x['tep'] for x in rec['tep']]})
    print(f'{cr["ma"]}: {pl["so"]} (ngày hiệu lực {loi.ngay(pl["ngay"])}), giá điều chỉnh {loi.tien(pl["gia_dieu_chinh"])} đồng '
          f'({loi.tien(pl["gia_hop_dong_truoc"])} thành {loi.tien(pl["gia_hop_dong_sau"])} đồng), cut over {loi.ngay(pl["cut_over_truoc"])} thành {loi.ngay(pl["cut_over_moi"])}.')
    for m in pl['moc_thanh_toan']:
        print(f'  Mốc {m["ma"]} (Đợt {m["dot"]}): hạn {loi.ngay(m["han_truoc"])} thành {loi.ngay(m["han_moi"])}')
    if (pl.get('uat') or {}).get('moi') and pl['uat']['moi'] != pl['uat']['truoc']:
        print(f'  Kiểm thử chấp nhận: {loi.ngay(pl["uat"]["truoc"].get("tu"))} - {loi.ngay(pl["uat"]["truoc"].get("den"))} thành '
              f'{loi.ngay(pl["uat"]["moi"]["tu"])} - {loi.ngay(pl["uat"]["moi"]["den"])}')
    for c in pl.get('cam_ket_chu_dau_tu', []):
        print(f'  Cam kết {c["ma"]} ({c["noi_dung"]}): hạn {loi.ngay(c["han_truoc"])} thành {loi.ngay(c["han_moi"])}')
    for d in pl.get('dot_thanh_toan', []):
        print(f'  Đợt {d["dot"]}: {loi.so(d["phan_tram_gia_dieu_chinh"], 0)}% giá điều chỉnh khi {d["su_kien"]} (mốc {d["moc"]})')
    for c in rec['canh_bao']:
        print('CẢNH BÁO: ' + c)
    print(('Đã ghi' if a.ghi else 'Đề xuất (chưa ghi, thêm --ghi để áp dụng)') + ':')
    for x in rec['tep']:
        print(f'  {x["tep"]}: {x["thay_doi"]}' + ('' if a.ghi else f' [{x["de_xuat"]}]'))
    print('Thứ tự chạy lại:')
    for i, l_ in enumerate(rec['thu_tu_chay_lai'], 1):
        print(f'  {i}. {l_}')


def phu_luc(cr):
    pl = adt.ghi_dot_thanh_toan(cr, a, NGAY)
    lich_su(cr, cr['trang_thai'], a.ghi_chu or f'Ghi đợt thanh toán riêng của phần giá điều chỉnh theo {pl.get("so", "")}')
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{cr["ma"]}.phu_luc', 'nguoi_dung', f'Ghi đợt thanh toán của phụ lục {pl.get("so", "")} ({cr["ma"]})',
                    vao=[a.dot_thanh_toan], ra=['du_lieu/thay_doi.json'], chi_tiet={'dot_thanh_toan': pl['dot_thanh_toan']})
    for d in pl['dot_thanh_toan']:
        print(f'{cr["ma"]}: Đợt {d["dot"]} {loi.so(d["phan_tram_gia_dieu_chinh"], 0)}% giá điều chỉnh ({loi.tien(pl["gia_dieu_chinh"])} đồng) khi {d["su_kien"]}, mốc {d["moc"]}')
    print('Tiếp theo: tinh_chi_phi.py (dòng tiền), rồi các tài liệu dùng chi_phi (chay.py trang_thai).')


def thuc_hien(cr):
    if cr['trang_thai'] != 'Đã phê duyệt':
        loi.thoat_loi(f'TD12 {cr["ma"]} đang ở trạng thái {cr["trang_thai"]}, chỉ ghi nhận thực hiện cho yêu cầu đã phê duyệt')
    if not a.kiem_tra.strip():
        loi.thoat_loi('TD15 Cần --kiem-tra: kết quả kiểm tra đạt phần thay đổi (Chủ đầu tư theo Mục 20.1 E-ĐKCT, thay đổi nội bộ do quản trị dự án) và biên bản')
    if NGAY < cr.get('ngay_quyet_dinh', cr['ngay_de_xuat']):
        loi.thoat_loi(f'Ngày kiểm tra {NGAY} trước ngày quyết định, dùng --ngay theo lịch dự án')
    cr.update({'trang_thai': 'Đã thực hiện', 'kiem_tra_dat': a.kiem_tra.strip(), 'nguoi_kiem_tra': a.nguoi, 'ngay_thuc_hien': NGAY})
    lich_su(cr, 'Đã thực hiện', a.kiem_tra.strip())
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{cr["ma"]}.thuc_hien', 'nguoi_dung', f'Kiểm tra đạt {cr["ma"]}: {a.kiem_tra}', ra=['du_lieu/thay_doi.json'])
    print(f'{cr["ma"]}: Đã thực hiện, kiểm tra đạt. Đóng bằng lệnh dong sau khi mọi tài liệu đã cập nhật.')


def tai_lieu_chua_cap_nhat(cr):
    """Tài liệu còn dùng đầu vào cũ hoặc chưa có phiên bản sau quyết định phê duyệt, và phiên bản sau thay đổi.
    Bỏ qua dữ liệu nguồn (kiểm tra bằng vết áp dụng) và báo cáo theo kỳ (anh_chup, giữ số liệu tại thời điểm lập)."""
    t_qd = next((x.get('ghi_luc', x['ngay']) for x in reversed(cr['lich_su']) if x['trang_thai'] == 'Đã phê duyệt'), '')
    sd = loi.so_do(); reg = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})['tai_lieu']
    bd = loi.nut_bien_dong(sd); cu, chua, pb_sau = [], [], {}
    dem_qd = cr.get('dem_phien_ban_khi_quyet_dinh')
    for s_ in cr.get('tai_lieu_cap_nhat', []):
        b = next((x for x in sd['buoc'] if x['id'] == s_.split(' ')[0]), None)
        if not b or b.get('anh_chup'):
            continue
        ds_tep = []
        for q in b['ra'].values():
            ds_tep += [k for k in reg if k.startswith(q.rstrip('/') + '/')] if os.path.isdir(loi.duong_dan(q)) else [q]
        for p in [p for p in ds_tep if os.path.exists(loi.duong_dan(p))]:
            lst = reg.get(p, [])
            if not lst:
                continue
            pb_sau[p] = lst[-1]['phien_ban']
            if (max(lst[-1].get('thu_tu', 0), lst[-1].get('thu_tu_kiem_tra', 0)) <= dem_qd) if dem_qd is not None else \
                    (max(lst[-1]['ngay'], lst[-1].get('ngay_kiem_tra', '')) <= t_qd):
                chua.append(f'{b["id"]} ({p})')
            if any(loi.bam_nut(sd, n) != h for n, h in lst[-1].get('vao', {}).items()
                   if n in b['vao'] and n not in bd and n != NUT_SO_THAY_DOI and loi.duong_dan_nut(sd, n)):
                cu.append(f'{b["id"]} ({p})')
    return cu, chua, pb_sau


def dong(cr):
    if cr['trang_thai'] in ('Từ chối', 'Hoãn'):
        if not a.ghi_chu.strip():
            loi.thoat_loi(f'TD12 Đóng yêu cầu {cr["trang_thai"].lower()} cần --ghi-chu: lý do và việc đã thông báo người đề xuất')
        ket_qua = cr['trang_thai']
    elif cr['trang_thai'] == 'Đã thực hiện':
        cu, chua, pb_sau = tai_lieu_chua_cap_nhat(cr)
        nguon = adt.nguon_chua_ap_dung(cr) if cr.get('ap_dung') else (['chưa chạy ap_dung'] if cr.get('lich_thay_doi') else [])
        bl = cr.get('lich_thay_doi') and adt.can_duong_co_so(cr) and not adt.co_duong_co_so(cr)
        if (cu or chua or nguon or bl) and not a.bo_qua_kiem_tra:
            loi.thoat_loi('Chưa đóng được CR. ' + (f'TD20 Dữ liệu nguồn chưa áp dụng: {", ".join(nguon)}. ' if nguon else '') +
                          (f'TD23 Chưa có đường cơ sở sau thay đổi: so_phien_ban.py duong_co_so {adt.ma_duong_co_so_moi()} --cr {cr["ma"]}. ' if bl else '') +
                          ('Tài liệu còn dùng đầu vào cũ: ' + ', '.join(sorted(set(cu))) + '. ' if cu else '') +
                          ('Tài liệu chưa có phiên bản sau quyết định phê duyệt: ' + ', '.join(sorted(set(chua))) + '. ' if chua else '') +
                          'Chạy ap_dung --ghi và các bước còn lại (chay.py trang_thai) hoặc dùng --bo-qua-kiem-tra kèm lý do trong --ghi-chu.')
        cr['phien_ban_sau'] = pb_sau
        ket_qua = 'Đã phê duyệt'
    elif cr['trang_thai'] == 'Đã phê duyệt':
        loi.thoat_loi(f'TD15 {cr["ma"]} chưa có kết quả kiểm tra đạt phần thay đổi. Chạy thuc_hien {cr["ma"]} --kiem-tra "..." trước khi đóng')
    else:
        loi.thoat_loi(f'TD12 {cr["ma"]} đang ở trạng thái {cr["trang_thai"]}, chưa đóng được')
    cr.update({'trang_thai': 'Đã đóng', 'ket_qua_dong': ket_qua, 'ngay_dong': NGAY, 'nguoi_dong': a.nguoi})
    lich_su(cr, 'Đã đóng', a.ghi_chu)
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{cr["ma"]}.dong', 'script', f'Đóng {cr["ma"]} ({ket_qua}): {a.ghi_chu}', ra=['du_lieu/thay_doi.json'])
    print(f'{cr["ma"]}: Đã đóng ({ket_qua}).')


if a.lenh == 'danh_sach':
    for c in so['yeu_cau']:
        print(f'{c["ma"]} [{c["trang_thai"]}] {c["tieu_de"]} | {c["md_tang"]:g} MD, nội bộ {loi.tien(c["chi_phi_tang"])} đồng, '
              f'đề nghị {loi.tien(c.get("gia_de_nghi") or 0)} đồng, cut over lùi {c.get("ngay_cham_cut_over", 0)} ngày, điểm {c.get("diem_tac_dong", "")}, mức {c["muc_ten"]}')
    sys.exit(0)
if a.lenh == 'danh_gia':
    danh_gia(); sys.exit(0)
CR = next((c for c in so['yeu_cau'] if c['ma'] == a.doi_tuong), None)
if not CR:
    loi.thoat_loi('Không có yêu cầu thay đổi ' + str(a.doi_tuong))
LENH = {'quyet_dinh': quyet_dinh, 'ap_dung': ap_dung, 'phu_luc': phu_luc, 'thuc_hien': thuc_hien, 'dong': dong}
if a.lenh not in LENH:
    loi.thoat_loi('Lệnh không hợp lệ')
LENH[a.lenh](CR)
