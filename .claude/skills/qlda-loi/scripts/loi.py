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


TIEN_TO_SKILL = 'skill:'  # tệp tham chiếu tĩnh của skill, ví dụ skill:qlda-change/references/phan_loai.json


# Kế hoạch của một kỳ đã qua (từ 1.6.3): đặt QLDA_KE_HOACH_KY=S<n> khi lập lại báo cáo tiến độ một kỳ cũ sau khi kế hoạch đã đổi (yêu cầu thay
# đổi, đường cơ sở mới). Các tệp kế hoạch dưới đây được đọc từ bản chụp lam_viec/mo_phong/ke_hoach_S<n>/<đường dẫn> do mo_phong_sprint.py lưu khi
# sinh kỳ đó (thiếu bản chụp của tệp nào thì đọc tệp hiện hành). Chỉ dùng cho bước đọc (tinh_tien_do.py, chay.py chuan_bi, hoan_thien báo cáo tiến độ).
TEP_KE_HOACH_KY = ('du_lieu/lich.json', 'du_lieu/wbs.json', 'du_lieu/chi_phi.json', 'du_lieu/rui_ro.json', 'du_lieu/phan_cong.json',
                   'dau_vao/du_an.json', 'dau_vao/don_gia.json', 'dau_vao/thanh_vien.json')
THU_MUC_KE_HOACH_KY = 'lam_viec/mo_phong/ke_hoach_{ky}'


def duong_dan(p):
    if p.startswith(TIEN_TO_SKILL):
        return os.path.join(THU_MUC_SKILLS, p[len(TIEN_TO_SKILL):])
    ky = os.environ.get('QLDA_KE_HOACH_KY')
    if ky and not os.path.isabs(p) and p.replace('\\', '/') in TEP_KE_HOACH_KY:
        q = os.path.join(GOC, THU_MUC_KE_HOACH_KY.format(ky=ky), p)
        if os.path.exists(q):
            return q
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
        obj = json.load(f)
    if tuong_doi(p).endswith('dau_vao/du_an.json') and isinstance(obj, dict):
        obj = gan_don_vi_thuc_hien(obj)
    return obj


def gan_don_vi_thuc_hien(da):
    """Tên đơn vị thực hiện lấy từ nha_thau.json (ten_viet_tat, rồi ten) để đổi nhà thầu chỉ cần sửa một tệp."""
    p = duong_dan('dau_vao/nha_thau.json')
    if not os.path.exists(p):
        return da
    with open(p, encoding='utf-8') as f:
        nt = json.load(f)
    ten = nt.get('ten_viet_tat') or nt.get('ten')
    return dict(da, don_vi_thuc_hien=ten) if ten else da


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
    """Số tiền kiểu Việt Nam. Số âm viết chữ "âm" trước số (âm 296.981.818), theo references/van_phong.md."""
    v = round(float(v))
    return ('âm ' if v < 0 else '') + so(abs(v), 0)


def trieu(v, le=2):
    v = float(v) / 1e6
    s = so(abs(v), le)
    return ('âm ' if v < 0 and s.strip('0,.') else '') + s


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
             'chu': lambda v: str(v), 'pt1': lambda v: so(float(v) * 100, 1) + '%', 'md2': lambda v: so(v, 2),
             'dem': lambda v: str(len(v)) if isinstance(v, (list, tuple, dict)) else ('0' if v in (None, '') else '1')}


# ---------------------------------------------------------------- tham chiếu dữ liệu
TACH_DUONG_DAN = re.compile(r"\[\s*'[^']*'\s*\]|\[\s*\"[^\"]*\"\s*\]|[^.\[\]]+|\[[^\]]*\]")


def _buoc_ngoac(cur, inner):
    """Một bước trong ngoặc vuông: ['khóa có dấu chấm'], [?k=v] (mọi phần tử khớp), [k=v] (phần tử đầu khớp), [số]."""
    if inner[:1] in ('"', "'"):
        return cur.get(inner[1:-1]) if isinstance(cur, dict) else None
    if inner.startswith('?') and '=' in inner:
        k, v = inner[1:].split('=', 1)
        return [x for x in cur if isinstance(x, dict) and str(x.get(k)) == v]
    if '=' in inner:
        k, v = inner.split('=', 1)
        return next((x for x in cur if isinstance(x, dict) and str(x.get(k)) == v), None)
    return cur[int(inner)]


