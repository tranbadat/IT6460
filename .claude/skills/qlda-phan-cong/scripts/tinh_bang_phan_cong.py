"""Tính các bảng của tài liệu phân công: ma trận RACI, giao việc theo người, tải theo sprint.

Dùng: python tinh_bang_phan_cong.py      (chay.py chuan_bi phan_cong_tai_lieu tự gọi)
Ra: du_lieu/phan_cong_bang.json (bảng tính sẵn cho đặc tả, khóa raci, tai_sprint, theo_nguoi).
RACI có cột Phê duyệt bên ngoài lấy từ trach_nhiem[].phe_duyet (ví dụ Chủ đầu tư xác nhận đặc tả, kiểm thử vận hành, nghiệm thu).
Tải theo sprint có dòng tổng, MD theo người cộng đúng tổng WBS (loi.khop_tong khi chỉ lệch do làm tròn). Lịch có giai đoạn Kết thúc thì thêm
cột kỳ KT (MD sau cut over, không có quỹ huy động nên ghi MD). Lịch lập lại (lap_lai_tu) thì ghi ngày lập lại để câu dẫn nêu sprint trước
ngày này là MD thực tế.
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

pc = loi.doc_json('du_lieu/phan_cong.json'); lich = loi.doc_json('du_lieu/lich.json'); wbs = loi.doc_json('du_lieu/wbs.json')
tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']
ids = [t['id'] for t in tvs]
ty_le = {t['id']: t.get('ty_le', 1) for t in tvs}
ten_ngan = {t['id']: (t['ho_ten'].split()[-1] if t['loai'] == 'nhom' else t['ho_ten']) for t in tvs}
by, la = loi.nut_wbs(wbs)
gv = {x['ma']: x for x in pc['giao_viec']}
tn = {x['ma']: x for x in pc['trach_nhiem']}
ngoai = pc.get('ben_ngoai', [])
ten_ngoai = lambda b: b.get('ten_ngan') or b['ten'].split(' (')[0]

# RACI: mức 1, mức 2. R = người thực hiện các gói con, A = người chịu trách nhiệm cuối, C, I theo khai báo
raci_rows, dam = [], []
for g in wbs['goi']:
    if g['muc'] > 2 or g['la'] and g['muc'] > 1:
        if not (g['la'] and g['muc'] == 2):
            continue
    leaves = [g] if g['la'] else [x for x in la if x['ma'].startswith(g['ma'] + '.')]
    R = {gv[x['ma']]['R'] for x in leaves if x['ma'] in gv} | {h for x in leaves if x['ma'] in gv for h in gv[x['ma']].get('ho_tro', [])}
    t = tn.get(g['ma']) or ({'A': gv[g['ma']]['R']} if g['la'] and g['ma'] in gv else {})
    row = [g['ma'], g['ten']]
    for p in ids:
        s = ''.join(k for k, ok in (('A', t.get('A') == p), ('R', p in R), ('C', p in t.get('C', [])), ('I', p in t.get('I', []))) if ok)
        row.append(s)
    vai_ngoai = lambda b: ', '.join(k for k in ('C', 'I') if b['id'] in t.get(k, []))
    row.append(', '.join(f'{ten_ngoai(b)} ({vai_ngoai(b)})' for b in ngoai if vai_ngoai(b)))
    row.append(', '.join(ten_ngoai(b) for b in ngoai if b['id'] in t.get('phe_duyet', [])))  # bên ngoài phê duyệt (Chủ đầu tư)
    raci_rows.append(row)
    if g['muc'] == 1:
        dam.append(len(raci_rows))
raci = {'cot': ['Mã', 'Hạng mục'] + [ten_ngan[p] for p in ids] + ['Bên ngoài', 'Phê duyệt bên ngoài'], 'dong': raci_rows,
        'widths': [700, 3000] + [800] * len(ids) + [1300, 1200], 'center_cols': list(range(2, 2 + len(ids))), 'dong_dam': dam}

sp = [s['ma'] for s in lich['sprint']] + sorted({r['sprint'] for r in lich['phan_bo']} - {s['ma'] for s in lich['sprint']})  # kỳ KT sau cut over
pbm = {(r['thanh_vien'], r['sprint']): r for r in lich['phan_bo']}
giao_tho = [sum(r['md'] for r in lich['phan_bo'] if r['thanh_vien'] == t['id']) for t in tvs]  # khớp master schedule
giao_khop = loi.khop_tong(giao_tho, wbs['tong_md'])  # tổng theo người bằng tổng WBS khi chỉ lệch do làm tròn
if giao_khop is None:
    print(f'CẢNH BÁO: MD theo người trong lịch cộng {loi.md(sum(giao_tho))}, khác tổng WBS {loi.md(wbs["tong_md"])}')
giao_lich = dict(zip([t['id'] for t in tvs], giao_khop or [round(v, 2) for v in giao_tho]))
quy_nguoi = {y['id']: y['quy'] for y in pc['tai']}
tai_rows = []
for t in tvs:
    row = [t['ho_ten']]
    for s in sp:
        r = pbm.get((t['id'], s))
        row.append(f'{loi.md(r["md"])}/{loi.md(r["quy"])}' if r and r['quy'] else (loi.md(r['md']) if r and r['md'] else '-'))
    q = quy_nguoi[t['id']]
    row += [loi.md(giao_lich[t['id']]), loi.md(q), loi.pt(giao_lich[t['id']] / q if q else 0)]
    tai_rows.append(row)
tong_sp = [(sum(r['md'] for r in lich['phan_bo'] if r['sprint'] == s), sum(r['quy'] for r in lich['phan_bo'] if r['sprint'] == s)) for s in sp]
tong_giao, tong_quy = sum(giao_lich.values()), sum(quy_nguoi.values())
tai_rows.append(['Tổng cộng'] + [f'{loi.md(round(m, 2))}/{loi.md(round(q, 2))}' if q else loi.md(round(m, 2)) for m, q in tong_sp]
                + [loi.md(round(tong_giao, 2)), loi.md(round(tong_quy, 2)), loi.pt(tong_giao / tong_quy if tong_quy else 0)])
W_SP = min(950, (13400 - 2200 - 2700) // max(1, len(sp)))  # khổ ngang: thu hẹp cột sprint khi có thêm kỳ KT
tai = {'cot': ['Thành viên'] + sp + ['Giao, MD', 'Quỹ, MD', 'Sử dụng'], 'dong': tai_rows, 'widths': [2200] + [W_SP] * len(sp) + [900, 900, 900],
       'center_cols': list(range(1, 1 + len(sp))), 'right_cols': [len(sp) + 1, len(sp) + 2, len(sp) + 3]}

lich_goi = {x['ma']: x for x in lich['goi']}
theo_nguoi = []
for t in tvs:
    goi = [x for x in pc['giao_viec'] if x['R'] == t['id'] or t['id'] in x.get('ho_tro', [])]
    for x in sorted(goi, key=lambda x: loi.khoa_ma(x['ma'])):
        lg = lich_goi.get(x['ma'], {})
        ng = [x['R']] + x.get('ho_tro', [])
        chia = dict(zip(ng, loi.chia_md(x['md'], [ty_le.get(p, 1) for p in ng])))  # dự phòng khi lịch chưa có phan_nguoi
        phan = lg.get('phan_nguoi', {}).get(t['id'], chia.get(t['id'], 0))
        theo_nguoi.append({'ho_ten': t['ho_ten'], 'ma': x['ma'], 'ten': x['ten'], 'md': x['md'], 'md_nguoi': phan, 'vai': 'Thực hiện' if x['R'] == t['id'] else 'Hỗ trợ',
                           'thoi_gian': f'{loi.ngay(lg.get("bat_dau"))} - {loi.ngay(lg.get("ket_thuc"))}' if lg else '', 'sprint': lg.get('sprint_bat_dau', '')})
LAP_LAI = lich.get('lap_lai_tu') or {}
_sp_tt = [s['ma'] for s in lich['sprint'] if LAP_LAI.get('ngay') and s['den'] < LAP_LAI['ngay']]
_kt = [x for x in sp if x not in {s['ma'] for s in lich['sprint']}]
chu_thich_tai = ('Mỗi ô ghi MD trên quỹ thời gian của thành viên trong sprint theo master schedule'
                 + (f'. Lịch được lập lại từ ngày {loi.ngay(LAP_LAI["ngay"])}, các sprint {", ".join(_sp_tt)} ghi MD thực tế đã làm (có thể vượt quỹ do '
                    'làm thêm trong sprint đã qua), các sprint sau ghi MD kế hoạch' if _sp_tt else ', là MD kế hoạch')
                 + ((f'. Cột {", ".join(_kt)} là giai đoạn Kết thúc sau cut over, ghi MD trên quỹ theo tỷ lệ huy động giai đoạn Kết thúc của thành viên '
                     'trong bảng huy động, thành viên không huy động giai đoạn này chỉ ghi MD'
                     if any(t.get('huy_dong_ket_thuc') for t in tvs) else
                     f'. Cột {", ".join(_kt)} là MD của giai đoạn Kết thúc sau cut over, chưa có quỹ huy động nên chỉ ghi MD') if _kt else '')
                 + '. Cột Giao bằng tổng các ô của thành viên, dòng cuối là tổng của các thành viên.')
# người hỗ trợ trên đường găng và quỹ chưa giao trong thời gian huy động (không tính MD giai đoạn Kết thúc ngoài quỹ)
_gv = {x['ma']: x for x in pc.get('giao_viec', [])}
_gang = [m for m in lich.get('duong_gang', []) if m in _gv]
_gang_ht = [m for m in _gang if _gv[m].get('ho_tro')]
# quỹ chưa giao = tổng phần quỹ còn trống max(0, quỹ - MD) của từng người từng sprint, không bù phần làm vượt quỹ, không gồm kỳ KT (từ 1.3.4)
_sp_ma = [s_['ma'] for s_ in lich['sprint']]
_md_ns = {}
for x in lich.get('phan_bo', []):
    _md_ns[(x['thanh_vien'], x['sprint'])] = _md_ns.get((x['thanh_vien'], x['sprint']), 0) + x['md']
_quy_ns = {t['id']: loi.quy_thoi_gian(t, lich['sprint']) for t in tvs}
_chua_giao = sum(max(0.0, _quy_ns[p].get(s_, 0) - _md_ns.get((p, s_), 0)) for p in _quy_ns for s_ in _sp_ma)
ho_tro_tom_tat = {'so_goi_gang': len(_gang), 'goi_gang_co_ho_tro': ', '.join(_gang_ht), 'so_goi_gang_co_ho_tro': len(_gang_ht),
                  'so_goi_co_ho_tro': sum(1 for x in pc.get('giao_viec', []) if x.get('ho_tro')),
                  'quy_chua_giao_huy_dong': round(_chua_giao, 2)}
loi.ghi_json('du_lieu/phan_cong_bang.json', {'raci': raci, 'tai_sprint': tai, 'theo_nguoi': theo_nguoi, 'ho_tro_tom_tat': ho_tro_tom_tat,
                                              'ngay_lap_lai': loi.ngay(LAP_LAI.get('ngay')) if LAP_LAI.get('ngay') else '',
                                              'sprint_thuc_te': ', '.join(s['ma'] for s in lich['sprint'] if LAP_LAI.get('ngay') and s['den'] < LAP_LAI['ngay']),
                                              'co_ky_kt': bool(_kt), 'chu_thich_tai': chu_thich_tai,
                                              'chu_giai_ten': [{'ten_ngan': ten_ngan[p], 'ho_ten': next(t['ho_ten'] for t in tvs if t['id'] == p)} for p in ids]
                                              + [{'ten_ngan': ten_ngoai(b), 'ho_ten': b['ten']} for b in ngoai],
                                              'thanh_vien': [dict(t, loai_ten='Thành viên nhóm' if t['loai'] == 'nhom' else 'Vị trí bổ sung',
                                                                  loai_cong_viec_ten=', '.join(t.get('loai_cong_viec', []))) for t in tvs]})
print(f'Đã tính bảng phân công: RACI {len(raci_rows)} dòng, {len(theo_nguoi)} dòng giao việc theo người')
