"""Xuất phụ lục bằng chứng prompt và skill (nộp kèm các tài liệu).

Dùng: python xuat_bang_chung.py
Nguồn: thư mục .claude/skills (danh sách skill, phiên bản), sơ đồ phụ thuộc, bang_chung/nhat_ky_chay.jsonl,
bang_chung/prompts/ (bản chụp prompt), bang_chung/kiem_tra/ (báo cáo kiểm tra lớp A, lớp B), du_lieu/phien_ban.json.
Ra: ket_qua/16_Bang_chung/Phu_luc_bang_chung_prompt_skill.docx
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import loi  # noqa: E402

sd = loi.so_do()
da = loi.doc_json('dau_vao/du_an.json', {})
blocks = []
add = lambda t, **kw: blocks.append(dict(kw, t=t))

add('center', text=da.get('don_vi_thuc_hien', ''), size=13)
add('center', text=da.get('ten_du_an', ''), size=13)
add('blank')
add('center', text='Phụ lục bằng chứng prompt và skill', size=20)
add('center', text='Quy trình, công cụ và nhật ký tạo các tài liệu dự án', size=14)
add('blank')
add('table', rows=[[k, v] for k, v in (('Môn học', da.get('mon_hoc', '')), ('Nhóm', da.get('ma_nhom', '')), ('Giảng viên', da.get('giang_vien', '')),
                                        ('Người lập', da.get('nguoi_lap', '')), ('Ngày xuất', loi.ngay(loi.bay_gio()[:10]))) if v], widths=[3000, 6300])
add('pagebreak')

# 1. Mục đích
add('h1', text='1. Mục đích')
add('p', text='Phụ lục này chứng minh cách các tài liệu của dự án được tạo ra: skill và phiên bản đã dùng, prompt giao cho từng agent, thứ tự các bước, '
              'kết quả kiểm tra và sửa lỗi, cùng mã băm của tệp đầu vào và đầu ra ở từng bước. Mã băm cho phép đối chiếu một tài liệu nộp kèm với '
              'đúng lần chạy đã tạo ra nó.')

# 2. Skill
add('h1', text='2. Danh sách skill')
rows = [['Skill', 'Phiên bản', 'Mô tả', 'Băm SKILL.md']]
for f in sorted(glob.glob(os.path.join(loi.THU_MUC_SKILLS, '*', 'SKILL.md'))):
    name = os.path.basename(os.path.dirname(f))
    txt = open(f, encoding='utf-8').read()
    m = re.search(r'^description:\s*(.+)$', txt, re.M)
    mo_ta = (m.group(1).strip() if m else '')[:260]
    rows.append([name, loi.phien_ban_skill(name) or '-', mo_ta, loi.bam(f)])
add('table', rows=rows, widths=[1900, 900, 5300, 1300], size=11)

# 3. Quy trình
add('h1', text='3. Quy trình và sơ đồ phụ thuộc')
add('p', text='Mỗi tài liệu do một skill tạo. Đầu vào của một bước là tệp do nhóm cung cấp hoặc đầu ra của bước trước. Khi một đầu vào thay đổi, '
              'các bước phía sau được đánh dấu cũ và phải chạy lại. Mỗi tài liệu đi qua vòng tạo, kiểm tra tự động (lớp A), kiểm tra đọc hiểu độc lập (lớp B) và sửa lỗi.')
rows = [['Bước', 'Tài liệu', 'Skill', 'Đầu vào', 'Đầu ra']]
for b in sd['buoc']:
    rows.append([b['id'], b['ten'], b['skill'], ', '.join(b['vao']), [p for p in b['ra'].values()]])
add('table', rows=rows, widths=[1500, 1900, 1500, 2300, 2100], size=10)

# 4. Phiên bản tài liệu
add('h1', text='4. Tài liệu đầu ra và phiên bản')
reg = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})['tai_lieu']
rows = [['Tệp', 'Phiên bản', 'Ngày', 'Bước', 'Băm nội dung', 'Ghi chú']]
for tep, lst in sorted(reg.items()):
    x = lst[-1]
    rows.append([tep, x['phien_ban'], x['ngay'][:16], x['buoc'], x['hash'], x.get('ghi_chu', '')])
add('table', rows=rows if len(rows) > 1 else rows + [['Chưa có tài liệu nào được đăng ký', '', '', '', '', '']], widths=[3000, 900, 1500, 1300, 1300, 1300], size=10)

# 5. Kết quả kiểm tra
add('h1', text='5. Kết quả kiểm tra tài liệu')
rows = [['Báo cáo', 'Tài liệu', 'Kết luận', 'Số lỗi', 'Số cảnh báo']]
for f in sorted(glob.glob(loi.duong_dan('bang_chung/kiem_tra/*.json'))):
    try:
        r = json.load(open(f, encoding='utf-8'))
        rows.append([os.path.basename(f), r.get('tai_lieu', ''), {'dat': 'Đạt', 'chua_dat': 'Chưa đạt'}.get(r.get('ket_luan'), r.get('ket_luan', '')),
                     str(r.get('so_loi', '')), str(r.get('so_canh_bao', ''))])
    except Exception:
        pass
add('table', rows=rows if len(rows) > 1 else rows + [['Chưa có báo cáo', '', '', '', '']], widths=[3000, 3000, 1100, 1000, 1200], size=10)

# 6. Nhật ký chạy
add('h1', text='6. Nhật ký chạy')
nk = []
p = loi.duong_dan('bang_chung/nhat_ky_chay.jsonl')
if os.path.exists(p):
    nk = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
_loai = {}
for x in nk:
    _loai[x.get('loai', '')] = _loai.get(x.get('loai', ''), 0) + 1
_ten_loai = {'agent': 'agent', 'script': 'script', 'nguoi_dung': 'người dùng'}
add('p', text=f'Tổng số bước đã ghi: {len(nk)}. ' + '. '.join(f'Bước do {_ten_loai.get(k, k)} thực hiện: {v}' for k, v in sorted(_loai.items())) + '.')
rows = [['Thời gian', 'Skill', 'Bước', 'Loại', 'Nội dung', 'Prompt', 'Kết quả']]
for x in nk:
    rows.append([loi.ngay(x['thoi_gian'][:10]) + ' ' + x['thoi_gian'][11:16], x['skill'], x['buoc'], x['loai'], x['mo_ta'][:220], x.get('prompt_hash') or '', str(x.get('ket_qua', ''))[:80]])
add('table', rows=rows, widths=[1100, 1300, 1500, 700, 2900, 900, 1000], size=9)

# 7. Prompt
add('h1', text='7. Prompt đã dùng')
pf = sorted(glob.glob(loi.duong_dan('bang_chung/prompts/*.md')))
add('p', text='Mỗi prompt được chụp lại tại lần dùng đầu tiên, đặt tên theo skill, tên prompt và mã băm nội dung. Mã băm trong nhật ký chạy trỏ tới đúng bản prompt ở mục này.')
for f in pf:
    add('h2', text=os.path.basename(f))
    for line in open(f, encoding='utf-8').read().splitlines():
        if line.strip():
            add('p', text=line)

# 8. Lịch sử git (nếu có)
try:
    g = subprocess.run(['git', '-C', loi.GOC, 'log', '--date=short', '--pretty=%ad | %h | %an | %s', '-n', '200'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if g.returncode == 0 and g.stdout.strip():
        add('h1', text='8. Lịch sử lưu trữ (git)')
        rows = [['Ngày', 'Mã', 'Người', 'Nội dung']] + [l.split(' | ', 3) for l in g.stdout.strip().splitlines()]
        add('table', rows=rows, widths=[1300, 1000, 1800, 5200], size=10)
except FileNotFoundError:
    pass

ra = sd['buoc'][-1]['ra']['doc_bang_chung']
h_nd = loi.bam_obj(blocks)
pb_du_kien, _ = loi.du_kien_phien_ban(ra, h_nd)
meta = {'ten': 'Phụ lục bằng chứng prompt và skill', 'header': 'Phụ lục bằng chứng prompt và skill', 'size_bang_pt': 10,
        'phien_ban': pb_du_kien, 'ngay': loi.ngay(loi.bay_gio()[:10])}
tmp = loi.duong_dan('lam_viec/bang_chung/noi_dung.json')
loi.ghi_json(tmp, {'meta': meta, 'blocks': blocks})
r = subprocess.run([sys.executable, os.path.join(HERE, 'build_docx.py'), tmp, loi.duong_dan(ra)], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout.strip() or r.stderr.strip())
if r.returncode == 0:
    pbs = loi.hoan_tat_buoc('bang_chung', 'Xuất phụ lục bằng chứng prompt và skill', hash_tep={ra: h_nd},
                            chi_tiet={'so_buoc_nhat_ky': len(nk), 'so_prompt': len(pf)})
    print(f'{ra}: phiên bản {pbs.get(ra)}')
else:
    loi.ghi_nhat_ky('qlda-loi', 'bang_chung', 'script', 'Xuất phụ lục bằng chứng prompt và skill', ra=[ra], ket_qua='lỗi')
sys.exit(r.returncode)
