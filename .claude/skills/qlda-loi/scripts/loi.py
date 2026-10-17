"""Thư viện dùng chung của bộ skill quản lý dự án (qlda).

Mọi script khác import file này. Chức năng:
- tìm thư mục gốc của dự án, đọc sơ đồ phụ thuộc
- đọc, ghi JSON; băm nội dung tệp
- định dạng số, tiền, ngày, phần trăm theo kiểu Việt Nam
- tính biểu thức tham chiếu dữ liệu {bi_danh#duong_dan|dinh_dang}
- ghi nhật ký bằng chứng (bang_chung/nhat_ky_chay.jsonl) và lưu bản chụp prompt
- đăng ký phiên bản tài liệu (du_lieu/phien_ban.json)
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import datetime as _dt
import hashlib
import json
import os
import re
import sys

THU_MUC_LOI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_SKILLS = os.path.dirname(THU_MUC_LOI)


# ---------------------------------------------------------------- thư mục, tệp
def tim_goc():
    """Thư mục gốc dự án: biến môi trường QLDA_GOC, hoặc thư mục cha gần nhất có dau_vao/ hoặc .claude/."""
    if os.environ.get('QLDA_GOC'):
        return os.path.abspath(os.environ['QLDA_GOC'])
    for start in (os.getcwd(), THU_MUC_SKILLS):
        d = os.path.abspath(start)
        while True:
            if os.path.isdir(os.path.join(d, 'dau_vao')):
                return d
            p = os.path.dirname(d)
            if p == d:
                break
            d = p
    return os.getcwd()


GOC = tim_goc()


def duong_dan(p):
    return p if os.path.isabs(p) else os.path.join(GOC, p)


def tuong_doi(p):
    try:
        return os.path.relpath(os.path.abspath(p), GOC).replace('\\', '/')
    except ValueError:
        return p


def doc_json(p, mac_dinh=None):
    p = duong_dan(p)
    if not os.path.exists(p):
        if mac_dinh is not None:
            return mac_dinh
        raise FileNotFoundError('Không tìm thấy ' + tuong_doi(p))
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def ghi_json(p, obj):
    p = duong_dan(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def bam(p):
    p = duong_dan(p)
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    if os.path.isdir(p):
        for r, _, fs in sorted(os.walk(p)):
            for f in sorted(fs):
                with open(os.path.join(r, f), 'rb') as fh:
                    h.update(f.encode()); h.update(fh.read())
    else:
        with open(p, 'rb') as fh:
            h.update(fh.read())
    return h.hexdigest()[:12]


def bay_gio():
    return _dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def so_do():
    return doc_json(os.path.join(THU_MUC_LOI, 'references', 'so_do_phu_thuoc.json'))


def du_an():
    return doc_json('dau_vao/du_an.json')


# ---------------------------------------------------------------- định dạng
def so(v, le=0):
    """Số kiểu Việt Nam: 1.234.567 hoặc 1.234,5"""
    if v is None or v == '':
        return ''
    v = float(v)
    s = f'{abs(v):,.{le}f}'.replace(',', '#').replace('.', ',').replace('#', '.')
    return ('-' if v < 0 and abs(v) >= 0.5 * 10 ** (-le) else '') + s


def tien(v):
    return so(round(float(v)), 0)


def trieu(v, le=2):
    return so(float(v) / 1e6, le)


def md(v):
    v = float(v)
    return so(v, 0) if abs(v - round(v)) < 1e-9 else so(v, 2)


def pt(v, le=1):
    """Tỷ lệ sang phần trăm: 0,125 thành 12,5%. Trường đã là phần trăm (tên có phan_tram) dùng ptg."""
    s = so(float(v) * 100, le)
    if ',' in s:
        s = s.rstrip('0').rstrip(',')
    return s + '%'


def ptg(v, le=1):
    """Giá trị đã là phần trăm: 15 thành 15%."""
    s = so(float(v), le)
    if ',' in s:
        s = s.rstrip('0').rstrip(',')
    return s + '%'


def chon_dinh_dang(fmt, path):
    """Trường có tên chứa phan_tram đã là phần trăm, định dạng pt được hiểu là ptg."""
    if fmt == 'pt' and 'phan_tram' in str(path).split('.')[-1]:
        return 'ptg'
    return fmt


def ngay(v):
    """ISO yyyy-mm-dd hoặc date -> dd/mm/yyyy"""
    if not v:
        return ''
    if isinstance(v, (_dt.date, _dt.datetime)):
        d = v
    else:
        d = _dt.date.fromisoformat(str(v)[:10])
    return f'{d.day:02d}/{d.month:02d}/{d.year}'


DINH_DANG = {'tien': tien, 'trieu': trieu, 'md': md, 'pt': pt, 'ptg': ptg, 'ngay': ngay, 'so': lambda v: so(v, 0),
             'so1': lambda v: so(v, 1), 'so2': lambda v: so(v, 2), 'so3': lambda v: so(v, 3), 'nguyen': lambda v: str(int(round(float(v)))),
             'chu': lambda v: str(v)}


# ---------------------------------------------------------------- tham chiếu dữ liệu
def lay(obj, path):
    """Đi theo đường dẫn a.b[0].c, a[ma=3.1].md (lọc phần tử danh sách theo khóa)."""
    cur = obj
    if path in ('', None):
        return cur
    for part in re.findall(r'[^.\[\]]+|\[[^\]]*\]', path):
        if part.startswith('['):
            inner = part[1:-1]
            if '=' in inner:
                k, v = inner.split('=', 1)
                cur = next((x for x in cur if str(x.get(k)) == v), None)
            else:
                cur = cur[int(inner)]
        else:
            cur = cur[part] if isinstance(cur, dict) else None
        if cur is None:
            raise KeyError(path)
    return cur


MAU_THAM_CHIEU = re.compile(r'\{([a-z_0-9]+)#([^}|]*)(?:\|([a-z0-9]+))?\}')


def giai_bieu_thuc(text, nguon, loi_ra=None):
    """Thay {bi_danh#duong_dan|dinh_dang} bằng giá trị từ nguon (dict bí danh -> dữ liệu)."""
    def thay(m):
        bd, path, fmt = m.group(1), m.group(2), m.group(3)
        try:
            v = lay(nguon[bd], path)
        except Exception:
            if loi_ra is not None:
                loi_ra.append(m.group(0))
            return m.group(0)
        if fmt:
            return DINH_DANG[chon_dinh_dang(fmt, path)](v)
        if isinstance(v, float):
            return so(v, 2) if abs(v - round(v)) > 1e-9 else so(v, 0)
        return str(v)
    return MAU_THAM_CHIEU.sub(thay, text)


def nap_nguon(bi_danh):
    """bi_danh: dict alias -> đường dẫn tương đối. Tệp thiếu thì bỏ qua (khung sẽ báo)."""
    out = {}
    for k, p in bi_danh.items():
        try:
            out[k] = doc_json(p)
        except FileNotFoundError:
            pass
    return out


# ---------------------------------------------------------------- nhật ký bằng chứng
def ten_skill_tu_duong_dan(p):
    p = os.path.abspath(p)
    rel = os.path.relpath(p, THU_MUC_SKILLS)
    return rel.split(os.sep)[0] if not rel.startswith('..') else ''


def phien_ban_skill(ten):
    f = os.path.join(THU_MUC_SKILLS, ten, 'PHIEN_BAN')
    if os.path.exists(f):
        return open(f, encoding='utf-8').read().strip()
    return ''


def luu_prompt(prompt_path):
    """Chụp lại nội dung prompt đã dùng vào bang_chung/prompts/<ten>__<hash>.md, trả về (đường dẫn, hash)."""
    if not prompt_path:
        return None, None
    src = prompt_path if os.path.isabs(prompt_path) else (prompt_path if os.path.exists(prompt_path) else duong_dan(prompt_path))
    if not os.path.exists(src):
        return prompt_path, None
    h = bam(src)
    name = os.path.splitext(os.path.basename(src))[0]
    skill = ten_skill_tu_duong_dan(src)
    dst = duong_dan(f'bang_chung/prompts/{skill + "__" if skill else ""}{name}__{h}.md')
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(src, encoding='utf-8') as fi, open(dst, 'w', encoding='utf-8') as fo:
            fo.write(fi.read())
    return tuong_doi(dst), h


def ghi_nhat_ky(skill, buoc, loai, mo_ta, vao=(), ra=(), ket_qua='', prompt=None, chi_tiet=None):
    """loai: script | agent | nguoi_dung. vao, ra: danh sách đường dẫn (băm tự động)."""
    p_luu, p_hash = luu_prompt(prompt)
    rec = {
        'thoi_gian': bay_gio(), 'skill': skill, 'phien_ban_skill': phien_ban_skill(skill), 'buoc': buoc, 'loai': loai,
        'mo_ta': mo_ta, 'prompt': p_luu, 'prompt_hash': p_hash,
        'vao': [{'tep': tuong_doi(duong_dan(x)), 'hash': bam(x)} for x in vao],
        'ra': [{'tep': tuong_doi(duong_dan(x)), 'hash': bam(x)} for x in ra],
        'ket_qua': ket_qua, 'chi_tiet': chi_tiet or {},
    }
    p = duong_dan('bang_chung/nhat_ky_chay.jsonl')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    return rec


# ---------------------------------------------------------------- phiên bản
def _so_phien_ban():
    return doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})