def _buoc_khoa(cur, part):
    """Một bước theo khóa. Gặp danh sách thì lấy khóa đó ở mọi phần tử (a.ds.ma ra danh sách mã)."""
    if isinstance(cur, dict):
        return cur.get(part)
    if isinstance(cur, list):
        ds = [x[part] for x in cur if isinstance(x, dict) and part in x]
        return ds if ds or not cur else None
    return None


def lay(obj, path):
    """Đi theo đường dẫn a.b[0].c, a[ma=3.1].md (phần tử đầu khớp), a[?muc=cao] (mọi phần tử khớp),
    a['8.3.2'] hoặc a["E-ĐKC 17.4"] (khóa có dấu chấm), a.ds.ma (lấy khóa ở mọi phần tử của danh sách)."""
    cur = obj
    if path in ('', None):
        return cur
    for part in TACH_DUONG_DAN.findall(path):
        cur = _buoc_ngoac(cur, part[1:-1].strip()) if part.startswith('[') else _buoc_khoa(cur, part)
        if cur is None:
            raise KeyError(path)
    return cur


MAU_THAM_CHIEU = re.compile(r'\{([a-z_0-9]+)#([^}|]*)(?:\|([a-z0-9]+))?\}')


def _chuoi_gia_tri(v, fmt, path):
    """Giá trị đơn sang chuỗi theo định dạng. Phần tử là đối tượng thì dùng mã (ma) hoặc tên (ten)."""
    if isinstance(v, dict):
        v = v.get('ma', v.get('ten', ''))
    if fmt:
        return DINH_DANG[chon_dinh_dang(fmt, path)](v)
    if isinstance(v, float):
        return so(v, 2) if abs(v - round(v)) > 1e-9 else so(v, 0)
    return str(v)


def gia_tri_chuoi(v, fmt=None, path=''):
    """Giá trị tham chiếu sang chuỗi: danh sách in thành chuỗi phân cách bằng dấu phẩy, |dem in số phần tử."""
    if fmt == 'dem':
        return DINH_DANG['dem'](v)
    if isinstance(v, (list, tuple)):
        return ', '.join(_chuoi_gia_tri(x, fmt, path) for x in v if x not in (None, ''))
    return _chuoi_gia_tri(v, fmt, path)


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
        return gia_tri_chuoi(v, fmt, path)
    return MAU_THAM_CHIEU.sub(thay, text)


# ---------------------------------------------------------------- dấu giữ chỗ, biểu mẫu
MAU_NGOAC_VUONG = re.compile(r'\[([^\[\]]*)\]')


def la_giu_cho(s):
    """Chuỗi có dấu giữ chỗ trong ngoặc vuông chứa chữ hoặc dấu ba chấm, ví dụ [Nhóm bổ sung ...], [...], [ghi tên]."""
    if not isinstance(s, str):
        return False
    for m in MAU_NGOAC_VUONG.finditer(s):
        inner = m.group(1)
        if not inner.strip() or re.search(r'[^\W\d_]|\.\.\.|…', inner):
            return True
    return False


def la_gia_tri_thieu(v):
    """Giá trị coi là thiếu: None, chuỗi rỗng, chỉ có dấu câu, hoặc dấu giữ chỗ."""
    if v is None:
        return True
    if isinstance(v, str):
        return not re.sub(r'[\W_]', '', v) or la_giu_cho(v)
    return False


def chuan_hoa_tieu_de(s):
    """Tiêu đề cột để so sánh: bỏ chú thích (1), gộp khoảng trắng, bỏ khoảng trắng quanh dấu /, chữ thường."""
    s = re.sub(r'\(\d+\)', '', str(s))
    s = re.sub(r'\s*/\s*', '/', re.sub(r'\s+', ' ', s)).strip()
    return s.lower()


