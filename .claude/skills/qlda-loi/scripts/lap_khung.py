"""Lập khung tài liệu từ đặc tả (dac_ta.json của từng skill) và dữ liệu dự án.

Dùng: python lap_khung.py <dac_ta.json> <khung_ra.json>

Đặc tả gồm:
  id, ten, tieu_de_dau_trang, huong ("doc" | "ngang"), nguon {bí danh: đường dẫn}, muc_luc (true: thêm mục lục),
  đường dẫn nguồn dạng "skill:<skill>/references/<tệp>.json" trỏ tới tệp tham chiếu tĩnh của skill (ví dụ quy tắc dùng dự phòng
  skill:qlda-change/references/phan_loai.json), dùng chung cho nhiều đặc tả;
  nguon_tuy_chon [bí danh]: thiếu tệp thì không dừng, bảng (bang, bang_san) dùng bí danh đó được bỏ qua kèm cảnh báo,
  bia {tieu_de, dong_phu[]}: bìa tài liệu nội bộ (đơn vị, dự án, bảng môn học, nhóm, giảng viên, người lập, phiên bản, ngày)
  bia {"kieu": "ho_so_thau", "dong_tren": [...], tieu_de, dong_phu[], "bang": [[nhãn, giá trị]]}: bìa hồ sơ gửi bên ngoài
      (HSDT), chỉ in dòng khai báo, không in môn học, nhóm, giảng viên. Thiếu dòng Ngày thì tự thêm.
  khoi[]: danh sách khối theo thứ tự trình bày
    {"h1"|"h2"|"h3": "tiêu đề"}
    {"doan": "câu có tham chiếu {bi_danh#duong_dan|dinh_dang}"}      đoạn tự động
    {"soan": "ID", "huong_dan": ..., "nguon": [...], "dang": "doan|danh_sach_doan|dong_bang",
     "cot": [tiêu đề cột] (dong_bang), "widths": [...], "toi_thieu": n, "bat_buoc": [cụm từ phải có]}
    {"bang": {"nguon": "bi_danh#duong_dan_toi_danh_sach", "cot": [[tiêu đề, trường|định dạng hoặc =mẫu {.truong|dd}, rộng, căn l|c|r]],
              "loc": {truong: giá trị hoặc [giá trị]}, "dam_neu": {truong: [giá trị]},
              "dong_tong": {"nhan": ..., "cot": [chỉ số cột], "tong": {"chỉ số cột": "bi_danh#duong_dan tổng gốc"}},
              "rong_thi": "câu khi danh sách rỗng", "mau_so": "10A" (bảng theo biểu mẫu, script của skill so cột với Mẫu 5A)}}
      dong_tong.tong: cột MD, phần trăm có tổng gốc (ví dụ wbs#tong_md) thì phần làm tròn của từng dòng được phân bổ lại
      bằng loi.lam_tron_tong để các dòng cộng đúng tổng gốc. Lệch quá sai số làm tròn thì giữ nguyên và cảnh báo.
    {"bang_tinh": {"rows": [[ô có tham chiếu]], "widths": [...], "right_cols": [...]}}
    {"bang_san": "bi_danh#duong_dan"}   bảng script tính sẵn: {"cot": [...], "dong": [[...]], "widths", "center_cols", "right_cols", "dong_dam"}
    {"pagebreak": true} | {"section": "ngang" | "doc"} | {"doan_ds": "bi_danh#duong_dan"} (danh sách đoạn văn có sẵn)
  kiem_tra {...}: dùng ở bước kiểm tra, không dùng ở đây.
Mục cần agent soạn được để dạng <<SOẠN:ID>> và mô tả trong khóa can_soan của khung.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loi  # noqa: E402

spec_path, out_path = sys.argv[1], sys.argv[2]
spec = json.load(open(spec_path, encoding='utf-8'))
sd = loi.so_do()

# ---------------- nguồn dữ liệu
nguon_paths = dict(spec.get('nguon', {}))
nguon_paths.setdefault('da', 'dau_vao/du_an.json')
nguon = loi.nap_nguon(nguon_paths)
thieu = [f'{k}: {p}' for k, p in nguon_paths.items() if k not in nguon and k not in spec.get('nguon_tuy_chon', [])]
if thieu:
    # gợi ý bước tạo ra tệp thiếu
    goi_y = []
    for x in thieu:
        p = x.split(': ', 1)[1]
        for b in sd['buoc']:
            if p in b['ra'].values():
                goi_y.append(f'{p} do bước {b["id"]} (skill {b["skill"]}) tạo')
        for k, v in sd['dau_vao'].items():
            if v['tep'] == p:
                goi_y.append(f'{p} là đầu vào do nhóm cung cấp ({v["mo_ta"]})')
    loi.thoat_loi('Thiếu dữ liệu đầu vào:\n- ' + '\n- '.join(thieu) + ('\nGợi ý:\n- ' + '\n- '.join(goi_y) if goi_y else ''))

loi_tham_chieu = []
G = lambda text: loi.giai_bieu_thuc(text, nguon, loi_tham_chieu)


def dinh_dang_gt(v, f=None):
    if v is None or v == '':
        return ''
    if isinstance(v, list):
        return loi.gia_tri_chuoi(v, f)
    if f:
        return loi.DINH_DANG[f](v)
    if isinstance(v, float):
        return loi.so(v, 2) if abs(v - round(v)) > 1e-9 else loi.so(v, 0)
    return str(v)


def gia_tri_o(row, expr):
    """expr: 'truong|dd' hoặc '=mẫu {.truong|dd} ...' (có thể kèm tham chiếu {bi_danh#...})"""
    if expr.startswith('='):
        return G(re.sub(r'\{\.([a-z_0-9]+)(?:\|([a-z0-9]+))?\}', lambda m: dinh_dang_gt(row.get(m.group(1)), m.group(2)), expr[1:]))
    k, _, f = expr.partition('|')
    return dinh_dang_gt(row.get(k), loi.chon_dinh_dang(f, k) if f else None)


dinh_dang_cot = loi.dinh_dang_cot


def khop(row, dk):
    for k, v in (dk or {}).items():
        vs = v if isinstance(v, list) else [v]
        if row.get(k) not in vs:
            return False
    return True


TUY_CHON = set(spec.get('nguon_tuy_chon', []))


def thieu_tuy_chon(bt):
    """Bảng (bang, bang_san) dùng nguồn khai báo trong nguon_tuy_chon mà chưa có tệp: bỏ qua bảng, cảnh báo, không dừng."""
    bd = bt.split('#', 1)[0]
    if bd in TUY_CHON and bd not in nguon:
        print(f'CẢNH BÁO: bỏ qua bảng {bt} vì chưa có tệp nguồn tùy chọn {nguon_paths.get(bd)}')
        return True
    return False


def tong_goc(dt, ci):
    """Tổng gốc khai báo cho cột ci của dòng tổng: "tong": {"<ci>": "bi_danh#duong_dan"} (ví dụ wbs#tong_md)."""
    bt = (dt.get('tong') or {}).get(str(ci))
    if not bt:
        return None
    try:
        bd, path = bt.split('#', 1)
        return float(loi.lay(nguon[bd], path))
    except Exception:
        loi_tham_chieu.append(bt)
        return None


def khop_tong_hien_thi(vals, goc, f, ten_cot):
    """Giá trị hiển thị các dòng và tổng sao cho cộng đúng tổng gốc (không ra 351,01 khi tổng gốc là 351).
    Chênh lệch chỉ do làm tròn từng dòng (không quá nửa đơn vị cuối mỗi dòng) thì phân bổ lại bằng loi.lam_tron_tong,
    chỉ trên các dòng đã bị làm tròn (dùng đến chữ số thập phân cuối), dòng số tròn giữ nguyên.
    Chênh lệch lớn hơn là sai dữ liệu: giữ nguyên và cảnh báo. Trả về (giá trị dòng đã định dạng, tổng)."""
    so_ = [float(v or 0) for v in vals]
    nhan = 100 if f in ('pt', 'pt1') else 1
    le = 2 if f in ('md', 'md2', 'mda') else 1
    moi = loi.khop_tong([v * nhan for v in so_], goc * nhan, le)
    if moi is None:
        print(f'CẢNH BÁO: cột {ten_cot} cộng {loi.so(sum(so_), le)}, khác tổng gốc {loi.so(goc, le)} quá sai số làm tròn, giữ nguyên số liệu')
        return dinh_dang_cot(vals, f), sum(so_)
    return dinh_dang_cot([v / nhan for v in moi], f), goc


blocks, can_soan = [], {}


def add(t, **kw):
    kw['t'] = t
    blocks.append(kw)


# ---------------- bìa
da = nguon.get('da', {})
bia = spec.get('bia')
KIEU_BIA_HO_SO_THAU = ('ho_so_thau', 'ho_so_du_thau')


def bang_bia(bia):
    """Bảng thông tin trên bìa. Kiểu ho_so_thau (HSMT, HSDT gửi bên ngoài): chỉ các dòng khai báo trong bia.bang
    và ngày, không in môn học, nhóm, giảng viên, người lập. Kiểu mặc định: bảng thông tin dự án của nhóm."""
    if bia.get('kieu') in KIEU_BIA_HO_SO_THAU:
        rows = [[G(k), G(v)] for k, v in bia.get('bang', [])]
        return rows if any(r[0] == 'Ngày' for r in rows) else rows + [['Ngày', '{{NGAY}}']]
    return [['Dự án', da.get('ten_du_an', '')], ['Khách hàng', da.get('khach_hang', '')], ['Đơn vị thực hiện', da.get('don_vi_thuc_hien', '')],
            ['Môn học', da.get('mon_hoc', '')], ['Nhóm', da.get('ma_nhom', '')], ['Giảng viên', da.get('giang_vien', '')],
            ['Người lập', da.get('nguoi_lap', '')], ['Phiên bản', '{{PHIEN_BAN}}'], ['Ngày', '{{NGAY}}']]


if bia:
    if bia.get('kieu') in KIEU_BIA_HO_SO_THAU:
        dong_tren = [G(d) for d in bia.get('dong_tren', [])]
    else:
        dong_tren = [da.get('don_vi_thuc_hien', ''), da.get('ten_du_an', '')]
    for d in dong_tren:
        add('center', text=d, size=13)
    add('blank'); add('blank')
    add('center', text=G(bia.get('tieu_de', spec['ten'])), size=20)
    for d in bia.get('dong_phu', []):
        add('center', text=G(d), size=14)
    add('blank'); add('blank')
    add('table', rows=[r for r in bang_bia(bia) if r[1]], widths=[3000, 6300])
    add('pagebreak')
if spec.get('muc_luc'):
    add('muc_luc', muc=[G(kb[lv]) for kb in spec.get('khoi', []) for lv in ('h1', 'h2') if lv in kb])
    add('pagebreak')

# ---------------- khối
for kb in spec['khoi']:
    if 'h1' in kb or 'h2' in kb or 'h3' in kb:
        lv = 'h1' if 'h1' in kb else ('h2' if 'h2' in kb else 'h3')
        add(lv, text=G(kb[lv]))
    elif 'doan' in kb:
        add('p', text=G(kb['doan']))
    elif 'soan' in kb:
        i = kb['soan']
        can_soan[i] = {k: kb[k] for k in ('huong_dan', 'nguon', 'dang', 'cot', 'toi_thieu', 'bat_buoc', 'widths') if k in kb}
        can_soan[i].setdefault('dang', 'danh_sach_doan')
        ph = f'<<SOẠN:{i}>>'
        if can_soan[i]['dang'] == 'dong_bang':
            add('table', rows=[kb['cot'], ph], widths=kb.get('widths') or [int(9300 / len(kb['cot']))] * len(kb['cot']),
                center_cols=kb.get('center_cols', []), right_cols=kb.get('right_cols', []))
        else:
            add('p', text=ph)
    elif 'bang' in kb:
        bs = kb['bang']
        if thieu_tuy_chon(bs['nguon']):
            continue
        try:
            bd, path = bs['nguon'].split('#', 1)
            ds = loi.lay(nguon[bd], path)
        except Exception:
            loi_tham_chieu.append(bs['nguon']); ds = []
        ds = [r for r in ds if khop(r, bs.get('loc'))]
        if bs.get('sap_xep'):
            ds = sorted(ds, key=lambda r: r.get(bs['sap_xep']) if not isinstance(r.get(bs['sap_xep']), str) else [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', r.get(bs['sap_xep']))])
        if not ds and bs.get('rong_thi'):
            add('p', text=G(bs['rong_thi'])); continue
        header = [c[0] for c in bs['cot']]
        rows = [header]
        dam = []
        for r in ds:
            rows.append([gia_tri_o(r, c[1]) for c in bs['cot']])
            if bs.get('dam_neu') and khop(r, bs['dam_neu']):
                dam.append(len(rows) - 1)
        le_cot = {}
        for ci, c in enumerate(bs['cot']):  # cùng số chữ số thập phân trong một cột
            if not c[1].startswith('=') and '|' in c[1]:
                k, _, f = c[1].partition('|'); f = loi.chon_dinh_dang(f, k)
                cot = dinh_dang_cot([r.get(k) for r in ds], f)
                if cot is not None:
                    for ri, v in enumerate(cot, 1):
                        rows[ri][ci] = v
                    le_cot[ci] = f
        if bs.get('dong_tong'):
            dt = bs['dong_tong']
            tong = [''] * len(header)
            ung_vien = [i for i in range(len(header)) if i not in dt.get('cot', [])]
            rong = [i for i in ung_vien if bs['cot'][i][2] >= 1500]
            tong[dt.get('cot_nhan', (rong or ung_vien or [0])[0])] = dt.get('nhan', 'Tổng cộng')
            for ci in dt.get('cot', []):
                key, _, f = bs['cot'][ci][1].partition('|')
                chon = [r for r in ds if not dt.get('chi_tinh') or khop(r, dt['chi_tinh'])]
                s = sum(float(r.get(key) or 0) for r in chon)
                f = loi.chon_dinh_dang(f, key) if f else f
                goc = tong_goc(dt, ci)
                if goc is not None and ci in le_cot and len(chon) == len(ds):
                    hien_thi, s = khop_tong_hien_thi([r.get(key) for r in ds], goc, f, header[ci])
                    for ri, v in enumerate(hien_thi, 1):
                        rows[ri][ci] = v
                if ci in le_cot:
                    tong[ci] = dinh_dang_cot([s] + [r.get(key) for r in ds], f)[0]
                else:
                    tong[ci] = loi.DINH_DANG[f](s) if f else loi.so(s, 0)
            rows.append(tong)
        al = [c[3] if len(c) > 3 else 'l' for c in bs['cot']]
        add('table', rows=rows, widths=[c[2] for c in bs['cot']], center_cols=[i for i, x in enumerate(al) if x == 'c'],
            right_cols=[i for i, x in enumerate(al) if x == 'r'], dong_dam=dam)
    elif 'bang_san' in kb:
        if thieu_tuy_chon(kb['bang_san']):
            continue
        try:
            bd, path = kb['bang_san'].split('#', 1)
            tb = loi.lay(nguon[bd], path)
        except Exception:
            loi_tham_chieu.append(kb['bang_san']); continue
        if not tb.get('dong') and kb.get('rong_thi'):
            add('p', text=G(kb['rong_thi'])); continue
        add('table', rows=[tb['cot']] + tb['dong'], widths=tb.get('widths') or kb.get('widths') or [int(9300 / len(tb['cot']))] * len(tb['cot']),
            center_cols=tb.get('center_cols', []), right_cols=tb.get('right_cols', []), dong_dam=tb.get('dong_dam', []))
    elif 'bang_tinh' in kb:
        bt = kb['bang_tinh']
        add('table', rows=[[G(c) if isinstance(c, str) else [G(x) for x in c] for c in r] for r in bt['rows']], widths=bt['widths'],
            center_cols=bt.get('center_cols', []), right_cols=bt.get('right_cols', []))
    elif 'doan_ds' in kb:  # danh sách đoạn văn có sẵn trong dữ liệu (ví dụ nguyên văn biểu mẫu)
        try:
            bd_, path_ = kb['doan_ds'].split('#', 1)
            for t_ in loi.lay(nguon[bd_], path_):
                add('p', text=G(t_))
        except Exception:
            loi_tham_chieu.append(kb['doan_ds'])
    elif 'pagebreak' in kb:
        add('pagebreak')
    elif 'section' in kb:
        add('section', huong=kb['section'])
    else:
        loi.thoat_loi('Khối đặc tả không hợp lệ: ' + json.dumps(kb, ensure_ascii=False)[:200])

if loi_tham_chieu:
    loi.thoat_loi('Tham chiếu dữ liệu không giải được (kiểm tra dữ liệu hoặc đặc tả):\n- ' + '\n- '.join(sorted(set(loi_tham_chieu))))

meta = {'ten': spec['ten'], 'id': spec['id'], 'header': G(spec.get('tieu_de_dau_trang', spec['ten'])), 'huong': spec.get('huong', 'doc'),
        'font': 'Times New Roman', 'size_pt': 13, 'size_bang_pt': spec.get('co_chu_bang', 12), 'nguon': nguon_paths}
loi.ghi_json(out_path, {'meta': meta, 'can_soan': can_soan, 'blocks': blocks})
print(f'Đã lập khung {spec["id"]}: {len(blocks)} khối, {len(can_soan)} mục cần agent soạn')
for k, v in can_soan.items():
    print(f'  {k} ({v["dang"]})')
