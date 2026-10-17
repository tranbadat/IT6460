"""Tổng hợp số liệu kết thúc dự án: kế hoạch so với thực tế về phạm vi, tiến độ, chi phí, nhân lực,
nghiệm thu, lỗi, thay đổi, rủi ro và bộ chỉ tiêu đánh giá (KPI).

Dùng: python tong_hop_ket_thuc.py [--ngay yyyy-mm-dd]
  --ngay  ngày chốt số liệu, mặc định là ngày ghi nhận cuối cùng trong nhật ký công việc.
Đầu vào: du_lieu/{wbs,lich,phan_cong,chi_phi,rui_ro,hsmt,rfp_yeu_cau}.json, du_lieu/thay_doi.json (nếu có),
         dau_vao/{du_an,thanh_vien,don_gia}.json, dau_vao/thuc_te/*.csv (xem qlda-bao-cao-tien-do/references/nhap_lieu.md).
Bước này gọi tinh_tien_do.py cho kỳ cuối để có SPI, CPI chốt và kiểm tra dữ liệu nhật ký.
KPI mặc định: references/kpi_mac_dinh.json, ghi đè ngưỡng trong dau_vao/kpi.json (kèm lý do).
Ra: du_lieu/ket_thuc.json. Mã thoát 0 đạt, 1 lỗi dữ liệu.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse
import datetime as dt
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('--ngay'); a = ap.parse_args()
D = dt.date.fromisoformat
da = loi.du_an(); dg = loi.doc_json('dau_vao/don_gia.json')
tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']; tv = {t['id']: t for t in tvs}
wbs = loi.doc_json('du_lieu/wbs.json'); lich = loi.doc_json('du_lieu/lich.json'); pc = loi.doc_json('du_lieu/phan_cong.json')
cp = loi.doc_json('du_lieu/chi_phi.json'); rr = loi.doc_json('du_lieu/rui_ro.json'); hsmt = loi.doc_json('du_lieu/hsmt.json')
rfp = loi.doc_json('du_lieu/rfp_yeu_cau.json'); so_td = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})
pl_td = loi.doc_json(os.path.join(loi.THU_MUC_SKILLS, 'qlda-change', 'references', 'phan_loai.json'))
KPI_CFG = loi.doc_json(os.path.join(HERE, '..', 'references', 'kpi_mac_dinh.json')); kpi_md = KPI_CFG['kpi']

nk = loi.doc_csv('dau_vao/thuc_te/nhat_ky_cong_viec.csv'); ht = loi.doc_csv('dau_vao/thuc_te/hoan_thanh.csv')
mt = {r['ma_moc']: r for r in loi.doc_csv('dau_vao/thuc_te/moc_thuc_te.csv')}
nt = loi.doc_csv('dau_vao/thuc_te/nghiem_thu.csv'); bug = loi.doc_csv('dau_vao/thuc_te/loi.csv')
cptt = loi.doc_csv('dau_vao/thuc_te/chi_phi_thuc_te.csv')
if not nk:
    loi.thoat_loi('Chưa có nhật ký công việc thực tế (dau_vao/thuc_te/nhat_ky_cong_viec.csv).')
ngay_chot = D(a.ngay) if a.ngay else max(D(r['ngay']) for r in nk)
F = []
add = lambda ma, mo, md='loi': F.append({'ma': ma, 'muc_do': md, 'mo_ta': mo})
days = loi.ngay_lam_viec(da)
by, la = loi.nut_wbs(wbs)

# 1. Chốt EVM kỳ cuối bằng tinh_tien_do.py
sp_cuoi = [s for s in lich['sprint'] if D(s['tu']) <= ngay_chot]
ky = sp_cuoi[-1]['ma'] if sp_cuoi and D(sp_cuoi[-1]['den']) == ngay_chot else 'KT'
r = subprocess.run([sys.executable, os.path.join(loi.THU_MUC_SKILLS, 'qlda-bao-cao-tien-do', 'scripts', 'tinh_tien_do.py'), '--ky',
                    ky if ky != 'KT' else ngay_chot.isoformat()] + (['--ma', 'KT'] if ky == 'KT' else []),
                   cwd=loi.GOC, capture_output=True, text=True, encoding='utf-8', errors='replace')
if r.returncode != 0:
    print(r.stdout, r.stderr)
    loi.thoat_loi('Dữ liệu thực tế chưa hợp lệ, sửa theo thông báo của tinh_tien_do.py rồi chạy lại.')
td = loi.doc_json(f'du_lieu/tien_do/{ky}.json')

# 2. Phạm vi
ht_moi = {}
for x in sorted(ht, key=lambda r: r['ngay_cap_nhat']):
    if D(x['ngay_cap_nhat']) <= ngay_chot:
        ht_moi[x['ma_goi']] = float(x['phan_tram'])
md_tt = {}
for x in nk:
    if D(x['ngay']) <= ngay_chot:
        md_tt[x['ma_goi']] = md_tt.get(x['ma_goi'], 0) + float(x['md'])
lg = {g['ma']: g for g in lich['goi']}
goi = []
md_tt_tron = dict(zip([g['ma'] for g in la], loi.lam_tron_tong([md_tt.get(g['ma'], 0) for g in la])))
for g in la:
    k, t = float(g['md']), md_tt_tron[g['ma']]
    goi.append({'ma': g['ma'], 'ten': g['ten'], 'md_ke_hoach': k, 'md_thuc_te': round(t, 2), 'chenh_lech': round(t - k, 2),
                'ty_le_chenh': round((t - k) / k, 4) if k else 0, 'phan_tram': ht_moi.get(g['ma'], 0.0),
                'nguoi': lg.get(g['ma'], {}).get('ho_ten_R', '')})
goi_xong = [x for x in goi if x['phan_tram'] >= 100]
goi_chua = [x for x in goi if x['phan_tram'] < 100]
vuot = sorted([x for x in goi if x['md_ke_hoach'] and x['ty_le_chenh'] > 0.2], key=lambda x: -x['chenh_lech'])
pham_vi = {'so_goi': len(goi), 'so_goi_hoan_thanh': len(goi_xong), 'ty_le_goi_hoan_thanh': round(len(goi_xong) / len(goi), 4) if goi else 0,
           'goi_chua_xong': goi_chua, 'goi_vuot_20pt': vuot[:10], 'goi': goi}

# 3. Tiến độ
moc = []
for m in lich['moc']:
    t = mt.get(m['ma'], {}).get('ngay_dat', '')
    lech = loi.ngay_lam_viec_giua(days, m['ngay'], t) if t else None
    tt = 'Chưa đạt' if not t else ('Đúng hạn' if lech <= 0 else f'Trễ {lech} ngày làm việc')
    moc.append({'ma': m['ma'], 'ten': m['ten'], 'ke_hoach': m['ngay'], 'thuc_te': t, 'lech_ngay': lech, 'trang_thai': tt,
                'dot_thanh_toan': m.get('dot_thanh_toan', '')})
moc_co = [m for m in moc if m['thuc_te']]
moc_cut = next((m for m in lich['moc'] if m['ngay'] == lich['cut_over'] or 'cut over' in m['ten'].lower()), lich['moc'][-1])
ngay_cut_tt = mt.get(moc_cut['ma'], {}).get('ngay_dat', '')
tre_cut = loi.ngay_lam_viec_giua(days, lich['cut_over'], ngay_cut_tt) if ngay_cut_tt else None
som_cut = max(0, -tre_cut) if tre_cut is not None else None
tre_cut = max(0, tre_cut) if tre_cut is not None else None
ngay_kt_tt = max([D(x['ngay']) for x in nk if D(x['ngay']) <= ngay_chot])
tien_do = {'ngay_bat_dau': lich['ngay_bat_dau'], 'ket_thuc_ke_hoach': lich['ket_thuc_du_kien'], 'ket_thuc_thuc_te': ngay_kt_tt.isoformat(),
           'cut_over': lich['cut_over'], 'moc_cut_over': moc_cut['ma'], 'cut_over_thuc_te': ngay_cut_tt,
           'so_ngay_tre_cut_over': tre_cut, 'so_ngay_som_cut_over': som_cut, 'dat_cut_over': tre_cut is not None and tre_cut <= 0,
           'so_moc': len(moc), 'so_moc_dat': len(moc_co), 'so_moc_dung_han': sum(1 for m in moc_co if m['lech_ngay'] <= 0),
           'ty_le_moc_dung_han': round(sum(1 for m in moc_co if m['lech_ngay'] <= 0) / len(moc), 4) if moc else 0, 'moc': moc,
           'spi_cuoi': td['spi'], 'cpi_cuoi': td['cpi'], 'ky_cuoi': ky, 'lich_su': loi.doc_json('du_lieu/tien_do/lich_su.json', {'ky': []})['ky']}
if tre_cut is None:
    add('K01', f'Chưa ghi ngày đạt mốc cut over {moc_cut["ma"]} trong moc_thuc_te.csv', 'canh_bao')

# 4. Nhân lực và chi phí
kh_nguoi = {}
for x in lich['phan_bo']:
    kh_nguoi[x['thanh_vien']] = kh_nguoi.get(x['thanh_vien'], 0) + float(x['md'])
tt_nguoi = {}
for x in nk:
    if D(x['ngay']) <= ngay_chot:
        tt_nguoi[x['thanh_vien']] = tt_nguoi.get(x['thanh_vien'], 0) + float(x['md'])
hs = float(dg.get('he_so_bao_hiem', 1.0))
tt_nguoi = dict(zip(tt_nguoi, loi.lam_tron_tong(list(tt_nguoi.values()))))
nguoi = []
for t in tvs:
    k, th = kh_nguoi.get(t['id'], 0), tt_nguoi.get(t['id'], 0)
    if not k and not th:
        continue
    dgn = loi.don_gia_ngay_vai_tro(dg, t['vai_tro'])
    if dgn is None:
        add('K02', f'Vai trò {t["vai_tro"]} của {t["ho_ten"]} không có lương tham chiếu trong don_gia.json'); dgn = 0
    nguoi.append({'id': t['id'], 'ho_ten': t['ho_ten'], 'vai_tro': t['vai_tro'], 'ten_vai_tro': dg['luong_tham_chieu_thang'].get(t['vai_tro'], {}).get('ten', t['vai_tro']), 'loai': t['loai'], 'md_ke_hoach': round(k, 2), 'md_thuc_te': round(th, 2),
                  'chenh_lech': round(th - k, 2), 'ty_le_chenh': round((th - k) / k, 4) if k else 0,
                  'chi_phi_ke_hoach': k * dgn * hs, 'chi_phi_thuc_te': th * dgn * hs})
md_kh = round(sum(x['md_ke_hoach'] for x in goi), 2); md_th = round(sum(x['md_thuc_te'] for x in goi), 2)
for k in ('chi_phi_ke_hoach', 'chi_phi_thuc_te'):  # làm tròn từng người sao cho tổng khớp tổng chính xác
    for x, v in zip(nguoi, loi.lam_tron_tong([x[k] for x in nguoi], 0)):
        x[k] = int(v)
cp_ns_kh = sum(x['chi_phi_ke_hoach'] for x in nguoi); cp_ns_tt = sum(x['chi_phi_thuc_te'] for x in nguoi)
b_kh = float(cp['B']); co_b_tt = bool(cptt); b_tt = sum(float(x['so_tien']) for x in cptt) if cptt else b_kh
gia = float(cp['gia_truoc_thue'])
chi_phi = {'BAC_md': md_kh, 'AC_md': md_th, 'chenh_md': round(md_th - md_kh, 2), 'ty_le_chenh_md': round((md_th - md_kh) / md_kh, 4) if md_kh else 0,
           'BAC': td['BAC'], 'AC': td['AC'], 'EV': td['EV'], 'A': cp['A'], 'B_ke_hoach': b_kh, 'B_thuc_te': b_tt, 'chenh_B': round(b_tt - b_kh), 'co_chi_phi_khac_thuc_te': co_b_tt,
           'B_ghi_chu': '' if co_b_tt else ' (chưa có số liệu thực tế, lấy theo kế hoạch)',
           'gia_hop_dong_truoc_thue': gia, 'chi_phi_nhan_su_ke_hoach': cp_ns_kh, 'chi_phi_nhan_su_thuc_te': cp_ns_tt,
           'chenh_chi_phi_nhan_su': cp_ns_tt - cp_ns_kh, 'he_so_bao_hiem': hs,
           'loi_nhuan_ke_hoach': round(gia - cp_ns_kh - b_kh), 'loi_nhuan_thuc_te': round(gia - cp_ns_tt - b_tt),
           'du_phong_ke_hoach': cp.get('du_phong_hien_co', cp.get('D', 0)), 'tong_emv': cp.get('tong_emv_rui_ro', 0)}
chi_phi['ty_suat_loi_nhuan_ke_hoach'] = round(chi_phi['loi_nhuan_ke_hoach'] / gia, 4) if gia else 0
chi_phi['ty_suat_loi_nhuan_thuc_te'] = round(chi_phi['loi_nhuan_thuc_te'] / gia, 4) if gia else 0
if not co_b_tt:
    add('K03', 'Chưa có chi_phi_thuc_te.csv, chi phí khác thực tế lấy bằng kế hoạch', 'canh_bao')
for x in nk:
    if x['ma_goi'] not in by:
        add('K04', f'Nhật ký ghi mã gói {x["ma_goi"]} không có trong WBS')

# 5. Nghiệm thu
nt_moi = {}
so_lan = {}
for x in sorted(nt, key=lambda r: r.get('ngay', '')):
    nt_moi[x['ma']] = x; so_lan[x['ma']] = so_lan.get(x['ma'], 0) + 1
for x in nt_moi.values():
    if x['ket_qua'] not in ('Đạt', 'Không đạt'):
        add('K05', f'nghiem_thu.csv: {x["ma"]} có kết quả "{x["ket_qua"]}", chỉ dùng Đạt hoặc Không đạt')
ds_nt = [dict(x, so_lan=so_lan[x['ma']]) for x in sorted(nt_moi.values(), key=lambda r: loi.khoa_ma(r['ma']))]
dat = [x for x in ds_nt if x['ket_qua'] == 'Đạt']
NHOM_NT = ('he_thong', 'san_pham', 'pham_vi', 'chinh_sach')  # yêu cầu về sản phẩm, không tính thủ tục đấu thầu, hợp đồng, nội dung đề xuất
khong_nt = {x['ma'] if isinstance(x, dict) else str(x) for x in wbs.get('khong_can_goi', [])}  # phần loại trừ phạm vi
yc = [y for y in rfp['yeu_cau'] if y.get('xu_ly') == 'dap_ung' and y.get('nhom') in NHOM_NT and y['ma'] not in khong_nt]
yc_kq = []
for y in yc:
    lq = [x for x in ds_nt if re.search(r'\b' + re.escape(y['ma']) + r'\b', x['tieu_chi'] + ' ' + x.get('ghi_chu', ''))]
    kq = 'Chưa nghiệm thu' if not lq else ('Đạt' if all(x['ket_qua'] == 'Đạt' for x in lq) else 'Không đạt')
    yc_kq.append({'ma': y['ma'], 'noi_dung': y['dien_giai'], 'ma_nghiem_thu': ', '.join(x['ma'] for x in lq), 'ket_qua': kq})
hm = []
for m in hsmt['mau_01a']:
    lq = [x for x in ds_nt if str(x.get('hang_muc', '')).strip() == str(m['stt'])]
    kq = 'Chưa nghiệm thu' if not lq else ('Đạt' if all(x['ket_qua'] == 'Đạt' for x in lq) else 'Không đạt')
    hm.append({'stt': m['stt'], 'danh_muc': m['danh_muc'], 'so_tieu_chi': len(lq), 'so_dat': sum(1 for x in lq if x['ket_qua'] == 'Đạt'), 'ket_qua': kq})
nghiem_thu = {'so_tieu_chi': len(ds_nt), 'so_dat': len(dat), 'ty_le_nghiem_thu_dat': round(len(dat) / len(ds_nt), 4) if ds_nt else 0,
              'so_nghiem_thu_lai': sum(1 for x in ds_nt if x['so_lan'] > 1), 'khong_dat': [x for x in ds_nt if x['ket_qua'] != 'Đạt'],
              'danh_sach': ds_nt, 'yeu_cau_rfp': yc_kq, 'so_yeu_cau_rfp': len(yc_kq),
              'so_yeu_cau_rfp_dat': sum(1 for x in yc_kq if x['ket_qua'] == 'Đạt'),
              'yeu_cau_chua_nghiem_thu': [x for x in yc_kq if x['ket_qua'] == 'Chưa nghiệm thu'], 'hang_muc': hm}
nghiem_thu['ty_le_yeu_cau_rfp_dat'] = round(nghiem_thu['so_yeu_cau_rfp_dat'] / len(yc_kq), 4) if yc_kq else 0
if not nt:
    add('K06', 'Chưa có kết quả nghiệm thu (nghiem_thu.csv)', 'canh_bao')

# 6. Lỗi
MUC = ['Nghiêm trọng', 'Cao', 'Trung bình', 'Thấp']
for x in bug:
    if x['muc_do'] not in MUC:
        add('K07', f'loi.csv: {x["ma"]} có mức "{x["muc_do"]}", chỉ dùng {", ".join(MUC)}')
    if x['ma_goi'] and x['ma_goi'] not in by:
        add('K08', f'loi.csv: {x["ma"]} ghi mã gói {x["ma_goi"]} không có trong WBS')
theo_muc = [{'muc': m, 'tong': sum(1 for x in bug if x['muc_do'] == m), 'da_dong': sum(1 for x in bug if x['muc_do'] == m and x['trang_thai'] == 'Đã đóng')} for m in MUC]
for t in theo_muc:
    t['con_mo'] = t['tong'] - t['da_dong']
tg = [loi.ngay_lam_viec_giua(days, x['ngay_phat_hien'], x['ngay_dong']) for x in bug if x['trang_thai'] == 'Đã đóng' and x.get('ngay_dong')]
theo_goi = {}
for x in bug:
    k = x['ma_goi'].split('.')[0] if x['ma_goi'] else '?'
    theo_goi[k] = theo_goi.get(k, 0) + 1
loi_ = {'tong': len(bug), 'theo_muc': theo_muc, 'con_mo': sum(t['con_mo'] for t in theo_muc),
        'loi_nghiem_trong_cao_con_mo': sum(t['con_mo'] for t in theo_muc if t['muc'] in ('Nghiêm trọng', 'Cao')),
        'mat_do_loi': round(len(bug) / md_th * 10, 2) if md_th else 0, 'thoi_gian_dong_tb': round(sum(tg) / len(tg), 1) if tg else 0,
        'theo_nhom_wbs': [{'nhom': k, 'ten': by[k]['ten'] if k in by else 'Không rõ', 'so_loi': v} for k, v in sorted(theo_goi.items(), key=lambda kv: loi.khoa_ma(kv[0]))],
        'con_mo_ds': [x for x in bug if x['trang_thai'] != 'Đã đóng']}

# 7. Thay đổi
han = {m['ma']: m['thoi_han_danh_gia_ngay'] for m in pl_td['muc']}
QD = ('Đã phê duyệt', 'Từ chối', 'Hoãn', 'Đã thực hiện', 'Đã đóng')
cr = []
for c in so_td['yeu_cau']:
    ngay_qd = c.get('ngay_quyet_dinh', '')
    so_ngay = loi.ngay_lam_viec_giua(days, c['ngay_de_xuat'], ngay_qd) if ngay_qd else None
    if so_ngay is not None and so_ngay < 0:
        add('K09', f'{c["ma"]}: ngày quyết định {ngay_qd} trước ngày đề xuất {c["ngay_de_xuat"]}, kiểm tra lại', 'canh_bao'); so_ngay = None
    dung_han = c['trang_thai'] in QD and so_ngay is not None and so_ngay <= han.get(c['muc'], 3)
    cr.append({'ma': c['ma'], 'tieu_de': c['tieu_de'], 'nguon': c.get('nguon', ''), 'muc': c.get('muc_ten', c['muc']), 'trang_thai': c['trang_thai'],
               'md_tang': c['md_tang'], 'chi_phi_tang': c['chi_phi_tang'], 'ngay_cham': c['ngay_cham'], 'ngay_de_xuat': c['ngay_de_xuat'],
               'ngay_quyet_dinh': ngay_qd, 'so_ngay_xu_ly': so_ngay, 'dung_han': dung_han, 'phu_luc_hop_dong': c.get('phu_luc_hop_dong', False)})
duyet = [c for c in cr if c['trang_thai'] in ('Đã phê duyệt', 'Đã thực hiện', 'Đã đóng')]
tt_cr = {}
for c in cr:
    tt_cr[c['trang_thai']] = tt_cr.get(c['trang_thai'], 0) + 1
thay_doi = {'tong': len(cr), 'theo_trang_thai': [{'trang_thai': k, 'so': v} for k, v in tt_cr.items()], 'so_duyet': len(duyet),
            'md_tang_duyet': round(sum(c['md_tang'] for c in duyet), 2), 'chi_phi_tang_duyet': round(sum(c['chi_phi_tang'] for c in duyet)),
            'ngay_cham_duyet': max([c['ngay_cham'] or 0 for c in duyet] or [0]), 'so_dung_han': sum(1 for c in cr if c['dung_han']),
            'ty_le_cr_dung_han': round(sum(1 for c in cr if c['dung_han']) / len(cr), 4) if cr else 1.0, 'danh_sach': cr}

# 8. Rủi ro
tdrr, su_kien = loi.theo_doi_rui_ro(ngay_chot.isoformat())
ds_rr = []
for r_ in rr['danh_sach']:
    ev = [x for x in su_kien if x['ma_rui_ro'] == r_['ma']]
    xr = [x for x in ev if x['trang_thai'] == 'Đã xảy ra']
    md_tdg = sum(float(x.get('md_tac_dong') or 0) for x in ev); tien_tdg = sum(float(x.get('chi_phi_tac_dong') or 0) for x in ev)
    ds_rr.append({'ma': r_['ma'], 'ten': r_['ten'], 'nhom': r_.get('nhom_ten', r_['nhom']), 'muc': r_.get('muc_ten', r_['muc']),
                  'emv_md': r_['emv_md'], 'emv_tien': r_['emv_tien'], 'trang_thai_cuoi': tdrr.get(r_['ma'], {}).get('trang_thai', 'Đang theo dõi'),
                  'da_xay_ra': bool(xr), 'da_kich_hoat': any(x['trang_thai'] == 'Đã kích hoạt ứng phó' for x in ev),
                  'hanh_dong': '. '.join(x['hanh_dong'] for x in ev if x.get('hanh_dong')), 'ma_cr': ', '.join(sorted({x['ma_cr'] for x in ev if x.get('ma_cr')})),
                  'md_tac_dong': round(md_tdg, 2), 'chi_phi_tac_dong': round(tien_tdg), 'so_su_kien': len(ev)})
ma_so = {r_['ma'] for r_ in rr['danh_sach']}
for m_ in sorted({x['ma_rui_ro'] for x in su_kien} - ma_so, key=loi.khoa_ma):  # rủi ro phát sinh ngoài sổ
    ev = [x for x in su_kien if x['ma_rui_ro'] == m_]
    ds_rr.append({'ma': m_, 'ten': next((x['ghi_chu'] for x in ev if x.get('ghi_chu')), 'Rủi ro phát sinh ngoài sổ'), 'nhom': 'Ngoài sổ đăng ký', 'muc': 'Chưa đánh giá',
                  'emv_md': 0, 'emv_tien': 0, 'trang_thai_cuoi': ev[-1].get('trang_thai', ''), 'da_xay_ra': any(x['trang_thai'] == 'Đã xảy ra' for x in ev),
                  'da_kich_hoat': any(x['trang_thai'] == 'Đã kích hoạt ứng phó' for x in ev), 'hanh_dong': '. '.join(x['hanh_dong'] for x in ev if x.get('hanh_dong')),
                  'ma_cr': ', '.join(sorted({x['ma_cr'] for x in ev if x.get('ma_cr')})), 'md_tac_dong': round(sum(float(x.get('md_tac_dong') or 0) for x in ev), 2),
                  'chi_phi_tac_dong': round(sum(float(x.get('chi_phi_tac_dong') or 0) for x in ev)), 'so_su_kien': len(ev), 'ngoai_so': True})
xay_ra = [x for x in ds_rr if x['da_xay_ra']]
du_phong = float(chi_phi['du_phong_ke_hoach'] or 0)
tac_dong_tien = sum(x['chi_phi_tac_dong'] for x in ds_rr)
rui_ro = {'tong': len(ds_rr), 'so_da_xay_ra': len(xay_ra), 'so_kich_hoat': sum(1 for x in ds_rr if x['da_kich_hoat']),
          'so_khong_xay_ra': sum(1 for x in ds_rr if not x['da_xay_ra']), 'tong_emv_md': rr['tong_hop']['tong_emv_md'],
          'tong_emv_tien': rr['tong_hop']['tong_emv_tien'], 'tac_dong_md': round(sum(x['md_tac_dong'] for x in ds_rr), 2),
          'tac_dong_tien': tac_dong_tien, 'du_phong': du_phong, 'ty_le_dung_du_phong': round(tac_dong_tien / du_phong, 4) if du_phong else 0,
          'ty_le_rui_ro_co_ung_pho': round(sum(1 for x in xay_ra if x['hanh_dong']) / len(xay_ra), 4) if xay_ra else 1.0,
          'xay_ra_ds': xay_ra, 'danh_sach': ds_rr, 'so_su_kien': len(su_kien),
          'rui_ro_moi': sorted({x['ma_rui_ro'] for x in su_kien} - {r_['ma'] for r_ in rr['danh_sach']})}
if not su_kien:
    add('K10', 'Chưa có nhật ký theo dõi rủi ro (theo_doi_rui_ro.csv), không đánh giá được ứng phó rủi ro', 'canh_bao')

# 9. KPI
do = {'so_ngay_tre_cut_over': tien_do['so_ngay_tre_cut_over'], 'ty_le_moc_dung_han': tien_do['ty_le_moc_dung_han'], 'spi_cuoi': td['spi'],
      'cpi_cuoi': td['cpi'], 'ty_le_chenh_md': abs(chi_phi['ty_le_chenh_md']), 'ty_le_goi_hoan_thanh': pham_vi['ty_le_goi_hoan_thanh'],
      'ty_le_nghiem_thu_dat': nghiem_thu['ty_le_nghiem_thu_dat'], 'ty_le_yeu_cau_rfp_dat': nghiem_thu['ty_le_yeu_cau_rfp_dat'],
      'loi_nghiem_trong_cao_con_mo': loi_['loi_nghiem_trong_cao_con_mo'], 'mat_do_loi': loi_['mat_do_loi'],
      'ty_le_cr_dung_han': thay_doi['ty_le_cr_dung_han'], 'ty_le_rui_ro_co_ung_pho': rui_ro['ty_le_rui_ro_co_ung_pho'],
      'ty_le_dung_du_phong': rui_ro['ty_le_dung_du_phong']}
ghi_de = {k['ma']: k for k in loi.doc_json('dau_vao/kpi.json', {'kpi': []}).get('kpi', [])}
kpi = []
for k in kpi_md:
    k = dict(k, **ghi_de.get(k['ma'], {}))
    v = do.get(k['do'])
    if v is None:
        kq = 'Chưa đủ dữ liệu'
    else:
        ok = v >= k['muc_tieu'] if k['so_sanh'] == 'ge' else (v <= k['muc_tieu'] if k['so_sanh'] == 'le' else v == k['muc_tieu'])
        kq = 'Đạt' if ok else 'Không đạt'
    f = (lambda x: loi.pt(x)) if k['don_vi'] == '%' else (lambda x: loi.so(x, 2) if isinstance(x, float) and x != int(x) else loi.so(x))
    kpi.append({'ma': k['ma'], 'nhom': k['nhom'], 'chi_tieu': k['chi_tieu'], 'so_sanh': k['so_sanh'], 'muc_tieu': k['muc_tieu'], 'thuc_te': v,
                'muc_tieu_hien_thi': ('Tối đa ' if k['so_sanh'] == 'le' else ('Tối thiểu ' if k['so_sanh'] == 'ge' else '')) + f(k['muc_tieu']) + ('' if k['don_vi'] in ('%', '') else ' ' + k['don_vi']),
                'thuc_te_hien_thi': '' if v is None else f(v) + ('' if k['don_vi'] in ('%', '') else ' ' + k['don_vi']),
                'ket_qua': kq, 'ly_do_ghi_de': ghi_de.get(k['ma'], {}).get('ly_do', '')})
so_dat = sum(1 for k in kpi if k['ket_qua'] == 'Đạt')
ty_le_kpi = round(so_dat / len(kpi), 4) if kpi else 0
xep_loai = next(x['ten'] for x in sorted(KPI_CFG['xep_loai'], key=lambda x: -x['tu']) if ty_le_kpi >= x['tu'])
theo_nhom_kpi = []
for nh in dict.fromkeys(k['nhom'] for k in kpi):
    ks = [k for k in kpi if k['nhom'] == nh]
    theo_nhom_kpi.append({'nhom': nh, 'so': len(ks), 'dat': sum(1 for k in ks if k['ket_qua'] == 'Đạt'), 'ma': ', '.join(k['ma'] for k in ks)})

loi_ds = [x for x in F if x['muc_do'] == 'loi']
out = {'ngay_chot': ngay_chot.isoformat(), 'ky_cuoi': ky, 'pham_vi': pham_vi, 'tien_do': tien_do, 'chi_phi': chi_phi, 'nhan_luc': nguoi,
       'nghiem_thu': nghiem_thu, 'loi': loi_, 'thay_doi': thay_doi, 'rui_ro': rui_ro, 'kpi': kpi, 'so_kpi': len(kpi), 'so_kpi_dat': so_dat,
       'ty_le_kpi_dat': ty_le_kpi, 'xep_loai': xep_loai, 'kpi_theo_nhom': theo_nhom_kpi,
       'xep_loai_thang': KPI_CFG['xep_loai'], 'kpi_khong_dat': [k for k in kpi if k['ket_qua'] != 'Đạt'],
       'kiem_tra': {'ket_luan': 'dat' if not loi_ds else 'chua_dat', 'phat_hien': F}}
for x in F:
    print(f"[{x['muc_do']}] {x['ma']}: {x['mo_ta']}")
if loi_ds:
    loi.ghi_json('lam_viec/ket_thuc/bao_cao_kiem_tra.json', out['kiem_tra'])
    loi.thoat_loi(f'{len(loi_ds)} lỗi dữ liệu, xem lam_viec/ket_thuc/bao_cao_kiem_tra.json')
loi.ghi_json('du_lieu/ket_thuc.json', out)
loi.hoan_tat_buoc('so_lieu_ket_thuc', 'Tổng hợp số liệu kết thúc dự án', ghi_chu=f'Chốt ngày {ngay_chot.isoformat()}', ket_qua=f'{so_dat}/{len(kpi)} KPI đạt')
print(f'Chốt số liệu ngày {loi.ngay(ngay_chot)}: {len(goi_xong)}/{len(goi)} gói hoàn thành, MD thực tế {loi.md(md_th)}/{loi.md(md_kh)}, '
      f'SPI {loi.so(td["spi"], 2)}, CPI {loi.so(td["cpi"], 2)}, nghiệm thu đạt {len(dat)}/{len(ds_nt)}, lỗi còn mở {loi_["con_mo"]}, '
      f'{len(cr)} yêu cầu thay đổi, {len(xay_ra)} rủi ro đã xảy ra. KPI đạt {so_dat}/{len(kpi)}.')
print('Đã ghi du_lieu/ket_thuc.json. Tiếp theo: python .claude/skills/qlda-loi/scripts/chay.py chuan_bi tong_ket')
