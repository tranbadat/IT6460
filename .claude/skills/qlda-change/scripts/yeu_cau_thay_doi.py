"""Ghi, đánh giá tác động và ra quyết định cho yêu cầu thay đổi (CR). Sổ thay đổi: du_lieu/thay_doi.json.

Dùng:
  python yeu_cau_thay_doi.py danh_gia <cr_nhap.json>
      Đánh giá CR do agent hoặc người dùng lập:
      {"tieu_de", "mo_ta", "ly_do", "nguoi_de_xuat", "ngay": "yyyy-mm-dd", "nguon": "chủ đầu tư | nhà thầu | rủi ro RRxx",
       "goi_thay_doi": [{"ma": "5.3.2", "md_tang": 3}], "goi_moi": [{"ma": "5.3.9", "ten": "...", "md": 4, "loai": "DEV", "cha": "5.3"}],
       "nut_thay_doi": ["wbs"]}   (nút trong sơ đồ phụ thuộc bị đổi trực tiếp; mặc định wbs)
      Tính: MD tăng, chi phí (MD x đơn giá loại công việc), số ngày chậm ước tính (gói trên đường găng hoặc vượt dự trữ),
      ảnh hưởng mốc, phân loại cấp phê duyệt, danh sách tài liệu phải cập nhật. Ghi CR trạng thái Chờ phê duyệt.
  python yeu_cau_thay_doi.py quyet_dinh <ma_cr> --ket-qua "Đã phê duyệt|Từ chối|Hoãn" --nguoi "<người quyết định>" [--ngay yyyy-mm-dd] [--ghi-chu ...]
  python yeu_cau_thay_doi.py dong <ma_cr> --ghi-chu "<đã cập nhật tài liệu nào>" [--ngay yyyy-mm-dd] [--bo-qua-kiem-tra]
      Chỉ đóng khi mọi tài liệu trong tai_lieu_cap_nhat đã tạo lại với đầu vào mới. Ghi phiên bản sau thay đổi vào phien_ban_sau.
  --ngay là ngày theo lịch dự án (biên bản họp, email phê duyệt), mặc định là ngày chạy lệnh. Thời gian xử lý CR tính từ ngày đề xuất đến ngày này.
  python yeu_cau_thay_doi.py danh_sach
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse, datetime as dt, json, math, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('lenh'); ap.add_argument('doi_tuong', nargs='?'); ap.add_argument('--ket-qua'); ap.add_argument('--nguoi', default=''); ap.add_argument('--ghi-chu', default='')
ap.add_argument('--ngay')
ap.add_argument('--bo-qua-kiem-tra', action='store_true')
a = ap.parse_args()
NGAY = a.ngay or loi.bay_gio()[:10]
if a.ngay:
    dt.date.fromisoformat(a.ngay)
PL = json.load(open(os.path.join(HERE, '..', 'references', 'phan_loai.json'), encoding='utf-8'))
so = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})

if a.lenh == 'danh_sach':
    for c in so['yeu_cau']:
        print(f'{c["ma"]} [{c["trang_thai"]}] {c["tieu_de"]} | {c["md_tang"]:g} MD, {loi.tien(c["chi_phi_tang"])} đồng, chậm {c["ngay_cham"]} ngày, mức {c["muc_ten"]}')
    sys.exit(0)

if a.lenh == 'danh_gia':
    cr = json.load(open(a.doi_tuong, encoding='utf-8'))
    wbs = loi.doc_json('du_lieu/wbs.json'); lich = loi.doc_json('du_lieu/lich.json'); dg = loi.doc_json('dau_vao/don_gia.json')
    pc = loi.doc_json('du_lieu/phan_cong.json'); tv = {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']}
    by = {g['ma']: g for g in wbs['goi']}; lg = {x['ma']: x for x in lich['goi']}; gv = {x['ma']: x for x in pc['giao_viec']}
    loi_ds = []
    md_tang, chi_phi, cham, chi_tiet = 0.0, 0.0, 0, []
    rate = lambda loai: dg['loai_cong_viec'][loai]['don_gia_tron_goi_thang'] / dg['md_moi_mm']
    for x in cr.get('goi_thay_doi', []):
        g = by.get(x['ma'])
        if not g or not g['la']:
            loi_ds.append(f'Gói {x["ma"]} không phải gói lá của WBS'); continue
        d = float(x['md_tang']); md_tang += d; chi_phi += d * rate(g['loai'])
        l = lg.get(x['ma'], {})
        ng = gv[x['ma']]; toc_do = sum(float(tv[p].get('ty_le', 1)) for p in [ng['R']] + ng.get('ho_tro', []))
        them_ngay = math.ceil(d / toc_do) if d > 0 else 0
        du_tru = l.get('du_tru_cpm', 0)
        c = max(0, them_ngay - du_tru) if not l.get('gang') else them_ngay
        cham = max(cham, c)
        chi_tiet.append({'ma': x['ma'], 'ten': g['ten'], 'md_tang': d, 'gang': bool(l.get('gang')), 'du_tru': du_tru, 'ngay_cham': c})
    for x in cr.get('goi_moi', []):
        if x.get('loai') not in dg['loai_cong_viec']:
            loi_ds.append(f'Gói mới {x.get("ma")} thiếu loại công việc hợp lệ'); continue
        if x.get('cha') not in by:
            loi_ds.append(f'Gói mới {x.get("ma")} có mục cha {x.get("cha")} không tồn tại')
        md_tang += float(x['md']); chi_phi += float(x['md']) * rate(x['loai'])
        chi_tiet.append({'ma': x['ma'], 'ten': x['ten'], 'md_tang': float(x['md']), 'gang': False, 'du_tru': None, 'ngay_cham': None})
    if loi_ds:
        loi.thoat_loi('\n- '.join([''] + loi_ds))
    du_tru_du_an = lich.get('du_tru_den_cut_over_ngay', 0)
    cham_cut_over = max(0, cham - du_tru_du_an)
    muc = next(m for m in PL['muc'] if (m['md_toi_da'] is None or md_tang <= m['md_toi_da']) and (m['ngay_cham_toi_da'] is None or cham_cut_over <= m['ngay_cham_toi_da'])
               and (m['chi_phi_toi_da'] is None or chi_phi <= m['chi_phi_toi_da']))
    nut = cr.get('nut_thay_doi') or ['wbs']
    KY_HD = loi.da_ky_hop_dong()  # trước khi ký hợp đồng, HSMT và HSDT chưa khóa
    tl = []
    for n in nut:
        r = subprocess.run([sys.executable, os.path.join(loi.THU_MUC_LOI, 'scripts', 'chay.py'), 'anh_huong', n, '--json'], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=loi.GOC)
        for b in json.loads(r.stdout)['anh_huong']:
            if b['buoc'] not in [x['buoc'] for x in tl]:
                tl.append(b)
    ma = f'CR{len(so["yeu_cau"]) + 1:02d}'
    rec = {'ma': ma, 'tieu_de': cr['tieu_de'], 'mo_ta': cr.get('mo_ta', ''), 'ly_do': cr.get('ly_do', ''), 'nguon': cr.get('nguon', ''),
           'nguoi_de_xuat': cr.get('nguoi_de_xuat', ''), 'ngay_de_xuat': cr.get('ngay', loi.bay_gio()[:10]), 'md_tang': round(md_tang, 2),
           'chi_phi_tang': round(chi_phi), 'ngay_cham': cham, 'ngay_cham_cut_over': cham_cut_over, 'chi_tiet_goi': chi_tiet,
           'muc': muc['ma'], 'muc_ten': muc['ten'], 'nguoi_phe_duyet_theo_quy_dinh': muc['nguoi_phe_duyet'],
           'han_danh_gia_ngay': muc['thoi_han_danh_gia_ngay'],
           'tai_lieu_cap_nhat': [f'{b["buoc"]} ({b["ten"]})' for b in tl if b['da_tao'] and not (b['khoa'] and KY_HD)],
           'tai_lieu_khoa': [f'{b["buoc"]} ({b["ten"]})' for b in tl if b['khoa'] and KY_HD],
           'phu_luc_hop_dong': muc['ma'] == 'lon',
           'trang_thai': 'Chờ phê duyệt', 'lich_su': [{'ngay': cr.get('ngay', loi.bay_gio()[:10]), 'ghi_luc': loi.bay_gio(), 'trang_thai': 'Chờ phê duyệt', 'nguoi': cr.get('nguoi_de_xuat', ''), 'ghi_chu': 'Lập và đánh giá tác động'}]}
    so['yeu_cau'].append(rec)
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{ma}.danh_gia', 'script', f'Đánh giá {ma}: {rec["tieu_de"]}', vao=[a.doi_tuong], ra=['du_lieu/thay_doi.json'],
                    ket_qua=rec['muc_ten'], chi_tiet={k: rec[k] for k in ('md_tang', 'chi_phi_tang', 'ngay_cham', 'ngay_cham_cut_over')})
    print(f'{ma}: tăng {md_tang:g} MD, {loi.tien(chi_phi)} đồng, chậm ước tính {cham} ngày ({cham_cut_over} ngày sau khi trừ dự trữ đến cut over). '
          f'Mức {muc["ten"]}, phê duyệt: {muc["nguoi_phe_duyet"]}, đánh giá trong {muc["thoi_han_danh_gia_ngay"]} ngày làm việc.')
    print('Tài liệu phải cập nhật nếu phê duyệt: ' + '; '.join(rec['tai_lieu_cap_nhat']))
    if rec['tai_lieu_khoa']:
        print('Không sửa (đường cơ sở đấu thầu): ' + '; '.join(rec['tai_lieu_khoa']) + ('. Cần phụ lục hợp đồng.' if rec['phu_luc_hop_dong'] else '. Ghi nhận trong biên bản thỏa thuận.'))
    sys.exit(0)

cr = next((c for c in so['yeu_cau'] if c['ma'] == a.doi_tuong), None)
if not cr:
    loi.thoat_loi('Không có yêu cầu thay đổi ' + str(a.doi_tuong))
if a.lenh == 'quyet_dinh':
    if a.ket_qua not in ('Đã phê duyệt', 'Từ chối', 'Hoãn'):
        loi.thoat_loi('--ket-qua phải là Đã phê duyệt, Từ chối hoặc Hoãn')
    cr['trang_thai'] = a.ket_qua; cr['nguoi_quyet_dinh'] = a.nguoi; cr['ngay_quyet_dinh'] = NGAY
    cr['dem_phien_ban_khi_quyet_dinh'] = loi.doc_json('du_lieu/phien_ban.json', {}).get('dem', 0)
    if NGAY < cr['ngay_de_xuat']:
        loi.thoat_loi(f'Ngày quyết định {NGAY} trước ngày đề xuất {cr["ngay_de_xuat"]}, dùng --ngay theo lịch dự án')
    cr['lich_su'].append({'ngay': NGAY, 'ghi_luc': loi.bay_gio(), 'trang_thai': a.ket_qua, 'nguoi': a.nguoi, 'ghi_chu': a.ghi_chu})
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{cr["ma"]}.quyet_dinh', 'nguoi_dung', f'{a.ket_qua} {cr["ma"]}: {a.ghi_chu}', ra=['du_lieu/thay_doi.json'], ket_qua=a.ket_qua)
    print(f'{cr["ma"]}: {a.ket_qua}.')
    if a.ket_qua == 'Đã phê duyệt':
        print('Thực hiện: sửa dữ liệu nguồn (lam_viec/wbs/wbs_nhap.json, giao việc), chạy lại theo thứ tự: ' + '; '.join(cr['tai_lieu_cap_nhat'])
              + f'. Ghi --ghi-chu "{cr["ma"]}" khi hoàn thiện từng tài liệu, rồi đóng yêu cầu.')
    sys.exit(0)
if a.lenh == 'dong':
    # Chỉ đóng khi mọi tài liệu phải cập nhật đã được tạo lại với đầu vào mới, ghi phiên bản sau thay đổi
    if cr['trang_thai'] not in ('Đã phê duyệt', 'Đã thực hiện'):
        loi.thoat_loi(f'{cr["ma"]} đang ở trạng thái {cr["trang_thai"]}, chỉ đóng CR đã phê duyệt')
    t_qd = next((x.get('ghi_luc', x['ngay']) for x in reversed(cr['lich_su']) if x['trang_thai'] == 'Đã phê duyệt'), '')
    sd = loi.so_do(); reg = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})['tai_lieu']
    bd = loi.nut_bien_dong(sd); cu, chua, pb_sau = [], [], {}
    for s_ in cr.get('tai_lieu_cap_nhat', []):
        b = next((x for x in sd['buoc'] if x['id'] == s_.split(' ')[0]), None)
        if not b:
            continue
        ds_tep = []
        for q in b['ra'].values():
            ds_tep += [k for k in reg if k.startswith(q.rstrip('/') + '/')] if os.path.isdir(loi.duong_dan(q)) else [q]
        for p in ds_tep:
            lst = reg.get(p, [])
            if not lst:
                continue
            pb_sau[p] = lst[-1]['phien_ban']
            dem_qd = cr.get('dem_phien_ban_khi_quyet_dinh')
            if (max(lst[-1].get('thu_tu', 0), lst[-1].get('thu_tu_kiem_tra', 0)) <= dem_qd) if dem_qd is not None else \
                    (max(lst[-1]['ngay'], lst[-1].get('ngay_kiem_tra', '')) <= t_qd):
                chua.append(f'{b["id"]} ({p})')
            if any(loi.bam_nut(sd, n) != h for n, h in lst[-1].get('vao', {}).items() if n in b['vao'] and n not in bd and loi.duong_dan_nut(sd, n)):
                cu.append(f'{b["id"]} ({p})')
    if (cu or chua) and not a.bo_qua_kiem_tra:
        loi.thoat_loi('Chưa đóng được CR. ' + ('Tài liệu còn dùng đầu vào cũ: ' + ', '.join(sorted(set(cu))) + '. ' if cu else '') +
                      ('Tài liệu chưa được tạo lại sau quyết định phê duyệt: ' + ', '.join(sorted(set(chua))) + '. ' if chua else '') +
                      'Chạy lại các bước này (chay.py trang_thai) hoặc dùng --bo-qua-kiem-tra kèm lý do trong --ghi-chu.')
    cr['phien_ban_sau'] = pb_sau
    cr['trang_thai'] = 'Đã đóng'; cr['ngay_dong'] = NGAY; cr['lich_su'].append({'ngay': NGAY, 'ghi_luc': loi.bay_gio(), 'trang_thai': 'Đã đóng', 'nguoi': a.nguoi, 'ghi_chu': a.ghi_chu})
    loi.ghi_json('du_lieu/thay_doi.json', so)
    loi.ghi_nhat_ky('qlda-change', f'thay_doi.{cr["ma"]}.dong', 'script', f'Đóng {cr["ma"]}: {a.ghi_chu}', ra=['du_lieu/thay_doi.json'])
    print(f'{cr["ma"]}: Đã đóng.')
    sys.exit(0)
loi.thoat_loi('Lệnh không hợp lệ')
