"""Điều phối chu trình mô phỏng mỗi sprint và giai đoạn kết thúc: liệt kê các bước theo thứ tự, trạng thái từng bước, lệnh cần chạy.

Dùng (chạy từ thư mục gốc dự án):
  python .claude/skills/qlda-mo-phong/scripts/chu_trinh.py S3            danh sách bước của sprint S3 và trạng thái
  python .claude/skills/qlda-mo-phong/scripts/chu_trinh.py S3 --chay     chạy các bước script liên tiếp đến bước cần agent hoặc người dùng
  python .claude/skills/qlda-mo-phong/scripts/chu_trinh.py ket_thuc      các bước sau sprint cuối
Bước do agent (viết kịch bản, Soạn thảo, Kiểm tra lớp B, Đánh giá thay đổi) và bước quyết định của người có thẩm quyền không chạy
tự động. Lệnh in kèm QLDA_NGAY=<ngày cuối kỳ> (ngày hiện hành khi mô phỏng, loi.ngay_hien_hanh), --chay đặt biến này cho tiến trình con.
Bản phát hành R<n>: qlda-master-schedule/scripts/phat_hanh.py S<n>; không có tệp này thì ghi chú gọi khi có.
Mã thoát: 0 mọi bước đã xong, 2 còn bước cần agent hoặc người dùng, 1 lỗi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse
import datetime as dt
import os
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mp_chung as C  # noqa: E402

loi = C.loi
S = '.claude/skills'
LENH_MP = f'python {S}/qlda-mo-phong/scripts/mo_phong_sprint.py'
LENH_TD = f'python {S}/qlda-bao-cao-tien-do/scripts/tinh_tien_do.py'
LENH_CHAY = f'python {S}/qlda-loi/scripts/chay.py'
LENH_PB = f'python {S}/qlda-phien-ban/scripts/so_phien_ban.py'
LENH_CR = f'python {S}/qlda-change/scripts/yeu_cau_thay_doi.py'


def ton_tai(p):
    return os.path.exists(loi.duong_dan(p))


def moi_hon(p, moc):
    """Tệp p có và được ghi sau thời điểm moc (chuỗi yyyy-mm-dd HH:MM:SS)."""
    if not ton_tai(p) or not moc:
        return ton_tai(p)
    return dt.datetime.fromtimestamp(os.path.getmtime(loi.duong_dan(p))) >= dt.datetime.fromisoformat(moc)


def tim_lenh_phat_hanh():
    """Lệnh lập bản phát hành theo sprint (do qlda-master-schedule cung cấp), không có thì rỗng."""
    for ten in ('qlda-master-schedule', 'qlda-phien-ban', 'qlda-loi'):
        f = os.path.join(loi.THU_MUC_SKILLS, ten, 'scripts', 'phat_hanh.py')
        if os.path.exists(f):
            return f'python {S}/{ten}/scripts/phat_hanh.py'
    return ''


def phien_ban(tep):
    return loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}}).get('tai_lieu', {}).get(tep, [])


def buoc_cr(sp, kb):
    """(bước đánh giá CR làm trước tinh_tien_do, các bước sau phê duyệt) cho các biến cố cr của kịch bản."""
    truoc, out = [], []
    so_td = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})
    co_ap_dung = 'ap_dung' in open(os.path.join(loi.THU_MUC_SKILLS, 'qlda-change', 'scripts', 'yeu_cau_thay_doi.py'), encoding='utf-8').read()
    for e in [e for e in kb.get('bien_co', []) if e.get('loai') == 'cr']:
        ma = e.get('ma_cr', '')
        cr = next((c for c in so_td['yeu_cau'] if c['ma'] == ma or c.get('tieu_de') == e.get('tieu_de')), None)
        tt = cr['trang_thai'] if cr else ''
        truoc.append(('agent', f'{ma}: agent Đánh giá thay đổi đọc {C.THU_MUC_LV}/cr_{sp}_{ma}.json, viết lam_viec/thay_doi/cr_nhap.json theo '
                    f'qlda-change/prompts/vai_danh_gia_thay_doi.md, rồi: {LENH_CR} danh_gia lam_viec/thay_doi/cr_nhap.json '
                    '(trước tinh_tien_do.py để sổ vấn đề liên kết được mã CR)', bool(cr)))
        out.append(('nguoi_dung', f'{ma}: người có thẩm quyền quyết định: {LENH_CR} quyet_dinh {ma} --ket-qua "Đã phê duyệt" --nguoi "..." '
                    '--ngay yyyy-mm-dd --van-ban "<số, ngày phụ lục hợp đồng>"', tt in ('Đã phê duyệt', 'Đã thực hiện', 'Đã đóng')))
        out.append(('script', f'{ma}: áp dụng thay đổi vào dữ liệu nguồn: ' + (f'{LENH_CR} ap_dung {ma}' if co_ap_dung else
                    'lệnh ap_dung của qlda-change chưa có, sửa dữ liệu nguồn theo tai_lieu_cap_nhat của CR (gọi lệnh khi có)'),
                    bool(cr and (cr.get('ngay_ap_dung') or (cr.get('ap_dung') or {}).get('da_ghi')))))  # qlda-change ghi khóa ap_dung.da_ghi
        bl = [x['ma'] for x in loi.doc_json('du_lieu/phien_ban.json', {}).get('duong_co_so', [])]
        out.append(('script', f'{ma}: chạy lại các bước kế hoạch bị ảnh hưởng theo thứ tự {LENH_CHAY} trang_thai (wbs, giao_viec, lich, rui_ro, '
                    'chi_phi, tài liệu kế hoạch)', 'BL2' in bl))  # BL2 chỉ lập được khi tài liệu kế hoạch đã dùng đầu vào mới
        out.append(('script', f'{LENH_PB} duong_co_so BL2 --ten "Đường cơ sở sau {ma}" --cr {ma}',
                    'BL2' in bl))
    return truoc, out


def cac_buoc(sp):
    """[(loại, lệnh hoặc mô tả, đã xong)] của sprint hoặc kỳ KT sp."""
    st = loi.doc_json(C.TEP_MO_PHONG, {}) or {}
    rec = next((x for x in st.get('sprint', []) if x['ma'] == sp), None)
    moc = rec['thoi_gian'] if rec else None
    tep_kb = f'{C.THU_MUC_LV}/kich_ban_{sp}.json'
    kb = loi.doc_json(tep_kb) if ton_tai(tep_kb) else {}
    td = f'du_lieu/tien_do/{sp}.json'
    bc = f'ket_qua/09_Bao_cao_tien_do/Bao_cao_tien_do_{sp}.docx'
    pb = phien_ban(bc)
    ky = f'{NGAY} --ma {sp}' if sp == C.KY_KET_THUC else sp
    out = []
    if sp == 'S1':
        hd = loi.doc_json('du_lieu/phien_ban.json', {}).get('hop_dong')
        out.append(('script', f'{LENH_PB} duong_co_so BL1 --ten "Đường cơ sở hợp đồng" --hop-dong (bước 0, ký hợp đồng trước S1)', bool(hd)))
    out += [('agent', f'Agent Mô phỏng viết {tep_kb} theo {S}/qlda-mo-phong/prompts/vai_mo_phong.md', bool(kb)),
            ('script', f'{LENH_MP} {sp}', bool(rec))]
    cr_truoc, cr_sau = buoc_cr(sp, kb)
    td_xong = bool(rec) and moi_hon(td, moc)
    bc_xong = td_xong and moi_hon(bc, moc)
    buoc_ph = []
    if sp != C.KY_KET_THUC:  # bản phát hành lập ngay sau khi có hoan_thanh.csv, loi.csv của sprint, trước khi đăng ký tài liệu của kỳ
        lenh_ph = tim_lenh_phat_hanh()
        ds_ph = loi.doc_json('du_lieu/phat_hanh.json', {}).get('ban_phat_hanh', [])
        r_ma = 'R' + sp.lstrip('S')
        buoc_ph.append(('script', f'{lenh_ph} {sp} --ghi-chu "Số liệu thực tế của bản phát hành lấy từ kết quả mô phỏng sprint {sp}."' if lenh_ph else
                        f'Phát hành bản {r_ma}: lệnh phát hành chưa có trong bộ skill, gọi khi có', any(x.get('ma') == r_ma for x in ds_ph)))
    buoc_td = [('script', f'{LENH_TD} --ky {ky}', td_xong)] + buoc_ph + [
               ('script', f'{LENH_CHAY} chuan_bi bao_cao_tien_do', bc_xong or (td_xong and moi_hon('lam_viec/bao_cao_tien_do/khung.json', moc))),
               ('agent', 'Agent Soạn thảo viết lam_viec/bao_cao_tien_do/ban_soan.json (qlda-loi/references/quy_trinh_chung.md), '
                'phần căn cứ ghi số liệu mô phỏng theo du_lieu/mo_phong.json', bc_xong),
               ('script', f'{LENH_CHAY} hoan_thien bao_cao_tien_do --ghi-chu "Kỳ {sp}, số liệu mô phỏng"', bc_xong),
               ('agent', f'Agent Kiểm tra lớp B với {S}/qlda-bao-cao-tien-do/dac_ta/bao_cao_tien_do.json, đạt thì {LENH_PB} trang_thai {bc} '
                '--trang-thai "Đã kiểm tra" --nguoi "..."', bc_xong and bool(pb) and pb[-1].get('trang_thai') in ('Đã kiểm tra', 'Đã duyệt', 'Đường cơ sở'))]
    buoc_pb = [('script', f'{LENH_PB} tong_hop', bc_xong and moi_hon('du_lieu/phien_ban_tong_hop.json', moc)
                    and os.path.getmtime(loi.duong_dan('du_lieu/phien_ban_tong_hop.json')) >= os.path.getmtime(loi.duong_dan(bc)))]
    return out + cr_truoc + buoc_td + buoc_pb + cr_sau


def buoc_ket_thuc():
    sd = loi.so_do()
    st = loi.doc_json(C.TEP_MO_PHONG, {}) or {}
    moc = st['sprint'][-1]['thoi_gian'] if st.get('sprint') else None
    x = lambda n: moi_hon(loi.duong_dan_nut(sd, n) or '', moc) if moc else False  # noqa: E731
    kt = []
    if C.KY_KET_THUC in C.NguCanh().sprint:
        kt = [('agent', f'Kỳ Kết thúc sau cut over: python {S}/qlda-mo-phong/scripts/chu_trinh.py {C.KY_KET_THUC} (kịch bản, sinh số liệu, báo cáo kỳ)',
               any(r['ma'] == C.KY_KET_THUC for r in st.get('sprint', [])))]
    return kt + [('script', f'python {S}/qlda-tong-ket/scripts/tong_hop_ket_thuc.py', x('ket_thuc')),
            ('agent', f'{LENH_CHAY} chuan_bi tong_ket, agent Soạn thảo, {LENH_CHAY} hoan_thien tong_ket, kiểm tra lớp B', x('doc_tong_ket')),
            ('agent', f'{LENH_CHAY} chuan_bi danh_gia, agent Soạn thảo, {LENH_CHAY} hoan_thien danh_gia, kiểm tra lớp B', x('doc_danh_gia')),
            ('agent', f'Agent Rút bài học ({S}/qlda-bai-hoc/prompts/vai_rut_bai_hoc.md), python {S}/qlda-bai-hoc/scripts/kiem_tra_bai_hoc.py '
             'lam_viec/bai_hoc/bai_hoc_nhap.json', x('bai_hoc')),
            ('agent', f'{LENH_CHAY} chuan_bi bai_hoc, agent Soạn thảo, {LENH_CHAY} hoan_thien bai_hoc, kiểm tra lớp B', x('doc_bai_hoc')),
            ('script', f'python {S}/qlda-bang-luong/scripts/chia_luong.py', x('xlsx_luong')),
            ('agent', f'{LENH_CHAY} chuan_bi phien_ban, agent Soạn thảo, {LENH_CHAY} hoan_thien phien_ban', x('doc_phien_ban')),
            ('script', f'{LENH_CHAY} bang_chung', x('doc_bang_chung'))]


def hien_thi(mo_ta):
    return f'QLDA_NGAY={NGAY} {mo_ta}' if NGAY and mo_ta.startswith('python ') else mo_ta


def in_buoc(ds, tieu_de):
    print(tieu_de)
    tiep = None
    for i, (loai, mo_ta, xong) in enumerate(ds, 1):
        print(f'{i:2d}. [{"x" if xong else " "}] ({loai}) {hien_thi(mo_ta)}')
        if not xong and tiep is None:
            tiep = (loai, mo_ta)
    if tiep:
        print(f'Nên làm tiếp: ({tiep[0]}) {hien_thi(tiep[1])}')
    return tiep


def chay_script(ds):
    """Chạy liên tiếp các bước script chưa xong ở đầu danh sách, dừng ở bước agent hoặc người dùng đầu tiên."""
    for loai, mo_ta, xong in ds:
        if xong:
            continue
        if loai != 'script' or not mo_ta.startswith('python '):
            return
        lenh = shlex.split(mo_ta.split(' (')[0])
        print('>> ' + hien_thi(mo_ta))
        r = subprocess.run([sys.executable] + lenh[1:], cwd=loi.GOC, env=dict(os.environ, QLDA_NGAY=NGAY) if NGAY else None)
        if r.returncode not in (0,):
            sys.exit(1)
        if 'chuan_bi' in lenh:
            return


NGAY = ''  # ngày hiện hành khi mô phỏng (QLDA_NGAY): ngày cuối của kỳ, dùng cho ngày tài liệu, bản phát hành, đường cơ sở


def main():
    global NGAY
    ap = argparse.ArgumentParser(); ap.add_argument('doi_tuong'); ap.add_argument('--chay', action='store_true')
    a = ap.parse_args()
    ctx = C.NguCanh()
    if a.doi_tuong == 'ket_thuc':
        NGAY = ctx.days[-1].isoformat()
        ds = buoc_ket_thuc()
        tiep = in_buoc(ds, 'Giai đoạn kết thúc (sau sprint cuối, dữ liệu thực tế mô phỏng xem du_lieu/mo_phong.json):')
    else:
        if a.doi_tuong not in ctx.sprint:
            loi.thoat_loi(f'{a.doi_tuong} không phải sprint hay kỳ KT của du_lieu/lich.json')
        NGAY = ctx.ngay_sprint(a.doi_tuong)[-1].isoformat()
        ds = cac_buoc(a.doi_tuong)
        if a.chay:
            chay_script(ds)
            ds = cac_buoc(a.doi_tuong)
        tiep = in_buoc(ds, f'Chu trình mô phỏng sprint {a.doi_tuong}:')
    sys.exit(2 if tiep else 0)


if __name__ == '__main__':
    main()
