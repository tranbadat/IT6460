"""Lập bảng phân chia lương theo công sức thực tế: lương = MD thực tế x đơn giá ngày của vai trò.

Dùng: python chia_luong.py [--den yyyy-mm-dd]
  --den  tính đến ngày, mặc định toàn bộ nhật ký.
Đầu vào: dau_vao/thuc_te/nhat_ky_cong_viec.csv, dau_vao/thanh_vien.json, dau_vao/don_gia.json (luong_tham_chieu_thang,
         ngay_lam_viec_moi_thang, he_so_bao_hiem), du_lieu/lich.json (sprint, MD kế hoạch theo người), du_lieu/chi_phi.json (A), dau_vao/du_an.json.
Cách tính:
- Đơn giá ngày của vai trò = lương tham chiếu tháng / số ngày làm việc mỗi tháng.
- Lương của thành viên = tổng MD thực tế trong nhật ký x đơn giá ngày vai trò. Chi phí doanh nghiệp = lương x hệ số bảo hiểm.
- Tỷ trọng = lương của thành viên / tổng lương. Đối chiếu với MD kế hoạch (master schedule) và với khoản A của cost estimate.
Kiểm tra dữ liệu (lỗi chặn): L01 thành viên không có trong danh sách, L02 vai trò không có đơn giá, L04 vượt tỷ lệ tham gia trong ngày,
  L05 MD không hợp lệ. Cảnh báo: L03 ngày ngoài lịch dự án, L06 ngày nghỉ, L07 ghi công ngoài thời gian huy động.
Ra: du_lieu/luong.json, ket_qua/14_Bang_phan_chia_luong/Bang_phan_chia_luong.xlsx (công thức SUMIFS, INDEX/MATCH, đã tính lại và đối chiếu).
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
import sys

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import PatternFill

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402
import xlsx_chung as X  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('--den'); a = ap.parse_args()
D = dt.date.fromisoformat
da = loi.du_an(); dg = loi.doc_json('dau_vao/don_gia.json'); lich = loi.doc_json('du_lieu/lich.json')
cp = loi.doc_json('du_lieu/chi_phi.json', {}); tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']; tv = {t['id']: t for t in tvs}
nk = loi.doc_csv('dau_vao/thuc_te/nhat_ky_cong_viec.csv')
if not nk:
    loi.thoat_loi('Chưa có nhật ký công việc thực tế (dau_vao/thuc_te/nhat_ky_cong_viec.csv), xem qlda-bao-cao-tien-do/references/nhap_lieu.md.')
sai_ngay = []
for i, r in enumerate(nk, 2):
    try:
        D(r['ngay'])
    except (ValueError, KeyError):
        sai_ngay.append(f'dòng {i}: "{r.get("ngay")}"')
if sai_ngay:
    loi.thoat_loi('nhat_ky_cong_viec.csv có ngày không đúng dạng yyyy-mm-dd: ' + ', '.join(sai_ngay[:10]))
den = D(a.den) if a.den else max(D(r['ngay']) for r in nk)
nk = [r for r in nk if D(r['ngay']) <= den]
F = []
add = lambda ma, mo, md='loi': F.append({'ma': ma, 'muc_do': md, 'mo_ta': mo})
days = set(loi.ngay_lam_viec(da)); nghi = set(da.get('ngay_nghi', []))
sp = lich['sprint']
sp_idx = {s['ma']: i for i, s in enumerate(sp, 1)}


def sprint_cua(d):
    for s in sp:
        if D(s['tu']) <= d <= D(s['den']):
            return s['ma']
    return ''


ngay_tv = {}
for i, r in enumerate(nk, 2):
    p = r['thanh_vien']
    try:
        v = float(r['md'])
        if v <= 0 or v > 1:
            raise ValueError
    except ValueError:
        add('L05', f'Dòng {i}: MD "{r["md"]}" không hợp lệ, ghi số trong khoảng (0, 1]'); continue
    if p not in tv:
        add('L01', f'Dòng {i}: thành viên "{p}" không có trong thanh_vien.json'); continue
    d = D(r['ngay'])
    if d.isoformat() in nghi or d.weekday() >= 5:
        add('L06', f'Dòng {i}: {tv[p]["ho_ten"]} ghi công ngày nghỉ {loi.ngay(d)}', 'canh_bao')
    elif d not in days:
        add('L03', f'Dòng {i}: ngày {loi.ngay(d)} ngoài lịch dự án', 'canh_bao')
    s = sprint_cua(d); t = tv[p]
    if s and ((t.get('tu_sprint') and sp_idx[s] < int(t['tu_sprint'])) or (t.get('den_sprint') and sp_idx[s] > int(t['den_sprint']))):
        add('L07', f'Dòng {i}: {t["ho_ten"]} ghi công sprint {s}, ngoài thời gian huy động', 'canh_bao')
    ngay_tv[(p, d)] = ngay_tv.get((p, d), 0) + v
for (p, d), v in ngay_tv.items():
    if v > float(tv[p].get('ty_le', 1)) + 1e-6:
        add('L04', f'{tv[p]["ho_ten"]} ghi {loi.so(v, 2)} MD ngày {loi.ngay(d)}, vượt tỷ lệ tham gia {loi.pt(float(tv[p].get("ty_le", 1)), 0)}')
vai = sorted({tv[r['thanh_vien']]['vai_tro'] for r in nk if r['thanh_vien'] in tv})
for v in vai:
    if loi.don_gia_ngay_vai_tro(dg, v) is None:
        add('L02', f'Vai trò {v} chưa có lương tham chiếu trong don_gia.json')
loi_ = [f for f in F if f['muc_do'] == 'loi']
for f in F:
    print(f"[{f['muc_do']}] {f['ma']}: {f['mo_ta']}")
if loi_:
    loi.ghi_json('lam_viec/bang_luong/bao_cao_kiem_tra.json', {'ket_luan': 'chua_dat', 'phat_hien': F})
    loi.thoat_loi(f'{len(loi_)} lỗi dữ liệu nhật ký, sửa rồi chạy lại.')

# Tính bằng Python (đối chiếu với Excel)
hs = float(dg.get('he_so_bao_hiem', 1.0)); nlv = float(dg.get('ngay_lam_viec_moi_thang', 22))
dgn = {v: dg['luong_tham_chieu_thang'][v]['luong'] / nlv for v in dg['luong_tham_chieu_thang']}
kh = {}
for x in lich['phan_bo']:
    kh[x['thanh_vien']] = kh.get(x['thanh_vien'], 0) + float(x['md'])
md_tt = {}; md_sp = {}
for r in nk:
    if r['thanh_vien'] in tv:
        md_tt[r['thanh_vien']] = md_tt.get(r['thanh_vien'], 0) + float(r['md'])
        k = (r['thanh_vien'], sprint_cua(D(r['ngay'])))
        md_sp[k] = md_sp.get(k, 0) + float(r['md'])
nguoi = []
for t in tvs:
    if not kh.get(t['id']) and not md_tt.get(t['id']):
        continue
    m = md_tt.get(t['id'], 0); g = dgn[t['vai_tro']]
    nguoi.append({'id': t['id'], 'ho_ten': t['ho_ten'], 'loai': 'Thành viên nhóm' if t['loai'] == 'nhom' else 'Vị trí bổ sung', 'vai_tro': t['vai_tro'],
                  'ten_vai_tro': dg['luong_tham_chieu_thang'][t['vai_tro']]['ten'], 'md_ke_hoach': round(kh.get(t['id'], 0), 2), 'md_thuc_te': round(m, 2),
                  'chenh_lech_md': round(m - kh.get(t['id'], 0), 2), 'don_gia_ngay': round(g), 'luong': m * g, 'bao_hiem': m * g * (hs - 1),
                  'chi_phi': m * g * hs, 'luong_ke_hoach': kh.get(t['id'], 0) * g,
                  'theo_sprint': [{'sprint': s['ma'], 'md': round(md_sp.get((t['id'], s['ma']), 0), 2)} for s in sp]})
tong_luong = sum(x['luong'] for x in nguoi)
for x in nguoi:
    x['ty_trong'] = round(x['luong'] / tong_luong, 4) if tong_luong else 0
    for k in ('luong', 'bao_hiem', 'chi_phi', 'luong_ke_hoach'):
        x[k] = round(x[k])
tong = {'md_ke_hoach': round(sum(x['md_ke_hoach'] for x in nguoi), 2), 'md_thuc_te': round(sum(md_tt.values()), 2),
        'luong': round(tong_luong), 'bao_hiem': round(tong_luong * (hs - 1)), 'chi_phi': round(tong_luong * hs),
        'luong_ke_hoach': round(sum(kh.get(x['id'], 0) * dgn[x['vai_tro']] for x in nguoi))}
A = float(cp.get('A', 0))
doi_chieu = {'A': A, 'ty_le_chi_phi_tren_A': round(tong['chi_phi'] / A, 4) if A else 0, 'chi_phi_ke_hoach': round(tong['luong_ke_hoach'] * hs),
             'chenh_chi_phi': round(tong['chi_phi'] - tong['luong_ke_hoach'] * hs), 'he_so_bao_hiem': hs, 'ngay_lam_viec_moi_thang': nlv}
theo_sprint = [{'sprint': s['ma'], 'tu': s['tu'], 'den': s['den'], 'md': round(sum(md_sp.get((x['id'], s['ma']), 0) for x in nguoi), 2),
                'luong': round(sum(md_sp.get((x['id'], s['ma']), 0) * dgn[x['vai_tro']] for x in nguoi))} for s in sp]

# Excel
OUT_DIR = loi.duong_dan('ket_qua/14_Bang_phan_chia_luong'); os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'Bang_phan_chia_luong.xlsx')
wb = Workbook()
wb.properties.creator = wb.properties.lastModifiedBy = loi.du_an().get('nguoi_lap', '')
tm = wb.active; tm.title = 'Thuyet_minh'
dong = [('Bảng phân chia lương', X.F_TEN), (da['ten_du_an'], None), (f'Nhóm {da.get("ma_nhom", "")}, {da.get("don_vi_thuc_hien", "")}', None),
        (f'Số liệu tính đến ngày {loi.ngay(den)}', None), ('', None),
        ('Căn cứ', X.F_TIEU_DE),
        ('1. Công sức thực tế theo nhật ký công việc (sheet Nhat_ky), mỗi dòng là MD của một thành viên cho một gói WBS trong một ngày.', None),
        ('2. Đơn giá ngày của vai trò bằng lương tham chiếu tháng chia số ngày làm việc mỗi tháng (sheet Tham_so).', None),
        ('3. Lương của thành viên bằng MD thực tế nhân đơn giá ngày của vai trò. Chi phí doanh nghiệp gồm lương và phần bảo hiểm theo hệ số.', None),
        ('4. Tỷ trọng là tỷ lệ lương của thành viên trên tổng lương. Bảng đối chiếu MD kế hoạch theo master schedule và khoản A của cost estimate.', None),
        ('', None), ('Ký hiệu', X.F_TIEU_DE), ('Chữ xanh dương: số liệu nhập. Chữ xanh lá: tham chiếu sheet khác. Chữ đen: công thức.', None),
        ('', None), ('Xác nhận', X.F_TIEU_DE), ('Thành viên ký xác nhận tại cột cuối của sheet Bang_luong.', None),
        (f'Người lập: {da.get("nguoi_lap", "")}', None)]
for i, (t, f) in enumerate(dong, 1):
    c = tm.cell(row=i, column=1, value=t); c.font = f or X.F_THUONG
tm.column_dimensions['A'].width = 120

ts = wb.create_sheet('Tham_so')
X.tieu_de(ts, 1, ['Vai trò', 'Tên vai trò', 'Lương tham chiếu tháng, đồng', 'Đơn giá ngày, đồng'], [12, 34, 22, 20])
vt = list(dg['luong_tham_chieu_thang'].items())
nv = len(vt) + 1
for i, (k, v) in enumerate(vt, 2):
    X.o(ts, i, 1, k, nhap=True); X.o(ts, i, 2, v['ten'], nhap=True); X.o(ts, i, 3, v['luong'], fmt=X.SO, nhap=True)
    X.o(ts, i, 4, f'=C{i}/$B${nv + 3}', fmt=X.SO)
X.o(ts, nv + 2, 1, 'Hệ số bảo hiểm', dam=True); X.o(ts, nv + 2, 2, hs, fmt='0.000', nhap=True)
X.o(ts, nv + 3, 1, 'Ngày làm việc mỗi tháng', dam=True); X.o(ts, nv + 3, 2, nlv, fmt='0', nhap=True)
X.ghi_chu_bang(ts, nv + 5, 'Nguồn lương tham chiếu: ' + str(dg.get('nguon_luong', '')))
X.ghi_chu_bang(ts, nv + 6, 'Nguồn hệ số bảo hiểm: ' + str(dg.get('nguon_he_so_bao_hiem', '')))
HS = f'Tham_so!$B${nv + 2}'

ss = wb.create_sheet('Sprint')
X.tieu_de(ss, 1, ['Sprint', 'Từ ngày', 'Đến ngày'], [10, 14, 14])
for i, s in enumerate(sp, 2):
    X.o(ss, i, 1, s['ma'], nhap=True); X.o(ss, i, 2, D(s['tu']), fmt=X.NGAY, nhap=True); X.o(ss, i, 3, D(s['den']), fmt=X.NGAY, nhap=True)
ns = len(sp) + 1

nks = wb.create_sheet('Nhat_ky')
X.tieu_de(nks, 1, ['Ngày', 'Sprint', 'Mã thành viên', 'Mã gói WBS', 'MD', 'Ghi chú'], [12, 9, 14, 12, 8, 40])
for i, r in enumerate(sorted(nk, key=lambda r: (r['ngay'], r['thanh_vien'], r['ma_goi'])), 2):
    X.o(nks, i, 1, D(r['ngay']), fmt=X.NGAY, nhap=True)
    X.o(nks, i, 2, f'=IFERROR(INDEX(Sprint!$A$2:$A${ns},MATCH(A{i},Sprint!$B$2:$B${ns},1)),"")', lien_ket=True)
    X.o(nks, i, 3, r['thanh_vien'], nhap=True); X.o(nks, i, 4, r['ma_goi'], nhap=True)
    X.o(nks, i, 5, float(r['md']), fmt=X.SO2, nhap=True); X.o(nks, i, 6, r.get('ghi_chu', ''), nhap=True)
nn = len(nk) + 1

bl = wb.create_sheet('Bang_luong', 1)
X.tieu_de(bl, 1, ['STT', 'Mã thành viên', 'Họ tên', 'Loại', 'Vai trò', 'MD kế hoạch', 'MD thực tế', 'Chênh lệch MD', 'Đơn giá ngày, đồng',
                  'Lương, đồng', 'Bảo hiểm phần doanh nghiệp, đồng', 'Chi phí doanh nghiệp, đồng', 'Tỷ trọng lương', 'Ký xác nhận'],
          [5, 13, 24, 15, 11, 11, 11, 11, 15, 16, 18, 18, 10, 16])
r0 = 2; rl = r0 + len(nguoi) - 1; rt = rl + 1
for i, x in enumerate(nguoi):
    r = r0 + i
    X.o(bl, r, 1, i + 1); X.o(bl, r, 2, x['id'], nhap=True); X.o(bl, r, 3, x['ho_ten'], nhap=True); X.o(bl, r, 4, x['loai'], nhap=True)
    X.o(bl, r, 5, x['vai_tro'], nhap=True); X.o(bl, r, 6, x['md_ke_hoach'], fmt=X.SO2, nhap=True)
    X.o(bl, r, 7, f'=SUMIFS(Nhat_ky!$E$2:$E${nn},Nhat_ky!$C$2:$C${nn},B{r})', fmt=X.SO2, lien_ket=True)
    X.o(bl, r, 8, f'=G{r}-F{r}', fmt=X.SO2)
    X.o(bl, r, 9, f'=INDEX(Tham_so!$D$2:$D${nv},MATCH(E{r},Tham_so!$A$2:$A${nv},0))', fmt=X.SO, lien_ket=True)
    X.o(bl, r, 10, f'=G{r}*I{r}', fmt=X.SO); X.o(bl, r, 11, f'=J{r}*({HS}-1)', fmt=X.SO); X.o(bl, r, 12, f'=J{r}+K{r}', fmt=X.SO)
    X.o(bl, r, 13, f'=IF($J${rt}=0,0,J{r}/$J${rt})', fmt=X.PT); X.o(bl, r, 14, '')
X.o(bl, rt, 3, 'Tổng cộng', dam=True)
for c in (6, 7, 8, 10, 11, 12, 13):
    L = 'ABCDEFGHIJKLMN'[c - 1]
    X.o(bl, rt, c, f'=SUM({L}{r0}:{L}{rl})', fmt=X.PT if c == 13 else (X.SO2 if c in (6, 7, 8) else X.SO), dam=True)
bl.conditional_formatting.add(f'H{r0}:H{rl}', FormulaRule(formula=[f'ABS(H{r0})>0.1*F{r0}'], fill=PatternFill('solid', fgColor='FCE4D6')))
X.ghi_chu_bang(bl, rt + 2, 'Ô chênh lệch tô màu khi MD thực tế lệch quá 10% so với kế hoạch.')

tsp = wb.create_sheet('Theo_sprint', 2)
hdr = ['Mã thành viên', 'Họ tên'] + [f'MD {s["ma"]}' for s in sp] + ['Tổng MD'] + [f'Lương {s["ma"]}' for s in sp] + ['Tổng lương']
X.tieu_de(tsp, 1, hdr, [13, 24] + [9] * len(sp) + [10] + [14] * len(sp) + [16])
from openpyxl.utils import get_column_letter as CL  # noqa: E402
for i, x in enumerate(nguoi):
    r = 2 + i
    X.o(tsp, r, 1, x['id'], nhap=True); X.o(tsp, r, 2, x['ho_ten'], nhap=True)
    for j, s in enumerate(sp):
        X.o(tsp, r, 3 + j, f'=SUMIFS(Nhat_ky!$E$2:$E${nn},Nhat_ky!$C$2:$C${nn},$A{r},Nhat_ky!$B$2:$B${nn},"{s["ma"]}")', fmt=X.SO2, lien_ket=True)
    ct = 3 + len(sp)
    X.o(tsp, r, ct, f'=SUM({CL(3)}{r}:{CL(ct - 1)}{r})', fmt=X.SO2)
    for j, s in enumerate(sp):
        X.o(tsp, r, ct + 1 + j, f'={CL(3 + j)}{r}*INDEX(Bang_luong!$I${r0}:$I${rl},MATCH($A{r},Bang_luong!$B${r0}:$B${rl},0))', fmt=X.SO)
    X.o(tsp, r, ct + 1 + len(sp), f'=SUM({CL(ct + 1)}{r}:{CL(ct + len(sp))}{r})', fmt=X.SO)
rtt = 2 + len(nguoi)
X.o(tsp, rtt, 2, 'Tổng cộng', dam=True)
for c in range(3, len(hdr) + 1):
    X.o(tsp, rtt, c, f'=SUM({CL(c)}2:{CL(c)}{rtt - 1})', fmt=X.SO2 if c <= 3 + len(sp) else X.SO, dam=True)

dc = wb.create_sheet('Doi_chieu', 3)
X.tieu_de(dc, 1, ['Chỉ tiêu', 'Giá trị', 'Ghi chú'], [52, 20, 60])
rows = [('Khoản A của cost estimate (chi phí nhân công theo đơn giá trọn gói), đồng', A, 'du_lieu/chi_phi.json', True),
        ('Tổng MD kế hoạch (master schedule)', f'=Bang_luong!F{rt}', '', False),
        ('Tổng MD thực tế (nhật ký)', f'=Bang_luong!G{rt}', '', False),
        ('Tổng lương theo MD thực tế, đồng', f'=Bang_luong!J{rt}', '', False),
        ('Chi phí doanh nghiệp theo MD thực tế, đồng', f'=Bang_luong!L{rt}', 'Lương nhân hệ số bảo hiểm', False),
        ('Chi phí doanh nghiệp theo MD kế hoạch, đồng', f'=SUMPRODUCT(Bang_luong!F{r0}:F{rl},Bang_luong!I{r0}:I{rl})*{HS}', '', False),
        ('Chênh lệch thực tế so với kế hoạch, đồng', '=B6-B7', 'Âm là thấp hơn kế hoạch', False),
        ('Tỷ lệ chi phí doanh nghiệp thực tế trên khoản A', '=IF(B2=0,0,B6/B2)', 'Phần còn lại của A bù chi phí quản lý và lợi nhuận', False)]
for i, (t, v, g, nh) in enumerate(rows, 2):
    X.o(dc, i, 1, t); X.o(dc, i, 2, v, fmt=X.PT if i == 9 else (X.SO2 if i in (3, 4) else X.SO), nhap=nh, lien_ket=not nh); X.o(dc, i, 3, g)
wb.save(OUT)

kq = X.tinh_lai(OUT)
ghi = 'Máy không có LibreOffice, Excel tự tính khi mở.'
if kq and kq.get('status'):
    lc = X.dem_loi_cong_thuc(OUT)
    if lc:
        loi.thoat_loi('Công thức lỗi: ' + ', '.join(lc[:10]))
    v = X.doc_gia_tri(OUT)
    so_ = [('tổng MD thực tế', v['Bang_luong'][f'G{rt}'].value, tong['md_thuc_te']), ('tổng lương', v['Bang_luong'][f'J{rt}'].value, tong['luong']),
           ('chi phí doanh nghiệp', v['Bang_luong'][f'L{rt}'].value, tong['chi_phi']),
           ('tổng lương theo sprint', v['Theo_sprint'].cell(row=rtt, column=len(hdr)).value, tong['luong']),
           ('tổng MD theo sprint', v['Theo_sprint'].cell(row=rtt, column=3 + len(sp)).value, tong['md_thuc_te'])]
    for ten, a_, b_ in so_:
        if a_ is None or abs(float(a_) - float(b_)) > 2:
            loi.thoat_loi(f'Đối chiếu Excel và Python lệch ở {ten}: {a_} khác {b_}. Kiểm tra ngày nhật ký nằm trong sprint.')
    for x in nguoi:
        r = r0 + nguoi.index(x)
        if abs(float(v['Bang_luong'][f'J{r}'].value) - x['luong']) > 2:
            loi.thoat_loi(f'Đối chiếu lương của {x["ho_ten"]} lệch giữa Excel và Python')
    ghi = 'Đã tính lại công thức, 0 lỗi, giá trị Excel khớp tính toán Python (MD, lương từng người, tổng theo sprint).'

out = {'den': den.isoformat(), 'nguoi': nguoi, 'tong': tong, 'doi_chieu': doi_chieu, 'theo_sprint': theo_sprint,
       'don_gia': [{'vai_tro': k, 'ten': v['ten'], 'luong_thang': v['luong'], 'don_gia_ngay': round(dgn[k])} for k, v in vt],
       'kiem_tra': {'ket_luan': 'dat', 'phat_hien': F, 'doi_chieu_excel': ghi}}
loi.ghi_json('du_lieu/luong.json', out)
print(f'Đến {loi.ngay(den)}: {len(nguoi)} người, {loi.md(tong["md_thuc_te"])} MD thực tế, tổng lương {loi.trieu(tong["luong"])} triệu, '
      f'chi phí doanh nghiệp {loi.trieu(tong["chi_phi"])} triệu ({loi.pt(doi_chieu["ty_le_chi_phi_tren_A"])} khoản A). {ghi}')
pbs = loi.hoan_tat_buoc('bang_luong', 'Lập bảng phân chia lương theo MD thực tế. ' + ghi,
                        hash_tep={'ket_qua/14_Bang_phan_chia_luong/Bang_phan_chia_luong.xlsx': loi.bam_obj(out)})
for k, v in pbs.items():
    print(f'  {k}: phiên bản {v}')
