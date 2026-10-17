"""Chuẩn bị dữ liệu HSDT: kiểm tra thông tin nhà thầu, đối chiếu yêu cầu HSMT, lập Mẫu 10A theo hạng mục Mẫu 01A.

Dùng: python tinh_hsdt.py      (chay.py chuan_bi hsdt tự gọi)
Kiểm tra (lỗi thì dừng): trường bắt buộc của nha_thau.json, hợp đồng tương tự đạt giá trị và thời gian theo HSMT,
doanh thu bình quân các năm HSMT yêu cầu, nhân sự chủ chốt đủ số lượng, giá dự thầu không vượt giá gói thầu,
mọi hạng mục Mẫu 01A có tiến độ hoàn thành trước cut over.
Ra: du_lieu/hsdt_bang.json (bảng đáp ứng HSMT, Mẫu 10A, tóm tắt năng lực).
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402

hsmt = loi.doc_json('du_lieu/hsmt.json'); nt = loi.doc_json('dau_vao/nha_thau.json'); cp = loi.doc_json('du_lieu/chi_phi.json')
lich = loi.doc_json('du_lieu/lich.json'); wbs = loi.doc_json('du_lieu/wbs.json'); pc = loi.doc_json('du_lieu/phan_cong.json')
loi_ds = []
for k in ('ten', 'dia_chi', 'dai_dien', 'chuc_vu_dai_dien', 'ma_so_thue', 'nam_thanh_lap', 'ngay_ky_don'):
    if nt.get(k) in (None, ''):
        loi_ds.append(f'nha_thau.json thiếu {k}')
hd = [h for h in nt.get('hop_dong_tuong_tu', []) if h.get('ten')]
if not hd:
    loi_ds.append('nha_thau.json chưa có hợp đồng tương tự')
min_hd = hsmt['tien']['hop_dong_tuong_tu_toi_thieu']
moc = hsmt['nang_luc']['moc_hop_dong_tuong_tu']  # dạng "01 tháng 01 năm 2024"
d_moc = dt.date(int(re.search(r'năm (\d{4})', moc).group(1)), int(re.search(r'tháng (\d+)', moc).group(1)), int(moc[:2]))
hd_dat = [h for h in hd if (h.get('gia_tri') or 0) >= min_hd and h.get('ngay_hoan_thanh') and dt.date.fromisoformat(h['ngay_hoan_thanh']) >= d_moc]
if hd and not hd_dat:
    loi_ds.append(f'Không có hợp đồng tương tự từ {loi.tien(min_hd)} đồng hoàn thành từ {moc}')
nam_yc = hsmt['nang_luc']['cac_nam_doanh_thu']
dtn = {int(x['nam']): float(x['doanh_thu']) for x in nt.get('doanh_thu', []) if x.get('nam') and x.get('doanh_thu')}
thieu_nam = [n for n in nam_yc if n not in dtn]
if thieu_nam:
    loi_ds.append(f'nha_thau.json thiếu doanh thu các năm {thieu_nam}')
dt_bq = sum(dtn.get(n, 0) for n in nam_yc) / len(nam_yc)
if not thieu_nam and dt_bq < hsmt['tien']['doanh_thu_binh_quan_toi_thieu']:
    loi_ds.append(f'Doanh thu bình quân {loi.tien(dt_bq)} đồng thấp hơn yêu cầu {loi.tien(hsmt["tien"]["doanh_thu_binh_quan_toi_thieu"])} đồng')
tv = {t['id']: t for t in loi.doc_json('dau_vao/thanh_vien.json')['thanh_vien']}
cho = [t['ho_ten'] for t in tv.values() if t.get('_can_xac_nhan')]
if cho:
    loi_ds.append('thanh_vien.json còn vị trí chưa xác nhận nhân sự (_can_xac_nhan): ' + ', '.join(cho) + '. Ghi họ tên thật và bỏ khóa _can_xac_nhan')
yc_cc = {y['stt']: y for y in hsmt.get('nhan_su_chu_chot', [])}
ns_cc = []
for x in pc['vi_tri_chu_chot']:
    if len(x.get('thanh_vien', [])) < x['so_luong']:
        loi_ds.append(f'Vị trí chủ chốt {x["vi_tri"]} thiếu nhân sự')
    yc = yc_cc.get(x['stt'], {}); m = re.search(r'(\d+) năm', yc.get('kinh_nghiem', ''))
    for i in x.get('thanh_vien', []):
        t = tv.get(i, {})
        for k in ('trinh_do', 'so_nam_kinh_nghiem', 'kinh_nghiem'):
            if t.get(k) in (None, ''):
                loi_ds.append(f'thanh_vien.json: {t.get("ho_ten", i)} (nhân sự chủ chốt) thiếu {k}')
        dat = 'Đáp ứng'
        if m and t.get('so_nam_kinh_nghiem') not in (None, '') and float(t['so_nam_kinh_nghiem']) < int(m.group(1)):
            dat = 'Chưa đáp ứng'
            if 'hoặc' not in yc.get('kinh_nghiem', ''):
                loi_ds.append(f'{t["ho_ten"]}: {t["so_nam_kinh_nghiem"]} năm kinh nghiệm, HSMT yêu cầu {yc["kinh_nghiem"].lower()}')
        ns_cc.append({'stt': x['stt'], 'vi_tri': x['vi_tri'], 'yeu_cau': yc.get('kinh_nghiem', ''), 'ho_ten': t.get('ho_ten', i),
                      'trinh_do': t.get('trinh_do', ''), 'so_nam': t.get('so_nam_kinh_nghiem', ''), 'kinh_nghiem': t.get('kinh_nghiem', ''),
                      'chung_chi': t.get('chung_chi', '') or 'Không', 'danh_gia': dat})
han = hsmt['lich'].get('dong_thau_iso'); ph = hsmt['lich'].get('phat_hanh_iso')
if nt.get('ngay_ky_don') and han and not (ph <= nt['ngay_ky_don'] <= han):
    loi_ds.append(f'Ngày ký đơn dự thầu {loi.ngay(nt["ngay_ky_don"])} phải trong khoảng phát hành HSMT {loi.ngay(ph)} đến đóng thầu {loi.ngay(han)}')
if cp['gia_chao'] > hsmt['tien']['gia_goi_thau']:
    loi_ds.append('Giá dự thầu vượt giá gói thầu')
if nt.get('hop_dong_khong_hoan_thanh'):
    loi_ds.append('Có hợp đồng không hoàn thành, cần đối chiếu tiêu chí lịch sử hợp đồng của HSMT')

# Mẫu 10A theo hạng mục 01A
lg = {x['ma']: x for x in lich['goi'] if x['la']}
by, la = loi.nut_wbs(wbs)
m10 = []
for h in hsmt['mau_01a']:
    goi = [g['ma'] for g in la if h['stt'] in (g.get('hang_muc_01a') or []) and g['ma'] in lg and not lg[g['ma']].get('dan_trai')]
    goi = goi or [g['ma'] for g in la if h['stt'] in (g.get('hang_muc_01a') or []) and g['ma'] in lg]
    if not goi:
        loi_ds.append(f'Hạng mục 01A số {h["stt"]} không có gói trong lịch'); continue
    a = min(lg[m]['bat_dau'] for m in goi); b = max(lg[m]['ket_thuc'] for m in goi)
    if b > lich['cut_over']:
        loi_ds.append(f'Hạng mục 01A số {h["stt"]} hoàn thành sau cut over')
    m10.append({'stt': h['stt'], 'danh_muc': h['danh_muc'], 'khoi_luong': h['khoi_luong'], 'don_vi': h['don_vi'], 'dia_diem': h['dia_diem'],
                'bat_dau': a, 'ket_thuc': b, 'yeu_cau': h['ngay_hoan_thanh'], 'goi': ', '.join(sorted(goi, key=loi.khoa_ma)[:6]) + (' ...' if len(goi) > 6 else '')})
L = hsmt['lich']


def don_du_thau():
    """Mẫu số 02 lấy nguyên văn từ dau_vao/Mau_5A.docx, điền các trường do Hệ thống trích xuất."""
    import docx
    ps = [p.text.strip() for p in docx.Document(loi.duong_dan('dau_vao/Mau_5A.docx')).paragraphs]
    i0 = next(i for i, t in enumerate(ps) if t.startswith('Mẫu số 02'))
    i1 = next(i for i in range(i0 + 1, len(ps)) if ps[i].startswith('Ghi chú'))
    goi = hsmt['goi_thau']['ten']; gia = cp['gia_chao']; bd = hsmt['tien']['bao_dam_du_thau']
    etbmt = nt.get('so_e_tbmt') or 'theo thông báo mời thầu trên Hệ thống mạng đấu thầu quốc gia'
    gia_txt = f"{loi.tien(gia)} đồng (bằng chữ: {loi.so_bang_chu(gia).lower()} đồng)"
    tim = re.compile(r'\s*_{2,}\s*,?\s*\[[^\]]*\]?|\s*_{2,}|\s*\[\s*[^\]]*\]')
    dien = {'Ngày:': [loi.ngay(nt.get('ngay_ky_don', ''))], 'Tên gói thầu:': [goi], 'Kính gửi:': [hsmt['goi_thau']['chu_dau_tu']],
            'Tên nhà thầu:': [nt.get('ten', ''), nt.get('ma_so_thue', ''), goi, etbmt, gia_txt],
            'Hiệu lực của E-HSDT': [f"{hsmt['thoi_han']['hieu_luc_hsdt_ngay']} ngày kể từ ngày đóng thầu"],
            'Bảo đảm dự thầu': [f"{loi.tien(bd)} đồng (bằng chữ: {loi.so_bang_chu(bd).lower()} đồng)"],
            'Hiệu lực của Bảo đảm dự thầu': [f"{hsmt['thoi_han']['hieu_luc_bao_dam_du_thau_ngay']} ngày kể từ ngày đóng thầu"],
            'Ngoài ra': [loi.ptg(nt.get('giam_gia_phan_tram') or 0)], 'Giá dự thầu sau khi': [gia_txt]}
    giam = float(nt.get('giam_gia_phan_tram') or 0)
    chao_hang = 'chào hàng' in hsmt['goi_thau'].get('hinh_thuc', '')
    out, so_muc = [], 0
    for t in ps[i0 + 1:i1]:
        if not t or t.upper().startswith('ĐƠN DỰ THẦU'):
            continue
        if not giam and (t.startswith('Ngoài ra') or t.startswith('Giá dự thầu sau khi')):
            continue  # không đề xuất giảm giá
        if bd < 50000000 and t.startswith('Hiệu lực của Bảo đảm dự thầu'):
            continue  # ghi chú (2) của mẫu
        if not chao_hang and re.match(r'\d+\.\s*Có đủ năng lực, kinh nghiệm', t):
            continue  # ghi chú (4): chỉ áp dụng chào hàng cạnh tranh
        k = next((k for k in dien if t.startswith(k)), None)
        if k:
            vals = iter(dien[k])
            t = tim.sub(lambda m: ' ' + next(vals, '') + (',' if ',' in m.group(0).split('[')[0] else ''), t)
            t = re.sub(r'\s+([,.;:])', r'\1', re.sub(r':\s*', ': ', t, count=1)).strip()
        t = re.sub(r'\s*\((\d)\)', '', t)
        m = re.match(r'(\d+)\.\s*(.*)', t)
        if m:
            so_muc += 1; t = f'{so_muc}. {m.group(2)}'
        out.append(t)
    out.append(f"Đơn dự thầu được ký bằng chữ ký số của {nt.get('dai_dien', '')}, {nt.get('chuc_vu_dai_dien', '')}, khi nộp E-HSDT.")
    return out


bd_ = hsmt['tien']['bao_dam_du_thau']; bl = nt.get('bao_dam_du_thau') or {}
if bd_ < 50000000:
    bao_dam_ghi_chu = 'Giá trị nhỏ hơn 50 triệu đồng nên nhà thầu cam kết trong đơn dự thầu theo Mục 18.8 E-CDNT, không nộp thư bảo lãnh dự thầu khi nộp E-HSDT.'
else:
    for k in ('to_chuc_phat_hanh', 'so', 'ngay_phat_hanh'):
        if not bl.get(k):
            loi_ds.append(f'nha_thau.json thiếu bao_dam_du_thau.{k} (giá trị bảo đảm từ 50 triệu đồng phải nộp thư bảo lãnh Mẫu số 04A)')
    bao_dam_ghi_chu = (f"Nhà thầu nộp thư bảo lãnh dự thầu theo Mẫu số 04A số {bl.get('so', '')} do {bl.get('to_chuc_phat_hanh', '')} phát hành ngày "
                       f"{loi.ngay(bl.get('ngay_phat_hanh', '')) if bl.get('ngay_phat_hanh') else ''}, hiệu lực {hsmt['thoi_han']['hieu_luc_bao_dam_du_thau_ngay']} ngày kể từ ngày đóng thầu.")
try:
    don = don_du_thau()
except (StopIteration, FileNotFoundError, KeyError) as e:
    don = []; loi_ds.append(f'Không đọc được Mẫu số 02 trong dau_vao/Mau_5A.docx ({e})')
dap_ung = [
    ['Giá dự thầu không vượt giá gói thầu', f'{loi.tien(cp["gia_chao"])} đồng, giá gói thầu {loi.tien(hsmt["tien"]["gia_goi_thau"])} đồng', 'Đáp ứng'],
    ['Hiệu lực E-HSDT', f'Tối thiểu {hsmt["thoi_han"]["hieu_luc_hsdt_ngay"]} ngày', 'Đáp ứng'],
    ['Bảo đảm dự thầu', f'{loi.tien(hsmt["tien"]["bao_dam_du_thau"])} đồng, ' + ('cam kết trong đơn dự thầu (Mục 18.8 E-CDNT)' if hsmt['tien']['bao_dam_du_thau'] < 50000000
                        else f'thư bảo lãnh hiệu lực tối thiểu {hsmt["thoi_han"]["hieu_luc_bao_dam_du_thau_ngay"]} ngày kể từ ngày đóng thầu'), 'Đáp ứng'],
    ['Hợp đồng tương tự', f'{len(hd_dat)} hợp đồng từ {loi.tien(min_hd)} đồng, hoàn thành từ {moc}', 'Đáp ứng' if hd_dat else 'Chưa đáp ứng'],
    ['Doanh thu bình quân', f'{loi.tien(dt_bq)} đồng các năm {", ".join(map(str, nam_yc))}', 'Đáp ứng' if dt_bq >= hsmt['tien']['doanh_thu_binh_quan_toi_thieu'] else 'Chưa đáp ứng'],
    ['Nhân sự chủ chốt (Bảng số 02)', '. '.join(f'{x["vi_tri"]}: {x.get("ho_ten", "")}' for x in pc['vi_tri_chu_chot']),
     'Đáp ứng' if all(x['danh_gia'] == 'Đáp ứng' for x in ns_cc) else 'Chưa đáp ứng'],
    ['Thời gian thực hiện', f'Từ {L["hop_dong_hieu_luc_du_kien"]} đến cut over {L["cut_over"]}, hoàn thành dự kiến {loi.ngay(lich["ket_thuc_du_kien"])}', 'Đáp ứng' if lich['ket_thuc_du_kien'] <= lich['cut_over'] else 'Chưa đáp ứng'],
    ['Phạm vi theo Mẫu 01A', f'{len(m10)}/{len(hsmt["mau_01a"])} hạng mục có tiến độ và giá', 'Đáp ứng' if len(m10) == len(hsmt['mau_01a']) else 'Chưa đáp ứng'],
]
out = {'mau_10a': m10, 'dap_ung': {'cot': ['Yêu cầu của HSMT', 'Đề xuất của nhà thầu', 'Đánh giá'], 'dong': dap_ung, 'widths': [2800, 5000, 1500]},
       'hop_dong_tuong_tu': hd, 'doanh_thu': [{'nam': n, 'doanh_thu': dtn.get(n, 0)} for n in nam_yc], 'doanh_thu_binh_quan': round(dt_bq),
       'so_hop_dong_dat': len(hd_dat), 'nhan_su_chu_chot': ns_cc, 'don_du_thau': don, 'bao_dam_ghi_chu': bao_dam_ghi_chu,
       'bao_dam_du_thau_chu': loi.so_bang_chu(hsmt['tien']['bao_dam_du_thau']).lower()}
loi.ghi_json('du_lieu/hsdt_bang.json', out)
if loi_ds:
    print('LỖI:', *loi_ds, sep='\n- ')
    print('Cập nhật dau_vao/nha_thau.json hoặc các bước liên quan (phân công, lịch, dự toán) rồi chạy lại.')
    sys.exit(1)
print(f'Đã chuẩn bị dữ liệu HSDT: {len(m10)} hạng mục Mẫu 10A, {len(hd_dat)} hợp đồng tương tự đạt, doanh thu bình quân {loi.tien(dt_bq)} đồng')
