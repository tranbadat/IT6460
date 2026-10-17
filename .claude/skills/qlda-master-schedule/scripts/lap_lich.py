"""Lập master schedule có ràng buộc nguồn lực từ WBS, giao việc và lịch làm việc.

Dùng: python lap_lich.py [lam_viec/lich/moc_nhap.json]
Đầu vào: du_lieu/wbs.json, du_lieu/phan_cong.json, dau_vao/thanh_vien.json, dau_vao/du_an.json, du_lieu/hsmt.json,
         lam_viec/lich/moc_nhap.json (agent Lập mốc viết: mốc, mục tiêu và sản phẩm demo của từng sprint).
Cách tính:
- Thời lượng gói = làm tròn lên (MD / tổng tỷ lệ tham gia của người thực hiện và người hỗ trợ) ngày làm việc.
- Mỗi người làm lần lượt từng gói. Gói có người hỗ trợ được chia phần theo thời gian khả dụng, mỗi người làm phần của mình độc lập.
  Phần việc bắt đầu khi các gói phụ thuộc đã xong, người đó đã tham gia dự án và đang rảnh. Gói hoàn thành khi mọi phần xong.
  Thứ tự ưu tiên: gói có thời điểm bắt đầu muộn nhất (theo CPM) sớm hơn. Phần việc được chèn vào khoảng trống sớm nhất của người làm.
- Đường găng tính theo phụ thuộc (CPM, không xét nguồn lực), kèm thời gian dự trữ của từng gói.
- Gói dàn trải (giao_viec: dan_trai = true, tu_sprint, den_sprint): khối lượng chia đều trong cửa sổ, chiếm một phần thời gian mỗi ngày
  của người thực hiện. Thời gian còn lại mỗi ngày dùng cho các gói khác.
- Mốc: ngày cố định hoặc ngày hoàn thành của các gói nêu trong sau_goi. Kiểm tra hạn của mốc.
- Ràng buộc không sớm hơn (moc_nhap.json, khóa khong_som_hon {mã gói: yyyy-mm-dd}): gói chỉ bắt đầu từ ngày đó, dùng cho
  công việc gắn ngày cố định như chuyển dữ liệu và hỗ trợ ngày đưa vào vận hành. Dự trữ đến cut over khi đó đo đến ngày bắt đầu
  của gói bị ghim (khoảng chậm cho phép của các gói phía trước).
Ra: du_lieu/lich.json. Lỗi khi lịch vượt ngày cut over, mốc trễ hạn, sprint thiếu mục tiêu. Mã thoát 0 đạt, 1 còn lỗi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import datetime as dt
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

moc_path = sys.argv[1] if len(sys.argv) > 1 else 'lam_viec/lich/moc_nhap.json'
wbs = loi.doc_json('du_lieu/wbs.json')
pc = loi.doc_json('du_lieu/phan_cong.json')
tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']
da = loi.du_an()
hsmt = loi.doc_json('du_lieu/hsmt.json')
if len(sys.argv) > 1 and not os.path.exists(loi.duong_dan(moc_path)):
    loi.thoat_loi(f'Không tìm thấy tệp mốc {moc_path}')
CHI_NGUON_LUC = not os.path.exists(loi.duong_dan(moc_path))
if CHI_NGUON_LUC:
    print(f'Chưa có {moc_path}: chỉ kiểm tra lịch theo nguồn lực (dùng khi giao việc), không ghi du_lieu/lich.json.')
moc_nhap = {} if CHI_NGUON_LUC else loi.doc_json(moc_path)
tv = {t['id']: t for t in tvs}
days = loi.ngay_lam_viec(da)
N = len(days)
sprints = loi.danh_sach_sprint(da)
by, la = loi.nut_wbs(wbs)
gv = {x['ma']: x for x in pc['giao_viec']}
F = []
add = lambda ma, mo, vt='', md='loi': F.append({'ma': ma, 'muc_do': md, 'nhom': 'lich', 'vi_tri': vt, 'mo_ta': mo, 'cach_sua': 'can_nguoi_dung', 'de_xuat': ''})

# ngày làm việc mở rộng sau cut over (để thấy mức vượt nếu có)
ext = list(days)
d = days[-1]
nghi = {dt.date.fromisoformat(x) for x in da.get('ngay_nghi', [])}
while len(ext) < N * 3:
    d += dt.timedelta(days=1)
    if d.weekday() < 5 and d not in nghi:
        ext.append(d)


def bat_dau_tham_gia(p):
    t = tv[p]
    if t.get('tu_sprint') in (None, ''):
        return 0
    s = next((s for s in sprints if s['so'] == int(t['tu_sprint'])), None)
    return s['chi_so_dau'] if s else N


def ket_thuc_tham_gia(p):
    t = tv[p]
    if t.get('den_sprint') in (None, ''):
        return len(ext) - 1
    s = next((s for s in sprints if s['so'] == int(t['den_sprint'])), None)
    return s['chi_so_cuoi'] if s else len(ext) - 1


def cua_so_sprint(x, p):
    """Cửa sổ (chỉ số ngày đầu, cuối) của gói dàn trải: theo tu_sprint, den_sprint của gói, giới hạn trong thời gian tham gia."""
    a = bat_dau_tham_gia(p); b = min(N - 1, ket_thuc_tham_gia(p))
    if x.get('tu_sprint'):
        s = next(s for s in sprints if s['so'] == int(x['tu_sprint'])); a = max(a, s['chi_so_dau'])
    if x.get('den_sprint'):
        s = next(s for s in sprints if s['so'] == int(x['den_sprint'])); b = min(b, s['chi_so_cuoi'])
    return a, b


# gói dàn trải (level of effort): chiếm một phần thời gian mỗi ngày trong cửa sổ, không chặn người thực hiện
loe_md = {p: 0.0 for p in tv}
for g in la:
    x = gv[g['ma']]
    if x.get('dan_trai'):
        ng = [x['R']] + x.get('ho_tro', [])
        for p in ng:
            loe_md[p] += float(g['md']) / len(ng)
du = {}
for p in tv:
    a, b = bat_dau_tham_gia(p), min(N - 1, ket_thuc_tham_gia(p))
    so = max(1, b - a + 1)
    du[p] = float(tv[p].get('ty_le', 1)) - loe_md[p] / so
    if du[p] < 0.2:
        add('L04', f'{tv[p]["ho_ten"]}: việc dàn trải chiếm {loe_md[p]:.1f} MD, chỉ còn {max(du[p], 0):.0%} thời gian mỗi ngày cho gói khác', p,
            'loi' if du[p] <= 0 else 'canh_bao')
    du[p] = max(du[p], 0.05)

task = {}
for g in la:
    x = gv[g['ma']]
    ng = [x['R']] + x.get('ho_tro', [])
    t = {'ma': g['ma'], 'ten': g['ten'], 'md': float(g['md']), 'nguoi': ng, 'R': x['R'], 'dep': [p for p in g.get('phu_thuoc', []) if p in by],
         'loe': bool(x.get('dan_trai'))}
    if t['loe']:
        a, b = cua_so_sprint(x, x['R'])
        t.update({'cua_so': (a, b), 'dur': b - a + 1, 'rate': t['md'] / (b - a + 1)})
    else:
        t['rate'] = sum(du[p] for p in ng)
        t['dur'] = max(1, math.ceil(t['md'] / t['rate'] - 1e-9))
    task[g['ma']] = t


# ràng buộc không sớm hơn: chỉ số ngày làm việc đầu tiên từ ngày khai báo
ghim = {}
for ma_g, ngay_g in (moc_nhap.get('khong_som_hon') or {}).items():
    if ma_g not in task or task[ma_g]['loe']:
        add('L15', f'Ràng buộc không sớm hơn dẫn chiếu gói {ma_g} không phải gói lá thường', ma_g); continue
    d_g = dt.date.fromisoformat(ngay_g)
    ghim[ma_g] = next((i for i, x in enumerate(ext) if x >= d_g), len(ext) - 1)

# CPM theo phụ thuộc
succ = {m: [] for m in task}
for m, t in task.items():
    for p in t['dep']:
        succ[p].append(m)
order, seen = [], set()


def topo(u):
    if u in seen:
        return
    seen.add(u)
    for p in task[u]['dep']:
        topo(p)
    order.append(u)


for m in sorted(task, key=loi.khoa_ma):
    topo(m)
es, ef = {}, {}
for m in order:
    if task[m]['loe']:
        es[m], ef[m] = task[m]['cua_so']; continue
    es[m] = max([ef[p] + 1 for p in task[m]['dep'] if not task[p]['loe']], default=0)  # đường găng theo phụ thuộc, không xét ngày ghim
    ef[m] = es[m] + task[m]['dur'] - 1
proj = max([ef[m] for m in task if not task[m]['loe']] or [0])
lf, ls = {}, {}
for m in reversed(order):
    if task[m]['loe']:
        lf[m], ls[m] = ef[m], es[m]; continue
    lf[m] = min([ls[s] - 1 for s in succ[m] if not task[s]['loe']], default=proj)
    ls[m] = lf[m] - task[m]['dur'] + 1
tail = {}
for m in reversed(order):
    tail[m] = (0 if task[m]['loe'] else task[m]['dur']) + max([tail[s] for s in succ[m]], default=0)

# lập lịch có ràng buộc nguồn lực
free = {p: bat_dau_tham_gia(p) for p in tv}
start, finish = {}, {}
for m, t in task.items():
    if t['loe']:
        start[m], finish[m] = t['cua_so']
con = {m for m in task if not task[m]['loe']}
phan = {}  # (gói, người) -> (bắt đầu, kết thúc, MD): mỗi người làm phần việc của mình độc lập
ban = {p: [] for p in tv}  # khoảng bận của từng người


def khe_som_nhat(p, lb, d):
    """Ngày bắt đầu sớm nhất >= lb sao cho người p rảnh d ngày liên tục (cho phép chèn vào khoảng trống)."""
    t = max(lb, free[p])
    for x, y in sorted(ban[p]):
        if t + d - 1 < x:
            break
        if y >= t:
            t = y + 1
    return t


while con:
    ready = [m for m in con if all(p in finish for p in task[m]['dep'])]
    if not ready:
        loi.thoat_loi('Không lập được lịch: vòng phụ thuộc hoặc phụ thuộc thiếu')

    def dep_fin(m):
        return max([finish[p] + 1 for p in task[m]['dep']] + [ghim.get(m, 0)])
    m = min(ready, key=lambda m: (ls[m], dep_fin(m), -tail[m], loi.khoa_ma(m)))
    t = task[m]
    s0, f0 = None, None
    for p in t['nguoi']:
        md_p = t['md'] * du[p] / t['rate']
        d_p = max(1, math.ceil(md_p / du[p] - 1e-9))
        a = khe_som_nhat(p, dep_fin(m), d_p); b = a + d_p - 1
        phan[(m, p)] = (a, b, md_p)
        ban[p].append((a, b))
        s0 = a if s0 is None else min(s0, a); f0 = b if f0 is None else max(f0, b)
        if b > ket_thuc_tham_gia(p):
            add('L05', f'{tv[p]["ho_ten"]} được giao gói kết thúc sau thời gian tham gia dự án', m)
    start[m], finish[m] = s0, f0
    con.discard(m)

# gói dàn trải luôn kéo đến hết cửa sổ sprint nên không dùng để đo ngày kết thúc và dự trữ
ket_thuc = max([finish[m] for m in task if not task[m]['loe']] or list(finish.values()))
if ket_thuc > N - 1:
    tre = [m for m in task if finish[m] > N - 1]
    add('L01', f'Lịch có ràng buộc nguồn lực kết thúc {loi.ngay(ext[ket_thuc])}, sau ngày cut over {loi.ngay(days[-1])} '
               f'{ket_thuc - (N - 1)} ngày làm việc. Gói vượt: {", ".join(sorted(tre, key=loi.khoa_ma)[:12])}', '', 'loi')
du_tru = (N - 1) - ket_thuc
if ghim:
    sau_ghim, hang = set(ghim), list(ghim)  # gói bị ghim và các gói đứng sau chúng
    while hang:
        for s_ in succ[hang.pop()]:
            if s_ not in sau_ghim:
                sau_ghim.add(s_); hang.append(s_)
    tu_do = [finish[m] for m in task if not task[m]['loe'] and m not in sau_ghim]
    ung = [(N - 1) - max(tu_do)] if tu_do else []
    for m_g, i_g in ghim.items():  # khoảng chậm cho phép của các gói không ghim đứng ngay trước gói ghim
        truoc = [finish[p] + 1 for p in task[m_g]['dep'] if p not in sau_ghim]
        if truoc:
            ung.append(i_g - max(truoc))
    du_tru = min(ung + ([du_tru] if du_tru < 0 else []))
for m_g, i_g in ghim.items():
    if start[m_g] > i_g:
        add('L16', f'Gói {m_g} bắt đầu {loi.ngay(ext[start[m_g]])}, muộn hơn ngày ghim {loi.ngay(ext[i_g])} do gói trước chưa xong', m_g)


def sp_cua(i):
    return loi.sprint_cua_chi_so(sprints, i) or f'{da.get("sprint", {}).get("tien_to", "S")}+'


# phân bổ MD theo người, sprint
phan_bo = {}
for m, t in task.items():
    for p in t['nguoi']:
        if t['loe']:
            a, b, md_p = start[m], finish[m], t['md'] / len(t['nguoi'])
        else:
            a, b, md_p = phan[(m, p)]
        for i in range(a, b + 1):
            s_ = sp_cua(i)
            phan_bo[(p, s_)] = phan_bo.get((p, s_), 0) + md_p / (b - a + 1)
quy = {t['id']: loi.quy_thoi_gian(t, sprints) for t in tvs}
khoa_pb = [(t['id'], s['ma']) for t in tvs for s in sprints]
pb_tron = dict(zip(khoa_pb, loi.lam_tron_tong([phan_bo.get(k, 0) for k in khoa_pb])))  # tổng các ô bằng tổng MD
pb_rows = []
for t in tvs:
    for s in sprints:
        md_ = pb_tron[(t['id'], s['ma'])]
        q = quy[t['id']][s['ma']]
        pb_rows.append({'thanh_vien': t['id'], 'ho_ten': t['ho_ten'], 'sprint': s['ma'], 'md': md_, 'quy': q, 'ty_le': round(md_ / q, 4) if q else 0})
        if md_ > q + 0.01:
            add('L06', f'{t["ho_ten"]} quá tải ở {s["ma"]}: {md_:.2f}/{q:.2f} MD', s['ma'])

# mốc
moc = []
for x in moc_nhap.get('moc', []):
    if x.get('ngay'):
        ngay_moc = dt.date.fromisoformat(x['ngay'])
    elif x.get('sau_goi'):
        thieu = [g for g in x['sau_goi'] if g not in finish and g not in by]
        if thieu:
            add('L10', f'Mốc {x["ma"]} dẫn chiếu gói không có: {thieu}', x['ma']); continue
        leaves = []
        for g in x['sau_goi']:
            leaves += [m for m in task if m == g or m.startswith(g + '.')]
        ngay_moc = ext[max(finish[m] for m in leaves)]
    else:
        add('L11', f'Mốc {x["ma"]} thiếu ngày hoặc sau_goi', x['ma']); continue
    han = dt.date.fromisoformat(x['han']) if x.get('han') else None
    trang_thai = 'Đúng hạn' if not han or ngay_moc <= han else 'Trễ hạn'
    if han and ngay_moc > han:
        add('L12', f'Mốc {x["ma"]} ({x["ten"]}) dự kiến {loi.ngay(ngay_moc)}, trễ hạn {loi.ngay(han)}', x['ma'])
    moc.append({'ma': x['ma'], 'ten': x['ten'], 'ngay': ngay_moc.isoformat(), 'han': han.isoformat() if han else '', 'trang_thai': trang_thai,
                'can_cu': ', '.join(x.get('sau_goi', [])) or 'Ngày cố định', 'dot_thanh_toan': x.get('dot_thanh_toan', ''),
                'sprint': sp_cua(days.index(ngay_moc)) if ngay_moc in days else ''})
co_cut_over = any(m['ngay'] == hsmt['lich']['cut_over_iso'] or 'cut over' in m['ten'].lower() for m in moc)
if not co_cut_over:
    add('L13', 'Chưa có mốc cut over theo HSMT', '', 'canh_bao' if CHI_NGUON_LUC else 'loi')
for m1, m2 in zip(moc, moc[1:]):
    if m2['ngay'] < m1['ngay']:
        add('L14', f'Mốc {m2["ma"]} ({loi.ngay(m2["ngay"])}) sớm hơn mốc trước {m1["ma"]} ({loi.ngay(m1["ngay"])}), xem lại sau_goi hoặc thứ tự mốc',
            m2['ma'], 'canh_bao')

# sprint
mt = {x['sprint']: x for x in moc_nhap.get('muc_tieu_sprint', [])}
sp_rows = []
for s in sprints:
    x = mt.get(s['ma'])
    if not x or not x.get('muc_tieu'):
        add('L20', f'Sprint {s["ma"]} chưa có mục tiêu', s['ma'], 'canh_bao' if CHI_NGUON_LUC else 'loi')
    if not x or not x.get('san_pham_demo'):
        add('L21', f'Sprint {s["ma"]} chưa có sản phẩm trình diễn cuối sprint', s['ma'], 'canh_bao')
    md_ = round(sum(v for (p, sp), v in phan_bo.items() if sp == s['ma']), 2)
    q = round(sum(quy[p][s['ma']] for p in quy), 2)
    sp_rows.append(dict(s, muc_tieu=(x or {}).get('muc_tieu', ''), san_pham_demo=(x or {}).get('san_pham_demo', ''), md_ke_hoach=md_, quy=q,
                        ty_le_su_dung=round(md_ / q, 4) if q else 0, goi_hoan_thanh=sorted([m for m in task if sp_cua(finish[m]) == s['ma']], key=loi.khoa_ma)))

goi_out = []
for g in wbs['goi']:
    ms = [g['ma']] if g['la'] else [m for m in task if m.startswith(g['ma'] + '.')]
    if not ms:
        continue
    s_, f_ = min(start[m] for m in ms), max(finish[m] for m in ms)
    r = {'ma': g['ma'], 'ten': g['ten'], 'muc': g['muc'], 'la': g['la'], 'md': g['md'], 'bat_dau': ext[s_].isoformat(), 'ket_thuc': ext[f_].isoformat(),
         'so_ngay': len([i for i in range(s_, f_ + 1)]), 'sprint_bat_dau': sp_cua(s_), 'sprint_ket_thuc': sp_cua(f_), 'cha': g.get('cha', '')}
    if g['la']:
        t = task[g['ma']]
        md_nguoi = [t['md'] / len(t['nguoi']) if t['loe'] else phan[(g['ma'], p)][2] for p in t['nguoi']]
        r['phan_nguoi'] = dict(zip(t['nguoi'], loi.lam_tron_tong(md_nguoi)))  # MD từng người trong gói, dùng chung cho tài liệu phân công
        r.update({'nguoi': t['nguoi'], 'R': t['R'], 'ho_ten_R': tv[t['R']]['ho_ten'], 'phu_thuoc': t['dep'], 'thoi_luong': t['dur'],
                  'du_tru_cpm': ls[g['ma']] - es[g['ma']], 'gang': (ls[g['ma']] == es[g['ma']]) and not t['loe'], 'dan_trai': t['loe'], 'chi_so_bat_dau': start[g['ma']], 'chi_so_ket_thuc': finish[g['ma']]})
    goi_out.append(r)

gang = [m for m in order if ls[m] == es[m] and not task[m]['loe']]
loi_ = [f for f in F if f['muc_do'] == 'loi']
out = {'ngay_bat_dau': days[0].isoformat(), 'cut_over': days[-1].isoformat(), 'so_ngay_lam_viec': N, 'ngay_nghi': da.get('ngay_nghi', []),
       'sprint': sp_rows, 'goi': goi_out, 'moc': moc, 'phan_bo': pb_rows, 'duong_gang': gang, 'do_dai_gang_ngay': proj + 1,
       'ket_thuc_du_kien': ext[ket_thuc].isoformat(), 'du_tru_den_cut_over_ngay': du_tru, 'khong_som_hon': moc_nhap.get('khong_som_hon', {}),
       'tong_md': wbs['tong_md'], 'tong_quy': round(sum(sum(q.values()) for q in quy.values()), 2), 'so_sprint': len(sprints),
       'kiem_tra': {'ket_luan': 'dat' if not loi_ else 'chua_dat', 'so_loi': len(loi_), 'so_canh_bao': len(F) - len(loi_), 'phat_hien': F}}
loi.ghi_json('lam_viec/lich/bao_cao_kiem_tra.json', out['kiem_tra'])
loi.ghi_json('lam_viec/lich/lich_du_thao.json', out)  # luôn ghi để agent chẩn đoán khi chưa đạt
for f in F:
    print(f"[{f['muc_do']}] {f['ma']} {f['vi_tri']}: {f['mo_ta']}")
print(f'{len(sprints)} sprint, {N} ngày làm việc. Kết thúc dự kiến {loi.ngay(ext[ket_thuc])}, dự trữ đến cut over {du_tru} ngày. '
      f'Đường găng {proj + 1} ngày. Kết luận: {out["kiem_tra"]["ket_luan"]} ({len(loi_)} lỗi, {len(F) - len(loi_)} cảnh báo)')
if loi_:
    print('Đường găng theo phụ thuộc: ' + ' -> '.join(f'{m}({task[m]["dur"]})' for m in sorted(gang, key=lambda m: es[m])))
    tai = sorted(((x['ho_ten'], round(sum(y['md'] for y in pb_rows if y['thanh_vien'] == x['thanh_vien']), 1)) for x in pb_rows if x['sprint'] == sprints[0]['ma']), key=lambda z: -z[1])
    print('Bản dự thảo: lam_viec/lich/lich_du_thao.json (xem bat_dau, ket_thuc, nguoi của từng gói để điều chỉnh giao việc, phụ thuộc)')
    sys.exit(1)
if CHI_NGUON_LUC:
    print('Lịch khả thi theo nguồn lực. Lập mốc (prompts/vai_lap_moc.md) rồi chạy lại với tệp mốc để ghi du_lieu/lich.json.')
    sys.exit(0)
loi.ghi_json('du_lieu/lich.json', out)
print('Đã ghi du_lieu/lich.json. Tiếp theo: python .claude/skills/qlda-master-schedule/scripts/xuat_gantt.py')