def _dong_tieu_de(tbl):
    """Dòng tiêu đề của bảng biểu mẫu: dòng đầu tiên có từ 3 ô khác nhau (ô gộp chỉ tính một lần)."""
    for r in tbl.rows:
        o = []
        for c in r.cells:
            t = re.sub(r'\s+', ' ', c.text).strip()
            if t and (not o or o[-1] != t):
                o.append(t)
        if len(o) >= 3:
            return o
    return None


_BIEU_MAU = {}


def cot_bieu_mau(tep, mau_so):
    """Tiêu đề cột bảng của Mẫu số <mau_so> trong tệp mẫu (dau_vao/Mau_5A.docx), đọc ở bảng đầu tiên có dòng
    tiêu đề sau dòng "Mẫu số ...". Trả về danh sách tiêu đề, hoặc None khi không tìm thấy biểu mẫu hay bảng."""
    p = duong_dan(tep)
    if p not in _BIEU_MAU:
        import docx
        from docx.table import Table
        from docx.text.paragraph import Paragraph
        d = docx.Document(p)
        out, mau = {}, None
        for el in d.element.body.iterchildren():
            tag = el.tag.split('}')[-1]
            if tag == 'p':
                m = re.match(r'Mẫu số (\w+)', Paragraph(el, d).text.strip())
                mau = m.group(1) if m else mau
            elif tag == 'tbl' and mau and mau not in out:
                cot = _dong_tieu_de(Table(el, d))
                if cot:
                    out[mau] = cot
        _BIEU_MAU[p] = out
    return _BIEU_MAU[p].get(mau_so)


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


# khóa của bản ghi phiên bản không bị ghi đè khi đăng ký lại cùng nội dung (giữ nguyên bản ghi đường cơ sở, bản phát hành)
KHOA_PHIEN_BAN_GIU = ('phien_ban', 'ngay', 'nguoi', 'buoc', 'hash', 'trang_thai', 'thu_tu', 'ghi_chu', 'duong_co_so', 'phat_hanh',
                      'vao_duong_co_so', 'lich_su_trang_thai')


def dang_ky_phien_ban(buoc_id, tep, vao_ids, ghi_chu='', nguoi=None, trang_thai='Dự thảo', hash_noi_dung=None, them=None):
    """Ghi phiên bản cho một tệp đầu ra. Tăng số phiên bản khi nội dung đổi. Lưu băm đầu vào để phát hiện tài liệu cũ.
    Sau ký hợp đồng (giai đoạn thực hiện), phiên bản mới ghi khóa phat_hanh: bản phát hành hiện hành tại ngày tài liệu
    (them.ngay_tai_lieu, không có thì ngày hiện hành, xem ngay_hien_hanh), rỗng khi chưa có bản phát hành."""
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
        lst[-1].update({k: v for k, v in (them or {}).items() if k not in KHOA_PHIEN_BAN_GIU})
        ghi_json('du_lieu/phien_ban.json', reg)
        return pb
    if reg.get('hop_dong') and key.startswith('ket_qua/') and not (them or {}).get('ngay_tai_lieu'):
        them = dict(them or {}, ngay_tai_lieu=ngay(ngay_hien_hanh()))  # tệp không có ngày trên bìa (Excel): ngày hiện hành của dự án
    if reg.get('hop_dong') and 'phat_hanh' not in (them or {}):
        them = dict(them or {}, phat_hanh=ban_phat_hanh_hien_hanh((them or {}).get('ngay_tai_lieu')))
    ma_cr = cr_dang_ap_dung(buoc_id, reg) if reg.get('hop_dong') and 'ma_cr' not in (them or {}) else ''
    if ma_cr:  # phiên bản tạo do yêu cầu thay đổi đang áp dụng: gắn mã CR (quy ước 2.1 của qlda-phien-ban)
        them = dict(them or {}, ma_cr=ma_cr)
        ghi_chu = ghi_chu if ma_cr in str(ghi_chu) else (f'{ma_cr}. {ghi_chu}' if ghi_chu else ma_cr)
    try:
        nguoi = nguoi or du_an().get('nguoi_lap', '')
    except FileNotFoundError:
        nguoi = nguoi or ''
    lst.append({'phien_ban': pb, 'ngay': bay_gio(), 'nguoi': nguoi, 'buoc': buoc_id, 'hash': h, 'vao': vao,
                'ghi_chu': ghi_chu, 'trang_thai': trang_thai, 'thu_tu': reg['dem'], **(them or {})})
    ghi_json('du_lieu/phien_ban.json', reg)
    return pb


