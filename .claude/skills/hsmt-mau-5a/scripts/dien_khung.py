"""Bước 5b. Ghép nội dung agent Soạn thảo viết (ban_soan.json) vào khung.

Dùng: python3 dien_khung.py <hsmt_khung.json> <ban_soan.json> <hsmt_noi_dung.json>
ban_soan.json là một đối tượng {ID: nội dung}:
- dạng "doan" hoặc "danh_sach_doan": chuỗi hoặc danh sách chuỗi (mỗi chuỗi là một đoạn)
- dạng "dong_bang": danh sách các dòng, mỗi dòng là danh sách ô (chuỗi hoặc danh sách chuỗi)
Mã thoát 1 nếu thiếu ID, thừa ID, sai dạng hoặc sai số ô.
"""
import copy, json, sys

khung = json.load(open(sys.argv[1], encoding='utf-8'))
soan = json.load(open(sys.argv[2], encoding='utf-8'))
out = sys.argv[3]
can = khung['can_soan']
loi = []
for k in can:
    if k not in soan:
        loi.append('Thiếu nội dung cho ' + k)
for k in soan:
    if k not in can:
        loi.append('ID không có trong khung: ' + k)


def is_ph(s):
    return isinstance(s, str) and s.startswith('<<SOẠN:') and s.endswith('>>')


def pid(s):
    return s[len('<<SOẠN:'):-2]


def as_list(v):
    return v if isinstance(v, list) else [v]


def fill_inline(s):
    # thay chỗ giữ chỗ nằm giữa câu (dạng doan, nội dung một chuỗi)
    while '<<SOẠN:' in s:
        a = s.index('<<SOẠN:'); b = s.index('>>', a)
        k = s[a + 7:b]
        v = soan.get(k, '')
        if isinstance(v, list):
            v = ' '.join(v)
        s = s[:a] + v + s[b + 2:]
    return s


blocks = []
for b in khung['blocks']:
    b = copy.deepcopy(b)
    if b['t'] == 'p' and is_ph(b['text']) and can.get(pid(b['text']), {}).get('dang') == 'danh_sach_doan':
        for t in as_list(soan.get(pid(b['text']), '')):
            blocks.append({'t': 'p', 'text': t})
        continue
    if b['t'] in ('p', 'center', 'h1', 'h2'):
        b['text'] = fill_inline(b['text'])
    if b['t'] == 'table':
        ncol = len(b['widths'])
        rows = []
        for r in b['rows']:
            if is_ph(r):
                k = pid(r)
                for rr in as_list(soan.get(k, [])):
                    if not isinstance(rr, list) or len(rr) != ncol:
                        loi.append(f'{k}: mỗi dòng phải có {ncol} ô')
                        continue
                    rows.append(rr)
                continue
            new = []
            for c in r:
                if is_ph(c):
                    v = soan.get(pid(c), '')
                    new.append(v if isinstance(v, list) else v)
                elif isinstance(c, list):
                    new.append([fill_inline(x) for x in c])
                else:
                    new.append(fill_inline(c))
            rows.append(new)
        b['rows'] = rows
    blocks.append(b)

txt = json.dumps(blocks, ensure_ascii=False)
if '<<SOẠN:' in txt:
    loi.append('Còn chỗ giữ chỗ chưa điền')
if loi:
    print('LỖI:', *loi, sep='\n- ')
    sys.exit(1)
json.dump({'meta': khung['meta'], 'blocks': blocks}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'Đã ghép {len(soan)} mục vào khung: {out}')
