"""Sửa lỗi theo báo cáo kiểm tra (vai Sửa).

Dùng: python3 fix_hsmt.py <hsmt_noi_dung.json> <bao_cao_kiem_tra.json> <hsmt_noi_dung_moi.json> <nhat_ky_sua.json>
- Chỉ sửa trên file dữ liệu, không sửa file Word và không sửa phần nguyên văn Mẫu 5A.
- Chỉ tự sửa lỗi cơ học có cách sửa duy nhất (cach_sua = tu_dong).
- Lỗi về nội dung, số liệu, pháp lý, RFP (cach_sua = can_nguoi_dung) được chuyển cho người dùng quyết, không tự sửa.
Mã thoát: 0 nếu không còn việc chờ người dùng, 2 nếu còn.
"""
import json, re, sys

data_in, report_in, data_out, log_out = sys.argv[1:5]
data = json.load(open(data_in, encoding='utf-8'))
rep = json.load(open(report_in, encoding='utf-8'))

TEXT_RULES = {
    'DD03': [('[\u2013\u2014]', '-')],
    'PL01': [(r'Nghị định số 24/2024/NĐ-CP', 'Nghị định số 214/2025/NĐ-CP'), (r'24/2024/NĐ-CP', '214/2025/NĐ-CP')],
    'VP01': [(r'chạy được', 'hoạt động được'), (r'dùng được', 'có thể sử dụng'),
             (r'lỗi chặn', 'lỗi nghiêm trọng làm gián đoạn vận hành'), (r'đóng lỗi', 'khắc phục dứt điểm lỗi'),
             (r'go-live', 'đưa hệ thống vào vận hành')],
}
REBUILD = {'NV01', 'DD01', 'DD02', 'DD04'}

log, pending, rebuild = [], [], False
codes = {'DD03'}  # luôn chuẩn hóa gạch dài trong dữ liệu
for f in rep['phat_hien']:
    if f['cach_sua'] == 'tu_dong' and (f['ma'] in TEXT_RULES or f['ma'] in REBUILD):
        codes.add(f['ma'])
        if f['ma'] in REBUILD: rebuild = True
    elif f['muc_do'] == 'loi' or f['cach_sua'] == 'can_nguoi_dung':
        pending.append(f)

def walk(node, path):
    if isinstance(node, str):
        new = node
        for code in codes & TEXT_RULES.keys():
            for pat, rp in TEXT_RULES[code]:
                new2 = re.sub(pat, rp, new)
                if new2 != new:
                    log.append({'ma': code, 'vi_tri': path, 'truoc': new[:160], 'sau': new2[:160]})
                    new = new2
        return new
    if isinstance(node, list):
        return [walk(v, f'{path}[{i}]') for i, v in enumerate(node)]
    if isinstance(node, dict):
        return {k: (walk(v, f'{path}.{k}') if k in ('text', 'rows') else v) for k, v in node.items()}
    return node

data['blocks'] = [walk(b, f'blocks[{i}]') for i, b in enumerate(data['blocks'])]
json.dump(data, open(data_out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump({'da_sua_tu_dong': log, 'can_build_lai': rebuild or bool(log), 'cho_nguoi_dung': pending},
          open(log_out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'Đã tự sửa {len(log)} chỗ. Cần build lại: {rebuild or bool(log)}. Chờ người dùng quyết: {len(pending)} mục.')
for f in pending:
    print(f"  - {f['ma']}: {f['mo_ta']} | {f['vi_tri'][:80]}")
sys.exit(2 if pending else 0)
