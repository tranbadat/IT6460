"""Ghi, đánh giá tác động, ra quyết định, ghi nhận kết quả kiểm tra và đóng yêu cầu thay đổi (CR). Sổ thay đổi: du_lieu/thay_doi.json.

Dùng:
  python yeu_cau_thay_doi.py danh_gia <cr_nhap.json>
      Đánh giá CR do agent hoặc người dùng lập:
      {"tieu_de", "mo_ta", "ly_do", "nguoi_de_xuat", "ngay": "yyyy-mm-dd", "nguon": "chủ đầu tư | nhà thầu | rủi ro RRxx",
       "noi_bo": false, "dieu_kien": ["cham_dac_ta"], "ma_rui_ro": ["RR01"], "can_cu_hsmt": "Mục 17.1(c) E-ĐKCT",
       "nhan_dinh_ban_dau": "...", "rui_ro_moi": "...",
       "goi_thay_doi": [{"ma": "5.3.2", "md_tang": 3}], "goi_moi": [{"ma": "5.3.9", "ten": "...", "md": 4, "loai": "DEV", "cha": "5.3"}],
       "nut_thay_doi": ["wbs"]}
      noi_bo: true chỉ khi là thay đổi nội bộ của nhà thầu, không đổi cam kết với Chủ đầu tư (mới được xếp mức nhỏ).
      dieu_kien: điều kiện người đánh giá khai báo trong references/phan_loai.json (cham_dac_ta, doi_pham_vi, doi_gia, cam_ket_cdt).
      Tính: MD tăng, chi phí nội bộ (MD x đơn giá loại công việc), giá đề nghị Chủ đầu tư, số ngày chậm (gói găng hoặc vượt dự trữ),
      chậm cut over, mốc gắn đợt thanh toán bị dời, điểm tác động 1-10, mức, người phê duyệt, hạn đánh giá và quyết định,
      tài liệu phải cập nhật, tài liệu khóa, cần phụ lục hợp đồng. Ghi CR trạng thái Chờ phê duyệt.
  python yeu_cau_thay_doi.py quyet_dinh <ma_cr> --ket-qua "Đã phê duyệt|Từ chối|Hoãn" --nguoi "<người quyết định>" [--ngay yyyy-mm-dd]
      [--van-ban "<số, ngày văn bản thống nhất hoặc phụ lục>"] (bắt buộc khi phê duyệt mức lớn) [--xem-lai yyyy-mm-dd] (bắt buộc khi hoãn) [--ghi-chu ...]
  python yeu_cau_thay_doi.py thuc_hien <ma_cr> --kiem-tra "<kết quả kiểm tra đạt, biên bản>" --nguoi "<người kiểm tra>" [--ngay yyyy-mm-dd]
      Ghi nhận phần thay đổi đã thực hiện và được kiểm tra đạt (Chủ đầu tư kiểm tra theo Mục 20.1 E-ĐKCT, thay đổi nội bộ do quản trị dự án).
  python yeu_cau_thay_doi.py dong <ma_cr> --ghi-chu "<đã cập nhật tài liệu nào | lý do đã thông báo>" [--ngay yyyy-mm-dd] [--nguoi ...] [--bo-qua-kiem-tra]
      CR đã thực hiện: chỉ đóng khi mọi tài liệu trong tai_lieu_cap_nhat đã tạo lại với đầu vào mới, ghi phiên bản sau thay đổi.
      CR từ chối hoặc hoãn: đóng với ghi chú lý do đã thông báo người đề xuất, không kiểm tra tài liệu.
  --ngay là ngày theo lịch dự án (biên bản họp, email phê duyệt), mặc định là ngày chạy lệnh. Thời gian xử lý CR tính từ ngày đề xuất đến ngày này.
  python yeu_cau_thay_doi.py danh_sach
Kiểm tra: TD10 đến TD17 (lỗi dừng, cảnh báo in).
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse, datetime as dt, json, math, os, subprocess, sys  # noqa: E401
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import quy_tac_thay_doi as qt  # noqa: E402
loi = qt.loi

ap = argparse.ArgumentParser()
ap.add_argument('lenh'); ap.add_argument('doi_tuong', nargs='?'); ap.add_argument('--ket-qua'); ap.add_argument('--nguoi', default=''); ap.add_argument('--ghi-chu', default='')
ap.add_argument('--ngay'); ap.add_argument('--van-ban', default=''); ap.add_argument('--xem-lai'); ap.add_argument('--kiem-tra', default='')
ap.add_argument('--bo-qua-kiem-tra', action='store_true')
a = ap.parse_args()
NGAY = a.ngay or loi.bay_gio()[:10]
for d_ in (a.ngay, a.xem_lai):
    if d_:
        dt.date.fromisoformat(d_)
so = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})


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
def tinh_goi(cr, wbs, lich, dg, pc, tv, he_so):
    """MD, chi phí nội bộ, giá đề nghị, số ngày tăng theo gói. Trả (tổng, chi tiết, số ngày tăng theo gói lá, lỗi)."""
    by = {g['ma']: g for g in wbs['goi']}; lg = {x['ma']: x for x in lich['goi']}; gv = {x['ma']: x for x in pc['giao_viec']}
    rate = lambda loai: dg['loai_cong_viec'][loai]['don_gia_tron_goi_thang'] / dg['md_moi_mm']
    tong = {'md': 0.0, 'chi_phi': 0.0, 'gia': 0.0, 'cham': 0}
    chi_tiet, them, loi_ds = [], {}, []
    for x in cr.get('goi_thay_doi', []):
        g = by.get(x['ma'])
        if not g or not g['la']:
            loi_ds.append(f'Gói {x["ma"]} không phải gói lá của WBS'); continue
        d = float(x['md_tang']); cp_ = d * rate(g['loai'])
        ng = gv[x['ma']]; toc_do = sum(float(tv[p].get('ty_le', 1)) for p in [ng['R']] + ng.get('ho_tro', []))
        them_ngay = math.ceil(d / toc_do) if d > 0 else 0
        l = lg.get(x['ma'], {}); du_tru = l.get('du_tru_cpm', 0)
        c = them_ngay if l.get('gang') else max(0, them_ngay - du_tru)
        tong = {'md': tong['md'] + d, 'chi_phi': tong['chi_phi'] + cp_, 'gia': tong['gia'] + cp_ * he_so(x['ma']), 'cham': max(tong['cham'], c)}
        them[x['ma']] = them_ngay
        chi_tiet.append({'ma': x['ma'], 'ten': g['ten'], 'md_tang': d, 'gang': bool(l.get('gang')), 'du_tru': du_tru, 'ngay_cham': c})
    for x in cr.get('goi_moi', []):
        if x.get('loai') not in dg['loai_cong_viec']:
            loi_ds.append(f'Gói mới {x.get("ma")} thiếu loại công việc hợp lệ'); continue
        if x.get('cha') not in by:
            loi_ds.append(f'Gói mới {x.get("ma")} có mục cha {x.get("cha")} không tồn tại')
        cp_ = float(x['md']) * rate(x['loai'])
        tong = dict(tong, md=tong['md'] + float(x['md']), chi_phi=tong['chi_phi'] + cp_, gia=tong['gia'] + cp_ * he_so(x.get('cha', '')))
        chi_tiet.append({'ma': x['ma'], 'ten': x['ten'], 'md_tang': float(x['md']), 'gang': False, 'du_tru': None, 'ngay_cham': None})
    return tong, chi_tiet, them, loi_ds


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


def tai_lieu_anh_huong(cr):
    tl = []
    for n in cr.get('nut_thay_doi') or ['wbs']:
        r = subprocess.run([sys.executable, os.path.join(loi.THU_MUC_LOI, 'scripts', 'chay.py'), 'anh_huong', n, '--json'], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', cwd=loi.GOC)
        for b in json.loads(r.stdout)['anh_huong']:
            if b['buoc'] not in [x['buoc'] for x in tl]:
                tl.append(b)
    return tl


def nguoi_phe_duyet(muc, vai):
    ten = [vai[k]['ho_ten'] for k in muc['tham_quyen'] if k in vai]
    return muc['nguoi_phe_duyet'] + (f' ({", ".join(ten)})' if ten else '')


def kiem_tra_rui_ro(cr):
    rr = {r['ma'] for r in loi.doc_json('du_lieu/rui_ro.json', {'danh_sach': []})['danh_sach']}
    for m in cr.get('ma_rui_ro', []):
        if m not in rr:
            print(f'CẢNH BÁO: TD17 Mã rủi ro {m} không có trong sổ rủi ro')


def danh_gia():
    pl = nap_quy_tac()
    cr = json.load(open(a.doi_tuong, encoding='utf-8'))
    wbs = loi.doc_json('du_lieu/wbs.json'); lich = loi.doc_json('du_lieu/lich.json'); dg = loi.doc_json('dau_vao/don_gia.json')
    pc = loi.doc_json('du_lieu/phan_cong.json'); tv = {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']}
    cp = loi.doc_json('du_lieu/chi_phi.json'); da = loi.du_an()
    he_so, can_cu_gia = qt.he_so_gia(pl, cp, wbs)
    tong, chi_tiet, them, loi_ds = tinh_goi(cr, wbs, lich, dg, pc, tv, he_so)
    if loi_ds:
        loi.thoat_loi('\n- '.join([''] + loi_ds))
    kiem_tra_rui_ro(cr)
    cham_cut_over = max(0, tong['cham'] - lich.get('du_tru_den_cut_over_ngay', 0))
    moc = qt.moc_bi_anh_huong(them, wbs, lich, loi.ngay_lam_viec(da))
    dk = dieu_kien_cr(cr, pl, cham_cut_over, moc)
    diem, muc, ly_do = qt.cham_diem({'md': tong['md'], 'chi_phi': tong['chi_phi'], 'tieu_hao_du_tru': tong['cham'], 'cham_cut_over': cham_cut_over}, dk, pl)
    vai, _, _ = qt.vai_ban(pc, tv, loi.doc_json('dau_vao/nha_thau.json'), loi.doc_json('du_lieu/hsmt.json'))
    phu_luc = muc.get('phu_luc_hop_dong', False) and any(d.get('phu_luc') for d in pl['dieu_kien'] if d['ma'] in dk)
    KY_HD = loi.da_ky_hop_dong()  # trước khi ký hợp đồng, HSMT và HSDT chưa khóa
    tl = tai_lieu_anh_huong(cr)
    ngay_dx = cr.get('ngay', loi.bay_gio()[:10])
    han_dg = qt.cong_ngay_lam_viec(ngay_dx, muc['thoi_han_danh_gia_ngay'], da)
    ma = f'CR{len(so["yeu_cau"]) + 1:02d}'
    rec = {'ma': ma, 'tieu_de': cr['tieu_de'], 'mo_ta': cr.get('mo_ta', ''), 'ly_do': cr.get('ly_do', ''), 'nguon': cr.get('nguon', ''),
           'nguoi_de_xuat': cr.get('nguoi_de_xuat', ''), 'ngay_de_xuat': ngay_dx, 'noi_bo': bool(cr.get('noi_bo')), 'dieu_kien': dk,
           'ma_rui_ro': cr.get('ma_rui_ro', []), 'can_cu_hsmt': cr.get('can_cu_hsmt', ''), 'nhan_dinh_ban_dau': cr.get('nhan_dinh_ban_dau', ''),
           'rui_ro_moi': cr.get('rui_ro_moi', ''), 'md_tang': round(tong['md'], 2), 'chi_phi_tang': round(tong['chi_phi']), 'chi_phi_noi_bo': round(tong['chi_phi']),
           'gia_de_nghi': round(tong['gia']), 'can_cu_gia_de_nghi': can_cu_gia, 'ngay_cham': tong['cham'], 'ngay_cham_cut_over': cham_cut_over,
           'moc_anh_huong': moc, 'chi_tiet_goi': chi_tiet, 'diem_tac_dong': diem, 'ly_do_muc': ly_do, 'muc': muc['ma'], 'muc_ten': muc['ten'],
           'nguoi_phe_duyet_theo_quy_dinh': nguoi_phe_duyet(muc, vai), 'han_danh_gia_ngay': muc['thoi_han_danh_gia_ngay'], 'han_danh_gia': han_dg,
           'han_quyet_dinh': qt.cong_ngay_lam_viec(han_dg, muc['thoi_han_quyet_dinh_ngay'], da),
           'han_hop_ban': qt.cong_ngay_lam_viec(ngay_dx, muc['hop_ban_trong_ngay'], da) if muc.get('hop_ban_trong_ngay') else '',
           'tai_lieu_cap_nhat': [f'{b["buoc"]} ({b["ten"]})' for b in tl if b['da_tao'] and not (b['khoa'] and KY_HD)],
           'tai_lieu_khoa': [f'{b["buoc"]} ({b["ten"]})' for b in tl if b['khoa'] and KY_HD],
           'phu_luc_hop_dong': phu_luc, 'van_ban_yeu_cau': 'Phụ lục hợp đồng' if phu_luc else muc['van_ban'],
           'trang_thai': 'Chờ phê duyệt', 'lich_su': [{'ngay': ngay_dx, 'ghi_luc': loi.bay_gio(), 'trang_thai': 'Chờ phê duyệt', 'nguoi': cr.get('nguoi_de_xuat', ''),
                                                       'ghi_chu': 'Lập và đánh giá tác động'}]}
    so['yeu_cau'].append(rec)
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{ma}.danh_gia', 'script', f'Đánh giá {ma}: {rec["tieu_de"]}', vao=[a.doi_tuong], ra=['du_lieu/thay_doi.json'],
                    ket_qua=rec['muc_ten'], chi_tiet={k: rec[k] for k in ('md_tang', 'chi_phi_noi_bo', 'gia_de_nghi', 'ngay_cham', 'ngay_cham_cut_over', 'diem_tac_dong')})
    in_ket_qua(rec)


def in_ket_qua(rec):
    print(f'{rec["ma"]}: tăng {rec["md_tang"]:g} MD, chi phí nội bộ {loi.tien(rec["chi_phi_noi_bo"])} đồng, giá đề nghị Chủ đầu tư {loi.tien(rec["gia_de_nghi"])} đồng '
          f'({rec["can_cu_gia_de_nghi"]}). Chậm ước tính {rec["ngay_cham"]} ngày ({rec["ngay_cham_cut_over"]} ngày sau khi trừ dự trữ đến cut over).')
    for m in rec['moc_anh_huong']:
        print(f'  Mốc {m["ma"]} (Đợt {m["dot"]}): dời ngày dự kiến {m["ngay_doi"]} ngày, vượt hạn {m["vuot_han"]} ngày (ước tính theo phụ thuộc)')
    print(f'Điểm tác động {rec["diem_tac_dong"]}, mức {rec["muc_ten"]}' + (f' do: {"; ".join(rec["ly_do_muc"])}' if rec['ly_do_muc'] else '') + '.')
    print(f'Phê duyệt: {rec["nguoi_phe_duyet_theo_quy_dinh"]}. Hạn đánh giá {loi.ngay(rec["han_danh_gia"])}, hạn quyết định {loi.ngay(rec["han_quyet_dinh"])}'
          + (f', họp ban trước {loi.ngay(rec["han_hop_ban"])}' if rec['han_hop_ban'] else '') + f'. Văn bản: {rec["van_ban_yeu_cau"]}.')
    print('Tài liệu phải cập nhật nếu phê duyệt: ' + '; '.join(rec['tai_lieu_cap_nhat']))
    if rec['tai_lieu_khoa']:
        print('Không sửa (đường cơ sở đấu thầu): ' + '; '.join(rec['tai_lieu_khoa']) + ('. Cần phụ lục hợp đồng.' if rec['phu_luc_hop_dong'] else '. Ghi nhận trong biên bản thỏa thuận.'))


# ---------------------------------------------------------------- quyết định, thực hiện, đóng
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
    cr.update({'trang_thai': a.ket_qua, 'nguoi_quyet_dinh': a.nguoi, 'ngay_quyet_dinh': NGAY, 'van_ban': a.van_ban.strip() or cr.get('van_ban', ''),
               'ngay_xem_lai': a.xem_lai or '', 'dem_phien_ban_khi_quyet_dinh': loi.doc_json('du_lieu/phien_ban.json', {}).get('dem', 0)})
    if cr.get('han_quyet_dinh'):
        cr['quyet_dinh_dung_han'] = NGAY <= cr['han_quyet_dinh']
        if not cr['quyet_dinh_dung_han']:
            print(f'CẢNH BÁO: TD16 {cr["ma"]} quyết định ngày {loi.ngay(NGAY)}, quá hạn {loi.ngay(cr["han_quyet_dinh"])}')
    lich_su(cr, a.ket_qua, a.ghi_chu)
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{cr["ma"]}.quyet_dinh', 'nguoi_dung', f'{a.ket_qua} {cr["ma"]}: {a.ghi_chu}', ra=['du_lieu/thay_doi.json'], ket_qua=a.ket_qua)
    print(f'{cr["ma"]}: {a.ket_qua}.')
    if a.ket_qua == 'Đã phê duyệt':
        print('Thực hiện: sửa dữ liệu nguồn (lam_viec/wbs/wbs_nhap.json, giao việc), chạy lại theo thứ tự: ' + '; '.join(cr['tai_lieu_cap_nhat'])
              + f'. Ghi --ghi-chu "{cr["ma"]}" khi hoàn thiện từng tài liệu. Sau khi kiểm tra đạt, chạy thuc_hien rồi dong.')
    elif a.ket_qua == 'Hoãn':
        print(f'Xem xét lại ngày {loi.ngay(a.xem_lai)}: quyết định lại bằng quyet_dinh, hoặc dong khi hai bên thống nhất không thực hiện.')
    else:
        print('Thông báo lý do từ chối cho người đề xuất, sau đó dong kèm --ghi-chu.')


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
    """Tài liệu còn dùng đầu vào cũ hoặc chưa tạo lại sau quyết định phê duyệt, và phiên bản sau thay đổi."""
    t_qd = next((x.get('ghi_luc', x['ngay']) for x in reversed(cr['lich_su']) if x['trang_thai'] == 'Đã phê duyệt'), '')
    sd = loi.so_do(); reg = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})['tai_lieu']
    bd = loi.nut_bien_dong(sd); cu, chua, pb_sau = [], [], {}
    dem_qd = cr.get('dem_phien_ban_khi_quyet_dinh')
    for s_ in cr.get('tai_lieu_cap_nhat', []):
        b = next((x for x in sd['buoc'] if x['id'] == s_.split(' ')[0]), None)
        if not b:
            continue
        ds_tep = []
        for q in b['ra'].values():
            ds_tep += [k for k in reg if k.startswith(q.rstrip('/') + '/')] if os.path.isdir(loi.duong_dan(q)) else [q]
        for p in ds_tep:
            lst = reg.get(p, [])
            if not lst:
                continue
            pb_sau[p] = lst[-1]['phien_ban']
            if (max(lst[-1].get('thu_tu', 0), lst[-1].get('thu_tu_kiem_tra', 0)) <= dem_qd) if dem_qd is not None else \
                    (max(lst[-1]['ngay'], lst[-1].get('ngay_kiem_tra', '')) <= t_qd):
                chua.append(f'{b["id"]} ({p})')
            if any(loi.bam_nut(sd, n) != h for n, h in lst[-1].get('vao', {}).items() if n in b['vao'] and n not in bd and loi.duong_dan_nut(sd, n)):
                cu.append(f'{b["id"]} ({p})')
    return cu, chua, pb_sau


def dong(cr):
    if cr['trang_thai'] in ('Từ chối', 'Hoãn'):
        if not a.ghi_chu.strip():
            loi.thoat_loi(f'TD12 Đóng yêu cầu {cr["trang_thai"].lower()} cần --ghi-chu: lý do và việc đã thông báo người đề xuất')
        ket_qua = cr['trang_thai']
    elif cr['trang_thai'] == 'Đã thực hiện':
        cu, chua, pb_sau = tai_lieu_chua_cap_nhat(cr)
        if (cu or chua) and not a.bo_qua_kiem_tra:
            loi.thoat_loi('Chưa đóng được CR. ' + ('Tài liệu còn dùng đầu vào cũ: ' + ', '.join(sorted(set(cu))) + '. ' if cu else '') +
                          ('Tài liệu chưa được tạo lại sau quyết định phê duyệt: ' + ', '.join(sorted(set(chua))) + '. ' if chua else '') +
                          'Chạy lại các bước này (chay.py trang_thai) hoặc dùng --bo-qua-kiem-tra kèm lý do trong --ghi-chu.')
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
              f'đề nghị {loi.tien(c.get("gia_de_nghi") or 0)} đồng, chậm {c["ngay_cham"]} ngày, điểm {c.get("diem_tac_dong", "")}, mức {c["muc_ten"]}')
    sys.exit(0)
if a.lenh == 'danh_gia':
    danh_gia(); sys.exit(0)
CR = next((c for c in so['yeu_cau'] if c['ma'] == a.doi_tuong), None)
if not CR:
    loi.thoat_loi('Không có yêu cầu thay đổi ' + str(a.doi_tuong))
LENH = {'quyet_dinh': quyet_dinh, 'thuc_hien': thuc_hien, 'dong': dong}
if a.lenh not in LENH:
    loi.thoat_loi('Lệnh không hợp lệ')
LENH[a.lenh](CR)
