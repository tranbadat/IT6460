"""Tính các bảng của kế hoạch quản lý rủi ro: thang đo, ma trận xác suất và tác động, đối chiếu dự phòng.

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

rr = loi.doc_json('du_lieu/rui_ro.json'); cp = loi.doc_json('du_lieu/chi_phi.json'); da = loi.du_an()
T = rr['thang_do']
xs = {'cot': ['Mức', 'Xác suất', 'Giá trị dùng tính EMV'], 'dong': [[k, v, loi.pt(T['xac_suat_pt'][k])] for k, v in T['xac_suat'].items()], 'widths': [900, 5500, 2900], 'center_cols': [0, 2]}
td = {'cot': ['Mức', 'Tác động'], 'dong': [[k, v] for k, v in T['tac_dong'].items()], 'widths': [900, 8400], 'center_cols': [0]}
muc = {'cot': ['Mức rủi ro', 'Điểm (xác suất x tác động)', 'Cách xử lý'], 'dong': [
    [T['ten_muc']['cao'], f'{T["muc"]["cao"][0]} đến {T["muc"]["cao"][1]}', 'Bắt buộc có kế hoạch ứng phó, dấu hiệu nhận biết, theo dõi hằng tuần, báo cáo trong mỗi kỳ'],
    [T['ten_muc']['trung_binh'], f'{T["muc"]["trung_binh"][0]} đến {T["muc"]["trung_binh"][1]}', 'Có biện pháp phòng ngừa, theo dõi theo sprint'],
    [T['ten_muc']['thap'], f'{T["muc"]["thap"][0]} đến {T["muc"]["thap"][1]}', 'Ghi nhận, rà soát cuối sprint']], 'widths': [1600, 2600, 5100], 'center_cols': [0, 1]}
mt = {'cot': ['Xác suất, tác động', '1', '2', '3', '4', '5'],
      'dong': [[r['xac_suat']] + [r[f'td{j}'] for j in range(1, 6)] for r in rr['ma_tran']], 'widths': [2300] + [1400] * 5, 'center_cols': [0, 1, 2, 3, 4, 5]}
th = rr['tong_hop']
dp = {'cot': ['Chỉ tiêu', 'Giá trị'], 'dong': [
    ['Tổng EMV theo khối lượng', f'{loi.md(th["tong_emv_md"])} MD'], ['Tổng EMV theo chi phí', f'{loi.tien(th["tong_emv_tien"])} đồng'],
    ['Tổng EMV theo thời gian', f'{loi.so(th["tong_emv_ngay"], 1)} ngày làm việc'], ['Dự phòng chi phí trong dự toán', f'{loi.tien(cp["du_phong_hien_co"])} đồng'],
    ['Dự trữ thời gian đến cut over theo master schedule', f'{loi.doc_json("du_lieu/lich.json")["du_tru_den_cut_over_ngay"]} ngày làm việc'],
    ['Đánh giá dự phòng chi phí', ('Đủ' if cp['du_phong_hien_co'] >= th['tong_emv_tien'] else 'Thiếu')
     + (' (khi toàn bộ khoản B được dùng làm dự phòng)' if cp.get('cach_tinh_du_phong') == 'nam_trong_chi_phi_khac' else '')]], 'widths': [5300, 4000], 'right_cols': [1]}
ng = da.get('nguong_canh_bao', {})
kpi = {'cot': ['Chỉ số', 'Ngưỡng vàng', 'Ngưỡng đỏ', 'Hành động khi chạm ngưỡng'], 'dong': [
    ['SPI', f'dưới {loi.so(ng.get("spi_vang", 0.95), 2)}', f'dưới {loi.so(ng.get("spi_do", 0.85), 2)}', 'Rà soát rủi ro tiến độ, kích hoạt kế hoạch ứng phó của rủi ro liên quan'],
    ['CPI', f'dưới {loi.so(ng.get("cpi_vang", 0.95), 2)}', f'dưới {loi.so(ng.get("cpi_do", 0.85), 2)}', 'Rà soát rủi ro chi phí, xem xét dùng dự phòng theo quy định'],
    ['Lỗi nghiêm trọng đang mở', 'từ 2', 'từ 4', 'Ưu tiên khắc phục, đánh giá lại rủi ro chất lượng']], 'widths': [1300, 1600, 1600, 4800]}
cao = [r for r in rr['danh_sach'] if r['muc'] == 'cao']
loi.ghi_json('du_lieu/rui_ro_bang.json', {'xac_suat': xs, 'tac_dong': td, 'muc': muc, 'ma_tran': mt, 'du_phong': dp, 'nguong': kpi, 'so_cao': len(cao),
                                          'ma_cao': ', '.join(r['ma'] for r in cao)})
print(f'Đã tính bảng rủi ro: {len(rr["danh_sach"])} rủi ro, {len(cao)} mức cao')
