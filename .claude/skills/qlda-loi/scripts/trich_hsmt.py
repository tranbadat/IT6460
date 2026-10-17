"""Trích dữ liệu HSMT dùng chung cho các tài liệu sau (WBS, lịch, dự toán, HSDT, kế hoạch...).

Dùng: python trich_hsmt.py [thu_muc_lam_viec_hsmt] [--bo-qua-khoa]     (mặc định hsmt_lam_viec)
Chạy sau khi skill hsmt-mau-5a hoàn thành (có HSMT_ket_qua.docx và hsmt_noi_dung_v*.json).
Ra:
- du_lieu/hsmt.json: giá gói thầu, lịch, yêu cầu năng lực, nhân sự chủ chốt, tiêu chí kỹ thuật, Mẫu 01A,
  điều khoản hợp đồng (E-ĐKCT), bảng dữ liệu (E-BDL), các điểm lệch RFP có căn cứ
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

_ts = [x for x in sys.argv[1:] if not x.startswith('--')]
wd = loi.duong_dan(_ts[0] if _ts else 'hsmt_lam_viec')
if loi.da_ky_hop_dong() and '--bo-qua-khoa' not in sys.argv:
    loi.thoat_loi('HSMT đã khóa sau ký hợp đồng (đường cơ sở đấu thầu). Thay đổi ghi bằng phụ lục hợp đồng hoặc biên bản. Nếu thật sự cần trích lại, thêm --bo-qua-khoa.')
P = lambda n: os.path.join(wd, n)
for n in ('gia_tri_tinh.json', 'tham_so_chu_dau_tu.json', 'rfp_yeu_cau.json', 'HSMT_ket_qua.docx'):
    if not os.path.exists(P(n)):
        loi.thoat_loi(f'Thiếu {loi.tuong_doi(P(n))}. Chạy skill hsmt-mau-5a đến khi đạt kiểm tra trước.')
gv = json.load(open(P('gia_tri_tinh.json'), encoding='utf-8'))
ts = json.load(open(P('tham_so_chu_dau_tu.json'), encoding='utf-8'))
rfp = json.load(open(P('rfp_yeu_cau.json'), encoding='utf-8'))
nd_files = sorted(glob.glob(P('hsmt_noi_dung_v*.json')), key=lambda f: int(re.search(r'_v(\d+)\.json$', f).group(1)))
nd = json.load(open(nd_files[-1], encoding='utf-8'))


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


m01a = bang(['STT', 'Danh mục dịch vụ'])
kt = bang(['STT', 'Tiêu chí tổng quát'])
ns = bang(['STT', 'Vị trí công việc'])
cs = ts['chinh_sach']
L = gv['lich']
hsmt = {
    'goi_thau': {**ts['goi_thau'], 'chu_dau_tu': ts['chu_dau_tu']['ten']},
    'lich': {**L, 'cut_over_iso': iso(L['cut_over']), 'hop_dong_hieu_luc_iso': iso(L['hop_dong_hieu_luc_du_kien']),
             'dong_thau_iso': iso(L['dong_thau']), 'phat_hanh_iso': iso(L['phat_hanh'])},
    'tien': {k: int(v.replace('.', '')) for k, v in gv['tien'].items()},
    'thoi_han': gv['thoi_han'],
    'nang_luc': gv['nang_luc'],
    'ky_thuat': {'tieu_chi': [{'stt': int(r[0]), 'ten': r[1], 'diem_toi_da': int(r[2]), 'diem_toi_thieu': int(r[3])} for r in kt[1:] if str(r[0]).isdigit()],
                 'tong_toi_thieu': gv['ky_thuat']['tong_toi_thieu']},
    'nhan_su_chu_chot': [{'stt': int(r[0]), 'vi_tri': r[1], 'so_luong': int(r[2]), 'kinh_nghiem': r[3], 'chung_chi': r[4]} for r in ns[1:] if str(r[0]).isdigit()],
    'mau_01a': [{'stt': int(r[0]), 'danh_muc': r[1], 'mo_ta': r[2], 'khoi_luong': r[3], 'don_vi': r[4], 'dia_diem': r[5], 'ngay_hoan_thanh': r[6]}
                for r in m01a[1:] if str(r[0]).isdigit()],
    'hop_dong': {**gv['hop_dong'], 'bao_hanh_thang': 12, 'bao_lanh_bao_hanh_phan_tram': cs.get('bao_lanh_bao_hanh_phan_tram'),
                 'phat_cham_tien_do_phan_tram_ngay': cs.get('phat_cham_tien_do_phan_tram_ngay'), 'phat_toi_da_phan_tram': cs.get('phat_toi_da_phan_tram'),
                 'ty_le_nha_thau_phu_toi_da_phan_tram': cs.get('ty_le_nha_thau_phu_toi_da_phan_tram'), 'thanh_toan_trong_ngay': cs.get('thanh_toan_trong_ngay'),
                 'thay_the_nhan_su_ngay': cs.get('thay_the_nhan_su_ngay')},
    'e_bdl': bang_ma('E-CDNT'),
    'e_dkct': bang_ma('E-ĐKC'),
    'lech_rfp': [{'ma': y['ma'], 'nguyen_van': y['nguyen_van'], 'can_cu': y.get('can_cu_lech', '')} for y in rfp['yeu_cau'] if y.get('xu_ly') == 'lech_co_can_cu'],
}
m = re.search(r'Thời hạn trách nhiệm đối với sai sót:\s*(\d+)\s*tháng', hsmt['e_dkct'].get('E-ĐKC 20.1', ''))
if m:
    hsmt['hop_dong']['bao_hanh_thang'] = int(m.group(1))
if not hsmt['mau_01a']:
    loi.thoat_loi('Không tìm thấy bảng Mẫu 01A trong nội dung HSMT')

loi.ghi_json('du_lieu/hsmt.json', hsmt)
loi.ghi_json('du_lieu/rfp_yeu_cau.json', rfp)
os.makedirs(loi.duong_dan('ket_qua/01_HSMT'), exist_ok=True)
shutil.copy(P('HSMT_ket_qua.docx'), loi.duong_dan('ket_qua/01_HSMT/HSMT.docx'))
for f in glob.glob(P('bao_cao_kiem_tra*.json')):
    os.makedirs(loi.duong_dan('bang_chung/kiem_tra'), exist_ok=True)
    shutil.copy(f, loi.duong_dan('bang_chung/kiem_tra/hsmt_' + os.path.basename(f)))
pbs = loi.hoan_tat_buoc('hsmt', 'Trích dữ liệu HSMT dùng chung, sao chép HSMT đạt kiểm tra vào ket_qua', chi_tiet={'mau_01a': len(hsmt['mau_01a'])})
print(f'Đã trích du_lieu/hsmt.json: {len(hsmt["mau_01a"])} hạng mục Mẫu 01A, {len(hsmt["ky_thuat"]["tieu_chi"])} tiêu chí kỹ thuật, '
      f'{len(hsmt["e_dkct"])} mục E-ĐKCT, {len(rfp["yeu_cau"])} yêu cầu RFP')
for k, v in pbs.items():
    print(f'  {k}: phiên bản {v}')
