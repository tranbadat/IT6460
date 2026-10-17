"""Ghép nội dung agent Soạn thảo viết (ban_soan.json) vào khung, giải các tham chiếu dữ liệu.

Dùng: python dien_khung.py <khung.json> <ban_soan.json> <noi_dung_ra.json>
ban_soan.json: {ID: nội dung}
- dạng doan: chuỗi; danh_sach_doan: danh sách chuỗi; dong_bang: danh sách dòng, mỗi dòng đúng số cột.
- Trong nội dung, số liệu nên viết bằng tham chiếu {bi_danh#duong_dan|dinh_dang}, ví dụ {lich#cut_over|ngay},
  để số trong tài liệu luôn khớp dữ liệu và tự cập nhật khi dữ liệu thay đổi.
Mã thoát 1: thiếu hoặc thừa ID, sai dạng, sai số cột, chưa đủ số đoạn tối thiểu, thiếu cụm từ bắt buộc,
tham chiếu không giải được. Số liệu viết tay (tiền, MD, phần trăm, ngày) được cảnh báo.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import copy
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loi  # noqa: E402

khung = json.load(open(sys.argv[1], encoding='utf-8'))
soan = json.load(open(sys.argv[2], encoding='utf-8'))
out = sys.argv[3]
can = khung['can_soan']
nguon = loi.nap_nguon(khung['meta'].get('nguon', {}))
loi_ds, canh_bao = [], []

for k in can:
    if k not in soan:
        loi_ds.append('Thiếu nội dung cho ' + k)
for k in soan:
    if k not in can:
        loi_ds.append('ID không có trong khung: ' + k)

SO_VIET_TAY = re.compile(r'(?<![\w{#.])(\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?\s?(?:%|MD|MM|triệu|tỷ|đồng|ngày làm việc)|\d{1,2}/\d{1,2}/\d{4})')


def giai(text, id_):
    if not isinstance(text, str):
        return text
    raw = loi.MAU_THAM_CHIEU.sub('', text)
    for m in SO_VIET_TAY.finditer(raw):
        canh_bao.append(f'{id_}: số liệu viết tay "{m.group(0)}", nên dùng tham chiếu dữ liệu để tự cập nhật khi có thay đổi')
    bad = []
    s = loi.giai_bieu_thuc(text, nguon, bad)
    for b in bad:
        loi_ds.append(f'{id_}: tham chiếu không giải được {b}')
    return s


def ds(v):
    return v if isinstance(v, list) else [v]


da_giai = {}
for k, v in soan.items():
    if k not in can:
        continue
    d = can[k]
    dang = d.get('dang', 'danh_sach_doan')
    if dang == 'dong_bang':
        ncol = len(d['cot'])
        rows = []
        for r in ds(v):
            if not isinstance(r, list) or len(r) != ncol:
                loi_ds.append(f'{k}: mỗi dòng phải có {ncol} ô ({", ".join(d["cot"])})')
                continue
            rows.append([[giai(x, k) for x in c] if isinstance(c, list) else giai(c, k) for c in r])
        da_giai[k] = rows
        n = len(rows)
    else:
        items = [giai(x, k) for x in ds(v)]
        if dang == 'doan':
            items = [' '.join(items)]
        da_giai[k] = items
        n = len(items)
    if d.get('toi_thieu') and n < d['toi_thieu']:
        loi_ds.append(f'{k}: cần tối thiểu {d["toi_thieu"]} {"dòng" if dang == "dong_bang" else "đoạn"}, hiện có {n}')
    flat = json.dumps(da_giai[k], ensure_ascii=False).lower()
    for kw in d.get('bat_buoc', []):
        if loi.giai_bieu_thuc(kw, nguon).lower() not in flat:
            loi_ds.append(f'{k}: thiếu nội dung bắt buộc "{loi.giai_bieu_thuc(kw, nguon)}"')
    if re.search(r'_{3,}|\[(ghi|nêu)', flat):
        loi_ds.append(f'{k}: còn ký hiệu ___ hoặc hướng dẫn trong ngoặc vuông')


def is_ph(s):
    return isinstance(s, str) and s.startswith('<<SOẠN:') and s.endswith('>>')


def pid(s):
    return s[7:-2]


blocks = []
for b in khung['blocks']:
    b = copy.deepcopy(b)
    if b['t'] == 'p' and is_ph(b['text']):
        for t in da_giai.get(pid(b['text']), []):
            blocks.append({'t': 'p', 'text': t})
        continue
    if b['t'] == 'table':
        rows = []
        for r in b['rows']:
            if is_ph(r):
                rows += da_giai.get(pid(r), [])
            else:
                rows.append(r)
        b['rows'] = rows
    blocks.append(b)

if '<<SOẠN:' in json.dumps(blocks, ensure_ascii=False):
    loi_ds.append('Còn chỗ giữ chỗ chưa điền')
for c in sorted(set(canh_bao)):
    print('CẢNH BÁO:', c)
if loi_ds:
    print('LỖI:', *loi_ds, sep='\n- ')
    sys.exit(1)
loi.ghi_json(out, {'meta': khung['meta'], 'blocks': blocks, 'canh_bao_soan': sorted(set(canh_bao))})
print(f'Đã ghép {len(da_giai)} mục vào khung: {loi.tuong_doi(out)}')
