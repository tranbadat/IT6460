"""Bước 3. Tính các giá trị định lượng của HSMT từ mốc RFP, tham số chủ đầu tư và quy tắc của Mẫu 5A, Luật Đấu thầu.

Dùng: python3 tinh_gia_tri.py <tham_so_chu_dau_tu.json> <rfp_yeu_cau.json> <gia_tri_tinh.json>
Mọi con số trong HSMT (ngày, tiền, tỷ lệ, mốc năm) lấy từ file ra của script này để các agent khác nhau
cho cùng một kết quả. Script dừng và báo lỗi nếu giá trị vi phạm giới hạn luật định.
"""
import json, sys
from datetime import date, timedelta

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
doanh_thu = gia * cs['he_so_k_doanh_thu']  # gói thầu dưới 12 tháng: giá gói thầu x k
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
  'ty_le_hop_dong_tuong_tu': cs['ty_le_hop_dong_tuong_tu_phan_tram'],
 },
 'ky_thuat': {'trong_so': w, 'diem_toi_thieu': diem_tt, 'tong_toi_thieu': cs['diem_ky_thuat_toi_thieu_phan_tram']},
 'hop_dong': {
  'bao_dam_thuc_hien_phan_tram': cs['ty_le_bao_dam_thuc_hien_phan_tram'], 'tam_ung_phan_tram': cs['tam_ung_phan_tram'],
  'thanh_toan': cs['thanh_toan'], 'nha_thau_phu_toi_da_phan_tram': cs['ty_le_nha_thau_phu_toi_da_phan_tram'],
 },
 'loi': loi, 'canh_bao': canh_bao,
}
json.dump(kq, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: kq[k] for k in ('lich', 'tien', 'nang_luc')}, ensure_ascii=False))
for c in canh_bao:
    print('CẢNH BÁO:', c)
if loi:
    print('LỖI:', *loi, sep='\n- ')
    sys.exit(1)
