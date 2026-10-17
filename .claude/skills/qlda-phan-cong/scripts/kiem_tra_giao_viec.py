"""Kiểm tra và chuẩn hóa bảng giao việc (bước giao_viec).

Dùng: python kiem_tra_giao_viec.py <phan_cong_nhap.json>
Kiểm tra: mọi gói lá có một người thực hiện (R); người hỗ trợ hợp lệ; loại công việc phù hợp năng lực người nhận;
mỗi mục mức 1, mức 2 có đúng một người chịu trách nhiệm cuối (A); C, I là thành viên hoặc bên ngoài đã khai báo;
tổng MD giao mỗi người không vượt quỹ thời gian; vị trí nhân sự chủ chốt khớp Bảng số 02 của HSMT.
Đạt thì ghi du_lieu/phan_cong.json, đăng ký phiên bản, ghi nhật ký. Mã thoát 0 đạt, 1 còn lỗi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

src = sys.argv[1]
pc = json.load(open(src, encoding='utf-8'))
wbs = loi.doc_json('du_lieu/wbs.json')
hsmt = loi.doc_json('du_lieu/hsmt.json')
tvs = loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']
tv = {t['id']: t for t in tvs}
ngoai = {b['id']: b for b in pc.get('ben_ngoai', [])}
sprints = loi.danh_sach_sprint()
by, la = loi.nut_wbs(wbs)
F = []
add = lambda ma, mo, vt='', md='loi': F.append({'ma': ma, 'muc_do': md, 'nhom': 'phan_cong', 'vi_tri': vt, 'mo_ta': mo, 'cach_sua': 'can_nguoi_dung', 'de_xuat': ''})
for t in tvs:
    if t.get('_can_xac_nhan'):
        F.append({'ma': 'P22', 'muc_do': 'canh_bao', 'vi_tri': t['id'], 'mo_ta': f'Vị trí {t["ho_ten"]} ({t.get("chuc_danh", "")}) chưa xác nhận nhân sự, HSDT sẽ không lập được cho đến khi có họ tên thật'})

gv = {}
for x in pc.get('giao_viec', []):
    if x['ma'] in gv:
        add('P01', 'Gói được giao hai lần', x['ma'])
    gv[x['ma']] = x
for g in la:
    x = gv.get(g['ma'])
    if not x:
        add('P02', 'Gói lá chưa có người thực hiện (R)', g['ma']); continue
    if x.get('R') not in tv:
        add('P03', f'Người thực hiện {x.get("R")} không có trong thanh_vien.json', g['ma']); continue
    for h in x.get('ho_tro', []):
        if h not in tv:
            add('P04', f'Người hỗ trợ {h} không có trong thanh_vien.json', g['ma'])
    for p in [x['R']] + x.get('ho_tro', []):
        if p in tv and g.get('loai') not in tv[p].get('loai_cong_viec', []) and not x.get('ly_do'):
            add('P05', f'{tv[p]["ho_ten"]} được giao loại {g.get("loai")} ngoài năng lực khai báo {tv[p].get("loai_cong_viec")}, cần ghi ly_do', g['ma'], 'canh_bao')
for m in gv:
    if m not in {g['ma'] for g in la}:
        add('P06', 'Mã giao việc không phải gói lá trong WBS', m)

tn = {x['ma']: x for x in pc.get('trach_nhiem', [])}
for g in wbs['goi']:
    if g['muc'] <= 2 and not g['la']:
        x = tn.get(g['ma'])
        if not x or not x.get('A'):
            add('P10', 'Mục chưa có người chịu trách nhiệm cuối (A)', g['ma']); continue
        if x['A'] not in tv:
            add('P11', f'Người chịu trách nhiệm {x["A"]} không phải thành viên', g['ma'])
        for k in ('C', 'I'):
            for i in x.get(k, []):
                if i not in tv and i not in ngoai:
                    add('P12', f'{k} = {i} không phải thành viên hoặc bên ngoài đã khai báo', g['ma'])

# tải công việc theo quỹ thời gian
quy = {t['id']: loi.quy_thoi_gian(t, sprints) for t in tvs}
md_giao = {t['id']: 0.0 for t in tvs}
md_loai = {t['id']: {} for t in tvs}
for g in la:
    x = gv.get(g['ma'])
    if not x or x.get('R') not in tv:
        continue
    ng = [x['R']] + [h for h in x.get('ho_tro', []) if h in tv]
    tong_tl = sum(float(tv[p].get('ty_le', 1)) for p in ng)
    for p in ng:
        v = float(g['md']) * float(tv[p].get('ty_le', 1)) / tong_tl
        md_giao[p] += v
        md_loai[p][g['loai']] = md_loai[p].get(g['loai'], 0) + v
tai = []
for t in tvs:
    q = sum(quy[t['id']].values())
    u = md_giao[t['id']] / q if q else 0
    if md_giao[t['id']] > q + 1e-6:
        add('P20', f'{t["ho_ten"]}: giao {md_giao[t["id"]]:.2f} MD vượt quỹ {q:.2f} MD', t['id'])
    elif u > 0.95:
        add('P21', f'{t["ho_ten"]}: sử dụng {u:.0%} quỹ thời gian, ít dư địa xử lý phát sinh', t['id'], 'canh_bao')
    tai.append({'id': t['id'], 'ho_ten': t['ho_ten'], 'loai': t['loai'], 'chuc_danh': t.get('chuc_danh', ''), 'md_giao': round(md_giao[t['id']], 2),
                'quy': round(q, 2), 'ty_le_su_dung': round(u, 4), 'theo_loai': {k: round(v, 2) for k, v in md_loai[t['id']].items()}})

# nhân sự chủ chốt theo HSMT
cc = {x['stt']: x for x in pc.get('vi_tri_chu_chot', [])}
for y in hsmt.get('nhan_su_chu_chot', []):
    x = cc.get(y['stt'])
    n = len(x.get('thanh_vien', [])) if x else 0
    if n < y['so_luong']:
        add('P30', f'Vị trí chủ chốt {y["vi_tri"]} cần {y["so_luong"]} người, mới đề xuất {n}', str(y['stt']))
    for i in (x or {}).get('thanh_vien', []):
        if i not in tv:
            add('P31', f'Nhân sự chủ chốt {i} không có trong thanh_vien.json', str(y['stt']))

loi_ = [f for f in F if f['muc_do'] == 'loi']
loi.ghi_json('lam_viec/giao_viec/bao_cao_kiem_tra.json', {'ket_luan': 'dat' if not loi_ else 'chua_dat', 'so_loi': len(loi_), 'so_canh_bao': len(F) - len(loi_), 'phat_hien': F})
for f in F:
    print(f"[{f['muc_do']}] {f['ma']} {f['vi_tri']}: {f['mo_ta']}")
tong_q = sum(x['quy'] for x in tai); tong_g = sum(x['md_giao'] for x in tai)
print(f'Giao {tong_g:.2f} MD trên quỹ {tong_q:.2f} MD. Kết luận: {"dat" if not loi_ else "chua_dat"} ({len(loi_)} lỗi, {len(F) - len(loi_)} cảnh báo)')
if loi_:
    sys.exit(1)
out = {'giao_viec': [dict(gv[g['ma']], ten=g['ten'], md=g['md'], loai=g['loai']) for g in la],
       'trach_nhiem': [dict(tn[g['ma']], ten=g['ten'], muc=g['muc']) for g in wbs['goi'] if g['ma'] in tn],
       'ben_ngoai': pc.get('ben_ngoai', []), 'vi_tri_chu_chot': [dict(cc.get(y['stt'], {}), vi_tri=y['vi_tri'], so_luong=y['so_luong'],
       ho_ten=', '.join(tv[i]['ho_ten'] for i in cc.get(y['stt'], {}).get('thanh_vien', []) if i in tv)) for y in hsmt.get('nhan_su_chu_chot', [])],
       'tai': tai, 'tong_md_giao': round(tong_g, 2), 'tong_quy': round(tong_q, 2), 'du_quy': round(tong_q - tong_g, 2)}
loi.ghi_json('du_lieu/phan_cong.json', out)
loi.hoan_tat_buoc('giao_viec', f'Kiểm tra và chuẩn hóa giao việc: {tong_g:.2f} MD trên quỹ {tong_q:.2f} MD')
print('Đã ghi du_lieu/phan_cong.json')
