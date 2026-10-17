"""Trích dữ liệu HSMT dùng chung cho các tài liệu sau (WBS, lịch, dự toán, HSDT, kế hoạch...).

Dùng: python trich_hsmt.py [thu_muc_lam_viec_hsmt] [--bo-qua-khoa]     (mặc định hsmt_lam_viec)
Chạy sau khi skill hsmt-mau-5a hoàn thành (có HSMT_ket_qua.docx và hsmt_noi_dung_v*.json).
Dừng khi HSMT chưa đạt: bao_cao_kiem_tra.json chưa qua chay_quy_trinh.py ghi_nhan, kết luận vòng khác dat,
báo cáo không thuộc vòng cuối của sổ so_phat_hien.json, sổ còn mục mở, HSMT_ket_qua.docx khác bản ghi_nhan đã nâng
(md5_giao), vòng ghi trong tệp Word khác vòng của báo cáo, hoặc không có hsmt_noi_dung_v*.json khớp md5 nội dung ghi trong Word.
Dữ liệu trích lấy từ đúng tệp nội dung đã tạo ra tệp Word được giao.
Ra:
- du_lieu/hsmt.json: giá gói thầu, lịch, yêu cầu năng lực, nhân sự chủ chốt, tiêu chí kỹ thuật (kèm tiêu chí chi tiết
  ky_thuat.tieu_chi[].chi_tiet), Mẫu 01A, điều khoản hợp đồng (E-ĐKCT), hạng mục Mẫu 01A gắn từng đợt thanh toán
  (hop_dong.thanh_toan[].hang_muc_01a), phân định trách nhiệm Chương V mục 3.5 (phan_dinh), bảng dữ liệu (E-BDL),
  các điểm lệch RFP có căn cứ
- du_lieu/rfp_yeu_cau.json: danh mục yêu cầu RFP (bản sao từ thư mục làm việc HSMT)
- ket_qua/01_HSMT/HSMT.docx: bản HSMT đạt kiểm tra
Đăng ký phiên bản và ghi nhật ký bằng chứng.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import datetime as dt
import glob
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loi  # noqa: E402

sys.path.insert(0, os.path.join(loi.THU_MUC_SKILLS, 'hsmt-mau-5a', 'scripts'))
from quy_uoc import TEN_SO, hang_muc_theo_dot, md5_tep, vong_cua_word  # noqa: E402  quy ước viết E-ĐKC 13.1 và sổ phát hiện của skill hsmt-mau-5a

_ts = [x for x in sys.argv[1:] if not x.startswith('--')]
wd = loi.duong_dan(_ts[0] if _ts else 'hsmt_lam_viec')
if loi.da_ky_hop_dong() and '--bo-qua-khoa' not in sys.argv:
    loi.thoat_loi('HSMT đã khóa sau ký hợp đồng (đường cơ sở đấu thầu). Thay đổi ghi bằng phụ lục hợp đồng hoặc biên bản. Nếu thật sự cần trích lại, thêm --bo-qua-khoa.')
P = lambda n: os.path.join(wd, n)
for n in ('gia_tri_tinh.json', 'tham_so_chu_dau_tu.json', 'rfp_yeu_cau.json', 'HSMT_ket_qua.docx'):
    if not os.path.exists(P(n)):
        loi.thoat_loi(f'Thiếu {loi.tuong_doi(P(n))}. Chạy skill hsmt-mau-5a đến khi đạt kiểm tra trước.')


def kiem_hsmt_dat():
    """Chỉ trích HSMT đã đạt: kết luận vòng (sau lớp B và ghi_nhan) là dat, sổ phát hiện không còn mục mở."""
    bc_p = P('bao_cao_kiem_tra.json')
    if not os.path.exists(bc_p):
        loi.thoat_loi(f'Thiếu {loi.tuong_doi(bc_p)}. Chạy kiểm tra lớp B rồi chay_quy_trinh.py ghi_nhan của skill hsmt-mau-5a.')
    bc = json.load(open(bc_p, encoding='utf-8'))
    if 'phat_hien_mo' not in bc:
        loi.thoat_loi(f'{loi.tuong_doi(bc_p)} chưa được ghi nhận vòng. Chạy chay_quy_trinh.py ghi_nhan {loi.tuong_doi(wd)} của skill hsmt-mau-5a.')
    if bc.get('ket_luan') != 'dat':
        loi.thoat_loi(f'HSMT chưa đạt: kết luận vòng {bc.get("vong")} là {bc.get("ket_luan")}. Xử lý các mục chờ rồi chạy lại hoan_thien, lớp B, ghi_nhan.')
    so = json.load(open(P(TEN_SO), encoding='utf-8')) if os.path.exists(P(TEN_SO)) else {'vong': bc.get('vong'), 'phat_hien': []}
    if bc.get('vong') != so.get('vong'):
        loi.thoat_loi(f'Báo cáo kiểm tra thuộc vòng {bc.get("vong")}, sổ phát hiện đã ở vòng {so.get("vong")}. Chạy lại lớp B và ghi_nhan cho vòng mới.')
    mo = [x['id'] for x in so['phat_hien'] if x.get('trang_thai') == 'mo']
    if mo:
        loi.thoat_loi(f'Sổ phát hiện {loi.tuong_doi(P(TEN_SO))} còn {len(mo)} mục mở: {", ".join(mo)}.')
    return bc


def kiem_ban_giao(bc):
    """HSMT_ket_qua.docx đúng là bản ghi_nhan đã nâng ở vòng đạt. Trả tệp hsmt_noi_dung đã tạo ra bản này."""
    giao = P('HSMT_ket_qua.docx')
    if not bc.get('md5_giao') or md5_tep(giao) != bc['md5_giao']:
        loi.thoat_loi(f'HSMT_ket_qua.docx không phải bản đã kiểm tra và ghi nhận ở vòng {bc.get("vong")} (md5 khác md5_giao). Chạy lại ghi_nhan của vòng đạt.')
    vong_w, md5_nd = vong_cua_word(giao)
    if vong_w != str(bc.get('vong')):
        loi.thoat_loi(f'HSMT_ket_qua.docx thuộc vòng {vong_w or "không rõ"}, báo cáo kiểm tra thuộc vòng {bc.get("vong")}.')
    nd_khop = [f for f in glob.glob(P('hsmt_noi_dung_v*.json')) if md5_tep(f) == md5_nd]
    if not nd_khop:
        loi.thoat_loi('Không có hsmt_noi_dung_v*.json khớp nội dung của HSMT_ket_qua.docx (md5 ghi trong tệp Word). Chạy lại hoan_thien, lớp B, ghi_nhan.')
    return nd_khop[0]


nd_file = kiem_ban_giao(kiem_hsmt_dat())
gv = json.load(open(P('gia_tri_tinh.json'), encoding='utf-8'))
ts = json.load(open(P('tham_so_chu_dau_tu.json'), encoding='utf-8'))
rfp = json.load(open(P('rfp_yeu_cau.json'), encoding='utf-8'))
nd = json.load(open(nd_file, encoding='utf-8'))


def iso(d):
    return dt.datetime.strptime(d, '%d/%m/%Y').date().isoformat()


def bang(header2):
    for b in nd['blocks']:
        if b['t'] == 'table' and b['rows'] and [re.sub(r'\(\d\)$', '', str(c)).strip() for c in b['rows'][0][:2]] == header2:
            return b['rows']
    return []


def bang_ma(tien_to):
    out = {}
    for b in nd['blocks']:
        if b['t'] == 'table' and b['rows'] and str(b['rows'][0][0]).startswith(tien_to):
            for r in b['rows']:
                v = r[1] if len(r) > 1 else ''
                out[str(r[0])] = ' '.join(v) if isinstance(v, list) else str(v)
    return out


def so_diem(v):
    x = float(str(v).replace(',', '.'))
    return int(x) if x.is_integer() else x


def o_ds(c):
    return c if isinstance(c, list) else [c]


def tieu_chi_chi_tiet():
    """{stt tiêu chí tổng quát: [tiêu chí chi tiết]} từ Bảng tiêu chí chi tiết (dòng j.i), Mục 3 Chương III."""
    out = {}
    for r in bang(['STT', 'Tiêu chí chi tiết'])[1:]:
        m = re.fullmatch(r'(\d+)\.(\d+)', str(r[0]))
        if not m:
            continue
        ten, nd = (o_ds(r[1]) + [''])[:2]
        cb = ' '.join(o_ds(r[3]))
        tt = re.search(r'tối thiểu (\d+(?:,\d+)?) điểm', cb)
        muc = [re.match(r'^(.+?) \((\d+(?:,\d+)?) điểm\): (.*)$', x) for x in o_ds(r[4])]
        out.setdefault(int(m.group(1)), []).append({
            'stt': str(r[0]), 'ten': ten, 'noi_dung': nd, 'diem_toi_da': so_diem(r[2]), 'co_ban': cb.startswith('Có'),
            'diem_toi_thieu': so_diem(tt.group(1)) if tt else None,
            'muc_cham': [{'muc': x.group(1), 'diem': so_diem(x.group(2)), 'mo_ta': x.group(3)} for x in muc if x]})
    return out


def phan_dinh():
    """Chương V mục 3.5: tham số phân định (bỏ khóa ghi chú _...), hạn do tinh_gia_tri.py tính, các dòng bảng."""
    pd = {k: v for k, v in (ts.get('phan_dinh') or {}).items() if not k.startswith('_')}
    gpd = gv.get('phan_dinh') or {}
    han = gpd.get('han_cung_cap_thong_tin_he_thong')
    dong = [{'stt': int(r[0]), 'noi_dung': ' '.join(o_ds(r[1])), 'phan_dinh': ' '.join(o_ds(r[2]))}
            for r in bang(['STT', 'Nội dung'])[1:] if str(r[0]).isdigit() and len(r) == 3]
    ht = gpd.get('thoi_han_ha_tang') or {}  # ngày đầy đủ do tinh_gia_tri.py tính từ tham số dd/mm
    return {**pd, 'han_cung_cap_thong_tin_he_thong': han, 'han_cung_cap_thong_tin_he_thong_iso': iso(han) if han else None,
            'thoi_han_ha_tang': ht, 'thoi_han_ha_tang_iso': {k: iso(v) for k, v in ht.items()},
            'dot_xac_nhan_dac_ta': gpd.get('dot_xac_nhan_dac_ta'), 'dong': dong}


def thanh_toan(e_dkct):
    """Các đợt của tham số kèm hang_muc_01a: STT hạng mục Mẫu 01A ghi trong dòng đợt đó tại Mục 13.1 E-ĐKCT."""
    van = next((v for k, v in e_dkct.items() if k.replace(' ', '').startswith('E-ĐKC13.1')), '')
    hm = hang_muc_theo_dot(van)
    return [{**x, 'hang_muc_01a': hm.get(int(x['dot']), [])} for x in gv['hop_dong']['thanh_toan']]


m01a = bang(['STT', 'Danh mục dịch vụ'])
kt = bang(['STT', 'Tiêu chí tổng quát'])
ns = bang(['STT', 'Vị trí công việc'])
cs = ts['chinh_sach']
L = gv['lich']
tc_ct = tieu_chi_chi_tiet()
e_dkct = bang_ma('E-ĐKC')
hsmt = {
    'goi_thau': {**ts['goi_thau'], 'chu_dau_tu': ts['chu_dau_tu']['ten']},
    'lich': {**L, 'cut_over_iso': iso(L['cut_over']), 'hop_dong_hieu_luc_iso': iso(L['hop_dong_hieu_luc_du_kien']),
             'dong_thau_iso': iso(L['dong_thau']), 'phat_hanh_iso': iso(L['phat_hanh'])},
    'tien': {k: int(v.replace('.', '')) for k, v in gv['tien'].items()},
    'thoi_han': gv['thoi_han'],
    'nang_luc': gv['nang_luc'],
    'ky_thuat': {'tieu_chi': [{'stt': int(r[0]), 'ten': r[1], 'diem_toi_da': int(r[2]), 'diem_toi_thieu': int(r[3]), 'chi_tiet': tc_ct.get(int(r[0]), [])}
                              for r in kt[1:] if str(r[0]).isdigit()],
                 'tong_toi_thieu': gv['ky_thuat']['tong_toi_thieu']},
    'nhan_su_chu_chot': [{'stt': int(r[0]), 'vi_tri': r[1], 'so_luong': int(r[2]), 'kinh_nghiem': r[3], 'chung_chi': r[4]} for r in ns[1:] if str(r[0]).isdigit()],
    'mau_01a': [{'stt': int(r[0]), 'danh_muc': r[1], 'mo_ta': r[2], 'khoi_luong': r[3], 'don_vi': r[4], 'dia_diem': r[5], 'ngay_hoan_thanh': r[6]}
                for r in m01a[1:] if str(r[0]).isdigit()],
    'hop_dong': {**gv['hop_dong'], 'bao_hanh_thang': 12, 'bao_lanh_bao_hanh_phan_tram': cs.get('bao_lanh_bao_hanh_phan_tram'),
                 'phat_cham_tien_do_phan_tram_ngay': cs.get('phat_cham_tien_do_phan_tram_ngay'), 'phat_toi_da_phan_tram': cs.get('phat_toi_da_phan_tram'),
                 'ty_le_nha_thau_phu_toi_da_phan_tram': cs.get('ty_le_nha_thau_phu_toi_da_phan_tram'), 'thanh_toan_trong_ngay': cs.get('thanh_toan_trong_ngay'),
                 'phat_khong_huy_dong_nhan_su_phan_tram_ngay': cs.get('phat_khong_huy_dong_nhan_su_phan_tram_ngay'),
                 'gia_han_khi_chu_dau_tu_cung_cap_cham': cs.get('gia_han_khi_chu_dau_tu_cung_cap_cham'),
                 'thay_the_nhan_su_ngay': cs.get('thay_the_nhan_su_ngay'), 'thanh_toan': thanh_toan(e_dkct)},
    'phan_dinh': phan_dinh(),
    'e_bdl': bang_ma('E-CDNT'),
    'e_dkct': e_dkct,
    'lech_rfp': [{'ma': y['ma'], 'nguyen_van': y['nguyen_van'], 'can_cu': y.get('can_cu_lech', '')} for y in rfp['yeu_cau'] if y.get('xu_ly') == 'lech_co_can_cu'],
}
m = re.search(r'Thời hạn trách nhiệm đối với sai sót:\s*(\d+)\s*tháng', hsmt['e_dkct'].get('E-ĐKC 20.1', ''))
if m:
    hsmt['hop_dong']['bao_hanh_thang'] = int(m.group(1))
if not hsmt['mau_01a']:
    loi.thoat_loi('Không tìm thấy bảng Mẫu 01A trong nội dung HSMT')
thieu_ct = [t['stt'] for t in hsmt['ky_thuat']['tieu_chi'] if not t['chi_tiet']]
if thieu_ct:
    loi.thoat_loi(f'Không tìm thấy tiêu chí chi tiết của tiêu chí kỹ thuật {thieu_ct} trong nội dung HSMT')
if not any(x['hang_muc_01a'] for x in hsmt['hop_dong']['thanh_toan']):
    loi.thoat_loi('Mục 13.1 E-ĐKCT chưa nêu hạng mục Mẫu số 01A gắn từng đợt thanh toán')

loi.ghi_json('du_lieu/hsmt.json', hsmt)
loi.ghi_json('du_lieu/rfp_yeu_cau.json', rfp)
os.makedirs(loi.duong_dan('ket_qua/01_HSMT'), exist_ok=True)
shutil.copy(P('HSMT_ket_qua.docx'), loi.duong_dan('ket_qua/01_HSMT/HSMT.docx'))
for f in glob.glob(P('bao_cao_kiem_tra*.json')):
    os.makedirs(loi.duong_dan('bang_chung/kiem_tra'), exist_ok=True)
    shutil.copy(f, loi.duong_dan('bang_chung/kiem_tra/hsmt_' + os.path.basename(f)))
pbs = loi.hoan_tat_buoc('hsmt', 'Trích dữ liệu HSMT dùng chung, sao chép HSMT đạt kiểm tra vào ket_qua', chi_tiet={'mau_01a': len(hsmt['mau_01a'])})
print(f'Đã trích du_lieu/hsmt.json: {len(hsmt["mau_01a"])} hạng mục Mẫu 01A, {len(hsmt["ky_thuat"]["tieu_chi"])} tiêu chí kỹ thuật '
      f'({sum(len(t["chi_tiet"]) for t in hsmt["ky_thuat"]["tieu_chi"])} tiêu chí chi tiết), {len(hsmt["e_dkct"])} mục E-ĐKCT, '
      f'{len(hsmt["phan_dinh"]["dong"])} dòng phân định, {len(rfp["yeu_cau"])} yêu cầu RFP')
print('  Hạng mục Mẫu 01A theo đợt: ' + '; '.join(f'Đợt {x["dot"]}: {x["hang_muc_01a"] or "không"}' for x in hsmt['hop_dong']['thanh_toan']))
for k, v in pbs.items():
    print(f'  {k}: phiên bản {v}')
