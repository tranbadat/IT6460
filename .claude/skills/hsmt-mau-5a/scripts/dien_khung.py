"""Bước 5b. Ghép nội dung agent Soạn thảo viết (ban_soan.json) vào khung.

Dùng: python3 dien_khung.py <hsmt_khung.json> <ban_soan.json> <hsmt_noi_dung.json>
ban_soan.json là một đối tượng {ID: nội dung}:
- dạng "doan" hoặc "danh_sach_doan": chuỗi hoặc danh sách chuỗi (mỗi chuỗi là một đoạn)
- dạng "dong_bang": danh sách các dòng, mỗi dòng là danh sách ô (chuỗi hoặc danh sách chuỗi)
- dạng "tieu_chi_chi_tiet": đối tượng {tieu_chi_chi_tiet: [...], khong_tinh_diem: [...]}, script kiểm tra theo
  rang_buoc của khung (số tiêu chí chi tiết, tổng điểm, mức chấm, tiêu chí cơ bản, độ phủ) rồi dựng các dòng bảng
Mã thoát 1 nếu thiếu ID, thừa ID, sai dạng, sai số ô hoặc tiêu chí chi tiết không đạt ràng buộc.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import copy, json, os, re, sys

# Dấu giữ chỗ: dùng loi.la_giu_cho của bộ BTL_QLDA nếu có, dùng riêng skill thì theo cùng quy tắc
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'qlda-loi', 'scripts'))
try:
    from loi import la_giu_cho
except ImportError:
    def la_giu_cho(s):
        """Chuỗi có ngoặc vuông chứa chữ hoặc dấu ba chấm, hoặc ngoặc vuông rỗng (cùng quy tắc qlda-loi/scripts/loi.py)."""
        return isinstance(s, str) and any(not g.strip() or re.search(r'[^\W\d_]|\.\.\.|…', g) for g in re.findall(r'\[([^\[\]]*)\]', s))

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


def chuoi_trong(v):
    """Mọi chuỗi trong giá trị bản soạn (chuỗi, danh sách, đối tượng lồng nhau)."""
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        return [s for x in v for s in chuoi_trong(x)]
    if isinstance(v, dict):
        return [s for x in v.values() for s in chuoi_trong(x)]
    return []


for k, v in soan.items():
    for s in chuoi_trong(v):
        if la_giu_cho(s) or re.search(r'_{3,}', s):
            m = next((x for x in re.finditer(r'\[[^\[\]]*\]|_{3,}', s) if x.group(0).startswith('_') or la_giu_cho(x.group(0))), None)
            vt = s[max(0, m.start() - 50): m.end() + 20] if m else s[:120]
            loi.append(f'{k}: còn dấu giữ chỗ hoặc ký hiệu ___ của mẫu: ...{vt}...')


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


def so_vn(v):
    return str(int(v)) if float(v).is_integer() else str(v).replace('.', ',')


def co_chu(v):
    return bool(str(v or '').strip())


def loi_muc_cham(mc, d, ten, toi_thieu):
    if not isinstance(mc, list) or len(mc) < toi_thieu:
        return [f'{ten}: cần ít nhất {toi_thieu} mức chấm']
    out = [f'{ten}: mức chấm {i + 1} thiếu muc, diem hoặc mo_ta' for i, m in enumerate(mc)
           if not (isinstance(m, dict) and co_chu(m.get('muc')) and co_chu(m.get('mo_ta')) and isinstance(m.get('diem'), (int, float)))]
    if out:
        return out
    ds = [m['diem'] for m in mc]
    if ds[0] != d or ds[-1] != 0 or any(a <= b for a, b in zip(ds, ds[1:])):
        out.append(f'{ten}: điểm các mức phải giảm dần từ {so_vn(d)} (mức cao nhất) đến 0 (mức thấp nhất), hiện là {ds}')
    return out


def loi_tieu_chi_con(x, ten, rb, ma_hop_le):
    n = len(rb['trong_so'])
    out = [] if isinstance(x.get('tieu_chi'), int) and 1 <= x['tieu_chi'] <= n else [f'{ten}: tieu_chi phải là số thứ tự tiêu chí tổng quát từ 1 đến {n}']
    out += [f'{ten}: thiếu {k}' for k in ('ten', 'noi_dung') if not co_chu(x.get(k))]
    d = x.get('diem')
    if not isinstance(d, (int, float)) or d <= 0:
        return out + [f'{ten}: diem phải là số dương']
    if not isinstance(x.get('co_ban'), bool):
        out.append(f'{ten}: co_ban phải là true hoặc false')
    tt = x.get('diem_toi_thieu')
    if tt is not None and (x.get('co_ban') is not True or not isinstance(tt, (int, float)) or not 0 < tt <= d):
        out.append(f'{ten}: chỉ tiêu chí cơ bản được có diem_toi_thieu, lớn hơn 0 và không quá điểm tối đa (Mục 3.1 Chương III Mẫu số 5A)')
    out += loi_muc_cham(x.get('muc_cham'), d, ten, rb['so_muc_cham_toi_thieu'])
    la = [m for m in x.get('phu', []) if m not in ma_hop_le]
    return out + ([f'{ten}: mã phu không có trong can_phu: {la}'] if la else [])


def loi_nhom(ds, rb):
    lo, hi = rb['so_tieu_chi_chi_tiet']
    out = []
    for j, w in enumerate(rb['trong_so'], 1):
        con = [x for x in ds if x['tieu_chi'] == j]
        if not lo <= len(con) <= hi:
            out.append(f'tiêu chí tổng quát {j} có {len(con)} tiêu chí chi tiết, cần từ {lo} đến {hi}')
        tong = sum(x['diem'] for x in con)
        if abs(tong - w) > 1e-9:
            out.append(f'tiêu chí tổng quát {j}: tổng điểm các tiêu chí chi tiết là {so_vn(tong)}, khác điểm tối đa {w}')
    return out


def loi_do_phu(v, ds, rb, ma_hop_le):
    cham = {m for x in ds for m in x.get('phu', [])}
    ktd = v.get('khong_tinh_diem', [])
    out = [f'khong_tinh_diem: {x} cần ma thuộc can_phu và ly_do thuộc {list(rb["ly_do_khong_tinh_diem"])}' for x in ktd
           if not (isinstance(x, dict) and x.get('ma') in ma_hop_le and x.get('ly_do') in rb['ly_do_khong_tinh_diem'])]
    khong = {x.get('ma') for x in ktd if isinstance(x, dict)}
    out += [f'{m}: vừa được chấm điểm vừa ghi khong_tinh_diem' for m in sorted(cham & khong)]
    return out + [f"{c['ma']} ({c['noi_dung'][:70]}): chưa có tiêu chí chi tiết nào phủ (phu) và không ghi khong_tinh_diem"
                  for c in rb['can_phu'] if c['ma'] not in cham | khong]


def kiem_tieu_chi(v, rb):
    """Kiểm tra bản soạn tiêu chí chi tiết theo ràng buộc của khung. Trả danh sách lỗi."""
    if not isinstance(v, dict) or not isinstance(v.get('tieu_chi_chi_tiet'), list) or not v['tieu_chi_chi_tiet']:
        return ['phải là đối tượng có danh sách tieu_chi_chi_tiet']
    ds = v['tieu_chi_chi_tiet']
    if not all(isinstance(x, dict) for x in ds):
        return ['mỗi phần tử của tieu_chi_chi_tiet phải là đối tượng']
    ma_hop_le = {c['ma'] for c in rb['can_phu']}
    out = [e for i, x in enumerate(ds) for e in loi_tieu_chi_con(x, f'tieu_chi_chi_tiet[{i}]', rb, ma_hop_le)]
    tinh_duoc = all(isinstance(x.get('tieu_chi'), int) and isinstance(x.get('diem'), (int, float)) for x in ds)
    return out + (loi_nhom(ds, rb) if tinh_duoc else []) + loi_do_phu(v, ds, rb, ma_hop_le)


def dong_tieu_chi(v, rb):
    """Các dòng bảng: dòng tiêu chí tổng quát, sau đó các tiêu chí chi tiết j.i."""
    rows = []
    for j, (w, m) in enumerate(zip(rb['trong_so'], rb['diem_toi_thieu']), 1):
        ten_tq = soan.get(f'TIEU_CHI_{j}', '')
        rows.append([str(j), ' '.join(ten_tq) if isinstance(ten_tq, list) else ten_tq, str(w), '', f'Tối thiểu {m} điểm'])
        for i, x in enumerate([x for x in v['tieu_chi_chi_tiet'] if x['tieu_chi'] == j], 1):
            cb = 'Không' if not x['co_ban'] else 'Có' + (f", tối thiểu {so_vn(x['diem_toi_thieu'])} điểm" if x.get('diem_toi_thieu') is not None else '')
            rows.append([f'{j}.{i}', [x['ten'], x['noi_dung']], so_vn(x['diem']), cb,
                         [f"{mc['muc']} ({so_vn(mc['diem'])} điểm): {mc['mo_ta']}" for mc in x['muc_cham']]])
    return rows


def dong_bang_dac_biet(k):
    """Dòng bảng cho ID dạng tieu_chi_chi_tiet. Ghi lỗi vào loi nếu bản soạn không đạt ràng buộc."""
    if k not in soan:
        return []
    e = kiem_tieu_chi(soan[k], can[k]['rang_buoc'])
    loi.extend(f'{k}: {x}' for x in e)
    return [] if e else dong_tieu_chi(soan[k], can[k]['rang_buoc'])


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
            if is_ph(r) and can.get(pid(r), {}).get('dang') == 'tieu_chi_chi_tiet':
                rows += dong_bang_dac_biet(pid(r))
                continue
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