def du_kien_phien_ban(tep, hash_noi_dung):
    """Phiên bản sẽ dùng nếu đăng ký nội dung có băm hash_noi_dung: giữ nguyên nếu không đổi, tăng 0.1 nếu đổi."""
    lst = _so_phien_ban()['tai_lieu'].get(tuong_doi(duong_dan(tep)), [])
    if lst and lst[-1]['hash'] == hash_noi_dung:
        return lst[-1]['phien_ban'], False
    if not lst:
        return '0.1', True
    major, minor = [int(x) for x in lst[-1]['phien_ban'].split('.')]
    return f'{major}.{minor + 1}', True


def bam_obj(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def dang_ky_phien_ban(buoc_id, tep, vao_ids, ghi_chu='', nguoi=None, trang_thai='Dự thảo', hash_noi_dung=None, them=None):
    """Ghi phiên bản cho một tệp đầu ra. Tăng số phiên bản khi nội dung đổi. Lưu băm đầu vào để phát hiện tài liệu cũ."""
    reg = _so_phien_ban()
    key = tuong_doi(duong_dan(tep))
    h = hash_noi_dung or bam(tep)
    lst = reg['tai_lieu'].setdefault(key, [])
    sd = so_do()
    vao = {i: bam_nut(sd, i) for i in vao_ids if duong_dan_nut(sd, i)}
    pb, moi = du_kien_phien_ban(tep, h)
    reg['dem'] = reg.get('dem', 0) + 1  # số thứ tự đăng ký, dùng để biết tệp được tạo trước hay sau một quyết định
    if not moi:
        lst[-1]['thu_tu_kiem_tra'] = reg['dem']
        lst[-1]['vao'] = vao
        lst[-1]['ngay_kiem_tra'] = bay_gio()
        lst[-1].update(them or {})
        ghi_json('du_lieu/phien_ban.json', reg)
        return pb
    try:
        nguoi = nguoi or du_an().get('nguoi_lap', '')
    except FileNotFoundError:
        nguoi = nguoi or ''
    lst.append({'phien_ban': pb, 'ngay': bay_gio(), 'nguoi': nguoi, 'buoc': buoc_id, 'hash': h, 'vao': vao,
                'ghi_chu': ghi_chu, 'trang_thai': trang_thai, 'thu_tu': reg['dem'], **(them or {})})
    ghi_json('du_lieu/phien_ban.json', reg)
    return pb


def hoan_tat_buoc(buoc_id, mo_ta, ghi_chu='', ket_qua='đạt', chi_tiet=None, bo_qua=(), hash_tep=None):
    """Gọi cuối mỗi script tạo đầu ra: đăng ký phiên bản mọi đầu ra đã có của bước và ghi nhật ký.
    hash_tep: {đường dẫn: băm nội dung} cho tệp nhị phân (xlsx, docx) để số phiên bản chỉ tăng khi nội dung đổi."""
    sd = so_do()
    b = next(x for x in sd['buoc'] if x['id'] == buoc_id)
    ra = [p for k, p in b['ra'].items() if os.path.exists(duong_dan(p)) and k not in bo_qua]
    pbs = {}
    for p in ra:
        if os.path.isdir(duong_dan(p)):
            continue
        h = (hash_tep or {}).get(p) or (bam_obj(doc_json(p)) if p.endswith('.json') else None)
        pbs[p] = dang_ky_phien_ban(buoc_id, p, b['vao'], ghi_chu, hash_noi_dung=h)
    vao = [duong_dan_nut(sd, i) for i in b['vao'] if duong_dan_nut(sd, i) and os.path.exists(duong_dan(duong_dan_nut(sd, i)))]
    ghi_nhat_ky(b['skill'], buoc_id, 'script', mo_ta, vao=vao, ra=ra, ket_qua=ket_qua, chi_tiet=dict(chi_tiet or {}, phien_ban=pbs))
    return pbs


def duong_dan_nut(sd, nut_id):
    if nut_id in sd['dau_vao']:
        return sd['dau_vao'][nut_id]['tep']
    for b in sd['buoc']:
        if nut_id in b.get('ra', {}):
            return b['ra'][nut_id]
    return None


def thoat_loi(msg, code=1):
    print('LỖI: ' + msg)
    sys.exit(code)


# ---------------------------------------------------------------- lịch làm việc
def ngay_lam_viec(da=None):
    """Danh sách ngày làm việc (date) từ ngay_bat_dau đến trước ngày cut over, trừ thứ Bảy, Chủ nhật và ngày nghỉ."""
    da = da or du_an()
    d0 = _dt.date.fromisoformat(da['ngay_bat_dau'])
    d1 = _dt.date.fromisoformat(da['ngay_cut_over'])
    nghi = {_dt.date.fromisoformat(x) for x in da.get('ngay_nghi', [])}
    out, d = [], d0
    while d <= d1:
        if d.weekday() < 5 and d not in nghi:
            out.append(d)
        d += _dt.timedelta(days=1)
    if da.get('cut_over_la_ngay_lam_viec', True) is False and out and out[-1] == d1:
        out.pop()
    return out


def danh_sach_sprint(da=None):
    """[{ma, so, tu, den, so_ngay, chi_so_dau, chi_so_cuoi}] theo du_an.sprint."""
    da = da or du_an()
    days = ngay_lam_viec(da)
    cfg = da.get('sprint', {})
    n = int(cfg.get('so_ngay_lam_viec', 10))
    tt = cfg.get('tien_to', 'S')
    k = len(days) // n
    du = len(days) - k * n
    sp, i = [], 0
    for s in range(k):
        size = n + (du if (s == k - 1 and cfg.get('gop_phan_du_vao_sprint_cuoi', True)) else 0)
        sp.append({'ma': f'{tt}{s + 1}', 'so': s + 1, 'tu': days[i].isoformat(), 'den': days[i + size - 1].isoformat(),
                   'so_ngay': size, 'chi_so_dau': i, 'chi_so_cuoi': i + size - 1})
        i += size
    if i < len(days):
        sp.append({'ma': f'{tt}{len(sp) + 1}', 'so': len(sp) + 1, 'tu': days[i].isoformat(), 'den': days[-1].isoformat(),
                   'so_ngay': len(days) - i, 'chi_so_dau': i, 'chi_so_cuoi': len(days) - 1})
    return sp


def sprint_cua_chi_so(sprints, i):
    for s in sprints:
        if s['chi_so_dau'] <= i <= s['chi_so_cuoi']:
            return s['ma']
    return None


def quy_thoi_gian(tv, sprints):
    """MD khả dụng của một người trong từng sprint (theo ty_le, tu_sprint, den_sprint)."""
    out = {}
    for s in sprints:
        ok = (tv.get('tu_sprint') in (None, '') or s['so'] >= int(tv['tu_sprint'])) and \
             (tv.get('den_sprint') in (None, '') or s['so'] <= int(tv['den_sprint']))
        out[s['ma']] = round(s['so_ngay'] * float(tv.get('ty_le', 1.0)), 2) if ok else 0.0
    return out


def nut_wbs(wbs):
    """Từ điển mã -> mục, danh sách mục lá (không có mục con)."""
    goi = wbs['goi']
    by = {g['ma']: g for g in goi}
    co_con = {g['ma'].rsplit('.', 1)[0] for g in goi if '.' in g['ma']}
    la = [g for g in goi if g['ma'] not in co_con]
    return by, la


def khoa_ma(ma):
    return [int(x) if x.isdigit() else x for x in str(ma).split('.')]


# Dữ liệu thực tế (CSV trong dau_vao/thuc_te)
def doc_csv(p):
    import csv
    p = duong_dan(p)
    if not os.path.exists(p):
        return []
    with open(p, encoding='utf-8-sig') as f:
        return [{k.strip(): (v or '').strip() for k, v in r.items() if k} for r in csv.DictReader(f) if any((v or '').strip() for v in r.values())]


TRANG_THAI_RUI_RO = ('Đang theo dõi', 'Đã kích hoạt ứng phó', 'Đã xảy ra', 'Đã đóng')


def theo_doi_rui_ro(den=None):
    """Trạng thái mới nhất của từng rủi ro theo dau_vao/thuc_te/theo_doi_rui_ro.csv, đến ngày den (yyyy-mm-dd).
    Trả về (trang_thai_moi_nhat theo mã, danh sách sự kiện đã sắp theo ngày)."""
    ds = sorted(doc_csv('dau_vao/thuc_te/theo_doi_rui_ro.csv'), key=lambda r: r.get('ngay', ''))
    if den:
        ds = [r for r in ds if r.get('ngay', '') <= str(den)]
    moi = {}
    for r in ds:
        moi[r['ma_rui_ro']] = r
    return moi, ds


def don_gia_ngay_vai_tro(dg, vai_tro):
    """Đơn giá lương ngày của vai trò: lương tham chiếu tháng chia số ngày làm việc mỗi tháng (don_gia.json)."""
    v = dg['luong_tham_chieu_thang'].get(vai_tro)
    if not v:
        return None
    return float(v['luong']) / float(dg.get('ngay_lam_viec_moi_thang', 22))


def ngay_lam_viec_giua(days, a, b):
    """Số ngày làm việc từ a đến b (b sau a thì dương, trước a thì âm), days là danh sách ngày làm việc."""
    import datetime as _dt
    a = _dt.date.fromisoformat(str(a)[:10]); b = _dt.date.fromisoformat(str(b)[:10])
    if a == b:
        return 0
    s = 1 if b > a else -1
    lo, hi = min(a, b), max(a, b)
    n = sum(1 for d in days if lo < d <= hi)
    if n == 0:  # ngoài lịch dự án: đếm thứ hai đến thứ sáu
        n = sum(1 for i in range(1, (hi - lo).days + 1) if (lo + _dt.timedelta(days=i)).weekday() < 5)
    return s * n


def lam_tron_tong(gia_tri, le=2):
    """Làm tròn từng phần sao cho tổng các phần bằng tổng đã làm tròn (phương pháp phần dư lớn nhất)."""
    k = 10 ** le
    tong = round(sum(gia_tri) * k)
    san = [int(v * k // 1) for v in gia_tri]
    du = sorted(range(len(gia_tri)), key=lambda i: -(gia_tri[i] * k - san[i]))
    for i in du[:max(0, tong - sum(san))]:
        san[i] += 1
    return [x / k for x in san]


def nut_bien_dong(sd=None):
    """Nút đầu vào thay đổi liên tục (sổ phiên bản, nhật ký), không dùng để xét tài liệu cũ."""
    sd = sd or so_do()
    return {k for k, v in sd['dau_vao'].items() if v.get('bien_dong')}


def da_ky_hop_dong():
    """Hợp đồng đã ký khi đã lập đường cơ sở hợp đồng (so_phien_ban.py duong_co_so ... --hop-dong)."""
    return bool(doc_json('du_lieu/phien_ban.json', {}).get('hop_dong'))


def so_bang_chu(n):
    """Số nguyên sang chữ tiếng Việt: 30000000 thành Ba mươi triệu đồng chẵn (không kèm đơn vị)."""
    n = int(round(float(n)))
    if n == 0:
        return 'Không'
    cs = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín']

    def ba_so(x, day_du):
        tr, ch, dv = x // 100, x // 10 % 10, x % 10
        out = []
        if day_du or tr:
            out += [cs[tr], 'trăm']
        if ch == 0 and dv and (day_du or tr):
            out.append('lẻ')
        elif ch == 1:
            out.append('mười')
        elif ch > 1:
            out += [cs[ch], 'mươi']
        if dv:
            if dv == 1 and ch > 1:
                out.append('mốt')
            elif dv == 5 and ch > 0:
                out.append('lăm')
            elif dv == 4 and ch > 1:
                out.append('tư')
            else:
                out.append(cs[dv])
        return out
    don_vi = ['', 'nghìn', 'triệu', 'tỷ']
    nhom = []
    while n:
        nhom.append(n % 1000); n //= 1000
    out = []
    for i in range(len(nhom) - 1, -1, -1):
        if nhom[i] == 0:
            if i % 3 == 0 and i > 0 and len(out) and out[-1] != 'tỷ' and i == 3:
                out.append('tỷ')
            continue
        out += ba_so(nhom[i], day_du=(i < len(nhom) - 1))
        if i:
            out.append(don_vi[i % 3] if i % 3 else ('tỷ' if i == 3 else 'tỷ'))
    s = ' '.join(out)
    return s[0].upper() + s[1:]


DINH_DANG['chu'] = lambda v: so_bang_chu(v) if isinstance(v, (int, float)) or str(v).replace('.', '').isdigit() else str(v)


def bam_nut(sd, nut):
    """Băm của một nút đầu vào. Tệp Word đã đăng ký dùng băm nội dung trong sổ phiên bản, nên dựng lại tệp
    chỉ để đổi số phiên bản trên bìa (khi lập đường cơ sở) không làm các tài liệu sau bị coi là cũ."""
    p = duong_dan_nut(sd, nut)
    if not p:
        return None
    if p.endswith('.docx') and os.path.isfile(duong_dan(p)):
        lst = _so_phien_ban()['tai_lieu'].get(tuong_doi(duong_dan(p)))
        if lst:
            return 'nd:' + lst[-1]['hash']
    return bam(p)


def dinh_dang_cot(vals, f):
    """Định dạng cả cột với cùng số chữ số thập phân (MD, phần trăm)."""
    if f not in ('md', 'pt', 'ptg'):
        return None
    try:
        so_ = [float(v) for v in vals if v not in (None, '')]
    except (TypeError, ValueError):
        return None
    if f == 'md':
        le = 2 if any(abs(v - round(v)) > 1e-9 for v in so_) else 0
        return ['' if v in (None, '') else so(float(v), le) for v in vals]
    if f in ('pt', 'ptg'):
        nhan = 100 if f == 'pt' else 1
        le = 1 if any(abs(v * nhan - round(v * nhan)) > 1e-6 for v in so_) else 0
        return ['' if v in (None, '') else so(float(v) * nhan, le) + '%' for v in vals]
    return None


def _bao_loi_thieu_tep(t, e, tb):
    """Thiếu tệp đầu vào: báo ngắn gọn thay cho traceback, kèm gợi ý xem trạng thái."""
    if issubclass(t, FileNotFoundError):
        print(f'LỖI: {e}. Xem bước cần làm trước: python .claude/skills/qlda-loi/scripts/chay.py trang_thai', file=sys.stderr)
        return
    sys.__excepthook__(t, e, tb)


sys.excepthook = _bao_loi_thieu_tep