def cr_dang_ap_dung(buoc_id, reg=None):
    """Mã yêu cầu thay đổi đang áp dụng mà bước buoc_id thuộc danh sách tài liệu phải cập nhật: CR đã phê duyệt, đã ghi áp dụng vào
    dữ liệu nguồn, chưa đóng (bản sửa sau đường cơ sở sau thay đổi vẫn gắn mã CR). Không có thì trả ''."""
    for c in doc_json('du_lieu/thay_doi.json', {'yeu_cau': []}).get('yeu_cau', []):
        if c.get('trang_thai') in ('Đã phê duyệt', 'Đã thực hiện') and (c.get('ap_dung') or {}).get('da_ghi') \
                and buoc_id in {x.split(' ')[0] for x in c.get('tai_lieu_cap_nhat', [])}:
            return c['ma']
    return ''


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
    """[{ma, so, tu, den, so_ngay, chi_so_dau, chi_so_cuoi}] theo du_an.sprint.
    Khi cut over lùi theo phụ lục (du_an.sprint.cut_over_goc sớm hơn ngay_cut_over): các sprint đến cut over gốc giữ nguyên như lập
    ban đầu (kể cả sprint_nhan_phan_du), phần ngày thêm chia thành sprint mới theo so_ngay_lam_viec, phần dư dồn vào sprint cuối mới."""
    da = da or du_an()
    goc = (da.get('sprint') or {}).get('cut_over_goc')
    if goc and str(goc) < str(da['ngay_cut_over']):
        return _sprint_keo_dai(da, goc)
    return _chia_sprint(da)


