"""Bước 3. Tính các giá trị định lượng của HSMT từ mốc RFP, tham số chủ đầu tư và quy tắc của Mẫu 5A, Luật Đấu thầu.

Dùng: python3 tinh_gia_tri.py <tham_so_chu_dau_tu.json> <rfp_yeu_cau.json> <gia_tri_tinh.json>
Mọi con số trong HSMT (ngày, tiền, tỷ lệ, mốc năm) lấy từ file ra của script này để các agent khác nhau
cho cùng một kết quả. Script dừng và báo lỗi nếu giá trị vi phạm giới hạn luật định.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json, os, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quy_uoc import (BEN, CAU_HINH_HA_TANG, HA_TANG_CHU_DAU_TU, DO_PHI_CHUC_NANG, HA_TANG, KIEM_THU_VAN_HANH, THAY_DOI_HE_THONG, THOI_HAN_HA_TANG, THUE_GTGT, lay,  # noqa: E402
                     tham_so_thieu)

ts = json.load(open(sys.argv[1], encoding='utf-8'))
rfp = json.load(open(sys.argv[2], encoding='utf-8'))
out_path = sys.argv[3]
cs, gt, lich = ts['chinh_sach'], ts['goi_thau'], ts['lich']
nam = ts['nam_ap_dung_cho_20XX']
loi, canh_bao = [], []


def ngay(dm, y=nam):
    d, m = [int(x) for x in dm.split('/')[:2]]
    return date(y, m, d)


def f_ngay(d):
    return f'{d.day:02d}/{d.month:02d}/{d.year}'


def f_ngay_chu(d):
    return f'{d.day:02d} tháng {d.month:02d} năm {d.year}'


def tien(v):
    return format(int(round(v)), ',').replace(',', '.')


def lui_ngay_lam_viec(d, n):
    k = d
    while n > 0:
        k -= timedelta(days=1)
        if k.weekday() < 5:
            n -= 1
    return k


moc = rfp['moc']
phat_hanh = ngay(moc['phat_hanh'])
dong_thau = ngay(moc['han_nop'])
cut_over = ngay(moc['cut_over'])
hd_hieu_luc = ngay(lich['ngay_hop_dong_hieu_luc_du_kien'])
gia = gt['gia_goi_thau']

# Lịch đấu thầu
so_ngay_chuan_bi = (dong_thau - phat_hanh).days
toi_thieu = 9 if gia <= 10_000_000_000 else 18
if so_ngay_chuan_bi < toi_thieu:
    loi.append(f'Thời gian chuẩn bị E-HSDT {so_ngay_chuan_bi} ngày, tối thiểu {toi_thieu} ngày')
han_hoi = lui_ngay_lam_viec(dong_thau, 3)
han_tra_loi = lui_ngay_lam_viec(dong_thau, 2)
if moc.get('hoi_dap_den'):
    hoi_rfp = ngay(moc['hoi_dap_den'])
    if hoi_rfp > han_hoi:
        canh_bao.append(f'RFP cho hỏi đáp đến {f_ngay(hoi_rfp)}, muộn hơn hạn làm rõ hợp lệ {f_ngay(han_hoi)}: ghi thành điểm lệch RFP có căn cứ')
hn = lich['hoi_nghi_tien_dau_thau']
hoi_nghi = ngay(hn['ngay']) if hn.get('co') else None
if hoi_nghi and not (phat_hanh <= hoi_nghi <= han_hoi):
    loi.append('Hội nghị tiền đấu thầu phải nằm trong khoảng phát hành đến hạn làm rõ')
h, m = [int(x) for x in lich['gio_dong_thau'].split(':')]
mo_m = m + lich['phut_mo_thau_sau_dong_thau']
gio_mo = f'{h + mo_m // 60} giờ {mo_m % 60:02d}'
gio_dong = f'{h} giờ {m:02d}'
if hd_hieu_luc <= dong_thau:
    loi.append('Ngày hợp đồng hiệu lực dự kiến phải sau thời điểm đóng thầu')
so_tuan = round((cut_over - hd_hieu_luc).days / 7)

# Bảo đảm dự thầu
bddt = gia * cs['ty_le_bao_dam_du_thau_phan_tram'] / 100
if not (1 <= cs['ty_le_bao_dam_du_thau_phan_tram'] <= 3):
    loi.append('Tỷ lệ bảo đảm dự thầu ngoài khoảng cho phép')
hl_bddt = cs['hieu_luc_hsdt_ngay'] + cs['bao_dam_du_thau_cong_them_ngay']
if cs['hoan_tra_bao_dam_du_thau_ngay'] > 14:
    loi.append('Hoàn trả bảo đảm dự thầu không quá 14 ngày')

# Năng lực, kinh nghiệm
nam_dong = dong_thau.year
moc_lich_su = date(nam_dong - cs['nam_lich_su_hop_dong'], 1, 1)
moc_tuong_tu = date(nam_dong - cs['nam_hop_dong_tuong_tu'], 1, 1)
if not (3 <= cs['nam_hop_dong_tuong_tu'] <= 5):
    loi.append('Số năm hợp đồng tương tự thông thường từ 03 đến 05 năm')
# năm tài chính gần nhất: đóng thầu trong 3 tháng đầu năm thì lùi thêm một năm
nam_tc_gan_nhat = nam_dong - 2 if dong_thau.month <= 3 else nam_dong - 1
nam_doanh_thu = list(range(nam_tc_gan_nhat - cs['nam_doanh_thu'] + 1, nam_tc_gan_nhat + 1))


def thue_gtgt():
    """(giá trị thuế GTGT trong giá gói thầu, thông tin cho Bảng số 01 dòng 3). Tham số trống thì coi bằng 0 và TS01 báo chờ."""
    loai, can_cu = cs.get('thue_gtgt_goi_thau'), str(cs.get('can_cu_thue_gtgt') or '').strip()
    tt = {'loai': loai, 'thue_suat_phan_tram': None, 'gia_tri_thue': None, 'can_cu': can_cu or None}
    if loai is None:
        return 0, tt
    if loai not in THUE_GTGT:
        loi.append(f'chinh_sach.thue_gtgt_goi_thau phải là một trong {list(THUE_GTGT)}'); return 0, tt
    if loai == 'khong_chiu_thue':
        if not can_cu:
            loi.append('chinh_sach.thue_gtgt_goi_thau = khong_chiu_thue cần can_cu_thue_gtgt (văn bản, điều khoản quy định không chịu thuế)')
        return 0, {**tt, 'thue_suat_phan_tram': 0, 'gia_tri_thue': tien(0)}
    r = cs.get('thue_suat_gtgt_phan_tram')
    if isinstance(r, bool) or not isinstance(r, (int, float)) or not 0 < r <= 100:
        loi.append('chinh_sach.thue_gtgt_goi_thau = chiu_thue cần thue_suat_gtgt_phan_tram lớn hơn 0, không quá 100'); return 0, tt
    vat = gia - gia / (1 + r / 100)  # giá gói thầu đã gồm thuế GTGT
    return vat, {**tt, 'thue_suat_phan_tram': r, 'gia_tri_thue': tien(vat)}


def hang_muc_tuong_tu():
    """Hạng mục chính và giá trị từng hạng mục khi cho cộng gộp hợp đồng tương tự (ghi chú (11) Bảng số 01)."""
    cg = cs.get('hop_dong_tuong_tu_cong_gop')
    if cg is not None and not isinstance(cg, bool):
        loi.append('chinh_sach.hop_dong_tuong_tu_cong_gop phải là true hoặc false')
    if cg is not True:
        return []
    ds = cs.get('hang_muc_tuong_tu')
    hop_le = isinstance(ds, list) and ds and all(isinstance(x, dict) and str(x.get('ten') or '').strip() and not isinstance(x.get('gia_tri'), bool)
                                                and isinstance(x.get('gia_tri'), (int, float)) and x['gia_tri'] > 0 for x in ds)
    if not hop_le:
        loi.append('chinh_sach.hop_dong_tuong_tu_cong_gop = true cần hang_muc_tuong_tu [{ten, gia_tri}]: hạng mục chính và giá trị tối thiểu từng hạng mục (ghi chú (11) Bảng số 01)')
        return []
    return [{'ten': x['ten'].strip(), 'gia_tri': tien(x['gia_tri'])} for x in ds]


vat, thue = thue_gtgt()
doanh_thu = (gia - vat) * cs['he_so_k_doanh_thu']  # ghi chú (6) Bảng số 01, gói thầu dưới 12 tháng: (giá gói thầu - thuế GTGT) x k
hm_tuong_tu = hang_muc_tuong_tu()
ns = cs.get('phat_khong_huy_dong_nhan_su_phan_tram_ngay')
if ns is not None and (isinstance(ns, bool) or not isinstance(ns, (int, float)) or not 0 <= ns <= cs['phat_toi_da_phan_tram']):
    loi.append('chinh_sach.phat_khong_huy_dong_nhan_su_phan_tram_ngay phải từ 0 (không áp dụng phạt riêng) đến mức phạt tối đa')
if cs.get('gia_han_khi_chu_dau_tu_cung_cap_cham') is not None and not isinstance(cs['gia_han_khi_chu_dau_tu_cung_cap_cham'], bool):
    loi.append('chinh_sach.gia_han_khi_chu_dau_tu_cung_cap_cham phải là true hoặc false')
hd_tuong_tu = gia * cs['ty_le_hop_dong_tuong_tu_phan_tram'] / 100
w = cs['trong_so_tieu_chi_ky_thuat']
if sum(w) != 100:
    loi.append('Tổng trọng số tiêu chí kỹ thuật phải là 100')
diem_tt = [round(x * cs['diem_toi_thieu_tung_tieu_chi_phan_tram'] / 100) for x in w]

# Hợp đồng
if not (2 <= cs['ty_le_bao_dam_thuc_hien_phan_tram'] <= 10):
    loi.append('Bảo đảm thực hiện hợp đồng phải từ 2% đến 10%')
hl_bdth = cut_over + timedelta(days=cs['bao_dam_thuc_hien_sau_cut_over_ngay'])
tong_tt = sum(x['phan_tram'] for x in cs['thanh_toan'])
if tong_tt != 100:
    loi.append(f'Tổng các đợt thanh toán là {tong_tt}%, phải là 100%')
if cs['tam_ung_phan_tram'] and cs['thanh_toan'][0]['phan_tram'] != cs['tam_ung_phan_tram']:
    loi.append('Đợt 1 phải bằng tỷ lệ tạm ứng')
if cs['tiet_kiem_chi_phi_phan_tram'] > 50:
    canh_bao.append('Tỷ lệ thưởng tiết kiệm chi phí thường không quá 50%')
if cs['ty_le_tang_giam_khoi_luong_phan_tram'] > 10:
    loi.append('Tỷ lệ tăng, giảm khối lượng không vượt 10%')
pkss = cs.get('phat_khac_phuc_sai_sot_phan_tram')
if pkss is not None and not (0 < pkss <= 100):
    loi.append('Tỷ lệ phạt khắc phục sai sót phải lớn hơn 0 và không quá 100% chi phí khắc phục')


def kiem_phan_dinh(pd):
    """Kiểm tra nhóm phan_dinh (Chương V mục 3.5). Trả ngày hạn cung cấp thông tin hệ thống hiện có hoặc None."""
    for k, _ in HA_TANG:
        v = lay(pd, 'ha_tang_ben_cung_cap.' + k)
        if v is not None and v not in BEN:
            loi.append(f'phan_dinh.ha_tang_ben_cung_cap.{k} phải là một trong {list(BEN)}')
    dk = pd.get('dieu_kien_do_phi_chuc_nang')
    if dk is not None and dk not in DO_PHI_CHUC_NANG:
        so = [dk.get(k) for k in ('so_nguoi_dung_dong_thoi', 'ty_le_san_sang_phan_tram')] if isinstance(dk, dict) else [None]
        if not all(isinstance(v, (int, float)) and v > 0 for v in so) or so[1] > 100:
            loi.append('phan_dinh.dieu_kien_do_phi_chuc_nang phải là "nha_thau_de_xuat" hoặc {so_nguoi_dung_dong_thoi, ty_le_san_sang_phan_tram} dương, tỷ lệ không quá 100')
    tt = pd.get('thong_tin_he_thong_hien_co')
    if tt is None:
        return None
    thieu = [k for k in ('ten', 'tai_lieu', 'thoi_han_cung_cap_ngay') if tt.get(k) in (None, '', [])]
    if thieu:
        loi.append(f'phan_dinh.thong_tin_he_thong_hien_co thiếu {thieu}')
        return None
    han = hd_hieu_luc + timedelta(days=tt['thoi_han_cung_cap_ngay'])
    if han >= cut_over:
        loi.append('Hạn cung cấp thông tin hệ thống hiện có phải trước ngày cut over')
    return han


def thoi_han_ha_tang(pd):
    """{khóa: dd/mm/yyyy} của phan_dinh.thoi_han_ha_tang. Ngày phải từ ngày hợp đồng hiệu lực đến trước cut over."""
    for k, gt in (('kiem_thu_van_hanh_tren', KIEM_THU_VAN_HANH), ('thay_doi_he_thong_hien_co', THAY_DOI_HE_THONG)):
        if pd.get(k) is not None and pd[k] not in gt:
            loi.append(f'phan_dinh.{k} phải là một trong {list(gt)}')
    ch = pd.get('cau_hinh_ha_tang')
    if ch is not None and ch not in CAU_HINH_HA_TANG and not (
            isinstance(ch, dict) and ch and all(k in HA_TANG_CHU_DAU_TU and isinstance(v, str) and v.strip() for k, v in ch.items())):
        loi.append(f'phan_dinh.cau_hinh_ha_tang phải là "nha_thau_de_xuat" hoặc đối tượng cấu hình {{{", ".join(HA_TANG_CHU_DAU_TU)}: mô tả}}')
    out = {}
    for k, ten in THOI_HAN_HA_TANG:
        v = lay(pd, 'thoi_han_ha_tang.' + k)
        if v is None:
            continue
        try:
            d = ngay(v)
        except (ValueError, AttributeError):
            loi.append(f'phan_dinh.thoi_han_ha_tang.{k} phải có dạng dd/mm, hiện là {v}'); continue
        if not (hd_hieu_luc <= d < cut_over):
            loi.append(f'Thời hạn bàn giao {ten} {f_ngay(d)} phải từ ngày hợp đồng có hiệu lực {f_ngay(hd_hieu_luc)} đến trước ngày cut over {f_ngay(cut_over)}')
        out[k] = f_ngay(d)
    return out


han_tt = kiem_phan_dinh(ts.get('phan_dinh') or {})
han_ht = thoi_han_ha_tang(ts.get('phan_dinh') or {})
cdt = ts['chu_dau_tu']
if cdt['ten'].lower() in str(cdt.get('dia_chi', '')).lower():
    loi.append('chu_dau_tu.dia_chi phải là địa chỉ cụ thể (số nhà, đường, phường, tỉnh hoặc thành phố), không ghi theo tên Chủ đầu tư')
for k, vt in tham_so_thieu(ts):
    canh_bao.append(f'Thiếu tham số {k} ({vt}): HSMT giữ câu mẫu kèm dấu chờ Chủ đầu tư quyết định, kết luận kiểm tra là cho_nguoi_dung đến khi bổ sung')
dot_dac_ta = next((x['dot'] for x in cs['thanh_toan'] if 'đặc tả' in x['su_kien']), None)

kq = {
 'nam': nam,
 'lich': {
  'phat_hanh': f_ngay(phat_hanh), 'dong_thau': f_ngay(dong_thau), 'gio_dong_thau': gio_dong, 'gio_mo_thau': gio_mo,
  'so_ngay_chuan_bi_hsdt': so_ngay_chuan_bi, 'han_nha_thau_de_nghi_lam_ro': f_ngay(han_hoi), 'han_chu_dau_tu_tra_loi': f_ngay(han_tra_loi),
  'hoi_nghi_tien_dau_thau': ({'ngay': f_ngay(hoi_nghi), 'gio': hn['gio'].replace(':', ' giờ ')} if hoi_nghi else None),
  'hop_dong_hieu_luc_du_kien': f_ngay(hd_hieu_luc), 'cut_over': f_ngay(cut_over), 'so_tuan_thuc_hien': so_tuan,
 },
 'tien': {
  'gia_goi_thau': tien(gia), 'bao_dam_du_thau': tien(bddt), 'doanh_thu_binh_quan_toi_thieu': tien(doanh_thu),
  'hop_dong_tuong_tu_toi_thieu': tien(hd_tuong_tu),
 },
 'thoi_han': {
  'hieu_luc_hsdt_ngay': cs['hieu_luc_hsdt_ngay'], 'hieu_luc_bao_dam_du_thau_ngay': hl_bddt,
  'hoan_tra_bao_dam_du_thau_ngay': cs['hoan_tra_bao_dam_du_thau_ngay'],
  'hieu_luc_bao_dam_thuc_hien_den': f_ngay_chu(hl_bdth),
 },
 'nang_luc': {
  'moc_lich_su_hop_dong': f_ngay_chu(moc_lich_su), 'moc_hop_dong_tuong_tu': f_ngay_chu(moc_tuong_tu),
  'nam_tai_chinh_gan_nhat': nam_tc_gan_nhat, 'cac_nam_doanh_thu': nam_doanh_thu, 'he_so_k': cs['he_so_k_doanh_thu'],
  'ty_le_hop_dong_tuong_tu': cs['ty_le_hop_dong_tuong_tu_phan_tram'], 'thue_gtgt': thue,
  'hop_dong_tuong_tu_cong_gop': cs.get('hop_dong_tuong_tu_cong_gop'), 'hang_muc_tuong_tu': hm_tuong_tu,
 },
 'ky_thuat': {'trong_so': w, 'diem_toi_thieu': diem_tt, 'tong_toi_thieu': cs['diem_ky_thuat_toi_thieu_phan_tram']},
 'hop_dong': {
  'bao_dam_thuc_hien_phan_tram': cs['ty_le_bao_dam_thuc_hien_phan_tram'], 'tam_ung_phan_tram': cs['tam_ung_phan_tram'],
  'thanh_toan': cs['thanh_toan'], 'nha_thau_phu_toi_da_phan_tram': cs['ty_le_nha_thau_phu_toi_da_phan_tram'],
 },
 'phan_dinh': {'han_cung_cap_thong_tin_he_thong': f_ngay(han_tt) if han_tt else None, 'dot_xac_nhan_dac_ta': dot_dac_ta, 'thoi_han_ha_tang': han_ht},
 'loi': loi, 'canh_bao': canh_bao,
}
json.dump(kq, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: kq[k] for k in ('lich', 'tien', 'nang_luc')}, ensure_ascii=False))
for c in canh_bao:
    print('CẢNH BÁO:', c)
if loi:
    print('LỖI:', *loi, sep='\n- ')
    sys.exit(1)
