"""Bản phát hành theo sprint: cuối mỗi sprint một bản R<n>, bản của sprint có cut over là bản phát hành chính thức.

Dùng: python phat_hanh.py <S1 [S2 ...] | tat_ca> [--ghi-chu "..."]
      tat_ca: mọi sprint của lịch đã kết thúc đến ngày hiện hành (QLDA_NGAY khi mô phỏng), cộng --ke-hoach để lập cả sprint chưa tới.
Đầu vào: du_lieu/lich.json (sprint, giai đoạn gói), du_lieu/wbs.json (hạng mục Mẫu 01A, nguồn yêu cầu RFP của gói),
         du_lieu/hsmt.json (tên hạng mục Mẫu 01A), dau_vao/thuc_te/hoan_thanh.csv, dau_vao/thuc_te/loi.csv, du_lieu/thay_doi.json.
Cách lập mỗi bản (ngày phát hành là ngày cuối sprint):
- Gói hoàn thành: gói lá giai đoạn Thực hiện đạt 100% trong hoan_thanh.csv từ sau bản trước đến ngày phát hành (nguồn thực tế).
  Khi hoan_thanh.csv chưa có dòng nào từ ngày đầu sprint thì lấy gói kế hoạch xong trong sprint theo lịch, đánh dấu nguồn kế hoạch.
  Gói quản lý dự án (Khởi động, Suốt dự án, Kết thúc) không thuộc bản phát hành sản phẩm.
- Tính năng: hạng mục Mẫu 01A và yêu cầu RFP (mã R trong nguồn của gói) mà gói của bản phủ, kèm trạng thái đã đủ gói tích lũy.
- Lỗi đã sửa: loi.csv trạng thái Đã đóng, ngày đóng trong kỳ. Lỗi còn mở: phát hiện đến ngày phát hành, chưa đóng đến ngày đó.
- Yêu cầu thay đổi: CR được phê duyệt (Đã phê duyệt, Đã thực hiện, Đã đóng sau thực hiện) có gói mới hoặc gói thay đổi
  hoàn thành trong bản (đưa vào), CR phê duyệt trong kỳ chưa có gói hoàn thành (đã nhận vào phạm vi).
- Ghi chú phát hành: câu tóm tắt do script lập từ số liệu, cộng --ghi-chu của nhóm (lập lại không có --ghi-chu thì giữ ghi chú cũ).
Ra: du_lieu/phat_hanh.json {ban_phat_hanh: [...], ban_chinh_thuc}. Lập lại một sprint thì thay bản cũ cùng mã, giữ bản khác.
Phiên bản tài liệu đăng ký sau ký hợp đồng ghi khóa phat_hanh là bản hiện hành tại ngày tài liệu (loi.ban_phat_hanh_hien_hanh).
Mã thoát 0 đạt, 1 lỗi.
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
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

TIEN_TO = 'R'
TRANG_THAI_CR_HIEU_LUC = ('Đã phê duyệt', 'Đã thực hiện')
KET_QUA_CR_KHONG_HIEU_LUC = ('Từ chối', 'Hoãn')
TRANG_THAI_LOI_DONG = 'Đã đóng'
PHAN_TRAM_XONG = 100.0
TEP_RA = 'du_lieu/phat_hanh.json'
TEP_VAO = ['du_lieu/lich.json', 'du_lieu/wbs.json', 'du_lieu/hsmt.json', 'dau_vao/thuc_te/hoan_thanh.csv', 'dau_vao/thuc_te/loi.csv',
           'du_lieu/thay_doi.json']

ap = argparse.ArgumentParser()
ap.add_argument('sprint', nargs='+', help='mã sprint (S1 S2) hoặc tat_ca')
ap.add_argument('--ke-hoach', action='store_true', help='với tat_ca: lập cả sprint chưa kết thúc theo kế hoạch')
ap.add_argument('--ghi-chu', default='', help='ghi chú phát hành của nhóm, thêm sau câu tóm tắt')
a = ap.parse_args()

lich = loi.doc_json('du_lieu/lich.json')
wbs = loi.doc_json('du_lieu/wbs.json')
hsmt = loi.doc_json('du_lieu/hsmt.json', {})
F = []


def add(ma, mo_ta, vi_tri='', muc_do='loi'):
    F.append({'ma': ma, 'muc_do': muc_do, 'nhom': 'phat_hanh', 'vi_tri': vi_tri, 'mo_ta': mo_ta})


sprints = lich['sprint']
SP = {s['ma']: s for s in sprints}
_, la = loi.nut_wbs(wbs)
LA = {g['ma']: g for g in la}
lg = {g['ma']: g for g in lich['goi']}
gd = {m: lg.get(m, {}).get('giai_doan') or 'thuc_hien' for m in LA}
GOI_SP = {m for m in LA if gd[m] == 'thuc_hien'}  # gói sản phẩm (giai đoạn Thực hiện)
TEN_01A = {h['stt']: h['danh_muc'] for h in hsmt.get('mau_01a', [])}
YEU_CAU = {x['ma']: x['yeu_cau'] for x in wbs.get('truy_vet_rfp', [])}

if a.sprint == ['tat_ca']:
    hom_nay = loi.ngay_hien_hanh()
    chon = [s['ma'] for s in sprints if a.ke_hoach or s['den'] <= hom_nay]
    if not chon:
        loi.thoat_loi(f'Chưa có sprint nào kết thúc đến {loi.ngay(hom_nay)}. Dùng --ke-hoach để lập theo kế hoạch.')
else:
    chon = a.sprint
    for s_ in chon:
        if s_ not in SP:
            add('PH01', f'Sprint {s_} không có trong du_lieu/lich.json ({", ".join(SP)})', s_)

# ngày hoàn thành thực tế của từng gói: lần cập nhật đầu tiên đạt 100%
ht = sorted(loi.doc_csv('dau_vao/thuc_te/hoan_thanh.csv'), key=lambda r: r.get('ngay_cap_nhat', ''))
ngay_xong, ngay_ht_cuoi = {}, ''
for i, r in enumerate(ht, 2):
    d = loi.ngay_iso(r.get('ngay_cap_nhat'))
    if not d or r.get('ma_goi') not in LA:
        add('PH02', f'hoan_thanh.csv dòng {i}: ngày hoặc mã gói {r.get("ma_goi")} không hợp lệ (phải là gói lá WBS)', str(i), 'canh_bao'); continue
    try:
        pt = float(r.get('phan_tram') or 0)
    except ValueError:
        add('PH02', f'hoan_thanh.csv dòng {i}: phan_tram {r.get("phan_tram")} không phải số', str(i), 'canh_bao'); continue
    ngay_ht_cuoi = max(ngay_ht_cuoi, d)
    if pt >= PHAN_TRAM_XONG - 1e-9 and r['ma_goi'] not in ngay_xong:
        ngay_xong[r['ma_goi']] = d

bug = loi.doc_csv('dau_vao/thuc_te/loi.csv')
cr_ds = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []}).get('yeu_cau', [])


def cr_hieu_luc(c, den):
    """CR đã được phê duyệt đến ngày den và không bị từ chối, hoãn."""
    if not c.get('ngay_quyet_dinh') or c['ngay_quyet_dinh'][:10] > den:
        return False
    if c.get('trang_thai') == 'Đã đóng':
        return c.get('ket_qua_dong') not in KET_QUA_CR_KHONG_HIEU_LUC
    return c.get('trang_thai') in TRANG_THAI_CR_HIEU_LUC


def goi_xong(den, thuc_te):
    """Gói sản phẩm đã xong đến ngày den (thực tế theo hoan_thanh.csv, kế hoạch theo lịch)."""
    if thuc_te:
        return {m for m, d in ngay_xong.items() if d <= den and m in GOI_SP}
    return {m for m in GOI_SP if lg.get(m, {}).get('ket_thuc', '9999') <= den}


def tinh_nang(goi_ban, xong):
    """Hạng mục Mẫu 01A và yêu cầu RFP mà gói của bản phủ, đã đủ gói (tích lũy) hay chưa."""
    hm, yc = {}, {}
    for m in GOI_SP:
        for h in LA[m].get('hang_muc_01a', []):
            hm.setdefault(h, []).append(m)
        for n in LA[m].get('nguon', []):
            if str(n).startswith('R') and str(n)[1:].isdigit():
                yc.setdefault(n, []).append(m)
    out_hm = [{'stt': h, 'danh_muc': TEN_01A.get(h, ''), 'so_goi_trong_ban': sum(1 for m in ds if m in goi_ban),
               'so_goi_xong': sum(1 for m in ds if m in xong), 'tong_goi': len(ds), 'hoan_thanh': all(m in xong for m in ds)}
              for h, ds in sorted(hm.items()) if any(m in goi_ban for m in ds)]
    out_yc = [{'ma': n, 'yeu_cau': YEU_CAU.get(n, ''), 'goi': sorted((m for m in ds if m in goi_ban), key=loi.khoa_ma),
               'hoan_thanh': all(m in xong for m in ds)}
              for n, ds in sorted(yc.items(), key=lambda kv: int(kv[0][1:])) if any(m in goi_ban for m in ds)]
    return out_hm, out_yc


def loi_ky(tu, den):
    """(lỗi đã sửa trong kỳ (tu, den], lỗi còn mở tại den) theo loi.csv."""
    gon = lambda r: {'ma': r.get('ma', ''), 'muc_do': r.get('muc_do', ''), 'ma_goi': r.get('ma_goi', ''), 'mo_ta': r.get('mo_ta', '')}
    da_sua, con_mo = [], []
    for r in bug:
        ph, dong = loi.ngay_iso(r.get('ngay_phat_hien')), loi.ngay_iso(r.get('ngay_dong'))
        if not ph or ph > den:
            continue
        if r.get('trang_thai') == TRANG_THAI_LOI_DONG and dong and dong <= den:
            if dong > tu:
                da_sua.append(gon(r))
        else:
            con_mo.append(gon(r))
    return da_sua, con_mo


def dem_muc_do(ds):
    out = {}
    for x in ds:
        out[x['muc_do'] or 'Chưa phân loại'] = out.get(x['muc_do'] or 'Chưa phân loại', 0) + 1
    return out


MO_PHONG = os.path.exists(loi.duong_dan('du_lieu/mo_phong.json'))  # số liệu thực tế do qlda-mo-phong sinh


def lap_ban(s, ghi_chu_nhom=''):
    i = sprints.index(s)
    tu = sprints[i - 1]['den'] if i else '0000-00-00'  # sau ngày phát hành bản trước
    den = s['den']
    thuc_te = bool(ngay_ht_cuoi) and ngay_ht_cuoi >= s['tu']
    ke_hoach_sp = [m for m in s.get('goi_hoan_thanh', []) if m in GOI_SP]
    if thuc_te:
        goi_ban = sorted((m for m, d in ngay_xong.items() if tu < d <= den and m in GOI_SP), key=loi.khoa_ma)
    else:
        goi_ban = sorted(ke_hoach_sp, key=loi.khoa_ma)
    xong = goi_xong(den, thuc_te)
    chua_xong_kh = sorted((m for m in GOI_SP if lg.get(m, {}).get('ket_thuc', '9999') <= den and m not in xong), key=loi.khoa_ma) if thuc_te else []
    hm, yc = tinh_nang(set(goi_ban), xong)
    da_sua, con_mo = loi_ky(tu, den)
    cr_vao, cr_nhan = [], []
    for c in cr_ds:
        if not cr_hieu_luc(c, den):
            continue
        g_cr = [x['ma'] for x in c.get('goi_moi', []) + c.get('goi_thay_doi', []) if x.get('ma')]
        trong = sorted((m for m in g_cr if m in goi_ban), key=loi.khoa_ma)
        if trong:
            cr_vao.append({'ma': c['ma'], 'tieu_de': c.get('tieu_de', ''), 'ngay_quyet_dinh': c['ngay_quyet_dinh'][:10], 'goi': trong})
        elif tu < c['ngay_quyet_dinh'][:10] <= den:
            cr_nhan.append({'ma': c['ma'], 'tieu_de': c.get('tieu_de', ''), 'ngay_quyet_dinh': c['ngay_quyet_dinh'][:10], 'goi': g_cr})
    chinh_thuc = den == lich['cut_over']
    ma = f'{TIEN_TO}{s["so"]}'
    loai = 'Chính thức, đưa vào vận hành (cut over)' if chinh_thuc else 'Trình diễn cuối sprint'
    tom_tat = (f'Bản {ma} phát hành ngày {loi.ngay(den)}, cuối sprint {s["ma"]}, loại {loai.lower()}. Gồm {len(goi_ban)} gói hoàn thành trong sprint'
               f' ({("theo số liệu thực tế mô phỏng" if MO_PHONG else "theo số liệu thực tế") if thuc_te else "theo kế hoạch, chưa có số liệu thực tế"}), phủ {len(hm)} hạng mục Mẫu 01A và '
               f'{len(yc)} yêu cầu RFP, sửa {len(da_sua)} lỗi, còn mở {len(con_mo)} lỗi.')
    if cr_vao:
        tom_tat += ' Đưa vào yêu cầu thay đổi ' + ', '.join(c['ma'] for c in cr_vao) + '.'
    if chua_xong_kh:
        tom_tat += f' Có {len(chua_xong_kh)} gói theo kế hoạch đến hạn trước ngày phát hành nhưng chưa hoàn thành.'
    return {'ma': ma, 'sprint': s['ma'], 'ngay': den, 'tu_ngay': s['tu'], 'loai': loai, 'chinh_thuc': chinh_thuc,
            'nguon': 'thuc_te' if thuc_te else 'ke_hoach', 'muc_tieu': s.get('muc_tieu', ''), 'san_pham_demo': s.get('san_pham_demo', ''),
            'goi': goi_ban, 'so_goi': len(goi_ban), 'md': round(sum(float(LA[m]['md']) for m in goi_ban), 2),
            'goi_ke_hoach': sorted(ke_hoach_sp, key=loi.khoa_ma), 'goi_chua_xong_theo_ke_hoach': chua_xong_kh,
            'so_goi_tich_luy': len(xong), 'tong_goi_san_pham': len(GOI_SP),
            'hang_muc_01a': hm, 'yeu_cau_rfp': yc, 'loi_da_sua': da_sua, 'loi_con_mo': con_mo,
            'so_loi_da_sua': len(da_sua), 'so_loi_con_mo': len(con_mo), 'loi_con_mo_theo_muc_do': dem_muc_do(con_mo),
            'cr_dua_vao': cr_vao, 'cr_phe_duyet_trong_ky': cr_nhan,
            'ghi_chu_nhom': ghi_chu_nhom, 'ghi_chu': (tom_tat + (' ' + ghi_chu_nhom if ghi_chu_nhom else '')).strip(), 'lap_luc': loi.bay_gio()}


loi_ = [f for f in F if f['muc_do'] == 'loi']
for f in F:
    print(f"[{f['muc_do']}] {f['ma']} {f['vi_tri']}: {f['mo_ta']}")
if loi_:
    loi.thoat_loi(f'{len(loi_)} lỗi, chưa lập bản phát hành.')

cu = loi.doc_json(TEP_RA, {'ban_phat_hanh': []})
ban = {x['ma']: x for x in cu.get('ban_phat_hanh', []) if x.get('sprint') in SP}  # bỏ bản của sprint không còn trong lịch
for s_ in chon:
    ma_ = TIEN_TO + str(SP[s_]['so'])
    b = lap_ban(SP[s_], a.ghi_chu.strip() or ban.get(ma_, {}).get('ghi_chu_nhom', ''))  # lập lại không có --ghi-chu thì giữ ghi chú cũ
    ban[b['ma']] = b
    print(f'{b["ma"]} ({b["sprint"]}, {loi.ngay(b["ngay"])}, nguồn {"thực tế" if b["nguon"] == "thuc_te" else "kế hoạch"}): '
          f'{b["so_goi"]} gói, {len(b["hang_muc_01a"])} hạng mục 01A, lỗi sửa {b["so_loi_da_sua"]}, còn mở {b["so_loi_con_mo"]}, '
          f'CR {", ".join(c["ma"] for c in b["cr_dua_vao"]) or "không"}' + (' [chính thức]' if b['chinh_thuc'] else ''))
ds = sorted(ban.values(), key=lambda x: (x['ngay'], int(x['ma'][len(TIEN_TO):])))
out = {'ngay_cap_nhat': loi.bay_gio()[:10], 'cut_over': lich['cut_over'], 'ban_phat_hanh': ds,
       'ban_chinh_thuc': next((x['ma'] for x in ds if x['chinh_thuc']), ''),
       'kiem_tra': {'ket_luan': 'dat', 'so_canh_bao': len(F), 'phat_hien': F}}
loi.ghi_json(TEP_RA, out)
sd = loi.so_do()
ma_lap = [TIEN_TO + str(SP[s_]['so']) for s_ in chon]
mo_ta = 'Lập bản phát hành ' + ', '.join(ma_lap)
if any(b_['id'] == 'phat_hanh' for b_ in sd['buoc']):
    loi.hoan_tat_buoc('phat_hanh', mo_ta)
else:  # sơ đồ phụ thuộc chưa có bước phat_hanh: chỉ ghi nhật ký
    loi.ghi_nhat_ky('qlda-master-schedule', 'phat_hanh', 'script', mo_ta, vao=[p for p in TEP_VAO if os.path.exists(loi.duong_dan(p))],
                    ra=[TEP_RA], ket_qua='đạt')
print(f'Đã ghi {TEP_RA}: {len(ds)} bản phát hành' + (f', bản chính thức {out["ban_chinh_thuc"]}' if out['ban_chinh_thuc'] else '') + '.')
