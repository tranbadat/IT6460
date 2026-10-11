"""Điều phối các bước có script. Các bước của agent (phân tích RFP, soạn thảo, kiểm tra lớp B) chạy xen giữa.

Dùng:
  python3 chay_quy_trinh.py chuan_bi <Mau_5A.docx> <tham_so_chu_dau_tu.json> <thu_muc_lam_viec>
      Cần có <thu_muc_lam_viec>/rfp_yeu_cau.json (agent Phân tích RFP viết trước).
      Chạy: phân tích mẫu, tính giá trị, lập khung. Ra hsmt_khung.json cho agent Soạn thảo.
  python3 chay_quy_trinh.py hoan_thien <Mau_5A.docx> <thu_muc_lam_viec>
      Cần có <thu_muc_lam_viec>/ban_soan.json (agent Soạn thảo viết).
      Chạy: ghép bản soạn, rồi vòng tạo, kiểm tra lớp A, sửa (tối đa 3 vòng).
Mã thoát: 0 đạt, 2 còn mục chờ người dùng hoặc agent Soạn thảo, 1 lỗi.
"""
import os, shutil, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
run = lambda *a: subprocess.run([sys.executable, *a], capture_output=True, text=True)
S = lambda n: os.path.join(here, n)


def step(name, r):
    print(f'[{name}] ' + (r.stdout.strip() or r.stderr.strip()))
    if r.returncode not in (0,):
        print(r.stderr.strip())
    return r.returncode


cmd = sys.argv[1]
if cmd == 'chuan_bi':
    mau, tham_so, wd = sys.argv[2:5]
    os.makedirs(wd, exist_ok=True)
    if not os.path.exists(os.path.join(wd, 'rfp_yeu_cau.json')):
        sys.exit('Thiếu rfp_yeu_cau.json. Chạy agent Phân tích RFP trước (prompts/vai_phan_tich_rfp.md).')
    shutil.copy(tham_so, os.path.join(wd, 'tham_so_chu_dau_tu.json'))
    P = lambda n: os.path.join(wd, n)
    if step('phân tích mẫu', run(S('phan_tich_mau.py'), mau, wd)): sys.exit(1)
    if step('tính giá trị', run(S('tinh_gia_tri.py'), P('tham_so_chu_dau_tu.json'), P('rfp_yeu_cau.json'), P('gia_tri_tinh.json'))): sys.exit(1)
    if step('lập khung', run(S('lap_khung.py'), P('mau5a_cau_truc.json'), P('tham_so_chu_dau_tu.json'), P('rfp_yeu_cau.json'), P('gia_tri_tinh.json'), P('hsmt_khung.json'))): sys.exit(1)
    print('Xong bước chuẩn bị. Tiếp theo: agent Soạn thảo viết ban_soan.json theo prompts/vai_soan_thao.md.')
    sys.exit(0)

if cmd == 'hoan_thien':
    mau, wd = sys.argv[2:4]
    P = lambda n: os.path.join(wd, n)
    if step('ghép bản soạn', run(S('dien_khung.py'), P('hsmt_khung.json'), P('ban_soan.json'), P('hsmt_noi_dung_v1.json'))):
        print('DỪNG: agent Soạn thảo cần sửa ban_soan.json.'); sys.exit(2)
    cur = P('hsmt_noi_dung_v1.json')
    for n in range(1, 4):
        doc, bc = P(f'HSMT_v{n}.docx'), P(f'bao_cao_kiem_tra_v{n}.json')
        if step(f'vòng {n} tạo', run(S('build_hsmt.py'), cur, P('mau5a_fixed.json'), doc)): sys.exit(1)
        r = run(S('verify_hsmt.py'), doc, '--lam-viec', wd, '--mau', mau, '--json', bc)
        print(f'[vòng {n} kiểm tra] ' + r.stdout.strip().splitlines()[-1])
        if r.returncode == 0:
            shutil.copy(doc, P('HSMT_ket_qua.docx'))
            print(f'ĐẠT lớp A. File: {P("HSMT_ket_qua.docx")}. Tiếp theo: agent Kiểm tra lớp B theo prompts/vai_kiem_tra.md.')
            sys.exit(0)
        nxt = P(f'hsmt_noi_dung_v{n + 1}.json')
        r = run(S('fix_hsmt.py'), cur, bc, nxt, P(f'nhat_ky_sua_v{n}.json'))
        print(f'[vòng {n} sửa] ' + r.stdout.strip())
        if r.returncode == 2:
            print('DỪNG: còn mục cần agent Soạn thảo hoặc người dùng xử lý, xem', bc); sys.exit(2)
        cur = nxt
    print('DỪNG: quá 3 vòng vẫn còn lỗi.'); sys.exit(1)
sys.exit('Lệnh không hợp lệ: dùng chuan_bi hoặc hoan_thien')
