"""Lập master schedule có ràng buộc nguồn lực từ WBS, giao việc và lịch làm việc.

Dùng: python lap_lich.py [lam_viec/lich/moc_nhap.json]
Đầu vào: du_lieu/wbs.json, du_lieu/phan_cong.json, dau_vao/thanh_vien.json, dau_vao/du_an.json, du_lieu/hsmt.json,
         lam_viec/lich/moc_nhap.json (agent Lập mốc viết: mốc, mục tiêu và sản phẩm demo của từng sprint).
Cách tính:
- Thời lượng gói = giá trị lớn hơn giữa làm tròn lên (MD / tổng tỷ lệ tham gia của người thực hiện và người hỗ trợ) và thời lượng
  tối thiểu (ngày làm việc). Thời lượng tối thiểu lấy từ thoi_luong_toi_thieu của gói lá trong WBS và từ moc_nhap.json khóa
  chu_dau_tu_tham_gia [{goi, loai}]: loai phe_duyet lấy du_an.thoi_gian_phe_duyet_tai_lieu_ngay, loai uat ghim gói vào khoảng
  du_an.uat {tu, den} (không sớm hơn tu, thời lượng bằng số ngày làm việc của khoảng, lỗi L23 khi kết thúc sau den).
  Người làm chỉ bận số ngày cần cho phần MD của mình (tính từ ngày bắt đầu gói), thời gian còn lại của thời lượng tối thiểu
  là thời gian Chủ đầu tư xem xét, kiểm thử. Gói sau chỉ bắt đầu khi gói hết thời lượng tối thiểu.
- Mỗi người làm lần lượt từng gói. Gói có người hỗ trợ được chia phần theo thời gian khả dụng, mỗi người làm phần của mình độc lập.
  Phần việc bắt đầu khi các gói phụ thuộc đã xong, người đó đã tham gia dự án và đang rảnh. Gói hoàn thành khi mọi phần xong.
  Thứ tự ưu tiên: gói có thời điểm bắt đầu muộn nhất (theo CPM) sớm hơn. Phần việc được chèn vào khoảng trống sớm nhất của người làm.
- Đường găng tính theo phụ thuộc (CPM, không xét nguồn lực), kèm thời gian dự trữ của từng gói.
- Gói dàn trải (giao_viec: dan_trai = true, tu_sprint, den_sprint): khối lượng chia đều trong cửa sổ, chiếm một phần thời gian mỗi ngày
  của người thực hiện. Thời gian còn lại mỗi ngày dùng cho các gói khác.
- Mốc: ngày cố định hoặc ngày hoàn thành của các gói nêu trong sau_goi. Kiểm tra hạn của mốc.
- Ràng buộc không sớm hơn (moc_nhap.json, khóa khong_som_hon {mã gói: yyyy-mm-dd}): gói chỉ bắt đầu từ ngày đó, dùng cho
  công việc gắn ngày cố định như chuyển dữ liệu và hỗ trợ ngày đưa vào vận hành. Dự trữ đến cut over khi đó đo đến ngày bắt đầu
  của gói bị ghim (khoảng chậm cho phép của các gói phía trước). Gói kiểm thử chấp nhận ghim theo khoảng uat cũng tính như vậy.
- Phụ thuộc bên ngoài (moc_nhap.json, khóa dau_vao_ben_ngoai {mã cam kết: [mã gói hoặc mục cha]}): gói không bắt đầu trước hạn
  của cam kết trong du_an.cam_ket_chu_dau_tu. Lỗi L17 khi gói bắt đầu trước hạn, cảnh báo L18 khi cam kết có hạn chưa ánh xạ gói.
  Ràng buộc này không dùng để đo dự trữ đến cut over.
- Sử dụng quỹ: cảnh báo L07 khi một người được huy động trong sprint nhưng dùng dưới NGUONG_SU_DUNG_NGUOI_SPRINT quỹ của sprint,
  L08 khi tỷ lệ sử dụng quỹ toàn dự án thấp hơn du_an.nguong_su_dung_quy_toi_thieu (bước hsdt dừng ở ngưỡng này).
Ra: du_lieu/lich.json (thêm ty_le_su_dung_quy, nhu_cau_theo_sprint, su_dung_theo_nguoi_sprint, cam_ket_chu_dau_tu,
chu_dau_tu_tham_gia, rang_buoc của gói lá). Lỗi khi lịch vượt ngày cut over, mốc trễ hạn, sprint thiếu mục tiêu.
Mã thoát 0 đạt, 1 còn lỗi.
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
_thieu_gv = [g['ma'] for g in la if g['ma'] not in gv]
if _thieu_gv:
    loi.thoat_loi(f'Gói lá chưa có trong du_lieu/phan_cong.json (chạy lại bước giao_viec sau khi đổi WBS): {", ".join(_thieu_gv[:12])}')
NGUONG_SU_DUNG_NGUOI_SPRINT = 0.3  # người huy động trong sprint dùng dưới tỷ lệ này của quỹ sprint thì cảnh báo L07
LOAI_CHU_DAU_TU = ('phe_duyet', 'uat')
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


def chi_so_tu(d):
    """Chỉ số ngày làm việc đầu tiên không sớm hơn ngày d (yyyy-mm-dd hoặc date)."""
    d = dt.date.fromisoformat(d) if isinstance(d, str) else d
    return next((i for i, x in enumerate(ext) if x >= d), len(ext) - 1)


def chi_so_den(d):
    """Chỉ số ngày làm việc cuối cùng không muộn hơn ngày d."""
    d = dt.date.fromisoformat(d) if isinstance(d, str) else d
    return max((i for i, x in enumerate(ext) if x <= d), default=0)


def la_cua(ma):
    """Mã các gói lá thuộc mã ma (chính nó nếu là gói lá)."""
    return [g['ma'] for g in la if g['ma'] == ma or g['ma'].startswith(str(ma) + '.')]


# ràng buộc từ Chủ đầu tư: thời lượng tối thiểu (WBS, phê duyệt tài liệu, kiểm thử chấp nhận) và hạn cam kết đầu vào
tmin = {g['ma']: int(g['thoi_luong_toi_thieu']) for g in la if g.get('thoi_luong_toi_thieu')}
rb_goi = {m: [{'loai': 'thoi_luong_toi_thieu', 'so_ngay': n}] for m, n in tmin.items()}  # ràng buộc ngày của từng gói lá, ghi vào lich.json
ghim_uat = {}  # gói kiểm thử chấp nhận: (chỉ số ngày đầu, cuối) của khoảng uat
cdt_vao = []
for x in moc_nhap.get('chu_dau_tu_tham_gia') or []:
    m, loai_ = str(x.get('goi', '')), x.get('loai')
    if m not in {g['ma'] for g in la} or loai_ not in LOAI_CHU_DAU_TU:
        add('L24', f'chu_dau_tu_tham_gia: {m} không phải gói lá trong WBS hoặc loại {loai_} không thuộc {list(LOAI_CHU_DAU_TU)}', m); continue
    if loai_ == 'phe_duyet':
        n = da.get('thoi_gian_phe_duyet_tai_lieu_ngay')
        if not n:
            add('L24', 'du_an.json chưa có thoi_gian_phe_duyet_tai_lieu_ngay, đề nghị nhóm bổ sung', m); continue
        rb = {'loai': 'phe_duyet', 'so_ngay': int(n)}
    else:
        uat = da.get('uat') or {}
        if not (uat.get('tu') and uat.get('den')):
            add('L24', 'du_an.json chưa có uat {tu, den}, đề nghị nhóm bổ sung', m); continue
        a_, b_ = chi_so_tu(uat['tu']), chi_so_den(uat['den'])
        ghim_uat[m] = (a_, b_)
        rb = {'loai': 'uat', 'so_ngay': b_ - a_ + 1, 'tu': uat['tu'], 'den': uat['den']}
    tmin[m] = max(tmin.get(m, 0), rb['so_ngay'])
    rb_goi.setdefault(m, []).append(rb)
    cdt_vao.append(dict(rb, goi=m))
CAM_KET = {c['ma']: c for c in da.get('cam_ket_chu_dau_tu', [])}
anh_xa_ck = moc_nhap.get('dau_vao_ben_ngoai') or {}
ghim_ben_ngoai, ck_goi = {}, {}  # gói -> chỉ số ngày hạn cam kết muộn nhất; mã cam kết -> gói lá
for ma_ck, ds_goi in anh_xa_ck.items():
    if ma_ck not in CAM_KET:
        add('L19', f'dau_vao_ben_ngoai dẫn chiếu cam kết {ma_ck} không có trong du_an.cam_ket_chu_dau_tu', ma_ck); continue
    for ma_g in ds_goi:
        if not la_cua(ma_g):
            add('L19', f'dau_vao_ben_ngoai {ma_ck}: gói {ma_g} không có trong WBS', ma_g)
        for m in la_cua(ma_g):
            ck_goi.setdefault(ma_ck, []).append(m)
            if CAM_KET[ma_ck].get('han'):
                ghim_ben_ngoai[m] = max(ghim_ben_ngoai.get(m, 0), chi_so_tu(CAM_KET[ma_ck]['han']))
            rb_goi.setdefault(m, []).append({'loai': 'cam_ket', 'ma': ma_ck, 'han': CAM_KET[ma_ck].get('han')})
if not CHI_NGUON_LUC:
    for c in CAM_KET.values():
        if c.get('han') and not ck_goi.get(c['ma']):
            add('L18', f'Cam kết {c["ma"]} ({c["noi_dung"]}) hạn {loi.ngay(c["han"])} chưa ánh xạ gói nào trong dau_vao_ben_ngoai', c['ma'], 'canh_bao')
    for loai_, co in (('phe_duyet', da.get('thoi_gian_phe_duyet_tai_lieu_ngay')), ('uat', (da.get('uat') or {}).get('tu'))):
        if co and not any(x['loai'] == loai_ for x in cdt_vao):
            add('L22', f'du_an.json có tham số {loai_} nhưng chu_dau_tu_tham_gia chưa gắn gói nào loại {loai_}', loai_, 'canh_bao')


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
         'loe': bool(x.get('dan_trai')), 'loai': g.get('loai', ''), 'tmin': tmin.get(g['ma'], 0)}
    if t['loe']:
        a, b = cua_so_sprint(x, x['R'])
        t.update({'cua_so': (a, b), 'dur': b - a + 1, 'rate': t['md'] / (b - a + 1)})
        if t['tmin']:
            add('L24', f'Gói dàn trải {g["ma"]} không áp dụng thời lượng tối thiểu, thời lượng theo cửa sổ sprint', g['ma'])
    else:
        t['rate'] = sum(du[p] for p in ng)
        t['dur_md'] = max(1, math.ceil(t['md'] / t['rate'] - 1e-9))
        t['dur'] = max(t['dur_md'], t['tmin'])
    task[g['ma']] = t


# ràng buộc không sớm hơn: chỉ số ngày làm việc đầu tiên từ ngày khai báo
ghim_co_dinh = {}  # gói phải bắt đầu đúng ngày (khong_som_hon, khoảng uat): lỗi L16 khi muộn hơn, dùng để đo dự trữ đến cut over
for ma_g, ngay_g in (moc_nhap.get('khong_som_hon') or {}).items():
    if ma_g not in task or task[ma_g]['loe']:
        add('L15', f'Ràng buộc không sớm hơn dẫn chiếu gói {ma_g} không phải gói lá thường', ma_g); continue
    ghim_co_dinh[ma_g] = chi_so_tu(ngay_g)
    rb_goi.setdefault(ma_g, []).append({'loai': 'khong_som_hon', 'ngay': ngay_g})
for m, (a_, _) in ghim_uat.items():
    ghim_co_dinh[m] = max(ghim_co_dinh.get(m, 0), a_)
ghim = {m: max(ghim_co_dinh.get(m, 0), ghim_ben_ngoai.get(m, 0)) for m in set(ghim_co_dinh) | set(ghim_ben_ngoai)}

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
    start[m], finish[m] = s0, max(f0, s0 + t['tmin'] - 1)  # gói kéo dài đủ thời lượng tối thiểu, người làm chỉ bận phần MD của mình
    con.discard(m)

# gói dàn trải luôn kéo đến hết cửa sổ sprint nên không dùng để đo ngày kết thúc và dự trữ
ket_thuc = max([finish[m] for m in task if not task[m]['loe']] or list(finish.values()))
if ket_thuc > N - 1:
    tre = [m for m in task if finish[m] > N - 1]
    add('L01', f'Lịch có ràng buộc nguồn lực kết thúc {loi.ngay(ext[ket_thuc])}, sau ngày cut over {loi.ngay(days[-1])} '
               f'{ket_thuc - (N - 1)} ngày làm việc. Gói vượt: {", ".join(sorted(tre, key=loi.khoa_ma)[:12])}', '', 'loi')
du_tru = (N - 1) - ket_thuc
if ghim_co_dinh:
    sau_ghim, hang = set(ghim_co_dinh), list(ghim_co_dinh)  # gói bị ghim và các gói đứng sau chúng
    while hang:
        for s_ in succ[hang.pop()]:
            if s_ not in sau_ghim:
                sau_ghim.add(s_); hang.append(s_)
    tu_do = [finish[m] for m in task if not task[m]['loe'] and m not in sau_ghim]
    ung = [(N - 1) - max(tu_do)] if tu_do else []
    for m_g, i_g in ghim_co_dinh.items():  # khoảng chậm cho phép của các gói không ghim đứng ngay trước gói ghim
        truoc = [finish[p] + 1 for p in task[m_g]['dep'] if p not in sau_ghim]
        if truoc:
            ung.append(i_g - max(truoc))
    du_tru = min(ung + ([du_tru] if du_tru < 0 else []))
for m_g, i_g in ghim_co_dinh.items():
    if start[m_g] > i_g:
        add('L16', f'Gói {m_g} bắt đầu {loi.ngay(ext[start[m_g]])}, muộn hơn ngày ghim {loi.ngay(ext[i_g])} do gói trước chưa xong', m_g)
for m_g, (_, i_den) in ghim_uat.items():
    if finish[m_g] > i_den:
        add('L23', f'Gói kiểm thử chấp nhận {m_g} kết thúc {loi.ngay(ext[finish[m_g]])}, sau khoảng UAT đến {loi.ngay(ext[i_den])}', m_g)
for m_g, i_h in ghim_ben_ngoai.items():
    if start[m_g] < i_h:
        ck_ = ', '.join(c for c, ds in ck_goi.items() if m_g in ds and CAM_KET[c].get('han'))
        add('L17', f'Gói {m_g} bắt đầu {loi.ngay(ext[start[m_g]])}, trước hạn cam kết {ck_} của Chủ đầu tư ({loi.ngay(ext[i_h])})', m_g)


def sp_cua(i):
    return loi.sprint_cua_chi_so(sprints, i) or f'{da.get("sprint", {}).get("tien_to", "S")}+'


# phân bổ MD theo người, sprint và theo loại công việc, sprint
phan_bo, nhu_cau = {}, {}
for m, t in task.items():
    for p in t['nguoi']:
        if t['loe']:
            a, b, md_p = start[m], finish[m], t['md'] / len(t['nguoi'])
        else:
            a, b, md_p = phan[(m, p)]
        for i in range(a, b + 1):
            s_ = sp_cua(i)
            phan_bo[(p, s_)] = phan_bo.get((p, s_), 0) + md_p / (b - a + 1)
            nhu_cau[(t['loai'], s_)] = nhu_cau.get((t['loai'], s_), 0) + md_p / (b - a + 1)
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
        elif q and md_ < NGUONG_SU_DUNG_NGUOI_SPRINT * q - 1e-9:
            add('L07', f'{t["ho_ten"]} được huy động ở {s["ma"]} nhưng chỉ dùng {md_:.2f}/{q:.2f} MD ({md_ / q:.0%}), dưới {NGUONG_SU_DUNG_NGUOI_SPRINT:.0%} quỹ sprint',
                f'{t["id"]} {s["ma"]}', 'canh_bao')


def su_dung_theo_nguoi():
    """MD, quỹ, tỷ lệ sử dụng của từng người theo sprint và cả dự án, các sprint dùng dưới ngưỡng."""
    out_ = []
    for t in tvs:
        rows_t = [r for r in pb_rows if r['thanh_vien'] == t['id']]
        md_t, q_t = round(sum(r['md'] for r in rows_t), 2), round(sum(r['quy'] for r in rows_t), 2)
        out_.append({'thanh_vien': t['id'], 'ho_ten': t['ho_ten'], 'md': md_t, 'quy': q_t, 'ty_le': round(md_t / q_t, 4) if q_t else 0,
                     'sprint': {r['sprint']: {'md': r['md'], 'quy': r['quy'], 'ty_le': r['ty_le']} for r in rows_t},
                     'sprint_duoi_nguong': [r['sprint'] for r in rows_t if r['quy'] and r['md'] < NGUONG_SU_DUNG_NGUOI_SPRINT * r['quy'] - 1e-9]})
    return out_


def nhu_cau_sprint():
    """MD theo loại công việc và sprint (làm tròn để tổng các ô bằng tổng MD), dùng để đề xuất huy động theo sprint."""
    loai_ds = sorted({t['loai'] for t in task.values()})
    khoa = [(lo, s['ma']) for s in sprints for lo in loai_ds]
    tron = dict(zip(khoa, loi.lam_tron_tong([nhu_cau.get(k, 0) for k in khoa])))
    return [{'sprint': s['ma'], 'theo_loai': {lo: tron[(lo, s['ma'])] for lo in loai_ds}, 'md': round(sum(tron[(lo, s['ma'])] for lo in loai_ds), 2)}
            for s in sprints]


tong_quy = round(sum(sum(q.values()) for q in quy.values()), 2)
ty_le_su_dung_quy = round(float(wbs['tong_md']) / tong_quy, 4) if tong_quy else 0
nguong_quy = da.get('nguong_su_dung_quy_toi_thieu')
if nguong_quy is not None and ty_le_su_dung_quy < float(nguong_quy):
    add('L08', f'Tỷ lệ sử dụng quỹ huy động {ty_le_su_dung_quy:.1%} thấp hơn ngưỡng {float(nguong_quy):.0%} của du_an.json, bước hsdt sẽ dừng. '
               f'Xem su_dung_theo_nguoi_sprint và nhu_cau_theo_sprint để đề xuất huy động sát nhu cầu', '', 'canh_bao')

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
        if t['tmin'] and not t['loe']:
            r.update({'thoi_luong_toi_thieu': t['tmin'], 'thoi_luong_theo_md': t['dur_md']})
        if rb_goi.get(g['ma']):
            r['rang_buoc'] = rb_goi[g['ma']]
    goi_out.append(r)

# cam kết của Chủ đầu tư và gói có Chủ đầu tư tham gia, dùng cho HSDT, master plan, rủi ro
ck_out = []
for c in CAM_KET.values():
    ds = sorted(set(ck_goi.get(c['ma'], [])), key=loi.khoa_ma)
    bd = min((start[m] for m in ds), default=None)
    ck_out.append({'ma': c['ma'], 'noi_dung': c.get('noi_dung', ''), 'han': c.get('han'), 'goi': ds, 'bat_dau_som_nhat': ext[bd].isoformat() if bd is not None else '',
                   'dat': (bd is None or not c.get('han') or ext[bd].isoformat() >= c['han'])})
cdt_out = [dict(x, bat_dau=ext[start[x['goi']]].isoformat(), ket_thuc=ext[finish[x['goi']]].isoformat(),
                so_ngay_lich=finish[x['goi']] - start[x['goi']] + 1) for x in cdt_vao if x['goi'] in start]  # so_ngay: thời lượng tối thiểu

gang = [m for m in order if ls[m] == es[m] and not task[m]['loe']]
loi_ = [f for f in F if f['muc_do'] == 'loi']
out = {'ngay_bat_dau': days[0].isoformat(), 'cut_over': days[-1].isoformat(), 'so_ngay_lam_viec': N, 'ngay_nghi': da.get('ngay_nghi', []),
       'sprint': sp_rows, 'goi': goi_out, 'moc': moc, 'phan_bo': pb_rows, 'duong_gang': gang, 'do_dai_gang_ngay': proj + 1,
       'ket_thuc_du_kien': ext[ket_thuc].isoformat(), 'du_tru_den_cut_over_ngay': du_tru, 'khong_som_hon': moc_nhap.get('khong_som_hon', {}),
       'tong_md': wbs['tong_md'], 'tong_quy': tong_quy, 'so_sprint': len(sprints),
       'ty_le_su_dung_quy': ty_le_su_dung_quy, 'nguong_su_dung_quy_toi_thieu': nguong_quy, 'nguong_su_dung_nguoi_sprint': NGUONG_SU_DUNG_NGUOI_SPRINT,
       'nhu_cau_theo_sprint': nhu_cau_sprint(), 'su_dung_theo_nguoi_sprint': su_dung_theo_nguoi(),
       'cam_ket_chu_dau_tu': ck_out, 'chu_dau_tu_tham_gia': cdt_out,
       'kiem_tra': {'ket_luan': 'dat' if not loi_ else 'chua_dat', 'so_loi': len(loi_), 'so_canh_bao': len(F) - len(loi_), 'phat_hien': F}}
loi.ghi_json('lam_viec/lich/bao_cao_kiem_tra.json', out['kiem_tra'])
loi.ghi_json('lam_viec/lich/lich_du_thao.json', out)  # luôn ghi để agent chẩn đoán khi chưa đạt
for f in F:
    print(f"[{f['muc_do']}] {f['ma']} {f['vi_tri']}: {f['mo_ta']}")
print(f'{len(sprints)} sprint, {N} ngày làm việc. Kết thúc dự kiến {loi.ngay(ext[ket_thuc])}, dự trữ đến cut over {du_tru} ngày. '
      f'Đường găng {proj + 1} ngày. Tỷ lệ sử dụng quỹ {ty_le_su_dung_quy:.1%}. '
      f'Kết luận: {out["kiem_tra"]["ket_luan"]} ({len(loi_)} lỗi, {len(F) - len(loi_)} cảnh báo)')
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
