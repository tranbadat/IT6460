"""Sinh số liệu thực tế mô phỏng cho một sprint từ kịch bản biến cố, nhất quán với kế hoạch đã duyệt hiện hành.

Dùng (chạy từ thư mục gốc dự án):
  python .claude/skills/qlda-mo-phong/scripts/mo_phong_sprint.py S2 [--kich-ban lam_viec/mo_phong/kich_ban_S2.json] [--hat-giong 2027]
  python .../mo_phong_sprint.py S2 --lam-lai [--ep]   xóa phần dữ liệu của S2 (và các sprint sau) rồi sinh lại từ kịch bản
  python .../mo_phong_sprint.py kiem_tra              chỉ kiểm tra nhất quán toàn bộ dữ liệu thực tế hiện có (MP01 đến MP12)
Đầu vào: kịch bản lam_viec/mo_phong/kich_ban_S<n>.json (references/kich_ban.md), du_lieu/lich.json (goi, phan_bo, moc, sprint),
         du_lieu/wbs.json, rui_ro.json, thay_doi.json, hsmt.json, rfp_yeu_cau.json, dau_vao/thanh_vien.json, don_gia.json, du_an.json,
         dữ liệu thực tế đã có trong dau_vao/thuc_te/.
Ra: ghi nối tiếp dau_vao/thuc_te/*.csv và retro.md; du_lieu/mo_phong.json (ghi chú số liệu mô phỏng, hạt giống, kịch bản, việc hẹn);
    lam_viec/mo_phong/truoc_S<n>/ (bản chụp trước khi sinh, dùng cho --lam-lai), lich_S<n>.json (kế hoạch dùng khi sinh),
    ket_qua_S<n>.json (tóm tắt), cr_S<n>_<mã>.json (thông tin yêu cầu thay đổi cho agent Đánh giá thay đổi).
Quy tắc:
- Sinh theo thứ tự sprint, mỗi sprint một lần. Sprint đã sinh thì dừng (idempotent), --lam-lai khôi phục bản chụp trước sprint đó
  (xóa luôn các sprint sau) rồi sinh lại. Tệp bị sửa tay sau lần sinh cuối thì --lam-lai dừng, trừ khi có --ep.
- Hạt giống ngẫu nhiên (--hat-giong ở sprint đầu, mặc định references/cau_hinh.json) lưu trong du_lieu/mo_phong.json, cùng hạt giống,
  cùng kịch bản, cùng kế hoạch thì ra cùng số liệu.
- Kiểm tra kịch bản KB01 đến KB15 (kich_ban.py) và nhất quán MP01 đến MP12 (kiem_tra_mo_phong.py) trước khi ghi; có lỗi thì không ghi gì.
Mã thoát: 0 đạt, 1 lỗi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ghi_bien_co as G  # noqa: E402
import kich_ban as KB  # noqa: E402
import kiem_tra_mo_phong as KT  # noqa: E402
import mp_chung as C  # noqa: E402
from mo_phong_lich import MoPhongLich  # noqa: E402

loi = C.loi


def in_phat_hien(F):
    for f in F:
        print(f'[{f["muc_do"]}] {f["ma"]}' + (f' {f["vi_tri"]}' if f.get('vi_tri') else '') + f': {f["mo_ta"]}')
    return [f for f in F if f['muc_do'] == 'loi']


def doc_tat_ca():
    return {t: C.doc_bang(t) for t in C.COT}


def trang_thai_mac_dinh(seed, nhieu):
    return {'_ghi_chu': C.GHI_CHU_MO_PHONG, 'so_lieu_mo_phong': True, 'can_cu_muc_bien_co': 'Quyết định của nhóm ngày 24/10/2026: biến cố vừa phải, '
            'vài gói chậm, 2 đến 3 rủi ro trong sổ xảy ra, lỗi theo tỷ lệ hợp lý, vấn đề mở rồi đóng, yêu cầu thay đổi tại S4, dự án vẫn hoàn thành',
            'phien_ban_skill': loi.phien_ban_skill(C.SKILL), 'hat_giong': seed, 'nhieu_md': nhieu, 'sprint': [], 'tac_dong_goi': {},
            'cho_xu_ly': [], 'yeu_cau_thay_doi': []}


def bam_tep():
    return {p: loi.bam(p) for p in C.tat_ca_tep()}


# ---------------------------------------------------------------- bản chụp, làm lại
def chup(ten):
    """Chụp dữ liệu thực tế và du_lieu/mo_phong.json vào lam_viec/mo_phong/<ten>/."""
    d = loi.duong_dan(f'{C.THU_MUC_LV}/{ten}')
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for p in C.tat_ca_tep() + [C.TEP_MO_PHONG]:
        if os.path.exists(loi.duong_dan(p)):
            shutil.copy2(loi.duong_dan(p), os.path.join(d, os.path.basename(p)))


def khoi_phuc(ten):
    d = loi.duong_dan(f'{C.THU_MUC_LV}/{ten}')
    if not os.path.isdir(d):
        loi.thoat_loi(f'Không có bản chụp {C.THU_MUC_LV}/{ten}/, không làm lại được')
    for p in C.tat_ca_tep() + [C.TEP_MO_PHONG]:
        src, dst = os.path.join(d, os.path.basename(p)), loi.duong_dan(p)
        if os.path.exists(src):
            shutil.copy2(src, dst)
        elif os.path.exists(dst):
            os.remove(dst)


def lam_lai(sp, st, ep):
    ma_da = [x['ma'] for x in st['sprint']]
    if sp not in ma_da:
        loi.thoat_loi(f'{sp} chưa được sinh, chạy không cần --lam-lai')
    cuoi = st['sprint'][-1]
    sua = [p for p, h in bam_tep().items() if cuoi.get('hash_sau', {}).get(p) != h]
    if sua and not ep:
        loi.thoat_loi(f'Các tệp đã bị sửa sau lần sinh {cuoi["ma"]}: {", ".join(sua)}. Làm lại sẽ mất phần sửa này. '
                      'Chuyển phần sửa vào kịch bản, hoặc chạy lại với --ep để chấp nhận mất')
    sau = ma_da[ma_da.index(sp) + 1:]
    chup(TAM_LAM_LAI)
    khoi_phuc(f'truoc_{sp}')
    print(f'Đã khôi phục dữ liệu thực tế về trước {sp}' + (f', xóa luôn {", ".join(sau)} (sinh lại theo thứ tự)' if sau else '') + '.')
    if os.path.exists(loi.duong_dan('du_lieu/tien_do')):
        print('Lưu ý: chạy lại tinh_tien_do.py cho các kỳ từ ' + sp + ' trở đi sau khi sinh lại.')


# ---------------------------------------------------------------- tác động lên gói, ngày nghỉ
def gop_tac_dong(cu, bien_co, kt):
    out = {k: dict(v) for k, v in cu.items()}
    for e in bien_co:
        g, them = None, {}
        if e['loai'] == 'goi':
            g = e['ma_goi']; them = {'ty_le': float(e.get('ty_le_md') or 0), 'tre': int(e.get('so_ngay_tre') or 0), 'co_bien_co': True}
        elif e['loai'] == 'rui_ro' and e.get('trang_thai', 'Đã xảy ra') == 'Đã xảy ra':
            g = e.get('ma_goi') or kt.goi_mac_dinh_rr(e['ma_rui_ro'])
            them = {'md_them': float(e.get('md_tac_dong') or 0), 'tre': int(e.get('ngay_tac_dong') or 0)}
        elif e['loai'] == 'loi' and e.get('md_sua'):
            g = e['ma_goi']; them = {'md_them': float(e['md_sua'])}
        if not g:
            continue
        x = out.setdefault(g, {'ty_le': 0.0, 'md_them': 0.0, 'tre': 0, 'co_bien_co': False})
        x['ty_le'] = round(x['ty_le'] + them.get('ty_le', 0), 4); x['md_them'] = round(x['md_them'] + them.get('md_them', 0), 2)
        x['tre'] += them.get('tre', 0); x['co_bien_co'] = x['co_bien_co'] or them.get('co_bien_co', False)
    return out


def ngay_nghi(ctx, sp, bien_co, rng):
    out, ngay = set(), ctx.ngay_sprint(sp)
    for e in [e for e in bien_co if e['loai'] == 'nghi']:
        n = int(e['so_ngay'])
        i0 = ngay.index(C.D(e['tu_ngay'])) if e.get('tu_ngay') else rng.randrange(0, len(ngay) - n + 1)
        out |= {(e['thanh_vien'], d) for d in ngay[i0:i0 + n]}
    return out


# ---------------------------------------------------------------- tóm tắt
def tom_tat(ctx, sp, rows, xong_moi, mp, bc, bien_co):
    nguoi = {}
    for r in rows:
        nguoi[r['thanh_vien']] = nguoi.get(r['thanh_vien'], 0) + float(r['md'])
    md_nguoi = {p: {'md': round(m, 2), 'quy': ctx.quy.get((p, sp), 0), 'ty_le_su_dung': round(m / ctx.quy[(p, sp)], 4) if ctx.quy.get((p, sp)) else 0}
                for p, m in sorted(nguoi.items())}
    md_ke_hoach = round(sum(float(x['md']) for x in ctx.lich['phan_bo'] if x['sprint'] == sp), 2)
    dem = {}
    for e in bien_co:
        dem[e['loai']] = dem.get(e['loai'], 0) + 1
    return {'sprint': sp, 'tong_md': round(sum(nguoi.values()), 2), 'md_ke_hoach_sprint': md_ke_hoach, 'md_theo_nguoi': md_nguoi,
            'goi_hoan_thanh': sorted(xong_moi, key=loi.khoa_ma), 'goi_cham': mp.goi_cham(C.cau_hinh()['nguong_cham']), 'spi_uoc_tinh': mp.spi_uoc_tinh(),
            'so_bien_co': dem, 'so_dong_them': {k: v for k, v in bc.dem.items() if v}, 'cho_xu_ly_con_lai': len(bc.hen)}


def goi_y(ctx, sp, tt, bc, mp, xong):
    """Gợi ý cho agent viết kịch bản: mốc đủ điều kiện chưa ghi, gói chậm chưa có vấn đề trong sổ, gói kẹt."""
    out = []
    for m, d in G.moc_du_dieu_kien(ctx, xong, {r['ma_moc'] for r in bc.bang['moc_thuc_te']}, bc.den):
        out.append(f'Mốc {m} đủ điều kiện từ {d} nhưng chưa ghi trong kịch bản (biến cố moc)')
    mo_ta = ' '.join(r['mo_ta'] for r in bc.bang['so_van_de'])
    for x in tt['goi_cham']:
        if x['ma'] not in mo_ta:
            out.append(f'Gói {x["ma"]} chậm (thực tế {x["thuc_te"]:.0%}, kế hoạch {x["ke_hoach"]:.0%}), sổ vấn đề chưa có vấn đề nêu mã gói: '
                       'báo cáo tiến độ sẽ cảnh báo T25. Thêm biến cố van_de rồi chạy --lam-lai nếu cần')
    for p, g in mp.khong_huy_dong if hasattr(mp, 'khong_huy_dong') else []:
        out.append(f'Gói {g} còn việc của {p} nhưng {p} không được huy động trong {sp}')
    return out


# ---------------------------------------------------------------- chạy
def kiem_tra_tat_ca():
    F = KT.kiem_tra(doc_tat_ca())
    loi_ = in_phat_hien(F)
    print(f'Kiểm tra nhất quán: {len(loi_)} lỗi, {len(F) - len(loi_)} cảnh báo.')
    loi.ghi_nhat_ky(C.SKILL, 'mo_phong.kiem_tra', 'script', f'Kiểm tra nhất quán dữ liệu thực tế: {len(loi_)} lỗi',
                    vao=[C.tep_csv(t) for t in C.COT], ket_qua='dat' if not loi_ else 'chua_dat')
    sys.exit(1 if loi_ else 0)


def kiem_tra_thu_tu(ctx, sp, st, bang):
    thu_tu = list(ctx.sprint)  # các sprint của lịch, rồi kỳ KT khi lịch có gói giai đoạn Kết thúc
    ma_da = [x['ma'] for x in st['sprint']]
    if sp in ma_da:
        loi.thoat_loi(f'{sp} đã được sinh ({next(x["thoi_gian"] for x in st["sprint"] if x["ma"] == sp)}). Không ghi trùng. '
                      f'Sinh lại thì dùng --lam-lai')
    truoc = thu_tu[:thu_tu.index(sp)]
    thieu = [s for s in truoc if s not in ma_da]
    if thieu:
        loi.thoat_loi(f'Chưa sinh {", ".join(thieu)}. Sinh theo thứ tự sprint')
    tu = ctx.sprint[sp]['tu']
    da_co = [r for r in bang['nhat_ky_cong_viec'] if r['ngay'] >= tu] + [r for r in bang['hoan_thanh'] if r['ngay_cap_nhat'] >= tu]
    if da_co:
        loi.thoat_loi(f'dau_vao/thuc_te/ đã có {len(da_co)} dòng từ ngày {tu} trở đi (nhập tay hoặc sinh trước). Không ghi trùng sprint {sp}')


TAM_LAM_LAI = 'tam_lam_lai'


def main():
    """Chạy một lần sinh. Khi --lam-lai mà lần sinh lại không thành công thì trả dữ liệu về như trước lệnh."""
    try:
        chay()
    except SystemExit as e:
        if e.code and os.path.isdir(loi.duong_dan(f'{C.THU_MUC_LV}/{TAM_LAM_LAI}')) and '--lam-lai' in sys.argv:
            khoi_phuc(TAM_LAM_LAI)
            print('Sinh lại không thành công, dữ liệu thực tế giữ nguyên như trước lệnh --lam-lai.')
        raise
    finally:
        tam = loi.duong_dan(f'{C.THU_MUC_LV}/{TAM_LAM_LAI}')
        if os.path.isdir(tam):
            shutil.rmtree(tam)


def chay():
    ap = argparse.ArgumentParser()
    ap.add_argument('sprint'); ap.add_argument('--kich-ban'); ap.add_argument('--hat-giong', type=int)
    ap.add_argument('--lam-lai', action='store_true'); ap.add_argument('--ep', action='store_true')
    a = ap.parse_args()
    if a.sprint == 'kiem_tra':
        kiem_tra_tat_ca()
    sp = a.sprint
    cfg = C.cau_hinh()
    st = loi.doc_json(C.TEP_MO_PHONG, {}) or {}
    if a.lam_lai:
        lam_lai(sp, trang_thai_mac_dinh(0, 0) | st, a.ep)
        st = loi.doc_json(C.TEP_MO_PHONG, {}) or {}
    seed = st.get('hat_giong', a.hat_giong if a.hat_giong is not None else cfg['hat_giong_mac_dinh'])
    if a.hat_giong is not None and st.get('sprint') and a.hat_giong != st['hat_giong']:
        loi.thoat_loi(f'Hạt giống đã cố định {st["hat_giong"]} từ sprint đầu. Đổi hạt giống thì làm lại từ S1 (--lam-lai)')
    tep_kb = a.kich_ban or f'{C.THU_MUC_LV}/kich_ban_{sp}.json'
    kb = loi.doc_json(tep_kb)
    st = trang_thai_mac_dinh(seed, kb.get('nhieu_md', cfg['nhieu_md'])) | st
    ctx = C.NguCanh()
    if sp not in ctx.sprint:
        loi.thoat_loi(f'Kỳ {sp} không có trong du_lieu/lich.json ({", ".join(ctx.sprint)})')
    bang = doc_tat_ca()
    kiem_tra_thu_tu(ctx, sp, st, bang)
    xong_cu = {}
    for r in sorted(bang['hoan_thanh'], key=lambda r: r['ngay_cap_nhat']):
        if float(r['phan_tram'] or 0) >= 100:
            xong_cu.setdefault(r['ma_goi'], r['ngay_cap_nhat'])
    tt = {'xong': xong_cu, 'vd': {r['ma'] for r in bang['so_van_de']}, 'moc': {r['ma_moc'] for r in bang['moc_thuc_te']},
          'rr_xay_ra': {r['ma_rui_ro'] for r in bang['theo_doi_rui_ro'] if r['trang_thai'] == 'Đã xảy ra'}}
    kt = KB.KiemTra(ctx, sp, kb, tt)
    if in_phat_hien(kt.chay()):
        loi.thoat_loi(f'Kịch bản {tep_kb} chưa hợp lệ, sửa rồi chạy lại')
    bien_co = kb['bien_co']
    rng = random.Random(f'{seed}:{sp}')
    tac_dong = gop_tac_dong(st['tac_dong_goi'], bien_co, kt)
    nghi = ngay_nghi(ctx, sp, bien_co, rng)
    mp = MoPhongLich(ctx, sp, tac_dong, nghi, bang['nhat_ky_cong_viec'], bang['hoan_thanh'], seed, st['nhieu_md'])
    rows, xong_moi, ht_moi, tk = mp.chay()
    mp.khong_huy_dong = tk['khong_huy_dong']
    bc = G.GhiBienCo(ctx, sp, bang, st['cho_xu_ly'], rng, dict(mp.xong)).chay(bien_co)
    bc.bang['nhat_ky_cong_viec'] += rows; bc.bang['hoan_thanh'] += ht_moi
    bc.dem['nhat_ky_cong_viec'] = len(rows); bc.dem['hoan_thanh'] = len(ht_moi)
    F = bc.F + KT.kiem_tra(bc.bang)
    if bc.retro and G.kiem_retro(sp):
        F.append({'ma': 'KB01', 'muc_do': 'loi', 'vi_tri': sp, 'mo_ta': G.kiem_retro(sp)})
    if in_phat_hien(F):
        loi.thoat_loi('Số liệu sinh ra không nhất quán, không ghi tệp nào. Sửa kịch bản hoặc dữ liệu đã có theo thông báo')
    ghi(ctx, sp, st, kb, tep_kb, bc, mp, xong_moi, rows, tac_dong)


def ghi(ctx, sp, st, kb, tep_kb, bc, mp, xong_moi, rows, tac_dong):
    if not os.path.isdir(loi.duong_dan(f'{C.THU_MUC_LV}/{TAM_LAM_LAI}')):
        chup(f'truoc_{sp}')
    loi.ghi_json(f'{C.THU_MUC_LV}/lich_{sp}.json', ctx.lich)
    for t in C.COT:
        C.ghi_bang(t, sorted(bc.bang[t], key=lambda r: (r.get('ngay') or r.get('ngay_cap_nhat') or '', )) if t in ('nhat_ky_cong_viec', 'hoan_thanh') else bc.bang[t])
    if bc.retro:
        G.ghi_retro(sp, bc.retro)
    for c in bc.cr:
        loi.ghi_json(f'{C.THU_MUC_LV}/cr_{sp}_{c.get("ma_cr", "CR")}.json', dict(c, sprint=sp, _ghi_chu='Thông tin yêu cầu thay đổi từ kịch bản mô phỏng, '
                     'đầu vào cho agent Đánh giá thay đổi (qlda-change/prompts/vai_danh_gia_thay_doi.md) lập lam_viec/thay_doi/cr_nhap.json'))
    tt = tom_tat(ctx, sp, rows, xong_moi, mp, bc, kb['bien_co'])
    gy = goi_y(ctx, sp, tt, bc, mp, mp.xong)
    tt['goi_y'] = gy
    loi.ghi_json(f'{C.THU_MUC_LV}/ket_qua_{sp}.json', tt)
    st['tac_dong_goi'] = tac_dong; st['cho_xu_ly'] = bc.hen
    st['yeu_cau_thay_doi'] = [x for x in st.get('yeu_cau_thay_doi', []) if x.get('sprint') != sp] + [
        {'ma_cr': c.get('ma_cr'), 'sprint': sp, 'ngay': c.get('ngay'), 'tieu_de': c.get('tieu_de'), 'tep': f'{C.THU_MUC_LV}/cr_{sp}_{c.get("ma_cr", "CR")}.json'}
        for c in bc.cr]
    st['sprint'].append({'ma': sp, 'tu': bc.tu, 'den': bc.den, 'kich_ban': loi.tuong_doi(loi.duong_dan(tep_kb)), 'kich_ban_hash': loi.bam(tep_kb),
                         'kich_ban_noi_dung': kb, 'lich_hash': loi.bam('du_lieu/lich.json'), 'thoi_gian': loi.bay_gio(), 'tom_tat': {
                             k: tt[k] for k in ('tong_md', 'md_ke_hoach_sprint', 'spi_uoc_tinh', 'goi_hoan_thanh', 'so_bien_co', 'so_dong_them')}, 'hash_sau': bam_tep()})
    loi.ghi_json(C.TEP_MO_PHONG, st)
    for x in gy:
        print('[goi_y] ' + x)
    print(f'Đã sinh {sp} ({loi.ngay(bc.tu)} đến {loi.ngay(bc.den)}): {tt["tong_md"]:g} MD ghi công (kế hoạch sprint {tt["md_ke_hoach_sprint"]:g} MD), '
          f'{len(xong_moi)} gói hoàn thành, {len(tt["goi_cham"])} gói chậm, SPI ước tính {tt["spi_uoc_tinh"]:.2f}, dòng thêm: '
          + ', '.join(f'{k} {v}' for k, v in tt['so_dong_them'].items()) + f'. Việc hẹn sang sprint sau: {len(bc.hen)}.')
    ky = f'{bc.den} --ma {sp}' if sp == C.KY_KET_THUC else sp
    print(f'Tiếp theo: python .claude/skills/qlda-bao-cao-tien-do/scripts/tinh_tien_do.py --ky {ky}'
          + (' (trước đó chạy quy trình qlda-change danh_gia cho yêu cầu thay đổi trong kịch bản)' if bc.cr else ''))
    loi.ghi_nhat_ky(C.SKILL, f'mo_phong.{sp}.sinh', 'script', f'Sinh số liệu mô phỏng {sp}: {tt["tong_md"]:g} MD, {len(xong_moi)} gói hoàn thành',
                    vao=[tep_kb, 'du_lieu/lich.json', 'du_lieu/rui_ro.json'], ra=C.tat_ca_tep() + [C.TEP_MO_PHONG],
                    ket_qua='dat', chi_tiet={'hat_giong': st['hat_giong'], 'so_dong_them': tt['so_dong_them']})


if __name__ == '__main__':
    main()
