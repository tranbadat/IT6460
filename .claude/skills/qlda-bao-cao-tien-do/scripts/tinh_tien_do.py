"""Tính số liệu báo cáo tiến độ theo phương pháp giá trị thu được (EVM) cho một kỳ.

Dùng: python tinh_tien_do.py --ky S3            (ngày báo cáo là ngày cuối sprint S3)
      python tinh_tien_do.py --ky KT            (kỳ Kết thúc sau cut over, ngày báo cáo là ngay_dong_du_an của lịch)
      python tinh_tien_do.py --ky 2027-04-30 [--ma KT]   (ngày báo cáo bất kỳ, --ma đặt mã kỳ)
Đầu vào: du_lieu/lich.json, du_lieu/wbs.json, du_lieu/chi_phi.json, dau_vao/don_gia.json, dau_vao/thanh_vien.json,
         dau_vao/thuc_te/nhat_ky_cong_viec.csv (ngay, thanh_vien, ma_goi, md, ghi_chu),
         dau_vao/thuc_te/hoan_thanh.csv (ngay_cap_nhat, ma_goi, phan_tram, ghi_chu),
         dau_vao/thuc_te/moc_thuc_te.csv, theo_doi_rui_ro.csv, chi_phi_thuc_te.csv, so_van_de.csv, hanh_dong.csv,
         du_lieu/rui_ro.json, du_lieu/thay_doi.json (nếu có).
Ngày làm việc của dự án tính đến ngay_dong_du_an khi lịch có giai đoạn Kết thúc (thuc_te.ngay_lam_viec_du_an): nhật ký kỳ KT không bị
T04, T05, PV gồm gói Kết thúc, MD kế hoạch theo người gồm phan_bo kỳ KT.
Số liệu mô phỏng: có du_lieu/mo_phong.json (qlda-mo-phong) thì đầu ra ghi can_cu_mo_phong để báo cáo nêu số liệu thực tế là số liệu mô phỏng.
Cách tính:
- BAC theo MD là tổng MD gói lá, theo tiền là MD x đơn giá loại công việc (đường cơ sở chi phí nhân công).
- PV: phần kế hoạch của từng gói tính tuyến tính theo ngày làm việc đã qua trong khoảng bắt đầu, kết thúc của gói.
- EV: MD gói x tỷ lệ hoàn thành mới nhất đến ngày báo cáo. AC theo công: MD thực tế ghi nhận, quy tiền theo đơn giá loại công việc của gói.
- SPI = EV/PV, CPI = EV/AC, EAC = BAC/CPI, ETC = EAC - AC, VAC = BAC - EAC, TCPI = (BAC - EV)/(BAC - AC).
- Chi phí thực (thuc_te.py), theo don_gia.json cach_tra_luong như cost estimate, EV và AC cùng cơ sở lương:
  AC nhân sự = lương đến ngày báo cáo (MD nhật ký khi cong_suc, ngày huy động theo lich.json phan_bo[].quy khi huy_dong, ket_hop)
  x lương ngày vai trò x hệ số bảo hiểm. BAC nhân sự = lương kế hoạch cả dự án (bằng tong_chi_phi_nguoi của cost estimate).
  EV nhân sự = lương kế hoạch lũy kế tại thời điểm kế hoạch đạt khối lượng bằng EV (MD), nên đúng kế hoạch thì EV nhân sự bằng
  lương kế hoạch đến ngày báo cáo. CPI thực = EV nhân sự/AC nhân sự, chỉ dưới 1 khi lương đã trả vượt phần việc thu được.
  Chi phí khác (khoản B) chưa có kế hoạch chi theo thời gian nên trình bày riêng: đã chi so với dự toán B + D, không vào CPI thực.
  AC thực = AC nhân sự + chi phí khác đã chi. BAC thực = BAC nhân sự + B + D. EAC thực = AC nhân sự + (BAC nhân sự - EV nhân sự)
  + chi phí khác đã chi + chi phí khác còn lại theo dự toán (không nhỏ hơn cam kết). VAC thực = BAC thực - EAC thực.
  Chênh lệch giữa khoản A và lương kế hoạch thuộc cost estimate (chenh_lech_A_nguoi), không vào trạng thái.
  Tỷ lệ sử dụng quỹ huy động = MD thực tế/MD huy động đến ngày báo cáo, là chỉ số năng lực.
- Dự báo ngày hoàn thành: phần thời lượng kế hoạch còn lại chia SPI, cộng vào ngày báo cáo. Ngày báo cáo sau ngày kết thúc kế hoạch
  (kỳ KT): gói trước cut over đã xong thì lấy ngày xong thực tế của gói cuối, chưa xong thì MD còn lại chia nhịp EV bình quân mỗi ngày.
  Gói Kết thúc không vào dự báo. Dự báo vượt cut over thì trạng thái chung tối thiểu là vàng.
- Trạng thái theo ngưỡng trong du_an.json: xanh, vàng, đỏ. Trạng thái chung lấy mức xấu nhất của SPI, CPI theo công, CPI thực.
- Mốc: so ngày đạt (chỉ tính ngày đạt đến ngày báo cáo) với hạn của mốc (han, mốc cut over lấy ngày cut over hợp đồng,
  không có hạn thì lấy ngày kế hoạch), kèm lệch so với ngày kế hoạch hiện hành.
- Vấn đề (so_van_de.py): bảng lấy từ sổ vấn đề tại ngày báo cáo; tín hiệu tự động (gói chậm, chỉ số dưới ngưỡng, rủi ro đã xảy ra,
  mốc quá hạn) ghi nguồn và vấn đề tương ứng trong sổ.
Kiểm tra dữ liệu: T01 đến T12 nhật ký, hoàn thành, rủi ro; T13 đến T25 sổ vấn đề (xem so_van_de.py); T26 moc_thuc_te.csv sai dạng ngày;
T27 chi_phi_thuc_te.csv sai định dạng; T28 chi phí lương kế hoạch lệch cost estimate (cảnh báo); T29 vai trò huy động chưa có lương tham chiếu;
T30 chưa khai báo cach_tra_luong.
Ra: du_lieu/tien_do/<ky>.json, du_lieu/tien_do/hien_tai.json, du_lieu/tien_do/lich_su.json. Mã thoát 0 đạt, 1 lỗi dữ liệu.
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
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402
import so_van_de  # noqa: E402
import thuc_te  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('--ky', required=True); ap.add_argument('--ma', help='mã kỳ khi --ky là ngày, ví dụ KT cho kỳ kết thúc')
a = ap.parse_args()
lich = loi.doc_json('du_lieu/lich.json'); wbs = loi.doc_json('du_lieu/wbs.json'); dg = loi.doc_json('dau_vao/don_gia.json')
cp = loi.doc_json('du_lieu/chi_phi.json', {})
da = loi.du_an(); tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']; tv = {t['id']: t for t in tvs}
rr = loi.doc_json('du_lieu/rui_ro.json', {'danh_sach': []}); so_td = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})
D = dt.date.fromisoformat
sp = {s['ma']: s for s in thuc_te.cac_ky(lich, da)}  # sprint và kỳ KT (giai đoạn Kết thúc) khi lịch có
if a.ky == thuc_te.KY_KET_THUC and a.ky not in sp:
    loi.thoat_loi('Lịch chưa có giai đoạn Kết thúc (lich.json giai_doan ket_thuc, ngay_dong_du_an), lập lại master schedule hoặc dùng --ky <ngày> --ma KT.')
if a.ky in sp:
    ngay_bc = D(sp[a.ky]['den']); ky = a.ky; tu_ngay = sp[a.ky]['tu']
else:
    ngay_bc = D(a.ky); ky = a.ky if not a.ma else a.ma
    tu_ngay = next((s['tu'] for s in sp.values() if s['tu'] <= a.ky <= s['den']), lich['ngay_bat_dau'])
NBC = ngay_bc.isoformat()
days = thuc_te.ngay_lam_viec_du_an(da, lich)  # đến ngay_dong_du_an khi lịch có giai đoạn Kết thúc
idx = {d: i for i, d in enumerate(days)}
n_qua = sum(1 for d in days if d <= ngay_bc)
by, la = loi.nut_wbs(wbs)
lg = {x['ma']: x for x in lich['goi']}
rate = {g['ma']: dg['loai_cong_viec'][g['loai']]['don_gia_tron_goi_thang'] / dg['md_moi_mm'] for g in la}
F = []
add = lambda ma, mo, md='loi': F.append({'ma': ma, 'muc_do': md, 'mo_ta': mo})  # noqa: E731


doc_csv = loi.doc_csv


nk = doc_csv('dau_vao/thuc_te/nhat_ky_cong_viec.csv')
ht = doc_csv('dau_vao/thuc_te/hoan_thanh.csv')
mt_ds = doc_csv('dau_vao/thuc_te/moc_thuc_te.csv')
if not nk and not ht:
    loi.thoat_loi('Chưa có dữ liệu thực tế. Nhóm cần ghi dau_vao/thuc_te/nhat_ky_cong_viec.csv và hoan_thanh.csv (xem references/nhap_lieu.md).')

# kiểm tra dữ liệu thực tế
ngay_nguoi = {}
for i, r in enumerate(nk, 2):
    try:
        d = D(r['ngay']); m = float(r['md'])
    except Exception:
        add('T01', f'nhat_ky_cong_viec.csv dòng {i}: ngày hoặc MD không hợp lệ'); continue
    if r['thanh_vien'] not in tv:
        add('T02', f'nhat_ky_cong_viec.csv dòng {i}: thành viên {r["thanh_vien"]} không có trong thanh_vien.json')
    if r['ma_goi'] not in rate:
        add('T03', f'nhat_ky_cong_viec.csv dòng {i}: mã gói {r["ma_goi"]} không phải gói lá của WBS')
    if d < days[0] or d > days[-1]:
        add('T04', f'nhat_ky_cong_viec.csv dòng {i}: ngày {r["ngay"]} ngoài thời gian dự án', 'canh_bao')
    if d not in idx:
        add('T05', f'nhat_ky_cong_viec.csv dòng {i}: ngày {r["ngay"]} không phải ngày làm việc', 'canh_bao')
    k = (r['thanh_vien'], d); ngay_nguoi[k] = ngay_nguoi.get(k, 0) + m
for (p, d), m in ngay_nguoi.items():
    if p in tv and m > float(tv[p].get('ty_le', 1)) + 0.01:
        add('T06', f'{tv[p]["ho_ten"]} ghi {m:g} MD ngày {loi.ngay(d)}, vượt thời gian tham gia mỗi ngày')
pt, ngay_xong = {}, {}  # tỷ lệ mới nhất, ngày đạt 100% đến ngày báo cáo
for i, r in enumerate(sorted(ht, key=lambda r: r['ngay_cap_nhat']), 2):
    if r['ma_goi'] not in rate:
        add('T07', f'hoan_thanh.csv: mã gói {r["ma_goi"]} không phải gói lá'); continue
    try:
        d = D(r['ngay_cap_nhat']); v = float(r['phan_tram'])
    except Exception:
        add('T08', f'hoan_thanh.csv dòng {i}: dữ liệu không hợp lệ'); continue
    if not 0 <= v <= 100:
        add('T09', f'hoan_thanh.csv: tỷ lệ {v} của {r["ma_goi"]} ngoài 0 đến 100')
    if d <= ngay_bc:
        if r['ma_goi'] in pt and v < pt[r['ma_goi']] - 1e-9:
            add('T10', f'hoan_thanh.csv: tỷ lệ hoàn thành của {r["ma_goi"]} giảm từ {pt[r["ma_goi"]]:g} xuống {v:g}', 'canh_bao')
        pt[r['ma_goi']] = v
        if v >= 100:
            ngay_xong.setdefault(r['ma_goi'], d)
tdrr, _ = loi.theo_doi_rui_ro(NBC)
ma_rr = {r['ma'] for r in rr['danh_sach']}
for m in tdrr:
    if m not in ma_rr:
        add('T11', f'theo_doi_rui_ro.csv: rủi ro {m} chưa có trong sổ rủi ro, được tính là rủi ro phát sinh ngoài sổ. Bổ sung vào sổ (qlda-risk) nếu cần theo dõi tiếp', 'canh_bao')
    elif tdrr[m].get('trang_thai') not in loi.TRANG_THAI_RUI_RO:
        add('T12', f'theo_doi_rui_ro.csv: trạng thái "{tdrr[m].get("trang_thai")}" của {m} không thuộc {", ".join(loi.TRANG_THAI_RUI_RO)}')
# sổ vấn đề và hành động
tdrr_tat_ca, _ = loi.theo_doi_rui_ro()
vd, F_vd = so_van_de.lap_so(NBC, tu_ngay, tv, *so_van_de.tap_ma_hop_le(rr, tdrr_tat_ca, so_td))
F += F_vd
# mốc thực tế: chỉ tính ngày đạt đến ngày báo cáo
for m in thuc_te.kiem_tra_o(mt_ds, 'moc_thuc_te.csv', cot_ngay=('ngay_dat',), bat_buoc=('ma_moc', 'ngay_dat')):
    add('T26', m)
mt = {r['ma_moc']: r for r in mt_ds if thuc_te.la_ngay(r.get('ngay_dat', '')) and r['ngay_dat'] <= NBC}
# chi phí khác thực tế, huy động
cptt, sai_cp, _ = thuc_te.doc_chi_phi_thuc_te()
for m in sai_cp:
    add('T27', m)
lng = thuc_te.luong_ngay(dg, tvs); hs = float(dg.get('he_so_bao_hiem', 1.0))
hd_ca, _ = thuc_te.md_huy_dong(lich, tvs, days)
hd_den, _ = thuc_te.md_huy_dong(lich, tvs, days, ngay_bc)
for t in tvs:
    if lng[t['id']] is None and hd_ca.get(t['id']):
        add('T29', f'Vai trò {t["vai_tro"]} của {t["ho_ten"]} chưa có lương tham chiếu trong don_gia.json, không tính được chi phí huy động')
CACH = thuc_te.cach_tra_luong(dg)
if not CACH:
    add('T30', thuc_te.thong_bao_thieu_cach())
cp_hd_ca = thuc_te.chi_phi_luong(hd_ca, lng, hs); cp_hd_den = thuc_te.chi_phi_luong(hd_den, lng, hs)
cp_kh_ca = thuc_te.chi_phi_luong_ke_hoach(CACH, lich, tvs, dg, days, wbs['tong_md'])
lech_ce = thuc_te.doi_chieu_cost_estimate(cp, cp_kh_ca, CACH)
if lech_ce:
    add('T28', lech_ce, 'canh_bao')
loi_ = [f for f in F if f['muc_do'] == 'loi']
for f in F:
    print(f'[{f["muc_do"]}] {f["ma"]}: {f["mo_ta"]}')
if loi_:
    sys.exit(1)


def pv_frac(g, den=None):
    l = lg[g['ma']]; den = den or ngay_bc
    a_, b_ = D(l['bat_dau']), D(l['ket_thuc'])
    tot = sum(1 for d in days if a_ <= d <= b_) or 1
    qua = sum(1 for d in days if a_ <= d <= min(b_, den))
    return qua / tot


goi = []
PV = EV = AC = PVv = EVv = ACv = 0.0
ac_goi = {}
for r in nk:
    if D(r['ngay']) <= ngay_bc:
        ac_goi[r['ma_goi']] = ac_goi.get(r['ma_goi'], 0) + float(r['md'])
for g in la:
    md_ = float(g['md']); f_ = pv_frac(g); e_ = pt.get(g['ma'], 0) / 100; c_ = ac_goi.get(g['ma'], 0)
    PV += md_ * f_; EV += md_ * e_; AC += c_
    PVv += md_ * f_ * rate[g['ma']]; EVv += md_ * e_ * rate[g['ma']]; ACv += c_ * rate[g['ma']]
    if f_ > 0 or e_ > 0 or c_ > 0:
        lech = e_ - f_
        tt = 'Hoàn thành' if e_ >= 1 else ('Chậm' if lech < -0.1 else ('Vượt kế hoạch' if lech > 0.1 else 'Đúng kế hoạch'))
        goi.append({'ma': g['ma'], 'ten': g['ten'], 'md': md_, 'ke_hoach': round(f_, 4), 'thuc_te': round(e_, 4), 'md_thuc_te': round(c_, 2),
                    'lech': round(lech, 4), 'trang_thai': tt, 'nguoi': lg[g['ma']].get('ho_ten_R', ''), 'ket_thuc_ke_hoach': lg[g['ma']]['ket_thuc']})
BAC = float(wbs['tong_md']); BACv = sum(float(g['md']) * rate[g['ma']] for g in la)
spi = EV / PV if PV else 0; cpi = EV / AC if AC else 0
eac = BAC / cpi if cpi else BAC; eacv = BACv / (EVv / ACv) if ACv and EVv else BACv
tcpi = (BAC - EV) / (BAC - AC) if BAC - AC else 0
ng = da.get('nguong_canh_bao', {})

# chi phí thực theo cách trả lương
md_nk = {}
for r in nk:
    if D(r['ngay']) <= ngay_bc:
        md_nk[r['thanh_vien']] = md_nk.get(r['thanh_vien'], 0) + float(r['md'])
THEO_HD = thuc_te.theo_huy_dong(CACH)
AC_ns = sum(cp_hd_den.values()) if THEO_HD else sum(thuc_te.chi_phi_luong(md_nk, lng, hs).values())
AC_khac = thuc_te.tong_chi_phi_khac(cptt, ngay_bc); AC_thuc = AC_ns + AC_khac
B_kh = float(cp.get('B', 0)) + float(cp.get('D', 0))
BAC_ns = sum(cp_kh_ca.values())
kl_ngay = [sum(float(g['md']) * pv_frac(g, d) for g in la) for d in days]  # khối lượng kế hoạch lũy kế cuối mỗi ngày
cp_ngay = [thuc_te.chi_phi_luong_luy_ke(CACH, lich, tvs, dg, days, d, wbs['tong_md']) for d in days]  # lương kế hoạch lũy kế
PV_ns = thuc_te.chi_phi_luong_luy_ke(CACH, lich, tvs, dg, days, ngay_bc, wbs['tong_md'])
EV_ns = thuc_te.ev_luong(EV, kl_ngay, cp_ngay)
cpi_thuc = EV_ns / AC_ns if AC_ns else 0
BAC_thuc = BAC_ns + B_kh
khac_con = max(0.0, B_kh - AC_khac, thuc_te.tong_chi_phi_khac(cptt, loai='cam_ket'))
EAC_thuc = AC_ns + max(0.0, BAC_ns - EV_ns) + AC_khac + khac_con
md_hd = sum(hd_den.values())
ty_le_su_dung = AC / md_hd if md_hd else 0


def mau(v, vang, do):
    return 'Đỏ' if v < do else ('Vàng' if v < vang else 'Xanh')


tt_spi = mau(spi, ng.get('spi_vang', 0.95), ng.get('spi_do', 0.85)); tt_cpi = mau(cpi, ng.get('cpi_vang', 0.95), ng.get('cpi_do', 0.85))
tt_cpi_thuc = mau(cpi_thuc, ng.get('cpi_vang', 0.95), ng.get('cpi_do', 0.85)) if BAC_ns and AC_ns else 'Chưa đủ dữ liệu'
tt3 = (tt_spi, tt_cpi, tt_cpi_thuc)
tong = 'Đỏ' if 'Đỏ' in tt3 else ('Vàng' if 'Vàng' in tt3 else 'Xanh')
# Dự báo theo SPI: thời lượng còn lại của kế hoạch kéo dài theo 1/SPI
kt_kh = dt.date.fromisoformat(lich['ket_thuc_du_kien'])
idx_kt = max(i for i, d in enumerate(days) if d <= kt_kh) if any(d <= kt_kh for d in days) else len(days) - 1
goi_truoc_cut = [g for g in la if lg[g['ma']].get('giai_doan') != 'ket_thuc']  # gói Kết thúc làm sau cut over, không vào dự báo
md_con = sum(float(g['md']) * (1 - pt.get(g['ma'], 0) / 100) for g in goi_truoc_cut)
if n_qua - 1 <= idx_kt:
    du_bao_idx = n_qua - 1 + int(round(max(0, idx_kt - (n_qua - 1)) / spi)) if spi else idx_kt
else:  # ngày báo cáo sau ngày kết thúc kế hoạch (kỳ KT): phần việc còn lại chia nhịp EV bình quân mỗi ngày đã qua
    du_bao_idx = n_qua - 1 + (math.ceil(md_con / (EV / n_qua)) if EV and md_con > 1e-6 else 0)
ext = list(days)
while len(ext) <= du_bao_idx:
    ext.append(ext[-1] + dt.timedelta(days=1 if ext[-1].weekday() < 4 else 3))
du_bao = ext[max(0, du_bao_idx)]
if n_qua - 1 > idx_kt and md_con <= 1e-6:  # gói trước cut over đã xong: ngày xong thực tế của gói cuối
    du_bao = max((ngay_xong[g['ma']] for g in goi_truoc_cut if g['ma'] in ngay_xong), default=du_bao)
if du_bao.isoformat() > lich['cut_over'] and tong == 'Xanh':
    tong = 'Vàng'  # chỉ số đạt ngưỡng nhưng dự báo vượt cut over

# mốc: so với hạn (hạn hợp đồng hoặc ngày cut over), kèm lệch so với kế hoạch hiện hành
ma_cut = next((m['ma'] for m in lich['moc'] if m['ngay'] == lich['cut_over'] or 'cut over' in m['ten'].lower()), lich['moc'][-1]['ma'])


def trang_thai_moc(m, han, thuc):
    if not thuc:
        return 'Chưa đến hạn' if m['ngay'] > NBC else ('Chưa đạt, sau ngày kế hoạch' if han >= NBC else 'Quá hạn chưa đạt')
    if thuc > han:
        return f'Đạt, trễ hạn {loi.ngay_lam_viec_giua(days, han, thuc)} ngày làm việc'
    if thuc > m['ngay']:
        return f'Đạt trong hạn, sau kế hoạch {loi.ngay_lam_viec_giua(days, m["ngay"], thuc)} ngày làm việc'
    return 'Đạt, đúng hạn'


moc = []
for m in lich['moc']:
    han = m.get('han') or (lich['cut_over'] if m['ma'] == ma_cut else '') or m['ngay']
    thuc = mt.get(m['ma'], {}).get('ngay_dat', '')
    moc.append({'ma': m['ma'], 'ten': m['ten'], 'ke_hoach': m['ngay'], 'han': han, 'thuc_te': thuc, 'trang_thai': trang_thai_moc(m, han, thuc)})
# công sức theo thành viên, huy động
tl_sp = thuc_te.ty_le_sprint_da_qua(lich, days, ngay_bc)
nguoi = []
for t in tvs:
    kh = sum(r['md'] * tl_sp.get(r['sprint'], 0) for r in lich['phan_bo'] if r['thanh_vien'] == t['id'])
    th = sum(float(r['md']) for r in nk if r['thanh_vien'] == t['id'] and D(r['ngay']) <= ngay_bc)
    q = hd_den.get(t['id'], 0)
    if kh or th or q:
        nguoi.append({'ho_ten': t['ho_ten'], 'ke_hoach': round(kh, 2), 'thuc_te': round(th, 2), 'chenh_lech': round(th - kh, 2),
                      'huy_dong': round(q, 2), 'san_sang': round(q - th, 2), 'ty_le_su_dung': round(th / q, 4) if q else 0})
rui_ro = []
for r in rr['danh_sach']:
    t = tdrr.get(r['ma'], {}); tt = t.get('trang_thai', 'Đang theo dõi')
    if r['muc'] == 'cao' or tt not in ('Đang theo dõi',):
        rui_ro.append({'ma': r['ma'], 'ten': r['ten'], 'muc': r.get('muc_ten', r['muc']), 'trang_thai': tt, 'hanh_dong': t.get('hanh_dong', ''),
                       'phu_trach': r.get('ho_ten_phu_trach', '')})


def trang_thai_cr_tai(c, ngay):
    """Trạng thái của CR tại ngày báo cáo theo lịch sử (báo cáo lập lại sau quyết định vẫn ghi trạng thái tại thời điểm của kỳ)."""
    ls_ = [x for x in c.get('lich_su', []) if x.get('ngay', '') <= ngay]
    return ls_[-1]['trang_thai'] if ls_ else c['trang_thai']


cr = [{'ma': c['ma'], 'tieu_de': c['tieu_de'], 'trang_thai': trang_thai_cr_tai(c, NBC), 'md_tang': c['md_tang'], 'ngay_cham': c['ngay_cham'],
       'ngay_cham_cut_over': c.get('ngay_cham_cut_over', 0), 'cut_over_moi': c.get('cut_over_moi', ''), 'gia_de_nghi': c.get('gia_de_nghi'),
       'muc_ten': c.get('muc_ten', ''), 'phu_luc_hop_dong': bool(c.get('phu_luc_hop_dong'))} for c in so_td['yeu_cau'] if c['ngay_de_xuat'] <= NBC]

# tín hiệu tự động đối chiếu với sổ vấn đề
ten_rr = {r['ma']: r['ten'] for r in rr['danh_sach']}
tin_hieu = [{'nguon': 'Gói chậm', 'noi_dung': f'Gói {x["ma"]} {x["ten"]}: hoàn thành {loi.pt(x["thuc_te"])}, kế hoạch {loi.pt(x["ke_hoach"])}',
             'khop': ('mo_ta', x['ma'])} for x in goi if x['trang_thai'] == 'Chậm']
for ten, v, t_, nguong, loai in (('SPI', spi, tt_spi, ng.get('spi_vang', 0.95), 'Tiến độ'), ('CPI theo công', cpi, tt_cpi, ng.get('cpi_vang', 0.95), 'Chi phí'),
                                 ('CPI theo chi phí thực', cpi_thuc, tt_cpi_thuc, ng.get('cpi_vang', 0.95), 'Chi phí')):
    if t_ in ('Vàng', 'Đỏ'):
        tin_hieu.append({'nguon': 'Chỉ số dưới ngưỡng', 'noi_dung': f'{ten}: {loi.so(v, 2)}, ngưỡng {loi.so(nguong, 2)}', 'khop': ('loai', loai)})
tin_hieu += [{'nguon': 'Rủi ro đã xảy ra', 'noi_dung': f'Rủi ro {m}: {ten_rr.get(m) or t.get("ghi_chu") or "phát sinh ngoài sổ"}', 'khop': ('rui_ro', m)}
             for m, t in sorted(tdrr.items(), key=lambda kv: loi.khoa_ma(kv[0])) if t.get('trang_thai') == 'Đã xảy ra']
tin_hieu += [{'nguon': 'Mốc quá hạn', 'noi_dung': f'Mốc {m["ma"]}: {m["ten"]}', 'khop': ('mo_ta', m['ma'])} for m in moc if m['trang_thai'] == 'Quá hạn chưa đạt']
van_de_phat_hien, F_th = so_van_de.doi_chieu_tin_hieu(tin_hieu, vd['van_de'])
for f in F_th:
    print(f'[{f["muc_do"]}] {f["ma"]}: {f["mo_ta"]}')
F += F_th

# chỉ số lưu 4 chữ số thập phân, chỉ làm tròn khi hiển thị (so2): làm tròn hai lần (0,9349 -> 0,935 -> 0,94) làm lệch số trong tài liệu
SO_LE_CHI_SO = 4
gia = float(cp.get('gia_truoc_thue', 0))
out = {'ky': ky, 'ngay_bao_cao': NBC, 'tu_ngay': tu_ngay, 'so_ngay_da_qua': n_qua, 'so_ngay_lam_viec': len(days), 'ty_le_thoi_gian': round(n_qua / len(days), 4),
       'BAC_md': BAC, 'PV_md': round(PV, 2), 'EV_md': round(EV, 2), 'AC_md': round(AC, 2), 'SV_md': round(EV - PV, 2), 'CV_md': round(EV - AC, 2),
       'BAC': round(BACv), 'PV': round(PVv), 'EV': round(EVv), 'AC': round(ACv), 'SV': round(EVv - PVv), 'CV': round(EVv - ACv),
       'spi': round(spi, SO_LE_CHI_SO), 'cpi': round(cpi, SO_LE_CHI_SO), 'EAC_md': round(eac, 2), 'ETC_md': round(eac - AC, 2), 'VAC_md': round(BAC - eac, 2), 'EAC': round(eacv), 'tcpi': round(tcpi, SO_LE_CHI_SO),
       'md_huy_dong': round(md_hd, 2), 'md_san_sang': round(md_hd - AC, 2), 'ty_le_su_dung_quy': round(ty_le_su_dung, 4),
       'BAC_thuc_nhan_su': round(BAC_ns), 'PV_thuc_nhan_su': round(PV_ns), 'EV_thuc_nhan_su': round(EV_ns), 'AC_thuc_nhan_su': round(AC_ns),
       'CV_thuc_nhan_su': round(EV_ns - AC_ns), 'cpi_thuc': round(cpi_thuc, SO_LE_CHI_SO), 'B_ke_hoach': round(B_kh), 'AC_thuc_khac': round(AC_khac),
       'AC_thuc': round(AC_thuc), 'BAC_thuc': round(BAC_thuc), 'EAC_thuc': round(EAC_thuc), 'VAC_thuc': round(BAC_thuc - EAC_thuc),
       'chi_phi_huy_dong_ca_du_an': round(sum(cp_hd_ca.values())), 'chi_phi_luong_ke_hoach_ca_du_an': round(sum(cp_kh_ca.values())),
       'cach_tra_luong': CACH, 'cach_tra_luong_ten': thuc_te.CACH_TRA_LUONG[CACH],
       'co_so_luong_ac': 'ngày huy động theo kế hoạch huy động' if THEO_HD else 'MD ghi công trong nhật ký công việc',
       'ghi_chu_san_sang': ('Ngày sẵn sàng không ghi công được tính lương theo cách trả lương đã khai báo.' if THEO_HD else
                            'Ngày sẵn sàng không ghi công không tính lương, chỉ dùng để theo dõi năng lực.'),
       'gia_truoc_thue': round(gia), 'chenh_lech_gia_du_bao': round(gia - EAC_thuc),
       'ty_le_hoan_thanh': round(EV / BAC, 4), 'du_bao_hoan_thanh': du_bao.isoformat(), 'ket_thuc_ke_hoach': lich['ket_thuc_du_kien'], 'cut_over': lich['cut_over'],
       'tre_so_voi_cut_over': du_bao.isoformat() > lich['cut_over'],
       'trang_thai_spi': tt_spi, 'trang_thai_cpi': tt_cpi, 'trang_thai_cpi_thuc': tt_cpi_thuc, 'trang_thai_chung': tong, 'goi': goi,
       'goi_cham': [x for x in goi if x['trang_thai'] == 'Chậm'],
       'so_goi_cham': sum(1 for x in goi if x['trang_thai'] == 'Chậm'), 'moc': moc, 'nguoi': nguoi, 'rui_ro': rui_ro, 'thay_doi': cr, 'so_thay_doi': len(cr),
       'van_de': vd['van_de'], 'hanh_dong': vd['hanh_dong'], 'van_de_tong_hop': vd['van_de_tong_hop'], 'van_de_phat_hien': van_de_phat_hien,
       'ngay_dong_du_an': lich.get('ngay_dong_du_an', ''), 'so_lieu_mo_phong': bool(thuc_te.mo_phong()),
       'can_cu_mo_phong': thuc_te.can_cu_mo_phong('báo cáo'), 'canh_bao_du_lieu': F}
os.makedirs(loi.duong_dan('du_lieu/tien_do'), exist_ok=True)
loi.ghi_json(f'du_lieu/tien_do/{ky}.json', out)
loi.ghi_json('du_lieu/tien_do/hien_tai.json', out)
ls = loi.doc_json('du_lieu/tien_do/lich_su.json', {'ky': []})
ls['ky'] = [x for x in ls['ky'] if x['ky'] != ky] + [{k: out[k] for k in ('ky', 'ngay_bao_cao', 'PV_md', 'EV_md', 'AC_md', 'spi', 'cpi', 'cpi_thuc',
                                                                         'ty_le_su_dung_quy', 'trang_thai_chung')}]
ls['ky'].sort(key=lambda x: x['ngay_bao_cao'])
loi.ghi_json('du_lieu/tien_do/lich_su.json', ls)
print(f'Kỳ {ky} ({loi.ngay(ngay_bc)}): PV {PV:.1f}, EV {EV:.1f}, AC {AC:.1f} MD. SPI {spi:.2f} ({tt_spi}), CPI {cpi:.2f} ({tt_cpi}), '
      f'CPI thực {cpi_thuc:.2f} ({tt_cpi_thuc}), sử dụng quỹ huy động {ty_le_su_dung:.1%}. Dự báo hoàn thành {loi.ngay(du_bao)}. '
      f'{out["so_goi_cham"]} gói chậm, {vd["van_de_tong_hop"]["so_mo"]} vấn đề mở.')
loi.ghi_nhat_ky('qlda-bao-cao-tien-do', f'tien_do.{ky}.tinh', 'script', f'Tính EVM kỳ {ky}: SPI {spi:.2f}, CPI {cpi:.2f}, CPI thực {cpi_thuc:.2f}',
                vao=['dau_vao/thuc_te/nhat_ky_cong_viec.csv', 'dau_vao/thuc_te/hoan_thanh.csv', 'dau_vao/thuc_te/chi_phi_thuc_te.csv',
                     'dau_vao/thuc_te/so_van_de.csv', 'dau_vao/thuc_te/hanh_dong.csv', 'du_lieu/lich.json', 'du_lieu/chi_phi.json'],
                ra=[f'du_lieu/tien_do/{ky}.json'], ket_qua=tong)
