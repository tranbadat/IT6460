"""Lập khung tài liệu từ đặc tả (dac_ta.json của từng skill) và dữ liệu dự án.

Dùng: python lap_khung.py <dac_ta.json> <khung_ra.json>

Đặc tả gồm:
  id, ten, tieu_de_dau_trang, huong ("doc" | "ngang"), nguon {bí danh: đường dẫn}, bia {tieu_de, dong_phu[]}, muc_luc (true: thêm mục lục),
  khoi[]: danh sách khối theo thứ tự trình bày
    {"h1"|"h2"|"h3": "tiêu đề"}
    {"doan": "câu có tham chiếu {bi_danh#duong_dan|dinh_dang}"}      đoạn tự động
    {"soan": "ID", "huong_dan": ..., "nguon": [...], "dang": "doan|danh_sach_doan|dong_bang",
     "cot": [tiêu đề cột] (dong_bang), "widths": [...], "toi_thieu": n, "bat_buoc": [cụm từ phải có]}
    {"bang": {"nguon": "bi_danh#duong_dan_toi_danh_sach", "cot": [[tiêu đề, trường|định dạng hoặc =mẫu {.truong|dd}, rộng, căn l|c|r]],
              "loc": {truong: giá trị hoặc [giá trị]}, "dam_neu": {truong: [giá trị]}, "dong_tong": {"nhan": ..., "cot": [chỉ số cột]},
              "rong_thi": "câu khi danh sách rỗng"}}
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
        return ', '.join(str(x) for x in v)
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


blocks, can_soan = [], {}


def add(t, **kw):
    kw['t'] = t
    blocks.append(kw)


# ---------------- bìa
da = nguon.get('da', {})
bia = spec.get('bia')
if bia:
    add('center', text=da.get('don_vi_thuc_hien', ''), size=13)
    add('center', text=da.get('ten_du_an', ''), size=13)
    add('blank'); add('blank')
    add('center', text=G(bia.get('tieu_de', spec['ten'])), size=20)
    for d in bia.get('dong_phu', []):
        add('center', text=G(d), size=14)
    add('blank'); add('blank')
    rows = [['Dự án', da.get('ten_du_an', '')], ['Khách hàng', da.get('khach_hang', '')], ['Đơn vị thực hiện', da.get('don_vi_thuc_hien', '')],
            ['Môn học', da.get('mon_hoc', '')], ['Nhóm', da.get('ma_nhom', '')], ['Giảng viên', da.get('giang_vien', '')],
            ['Người lập', da.get('nguoi_lap', '')], ['Phiên bản', '{{PHIEN_BAN}}'], ['Ngày', '{{NGAY}}']]
    add('table', rows=[r for r in rows if r[1]], widths=[3000, 6300])
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
                s = sum(float(r.get(key) or 0) for r in ds if not dt.get('chi_tinh') or khop(r, dt['chi_tinh']))
                f = loi.chon_dinh_dang(f, key) if f else f
                if ci in le_cot:
                    tong[ci] = dinh_dang_cot([s] + [r.get(key) for r in ds], f)[0]
                else:
                    tong[ci] = loi.DINH_DANG[f](s) if f else loi.so(s, 0)
            rows.append(tong)
        al = [c[3] if len(c) > 3 else 'l' for c in bs['cot']]
        add('table', rows=rows, widths=[c[2] for c in bs['cot']], center_cols=[i for i, x in enumerate(al) if x == 'c'],
            right_cols=[i for i, x in enumerate(al) if x == 'r'], dong_dam=dam)
    elif 'bang_san' in kb:
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
