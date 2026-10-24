"""Tổng hợp số liệu kết thúc dự án: kế hoạch so với thực tế về phạm vi, tiến độ, chi phí, nhân lực,
nghiệm thu, lỗi, thay đổi, rủi ro và bộ chỉ tiêu đánh giá (KPI).

Dùng: python tong_hop_ket_thuc.py [--ngay yyyy-mm-dd]
  --ngay  ngày chốt số liệu, mặc định là ngày ghi nhận cuối cùng trong nhật ký công việc. Ngày đó thuộc kỳ KT (giai đoạn Kết thúc) thì
          chốt tại ngày đóng dự án khi ngày hiện hành (QLDA_NGAY khi mô phỏng) đã đến ngày đó, để trùng báo cáo tiến độ kỳ KT.
Đầu vào: du_lieu/{wbs,lich,phan_cong,chi_phi,rui_ro,hsmt,rfp_yeu_cau}.json, du_lieu/thay_doi.json (nếu có),
         dau_vao/{du_an,thanh_vien,don_gia}.json, dau_vao/thuc_te/*.csv (xem qlda-bao-cao-tien-do/references/nhap_lieu.md).
Bước này gọi tinh_tien_do.py cho kỳ cuối để có SPI, CPI (theo công và theo chi phí thực), sổ vấn đề tại ngày chốt và kiểm tra dữ liệu nhật ký.
Chi phí nhân sự theo don_gia.json cach_tra_luong, cùng cơ sở với cost estimate (qlda-bao-cao-tien-do/scripts/thuc_te.py): cong_suc tính
trên MD công việc (kế hoạch là MD giao theo lich.json, thực tế là MD nhật ký), ngày sẵn sàng không tính lương; huy_dong, ket_hop tính
trên ngày huy động cắt theo ngày chốt, tách phần ngày có ghi công và ngày sẵn sàng. Chênh lệch giá hợp đồng và chi phí dùng dòng này.
Yêu cầu thay đổi đúng hạn khi ngày quyết định không muộn hơn han_quyet_dinh của CR, CR cũ không có khóa này thì tính theo thời hạn
đánh giá trong qlda-change/references/phan_loai.json.
Khoản B: khi don_gia.json du_phong_rui_ro có so_tien thì tách dự phòng rủi ro khỏi khoản B, chưa có thì giữ cả khoản B làm dự phòng kèm cảnh báo.
chi_phi_thuc_te.csv có cột loai thì tách đã chi (da_chi) và nghĩa vụ đã cam kết chưa chi (cam_ket, ví dụ bảo hành).
MD kế hoạch theo người lấy lich.json phan_bo (gồm kỳ KT), làm tròn sao cho tổng bằng tổng MD của WBS.
Ngày làm việc tính đến ngay_dong_du_an khi lịch có giai đoạn Kết thúc (thuc_te.ngay_lam_viec_du_an). Ngày chốt trong kỳ KT thì kỳ cuối là KT.
Có du_lieu/mo_phong.json (qlda-mo-phong) thì ghi so_lieu_mo_phong và can_cu_mo_phong cho phần căn cứ của báo cáo tổng kết, đánh giá, bài học.
Mốc so với hạn (han của mốc, mốc cut over lấy ngày cut over hợp đồng), kèm lệch so với ngày kế hoạch hiện hành.
KPI mặc định: references/kpi_mac_dinh.json, ghi đè ngưỡng trong dau_vao/kpi.json (kèm lý do).
Kiểm tra: K01 đến K10 như cũ; K11 định dạng ô CSV (lỗi); K12 MD kế hoạch theo người lệch tổng WBS; K13 chi phí huy động lệch cost estimate;
K14 dự phòng rủi ro chưa khai báo số tiền; K15 chưa ghi nghĩa vụ cam kết; K16 KPI chưa có ngưỡng; K17 còn vấn đề mở khi kết thúc (cảnh báo);
K18 chưa khai báo cach_tra_luong (dừng); K19 du_phong_rui_ro.so_tien ngoài khoảng 0 đến B; K20 không có dự phòng nhưng rủi ro có tác động (cảnh báo).
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
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-bao-cao-tien-do', 'scripts'))
import loi  # noqa: E402
import thuc_te  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('--ngay'); a = ap.parse_args()
D = dt.date.fromisoformat
da = loi.du_an(); dg = loi.doc_json('dau_vao/don_gia.json')
tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']; tv = {t['id']: t for t in tvs}
wbs = loi.doc_json('du_lieu/wbs.json'); lich = loi.doc_json('du_lieu/lich.json'); pc = loi.doc_json('du_lieu/phan_cong.json')
cp = loi.doc_json('du_lieu/chi_phi.json'); rr = loi.doc_json('du_lieu/rui_ro.json'); hsmt = loi.doc_json('du_lieu/hsmt.json')
rfp = loi.doc_json('du_lieu/rfp_yeu_cau.json'); so_td = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})
pl_td = loi.doc_json(os.path.join(loi.THU_MUC_SKILLS, 'qlda-change', 'references', 'phan_loai.json'))
KPI_CFG = loi.doc_json(os.path.join(HERE, '..', 'references', 'kpi_mac_dinh.json')); kpi_md = KPI_CFG['kpi']
CACH = thuc_te.cach_tra_luong(dg)
if not CACH:
    loi.thoat_loi(thuc_te.thong_bao_thieu_cach('K18'))
THEO_HD = thuc_te.theo_huy_dong(CACH)

nk = loi.doc_csv('dau_vao/thuc_te/nhat_ky_cong_viec.csv'); ht = loi.doc_csv('dau_vao/thuc_te/hoan_thanh.csv')
mt = {r['ma_moc']: r for r in loi.doc_csv('dau_vao/thuc_te/moc_thuc_te.csv')}
nt = loi.doc_csv('dau_vao/thuc_te/nghiem_thu.csv'); bug = loi.doc_csv('dau_vao/thuc_te/loi.csv')
tdrr_ds = loi.doc_csv('dau_vao/thuc_te/theo_doi_rui_ro.csv')
if not nk:
    loi.thoat_loi('Chưa có nhật ký công việc thực tế (dau_vao/thuc_te/nhat_ky_cong_viec.csv).')
sai_o = (thuc_te.kiem_tra_o(nk, 'nhat_ky_cong_viec.csv', cot_ngay=('ngay',), cot_so=('md',), bat_buoc=('ngay', 'thanh_vien', 'ma_goi', 'md'))
         + thuc_te.kiem_tra_o(ht, 'hoan_thanh.csv', cot_ngay=('ngay_cap_nhat',), cot_so=('phan_tram',), bat_buoc=('ngay_cap_nhat', 'ma_goi', 'phan_tram'))
         + thuc_te.kiem_tra_o(nt, 'nghiem_thu.csv', cot_ngay=('ngay',), bat_buoc=('ma', 'ket_qua'))
         + thuc_te.kiem_tra_o(bug, 'loi.csv', cot_ngay=('ngay_phat_hien', 'ngay_dong'), bat_buoc=('ma', 'ngay_phat_hien', 'muc_do', 'trang_thai'))
         + thuc_te.kiem_tra_o(tdrr_ds, 'theo_doi_rui_ro.csv', cot_ngay=('ngay',), cot_so=('md_tac_dong', 'chi_phi_tac_dong'), bat_buoc=('ngay', 'ma_rui_ro')))
cptt, sai_cp, co_loai = thuc_te.doc_chi_phi_thuc_te()
if sai_o + sai_cp:
    loi.thoat_loi('Dữ liệu thực tế sai định dạng (K11), sửa rồi chạy lại:\n- ' + '\n- '.join(sai_o + sai_cp))
ngay_chot = D(a.ngay) if a.ngay else max(D(r['ngay']) for r in nk)
ky_kt = thuc_te.ky_ket_thuc(lich, da)
if not a.ngay and ky_kt and D(ky_kt['tu']) <= ngay_chot <= D(ky_kt['den']):  # ghi nhận cuối trong kỳ KT: chốt tại ngày đóng dự án khi đã đến
    ngay_chot = max(ngay_chot, min(D(ky_kt['den']), D(loi.ngay_hien_hanh())))
F = []
add = lambda ma, mo, md='loi': F.append({'ma': ma, 'muc_do': md, 'mo_ta': mo})  # noqa: E731
days = thuc_te.ngay_lam_viec_du_an(da, lich)  # đến ngay_dong_du_an khi lịch có giai đoạn Kết thúc
by, la = loi.nut_wbs(wbs)

# 1. Chốt EVM kỳ cuối bằng tinh_tien_do.py
KT = thuc_te.KY_KET_THUC
sp_cuoi = [s for s in thuc_te.cac_ky(lich, da) if D(s['tu']) <= ngay_chot]
ky = sp_cuoi[-1]['ma'] if sp_cuoi and D(sp_cuoi[-1]['den']) == ngay_chot else KT
r = subprocess.run([sys.executable, os.path.join(loi.THU_MUC_SKILLS, 'qlda-bao-cao-tien-do', 'scripts', 'tinh_tien_do.py'), '--ky',
                    ky if ky != KT else ngay_chot.isoformat()] + (['--ma', KT] if ky == KT else []),
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
moc_cut = next((m for m in lich['moc'] if m['ngay'] == lich['cut_over'] or 'cut over' in m['ten'].lower()), lich['moc'][-1])


def ket_qua_moc(t, lech, lech_kh):
    if not t:
        return 'Chưa đạt'
    if lech > 0:
        return f'Trễ hạn {lech} ngày làm việc'
    return f'Đúng hạn, sau kế hoạch {lech_kh} ngày làm việc' if lech_kh > 0 else 'Đúng hạn'


moc = []
for m in lich['moc']:  # so với hạn của mốc (mốc cut over: ngày cut over hợp đồng), không có hạn thì so với ngày kế hoạch
    han = m.get('han') or (lich['cut_over'] if m['ma'] == moc_cut['ma'] else '') or m['ngay']
    t = mt.get(m['ma'], {}).get('ngay_dat', '')
    t = t if t and t <= ngay_chot.isoformat() else ''
    lech = loi.ngay_lam_viec_giua(days, han, t) if t else None
    lech_kh = loi.ngay_lam_viec_giua(days, m['ngay'], t) if t else None
    moc.append({'ma': m['ma'], 'ten': m['ten'], 'ke_hoach': m['ngay'], 'han': han, 'thuc_te': t, 'lech_ngay': lech, 'lech_ke_hoach': lech_kh,
                'trang_thai': ket_qua_moc(t, lech, lech_kh), 'dot_thanh_toan': m.get('dot_thanh_toan', '')})
moc_co = [m for m in moc if m['thuc_te']]
ngay_cut_tt = next(m['thuc_te'] for m in moc if m['ma'] == moc_cut['ma'])
tre_cut = loi.ngay_lam_viec_giua(days, lich['cut_over'], ngay_cut_tt) if ngay_cut_tt else None
som_cut = max(0, -tre_cut) if tre_cut is not None else None
tre_cut = max(0, tre_cut) if tre_cut is not None else None
ngay_kt_tt = max([D(x['ngay']) for x in nk if D(x['ngay']) <= ngay_chot])
tien_do = {'ngay_bat_dau': lich['ngay_bat_dau'], 'ket_thuc_ke_hoach': lich['ket_thuc_du_kien'], 'ket_thuc_thuc_te': ngay_kt_tt.isoformat(),
           'cut_over': lich['cut_over'], 'moc_cut_over': moc_cut['ma'], 'cut_over_thuc_te': ngay_cut_tt,
           'so_ngay_tre_cut_over': tre_cut, 'so_ngay_som_cut_over': som_cut, 'dat_cut_over': tre_cut is not None and tre_cut <= 0,
           'so_moc': len(moc), 'so_moc_dat': len(moc_co), 'so_moc_dung_han': sum(1 for m in moc_co if m['lech_ngay'] <= 0),
           'ty_le_moc_dung_han': round(sum(1 for m in moc_co if m['lech_ngay'] <= 0) / len(moc), 4) if moc else 0, 'moc': moc,
           'spi_cuoi': td['spi'], 'cpi_cuoi': td['cpi'], 'cpi_thuc_cuoi': td.get('cpi_thuc'), 'ky_cuoi': ky, 'lich_su': loi.doc_json('du_lieu/tien_do/lich_su.json', {'ky': []})['ky']}
if tre_cut is None:
    add('K01', f'Chưa ghi ngày đạt mốc cut over {moc_cut["ma"]} trong moc_thuc_te.csv', 'canh_bao')

# 4. Nhân lực và chi phí: chi phí nhân sự theo cách trả lương, đóng góp theo MD thực tế
tong_wbs = float(wbs['tong_md']); kh_tho = thuc_te.md_cong_viec(lich)
if abs(sum(kh_tho.values()) - tong_wbs) > 0.5:
    add('K12', f'MD kế hoạch theo người trong lich.json ({loi.md(sum(kh_tho.values()))}) lệch tổng WBS ({loi.md(tong_wbs)}), lập lại master schedule', 'canh_bao')
kh_nguoi = thuc_te.md_cong_viec(lich, tong_wbs=tong_wbs)  # một nguồn: tổng theo người bằng tổng WBS, cùng cost estimate
tt_nguoi = {}
for x in nk:
    if D(x['ngay']) <= ngay_chot:
        tt_nguoi[x['thanh_vien']] = tt_nguoi.get(x['thanh_vien'], 0) + float(x['md'])
hs = float(dg.get('he_so_bao_hiem', 1.0))
tt_nguoi = dict(zip(tt_nguoi, loi.lam_tron_tong(list(tt_nguoi.values()))))
hd_kh, _ = thuc_te.md_huy_dong(lich, tvs, days)
hd_tt, _ = thuc_te.md_huy_dong(lich, tvs, days, ngay_chot)
nguoi = []
for t in tvs:
    k, th, qk, qt = kh_nguoi.get(t['id'], 0), tt_nguoi.get(t['id'], 0), hd_kh.get(t['id'], 0), hd_tt.get(t['id'], 0)
    if not (k or th or qk):
        continue
    dgn = loi.don_gia_ngay_vai_tro(dg, t['vai_tro'])
    if dgn is None:
        add('K02', f'Vai trò {t["vai_tro"]} của {t["ho_ten"]} không có lương tham chiếu trong don_gia.json'); dgn = 0
    nguoi.append({'id': t['id'], 'ho_ten': t['ho_ten'], 'vai_tro': t['vai_tro'], 'ten_vai_tro': dg['luong_tham_chieu_thang'].get(t['vai_tro'], {}).get('ten', t['vai_tro']),
                  'loai': t['loai'], 'md_ke_hoach': round(k, 2), 'md_thuc_te': round(th, 2), 'chenh_lech': round(th - k, 2),
                  'ty_le_chenh': round((th - k) / k, 4) if k else 0, 'md_huy_dong_ke_hoach': round(qk, 2), 'md_huy_dong': round(qt, 2),
                  'md_san_sang': round(qt - th, 2), 'ty_le_su_dung': round(th / qt, 4) if qt else 0,
                  'chi_phi_huy_dong_ke_hoach': qk * dgn * hs, 'chi_phi_huy_dong_thuc_te': qt * dgn * hs,
                  'chi_phi_cong_suc_ke_hoach': k * dgn * hs, 'chi_phi_cong_suc_thuc_te': th * dgn * hs})
md_kh = round(sum(x['md_ke_hoach'] for x in goi), 2); md_th = round(sum(x['md_thuc_te'] for x in goi), 2)
KCP = ('chi_phi_huy_dong_ke_hoach', 'chi_phi_huy_dong_thuc_te', 'chi_phi_cong_suc_ke_hoach', 'chi_phi_cong_suc_thuc_te')
for k in KCP:  # làm tròn từng người sao cho tổng khớp tổng chính xác
    for x, v in zip(nguoi, loi.lam_tron_tong([x[k] for x in nguoi], 0)):
        x[k] = int(v)
T = {k: sum(x[k] for x in nguoi) for k in KCP}
K_LUONG = 'chi_phi_huy_dong' if THEO_HD else 'chi_phi_cong_suc'  # chi phí lương theo cách trả lương
lech_ce = thuc_te.doi_chieu_cost_estimate(cp, {x['id']: x[K_LUONG + '_ke_hoach'] for x in nguoi}, CACH)
if lech_ce:
    add('K13', lech_ce, 'canh_bao')


def tach_khoan_b():
    """(B và D kế hoạch, dự phòng rủi ro, dự phòng đã tách khỏi B hay chưa) theo don_gia.json du_phong_rui_ro."""
    cfg = dg.get('du_phong_rui_ro', {}); b_d = float(cp['B']) + float(cp.get('D', 0) or 0)
    if cfg.get('cach_tinh', 'nam_trong_chi_phi_khac') != 'nam_trong_chi_phi_khac':
        return b_d, float(cp.get('D', 0) or 0), True
    dp, da_tach, loi_dp = thuc_te.du_phong_khoan_b(cfg, cp['B'])  # cùng quy ước với cost estimate: trống là cả B, 0 là không có dự phòng
    if loi_dp:
        add('K19', loi_dp); return b_d, dp, False
    if da_tach:
        return b_d, dp, True
    add('K14', 'don_gia.json du_phong_rui_ro chưa khai báo so_tien: dự phòng rủi ro lấy bằng toàn bộ khoản B (gồm môi trường, công cụ, bảo hành). '
               'Đề nghị nhóm khai báo số tiền dự phòng trong khoản B để tách khỏi chi phí khác', 'canh_bao')
    return b_d, dp, False


b_kh_tong, du_phong_kh, da_tach_dp = tach_khoan_b()
b_kh = b_kh_tong - du_phong_kh if da_tach_dp else b_kh_tong
co_b_tt = bool(cptt)
b_tt = thuc_te.tong_chi_phi_khac(cptt, ngay_chot) if co_b_tt else b_kh_tong
cam_ket = thuc_te.tong_chi_phi_khac(cptt, ngay_chot, 'cam_ket') if co_b_tt else 0
if co_b_tt and not cam_ket:
    add('K15', 'chi_phi_thuc_te.csv chưa có dòng loai cam_ket: nghĩa vụ đã cam kết chưa chi (bảo hành) không được tính, chênh lệch khoản B có thể bị hiểu là tiết kiệm'
        + ('' if co_loai else '. Tệp chưa có cột loai, mọi dòng được coi là đã chi'), 'canh_bao')
gia = float(cp['gia_truoc_thue'])
cp_ns_kh, cp_ns_tt = T[K_LUONG + '_ke_hoach'], T[K_LUONG + '_thuc_te']
tong_kh = cp_ns_kh + b_kh_tong; tong_tt = cp_ns_tt + b_tt + cam_ket
chi_phi = {'BAC_md': md_kh, 'AC_md': md_th, 'chenh_md': round(md_th - md_kh, 2), 'ty_le_chenh_md': round((md_th - md_kh) / md_kh, 4) if md_kh else 0,
           'BAC': td['BAC'], 'AC': td['AC'], 'EV': td['EV'], 'A': cp['A'], 'B_ke_hoach': b_kh, 'B_thuc_te': b_tt, 'chenh_B': round(b_tt - b_kh),
           'co_chi_phi_khac_thuc_te': co_b_tt, 'B_ghi_chu': '' if co_b_tt else ' (chưa có số liệu thực tế, lấy theo kế hoạch)',
           'cam_ket_chua_chi': round(cam_ket), 'du_phong_tach_khoi_B': da_tach_dp, 'cach_tra_luong': CACH,
           'cach_tra_luong_ten': thuc_te.CACH_TRA_LUONG[CACH], 'co_so_luong': thuc_te.CO_SO_LUONG[CACH],
           'chi_phi_huy_dong_ke_hoach': T['chi_phi_huy_dong_ke_hoach'], 'chi_phi_huy_dong_thuc_te': T['chi_phi_huy_dong_thuc_te'],
           'gia_hop_dong_truoc_thue': gia, 'chi_phi_nhan_su_ke_hoach': cp_ns_kh, 'chi_phi_nhan_su_thuc_te': cp_ns_tt, 'chenh_chi_phi_nhan_su': cp_ns_tt - cp_ns_kh,
           'chi_phi_cong_suc_ke_hoach': T['chi_phi_cong_suc_ke_hoach'], 'chi_phi_cong_suc_thuc_te': T['chi_phi_cong_suc_thuc_te'],
           'chi_phi_san_sang_ke_hoach': cp_ns_kh - T['chi_phi_cong_suc_ke_hoach'] if THEO_HD else 0,
           'chi_phi_san_sang_thuc_te': cp_ns_tt - T['chi_phi_cong_suc_thuc_te'] if THEO_HD else 0,
           'md_huy_dong_ke_hoach': round(sum(hd_kh.values()), 2), 'md_huy_dong': round(sum(hd_tt.values()), 2),
           'md_san_sang': round(sum(hd_tt.values()) - md_th, 2), 'ty_le_su_dung_huy_dong': round(md_th / sum(hd_tt.values()), 4) if sum(hd_tt.values()) else 0,
           'he_so_bao_hiem': hs, 'tong_chi_phi_ke_hoach': round(tong_kh), 'tong_chi_phi_thuc_te': round(tong_tt),
           'loi_nhuan_ke_hoach': round(gia - tong_kh), 'loi_nhuan_thuc_te': round(gia - tong_tt),
           'du_phong_ke_hoach': du_phong_kh, 'tong_emv': cp.get('tong_emv_rui_ro', 0), 'cpi_thuc_cuoi': td.get('cpi_thuc'),
           'AC_thuc': td.get('AC_thuc'), 'AC_thuc_nhan_su': td.get('AC_thuc_nhan_su'), 'EV_thuc_nhan_su': td.get('EV_thuc_nhan_su'), 'BAC_thuc': td.get('BAC_thuc')}
chi_phi['ty_suat_loi_nhuan_ke_hoach'] = round(chi_phi['loi_nhuan_ke_hoach'] / gia, 4) if gia else 0
chi_phi['ty_suat_loi_nhuan_thuc_te'] = round(chi_phi['loi_nhuan_thuc_te'] / gia, 4) if gia else 0
T_ = loi.tien
CP_ = chi_phi
if THEO_HD:
    dong_cp = [['Chi phí nhân sự theo ngày huy động (lương ngày vai trò x hệ số bảo hiểm x ngày huy động)', T_(cp_ns_kh), T_(cp_ns_tt), T_(cp_ns_tt - cp_ns_kh)],
               ['Trong đó ngày có ghi công', T_(CP_['chi_phi_cong_suc_ke_hoach']), T_(CP_['chi_phi_cong_suc_thuc_te']),
                T_(CP_['chi_phi_cong_suc_thuc_te'] - CP_['chi_phi_cong_suc_ke_hoach'])],
               ['Trong đó ngày sẵn sàng không ghi công', T_(CP_['chi_phi_san_sang_ke_hoach']), T_(CP_['chi_phi_san_sang_thuc_te']),
                T_(CP_['chi_phi_san_sang_thuc_te'] - CP_['chi_phi_san_sang_ke_hoach'])]]
else:
    dong_cp = [['Chi phí nhân sự theo MD công việc (lương ngày vai trò x hệ số bảo hiểm x MD)', T_(cp_ns_kh), T_(cp_ns_tt), T_(cp_ns_tt - cp_ns_kh)],
               [f'Ngày sẵn sàng không ghi công ({loi.md(CP_["md_huy_dong_ke_hoach"] - md_kh)} MD kế hoạch, {loi.md(CP_["md_san_sang"])} MD thực tế), '
                'không tính lương', '0', '0', '0']]
dong_cp += [['Chi phí khác đã chi (khoản B' + (', không gồm dự phòng rủi ro)' if da_tach_dp else ', gồm dự phòng rủi ro)'), T_(b_kh),
            T_(b_tt) + chi_phi['B_ghi_chu'], T_(b_tt - b_kh)]]
if da_tach_dp:
    dong_cp.append(['Dự phòng rủi ro (tác động thực tế ở mục 6)', T_(du_phong_kh), '', ''])
if cam_ket:
    dong_cp.append(['Nghĩa vụ đã cam kết chưa chi (bảo hành)', '', T_(cam_ket), ''])
dong_cp += [['Tổng chi phí', T_(tong_kh), T_(tong_tt), T_(tong_tt - tong_kh)], ['Giá hợp đồng trước thuế', T_(gia), T_(gia), '0'],
            ['Chênh lệch giá hợp đồng và chi phí', T_(gia - tong_kh), T_(gia - tong_tt), T_(tong_kh - tong_tt)]]
chi_phi['bang'] = {'cot': ['Khoản mục', 'Kế hoạch, đồng', 'Thực tế, đồng', 'Chênh lệch, đồng'], 'dong': dong_cp,
                   'widths': [3700, 1900, 1900, 1800], 'right_cols': [1, 2, 3]}
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
    if c.get('han_quyet_dinh'):  # hạn quyết định do yeu_cau_thay_doi.py ghi theo mức và ngày tiếp nhận
        dung_han = c['trang_thai'] in QD and bool(ngay_qd) and ngay_qd <= c['han_quyet_dinh']
    else:  # CR cũ chưa có hạn quyết định: so số ngày xử lý với thời hạn đánh giá của mức
        dung_han = c['trang_thai'] in QD and so_ngay is not None and so_ngay <= han.get(c['muc'], 3)
    cr.append({'ma': c['ma'], 'tieu_de': c['tieu_de'], 'nguon': c.get('nguon', ''), 'muc': c.get('muc_ten', c['muc']), 'trang_thai': c['trang_thai'],
               'md_tang': c['md_tang'], 'chi_phi_tang': c['chi_phi_tang'], 'ngay_cham': c['ngay_cham'], 'ngay_de_xuat': c['ngay_de_xuat'],
               'ngay_quyet_dinh': ngay_qd, 'han_quyet_dinh': c.get('han_quyet_dinh', ''), 'so_ngay_xu_ly': so_ngay, 'dung_han': dung_han, 'phu_luc_hop_dong': c.get('phu_luc_hop_dong', False)})
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
if not du_phong and tac_dong_tien > 0:
    add('K20', f'Không có dự phòng rủi ro (du_phong_rui_ro.so_tien bằng 0) nhưng tác động thực tế {loi.tien(tac_dong_tien)} đồng, K13 không phản ánh việc vượt dự phòng', 'canh_bao')
if not su_kien:
    add('K10', 'Chưa có nhật ký theo dõi rủi ro (theo_doi_rui_ro.csv), không đánh giá được ứng phó rủi ro', 'canh_bao')

# 8b. Vấn đề tồn đọng (sổ vấn đề tại ngày chốt, do tinh_tien_do.py lập)
vd_th = td.get('van_de_tong_hop') or {'tong': 0, 'so_mo': 0, 'so_qua_han': 0, 'so_dong': 0}
ton_dong = [x for x in td.get('van_de', []) if x['trang_thai'] != 'Đã đóng']
ma_ton = {x['ma'] for x in ton_dong}
hd_ton = [h for h in td.get('hanh_dong', []) if h['ma_van_de'] in ma_ton and h['trang_thai'] not in ('Hoàn thành', 'Hủy')]
van_de = {'tong_hop': vd_th, 'ton_dong': ton_dong, 'hanh_dong_ton_dong': hd_ton,
          'tom_tat': [f'Sổ vấn đề ghi nhận {vd_th["tong"]} vấn đề, đã đóng {vd_th["so_dong"]}, còn mở {vd_th["so_mo"]} '
                      f'(quá hạn {vd_th["so_qua_han"]}) tại ngày {loi.ngay(ngay_chot)}.' if vd_th['tong'] else
                      'Sổ vấn đề không ghi nhận vấn đề nào trong thời gian thực hiện dự án.']}
if ton_dong:
    add('K17', f'Còn {len(ton_dong)} vấn đề chưa đóng khi kết thúc ({", ".join(sorted(ma_ton, key=loi.khoa_ma))}), cần chuyển thành công việc sau dự án', 'canh_bao')

# 9. KPI
do = {'so_ngay_tre_cut_over': tien_do['so_ngay_tre_cut_over'], 'ty_le_moc_dung_han': tien_do['ty_le_moc_dung_han'], 'spi_cuoi': td['spi'],
      'cpi_cuoi': td['cpi'], 'ty_le_chenh_md': abs(chi_phi['ty_le_chenh_md']), 'ty_le_goi_hoan_thanh': pham_vi['ty_le_goi_hoan_thanh'],
      'ty_le_nghiem_thu_dat': nghiem_thu['ty_le_nghiem_thu_dat'], 'ty_le_yeu_cau_rfp_dat': nghiem_thu['ty_le_yeu_cau_rfp_dat'],
      'loi_nghiem_trong_cao_con_mo': loi_['loi_nghiem_trong_cao_con_mo'], 'mat_do_loi': loi_['mat_do_loi'],
      'ty_le_cr_dung_han': thay_doi['ty_le_cr_dung_han'], 'ty_le_rui_ro_co_ung_pho': rui_ro['ty_le_rui_ro_co_ung_pho'],
      'ty_le_dung_du_phong': rui_ro['ty_le_dung_du_phong'], 'ty_le_su_dung_huy_dong': chi_phi['ty_le_su_dung_huy_dong']}
ghi_de = {k['ma']: k for k in loi.doc_json('dau_vao/kpi.json', {'kpi': []}).get('kpi', [])}
kpi = []
for k in kpi_md:
    k = dict(k, **ghi_de.get(k['ma'], {}))
    if k.get('muc_tieu') is None and k.get('muc_tieu_tu'):
        k['muc_tieu'] = da.get(k['muc_tieu_tu'])
    v = do.get(k['do'])
    if k.get('muc_tieu') is None:
        add('K16', f'{k["ma"]} chưa có ngưỡng: khai báo {k.get("muc_tieu_tu") or "muc_tieu"} trong dau_vao/du_an.json hoặc dau_vao/kpi.json', 'canh_bao')
        kq = 'Chưa đủ dữ liệu'
    elif v is None:
        kq = 'Chưa đủ dữ liệu'
    else:
        ok = v >= k['muc_tieu'] if k['so_sanh'] == 'ge' else (v <= k['muc_tieu'] if k['so_sanh'] == 'le' else v == k['muc_tieu'])
        kq = 'Đạt' if ok else 'Không đạt'
    f = (lambda x: loi.pt(x)) if k['don_vi'] == '%' else (lambda x: loi.so(x, 2) if isinstance(x, float) and x != int(x) else loi.so(x))
    kpi.append({'ma': k['ma'], 'nhom': k['nhom'], 'chi_tieu': k['chi_tieu'], 'so_sanh': k['so_sanh'], 'muc_tieu': k['muc_tieu'], 'thuc_te': v,
                'muc_tieu_hien_thi': '' if k['muc_tieu'] is None else ('Tối đa ' if k['so_sanh'] == 'le' else ('Tối thiểu ' if k['so_sanh'] == 'ge' else '')) + f(k['muc_tieu']) + ('' if k['don_vi'] in ('%', '') else ' ' + k['don_vi']),
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
out = {'ngay_chot': ngay_chot.isoformat(), 'ky_cuoi': ky, 'pham_vi': pham_vi, 'tien_do': tien_do, 'chi_phi': chi_phi, 'nhan_luc': nguoi, 'van_de': van_de,
       'nghiem_thu': nghiem_thu, 'loi': loi_, 'thay_doi': thay_doi, 'rui_ro': rui_ro, 'kpi': kpi, 'so_kpi': len(kpi), 'so_kpi_dat': so_dat,
       'ty_le_kpi_dat': ty_le_kpi, 'xep_loai': xep_loai, 'kpi_theo_nhom': theo_nhom_kpi,
       'xep_loai_thang': KPI_CFG['xep_loai'], 'kpi_khong_dat': [k for k in kpi if k['ket_qua'] != 'Đạt'],
       'ngay_dong_du_an': lich.get('ngay_dong_du_an', ''), 'so_lieu_mo_phong': bool(thuc_te.mo_phong()),
       'can_cu_mo_phong': thuc_te.can_cu_mo_phong('báo cáo'),
       'kiem_tra': {'ket_luan': 'dat' if not loi_ds else 'chua_dat', 'phat_hien': F}}
for x in F:
    print(f"[{x['muc_do']}] {x['ma']}: {x['mo_ta']}")
if loi_ds:
    loi.ghi_json('lam_viec/ket_thuc/bao_cao_kiem_tra.json', out['kiem_tra'])
    loi.thoat_loi(f'{len(loi_ds)} lỗi dữ liệu, xem lam_viec/ket_thuc/bao_cao_kiem_tra.json')
loi.ghi_json('du_lieu/ket_thuc.json', out)
loi.hoan_tat_buoc('so_lieu_ket_thuc', 'Tổng hợp số liệu kết thúc dự án', ghi_chu=f'Chốt ngày {ngay_chot.isoformat()}', ket_qua=f'{so_dat}/{len(kpi)} KPI đạt')
print(f'Chốt số liệu ngày {loi.ngay(ngay_chot)}: {len(goi_xong)}/{len(goi)} gói hoàn thành, MD thực tế {loi.md(md_th)}/{loi.md(md_kh)}, '
      f'SPI {loi.so(td["spi"], 2)}, CPI {loi.so(td["cpi"], 2)}, CPI thực {loi.so(td.get("cpi_thuc") or 0, 2)}, '
      f'chi phí nhân sự ({thuc_te.CACH_TRA_LUONG[CACH]}) {loi.tien(cp_ns_tt)} đồng, chênh lệch giá hợp đồng và chi phí {loi.tien(chi_phi["loi_nhuan_thuc_te"])} đồng, '
      f'nghiệm thu đạt {len(dat)}/{len(ds_nt)}, lỗi còn mở {loi_["con_mo"]}, {vd_th["so_mo"]} vấn đề còn mở, '
      f'{len(cr)} yêu cầu thay đổi, {len(xay_ra)} rủi ro đã xảy ra. KPI đạt {so_dat}/{len(kpi)}.')
print('Đã ghi du_lieu/ket_thuc.json. Tiếp theo: python .claude/skills/qlda-loi/scripts/chay.py chuan_bi tong_ket')