def _sprint_keo_dai(da, goc):
    sp = _chia_sprint(dict(da, ngay_cut_over=goc))
    days = ngay_lam_viec(da)
    cfg = da.get('sprint', {})
    n, tt = int(cfg.get('so_ngay_lam_viec', 10)), cfg.get('tien_to', 'S')
    i = sp[-1]['chi_so_cuoi'] + 1 if sp else 0
    con = len(days) - i
    k = max(1, con // n) if con > 0 else 0
    for s in range(k):
        size = n if s < k - 1 else con - n * (k - 1)
        so_ = len(sp) + 1
        sp.append({'ma': f'{tt}{so_}', 'so': so_, 'tu': days[i].isoformat(), 'den': days[i + size - 1].isoformat(),
                   'so_ngay': size, 'chi_so_dau': i, 'chi_so_cuoi': i + size - 1, 'keo_dai': True})
        i += size
    return sp


def _chia_sprint(da):
    """Chia ngày làm việc từ ngay_bat_dau đến ngay_cut_over thành sprint theo du_an.sprint."""
    days = ngay_lam_viec(da)
    cfg = da.get('sprint', {})
    n = int(cfg.get('so_ngay_lam_viec', 10))
    tt = cfg.get('tien_to', 'S')
    k = len(days) // n
    du = len(days) - k * n
    nhan = cfg.get('sprint_nhan_phan_du')  # số thứ tự sprint nhận phần ngày dư; trống thì theo gop_phan_du_vao_sprint_cuoi
    if nhan is None:
        nhan = k if cfg.get('gop_phan_du_vao_sprint_cuoi', True) else None
    elif not (isinstance(nhan, int) and 1 <= nhan <= k):
        thoat_loi(f'du_an.json sprint.sprint_nhan_phan_du = {nhan!r} phải là số nguyên từ 1 đến {k}')
    sp, i = [], 0
    for s in range(k):
        size = n + (du if nhan is not None and s + 1 == int(nhan) else 0)
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
    """MD khả dụng của một người trong từng sprint (theo ty_le, tu_sprint, den_sprint).
    ty_le_theo_sprint {mã sprint: tỷ lệ} (từ 1.6.2): huy động theo nhu cầu của từng sprint, thay ty_le khi tính quỹ của sprint đó. Chỉ đổi quỹ
    huy động, không đổi tốc độ xếp lịch (lap_lich.py báo L06 khi MD xếp vượt quỹ của sprint)."""
    out = {}
    tl_sp = tv.get('ty_le_theo_sprint') or {}
    for s in sprints:
        ok = (tv.get('tu_sprint') in (None, '') or s['so'] >= int(tv['tu_sprint'])) and \
             (tv.get('den_sprint') in (None, '') or s['so'] <= int(tv['den_sprint']))
        out[s['ma']] = round(s['so_ngay'] * float(tl_sp.get(s['ma'], tv.get('ty_le', 1.0))), 2) if ok else 0.0
    if tv.get('huy_dong_ket_thuc'):  # quỹ giai đoạn Kết thúc sau cut over (kỳ KT), cùng cơ sở với lap_lich.py (từ 1.6.3)
        out['KT'] = round(giai_doan_du_an()[0]['ket_thuc']['so_ngay'] * float(tv['huy_dong_ket_thuc']), 2)
    return out


# ---------------------------------------------------------------- giai đoạn dự án
GIAI_DOAN = {'khoi_dong': 'Khởi động', 'thuc_hien': 'Thực hiện', 'xuyen_suot': 'Suốt dự án', 'ket_thuc': 'Kết thúc'}
THU_TU_GIAI_DOAN = ('khoi_dong', 'xuyen_suot', 'thuc_hien', 'ket_thuc')
TEN_MUC_QUAN_LY = 'quản lý dự án'  # mục WBS có mục con, tên bắt đầu bằng cụm này (không phân biệt hoa thường) là mục quản lý dự án
LOAI_PM = 'PM'  # gói lá loại PM ngoài mục quản lý dự án vẫn là gói quản lý dự án (không gắn sprint phát triển)
LOAI_QUAN_LY = ('PM', 'QA')  # loại công việc quản lý dự án (lập kế hoạch, giám sát, bảo đảm chất lượng)
SO_NGAY_KHOI_DONG_MAC_DINH = 5  # ngày làm việc đầu dự án khi du_an.json chưa khai báo giai_doan.khoi_dong
SO_NGAY_KET_THUC_MAC_DINH = 10  # ngày làm việc sau cut over khi du_an.json chưa khai báo giai_doan.ket_thuc


def ngay_iso(v):
    """Ngày dạng yyyy-mm-dd từ yyyy-mm-dd, dd/mm/yyyy hoặc date. Trả về '' khi không đọc được."""
    if not v:
        return ''
    if isinstance(v, (_dt.date, _dt.datetime)):
        return v.isoformat()[:10]
    s = str(v).strip()
    try:
        return _dt.date.fromisoformat(s[:10]).isoformat()
    except ValueError:
        pass
    try:
        return _dt.datetime.strptime(s[:10], '%d/%m/%Y').date().isoformat()
    except ValueError:
        return ''


def ngay_hien_hanh():
    """Ngày hiện hành (yyyy-mm-dd): biến môi trường QLDA_NGAY khi mô phỏng dự án, không có thì ngày máy."""
    return ngay_iso(os.environ.get('QLDA_NGAY')) or bay_gio()[:10]


def ngay_lam_viec_sau(da, ngay_goc, so_ngay):
    """so_ngay ngày làm việc liền sau ngay_goc (date), trừ thứ Bảy, Chủ nhật và ngày nghỉ của du_an.json."""
    nghi = {_dt.date.fromisoformat(x) for x in da.get('ngay_nghi', [])}
    out, d = [], ngay_goc
    while len(out) < so_ngay:
        d += _dt.timedelta(days=1)
        if d.weekday() < 5 and d not in nghi:
            out.append(d)
    return out


def giai_doan_du_an(da=None):
    """Lịch giai đoạn theo du_an.giai_doan {khoi_dong: {tu, den}, ket_thuc: {so_ngay_lam_viec}}.
    Thiếu khóa thì mặc định: Khởi động là SO_NGAY_KHOI_DONG_MAC_DINH ngày làm việc đầu, Kết thúc là SO_NGAY_KET_THUC_MAC_DINH
    ngày làm việc sau cut over. Thực hiện từ ngày bắt đầu đến cut over (các sprint).
    Trả về ({khoi_dong, thuc_hien, ket_thuc: {ma, ten, tu, den, so_ngay, mac_dinh}}, danh sách lỗi khai báo)."""
    da = da or du_an()
    days = ngay_lam_viec(da)
    cfg = da.get('giai_doan') or {}
    loi_ = []
    kd = cfg.get('khoi_dong') or {}
    kd_tu = ngay_iso(kd.get('tu')) or days[0].isoformat()
    kd_den = ngay_iso(kd.get('den')) or days[min(SO_NGAY_KHOI_DONG_MAC_DINH, len(days)) - 1].isoformat()
    if not (days[0].isoformat() <= kd_tu <= kd_den <= days[-1].isoformat()):
        loi_.append(f'giai_doan.khoi_dong {kd_tu} đến {kd_den} phải nằm trong {days[0].isoformat()} đến cut over {days[-1].isoformat()}, ngày bắt đầu không sau ngày kết thúc')
    kt = cfg.get('ket_thuc') or {}
    so_kt = kt.get('so_ngay_lam_viec', SO_NGAY_KET_THUC_MAC_DINH)
    if not (isinstance(so_kt, int) and so_kt > 0):
        loi_.append(f'giai_doan.ket_thuc.so_ngay_lam_viec = {so_kt!r} phải là số nguyên dương')
        so_kt = SO_NGAY_KET_THUC_MAC_DINH
    ds_kt = ngay_lam_viec_sau(da, days[-1], so_kt)
    so_kd = sum(1 for d in days if kd_tu <= d.isoformat() <= kd_den)
    gd = {'khoi_dong': {'tu': kd_tu, 'den': kd_den, 'so_ngay': so_kd, 'mac_dinh': not (kd.get('tu') and kd.get('den'))},
          'thuc_hien': {'tu': days[0].isoformat(), 'den': days[-1].isoformat(), 'so_ngay': len(days), 'mac_dinh': False},
          'ket_thuc': {'tu': ds_kt[0].isoformat(), 'den': ds_kt[-1].isoformat(), 'so_ngay': so_kt, 'mac_dinh': 'so_ngay_lam_viec' not in kt}}
    return {k: dict(v, ma=k, ten=GIAI_DOAN[k]) for k, v in gd.items()}, loi_


def muc_quan_ly_du_an(goi):
    """Mã các mục WBS quản lý dự án: mục có mục con, tên bắt đầu bằng TEN_MUC_QUAN_LY. Mục này có thể là một nhóm mức 1 riêng
    hoặc mục mức 2 trong từng nhóm (phần quản lý dự án phân bổ cho phân hệ). Không dựa vào số thứ tự nhóm."""
    co_con = {str(g.get('ma', '')).rsplit('.', 1)[0] for g in goi if '.' in str(g.get('ma', ''))}
    return {str(g.get('ma', '')) for g in goi if str(g.get('ma', '')) in co_con
            and str(g.get('ten', '')).strip().lower().startswith(TEN_MUC_QUAN_LY)}


def goi_quan_ly_du_an(goi):
    """Mã gói lá quản lý dự án: thuộc một mục quản lý dự án (muc_quan_ly_du_an) hoặc có loại công việc LOAI_PM.
    Các gói này không gắn sprint phát triển, nên ghi giai_doan tường minh (khoi_dong, xuyen_suot, ket_thuc)."""
    co_con = {str(g.get('ma', '')).rsplit('.', 1)[0] for g in goi if '.' in str(g.get('ma', ''))}
    ql = muc_quan_ly_du_an(goi)
    return {str(g.get('ma', '')) for g in goi if str(g.get('ma', '')) not in co_con
            and (g.get('loai') == LOAI_PM or any(str(g.get('ma', '')).startswith(m + '.') for m in ql))}


def phan_giai_doan(wbs, giao_viec=None):
    """Giai đoạn của từng gói lá: {mã: khoi_dong | thuc_hien | xuyen_suot | ket_thuc}.
    Gói lá ghi giai_doan trong WBS thì dùng giá trị đó (nên ghi tường minh cho mọi gói quản lý dự án). Không ghi thì suy ra:
    gói không phải gói quản lý dự án (goi_quan_ly_du_an: thuộc mục tên bắt đầu bằng Quản lý dự án hoặc loại PM) là Thực hiện;
    gói quản lý dự án dàn trải (giao_viec dan_trai) là Suốt dự án; trong một mục quản lý dự án có các mục con nhiều cấp
    (ví dụ nhóm mức 1 Quản lý dự án), gói thuộc mục con đầu là Khởi động, gói lá cuối của mục con cuối là Kết thúc;
    còn lại Suốt dự án. Quy tắc không dựa vào số thứ tự nhóm WBS. Giá trị ghi sai trả về nguyên văn để bước kiểm tra báo lỗi."""
    gv = {x['ma']: x for x in (giao_viec or [])}
    by, la = nut_wbs(wbs)
    ql_goi = goi_quan_ly_du_an(wbs['goi'])
    muc_ql = muc_quan_ly_du_an(wbs['goi'])
    co_con = {m.rsplit('.', 1)[0] for m in by if '.' in m}
    dau, cuoi = set(), set()  # mục con đầu (Khởi động) và gói lá cuối của mục con cuối (Kết thúc) của mục quản lý nhiều cấp
    for m in muc_ql:
        con = sorted((c for c in by if c.rsplit('.', 1)[0] == m and '.' in c and c in co_con), key=khoa_ma)
        if len(con) > 1:
            dau.add(con[0])
            cuoi.add(max((g['ma'] for g in la if g['ma'].startswith(con[-1] + '.')), key=khoa_ma, default=''))
    out = {}
    for g in la:
        if g.get('giai_doan'):
            out[g['ma']] = g['giai_doan']; continue
        if g['ma'] not in ql_goi:
            out[g['ma']] = 'thuc_hien'; continue
        if gv.get(g['ma'], {}).get('dan_trai'):
            out[g['ma']] = 'xuyen_suot'
        elif any(g['ma'].startswith(d + '.') for d in dau):
            out[g['ma']] = 'khoi_dong'
        elif g['ma'] in cuoi:
            out[g['ma']] = 'ket_thuc'
        else:
            out[g['ma']] = 'xuyen_suot'
    return out


def hien_thi_giai_doan(gd_la, sprint_la):
    """Chuỗi cột Giai đoạn của một gói từ giai đoạn và sprint (bắt đầu, kết thúc) của các gói lá thuộc nó:
    gói Thực hiện ghi sprint (S2 hoặc S2-S3), gói quản lý dự án ghi tên giai đoạn. Mục cha gồm nhiều giai đoạn liệt kê các giai đoạn
    của gói lá theo thứ tự Khởi động, Suốt dự án, sprint, Kết thúc (ví dụ Khởi động, Suốt dự án, S1-S7, Kết thúc), không gộp thành Suốt dự án."""
    ds = set(gd_la)
    sp = sorted({s for ab in sprint_la for s in ab if s}, key=lambda s: (not s[1:].isdigit(), int(s[1:]) if s[1:].isdigit() else 0, s))
    khoang_sp = (sp[0] if len(sp) == 1 else f'{sp[0]}-{sp[-1]}') if sp else GIAI_DOAN['thuc_hien']
    if ds == {'thuc_hien'}:
        return khoang_sp
    if len(ds) == 1:
        return GIAI_DOAN.get(next(iter(ds)), next(iter(ds)))
    thu_tu = ['khoi_dong', 'xuyen_suot', 'thuc_hien', 'ket_thuc']
    return ', '.join(khoang_sp if g == 'thuc_hien' else GIAI_DOAN[g] for g in thu_tu if g in ds) + \
        ''.join(', ' + str(g) for g in sorted(ds - set(thu_tu)))


def ban_phat_hanh_hien_hanh(ngay_tl=None):
    """Mã bản phát hành hiện hành tại ngày ngay_tl (bản mới nhất có ngày không sau ngay_tl) theo du_lieu/phat_hanh.json.
    Trả về '' khi chưa có bản phát hành nào đến ngày đó."""
    d = ngay_iso(ngay_tl) or ngay_hien_hanh()
    ds = [x for x in doc_json('du_lieu/phat_hanh.json', {}).get('ban_phat_hanh', []) if x.get('ngay', '') <= d]
    return max(ds, key=lambda x: (x['ngay'], khoa_ma(x['ma'][1:] or '0')))['ma'] if ds else ''


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


def chia_md(md_, trong_so, le=2):
    """Chia md_ theo trọng số (ví dụ tỷ lệ tham gia của người thực hiện và người hỗ trợ), làm tròn le chữ số
    bằng lam_tron_tong để các phần cộng đúng md_ (không ra 351,01 khi cộng theo người)."""
    t = sum(float(w) for w in trong_so)
    return lam_tron_tong([float(md_) * float(w) / t for w in trong_so], le) if t else [0.0] * len(trong_so)


def khop_tong(gia_tri, goc, le=2):
    """Các giá trị đã làm tròn le chữ số mà cộng lệch tổng gốc chỉ do làm tròn (mỗi giá trị lệch tối đa nửa đơn vị cuối):
    phân bổ lại phần lệch bằng lam_tron_tong trên các giá trị đã bị làm tròn (dùng đến chữ số cuối), giữ nguyên số tròn.
    Trả về danh sách mới, hoặc None khi lệch quá sai số làm tròn (sai dữ liệu, không tự chỉnh)."""
    k = 10 ** le
    don_vi = [round(float(v or 0) * k) for v in gia_tri]
    lech = round(float(goc) * k) - sum(don_vi)
    if lech == 0:
        return [u / k for u in don_vi]
    ung_vien = [i for i, u in enumerate(don_vi) if u % 10] or [i for i, u in enumerate(don_vi) if u]
    tong_uv = sum(don_vi[i] for i in ung_vien)
    if abs(lech) > len(don_vi) / 2 or not tong_uv:
        return None
    thay = dict(zip(ung_vien, lam_tron_tong([don_vi[i] * (tong_uv + lech) / tong_uv / k for i in ung_vien], le)))
    return [thay.get(i, u / k) for i, u in enumerate(don_vi)]


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
    return bam_hieu_luc(p)


def bam_hieu_luc(p):
    """Băm tệp cộng phần giá trị doc_json gán ngầm khi đọc (du_an.don_vi_thuc_hien lấy từ nha_thau.json).
    Phần gán chỉ được cộng khi khác giá trị trong tệp, nên băm cũ vẫn dùng được và đổi trường khác của nha_thau.json
    không làm các bước chỉ dùng du_an bị báo cũ."""
    h = bam(p)
    if not h or not p.endswith('.json') or not os.path.isfile(duong_dan(p)):
        return h
    with open(duong_dan(p), encoding='utf-8') as f:
        tho = json.load(f)
    da_gan = doc_json(p)
    khac = {k: v for k, v in da_gan.items() if tho.get(k) != v} if isinstance(da_gan, dict) and isinstance(tho, dict) else {}
    return h + ':' + bam_obj(khac) if khac else h


def dinh_dang_cot(vals, f):
    """Định dạng cả cột với cùng số chữ số thập phân (MD, phần trăm). pt1 (luôn một chữ số) và md2 (luôn hai chữ số) giữ số chữ số
    cố định giữa các kỳ của tài liệu theo kỳ (báo cáo tiến độ), từ 1.6.4."""
    if f in ('pt1', 'md2'):
        return ['' if v in (None, '') else DINH_DANG[f](v) for v in vals]
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
