"""Sổ phiên bản và đường cơ sở của bộ tài liệu dự án.

Dùng:
  python so_phien_ban.py tong_hop
      Tổng hợp sổ phiên bản (du_lieu/phien_ban.json), nhật ký chạy, sổ thay đổi, lịch sử git (nếu thư mục là kho git)
      thành du_lieu/phien_ban_tong_hop.json và ket_qua/15_Quan_ly_phien_ban/So_phien_ban.xlsx.
  python so_phien_ban.py trang_thai <tệp> --trang-thai "Đã kiểm tra|Đã duyệt" --nguoi "<họ tên>" [--ghi-chu ...]
      Cập nhật trạng thái phiên bản hiện hành của một tài liệu (sau kiểm tra lớp B, sau phê duyệt).
  python so_phien_ban.py duong_co_so <mã, ví dụ BL1> --ten "<tên đường cơ sở>" [--tep <tệp> ...] [--ngay yyyy-mm-dd] [--ghi-chu ...] [--hop-dong] [--bo-qua-kiem-tra]
      --hop-dong: đường cơ sở khi ký hợp đồng, HSMT và HSDT chuyển trạng thái Khóa, sau đó không tạo lại.
      Lập đường cơ sở: mỗi tài liệu được chọn (mặc định mọi tài liệu trong ket_qua) lên số chính kế tiếp (1.0, 2.0),
      trạng thái Đường cơ sở. Không lập được nếu tài liệu còn dùng đầu vào cũ.
Quy ước: references/quy_uoc.json.
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
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('lenh', nargs='?', default='tong_hop'); ap.add_argument('doi_tuong', nargs='?')
ap.add_argument('--trang-thai'); ap.add_argument('--nguoi', default=''); ap.add_argument('--ghi-chu', default='')
ap.add_argument('--ten', default=''); ap.add_argument('--tep', nargs='*'); ap.add_argument('--ngay'); ap.add_argument('--bo-qua-kiem-tra', action='store_true')
ap.add_argument('--hop-dong', action='store_true', help='đường cơ sở khi ký hợp đồng: khóa HSMT, HSDT')
a = ap.parse_args()
sd = loi.so_do(); BD = loi.nut_bien_dong(sd)
reg = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})
reg.setdefault('duong_co_so', [])
QU = loi.doc_json(os.path.join(HERE, '..', 'references', 'quy_uoc.json'))
buoc = {b['id']: b for b in sd['buoc']}


def cu(rec):
    vao_hien = buoc.get(rec.get('buoc'), {}).get('vao', list(rec.get('vao', {})))
    return sorted(n for n, h in rec.get('vao', {}).items()
                  if n in vao_hien and n not in BD and loi.duong_dan_nut(sd, n) and loi.bam_nut(sd, n) != h)


def tai_lieu_nop():
    return [p for p in reg['tai_lieu'] if p.startswith('ket_qua/') and os.path.exists(loi.duong_dan(p))]


if a.lenh == 'trang_thai':
    p = loi.tuong_doi(loi.duong_dan(a.doi_tuong or ''))
    if p not in reg['tai_lieu']:
        loi.thoat_loi(f'{p} chưa có trong sổ phiên bản')
    hop_le = [x['ma'] for x in QU['trang_thai'] if x['ma'] not in ('Đường cơ sở', 'Khóa')]
    if a.trang_thai not in hop_le:
        loi.thoat_loi('Trạng thái phải là một trong: ' + ', '.join(hop_le) + '. Đường cơ sở dùng lệnh duong_co_so.')
    rec = reg['tai_lieu'][p][-1]
    if cu(rec):
        loi.thoat_loi(f'{p} đang dùng đầu vào cũ ({", ".join(cu(rec))}), tạo lại trước khi cập nhật trạng thái.')
    rec.setdefault('lich_su_trang_thai', []).append({'tu': rec['trang_thai'], 'den': a.trang_thai, 'nguoi': a.nguoi, 'luc': loi.bay_gio(), 'ghi_chu': a.ghi_chu})
    rec['trang_thai'] = a.trang_thai
    loi.ghi_json('du_lieu/phien_ban.json', reg)
    loi.ghi_nhat_ky('qlda-phien-ban', 'phien_ban.trang_thai', 'script', f'{p} {rec["phien_ban"]}: {a.trang_thai} ({a.nguoi})', ra=['du_lieu/phien_ban.json'])
    print(f'{p} phiên bản {rec["phien_ban"]}: {a.trang_thai}')
    sys.exit(0)

if a.lenh == 'duong_co_so':
    ma = a.doi_tuong
    if not ma or any(x['ma'] == ma for x in reg['duong_co_so']):
        loi.thoat_loi('Cần mã đường cơ sở mới, chưa dùng (ví dụ BL1, BL2)')
    ds = [loi.tuong_doi(loi.duong_dan(t)) for t in a.tep] if a.tep else tai_lieu_nop()
    ds = [p for p in ds if not p.startswith(('ket_qua/15_', 'ket_qua/16_'))]
    loi_ = [f'{p}: chưa đăng ký' for p in ds if p not in reg['tai_lieu']]
    khoa = lambda p: reg.get('hop_dong') and buoc.get(reg['tai_lieu'][p][-1]['buoc'], {}).get('khoa')
    loi_ += [f'{p}: đầu vào đã đổi ({", ".join(cu(reg["tai_lieu"][p][-1]))})' for p in ds
             if p in reg['tai_lieu'] and cu(reg['tai_lieu'][p][-1]) and not khoa(p)]
    if loi_ and not a.bo_qua_kiem_tra:
        loi.thoat_loi('Chưa lập được đường cơ sở:\n  ' + '\n  '.join(loi_) + '\nChạy lại các bước liên quan (chay.py trang_thai) rồi lập lại.')
    chi_tiet, dung_lai = {}, []
    for p in ds:
        last = reg['tai_lieu'][p][-1]
        major = int(last['phien_ban'].split('.')[0]) + 1
        rec = dict(last, phien_ban=f'{major}.0', ngay=loi.bay_gio(), trang_thai='Đường cơ sở', ghi_chu=f'Đường cơ sở {ma}. {a.ghi_chu}'.strip(),
                   nguoi=a.nguoi or last.get('nguoi', ''), duong_co_so=ma)
        rec.pop('lich_su_trang_thai', None); rec.pop('ngay_kiem_tra', None)
        reg['tai_lieu'][p].append(rec); chi_tiet[p] = rec['phien_ban']
        if p.endswith('.docx') and rec.get('noi_dung') and os.path.exists(loi.duong_dan(rec['noi_dung'])):
            nd = loi.doc_json(rec['noi_dung']); nd['meta']['phien_ban'] = rec['phien_ban']
            nd_bl = loi.duong_dan(rec['noi_dung'].replace('.json', f'_{ma}.json')); loi.ghi_json(nd_bl, nd)
            r = subprocess.run([sys.executable, os.path.join(loi.THU_MUC_LOI, 'scripts', 'build_docx.py'), nd_bl, loi.duong_dan(p)]
                               + (['--co-dinh', rec['co_dinh']] if rec.get('co_dinh') else []), capture_output=True, text=True, encoding='utf-8', errors='replace')
            if r.returncode:
                print(f'Không dựng lại được {p}: {r.stderr.strip()[-300:]}')
            else:
                dung_lai.append(p)
    reg['duong_co_so'].append({'ma': ma, 'ten': a.ten, 'ngay': a.ngay or loi.bay_gio()[:10], 'luc': loi.bay_gio(), 'nguoi': a.nguoi, 'ghi_chu': a.ghi_chu,
                               'tai_lieu': chi_tiet, 'bo_qua_kiem_tra': bool(loi_)})
    if a.hop_dong:
        reg['hop_dong'] = {'duong_co_so': ma, 'ngay': a.ngay or loi.bay_gio()[:10]}
        for p in ds:
            if buoc.get(reg['tai_lieu'][p][-1]['buoc'], {}).get('khoa'):
                reg['tai_lieu'][p][-1]['trang_thai'] = 'Khóa'
    loi.ghi_json('du_lieu/phien_ban.json', reg)
    loi.ghi_nhat_ky('qlda-phien-ban', f'phien_ban.duong_co_so.{ma}', 'script', f'Lập đường cơ sở {ma} ({a.ten}), {len(chi_tiet)} tài liệu',
                    ra=['du_lieu/phien_ban.json'], chi_tiet=chi_tiet)
    print(f'Đường cơ sở {ma}: {len(chi_tiet)} tài liệu, dựng lại {len(dung_lai)} tệp Word với số phiên bản mới.')
    if os.path.isdir(loi.duong_dan('.git')):
        print(f'Gợi ý: git add -A && git commit -m "Đường cơ sở {ma}: {a.ten}" && git tag {ma}')
    sys.exit(0)

if a.lenh != 'tong_hop':
    loi.thoat_loi('Lệnh không hợp lệ')

# Tổng hợp
ten_buoc = lambda bid: buoc.get(bid, {}).get('ten', bid)


def ten_nut(n):
    if n in sd['dau_vao']:
        return sd['dau_vao'][n]['mo_ta']
    return next((b['ten'] for b in sd['buoc'] if n in b['ra']), n)


def ten_tep_tl(k):
    """Tên tài liệu theo bước tạo ra tệp, kèm tên tệp nếu bước có nhiều tệp Word."""
    lst = reg['tai_lieu'].get(k, [])
    ten = ten_buoc(lst[-1]['buoc']) if lst else os.path.basename(k)
    return ten + (' (' + os.path.splitext(os.path.basename(k))[0].replace('_', ' ') + ')' if k.startswith(('ket_qua/03_', 'ket_qua/09_')) else '')


def ngay_gio(v):
    v = str(v or '')
    return (loi.ngay(v[:10]) + (' ' + v[11:16] if len(v) > 10 else '')) if v else ''
danh_muc, du_lieu_ds, lich_su = [], [], []
thu_tu = {p: i for i, p in enumerate(p for b in sd['buoc'] for p in b['ra'].values())}


def thu_tu_tep(p):
    for q, i in thu_tu.items():
        if p == q or p.startswith(q.rstrip('/') + '/'):
            return i
    return 999


for p in sorted(reg['tai_lieu'], key=lambda p: (thu_tu_tep(p), p)):
    lst = reg['tai_lieu'][p]; last = lst[-1]; b = buoc.get(last['buoc'], {})
    if last['buoc'] == 'phien_ban':
        continue  # đầu ra của chính bước này không tự liệt kê
    doi = [] if b.get('anh_chup') else cu(last)  # báo cáo theo kỳ giữ số liệu tại thời điểm lập
    tinh_trang = ('Khóa' if b.get('khoa') and reg.get('hop_dong') else ('Cần cập nhật' if doi else 'Cập nhật'))
    if not os.path.exists(loi.duong_dan(p)):
        tinh_trang = 'Không còn tệp'
    row = {'tep': p, 'ten_tep': os.path.basename(p), 'buoc': last['buoc'], 'ten': ten_buoc(last['buoc']), 'skill': b.get('skill', ''), 'nhom': b.get('nhom', ''),
           'phien_ban': last['phien_ban'], 'ngay': last['ngay'][:10], 'ngay_tai_lieu': last.get('ngay_tai_lieu', ''), 'nguoi': last.get('nguoi', ''), 'trang_thai': last.get('trang_thai', ''),
           'tinh_trang': tinh_trang, 'dau_vao_da_doi': ', '.join(ten_nut(n) for n in doi), 'so_phien_ban': len(lst), 'duong_co_so': last.get('duong_co_so', '')}
    (danh_muc if p.startswith('ket_qua/') else du_lieu_ds).append(row)
    for r in lst:
        lich_su.append({'tep': p, 'ten_tep': os.path.basename(p), 'phien_ban': r['phien_ban'], 'ngay': r['ngay'], 'thoi_diem': ngay_gio(r['ngay']), 'ngay_tai_lieu': r.get('ngay_tai_lieu', ''),
                        'nguoi': r.get('nguoi', ''), 'buoc': r['buoc'], 'ten_buoc': ten_buoc(r['buoc']), 'trang_thai': r.get('trang_thai', ''), 'ghi_chu': r.get('ghi_chu', ''), 'hash': r['hash'],
                        'la_tai_lieu': p.startswith('ket_qua/')})
for i, r in enumerate(danh_muc, 1):
    r['ma'] = f'TL{i:02d}'

so_td = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})
cr = [{'ma': c['ma'], 'tieu_de': c['tieu_de'], 'trang_thai': c['trang_thai'], 'ngay_quyet_dinh': c.get('ngay_quyet_dinh', ''),
       'tai_lieu_cap_nhat': ', '.join(ten_buoc(x.split(' ')[0]) for x in c.get('tai_lieu_cap_nhat', [])),
       'tai_lieu_khoa': ', '.join(ten_buoc(x.split(' ')[0]) for x in c.get('tai_lieu_khoa', [])),
       'phien_ban_sau': '. '.join(f'{ten_tep_tl(k)} {v}' for k, v in c.get('phien_ban_sau', {}).items() if k.startswith('ket_qua/')),
       'phu_luc_hop_dong': 'Có' if c.get('phu_luc_hop_dong') else 'Không'} for c in so_td['yeu_cau']]

# Nhật ký chạy
import json  # noqa: E402
nk = []
pnk = loi.duong_dan('bang_chung/nhat_ky_chay.jsonl')
if os.path.exists(pnk):
    for line in open(pnk, encoding='utf-8'):
        try:
            nk.append(json.loads(line))
        except ValueError:
            pass
theo_skill = {}
for x in nk:
    t = theo_skill.setdefault(x['skill'], {'skill': x['skill'], 'phien_ban_skill': x.get('phien_ban_skill', ''), 'so_lan_script': 0, 'so_lan_agent': 0, 'prompt': set()})
    t['so_lan_script' if x.get('loai') == 'script' else 'so_lan_agent'] += 1
    if x.get('prompt'):
        t['prompt'].add(x['prompt'])
nhat_ky = [dict(v, prompt=', '.join(sorted(os.path.basename(p) for p in v['prompt']))) for v in theo_skill.values()]

# Git
git = []
try:
    r = subprocess.run(['git', '-C', loi.GOC, 'log', '--date=short', '--pretty=format:%h|%ad|%an|%s', '-n', '300'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20)
    if r.returncode == 0:
        git = [dict(zip(('ma', 'ngay', 'tac_gia', 'noi_dung'), line.split('|', 3))) for line in r.stdout.splitlines() if line.count('|') >= 3]
except Exception:
    pass

_ngs = []
for r in danh_muc:
    try:
        _ngs.append(dt.datetime.strptime(r['ngay_tai_lieu'], '%d/%m/%Y').date())
    except (ValueError, TypeError):
        pass
out = {'ngay_tong_hop': loi.bay_gio()[:10], 'ngay_tai_lieu': loi.ngay(max(_ngs).isoformat()) if _ngs else loi.ngay(loi.bay_gio()[:10]), 'danh_muc': danh_muc, 'du_lieu': du_lieu_ds, 'lich_su': lich_su,
       'lich_su_tai_lieu': [x for x in lich_su if x['la_tai_lieu']], 'duong_co_so': reg['duong_co_so'],
       'duong_co_so_bang': [{'ma': x['ma'], 'ten': x['ten'], 'ngay': x['ngay'], 'so_tai_lieu': len(x['tai_lieu']), 'nguoi': x.get('nguoi', ''),
                             'ghi_chu': x.get('ghi_chu', '')} for x in reg['duong_co_so']],
       'thay_doi': cr, 'nhat_ky': nhat_ky, 'so_lan_chay': len(nk), 'so_lan_agent': sum(1 for x in nk if x.get('loai') != 'script'),
       'git': git, 'co_git': bool(git), 'hop_dong': reg.get('hop_dong', {}), 'kho_luu_tru': loi.du_an().get('kho_luu_tru', ''),
       'so_tai_lieu': len(danh_muc), 'so_can_cap_nhat': sum(1 for r in danh_muc if r['tinh_trang'] == 'Cần cập nhật'),
       'so_phien_ban_tai_lieu': sum(1 for x in lich_su if x['la_tai_lieu']), 'quy_uoc': QU}
loi.ghi_json('du_lieu/phien_ban_tong_hop.json', out)

# Excel
from openpyxl import Workbook  # noqa: E402
from openpyxl.formatting.rule import FormulaRule  # noqa: E402
from openpyxl.styles import PatternFill  # noqa: E402
import xlsx_chung as X  # noqa: E402
OUT_DIR = loi.duong_dan('ket_qua/15_Quan_ly_phien_ban'); os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'So_phien_ban.xlsx')
wb = Workbook()
wb.properties.creator = wb.properties.lastModifiedBy = loi.du_an().get('nguoi_lap', '')
ws = wb.active; ws.title = 'Danh_muc'
X.tieu_de(ws, 1, ['Mã', 'Tài liệu', 'Tệp', 'Nhóm', 'Phiên bản', 'Ngày', 'Trạng thái', 'Tình trạng', 'Số phiên bản', 'Đầu vào đã đổi'],
          [7, 36, 52, 18, 10, 12, 14, 14, 12, 30])
for i, r in enumerate(danh_muc, 2):
    for j, k in enumerate(['ma', 'ten', 'tep', 'nhom', 'phien_ban', 'ngay', 'trang_thai', 'tinh_trang'], 1):
        X.o(ws, i, j, r[k], nhap=True)
    X.o(ws, i, 9, f'=COUNTIF(Lich_su!$A:$A,C{i})'); X.o(ws, i, 10, r['dau_vao_da_doi'], nhap=True)
if danh_muc:
    ws.conditional_formatting.add(f'H2:H{len(danh_muc) + 1}', FormulaRule(formula=['H2="Cần cập nhật"'], fill=PatternFill('solid', fgColor='FCE4D6')))
ls = wb.create_sheet('Lich_su')
X.tieu_de(ls, 1, ['Tệp', 'Phiên bản', 'Ngày giờ', 'Người', 'Bước', 'Trạng thái', 'Ghi chú', 'Băm nội dung'], [52, 10, 18, 18, 18, 14, 50, 14])
for i, r in enumerate(lich_su, 2):
    for j, k in enumerate(['tep', 'phien_ban', 'ngay', 'nguoi', 'buoc', 'trang_thai', 'ghi_chu', 'hash'], 1):
        X.o(ls, i, j, r[k], nhap=True)
dl = wb.create_sheet('Du_lieu')
X.tieu_de(dl, 1, ['Tệp dữ liệu', 'Bước', 'Phiên bản', 'Ngày', 'Tình trạng', 'Số phiên bản'], [40, 30, 10, 12, 14, 12])
for i, r in enumerate(du_lieu_ds, 2):
    for j, k in enumerate(['tep', 'ten', 'phien_ban', 'ngay', 'tinh_trang'], 1):
        X.o(dl, i, j, r[k], nhap=True)
    X.o(dl, i, 6, f'=COUNTIF(Lich_su!$A:$A,A{i})')
bl = wb.create_sheet('Duong_co_so')
X.tieu_de(bl, 1, ['Mã', 'Tên', 'Ngày', 'Tệp', 'Phiên bản'], [8, 36, 12, 52, 10])
i = 2
for x in reg['duong_co_so']:
    for p, v in x['tai_lieu'].items():
        for j, val in enumerate([x['ma'], x['ten'], x['ngay'], p, v], 1):
            X.o(bl, i, j, val, nhap=True)
        i += 1
td_ = wb.create_sheet('Thay_doi')
X.tieu_de(td_, 1, ['Mã CR', 'Nội dung', 'Trạng thái', 'Ngày quyết định', 'Tài liệu cập nhật', 'Phiên bản sau thay đổi', 'Tài liệu khóa', 'Phụ lục hợp đồng'],
          [8, 40, 14, 14, 50, 50, 22, 12])
for i, r in enumerate(cr, 2):
    for j, k in enumerate(['ma', 'tieu_de', 'trang_thai', 'ngay_quyet_dinh', 'tai_lieu_cap_nhat', 'phien_ban_sau', 'tai_lieu_khoa', 'phu_luc_hop_dong'], 1):
        X.o(td_, i, j, r[k], nhap=True, wrap=j in (2, 5, 6))
nks = wb.create_sheet('Nhat_ky')
X.tieu_de(nks, 1, ['Skill', 'Phiên bản skill', 'Số lần chạy script', 'Số lần agent', 'Prompt đã dùng'], [26, 14, 16, 14, 60])
for i, r in enumerate(nhat_ky, 2):
    for j, k in enumerate(['skill', 'phien_ban_skill', 'so_lan_script', 'so_lan_agent', 'prompt'], 1):
        X.o(nks, i, j, r[k], nhap=True)
if git:
    gs = wb.create_sheet('Git')
    X.tieu_de(gs, 1, ['Commit', 'Ngày', 'Tác giả', 'Nội dung'], [10, 12, 20, 80])
    for i, r in enumerate(git, 2):
        for j, k in enumerate(['ma', 'ngay', 'tac_gia', 'noi_dung'], 1):
            X.o(gs, i, j, r[k], nhap=True)
wb.save(OUT)
kq = X.tinh_lai(OUT)
if kq and kq.get('status'):
    lc = X.dem_loi_cong_thuc(OUT)
    if lc:
        loi.thoat_loi('Công thức lỗi: ' + ', '.join(lc[:10]))
    v = X.doc_gia_tri(OUT)
    for i, r in enumerate(danh_muc, 2):
        if v['Danh_muc'].cell(row=i, column=9).value != r['so_phien_ban']:
            loi.thoat_loi(f'Đếm phiên bản trong Excel lệch ở {r["tep"]}')
print(f'{len(danh_muc)} tài liệu, {out["so_phien_ban_tai_lieu"]} phiên bản tài liệu, {len(reg["duong_co_so"])} đường cơ sở, {len(cr)} yêu cầu thay đổi, '
      f'{len(nk)} lần chạy được ghi nhật ký, {"có" if git else "chưa có"} lịch sử git. Cần cập nhật: {out["so_can_cap_nhat"]}.')
h = loi.bam_obj({k: v for k, v in out.items() if k not in ('ngay_tong_hop', 'nhat_ky', 'so_lan_chay', 'so_lan_agent')})
loi.hoan_tat_buoc('phien_ban', 'Tổng hợp sổ phiên bản', bo_qua=('doc_phien_ban',),
                  hash_tep={'ket_qua/15_Quan_ly_phien_ban/So_phien_ban.xlsx': h, 'du_lieu/phien_ban_tong_hop.json': h})
print('Tiếp theo: python .claude/skills/qlda-loi/scripts/chay.py chuan_bi phien_ban')
