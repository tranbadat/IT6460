"""Điều phối các bước có script. Các bước của agent (phân tích RFP, soạn thảo, kiểm tra lớp B) chạy xen giữa.

Dùng:
  python3 chay_quy_trinh.py chuan_bi <Mau_5A.docx> <tham_so_chu_dau_tu.json> <thu_muc_lam_viec>
      Cần có <thu_muc_lam_viec>/rfp_yeu_cau.json (agent Phân tích RFP viết trước).
      Chạy: phân tích mẫu, tính giá trị, lập khung. Ra hsmt_khung.json cho agent Soạn thảo.
  python3 chay_quy_trinh.py hoan_thien <Mau_5A.docx> <thu_muc_lam_viec>
      Cần có <thu_muc_lam_viec>/ban_soan.json (agent Soạn thảo viết).
      Chạy: ghép bản soạn, rồi vòng tạo, kiểm tra lớp A, sửa tự động (tối đa 3 lần).
      Đạt hẳn: HSMT_ket_qua.docx. Lớp A không còn lỗi mới nhưng còn tham số chờ Chủ đầu tư hoặc phát hiện mở
      của vòng trước: HSMT_du_thao.docx để lớp B kiểm tra và xác nhận đóng.
  python3 chay_quy_trinh.py ghi_nhan <thu_muc_lam_viec> [bao_cao_kiem_tra.json]
      Chạy sau kiểm tra lớp B, kết thúc một vòng. Cập nhật sổ so_phat_hien.json: đóng phát hiện được lớp B xác nhận
      (khóa dong_phat_hien của báo cáo), đóng phát hiện lớp A không còn, thêm phát hiện mới. Ghi kết luận vòng vào báo cáo.
      Vòng đạt: tệp Word lớp B đã kiểm tra (khóa file của báo cáo, đúng md5 và đúng vòng) trở thành HSMT_ket_qua.docx.
  python3 chay_quy_trinh.py giai_trinh <thu_muc_lam_viec> <ma_PHxxx> "<nội dung giải trình>"
      Ghi giải trình của người dùng cho một phát hiện đang mở. Phát hiện có giải trình không chặn kết luận đạt.
Mã thoát: 0 đạt, 2 còn mục chờ người dùng hoặc agent Soạn thảo, 1 lỗi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json, os, shutil, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from quy_uoc import doc_so, ghi_so, hop_nhat, ket_luan_vong, md5_tep, vong_cua_word  # noqa: E402

run = lambda *a: subprocess.run([sys.executable, *a], capture_output=True, text=True, encoding='utf-8', errors='replace')
S = lambda n: os.path.join(here, n)
KET_LUAN = {'dat': 'ĐẠT', 'chua_dat': 'CHƯA ĐẠT', 'cho_nguoi_dung': 'CHƯA HOÀN TẤT, CHỜ NGƯỜI DÙNG'}


def step(name, r):
    print(f'[{name}] ' + (r.stdout.strip() or r.stderr.strip()))
    if r.returncode not in (0,):
        print(r.stderr.strip())
    return r.returncode


def in_muc_cho(phat_hien):
    for f in phat_hien:
        so_hieu = f.get('id_so') or f.get('id')
        print(f"  - {so_hieu + ' ' if so_hieu else ''}{f['ma']} [{f['muc_do']}]: {f['mo_ta'][:150]} | {f.get('vi_tri', '')[:70]}")


def chuan_bi(mau, tham_so, wd):
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


def ket_thuc_lop_a(doc, bc, P):
    """Lớp A không còn lỗi mới: giao HSMT_ket_qua.docx nếu đạt hẳn, ngược lại HSMT_du_thao.docx kèm danh sách chờ."""
    kl = bc['ket_luan']
    if kl == 'dat':
        shutil.copy(doc, P('HSMT_ket_qua.docx'))
        print(f'ĐẠT lớp A. File: {P("HSMT_ket_qua.docx")}. Tiếp theo: agent Kiểm tra lớp B theo prompts/vai_kiem_tra.md, rồi chay_quy_trinh.py ghi_nhan.')
        sys.exit(0)
    shutil.copy(doc, P('HSMT_du_thao.docx'))
    print(f'{KET_LUAN[kl]}: lớp A không còn lỗi mới nhưng còn {bc["so_cho_nguoi_dung"]} mục chờ (tham số Chủ đầu tư, phát hiện mở của vòng trước). '
          f'Bản dự thảo: {P("HSMT_du_thao.docx")}. Chưa tạo HSMT_ket_qua.docx.')
    in_muc_cho([f for f in bc['phat_hien'] if f['ma'] in ('TS01', 'PH01') or f.get('mang_sang')])
    print('Tiếp theo: lớp B kiểm tra bản dự thảo và xác nhận đóng phát hiện cũ, chay_quy_trinh.py ghi_nhan, rồi hỏi người dùng các mục chờ.')
    sys.exit(2)


def cat_ban_cu(P):
    """Bản giao, bản dự thảo của lần chạy trước đổi tên kèm vòng của chúng, để lớp B và bước trích không lấy nhầm."""
    for ten in ('HSMT_ket_qua.docx', 'HSMT_du_thao.docx'):
        if os.path.exists(P(ten)):
            v = vong_cua_word(P(ten))[0] or 'cu'
            os.replace(P(ten), P(ten.replace('.docx', f'_vong{v}.docx')))


def hoan_thien(mau, wd):
    P = lambda n: os.path.join(wd, n)
    vong = doc_so(wd)['vong'] + 1
    # nội dung v2 trở đi của lần chạy trước sinh từ v1 cũ; bỏ để không bị lấy nhầm là bản mới nhất
    for n in range(2, 5):
        if os.path.exists(P(f'hsmt_noi_dung_v{n}.json')):
            os.remove(P(f'hsmt_noi_dung_v{n}.json'))
    cat_ban_cu(P)
    if step('ghép bản soạn', run(S('dien_khung.py'), P('hsmt_khung.json'), P('ban_soan.json'), P('hsmt_noi_dung_v1.json'))):
        print('DỪNG: agent Soạn thảo cần sửa ban_soan.json.'); sys.exit(2)
    cur = P('hsmt_noi_dung_v1.json')
    print(f'Vòng kiểm tra {vong} (sổ phát hiện đã ghi nhận {vong - 1} vòng). Chạy lại hoan_thien trước ghi_nhan vẫn thuộc vòng này.')
    for n in range(1, 4):
        doc, bc_path = P(f'HSMT_v{n}.docx'), P(f'bao_cao_kiem_tra_v{n}.json')
        if step(f'lần {n} tạo', run(S('build_hsmt.py'), cur, P('mau5a_fixed.json'), doc, '--vong', str(vong))): sys.exit(1)
        r = run(S('verify_hsmt.py'), doc, '--lam-viec', wd, '--mau', mau, '--json', bc_path)
        print(f'[lần {n} kiểm tra lớp A] ' + (r.stdout.strip().splitlines() or [r.stderr.strip()])[-1])
        if 'Kết luận:' not in r.stdout:  # kiểm tra lớp A dừng giữa chừng, báo cáo không đáng tin
            print(r.stderr.strip()); sys.exit(1)
        bc = json.load(open(bc_path, encoding='utf-8'))
        if bc['ket_luan_lop_a'] == 'dat':
            ket_thuc_lop_a(doc, bc, P)
        nxt = P(f'hsmt_noi_dung_v{n + 1}.json')
        r = run(S('fix_hsmt.py'), cur, bc_path, nxt, P(f'nhat_ky_sua_v{n}.json'))
        print(f'[lần {n} sửa tự động] ' + r.stdout.strip())
        if r.returncode == 2:
            print('DỪNG: còn mục cần agent Soạn thảo hoặc người dùng xử lý, xem', bc_path); sys.exit(2)
        cur = nxt
    print('DỪNG: quá 3 vòng vẫn còn lỗi.'); sys.exit(1)


def kiem_ban_giao(wd, bc, vong):
    """Tệp Word lớp B đã kiểm tra: còn nguyên (md5 như lúc kiểm tra) và thuộc đúng vòng. Trả đường dẫn, lỗi thì dừng."""
    src = os.path.join(wd, bc.get('file', ''))
    if not bc.get('file') or not os.path.exists(src):
        sys.exit(f'LỖI: không thấy tệp đã kiểm tra {src}. Chạy verify_hsmt.py trên tệp trong thư mục làm việc.')
    if md5_tep(src) != bc.get('md5'):
        sys.exit(f'LỖI: {bc["file"]} đã thay đổi sau khi kiểm tra (md5 khác báo cáo). Kiểm tra lại rồi ghi_nhan.')
    if vong_cua_word(src)[0] != str(vong):
        sys.exit(f'LỖI: {bc["file"]} thuộc vòng {vong_cua_word(src)[0] or "không rõ"}, vòng đang ghi nhận là {vong}. Chạy hoan_thien rồi kiểm tra lại.')
    return src


def ghi_nhan(wd, bc_path):
    """Kết thúc một vòng: hợp nhất báo cáo (lớp A và lớp B) vào sổ phát hiện, ghi kết luận vòng, vòng đạt thì nâng bản đã kiểm tra thành bản giao."""
    bc = json.load(open(bc_path, encoding='utf-8'))
    so, loi = hop_nhat(doc_so(wd), bc)
    if loi:
        print('LỖI:', *loi, sep='\n- '); sys.exit(1)
    kl, ts01, mo = ket_luan_vong(so, bc)
    src = kiem_ban_giao(wd, bc, so['vong']) if kl == 'dat' else None
    ghi_so(wd, so)
    bc_moi = {**bc, 'vong': so['vong'], 'ket_luan': kl, 'phat_hien_mo': [x['id'] for x in mo], 'so_tham_so_cho': len(ts01)}
    if src:
        giao = os.path.join(wd, 'HSMT_ket_qua.docx')
        if os.path.abspath(src) != os.path.abspath(giao):
            shutil.copy(src, giao)
        bc_moi = {**bc_moi, 'tep_giao': 'HSMT_ket_qua.docx', 'md5_giao': md5_tep(giao)}
        print(f'Bản giao HSMT_ket_qua.docx là {bc["file"]} của vòng {so["vong"]}, md5 {bc_moi["md5_giao"]}.')
    json.dump(bc_moi, open(bc_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    dong = [x for x in so['phat_hien'] if x.get('vong_dong') == so['vong']]
    print(f"Vòng {so['vong']}: {len(dong)} phát hiện đã đóng, {len(mo)} phát hiện còn mở, {len(ts01)} tham số chờ Chủ đầu tư.")
    in_muc_cho(ts01 + mo)
    print(f'Kết luận vòng: {kl} ({KET_LUAN[kl]})')
    if kl != 'dat':
        print('Phát hiện còn mở được mang sang vòng sau. Chỉ đóng khi lớp B xác nhận đã khắc phục (dong_phat_hien) hoặc có giải trình (chay_quy_trinh.py giai_trinh).')
    sys.exit({'dat': 0, 'chua_dat': 1, 'cho_nguoi_dung': 2}[kl])


def giai_trinh(wd, ma, noi_dung):
    so = doc_so(wd)
    x = next((x for x in so['phat_hien'] if x['id'] == ma), None)
    if x is None or x['trang_thai'] != 'mo':
        sys.exit(f'LỖI: {ma} không phải phát hiện đang mở trong {os.path.join(wd, "so_phat_hien.json")}')
    if not noi_dung.strip():
        sys.exit('LỖI: cần nội dung giải trình')
    moi = {**x, 'trang_thai': 'giai_trinh', 'giai_trinh': noi_dung.strip(), 'vong_giai_trinh': so['vong']}
    ghi_so(wd, {**so, 'phat_hien': [moi if y['id'] == ma else y for y in so['phat_hien']]})
    print(f'Đã ghi giải trình cho {ma} ({x["ma"]}): {noi_dung.strip()[:120]}')


cmd = sys.argv[1] if len(sys.argv) > 1 else ''
if cmd == 'chuan_bi':
    chuan_bi(*sys.argv[2:5])
if cmd == 'hoan_thien':
    hoan_thien(*sys.argv[2:4])
if cmd == 'ghi_nhan':
    ghi_nhan(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else os.path.join(sys.argv[2], 'bao_cao_kiem_tra.json'))
if cmd == 'giai_trinh':
    giai_trinh(*sys.argv[2:5])
    sys.exit(0)
sys.exit('Lệnh không hợp lệ: dùng chuan_bi, hoan_thien, ghi_nhan hoặc giai_trinh')
