"""Tính các bảng của tài liệu phân công: ma trận RACI, giao việc theo người, tải theo sprint.

Dùng: python tinh_bang_phan_cong.py      (chay.py chuan_bi phan_cong_tai_lieu tự gọi)
Ra: du_lieu/phan_cong_bang.json (bảng tính sẵn cho đặc tả, khóa raci, tai_sprint, theo_nguoi).
RACI có cột Phê duyệt bên ngoài lấy từ trach_nhiem[].phe_duyet (ví dụ Chủ đầu tư xác nhận đặc tả, kiểm thử vận hành, nghiệm thu).
Tải theo sprint có dòng tổng, MD theo người cộng đúng tổng WBS (loi.khop_tong khi chỉ lệch do làm tròn).
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

sp = [s['ma'] for s in lich['sprint']]
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
        row.append(f'{loi.md(r["md"])}/{loi.md(r["quy"])}' if r and r['quy'] else '-')
    q = quy_nguoi[t['id']]
    row += [loi.md(giao_lich[t['id']]), loi.md(q), loi.pt(giao_lich[t['id']] / q if q else 0)]
    tai_rows.append(row)
tong_sp = [(sum(r['md'] for r in lich['phan_bo'] if r['sprint'] == s), sum(r['quy'] for r in lich['phan_bo'] if r['sprint'] == s)) for s in sp]
tong_giao, tong_quy = sum(giao_lich.values()), sum(quy_nguoi.values())
tai_rows.append(['Tổng cộng'] + [f'{loi.md(round(m, 2))}/{loi.md(round(q, 2))}' for m, q in tong_sp]
                + [loi.md(round(tong_giao, 2)), loi.md(round(tong_quy, 2)), loi.pt(tong_giao / tong_quy if tong_quy else 0)])
tai = {'cot': ['Thành viên'] + sp + ['Giao, MD', 'Quỹ, MD', 'Sử dụng'], 'dong': tai_rows, 'widths': [2200] + [950] * len(sp) + [900, 900, 900],
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
loi.ghi_json('du_lieu/phan_cong_bang.json', {'raci': raci, 'tai_sprint': tai, 'theo_nguoi': theo_nguoi,
                                              'chu_giai_ten': [{'ten_ngan': ten_ngan[p], 'ho_ten': next(t['ho_ten'] for t in tvs if t['id'] == p)} for p in ids]
                                              + [{'ten_ngan': ten_ngoai(b), 'ho_ten': b['ten']} for b in ngoai],
                                              'thanh_vien': [dict(t, loai_ten='Thành viên nhóm' if t['loai'] == 'nhom' else 'Vị trí bổ sung',
                                                                  loai_cong_viec_ten=', '.join(t.get('loai_cong_viec', []))) for t in tvs]})
print(f'Đã tính bảng phân công: RACI {len(raci_rows)} dòng, {len(theo_nguoi)} dòng giao việc theo người')
