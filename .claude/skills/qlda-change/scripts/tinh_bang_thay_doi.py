"""Tính các bảng của kế hoạch quản lý thay đổi: phân loại, ma trận lan truyền theo sơ đồ phụ thuộc, sổ thay đổi.

Dùng: python tinh_bang_thay_doi.py      (chay.py chuan_bi ke_hoach_thay_doi tự gọi)
Ra: du_lieu/thay_doi_bang.json
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

PL = json.load(open(os.path.join(HERE, '..', 'references', 'phan_loai.json'), encoding='utf-8'))
sd = loi.so_do(); cp = loi.doc_json('du_lieu/chi_phi.json'); pc = loi.doc_json('du_lieu/phan_cong.json')
tv = {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']}
so = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})


def f(v, fn):
    return 'Không giới hạn' if v is None else fn(v)


pl = {'cot': ['Mức', 'Khối lượng tăng tối đa', 'Chậm cut over tối đa', 'Chi phí tăng tối đa', 'Người phê duyệt', 'Thời hạn đánh giá'],
      'dong': [[m['ten'], f(m['md_toi_da'], lambda v: f'{loi.md(v)} MD'), f(m['ngay_cham_toi_da'], lambda v: f'{v} ngày'), f(m['chi_phi_toi_da'], lambda v: f'{loi.tien(v)} đồng'),
                m['nguoi_phe_duyet'], f'{m["thoi_han_danh_gia_ngay"]} ngày làm việc'] for m in PL['muc']], 'widths': [1100, 1400, 1300, 1600, 2600, 1300]}
nut = [('wbs', 'Phạm vi, WBS'), ('phan_cong', 'Giao việc'), ('thanh_vien', 'Thành viên, quỹ thời gian'), ('lich', 'Lịch, mốc'), ('don_gia', 'Đơn giá'),
       ('rui_ro', 'Sổ rủi ro'), ('du_an', 'Lịch làm việc, ngày nghỉ')]
rows = []
for n, ten in nut:
    r = subprocess.run([sys.executable, os.path.join(loi.THU_MUC_LOI, 'scripts', 'chay.py'), 'anh_huong', n, '--json'], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=loi.GOC)
    ds = json.loads(r.stdout)['anh_huong']
    rows.append([ten, ', '.join(b['ten'] for b in ds if not b['khoa']), ', '.join(b['ten'] for b in ds if b['khoa']) or 'Không'])
mt = {'cot': ['Thay đổi ở', 'Tài liệu phải cập nhật (theo thứ tự)', 'Đường cơ sở đấu thầu bị ảnh hưởng'], 'dong': rows, 'widths': [1900, 5600, 1800]}
ccb_ids = []
for x in pc.get('trach_nhiem', []):
    if x.get('muc') == 1 and x['A'] not in ccb_ids:
        ccb_ids.append(x['A'])
ccb = {'cot': ['Thành viên ban kiểm soát thay đổi', 'Vai trò trong ban'], 'dong': [[tv[i]['ho_ten'] + ', ' + tv[i].get('chuc_danh', ''), 'Chủ trì' if k == 0 else 'Thành viên'] for k, i in enumerate(ccb_ids)]
       + [[b['ten'], b.get('vai_tro', 'Bên liên quan ngoài nhóm')] for b in pc.get('ben_ngoai', [])], 'widths': [6000, 3300]}
cr = [{'ma': c['ma'], 'tieu_de': c['tieu_de'], 'ngay': c['ngay_de_xuat'], 'md_tang': c['md_tang'], 'chi_phi_tang': c['chi_phi_tang'], 'ngay_cham': c['ngay_cham'],
       'muc_ten': c['muc_ten'], 'trang_thai': c['trang_thai']} for c in so['yeu_cau']]
loi.ghi_json('du_lieu/thay_doi_bang.json', {'phan_loai': pl, 'lan_truyen': mt, 'ccb': ccb, 'so_thay_doi': cr, 'so_cr': len(cr),
                                            'don_gia_md_binh_quan': round(cp['A'] / cp['tong_md']), 'trang_thai': ', '.join(PL['trang_thai'])})
print(f'Đã tính bảng thay đổi: {len(rows)} nút lan truyền, {len(cr)} yêu cầu thay đổi trong sổ')
