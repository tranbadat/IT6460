"""Chuẩn bị dữ liệu HSDT: kiểm tra thông tin nhà thầu, đối chiếu yêu cầu HSMT, lập các bảng biểu mẫu theo Mẫu 5A.

Dùng: python tinh_hsdt.py      (chay.py chuan_bi hsdt tự gọi)
Kiểm tra (lỗi thì dừng):
- trường bắt buộc của nha_thau.json (kể cả điện thoại, e-mail), giá trị dạng giữ chỗ như [Nhóm bổ sung ...] coi là thiếu;
- hợp đồng tương tự đạt giá trị và thời gian theo HSMT, doanh thu bình quân, nhân sự chủ chốt đủ số lượng và kinh nghiệm;
- giá dự thầu không vượt giá gói thầu, tổng Mẫu 11A bằng giá dự thầu;
- tỷ lệ sử dụng quỹ huy động không thấp hơn du_an.nguong_su_dung_quy_toi_thieu;
- mọi hạng mục Mẫu 01A hoàn thành trước cut over, hạng mục gắn đợt thanh toán không hoàn thành muộn hơn mốc của đợt;
- dau_vao/chi_tieu_ky_thuat.json có chỉ tiêu, bảo hành, điều kiện cut over;
- tiêu đề cột các bảng biểu mẫu trong dac_ta/hsdt.json (khóa mau_so) khớp dau_vao/Mau_5A.docx.
Ra: du_lieu/hsdt_bang.json (bảng đáp ứng HSMT, chỉ dẫn tiêu chí kỹ thuật, Mẫu 06A, 06B, 06C, 07, 10A, 11A, chỉ tiêu kỹ thuật,
bảo hành, huy động nhân sự theo sprint, tóm tắt năng lực).
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import datetime as dt
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

DAC_TA = os.path.join(HERE, '..', 'dac_ta', 'hsdt.json')
MAU_5A = 'dau_vao/Mau_5A.docx'
TRUONG_NHA_THAU = ('ten', 'dia_chi', 'dai_dien', 'chuc_vu_dai_dien', 'ma_so_thue', 'dien_thoai', 'email', 'nam_thanh_lap', 'ngay_ky_don',
                   'nghia_vu_thue_nam_gan_nhat')
BIEU_MAU_BAT_BUOC = ('06A', '06B', '06C', '07', '10A', '11A')  # bảng phải có trong đặc tả, đúng cột Mẫu 5A
LOAI_QUAN_LY = ('PM',)  # gói quản lý dự án không dùng để tính ngày của hạng mục Mẫu 10A
THEO_HE_THONG = 'Theo hồ sơ nhân sự trên Hệ thống'  # trường Mẫu 06B chưa có trong thanh_vien.json
CHUA_THONG_NHAT = 'Hai bên thống nhất khi xác nhận đặc tả'  # chỉ tiêu để null trong chi_tieu_ky_thuat.json
KY_KINH_NGHIEM = re.compile(r'^\s*(\d{1,2})/(\d{4})\s*[-–]\s*(?:(\d{1,2})/(\d{4})|(nay|hiện nay|hiện tại))\s*:\s*(.+)$', re.S | re.I)

hsmt = loi.doc_json('du_lieu/hsmt.json'); nt = loi.doc_json('dau_vao/nha_thau.json'); cp = loi.doc_json('du_lieu/chi_phi.json')
lich = loi.doc_json('du_lieu/lich.json'); wbs = loi.doc_json('du_lieu/wbs.json'); pc = loi.doc_json('du_lieu/phan_cong.json')
da = loi.du_an(); kt = loi.doc_json('dau_vao/chi_tieu_ky_thuat.json', {})
spec = json.load(open(DAC_TA, encoding='utf-8'))
loi_ds, canh_bao = [], []
L = hsmt['lich']
d_dong = dt.date.fromisoformat(L['dong_thau_iso'])


def ngay_tu_chu(s):
    """'01 tháng 01 năm 2024' -> date."""
    return dt.date(int(re.search(r'năm (\d{4})', s).group(1)), int(re.search(r'tháng (\d+)', s).group(1)), int(s[:2]))


# ---------------- thông tin nhà thầu
for k in TRUONG_NHA_THAU:
    if loi.la_gia_tri_thieu(nt.get(k)):
        loi_ds.append(f'nha_thau.json thiếu {k}' + (f' (đang là dấu giữ chỗ "{nt[k]}")' if loi.la_giu_cho(nt.get(k)) else ''))
hd = [h for h in nt.get('hop_dong_tuong_tu', []) if h.get('ten')]
if not hd:
    loi_ds.append('nha_thau.json chưa có hợp đồng tương tự')
min_hd = hsmt['tien']['hop_dong_tuong_tu_toi_thieu']
moc = hsmt['nang_luc']['moc_hop_dong_tuong_tu']  # dạng "01 tháng 01 năm 2024"
d_moc = ngay_tu_chu(moc)
hd_dat = [h for h in hd if (h.get('gia_tri') or 0) >= min_hd and h.get('ngay_hoan_thanh') and dt.date.fromisoformat(h['ngay_hoan_thanh']) >= d_moc]
if hd and not hd_dat:
    loi_ds.append(f'Không có hợp đồng tương tự từ {loi.tien(min_hd)} đồng hoàn thành từ {moc}')
nam_yc = hsmt['nang_luc']['cac_nam_doanh_thu']
dtn = {int(x['nam']): float(x['doanh_thu']) for x in nt.get('doanh_thu', []) if x.get('nam') and x.get('doanh_thu')}
thieu_nam = [n for n in nam_yc if n not in dtn]
if thieu_nam:
    loi_ds.append(f'nha_thau.json thiếu doanh thu các năm {thieu_nam}')
dt_bq = sum(dtn.get(n, 0) for n in nam_yc) / len(nam_yc)
if not thieu_nam and dt_bq < hsmt['tien']['doanh_thu_binh_quan_toi_thieu']:
    loi_ds.append(f'Doanh thu bình quân {loi.tien(dt_bq)} đồng thấp hơn yêu cầu {loi.tien(hsmt["tien"]["doanh_thu_binh_quan_toi_thieu"])} đồng')
han = L.get('dong_thau_iso'); ph = L.get('phat_hanh_iso')
if nt.get('ngay_ky_don') and han and not (ph <= nt['ngay_ky_don'] <= han):
    loi_ds.append(f'Ngày ký đơn dự thầu {loi.ngay(nt["ngay_ky_don"])} phải trong khoảng phát hành HSMT {loi.ngay(ph)} đến đóng thầu {loi.ngay(han)}')
if cp['gia_chao'] > hsmt['tien']['gia_goi_thau']:
    loi_ds.append('Giá dự thầu vượt giá gói thầu')
if nt.get('hop_dong_khong_hoan_thanh'):
    loi_ds.append('Có hợp đồng không hoàn thành, cần đối chiếu tiêu chí lịch sử hợp đồng của HSMT')


# ---------------- nhân sự chủ chốt (Bảng số 02, Mẫu 06A, 06B, 06C)
def ky_kinh_nghiem(text):
    """Tách kinh_nghiem dạng 'mm/yyyy - mm/yyyy: nội dung; ...' thành [{tu, den, noi_dung, d_tu}]. Không tách được thì rỗng."""
    out = []
    for doan in re.split(r';\s*(?=\d{1,2}/\d{4}\s*[-–])', text or ''):
        m = KY_KINH_NGHIEM.match(doan)
        if m:
            den = f'{int(m.group(3)):02d}/{m.group(4)}' if m.group(3) else 'nay'
            out.append({'tu': f'{int(m.group(1)):02d}/{m.group(2)}', 'den': den, 'noi_dung': m.group(6).strip().rstrip(';.'),
                        'd_tu': dt.date(int(m.group(2)), int(m.group(1)), 1)})
    return out


def so_nam_kinh_nghiem(t):
    """Số năm kinh nghiệm tính từ thời điểm sớm nhất trong kinh_nghiem đến ngày đóng thầu (làm tròn xuống).
    Không suy được thì dùng so_nam_kinh_nghiem đã kê khai. Trả về (số năm, căn cứ)."""
    ky = ky_kinh_nghiem(t.get('kinh_nghiem'))
    if not ky:
        return t.get('so_nam_kinh_nghiem', ''), 'Theo kê khai của nhân sự'
    d0 = min(k['d_tu'] for k in ky)
    n = math.floor((d_dong - d0).days / 365.25)
    ke_khai = t.get('so_nam_kinh_nghiem')
    if ke_khai not in (None, '') and float(ke_khai) > n:
        canh_bao.append(f'{t["ho_ten"]}: kê khai {ke_khai} năm kinh nghiệm, kinh nghiệm liệt kê từ {d0.month:02d}/{d0.year} chỉ chứng minh '
                        f'{n} năm đến ngày đóng thầu, HSDT dùng {n} năm. Nhóm bổ sung giai đoạn trước vào kinh_nghiem nếu có')
    return n, f'Từ {d0.month:02d}/{d0.year} đến ngày đóng thầu {loi.ngay(d_dong)}'


def danh_gia_nhan_su(t, yc):
    """Đánh giá một nhân sự chủ chốt theo yêu cầu Bảng số 02, trả về dòng đối chiếu."""
    for k in ('trinh_do', 'kinh_nghiem'):
        if loi.la_gia_tri_thieu(t.get(k)):
            loi_ds.append(f'thanh_vien.json: {t.get("ho_ten", t["id"])} (nhân sự chủ chốt) thiếu {k}')
    so_nam, can_cu = so_nam_kinh_nghiem(t)
    m = re.search(r'(\d+) năm', yc.get('kinh_nghiem', ''))
    dat = 'Đáp ứng'
    if m and so_nam not in (None, '') and float(so_nam) < int(m.group(1)):
        dat = 'Chưa đáp ứng'
        if 'hoặc' not in yc.get('kinh_nghiem', ''):
            loi_ds.append(f'{t["ho_ten"]}: {so_nam} năm kinh nghiệm, HSMT yêu cầu {yc["kinh_nghiem"].lower()}')
    return {'yeu_cau': yc.get('kinh_nghiem', ''), 'ho_ten': t.get('ho_ten', t['id']), 'trinh_do': t.get('trinh_do', ''), 'so_nam': so_nam,
            'can_cu': can_cu, 'kinh_nghiem': t.get('kinh_nghiem', ''), 'chung_chi': t.get('chung_chi', '') or 'Không', 'danh_gia': dat}


tv = {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']}
cho = [t['ho_ten'] for t in tv.values() if t.get('_can_xac_nhan')]
if cho:
    loi_ds.append('thanh_vien.json còn vị trí chưa xác nhận nhân sự (_can_xac_nhan): ' + ', '.join(cho) + '. Ghi họ tên thật và bỏ khóa _can_xac_nhan')
yc_cc = {y['stt']: y for y in hsmt.get('nhan_su_chu_chot', [])}
ns_cc = []
for x in pc['vi_tri_chu_chot']:
    if len(x.get('thanh_vien', [])) < x['so_luong']:
        loi_ds.append(f'Vị trí chủ chốt {x["vi_tri"]} thiếu nhân sự')
    for i in x.get('thanh_vien', []):
        ns_cc.append(dict({'stt': x['stt'], 'vi_tri': x['vi_tri'], 'id': i}, **danh_gia_nhan_su(tv.get(i, {'id': i}), yc_cc.get(x['stt'], {}))))


def mau_06b(ds):
    """Mẫu số 06B. Nhân sự loại nhom là nhân sự của nhà thầu (người sử dụng lao động là nhà thầu) trừ khi thanh_vien.json
    khai báo nguoi_su_dung_lao_dong. Trường chưa có ghi THEO_HE_THONG và cảnh báo."""
    thieu, out = set(), []

    def lay_tv(t, k):
        if not loi.la_gia_tri_thieu(t.get(k)):
            return str(t[k])
        thieu.add(k)
        return THEO_HE_THONG
    for i, n in enumerate(ds, 1):
        t = tv.get(n['id'], {})
        cua_nt = t.get('loai') == 'nhom' and loi.la_gia_tri_thieu(t.get('nguoi_su_dung_lao_dong'))
        ngay_sinh = loi.ngay(t['ngay_sinh']) if t.get('ngay_sinh') else (str(t['nam_sinh']) if t.get('nam_sinh') else lay_tv(t, 'ngay_sinh'))
        out.append({'stt': i, 'ten': n['ho_ten'], 'can_cuoc': lay_tv(t, 'can_cuoc'), 'vi_tri': n['vi_tri'], 'ngay_sinh': ngay_sinh,
                    'trinh_do': ', '.join(x for x in (t.get('trinh_do'), t.get('chung_chi')) if x),
                    'nguoi_su_dung_lao_dong': nt['ten'] if cua_nt else lay_tv(t, 'nguoi_su_dung_lao_dong'),
                    'dia_chi_ld': nt['dia_chi'] if cua_nt else lay_tv(t, 'dia_chi_nguoi_su_dung_lao_dong'),
                    'chuc_danh': t.get('chuc_danh', ''), 'so_nam_lam_viec': lay_tv(t, 'so_nam_lam_viec_hien_tai'),
                    'nguoi_lien_lac': lay_tv(t, 'nguoi_lien_lac'),
                    'lien_lac': f'{nt["dien_thoai"]}, {nt["email"]}' if cua_nt else lay_tv(t, 'dien_thoai_lien_lac')})
    if thieu:
        canh_bao.append(f'Mẫu số 06B: thanh_vien.json chưa có {", ".join(sorted(thieu))} của nhân sự chủ chốt, bảng ghi "{THEO_HE_THONG}". '
                        'Nhóm bổ sung các trường này nếu muốn kê khai trực tiếp')
    return out


def mau_06c(ds):
    """Mẫu số 06C: kinh nghiệm chuyên môn theo trình tự thời gian, tách từ kinh_nghiem của thanh_vien.json."""
    out = []
    for i, n in enumerate(ds, 1):
        ky = sorted(ky_kinh_nghiem(n['kinh_nghiem']), key=lambda k: k['d_tu'])
        out += [{'stt': i, 'ten': n['ho_ten'], 'tu': k['tu'], 'den': k['den'], 'noi_dung': k['noi_dung']} for k in ky] or \
            [{'stt': i, 'ten': n['ho_ten'], 'tu': '', 'den': '', 'noi_dung': n['kinh_nghiem']}]
    return out


# ---------------- Mẫu số 07 (hợp đồng không hoàn thành)
def mau_07():
    """Lựa chọn của Mẫu số 07 lấy nguyên văn dau_vao/Mau_5A.docx, điền năm của mốc lịch sử hợp đồng. Không có hoặc có 01 hợp đồng
    thì chọn ý thứ nhất, từ 02 hợp đồng thì chọn ý thứ hai. Trả về (câu lựa chọn, danh sách hợp đồng)."""
    import docx
    nam = ngay_tu_chu(hsmt['nang_luc']['moc_lich_su_hop_dong']).year
    ds = nt.get('hop_dong_khong_hoan_thanh') or []
    o = next((c.text for tb in docx.Document(loi.duong_dan(MAU_5A)).tables for r in tb.rows for c in r.cells
              if 'Không có hoặc có 01 hợp đồng' in c.text), '')
    y = [re.sub(r'\s+', ' ', x.replace('', '')).strip() for x in o.split('\n') if x.strip()]
    if len(y) < 2:
        canh_bao.append('Không đọc được lựa chọn của Mẫu số 07 trong dau_vao/Mau_5A.docx, câu lựa chọn lập theo mốc lịch sử hợp đồng')
        y = [f'Không có hoặc có 01 hợp đồng (cung cấp dịch vụ phi tư vấn) không hoàn thành do lỗi của nhà thầu kể từ ngày '
             f'{hsmt["nang_luc"]["moc_lich_su_hop_dong"]}.'] * 2
    chon = re.sub(r'năm\s*_*\s*\[ghi năm\]', f'năm {nam}', y[0 if len(ds) < 2 else 1])
    rows = [{'nam': h.get('nam', ''), 'phan_viec': h.get('phan_viec', ''), 'gia_tri': h.get('gia_tri', ''),
             'mo_ta': '. '.join([f'Mô tả hợp đồng: {h.get("mo_ta", "")}', f'Tên Chủ đầu tư: {h.get("chu_dau_tu", "")}', f'Địa chỉ: {h.get("dia_chi", "")}',
                                 f'Nguyên nhân không hoàn thành hợp đồng: {h.get("nguyen_nhan", "")}'])} for h in ds]
    return 'Nhà thầu kê khai: ' + chon[0].lower() + chon[1:], rows


# ---------------- huy động, mốc, Mẫu 10A, 11A
nguong = da.get('nguong_su_dung_quy_toi_thieu')
ty_le = lich.get('ty_le_su_dung_quy', cp.get('ty_le_su_dung'))
if nguong in (None, ''):
    canh_bao.append('du_an.json chưa có nguong_su_dung_quy_toi_thieu, bỏ qua kiểm tra tỷ lệ sử dụng quỹ huy động')
elif ty_le is not None and float(ty_le) < float(nguong):
    loi_ds.append(f'Tỷ lệ sử dụng quỹ huy động {loi.pt(ty_le)} (MD công việc {loi.md(lich.get("tong_md", 0))} trên quỹ huy động '
                  f'{loi.md(lich.get("tong_quy", 0))} MD) thấp hơn ngưỡng {loi.pt(nguong)} (du_an.json nguong_su_dung_quy_toi_thieu). '
                  'Nhóm xem lại ước lượng WBS, lịch huy động nhân sự hoặc ngưỡng, chạy lại master schedule và cost estimate')


def huy_dong_theo_sprint():
    """Số người và MD huy động theo sprint, lấy từ lich.json phan_bo (quy), không có thì tính từ thanh_vien.json."""
    pb = lich.get('phan_bo') or [{'thanh_vien': i, 'sprint': s, 'quy': q} for i, t in tv.items()
                                 for s, q in loi.quy_thoi_gian(t, lich['sprint']).items()]
    out = []
    for s in lich['sprint']:
        co = [x for x in pb if x['sprint'] == s['ma'] and float(x.get('quy') or 0) > 0]
        out.append({'ma': s['ma'], 'tu': s['tu'], 'den': s['den'], 'so_nguoi': len({x['thanh_vien'] for x in co}),
                    'md_huy_dong': round(sum(float(x['quy']) for x in co), 2)})
    return out


lg = {x['ma']: x for x in lich['goi'] if x['la']}
by, la = loi.nut_wbs(wbs)


def goi_chinh(stt):
    """Gói chính của hạng mục 01A: gói lá có lịch, không dàn trải, không thuộc loại quản lý dự án.
    Trả về (gói chính, gói riêng của hạng mục để tính ngày bắt đầu)."""
    goi = [g for g in la if stt in (g.get('hang_muc_01a') or []) and g['ma'] in lg]
    chinh = [g for g in goi if not lg[g['ma']].get('dan_trai') and g.get('loai') not in LOAI_QUAN_LY] or \
        [g for g in goi if not lg[g['ma']].get('dan_trai')] or goi
    rieng = [g for g in chinh if len(g.get('hang_muc_01a') or []) == 1] or chinh
    return [g['ma'] for g in chinh], [g['ma'] for g in rieng]


def dot_cua_hang_muc():
    """{stt hạng mục 01A: đợt thanh toán}. Lấy hop_dong.thanh_toan[].hang_muc_01a nếu có, nếu không thì suy từ nội dung từng đợt
    tại E-ĐKC 13.1 và su_kien: hạng mục gắn đợt sớm nhất có nhắc tên tiếng Anh trong ngoặc hoặc tên hạng mục."""
    tt = hsmt['hop_dong'].get('thanh_toan', [])
    ro = {int(s): int(x['dot']) for x in tt for s in (x.get('hang_muc_01a') or [])}
    if ro:
        return ro
    van = next((v for k, v in hsmt.get('e_dkct', {}).items() if k.replace(' ', '').startswith('E-ĐKC13.1')), '')
    doan = {int(m.group(1)): m.group(2) for m in re.finditer(r'Đợt (\d+):(.*?)(?=Đợt \d+:|$)', van, re.S)}
    doan = {int(x['dot']): doan.get(int(x['dot']), '') + ' ' + x.get('su_kien', '') for x in tt} or doan
    out = {}
    for h in hsmt['mau_01a']:
        tu = [w for w in re.findall(r'\(([^()]+)\)', h['danh_muc']) + [re.sub(r'\s*\([^()]*\)', '', h['danh_muc']).strip()] if w]
        dot = next((d for d in sorted(doan) if any(re.search(rf'(?<!\w){re.escape(w)}(?!\w)', doan[d], re.I) for w in tu)), None)
        if dot:
            out[h['stt']] = dot
    return out


m10 = []
for h in hsmt['mau_01a']:
    goi, rieng = goi_chinh(h['stt'])
    if not goi:
        loi_ds.append(f'Hạng mục 01A số {h["stt"]} không có gói trong lịch'); continue
    a = min(lg[m]['bat_dau'] for m in rieng); b = max(lg[m]['ket_thuc'] for m in goi)
    if b > lich['cut_over']:
        loi_ds.append(f'Hạng mục 01A số {h["stt"]} hoàn thành sau cut over')
    m10.append({'stt': h['stt'], 'danh_muc': h['danh_muc'], 'mo_ta': h.get('mo_ta', ''), 'khoi_luong': h['khoi_luong'], 'don_vi': h['don_vi'],
                'dia_diem': h['dia_diem'], 'bat_dau': a, 'ket_thuc': b, 'yeu_cau': h['ngay_hoan_thanh'],
                'goi': ', '.join(sorted(goi, key=loi.khoa_ma)[:6]) + (' ...' if len(goi) > 6 else ''), 'goi_ds': goi})

dot_hm = dot_cua_hang_muc()
moc_dot = {int(m['dot_thanh_toan']): m for m in lich['moc'] if str(m.get('dot_thanh_toan', '')).strip()}
for r in m10:
    r['dot_thanh_toan'] = dot_hm.get(r['stt'], '')
    m = moc_dot.get(dot_hm.get(r['stt']))
    if m and r['ket_thuc'] > m['ngay']:
        tre = [g for g in sorted(r['goi_ds'], key=loi.khoa_ma) if lg[g]['ket_thuc'] > m['ngay']]
        loi_ds.append(f'Hạng mục 01A số {r["stt"]} ({r["danh_muc"]}) gắn đợt thanh toán {r["dot_thanh_toan"]} (mốc {m["ma"]} ngày '
                      f'{loi.ngay(m["ngay"])}) nhưng hoàn thành {loi.ngay(r["ket_thuc"])}, muộn hơn mốc do gói '
                      + ', '.join(f'{g} (xong {loi.ngay(lg[g]["ket_thuc"])})' for g in tre)
                      + '. Sửa hang_muc_01a của gói trong WBS (gói dùng chung không thuộc hạng mục này) hoặc sửa lịch, rồi chạy lại')
m10 = [{k: v for k, v in r.items() if k != 'goi_ds'} for r in m10]


def mau_11a():
    """Mẫu số 11A: hạng mục từ chi_phi.json mau_11a, thêm mô tả (Mẫu 01A) và đơn giá bằng thành tiền chia khối lượng."""
    mo_ta = {h['stt']: h.get('mo_ta', '') for h in hsmt['mau_01a']}
    out = []
    for x in cp.get('mau_11a', []):
        try:
            kl = float(str(x['khoi_luong']).replace(',', '.'))
        except ValueError:
            loi_ds.append(f'Mẫu 11A hạng mục {x["stt"]}: khối lượng "{x["khoi_luong"]}" không phải số'); kl = 0
        out.append({'stt': x['stt'], 'danh_muc': x['danh_muc'], 'mo_ta': mo_ta.get(x['stt'], ''), 'khoi_luong': x['khoi_luong'],
                    'don_vi': x['don_vi'], 'don_gia': round(x['thanh_tien'] / kl) if kl else 0, 'thanh_tien': x['thanh_tien']})
    if round(sum(x['thanh_tien'] for x in out)) != round(cp['gia_chao']):
        loi_ds.append(f'Tổng Mẫu 11A {loi.tien(sum(x["thanh_tien"] for x in out))} đồng khác giá dự thầu {loi.tien(cp["gia_chao"])} đồng')
    return out


# ---------------- đơn dự thầu, bảo đảm dự thầu
def don_du_thau():
    """Mẫu số 02 lấy nguyên văn từ dau_vao/Mau_5A.docx, điền các trường do Hệ thống trích xuất."""
    import docx
    ps = [p.text.strip() for p in docx.Document(loi.duong_dan(MAU_5A)).paragraphs]
    i0 = next(i for i, t in enumerate(ps) if t.startswith('Mẫu số 02'))
    i1 = next(i for i in range(i0 + 1, len(ps)) if ps[i].startswith('Ghi chú'))
    goi = hsmt['goi_thau']['ten']; gia = cp['gia_chao']; bd = hsmt['tien']['bao_dam_du_thau']
    etbmt = nt.get('so_e_tbmt') or 'theo thông báo mời thầu trên Hệ thống mạng đấu thầu quốc gia'
    gia_txt = f"{loi.tien(gia)} đồng (bằng chữ: {loi.so_bang_chu(gia).lower()} đồng)"
    tim = re.compile(r'\s*_{2,}\s*,?\s*\[[^\]]*\]?|\s*_{2,}|\s*\[\s*[^\]]*\]')
    dien = {'Ngày:': [loi.ngay(nt.get('ngay_ky_don', ''))], 'Tên gói thầu:': [goi], 'Kính gửi:': [hsmt['goi_thau']['chu_dau_tu']],
            'Tên nhà thầu:': [nt.get('ten', ''), nt.get('ma_so_thue', ''), goi, etbmt, gia_txt],
            'Hiệu lực của E-HSDT': [f"{hsmt['thoi_han']['hieu_luc_hsdt_ngay']} ngày kể từ ngày đóng thầu"],
            'Bảo đảm dự thầu': [f"{loi.tien(bd)} đồng (bằng chữ: {loi.so_bang_chu(bd).lower()} đồng)"],
            'Hiệu lực của Bảo đảm dự thầu': [f"{hsmt['thoi_han']['hieu_luc_bao_dam_du_thau_ngay']} ngày kể từ ngày đóng thầu"],
            'Ngoài ra': [loi.ptg(nt.get('giam_gia_phan_tram') or 0)], 'Giá dự thầu sau khi': [gia_txt]}
    giam = float(nt.get('giam_gia_phan_tram') or 0)
    chao_hang = 'chào hàng' in hsmt['goi_thau'].get('hinh_thuc', '')
    out, so_muc = [], 0
    for t in ps[i0 + 1:i1]:
        if not t or t.upper().startswith('ĐƠN DỰ THẦU'):
            continue
        if not giam and (t.startswith('Ngoài ra') or t.startswith('Giá dự thầu sau khi')):
            continue  # không đề xuất giảm giá
        if bd < 50000000 and t.startswith('Hiệu lực của Bảo đảm dự thầu'):
            continue  # ghi chú (2) của mẫu
        if not chao_hang and re.match(r'\d+\.\s*Có đủ năng lực, kinh nghiệm', t):
            continue  # ghi chú (4): chỉ áp dụng chào hàng cạnh tranh
        k = next((k for k in dien if t.startswith(k)), None)
        if k:
            vals = iter(dien[k])
            t = tim.sub(lambda m: ' ' + next(vals, '') + (',' if ',' in m.group(0).split('[')[0] else ''), t)
            t = re.sub(r'\s+([,.;:])', r'\1', re.sub(r':\s*', ': ', t, count=1)).strip()
        t = re.sub(r'\s*\((\d)\)', '', t)
        m = re.match(r'(\d+)\.\s*(.*)', t)
        if m:
            so_muc += 1; t = f'{so_muc}. {m.group(2)}'
        out.append(t)
    out.append(f"Đơn dự thầu được ký bằng chữ ký số của {nt.get('dai_dien', '')}, {nt.get('chuc_vu_dai_dien', '')}, khi nộp E-HSDT.")
    return out


bd_ = hsmt['tien']['bao_dam_du_thau']; bl = nt.get('bao_dam_du_thau') or {}
if bd_ < 50000000:
    bao_dam_ghi_chu = 'Giá trị nhỏ hơn 50 triệu đồng nên nhà thầu cam kết trong đơn dự thầu theo Mục 18.8 E-CDNT, không nộp thư bảo lãnh dự thầu khi nộp E-HSDT.'
else:
    for k in ('to_chuc_phat_hanh', 'so', 'ngay_phat_hanh'):
        if loi.la_gia_tri_thieu(bl.get(k)):
            loi_ds.append(f'nha_thau.json thiếu bao_dam_du_thau.{k} (giá trị bảo đảm từ 50 triệu đồng phải nộp thư bảo lãnh Mẫu số 04A)')
    bao_dam_ghi_chu = (f"Nhà thầu nộp thư bảo lãnh dự thầu theo Mẫu số 04A số {bl.get('so', '')} do {bl.get('to_chuc_phat_hanh', '')} phát hành ngày "
                       f"{loi.ngay(bl.get('ngay_phat_hanh', '')) if bl.get('ngay_phat_hanh') else ''}, hiệu lực {hsmt['thoi_han']['hieu_luc_bao_dam_du_thau_ngay']} ngày kể từ ngày đóng thầu.")
try:
    don = don_du_thau()
except (StopIteration, FileNotFoundError, KeyError) as e:
    don = []; loi_ds.append(f'Không đọc được Mẫu số 02 trong dau_vao/Mau_5A.docx ({e})')


# ---------------- chỉ tiêu kỹ thuật, bảo hành (dau_vao/chi_tieu_ky_thuat.json)
def viet_hoa_dau(s):
    s = s.strip()
    return s[:1].upper() + s[1:]


def bang_chi_tieu():
    """Bảng Yêu cầu HSMT, Chỉ tiêu, Giải pháp, Cách kiểm chứng. Giải pháp tách theo dấu chấm phẩy thành từng dòng trong ô."""
    ds = kt.get('chi_tieu') or []
    if not ds:
        loi_ds.append('dau_vao/chi_tieu_ky_thuat.json thiếu hoặc không có chỉ tiêu (chi_tieu). Nhóm khai báo chỉ tiêu kỹ thuật định lượng '
                      '(tỷ lệ sẵn sàng, thời gian phản hồi, tải đồng thời, an toàn, sao lưu) rồi chạy lại')
    dong = []
    for x in ds:
        for k in ('ma', 'yeu_cau_hsmt', 'chi_tieu', 'giai_phap', 'cach_kiem_chung'):
            if loi.la_gia_tri_thieu(x.get(k)):
                loi_ds.append(f'chi_tieu_ky_thuat.json, chỉ tiêu {x.get("ma", "?")} thiếu {k}')
        ct = [x.get('chi_tieu', '')]
        if 'rpo_gio' in x or 'rto_gio' in x:
            ct.append('RPO, RTO: ' + (f'{x["rpo_gio"]} giờ, {x["rto_gio"]} giờ' if x.get('rpo_gio') is not None and x.get('rto_gio') is not None
                                      else CHUA_THONG_NHAT.lower()))
        dong.append([x.get('ma', ''), x.get('yeu_cau_hsmt', ''), ct, [viet_hoa_dau(g) for g in str(x.get('giai_phap', '')).split(';') if g.strip()],
                     x.get('cach_kiem_chung', '')])
    return {'cot': ['Mã', 'Yêu cầu HSMT', 'Chỉ tiêu', 'Giải pháp', 'Cách kiểm chứng'], 'dong': dong, 'widths': [700, 1700, 2300, 2900, 1700],
            'center_cols': [0]}


def bang_bao_hanh():
    """Thời hạn phản hồi, khắc phục theo mức lỗi. Trường null ghi CHUA_THONG_NHAT."""
    bh = kt.get('bao_hanh') or {}
    if not bh.get('muc_loi') or loi.la_gia_tri_thieu(bh.get('thoi_han_thang')):
        loi_ds.append('chi_tieu_ky_thuat.json thiếu bao_hanh.thoi_han_thang hoặc bao_hanh.muc_loi (thời hạn phản hồi, khắc phục theo mức lỗi)')
    elif float(bh['thoi_han_thang']) < float(hsmt['hop_dong']['bao_hanh_thang']):
        loi_ds.append(f'Thời hạn bảo hành {bh["thoi_han_thang"]} tháng ngắn hơn yêu cầu HSMT {hsmt["hop_dong"]["bao_hanh_thang"]} tháng')
    if loi.la_gia_tri_thieu(kt.get('dieu_kien_cut_over')):
        loi_ds.append('chi_tieu_ky_thuat.json thiếu dieu_kien_cut_over (điều kiện quyết định đưa hệ thống vào vận hành)')
    dong = [[m.get('muc', ''), f'{m["phan_hoi_gio"]} giờ' if m.get('phan_hoi_gio') is not None else CHUA_THONG_NHAT,
             m.get('khac_phuc') or CHUA_THONG_NHAT] for m in bh.get('muc_loi', [])]
    if any(CHUA_THONG_NHAT in r for r in dong):
        canh_bao.append(f'chi_tieu_ky_thuat.json bao_hanh.muc_loi còn thời hạn null, bảng ghi "{CHUA_THONG_NHAT}"')
    return {'cot': ['Mức lỗi', 'Thời hạn phản hồi', 'Thời hạn khắc phục'], 'dong': dong, 'widths': [2600, 3300, 3400]}


def ho_tro_tang_cuong():
    """Câu về hỗ trợ tăng cường sau cut over (nếu có trong chi_tieu_ky_thuat.json)."""
    h = (kt.get('bao_hanh') or {}).get('ho_tro_tang_cuong') or {}
    if not h.get('tu') or not h.get('den'):
        return []
    if h['tu'] <= lich['cut_over']:
        canh_bao.append(f'Hỗ trợ tăng cường bắt đầu {loi.ngay(h["tu"])}, không sau ngày cut over {loi.ngay(lich["cut_over"])}')
    nd = h.get('noi_dung', '').strip().rstrip('.')
    return [f'Sau cut over, nhà thầu hỗ trợ tăng cường từ ngày {loi.ngay(h["tu"])} đến ngày {loi.ngay(h["den"])}: {nd[:1].lower() + nd[1:]}.']


# ---------------- bảng đáp ứng HSMT, chỉ dẫn tiêu chí kỹ thuật
def muc_theo_tieu_chi():
    """{stt tiêu chí kỹ thuật: [tiêu đề mục]} theo khóa tieu_chi của tiêu đề h2, h3 trong đặc tả."""
    out = {}
    for kb in spec['khoi']:
        lv = next((k for k in ('h2', 'h3') if k in kb), None)
        for s in (kb.get('tieu_chi') or []) if lv else []:
            out.setdefault(int(s), []).append('Mục ' + kb[lv])
    return out


def chi_dan_tieu_chi():
    """Dòng tiêu chí tổng quát, sau đó các tiêu chí chi tiết j.i của HSMT (hsmt.json ky_thuat.tieu_chi[].chi_tiet, nếu có).
    Vị trí đáp ứng của tiêu chí chi tiết là các mục của tiêu chí tổng quát chứa nó."""
    muc = muc_theo_tieu_chi()
    so_d = lambda v: '' if v is None else (str(int(v)) if float(v).is_integer() else str(v).replace('.', ','))  # noqa: E731
    dong = []
    for tc in hsmt['ky_thuat']['tieu_chi']:
        if not muc.get(tc['stt']):
            loi_ds.append(f'Đặc tả hsdt.json chưa có mục đáp ứng tiêu chí kỹ thuật {tc["stt"]} (khóa tieu_chi của tiêu đề)')
        dong.append([str(tc['stt']), tc['ten'], str(tc['diem_toi_da']), str(tc['diem_toi_thieu']), muc.get(tc['stt'], [])])
        dong += [[ct['stt'], ct['ten'], so_d(ct['diem_toi_da']), so_d(ct.get('diem_toi_thieu')), muc.get(tc['stt'], [])]
                 for ct in tc.get('chi_tiet') or []]
    return {'cot': ['STT', 'Tiêu chí đánh giá về kỹ thuật', 'Điểm tối đa', 'Điểm tối thiểu', 'Vị trí đáp ứng trong E-HSDT'], 'dong': dong,
            'widths': [600, 4400, 1000, 1000, 2300], 'center_cols': [0, 2, 3]}


def bang_dap_ung(ns_cc, m07):
    """Bảng đáp ứng: tính hợp lệ, Bảng số 01 (lịch sử hợp đồng, thuế, doanh thu, hợp đồng tương tự), Bảng số 02, tiêu chí kỹ thuật."""
    hl = hsmt['thoi_han']; muc = muc_theo_tieu_chi()
    dd = lambda ok: 'Đáp ứng' if ok else 'Chưa đáp ứng'  # noqa: E731
    dong = [
        ['Tính hợp lệ của E-HSDT, tư cách hợp lệ của nhà thầu', f'Đơn dự thầu theo Mẫu số 02, mã số thuế {nt.get("ma_so_thue", "")}', dd(bool(don))],
        ['Hiệu lực E-HSDT', f'{hl["hieu_luc_hsdt_ngay"]} ngày kể từ ngày đóng thầu', 'Đáp ứng'],
        ['Bảo đảm dự thầu', f'{loi.tien(hsmt["tien"]["bao_dam_du_thau"])} đồng, ' + ('cam kết trong đơn dự thầu (Mục 18.8 E-CDNT)' if hsmt['tien']['bao_dam_du_thau'] < 50000000
                            else f'thư bảo lãnh hiệu lực tối thiểu {hl["hieu_luc_bao_dam_du_thau_ngay"]} ngày kể từ ngày đóng thầu'), 'Đáp ứng'],
        ['Lịch sử không hoàn thành hợp đồng (Bảng số 01)', m07[0].rstrip('.') + ' (Mẫu số 07)', dd(len(nt.get('hop_dong_khong_hoan_thanh') or []) < 2)],
        ['Thực hiện nghĩa vụ kê khai thuế, nộp thuế (Bảng số 01)', nt.get('nghia_vu_thue_nam_gan_nhat', ''), dd(not loi.la_gia_tri_thieu(nt.get('nghia_vu_thue_nam_gan_nhat')))],
        ['Doanh thu bình quân (Bảng số 01)', f'{loi.tien(dt_bq)} đồng các năm {", ".join(map(str, nam_yc))}', dd(dt_bq >= hsmt['tien']['doanh_thu_binh_quan_toi_thieu'])],
        ['Hợp đồng tương tự (Bảng số 01)', f'{len(hd_dat)} hợp đồng từ {loi.tien(min_hd)} đồng, hoàn thành từ {moc} (Mẫu số 05)', dd(hd_dat)],
        ['Nhân sự chủ chốt (Bảng số 02)', '. '.join(f'{x["vi_tri"]}: {x.get("ho_ten", "")}' for x in pc['vi_tri_chu_chot']) + ' (Mẫu số 06A, 06B, 06C)',
         dd(all(x['danh_gia'] == 'Đáp ứng' for x in ns_cc))],
    ]
    for tc in hsmt['ky_thuat']['tieu_chi']:
        dong.append([f'Tiêu chí kỹ thuật {tc["stt"]}: {tc["ten"].split(":")[0]}',
                     f'{", ".join(muc.get(tc["stt"], []))}. Điểm tối thiểu {tc["diem_toi_thieu"]}/{tc["diem_toi_da"]}', dd(muc.get(tc['stt']))])
    dong += [
        ['Thời gian thực hiện', f'Từ {L["hop_dong_hieu_luc_du_kien"]} đến cut over {L["cut_over"]}, hoàn thành dự kiến {loi.ngay(lich["ket_thuc_du_kien"])}', dd(lich['ket_thuc_du_kien'] <= lich['cut_over'])],
        ['Phạm vi theo Mẫu 01A', f'{len(m10)}/{len(hsmt["mau_01a"])} hạng mục có tiến độ (Mẫu số 10A) và giá (Mẫu số 11A)', dd(len(m10) == len(hsmt['mau_01a']))],
        ['Giá dự thầu không vượt giá gói thầu', f'{loi.tien(cp["gia_chao"])} đồng, giá gói thầu {loi.tien(hsmt["tien"]["gia_goi_thau"])} đồng', dd(cp['gia_chao'] <= hsmt['tien']['gia_goi_thau'])],
    ]
    return {'cot': ['Yêu cầu của HSMT', 'Đề xuất của nhà thầu', 'Đánh giá'], 'dong': dong, 'widths': [2800, 5000, 1500]}


# ---------------- tiêu đề cột biểu mẫu so với Mẫu 5A
def kiem_tra_cot_bieu_mau():
    co = set()
    for kb in spec['khoi']:
        bs = kb.get('bang') or {}
        if not bs.get('mau_so'):
            continue
        co.add(bs['mau_so'])
        mau = loi.cot_bieu_mau(MAU_5A, bs['mau_so'])
        tieu_de = [c[0] for c in bs['cot']]
        if mau is None:
            loi_ds.append(f'Không tìm thấy bảng của Mẫu số {bs["mau_so"]} trong {MAU_5A}')
        elif [loi.chuan_hoa_tieu_de(x) for x in tieu_de] != [loi.chuan_hoa_tieu_de(x) for x in mau]:
            loi_ds.append(f'Đặc tả hsdt.json, bảng Mẫu số {bs["mau_so"]}: tiêu đề cột "{" | ".join(tieu_de)}" khác Mẫu 5A "{" | ".join(mau)}"')
    for m in BIEU_MAU_BAT_BUOC:
        if m not in co:
            loi_ds.append(f'Đặc tả hsdt.json thiếu bảng Mẫu số {m} (khối bang có khóa mau_so)')


try:
    kiem_tra_cot_bieu_mau()
    m07 = mau_07()
except Exception as e:  # thiếu hoặc hỏng tệp mẫu: báo lỗi và dừng ở cuối script
    m07 = ('', []); loi_ds.append(f'Không đọc được biểu mẫu trong {MAU_5A} ({type(e).__name__}: {e})')

out = {'mau_10a': m10, 'mau_11a': mau_11a(), 'dap_ung': bang_dap_ung(ns_cc, m07), 'chi_dan_tieu_chi': chi_dan_tieu_chi(),
       'hop_dong_tuong_tu': hd, 'doanh_thu': [{'nam': n, 'doanh_thu': dtn.get(n, 0)} for n in nam_yc], 'doanh_thu_binh_quan': round(dt_bq),
       'so_hop_dong_dat': len(hd_dat), 'nhan_su_chu_chot': ns_cc, 'mau_06b': mau_06b(ns_cc), 'mau_06c': mau_06c(ns_cc),
       'mau_07_lua_chon': m07[0], 'mau_07': m07[1], 'chi_tieu_ky_thuat': bang_chi_tieu(), 'bao_hanh_muc_loi': bang_bao_hanh(),
       'ho_tro_tang_cuong': ho_tro_tang_cuong(), 'huy_dong': huy_dong_theo_sprint(), 'tong_md_huy_dong': lich.get('tong_quy', 0),
       'don_du_thau': don, 'bao_dam_ghi_chu': bao_dam_ghi_chu, 'bao_dam_du_thau_chu': loi.so_bang_chu(hsmt['tien']['bao_dam_du_thau']).lower(),
       'canh_bao': canh_bao}
loi.ghi_json('du_lieu/hsdt_bang.json', out)
for c in canh_bao:
    print('CẢNH BÁO:', c)
if loi_ds:
    print('LỖI:', *loi_ds, sep='\n- ')
    print('Cập nhật dau_vao/nha_thau.json, dau_vao/chi_tieu_ky_thuat.json, dac_ta/hsdt.json hoặc các bước liên quan (WBS, lịch, dự toán) rồi chạy lại.')
    sys.exit(1)
print(f'Đã chuẩn bị dữ liệu HSDT: {len(m10)} hạng mục Mẫu 10A, {len(hd_dat)} hợp đồng tương tự đạt, doanh thu bình quân {loi.tien(dt_bq)} đồng, '
      f'{len(out["chi_tieu_ky_thuat"]["dong"])} chỉ tiêu kỹ thuật')
