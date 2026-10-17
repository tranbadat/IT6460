"""Tính số liệu báo cáo tiến độ theo phương pháp giá trị thu được (EVM) cho một kỳ.

Dùng: python tinh_tien_do.py --ky S3            (ngày báo cáo là ngày cuối sprint S3)
      python tinh_tien_do.py --ky 2027-04-30 [--ma KT]   (ngày báo cáo bất kỳ, --ma đặt mã kỳ)
Đầu vào: du_lieu/lich.json, du_lieu/wbs.json, dau_vao/don_gia.json, dau_vao/thanh_vien.json,
         dau_vao/thuc_te/nhat_ky_cong_viec.csv (ngay, thanh_vien, ma_goi, md, ghi_chu),
         dau_vao/thuc_te/hoan_thanh.csv (ngay_cap_nhat, ma_goi, phan_tram, ghi_chu),
         dau_vao/thuc_te/moc_thuc_te.csv, dau_vao/thuc_te/theo_doi_rui_ro.csv, du_lieu/rui_ro.json, du_lieu/thay_doi.json (nếu có).
Cách tính:
- BAC theo MD là tổng MD gói lá, theo tiền là MD x đơn giá loại công việc (đường cơ sở chi phí nhân công).
- PV: phần kế hoạch của từng gói tính tuyến tính theo ngày làm việc đã qua trong khoảng bắt đầu, kết thúc của gói.
- EV: MD gói x tỷ lệ hoàn thành mới nhất đến ngày báo cáo. AC: MD thực tế ghi nhận, quy tiền theo đơn giá loại công việc của gói.
- SPI = EV/PV, CPI = EV/AC, EAC = BAC/CPI, ETC = EAC - AC, VAC = BAC - EAC, TCPI = (BAC - EV)/(BAC - AC).
- Dự báo ngày hoàn thành: phần thời lượng kế hoạch còn lại chia SPI, cộng vào ngày báo cáo. Dự báo vượt cut over thì trạng thái chung tối thiểu là vàng.
- Trạng thái theo ngưỡng trong du_an.json: xanh, vàng, đỏ.
Kiểm tra dữ liệu: thành viên, gói, ngày hợp lệ, không quá 1 MD mỗi người mỗi ngày (theo tỷ lệ tham gia), tỷ lệ hoàn thành không giảm.
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
import csv
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('--ky', required=True); ap.add_argument('--ma', help='mã kỳ khi --ky là ngày, ví dụ KT cho kỳ kết thúc')
a = ap.parse_args()
lich = loi.doc_json('du_lieu/lich.json'); wbs = loi.doc_json('du_lieu/wbs.json'); dg = loi.doc_json('dau_vao/don_gia.json')
da = loi.du_an(); tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']; tv = {t['id']: t for t in tvs}
rr = loi.doc_json('du_lieu/rui_ro.json', {'danh_sach': []}); so_td = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})
D = dt.date.fromisoformat
sp = {s['ma']: s for s in lich['sprint']}
if a.ky in sp:
    ngay_bc = D(sp[a.ky]['den']); ky = a.ky
else:
    ngay_bc = D(a.ky); ky = a.ky if not a.ma else a.ma
days = loi.ngay_lam_viec(da)
idx = {d: i for i, d in enumerate(days)}
n_qua = sum(1 for d in days if d <= ngay_bc)
by, la = loi.nut_wbs(wbs)
lg = {x['ma']: x for x in lich['goi']}
rate = {g['ma']: dg['loai_cong_viec'][g['loai']]['don_gia_tron_goi_thang'] / dg['md_moi_mm'] for g in la}
F = []
add = lambda ma, mo, md='loi': F.append({'ma': ma, 'muc_do': md, 'mo_ta': mo})


doc_csv = loi.doc_csv


nk = doc_csv('dau_vao/thuc_te/nhat_ky_cong_viec.csv')
ht = doc_csv('dau_vao/thuc_te/hoan_thanh.csv')
mt = {r['ma_moc']: r for r in doc_csv('dau_vao/thuc_te/moc_thuc_te.csv')}
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
pt = {}
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
tdrr, _ = loi.theo_doi_rui_ro(ngay_bc.isoformat())
ma_rr = {r['ma'] for r in rr['danh_sach']}
for m in tdrr:
    if m not in ma_rr:
        add('T11', f'theo_doi_rui_ro.csv: rủi ro {m} chưa có trong sổ rủi ro, được tính là rủi ro phát sinh ngoài sổ. Bổ sung vào sổ (qlda-risk) nếu cần theo dõi tiếp', 'canh_bao')
    elif tdrr[m].get('trang_thai') not in loi.TRANG_THAI_RUI_RO:
        add('T12', f'theo_doi_rui_ro.csv: trạng thái "{tdrr[m].get("trang_thai")}" của {m} không thuộc {", ".join(loi.TRANG_THAI_RUI_RO)}')
loi_ = [f for f in F if f['muc_do'] == 'loi']
for f in F:
    print(f'[{f["muc_do"]}] {f["ma"]}: {f["mo_ta"]}')
if loi_:
    sys.exit(1)


def pv_frac(g):
    l = lg[g['ma']]
    a_, b_ = D(l['bat_dau']), D(l['ket_thuc'])
    tot = sum(1 for d in days if a_ <= d <= b_) or 1
    qua = sum(1 for d in days if a_ <= d <= min(b_, ngay_bc))
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


def mau(v, vang, do):
    return 'Đỏ' if v < do else ('Vàng' if v < vang else 'Xanh')


tt_spi = mau(spi, ng.get('spi_vang', 0.95), ng.get('spi_do', 0.85)); tt_cpi = mau(cpi, ng.get('cpi_vang', 0.95), ng.get('cpi_do', 0.85))
tong = 'Đỏ' if 'Đỏ' in (tt_spi, tt_cpi) else ('Vàng' if 'Vàng' in (tt_spi, tt_cpi) else 'Xanh')
# Dự báo theo SPI: thời lượng còn lại của kế hoạch kéo dài theo 1/SPI
kt_kh = dt.date.fromisoformat(lich['ket_thuc_du_kien'])
idx_kt = max(i for i, d in enumerate(days) if d <= kt_kh) if any(d <= kt_kh for d in days) else len(days) - 1
du_bao_idx = n_qua - 1 + int(round(max(0, idx_kt - (n_qua - 1)) / spi)) if spi else idx_kt
ext = list(days)
while len(ext) <= du_bao_idx:
    ext.append(ext[-1] + dt.timedelta(days=1 if ext[-1].weekday() < 4 else 3))
du_bao = ext[max(0, du_bao_idx)]
if du_bao.isoformat() > lich['cut_over'] and tong == 'Xanh':
    tong = 'Vàng'  # chỉ số đạt ngưỡng nhưng dự báo vượt cut over
moc = []
for m in lich['moc']:
    tt = mt.get(m['ma'], {})
    thuc = tt.get('ngay_dat', '')
    moc.append({'ma': m['ma'], 'ten': m['ten'], 'ke_hoach': m['ngay'], 'thuc_te': thuc,
                'trang_thai': ('Đạt, ' + ('đúng hạn' if thuc <= m['ngay'] else 'trễ')) if thuc else ('Chưa đến hạn' if m['ngay'] > ngay_bc.isoformat() else 'Quá hạn chưa đạt')})
# công sức theo thành viên
nguoi = []
for t in tvs:
    kh = sum(r['md'] * (min(1, max(0, (sum(1 for d in days if D(sp[r['sprint']]['tu']) <= d <= min(D(sp[r['sprint']]['den']), ngay_bc))) /
                                         max(1, sp[r['sprint']]['so_ngay'])))) for r in lich['phan_bo'] if r['thanh_vien'] == t['id'])
    th = sum(float(r['md']) for r in nk if r['thanh_vien'] == t['id'] and D(r['ngay']) <= ngay_bc)
    if kh or th:
        nguoi.append({'ho_ten': t['ho_ten'], 'ke_hoach': round(kh, 2), 'thuc_te': round(th, 2), 'chenh_lech': round(th - kh, 2)})
rui_ro = []
for r in rr['danh_sach']:
    t = tdrr.get(r['ma'], {}); tt = t.get('trang_thai', 'Đang theo dõi')
    if r['muc'] == 'cao' or tt not in ('Đang theo dõi',):
        rui_ro.append({'ma': r['ma'], 'ten': r['ten'], 'muc': r.get('muc_ten', r['muc']), 'trang_thai': tt, 'hanh_dong': t.get('hanh_dong', ''),
                       'phu_trach': r.get('ho_ten_phu_trach', '')})
cr = [{'ma': c['ma'], 'tieu_de': c['tieu_de'], 'trang_thai': c['trang_thai'], 'md_tang': c['md_tang'], 'ngay_cham': c['ngay_cham']} for c in so_td['yeu_cau']
      if c['ngay_de_xuat'] <= ngay_bc.isoformat()]
out = {'ky': ky, 'ngay_bao_cao': ngay_bc.isoformat(), 'so_ngay_da_qua': n_qua, 'so_ngay_lam_viec': len(days), 'ty_le_thoi_gian': round(n_qua / len(days), 4),
       'BAC_md': BAC, 'PV_md': round(PV, 2), 'EV_md': round(EV, 2), 'AC_md': round(AC, 2), 'SV_md': round(EV - PV, 2), 'CV_md': round(EV - AC, 2),
       'BAC': round(BACv), 'PV': round(PVv), 'EV': round(EVv), 'AC': round(ACv), 'SV': round(EVv - PVv), 'CV': round(EVv - ACv),
       'spi': round(spi, 3), 'cpi': round(cpi, 3), 'EAC_md': round(eac, 2), 'ETC_md': round(eac - AC, 2), 'VAC_md': round(BAC - eac, 2), 'EAC': round(eacv), 'tcpi': round(tcpi, 3),
       'ty_le_hoan_thanh': round(EV / BAC, 4), 'du_bao_hoan_thanh': du_bao.isoformat(), 'ket_thuc_ke_hoach': lich['ket_thuc_du_kien'], 'cut_over': lich['cut_over'],
       'tre_so_voi_cut_over': du_bao.isoformat() > lich['cut_over'],
       'trang_thai_spi': tt_spi, 'trang_thai_cpi': tt_cpi, 'trang_thai_chung': tong, 'goi': goi, 'goi_cham': [x for x in goi if x['trang_thai'] == 'Chậm'],
       'so_goi_cham': sum(1 for x in goi if x['trang_thai'] == 'Chậm'), 'moc': moc, 'nguoi': nguoi, 'rui_ro': rui_ro, 'thay_doi': cr, 'so_thay_doi': len(cr),
       'canh_bao_du_lieu': F}
os.makedirs(loi.duong_dan('du_lieu/tien_do'), exist_ok=True)
loi.ghi_json(f'du_lieu/tien_do/{ky}.json', out)
loi.ghi_json('du_lieu/tien_do/hien_tai.json', out)
ls = loi.doc_json('du_lieu/tien_do/lich_su.json', {'ky': []})
ls['ky'] = [x for x in ls['ky'] if x['ky'] != ky] + [{k: out[k] for k in ('ky', 'ngay_bao_cao', 'PV_md', 'EV_md', 'AC_md', 'spi', 'cpi', 'trang_thai_chung')}]
ls['ky'].sort(key=lambda x: x['ngay_bao_cao'])
loi.ghi_json('du_lieu/tien_do/lich_su.json', ls)
print(f'Kỳ {ky} ({loi.ngay(ngay_bc)}): PV {PV:.1f}, EV {EV:.1f}, AC {AC:.1f} MD. SPI {spi:.2f} ({tt_spi}), CPI {cpi:.2f} ({tt_cpi}). '
      f'Dự báo hoàn thành {loi.ngay(du_bao)}. {out["so_goi_cham"]} gói chậm.')
loi.ghi_nhat_ky('qlda-bao-cao-tien-do', f'tien_do.{ky}.tinh', 'script', f'Tính EVM kỳ {ky}: SPI {spi:.2f}, CPI {cpi:.2f}',
                vao=['dau_vao/thuc_te/nhat_ky_cong_viec.csv', 'dau_vao/thuc_te/hoan_thanh.csv', 'du_lieu/lich.json'], ra=[f'du_lieu/tien_do/{ky}.json'], ket_qua=tong)
