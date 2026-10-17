"""Xuất master schedule dạng Excel (Gantt theo tuần, sprint, mốc, tải nguồn lực) từ du_lieu/lich.json.

Dùng: python xuat_gantt.py
Quy ước: chữ xanh dương là dữ liệu do lap_lich.py tính (không sửa tay, sửa dữ liệu đầu vào rồi chạy lại),
chữ đen là công thức. Mục cha WBS, tổng sprint, tải nguồn lực, số ngày làm việc đều là công thức.
Sau khi tạo: tính lại công thức (nếu máy có LibreOffice), đối chiếu giá trị Excel với lich.json, đăng ký phiên bản.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import datetime as dt
import os
import sys

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import PatternFill, Alignment, Font
from openpyxl.utils import get_column_letter as L

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402
import xlsx_chung as X  # noqa: E402

lich = loi.doc_json('du_lieu/lich.json')
da = loi.du_an()
wbs = loi.doc_json('du_lieu/wbs.json')
OUT = loi.duong_dan('ket_qua/04_Master_schedule/Master_schedule.xlsx')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
D = lambda s: dt.date.fromisoformat(s)
wb = Workbook()
wb.properties.creator = wb.properties.lastModifiedBy = loi.du_an().get('nguoi_lap', '')

# ---------------- Tong_quan
ws = wb.active; ws.title = 'Tong_quan'
ws['A1'] = 'Master schedule'; ws['A1'].font = X.F_TEN
ws['A2'] = da['ten_du_an']; ws['A2'].font = X.F_THUONG
info = [('Ngày bắt đầu', D(lich['ngay_bat_dau']), X.NGAY, True), ('Ngày cut over', D(lich['cut_over']), X.NGAY, True),
        ('Số ngày làm việc', '=NETWORKDAYS(B4,B5,$F$4:$F$40)', '0', False), ('Tổng khối lượng, MD', "=SUMIFS(Lich_trinh!D:D,Lich_trinh!C:C,1)", X.SO2, False),
        ('Quỹ thời gian, MD', '=SUM(Phan_bo!E:E)', X.SO2, False), ('Tỷ lệ sử dụng quỹ', '=IF(B8=0,0,B7/B8)', X.PT, False),
        ('Kết thúc dự kiến (không tính gói dàn trải)', D(lich['ket_thuc_du_kien']), X.NGAY, True),
        ('Dự trữ đến cut over, ngày làm việc (trước các gói gắn ngày cố định)', lich['du_tru_den_cut_over_ngay'], '0', True),
        ('Số sprint', '=COUNTIFS(Sprint!A:A,"S*",Sprint!A:A,"<>Sprint")', '0', False), ('Đường găng theo phụ thuộc, ngày', lich['do_dai_gang_ngay'], '0', True)]
for i, (k, v, f, nhap) in enumerate(info, 4):
    X.o(ws, i, 1, k)
    X.o(ws, i, 2, v, fmt=f, nhap=nhap)
X.o(ws, 3, 6, 'Ngày nghỉ', dam=True)
for i, h in enumerate(lich['ngay_nghi'], 4):
    X.o(ws, i, 6, D(h), fmt=X.NGAY, nhap=True)
ws.column_dimensions['A'].width = 36; ws.column_dimensions['B'].width = 16; ws.column_dimensions['F'].width = 14
X.ghi_chu_bang(ws, 16, 'Chữ xanh dương: dữ liệu do bước lập lịch tính từ WBS, giao việc và lịch làm việc. Chữ đen: công thức. '
                       'Không sửa tay dữ liệu xanh dương. Khi cần thay đổi, sửa đầu vào (WBS, giao việc, mốc) và lập lại lịch.')

# ---------------- Lich_trinh
lt = wb.create_sheet('Lich_trinh')
cols = ['Mã WBS', 'Tên công việc', 'Mức', 'MD', 'Người thực hiện', 'Bắt đầu', 'Kết thúc', 'Số ngày làm việc', 'Sprint bắt đầu', 'Sprint kết thúc',
        'Phụ thuộc', 'Đường găng', 'Mục cha']
widths = [9, 46, 5, 8, 24, 11, 11, 10, 8, 8, 14, 7, 8]
d0 = D(lich['ngay_bat_dau']); d1 = D(lich['cut_over'])
w0 = d0 - dt.timedelta(days=d0.weekday())
tuan = []
while w0 <= d1:
    tuan.append(w0); w0 += dt.timedelta(days=7)
lt['A1'] = 'Lịch trình theo WBS'; lt['A1'].font = X.F_TEN
X.tieu_de(lt, 4, cols + [f'T{i + 1}' for i in range(len(tuan))], widths + [4.2] * len(tuan))
C0 = len(cols) + 1
for j, w in enumerate(tuan):
    c = lt.cell(row=3, column=C0 + j, value=w); c.number_format = 'dd/mm'; c.font = Font(name=X.FONT, size=8, color='0000FF')
    c.alignment = Alignment(text_rotation=90)
lt.row_dimensions[3].height = 36
tv = {t['id']: t['ho_ten'] for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']}
r = 5
for g in lich['goi']:
    X.o(lt, r, 1, str(g['ma']), dam=not g['la'])
    X.o(lt, r, 2, g['ten'], dam=not g['la'])
    X.o(lt, r, 3, g['muc'])
    if g['la']:
        X.o(lt, r, 4, float(g['md']), fmt=X.SO2, nhap=True)
        X.o(lt, r, 5, ', '.join(tv.get(p, p) for p in g['nguoi']) + (' (dàn trải)' if g.get('dan_trai') else ''), nhap=True)
        X.o(lt, r, 6, D(g['bat_dau']), fmt=X.NGAY, nhap=True)
        X.o(lt, r, 7, D(g['ket_thuc']), fmt=X.NGAY, nhap=True)
        X.o(lt, r, 11, ', '.join(g.get('phu_thuoc', [])), nhap=True)
        X.o(lt, r, 12, 'Có' if g.get('gang') else '', nhap=True)
    else:
        X.o(lt, r, 4, f'=SUMIFS(D:D,M:M,A{r})', fmt=X.SO2, dam=True)
        X.o(lt, r, 5, '')
        X.o(lt, r, 6, f'=_xlfn.MINIFS(F:F,M:M,A{r})', fmt=X.NGAY, dam=True)
        X.o(lt, r, 7, f'=_xlfn.MAXIFS(G:G,M:M,A{r})', fmt=X.NGAY, dam=True)
        X.o(lt, r, 11, ''); X.o(lt, r, 12, '')
    X.o(lt, r, 8, f'=NETWORKDAYS(F{r},G{r},Tong_quan!$F$4:$F$40)', fmt='0')
    X.o(lt, r, 9, g['sprint_bat_dau'], nhap=True); X.o(lt, r, 10, g['sprint_ket_thuc'], nhap=True)
    X.o(lt, r, 13, str(g.get('cha', '')))
    r += 1
last = r - 1
rng = f'{L(C0)}5:{L(C0 + len(tuan) - 1)}{last}'
cl = L(C0)
lt.conditional_formatting.add(rng, FormulaRule(formula=[f'AND($C5<3,{cl}$3<=$G5,{cl}$3+4>=$F5)'], fill=PatternFill('solid', fgColor='808080'), stopIfTrue=True))
lt.conditional_formatting.add(rng, FormulaRule(formula=[f'AND($L5="Có",{cl}$3<=$G5,{cl}$3+4>=$F5)'], fill=PatternFill('solid', fgColor='C00000'), stopIfTrue=True))
lt.conditional_formatting.add(rng, FormulaRule(formula=[f'AND({cl}$3<=$G5,{cl}$3+4>=$F5)'], fill=PatternFill('solid', fgColor='4472C4')))
lt.freeze_panes = 'C5'
X.ghi_chu_bang(lt, last + 2, 'Thanh xám: mục cha. Thanh đỏ: gói trên đường găng theo phụ thuộc. Thanh xanh: gói khác. Mỗi cột là một tuần, ngày đầu tuần ở dòng 3.')

# ---------------- Sprint
sp = wb.create_sheet('Sprint')
X.tieu_de(sp, 1, ['Sprint', 'Từ ngày', 'Đến ngày', 'Số ngày làm việc', 'MD kế hoạch', 'Quỹ thời gian, MD', 'Tỷ lệ sử dụng', 'Mục tiêu', 'Sản phẩm trình diễn'],
          [8, 12, 12, 10, 12, 14, 11, 44, 44])
for i, s in enumerate(lich['sprint'], 2):
    X.o(sp, i, 1, s['ma'], nhap=True); X.o(sp, i, 2, D(s['tu']), fmt=X.NGAY, nhap=True); X.o(sp, i, 3, D(s['den']), fmt=X.NGAY, nhap=True)
    X.o(sp, i, 4, f'=NETWORKDAYS(B{i},C{i},Tong_quan!$F$4:$F$40)', fmt='0')
    X.o(sp, i, 5, f'=SUMIFS(Phan_bo!D:D,Phan_bo!C:C,A{i})', fmt=X.SO2)
    X.o(sp, i, 6, f'=SUMIFS(Phan_bo!E:E,Phan_bo!C:C,A{i})', fmt=X.SO2)
    X.o(sp, i, 7, f'=IF(F{i}=0,0,E{i}/F{i})', fmt=X.PT)
    X.o(sp, i, 8, s['muc_tieu'], nhap=True, wrap=True); X.o(sp, i, 9, s['san_pham_demo'], nhap=True, wrap=True)
n_sp = len(lich['sprint']) + 1
X.o(sp, n_sp + 1, 1, 'Tổng', dam=True)
for c in (4, 5, 6):
    X.o(sp, n_sp + 1, c, f'=SUM({L(c)}2:{L(c)}{n_sp})', fmt=X.SO2 if c > 4 else '0', dam=True)
X.o(sp, n_sp + 1, 7, f'=IF(F{n_sp + 1}=0,0,E{n_sp + 1}/F{n_sp + 1})', fmt=X.PT, dam=True)

# ---------------- Moc
mc = wb.create_sheet('Moc')
X.tieu_de(mc, 1, ['Mốc', 'Nội dung', 'Ngày dự kiến', 'Hạn', 'Trạng thái', 'Căn cứ (gói hoàn thành)', 'Đợt thanh toán', 'Sprint'], [6, 44, 12, 12, 13, 26, 10, 8])
for i, m in enumerate(lich['moc'], 2):
    X.o(mc, i, 1, m['ma'], nhap=True); X.o(mc, i, 2, m['ten'], nhap=True, wrap=True); X.o(mc, i, 3, D(m['ngay']), fmt=X.NGAY, nhap=True)
    X.o(mc, i, 4, D(m['han']) if m['han'] else None, fmt=X.NGAY, nhap=True)
    X.o(mc, i, 5, f'=IF(D{i}="","Không có hạn",IF(C{i}<=D{i},"Đúng hạn","Trễ hạn"))')
    X.o(mc, i, 6, m['can_cu'], nhap=True, wrap=True); X.o(mc, i, 7, m['dot_thanh_toan'] or None, nhap=True); X.o(mc, i, 8, m['sprint'], nhap=True)
mc.conditional_formatting.add(f'E2:E{len(lich["moc"]) + 1}', FormulaRule(formula=['E2="Trễ hạn"'], fill=PatternFill('solid', fgColor='F8CBAD')))

# ---------------- Phan_bo và Tai_nguon
pb = wb.create_sheet('Phan_bo')
X.tieu_de(pb, 1, ['Mã thành viên', 'Họ tên', 'Sprint', 'MD kế hoạch', 'Quỹ thời gian, MD', 'Tỷ lệ'], [12, 26, 8, 12, 14, 9])
for i, x in enumerate(lich['phan_bo'], 2):
    X.o(pb, i, 1, x['thanh_vien'], nhap=True); X.o(pb, i, 2, x['ho_ten'], nhap=True); X.o(pb, i, 3, x['sprint'], nhap=True)
    X.o(pb, i, 4, x['md'], fmt=X.SO2, nhap=True); X.o(pb, i, 5, x['quy'], fmt=X.SO2, nhap=True)
    X.o(pb, i, 6, f'=IF(E{i}=0,0,D{i}/E{i})', fmt=X.PT)
pb.conditional_formatting.add(f'F2:F{len(lich["phan_bo"]) + 1}', FormulaRule(formula=['F2>1'], fill=PatternFill('solid', fgColor='F8CBAD')))
tn = wb.create_sheet('Tai_nguon')
tn['A1'] = 'Tải công việc theo thành viên và sprint, MD'; tn['A1'].font = X.F_TEN
ma_sp = [s['ma'] for s in lich['sprint']]
X.tieu_de(tn, 3, ['Mã', 'Họ tên'] + ma_sp + ['Tổng MD', 'Tổng quỹ', 'Tỷ lệ'], [10, 26] + [8] * len(ma_sp) + [10, 10, 9])
ids = []
for x in lich['phan_bo']:
    if x['thanh_vien'] not in ids:
        ids.append(x['thanh_vien'])
for i, p in enumerate(ids, 4):
    X.o(tn, i, 1, p, nhap=True); X.o(tn, i, 2, tv.get(p, p), nhap=True)
    for j, s in enumerate(ma_sp, 3):
        X.o(tn, i, j, f'=SUMIFS(Phan_bo!$D:$D,Phan_bo!$A:$A,$A{i},Phan_bo!$C:$C,{L(j)}$3)', fmt=X.SO2)
    k = 3 + len(ma_sp)
    X.o(tn, i, k, f'=SUM({L(3)}{i}:{L(k - 1)}{i})', fmt=X.SO2)
    X.o(tn, i, k + 1, f'=SUMIFS(Phan_bo!$E:$E,Phan_bo!$A:$A,$A{i})', fmt=X.SO2)
    X.o(tn, i, k + 2, f'=IF({L(k + 1)}{i}=0,0,{L(k)}{i}/{L(k + 1)}{i})', fmt=X.PT)
# ô đỏ: MD của thành viên trong sprint vượt quỹ thời gian của sprint đó (đối chiếu sheet Phan_bo)
tn.conditional_formatting.add(f'{L(3)}4:{L(2 + len(ma_sp))}{3 + len(ids)}',
                              FormulaRule(formula=[f'{L(3)}4>SUMIFS(Phan_bo!$E:$E,Phan_bo!$A:$A,$A4,Phan_bo!$C:$C,{L(3)}$3)+0.01'], fill=PatternFill('solid', fgColor='F8CBAD')))

# ---------------- Huong_dan
hd = wb.create_sheet('Huong_dan')
for i, t in enumerate(['Hướng dẫn sử dụng master schedule',
                       'Sheet Lich_trinh: lịch từng gói WBS, thanh Gantt theo tuần. Mục cha tính bằng công thức từ mục con.',
                       'Sheet Sprint: mục tiêu, sản phẩm trình diễn, MD kế hoạch và quỹ thời gian từng sprint.',
                       'Sheet Moc: các mốc, ngày dự kiến, hạn, trạng thái, liên kết đợt thanh toán.',
                       'Sheet Phan_bo và Tai_nguon: MD kế hoạch theo thành viên và sprint, ô đỏ là quá tải.',
                       'Cách cập nhật: sửa WBS, giao việc hoặc mốc và lập lại lịch theo skill master schedule. Không sửa tay các ô chữ xanh dương.',
                       f'Nguồn dữ liệu: du_lieu/lich.json, tạo lúc {loi.bay_gio()}.'], 1):
    c = hd.cell(row=i, column=1, value=t); c.font = X.F_TEN if i == 1 else X.F_THUONG
hd.column_dimensions['A'].width = 120
wb.save(OUT)

# ---------------- tính lại và đối chiếu
kq = X.tinh_lai(OUT)
ghi_chu = 'Chưa tính lại công thức (máy không có LibreOffice). Excel tự tính khi mở.'
if kq and kq.get('status'):
    loi_ct = X.dem_loi_cong_thuc(OUT)
    if loi_ct:
        loi.thoat_loi('Công thức lỗi: ' + ', '.join(loi_ct[:10]))
    v = X.doc_gia_tri(OUT)
    tong = v['Tong_quan']['B7'].value
    if tong is None or abs(float(tong) - float(wbs['tong_md'])) > 0.01:
        loi.thoat_loi(f'Tổng MD trong Excel ({tong}) khác WBS ({wbs["tong_md"]})')
    so_ngay = v['Tong_quan']['B6'].value
    if int(so_ngay) != lich['so_ngay_lam_viec']:
        loi.thoat_loi(f'Số ngày làm việc trong Excel ({so_ngay}) khác lịch ({lich["so_ngay_lam_viec"]})')
    for i, s in enumerate(lich['sprint'], 2):
        if abs(float(v['Sprint'][f'E{i}'].value) - s['md_ke_hoach']) > 0.05:
            loi.thoat_loi(f'MD sprint {s["ma"]} trong Excel khác lich.json')
    ghi_chu = f'Đã tính lại công thức, 0 lỗi, đối chiếu tổng MD {wbs["tong_md"]:g}, {so_ngay} ngày làm việc, MD từng sprint khớp lich.json.'
print('Đã tạo ' + loi.tuong_doi(OUT) + '. ' + ghi_chu)
pbs = loi.hoan_tat_buoc('lich', 'Lập lịch có ràng buộc nguồn lực và xuất master schedule Excel. ' + ghi_chu,
                        hash_tep={'ket_qua/04_Master_schedule/Master_schedule.xlsx': loi.bam_obj(lich)})
for k, v in pbs.items():
    print(f'  {k}: phiên bản {v}')
