"""Sửa tự động các lỗi cơ học theo báo cáo kiểm tra (vai Sửa).

Dùng: python sua_tu_dong.py <bao_cao.json> <noi_dung.json> [--ban-soan ban_soan.json]
Sửa tại chỗ nội dung đã ghép và bản soạn (để lần ghép sau giữ được bản sửa):
gạch dài, từ khẩu ngữ có một cách thay duy nhất (van_phong.json, nhóm tu_thay_the).
Không sửa số liệu, mã, phạm vi, nội dung pháp lý. Những lỗi đó chuyển cho agent Soạn thảo hoặc người dùng.
In danh sách chỗ đã sửa và các lỗi còn lại. Mã thoát 0 nếu không còn lỗi cần người xử lý, 2 nếu còn.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loi  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('bao_cao'); ap.add_argument('noi_dung'); ap.add_argument('--ban-soan')
a = ap.parse_args()
rep = json.load(open(a.bao_cao, encoding='utf-8'))
VP = json.load(open(os.path.join(loi.THU_MUC_LOI, 'references', 'van_phong.json'), encoding='utf-8'))
quy_tac = [('[–—]', '-')] + [(i['mau'], i['thay']) for i in VP['tu_thay_the']]
nhat_ky = []


def sua(node, path):
    if isinstance(node, str):
        new = node
        for pat, rp in quy_tac:
            n2 = re.sub(pat, rp, new)
            if n2 != new:
                nhat_ky.append({'vi_tri': path, 'truoc': new[:120], 'sau': n2[:120]})
                new = n2
        return new
    if isinstance(node, list):
        return [sua(v, f'{path}[{i}]') for i, v in enumerate(node)]
    if isinstance(node, dict):
        return {k: (sua(v, f'{path}.{k}') if k not in ('meta', 'widths', 'center_cols', 'right_cols', 'dong_dam', 't', 'key') else v) for k, v in node.items()}
    return node


co_loi_tu_dong = any(f['cach_sua'] == 'tu_dong' and f['ma'] in ('DD03', 'VP01') for f in rep['phat_hien'])
if co_loi_tu_dong:
    for p in [a.noi_dung] + ([a.ban_soan] if a.ban_soan and os.path.exists(a.ban_soan) else []):
        obj = json.load(open(p, encoding='utf-8'))
        obj = sua(obj, os.path.basename(p))
        loi.ghi_json(p, obj)
# DD01, DD02, DD04, CT01 không khắc phục được bằng tạo lại: nguyên nhân nằm ở đặc tả hoặc khung
con_lai = [f for f in rep['phat_hien'] if f['muc_do'] == 'loi' and not (f['cach_sua'] == 'tu_dong' and f['ma'] in ('DD03', 'VP01'))]
print(f'Đã sửa tự động {len(nhat_ky)} chỗ. Còn {len(con_lai)} lỗi cần agent Soạn thảo hoặc người dùng xử lý.')
for f in con_lai:
    print(f"  - {f['ma']}: {f['mo_ta']} | {f['vi_tri'][:80]}")
json.dump({'da_sua': nhat_ky, 'con_lai': con_lai}, open(os.path.splitext(a.bao_cao)[0] + '_sua.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
sys.exit(2 if con_lai else 0)
