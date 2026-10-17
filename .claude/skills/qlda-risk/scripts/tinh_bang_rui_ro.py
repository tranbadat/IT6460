"""Tính các bảng của kế hoạch quản lý rủi ro: thang đo có ngưỡng định lượng, quy đổi sang ma trận 3x3 hạng A, B, C,
ma trận 5x5 và 3x3 ghi mã rủi ro, đối chiếu dự phòng chi phí và dự trữ thời gian, phương án khi dự trữ thời gian thiếu.

EMV in theo triệu đồng, làm tròn, kèm khoảng tính từ cận dưới, cận trên của mức xác suất (ước tính định hướng).
EMV thời gian dùng đánh giá dự trữ chỉ gồm rủi ro liên kết gói trên đường găng, gói ghim ngày cut over hoặc mốc cut over.
Phương án khi dự trữ thiếu do nhóm chốt, ghi dau_vao/du_an.json khóa phuong_an_du_tru_thoi_gian (một hoặc nhiều khóa của PHUONG_AN).

Dùng: python tinh_bang_rui_ro.py      (chay.py chuan_bi ke_hoach_rui_ro tự gọi)
Ra: du_lieu/rui_ro_bang.json
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

rr = loi.doc_json('du_lieu/rui_ro.json'); cp = loi.doc_json('du_lieu/chi_phi.json'); da = loi.du_an(); lich = loi.doc_json('du_lieu/lich.json')
T = rr['thang_do']; th = rr['tong_hop']; ds = rr['danh_sach']
NG = T.get('nguong_tac_dong', {})
Q = T.get('quy_doi_3x3', {})
ty = lambda v: loi.so(float(v) / 1e6, 0)  # triệu đồng, làm tròn
khoang = lambda a, b, f: f'khoảng {f(a)} đến {f(b)}'
so1 = lambda v: loi.so(v, 1)
PHUONG_AN = {
    'tang_du_tru': ('Tăng dự trữ', 'Bổ sung nguồn lực hoặc điều chỉnh giao việc cho các gói trên đường găng để dự trữ đến cut over đạt tối thiểu {emv} ngày làm việc',
                    'Tăng MD hoặc chi phí nhân công, cập nhật giao việc, master schedule và cost estimate'),
    'dua_viec_len_som': ('Đưa việc lên sớm', 'Bắt đầu sớm hoặc thực hiện song song các gói {goi}',
                         'Tăng tải các sprint trước, kiểm tra lại phụ thuộc và tải từng người'),
    'thu_hep_pham_vi': ('Thu hẹp phạm vi', 'Thống nhất với Chủ đầu tư hoãn chức năng không thiết yếu sang sau cut over',
                        'Cần yêu cầu thay đổi và phụ lục hợp đồng, ảnh hưởng nghiệm thu'),
    'chap_nhan_bao_cdt': ('Chấp nhận và báo Chủ đầu tư', 'Giữ kế hoạch, theo dõi dấu hiệu của {ma}, thông báo Chủ đầu tư mức thiếu dự trữ và phương án khi rủi ro xảy ra',
                          'Có thể bị phạt chậm tiến độ theo E-ĐKC 15 trên giá trị đợt thanh toán gắn mốc cut over')}


def khoang_muc(nguong, k, f, nguyen=False):
    """Khoảng giá trị của mức k theo bảng ngưỡng {mức: giá trị từ}: dưới ngưỡng mức 2, từ a đến dưới b (số nguyên: a đến b - 1), từ ngưỡng mức 5."""
    if not nguong:
        return ''
    k = int(k)
    if k == 1:
        return f'dưới {f(nguong["2"])}'
    if str(k + 1) not in nguong:
        return f'từ {f(nguong[str(k)])}'
    tren = nguong[str(k + 1)]
    return f'{f(nguong[str(k)])} đến {f(tren - 1)}' if nguyen else f'{f(nguong[str(k)])} đến dưới {f(tren)}'


def bang_tac_dong():
    co = NG.get('co', {})
    hoa = lambda s: s[:1].upper() + s[1:]
    dk = lambda k: hoa(' hoặc '.join(T['ten_co'][c] for c, m in co.items() if m == int(k)))
    dong = [[k, v, khoang_muc(NG.get('ngay_tu'), k, lambda x: loi.so(x, 0), True), khoang_muc(NG.get('ty_le_chi_phi_tu'), k, loi.pt), dk(k)]
            for k, v in T['tac_dong'].items()]
    return {'cot': ['Mức', 'Tác động', 'Ngày chậm (ngày làm việc)', f'Chi phí trên {th.get("nguon_gia_co_so", "giá chào")}', 'Điều kiện về mốc, hợp đồng'], 'dong': dong,
            'widths': [700, 2700, 1700, 1700, 2500], 'center_cols': [0]}


def bang_quy_doi():
    nhom = {}
    for k, v in Q['muc'].items():
        nhom.setdefault(v, []).append(int(k))
    ten = lambda ks: f'Mức {ks[0]}' if len(ks) == 1 else f'Mức {ks[0]} đến {ks[-1]}'
    dong = [[ten(sorted(nhom[a])), Q['ten_xac_suat'][a], Q['ten_tac_dong'][a]] for a in ('thap', 'trung_binh', 'cao') if a in nhom]
    return {'cot': ['Thang 5 mức', 'Xác suất theo thang 3 mức', 'Tác động theo thang 3 mức'], 'dong': dong, 'widths': [3100, 3100, 3100]}


def bang_ma_tran_3x3():
    o = lambda c: c['hang'] + (': ' + ', '.join(c['ma']) if c['ma'] else '')
    dong = [[Q['ten_xac_suat'][r['xac_suat']]] + [o(r[b]) for b in ('cao', 'trung_binh', 'thap')] for r in rr['ma_tran_3x3']]
    return {'cot': ['Xác suất, tác động'] + [Q['ten_tac_dong'][b] for b in ('cao', 'trung_binh', 'thap')], 'dong': dong,
            'widths': [1800, 2500, 2500, 2500], 'center_cols': [0]}


def danh_gia_du_tru():
    du_tru = float(lich['du_tru_den_cut_over_ngay'])
    emv = float(th.get('tong_emv_ngay_gang', th['tong_emv_ngay']))
    thieu = round(max(0.0, emv - du_tru), 2)
    return {'emv_ngay_gang': emv, 'emv_ngay_gang_thap': th.get('tong_emv_ngay_gang_thap', emv), 'emv_ngay_gang_cao': th.get('tong_emv_ngay_gang_cao', emv),
            'du_tru': du_tru, 'thieu': thieu, 'du': thieu == 0, 'ket_luan': 'đủ' if thieu == 0 else 'thiếu', 'ma_gang': ', '.join(th.get('ma_gang', [])),
            'so_rui_ro_gang': len(th.get('ma_gang', [])),
            'danh_gia': 'Đủ' if thieu == 0 else f'Thiếu {so1(thieu)} ngày làm việc',
            # cụm từ bắt buộc của khối DU_PHONG: khi thiếu phải nêu đủ bốn phương án, khi đủ chỉ cần nhắc dự trữ
            'cum_phuong_an': ['dự trữ'] * 4 if thieu == 0 else ['tăng dự trữ', 'đưa việc lên sớm', 'thu hẹp phạm vi', 'chấp nhận']}


def bang_phuong_an(dt):
    """Phương án khi dự trữ thời gian thiếu; có cột Áp dụng khi nhóm đã quyết định trong du_an.json."""
    if dt['du']:
        return {'cot': ['Phương án'], 'dong': [], 'chon': []}
    gang = set(lich.get('duong_gang', [])) - set(lich.get('khong_som_hon') or {})  # gói ghim ngày cut over không đưa lên sớm được
    goi = sorted({g for r in ds if r['ma'] in th.get('ma_gang', []) and r.get('emv_ngay') for g in r.get('lien_ket_wbs', []) if g in gang},
                 key=lambda g: [int(x) for x in g.split('.') if x.isdigit()])
    ma = [r['ma'] for r in ds if r['ma'] in th.get('ma_gang', []) and r.get('emv_ngay')]
    chon = da.get('phuong_an_du_tru_thoi_gian') or []
    chon = [chon] if isinstance(chon, str) else list(chon)
    if [k for k in chon if k not in PHUONG_AN]:
        print(f'[canh_bao] dau_vao/du_an.json phuong_an_du_tru_thoi_gian có khóa không hợp lệ {[k for k in chon if k not in PHUONG_AN]}, '
              f'chỉ dùng {", ".join(PHUONG_AN)}')
    dong = [[t, c.format(emv=so1(dt['emv_ngay_gang']), goi=', '.join(goi) or 'trên đường găng', ma=', '.join(ma)), a] for t, c, a in PHUONG_AN.values()]
    if chon:
        dong = [d + ['Có' if k in chon else 'Không'] for k, d in zip(PHUONG_AN, dong)]
        return {'cot': ['Phương án', 'Cách thực hiện', 'Ảnh hưởng', 'Áp dụng'], 'dong': dong, 'widths': [2000, 3600, 2800, 900], 'chon': chon}
    print(f'[canh_bao] Dự trữ thời gian thiếu {so1(dt["thieu"])} ngày làm việc. Nhóm chốt phương án và ghi dau_vao/du_an.json '
          f'phuong_an_du_tru_thoi_gian (một hoặc nhiều khóa: {", ".join(PHUONG_AN)})')
    return {'cot': ['Phương án', 'Cách thực hiện', 'Ảnh hưởng'], 'dong': dong, 'widths': [2200, 4000, 3100], 'chon': []}


def danh_gia_du_phong_chi_phi():
    """Giá trị và lời đánh giá dự phòng chi phí theo chi_phi.json: du_phong_hien_co, cach_tinh_du_phong, khoản B.
    Dự phòng là cả khoản B theo khóa du_phong_ca_khoan_b của chi_phi.json; chi_phi.json cũ chưa có khóa thì suy từ du_phong_hien_co bằng B."""
    dp, emv_ = float(cp['du_phong_hien_co']), float(th['tong_emv_tien'])
    cach, b = cp.get('cach_tinh_du_phong'), cp.get('B')
    ca_b = cp.get('du_phong_ca_khoan_b')
    if not isinstance(ca_b, bool):
        ca_b = b is not None and round(dp) >= round(float(b))
    if cach == 'nam_trong_chi_phi_khac':
        gia_tri = f'{loi.tien(dp)} đồng, ' + ('toàn bộ khoản B' if ca_b else f'nằm trong khoản B {loi.tien(b)} đồng')
    else:
        gia_tri = f'{loi.tien(dp)} đồng, ' + ('dòng dự phòng bằng tổng EMV' if cach == 'emv' else 'dòng dự phòng theo tỷ lệ')
    if dp >= emv_:
        dg_ = 'Đủ so với tổng EMV' + (f', thấp hơn cận trên {ty(th["tong_emv_tien_cao"])} triệu đồng' if dp < th.get('tong_emv_tien_cao', 0) else '')
    else:
        dg_ = f'Thiếu {ty(emv_ - dp)} triệu đồng so với tổng EMV'
    return gia_tri, dg_ + (' (khi toàn bộ khoản B được dùng làm dự phòng)' if cach == 'nam_trong_chi_phi_khac' and ca_b else '')


def bang_du_phong(dt, chon):
    md0 = lambda v: loi.so(v, 0)
    dp_gia_tri, dp_danh_gia = danh_gia_du_phong_chi_phi()
    ten_pa = ', '.join(PHUONG_AN[k][0][:1].lower() + PHUONG_AN[k][0][1:] for k in chon if k in PHUONG_AN)
    dong = [
        ['Tổng EMV theo khối lượng', f'{md0(th["tong_emv_md"])} MD ({khoang(th.get("tong_emv_md_thap", 0), th.get("tong_emv_md_cao", 0), md0)} MD)'],
        ['Tổng EMV theo chi phí', f'{ty(th["tong_emv_tien"])} triệu đồng ({khoang(th.get("tong_emv_tien_thap", 0), th.get("tong_emv_tien_cao", 0), ty)} triệu đồng)'],
        ['Dự phòng chi phí trong dự toán', dp_gia_tri],
        ['Đánh giá dự phòng chi phí', dp_danh_gia],
        ['Tổng EMV theo thời gian', f'{so1(th["tong_emv_ngay"])} ngày làm việc ({khoang(th.get("tong_emv_ngay_thap", 0), th.get("tong_emv_ngay_cao", 0), so1)})'],
        ['EMV thời gian của rủi ro trên đường găng hoặc gắn mốc cut over', f'{so1(dt["emv_ngay_gang"])} ngày làm việc '
         f'({khoang(dt["emv_ngay_gang_thap"], dt["emv_ngay_gang_cao"], so1)}), {dt["so_rui_ro_gang"]} rủi ro'],
        ['Dự trữ thời gian đến cut over theo master schedule', f'{loi.so(dt["du_tru"], 0)} ngày làm việc'],
        ['Đánh giá dự trữ thời gian', dt['danh_gia'] + (f', nhóm chọn {ten_pa}' if ten_pa else '')]]
    return {'cot': ['Chỉ tiêu', 'Giá trị'], 'dong': dong, 'widths': [5000, 4300], 'right_cols': [1]}


xs = {'cot': ['Mức', 'Xác suất', 'Giá trị dùng tính EMV', 'Cận tính khoảng EMV'],
      'dong': [[k, v, loi.pt(T['xac_suat_pt'][k]), (lambda c: f'{loi.pt(c[0])} đến {loi.pt(c[1])}')(T.get('xac_suat_khoang', {}).get(k, [0, 0]))]
               for k, v in T['xac_suat'].items()], 'widths': [800, 3900, 2200, 2400], 'center_cols': [0, 2, 3]}
muc = {'cot': ['Mức rủi ro', 'Điểm (xác suất x tác động)', 'Cách xử lý'], 'dong': [
    [T['ten_muc']['cao'], f'{T["muc"]["cao"][0]} đến {T["muc"]["cao"][1]}', 'Bắt buộc có kế hoạch ứng phó, dấu hiệu nhận biết, theo dõi hằng tuần, báo cáo trong mỗi kỳ'],
    [T['ten_muc']['trung_binh'], f'{T["muc"]["trung_binh"][0]} đến {T["muc"]["trung_binh"][1]}', 'Có biện pháp phòng ngừa, theo dõi theo sprint'],
    [T['ten_muc']['thap'], f'{T["muc"]["thap"][0]} đến {T["muc"]["thap"][1]}', 'Ghi nhận, rà soát cuối sprint']], 'widths': [1600, 2600, 5100], 'center_cols': [0, 1]}
nguon_mt = rr.get('ma_tran_ma') or rr['ma_tran']
mt = {'cot': ['Xác suất, tác động', '1', '2', '3', '4', '5'],
      'dong': [[r['xac_suat']] + [r[f'td{j}'] for j in range(1, 6)] for r in nguon_mt], 'widths': [1700] + [1520] * 5, 'center_cols': [0, 1, 2, 3, 4, 5]}
ng = da.get('nguong_canh_bao', {})
kpi = {'cot': ['Chỉ số', 'Ngưỡng vàng', 'Ngưỡng đỏ', 'Hành động khi chạm ngưỡng'], 'dong': [
    ['SPI', f'dưới {loi.so(ng.get("spi_vang", 0.95), 2)}', f'dưới {loi.so(ng.get("spi_do", 0.85), 2)}', 'Rà soát rủi ro tiến độ, kích hoạt kế hoạch ứng phó của rủi ro liên quan'],
    ['CPI', f'dưới {loi.so(ng.get("cpi_vang", 0.95), 2)}', f'dưới {loi.so(ng.get("cpi_do", 0.85), 2)}', 'Rà soát rủi ro chi phí, xem xét dùng dự phòng theo quy định'],
    ['Lỗi nghiêm trọng đang mở', 'từ 2', 'từ 4', 'Ưu tiên khắc phục, đánh giá lại rủi ro chất lượng']], 'widths': [1300, 1600, 1600, 4800]}
dt = danh_gia_du_tru()
pa = bang_phuong_an(dt)
chon_pa = pa.pop('chon')
cao = [r for r in ds if r['muc'] == 'cao']
hang = th.get('so_hang', {})
emv = {'tien_trieu': round(th['tong_emv_tien'] / 1e6), 'tien_trieu_thap': round(th.get('tong_emv_tien_thap', 0) / 1e6),
       'tien_trieu_cao': round(th.get('tong_emv_tien_cao', 0) / 1e6), 'md': round(th['tong_emv_md']), 'ngay': th['tong_emv_ngay']}
ghi_chu_td = (f'Mức tác động của mỗi rủi ro là mức cao nhất đạt được theo số ngày chậm, chi phí tác động so với {th.get("nguon_gia_co_so", "giá chào")} '
              f'{ty(th.get("gia_co_so", 0))} triệu đồng và điều kiện về mốc, hợp đồng. Mức chấm khác mức suy ra được ghi lý do trong sổ.') if NG else ''
loi.ghi_json('du_lieu/rui_ro_bang.json', {
    'xac_suat': xs, 'tac_dong': bang_tac_dong() if NG else {'cot': ['Mức', 'Tác động'], 'dong': [[k, v] for k, v in T['tac_dong'].items()]},
    'ghi_chu_tac_dong': ghi_chu_td, 'muc': muc, 'quy_doi_3x3': bang_quy_doi() if Q else {'cot': [''], 'dong': []},
    'ma_tran': mt, 'ma_tran_3x3': bang_ma_tran_3x3() if rr.get('ma_tran_3x3') else {'cot': [''], 'dong': []},
    'du_phong': bang_du_phong(dt, chon_pa), 'du_tru': dt, 'phuong_an_du_tru': pa, 'emv': emv, 'nguong': kpi, 'so_cao': len(cao),
    'ma_cao': ', '.join(r['ma'] for r in cao), 'so_hang': hang, 'ma_hang_a': ', '.join(r['ma'] for r in ds if r.get('hang') == 'A'),
    'so_co_hoi': th.get('so_co_hoi', 0)})
print(f'Đã tính bảng rủi ro: {len(ds)} rủi ro, {len(cao)} mức cao, hạng A {hang.get("A", 0)}. EMV {emv["tien_trieu"]} triệu đồng '
      f'(khoảng {emv["tien_trieu_thap"]} đến {emv["tien_trieu_cao"]}). Dự trữ thời gian {dt["danh_gia"].lower()} '
      f'(EMV trên đường găng hoặc cut over {so1(dt["emv_ngay_gang"])} ngày, dự trữ {loi.so(dt["du_tru"], 0)} ngày)')
