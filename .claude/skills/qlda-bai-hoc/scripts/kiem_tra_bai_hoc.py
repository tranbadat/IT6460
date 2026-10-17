"""Kiểm tra danh sách bài học kinh nghiệm và ghi du_lieu/bai_hoc.json.

Dùng: python kiem_tra_bai_hoc.py lam_viec/bai_hoc/bai_hoc_nhap.json
Kiểm tra:
  B01 số bài học tối thiểu, B02 phủ nhóm bắt buộc, B03 mã bằng chứng phải tồn tại, B04 mỗi bài học có bằng chứng,
  B05 trích dẫn đủ rủi ro đã xảy ra, yêu cầu thay đổi, chỉ tiêu không đạt (lỗi), ghi chép cần cải thiện và nghiệm thu lại (cảnh báo),
  B06 có cả bài học tích cực và cần cải thiện, B07 đủ trường và độ dài, B08 mã trùng, B09 nhóm hoặc loại không hợp lệ.
Mã thoát 0 đạt, 1 còn lỗi.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

if len(sys.argv) < 2:
    loi.thoat_loi('Dùng: python kiem_tra_bai_hoc.py lam_viec/bai_hoc/bai_hoc_nhap.json')
nhap = loi.doc_json(sys.argv[1])
CFG = loi.doc_json(os.path.join(HERE, '..', 'references', 'nhom_bai_hoc.json'))
kt = loi.doc_json('du_lieu/ket_thuc.json'); rr = loi.doc_json('du_lieu/rui_ro.json'); lich = loi.doc_json('du_lieu/lich.json')
wbs = loi.doc_json('du_lieu/wbs.json'); so_td = loi.doc_json('du_lieu/thay_doi.json', {'yeu_cau': []})
F = []
add = lambda ma, mo, vt='', md='loi': F.append({'ma': ma, 'muc_do': md, 'vi_tri': vt, 'mo_ta': mo})

# Ghi chép cải tiến: "- R-S1-02 (cần cải thiện): nội dung"
retro = []
p = loi.duong_dan('dau_vao/thuc_te/retro.md')
if os.path.exists(p):
    for line in open(p, encoding='utf-8'):
        m = re.match(r'\s*[-*]\s*(R-S(\d+)-\d+)\s*\(([^)]*)\)\s*:?\s*(.*)', line)
        if m and m.group(4).strip():
            retro.append({'ma': m.group(1), 'sprint': 'S' + m.group(2), 'loai': m.group(3).strip(), 'noi_dung': m.group(4).strip()})
ma_tt = {
    'yêu cầu thay đổi': {c['ma'] for c in so_td['yeu_cau']},
    'rủi ro': {r['ma'] for r in rr['danh_sach']} | {x['ma'] for x in kt['rui_ro']['danh_sach']},
    'ghi chép cải tiến': {r['ma'] for r in retro},
    'nghiệm thu': {x['ma'] for x in kt['nghiem_thu']['danh_sach']},
    'lỗi': {x['ma'] for x in loi.doc_csv('dau_vao/thuc_te/loi.csv')},
    'chỉ tiêu': {k['ma'] for k in kt['kpi']},
    'mốc': {m['ma'] for m in lich['moc']},
    'sprint': {s['ma'] for s in lich['sprint']},
    'gói WBS': {g['ma'] for g in wbs['goi']},
    'yêu cầu RFP': {y['ma'] for y in loi.doc_json('du_lieu/rfp_yeu_cau.json')['yeu_cau']},
}


def loai_ma(x):
    return next((k for k, v in ma_tt.items() if x in v), None)


ds = nhap.get('bai_hoc', [])
if len(ds) < CFG['so_luong_toi_thieu']:
    add('B01', f'Có {len(ds)} bài học, tối thiểu {CFG["so_luong_toi_thieu"]}')
seen = set()
for b in ds:
    m = b.get('ma', '?')
    if m in seen:
        add('B08', f'Mã bài học trùng: {m}', m)
    seen.add(m)
    if b.get('nhom') not in CFG['nhom']:
        add('B09', f'Nhóm "{b.get("nhom")}" không thuộc {", ".join(CFG["nhom"])}', m)
    if b.get('loai') not in CFG['loai']:
        add('B09', f'Loại "{b.get("loai")}" không thuộc {", ".join(CFG["loai"])}', m)
    for k, n in CFG['do_dai_toi_thieu'].items():
        v = str(b.get(k, '')).strip()
        if not v:
            add('B07', f'Thiếu trường {k}', m)
        elif len(v) < n:
            add('B07', f'Trường {k} quá ngắn ({len(v)} ký tự, nên từ {n})', m, 'canh_bao')
    if not str(b.get('ap_dung_cho', '')).strip():
        add('B07', 'Thiếu trường ap_dung_cho', m, 'canh_bao')
    bc = b.get('bang_chung', [])
    if not bc:
        add('B04', 'Bài học không có mã bằng chứng', m)
    for x in bc:
        if not loai_ma(x):
            add('B03', f'Mã bằng chứng {x} không có trong dữ liệu dự án', m)
nhom_co = {b.get('nhom') for b in ds}
for n in CFG['nhom_bat_buoc']:
    if n not in nhom_co:
        add('B02', f'Chưa có bài học nhóm {CFG["nhom"][n]}')
if not any(b.get('loai') == 'tich_cuc' for b in ds) or not any(b.get('loai') == 'can_cai_thien' for b in ds):
    add('B06', 'Cần có cả bài học tích cực và bài học cần cải thiện')

trich = {}
for b in ds:
    for x in b.get('bang_chung', []):
        trich.setdefault(x, []).append(b.get('ma'))
    for x in re.findall(r'\b(?:CR|RR|NT|K)\d+\b|\bR-S\d+-\d+\b', ' '.join(str(b.get(k, '')) for k in ('tinh_huong', 'nguyen_nhan', 'bai_hoc', 'khuyen_nghi'))):
        trich.setdefault(x, []).append(b.get('ma'))
for x in kt['rui_ro']['xay_ra_ds']:
    if x['ma'] not in trich:
        add('B05', f'Rủi ro đã xảy ra {x["ma"]} chưa được rút bài học', x['ma'])
for c in kt['thay_doi']['danh_sach']:
    if c['ma'] not in trich:
        add('B05', f'Yêu cầu thay đổi {c["ma"]} chưa được rút bài học', c['ma'])
for k in kt['kpi_khong_dat']:
    if k['ma'] not in trich:
        add('B05', f'Chỉ tiêu không đạt {k["ma"]} chưa được rút bài học', k['ma'])
for r in retro:
    if 'cải thiện' in r['loai'] and r['ma'] not in trich:
        add('B05', f'Ghi chép cải tiến {r["ma"]} chưa được trích dẫn', r['ma'], 'canh_bao')
for x in kt['nghiem_thu']['danh_sach']:
    if x.get('so_lan', 1) > 1 and x['ma'] not in trich:
        add('B05', f'Tiêu chí nghiệm thu lại {x["ma"]} chưa được trích dẫn', x['ma'], 'canh_bao')

loi_ = [f for f in F if f['muc_do'] == 'loi']
for f in F:
    print(f"[{f['muc_do']}] {f['ma']} {f['vi_tri']}: {f['mo_ta']}")
ra = []
for b in sorted(ds, key=lambda b: loi.khoa_ma(b.get('ma', ''))):
    ra.append(dict(b, nhom_ten=CFG['nhom'].get(b.get('nhom'), ''), loai_ten=CFG['loai'].get(b.get('loai'), ''),
                   bang_chung_hien_thi=', '.join(b.get('bang_chung', [])),
                   khuyen_nghi_hien_thi=str(b.get('khuyen_nghi', '')).rstrip('.') + '. Áp dụng cho ' + str(b.get('ap_dung_cho', '')).strip().rstrip('.').lower() + '.' if b.get('ap_dung_cho') else b.get('khuyen_nghi', '')))
for r in retro:
    r['bai_hoc'] = ', '.join(sorted(set(trich.get(r['ma'], [])), key=loi.khoa_ma))
theo_nhom = [{'nhom': CFG['nhom'][n], 'tich_cuc': sum(1 for b in ds if b.get('nhom') == n and b.get('loai') == 'tich_cuc'),
              'can_cai_thien': sum(1 for b in ds if b.get('nhom') == n and b.get('loai') == 'can_cai_thien')} for n in CFG['nhom']]
theo_nhom = [x for x in theo_nhom if x['tich_cuc'] or x['can_cai_thien']]
dem_nguon = {}
for x in trich:
    k = loai_ma(x)
    if k:
        dem_nguon[k] = dem_nguon.get(k, 0) + 1
out = {'bai_hoc': ra, 'tong': len(ds), 'so_tich_cuc': sum(1 for b in ds if b.get('loai') == 'tich_cuc'),
       'so_can_cai_thien': sum(1 for b in ds if b.get('loai') == 'can_cai_thien'), 'theo_nhom': theo_nhom, 'retro': retro,
       'nguon_bang_chung': [{'loai': k, 'so_ma': v} for k, v in dem_nguon.items()],
       'kiem_tra': {'ket_luan': 'dat' if not loi_ else 'chua_dat', 'so_loi': len(loi_), 'so_canh_bao': len(F) - len(loi_), 'phat_hien': F}}
loi.ghi_json('lam_viec/bai_hoc/bao_cao_kiem_tra.json', out['kiem_tra'])
print(f'{len(ds)} bài học ({out["so_tich_cuc"]} tích cực, {out["so_can_cai_thien"]} cần cải thiện). Kết luận: {out["kiem_tra"]["ket_luan"]} '
      f'({len(loi_)} lỗi, {len(F) - len(loi_)} cảnh báo)')
if loi_:
    sys.exit(1)
loi.ghi_json('du_lieu/bai_hoc.json', out)
loi.hoan_tat_buoc('bai_hoc', 'Kiểm tra và ghi danh sách bài học kinh nghiệm', bo_qua=('doc_bai_hoc',), ket_qua=f'{len(ds)} bài học')
print('Đã ghi du_lieu/bai_hoc.json. Tiếp theo: python .claude/skills/qlda-loi/scripts/chay.py chuan_bi bai_hoc')
