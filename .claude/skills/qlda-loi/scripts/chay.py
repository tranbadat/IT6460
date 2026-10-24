"""Điều phối bộ skill quản lý dự án.

Dùng (chạy từ thư mục gốc dự án):
  python .claude/skills/qlda-loi/scripts/chay.py trang_thai            trạng thái mọi tài liệu, bước nên làm tiếp
  python .../chay.py chuan_bi <buoc>                                    kiểm tra đầu vào, lập khung cho agent Soạn thảo
  python .../chay.py hoan_thien <buoc> [--ghi-chu "..."] [--ngay ...]   ghép bản soạn, vòng tạo, kiểm tra, sửa (tối đa 3 vòng)
  python .../chay.py dang_ky <buoc> [--ghi-chu "..."]                   đăng ký phiên bản đầu ra do script riêng tạo (xlsx, json)
  python .../chay.py anh_huong <mã nút hoặc đường dẫn tệp>              các tài liệu phải cập nhật khi nút này thay đổi
  python .../chay.py bang_chung                                         xuất phụ lục bằng chứng prompt và skill
Thư mục làm việc của mỗi bước: lam_viec/<buoc>/ (khung.json, ban_soan.json, các vòng, báo cáo kiểm tra).
Tài liệu theo kỳ (đầu ra là thư mục, ví dụ báo cáo tiến độ): khi đạt, khung, bản soạn, các vòng được chép vào
lam_viec/<buoc>/<tên tệp đầu ra>/, bằng chứng lớp A là bang_chung/kiem_tra/<buoc>_<tên tệp>_v<phiên bản>_lopA.json.
CSV trong dau_vao/thuc_te/ chỉ có dòng tiêu đề coi như chưa có. Bước có đầu vào thực tế mà chưa tệp nào có dữ liệu
ở trạng thái "chờ dữ liệu thực tế", không được gợi ý làm tiếp.
Sau ký hợp đồng, phiên bản mới (hoan_thien, dang_ky) ghi khóa phat_hanh: bản phát hành hiện hành tại ngày tài liệu
(du_lieu/phat_hanh.json). Khi mô phỏng dự án, đặt biến môi trường QLDA_NGAY=yyyy-mm-dd làm ngày hiện hành.
Mã thoát: 0 đạt, 2 cần agent Soạn thảo hoặc người dùng xử lý, 1 lỗi.
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
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import loi  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('lenh'); ap.add_argument('doi_tuong', nargs='?'); ap.add_argument('--ghi-chu', default='')
ap.add_argument('--json', action='store_true'); ap.add_argument('--vong-toi-da', type=int, default=3)
ap.add_argument('--bo-qua-khoa', action='store_true', help='tạo lại tài liệu đã khóa (chỉ khi có căn cứ, ghi lý do trong --ghi-chu)')
ap.add_argument('--ngay', help='ngày ghi trên tài liệu (yyyy-mm-dd), mặc định theo ngay_tai_lieu của đặc tả')
a = ap.parse_args()
sd = loi.so_do()
BUOC = {b['id']: b for b in sd['buoc']}


def py(*args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=loi.GOC)


def tim_dac_ta(buoc_id):
    b = BUOC[buoc_id]
    for f in glob.glob(os.path.join(loi.THU_MUC_SKILLS, b['skill'], 'dac_ta', '*.json')):
        try:
            if json.load(open(f, encoding='utf-8')).get('id') == buoc_id:
                return f
        except Exception:
            pass
    return None


def co_du_lieu(p):
    """Tệp CSV chỉ có dòng tiêu đề (mẫu nhập liệu trống) coi như chưa có dữ liệu."""
    return not p.endswith('.csv') or bool(loi.doc_csv(p))


def ton_tai(nut):
    p = loi.duong_dan_nut(sd, nut)
    return bool(p) and os.path.exists(loi.duong_dan(p)) and co_du_lieu(p)


THU_MUC_THUC_TE = 'dau_vao/thuc_te/'


def cho_thuc_te(b):
    """Bước có đầu vào thực tế (dau_vao/thuc_te/) nhưng chưa tệp nào có dòng dữ liệu: chưa làm được, không gợi ý."""
    tt = [n for n in b['vao'] if (loi.duong_dan_nut(sd, n) or '').startswith(THU_MUC_THUC_TE)]
    return bool(tt) and not any(ton_tai(n) for n in tt)


def bat_buoc(nut):
    """Đầu vào nhóm theo khóa bat_buoc; đầu ra của bước khai báo ra_tuy_chon (ví dụ số liệu mô phỏng) không bắt buộc với bước sau."""
    if nut in sd['dau_vao']:
        return sd['dau_vao'][nut].get('bat_buoc', True)
    return not any(b.get('ra_tuy_chon') and nut in b['ra'] for b in sd['buoc'])


def nguon_cua(nut):
    if nut in sd['dau_vao']:
        return 'đầu vào do nhóm cung cấp: ' + sd['dau_vao'][nut]['mo_ta']
    for b in sd['buoc']:
        if nut in b['ra']:
            return f'bước {b["id"]} (skill {b["skill"]})'
    return '?'


BIEN_DONG = loi.nut_bien_dong(sd)


def tep_dang_ky(p, reg):
    """Các tệp trong sổ phiên bản ứng với đầu ra p (tệp, hoặc mọi tệp con nếu p là thư mục)."""
    q = loi.tuong_doi(loi.duong_dan(p))
    if os.path.isdir(loi.duong_dan(p)):
        # tệp đã chuyển khỏi thư mục đầu ra (bản cũ) giữ lịch sử trong sổ nhưng không tính vào trạng thái
        return [k for k in reg if k.startswith(q.rstrip('/') + '/') and os.path.exists(loi.duong_dan(k))]
    return [q]


def trang_thai_buoc(b):
    thieu = [n for n in b['vao'] if not ton_tai(n) and bat_buoc(n)]
    reg = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})['tai_lieu']
    ra_co = [p for p in b['ra'].values() if os.path.exists(loi.duong_dan(p))]
    thieu_ra = [p for p in b['ra'].values() if not os.path.exists(loi.duong_dan(p))]
    doi, chua_dk = set(), []
    for p in ra_co:
        ds = tep_dang_ky(p, reg)
        if not ds and not os.path.isdir(loi.duong_dan(p)):
            chua_dk.append(p)
        for q in ds:
            lst = reg.get(q, [])
            if not lst:
                chua_dk.append(q); continue
            if b.get('anh_chup'):
                continue  # tài liệu theo kỳ: giữ nguyên số liệu tại thời điểm lập
            for nut, h in lst[-1].get('vao', {}).items():
                r = loi.duong_dan_nut(sd, nut)
                if r and nut in b['vao'] and nut not in BIEN_DONG and loi.bam_nut(sd, nut) != h:
                    doi.add(nut)
    if not ra_co:
        tt = 'thiếu đầu vào' if thieu else ('chờ dữ liệu thực tế' if cho_thuc_te(b) else 'sẵn sàng thực hiện')
    elif chua_dk:
        tt = 'cũ, cần cập nhật'
        doi.add('chưa đăng ký phiên bản: ' + ', '.join(chua_dk))
    elif doi and b.get('khoa') and loi.da_ky_hop_dong():
        tt = 'đã khóa, ghi nhận thay đổi bằng phụ lục hoặc biên bản'
    elif doi:
        tt = 'cũ, cần cập nhật'
    elif thieu_ra:
        tt = 'thiếu tài liệu'
    else:
        tt = 'cập nhật'
    return {'id': b['id'], 'skill': b['skill'], 'ten': b['ten'], 'trang_thai': tt, 'thieu': thieu, 'dau_vao_da_doi': sorted(doi), 'thieu_ra': thieu_ra}


def ha_luu(nut):
    """Các bước bị ảnh hưởng (bắc cầu) khi nút thay đổi."""
    kq, hang = [], [nut]
    da = set()
    while hang:
        n = hang.pop(0)
        for b in sd['buoc']:
            if n in b['vao'] and b['id'] not in da:
                da.add(b['id']); kq.append(b)
                hang += list(b['ra'].keys())
    return kq


if a.lenh == 'trang_thai':
    rows = [trang_thai_buoc(b) for b in sd['buoc']]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); sys.exit(0)
    print(f'Thư mục dự án: {loi.GOC}')
    hd_ = loi.doc_json('du_lieu/phien_ban.json', {}).get('hop_dong')
    if hd_:  # giai đoạn thực hiện: phiên bản mới gắn bản phát hành hiện hành
        ph_ = loi.ban_phat_hanh_hien_hanh()
        print(f'Đã ký hợp đồng (đường cơ sở {hd_["duong_co_so"]}, {loi.ngay(hd_["ngay"])}). Ngày hiện hành {loi.ngay(loi.ngay_hien_hanh())}, '
              f'bản phát hành hiện hành: {ph_ or "chưa có"}. Phiên bản tài liệu mới ghi khóa phat_hanh theo ngày tài liệu.')
    for k, v in sd['dau_vao'].items():
        if not ton_tai(k):
            trong = ', chưa có dòng dữ liệu' if os.path.exists(loi.duong_dan(v['tep'])) else ''
            print(f'  Chưa có đầu vào {"bắt buộc" if v.get("bat_buoc", True) else "tùy chọn"}: {v["tep"]} ({v["mo_ta"]}{trong})')
    for r in rows:
        extra = ''
        if r['thieu']:
            extra = ' | thiếu: ' + ', '.join(f'{n} ({nguon_cua(n)})' for n in r['thieu'])
        if r['trang_thai'] == 'chờ dữ liệu thực tế':
            extra += f' | nhóm ghi dữ liệu thực tế vào {THU_MUC_THUC_TE} khi thực hiện dự án'
        if r['dau_vao_da_doi']:
            extra += ' | đầu vào đã đổi: ' + ', '.join(r['dau_vao_da_doi'])
        if r['trang_thai'] == 'thiếu tài liệu':
            extra += ' | chưa có: ' + ', '.join(r['thieu_ra']) + (f' (chạy chay.py chuan_bi {r["id"]})' if tim_dac_ta(r['id']) else ' (xem SKILL.md của skill)')
        print(f'[{r["trang_thai"]}] {r["id"]} - {r["ten"]} (skill {r["skill"]}){extra}')
    tiep = [r for r in rows if r['trang_thai'] in ('sẵn sàng thực hiện', 'cũ, cần cập nhật', 'thiếu tài liệu')]
    if tiep:
        print('Nên làm tiếp: ' + ', '.join(f'{r["id"]} (skill {r["skill"]})' for r in tiep[:3]))
    sys.exit(0)

if a.lenh == 'anh_huong':
    nut = a.doi_tuong
    if nut not in sd['dau_vao'] and not any(nut in b['ra'] for b in sd['buoc']):
        rel = loi.tuong_doi(loi.duong_dan(nut))
        nut = next((k for k, v in sd['dau_vao'].items() if v['tep'] == rel), None) or \
            next((k for b in sd['buoc'] for k, p in b['ra'].items() if p == rel), None)
        if not nut:
            loi.thoat_loi('Không tìm thấy nút hoặc tệp trong sơ đồ phụ thuộc: ' + a.doi_tuong)
    ds = ha_luu(nut)
    out = [{'buoc': b['id'], 'ten': b['ten'], 'skill': b['skill'], 'tep': list(b['ra'].values()), 'khoa': b.get('khoa', ''),
            'da_tao': any(os.path.exists(loi.duong_dan(p)) for p in b['ra'].values())} for b in ds]
    if a.json:
        print(json.dumps({'nut': nut, 'anh_huong': out}, ensure_ascii=False, indent=1)); sys.exit(0)
    print(f'Thay đổi ở {nut} ảnh hưởng {len(out)} bước, cập nhật theo thứ tự:')
    for i, o in enumerate(out, 1):
        tt = ' [đã khóa: ' + o['khoa'] + ']' if o['khoa'] else ('' if o['da_tao'] else ' [chưa tạo]')
        print(f'  {i}. {o["buoc"]} - {o["ten"]} (skill {o["skill"]}): {", ".join(o["tep"])}{tt}')
    sys.exit(0)

if a.lenh == 'bang_chung':
    r = py(os.path.join(HERE, 'xuat_bang_chung.py'))
    print(r.stdout.strip() or r.stderr.strip()); sys.exit(r.returncode)

if a.doi_tuong not in BUOC:
    loi.thoat_loi('Bước không có trong sơ đồ: ' + str(a.doi_tuong) + '. Các bước: ' + ', '.join(BUOC))
b = BUOC[a.doi_tuong]
wd = loi.duong_dan(f'lam_viec/{b["id"]}')
os.makedirs(wd, exist_ok=True)
P = lambda n: os.path.join(wd, n)

if a.lenh == 'dang_ky':
    pbs = loi.hoan_tat_buoc(b['id'], 'Đăng ký đầu ra của bước ' + b['ten'], a.ghi_chu)
    for k, v in pbs.items():
        print(f'Phiên bản {v}: {k}')
    sys.exit(0)

spec_path = tim_dac_ta(b['id'])
if not spec_path:
    loi.thoat_loi(f'Bước {b["id"]} không có đặc tả tài liệu. Chạy script riêng của skill {b["skill"]} theo SKILL.md.')
spec = json.load(open(spec_path, encoding='utf-8'))
if b.get('khoa') and loi.da_ky_hop_dong() and a.lenh in ('chuan_bi', 'hoan_thien') and not a.bo_qua_khoa:
    loi.thoat_loi(f'{b["ten"]} đã khóa sau ký hợp đồng: {b["khoa"]} Nếu thật sự cần tạo lại, dùng --bo-qua-khoa và ghi căn cứ trong --ghi-chu.')
if spec.get('chi_kiem_tra') and a.lenh in ('chuan_bi', 'hoan_thien'):
    loi.thoat_loi(f'Tài liệu của bước {b["id"]} do script riêng tạo: {spec["chi_kiem_tra"]}')


def lap_khung_moi():
    """Chạy script tính trước và lập khung, ghi băm nguồn để phát hiện khung cũ."""
    for cmd in spec.get('truoc', []):
        r = py(os.path.join(loi.THU_MUC_SKILLS, cmd[0]), *cmd[1:])
        print(r.stdout.strip())
        if r.returncode:
            print(r.stderr.strip())
            loi.ghi_nhat_ky(b['skill'], b['id'] + '.truoc', 'script', 'Chạy script tính trước khi lập khung: ' + cmd[0], ket_qua='lỗi')
            sys.exit(1)
    r = py(os.path.join(HERE, 'lap_khung.py'), spec_path, P('khung.json'))
    print(r.stdout.strip())
    if r.returncode:
        print(r.stderr.strip()); sys.exit(1)
    loi.ghi_json(P('khung_nguon.json'), bam_nguon())


def luu_theo_ky(ten_ra, so_vong):
    """Tài liệu theo kỳ dùng chung lam_viec/<buoc>/: chép khung, bản soạn, nội dung, Word và báo cáo kiểm tra các vòng
    vào lam_viec/<buoc>/<tên tệp đầu ra>/ để kỳ sau không ghi đè bằng chứng kỳ trước. Trả về thư mục lưu."""
    d = P(ten_ra)
    os.makedirs(d, exist_ok=True)
    tep = ['khung.json', 'khung_nguon.json', 'ban_soan.json', 'noi_dung.json']
    tep += [f'{b["id"]}_vong{i}.docx' for i in range(1, so_vong + 1)] + [f'bao_cao_kiem_tra_vong{i}.json' for i in range(1, so_vong + 1)]
    for t in tep:
        if os.path.exists(P(t)):
            shutil.copy(P(t), os.path.join(d, t))
    return loi.tuong_doi(d)


def bam_nguon():
    """Băm nguồn của khung, gồm cả du_an (bìa, đơn vị thực hiện gán từ nha_thau.json) để khung được lập lại khi đổi."""
    ds = dict(spec.get('nguon', {})); ds.setdefault('da', 'dau_vao/du_an.json'); ds['_dac_ta'] = loi.tuong_doi(spec_path)
    return {k: loi.bam_hieu_luc(v) for k, v in ds.items()}

if a.lenh == 'chuan_bi':
    thieu = [f'{n} ({nguon_cua(n)})' for n in b['vao'] if not ton_tai(n) and bat_buoc(n)]
    if thieu:
        loi.ghi_nhat_ky(b['skill'], b['id'] + '.chuan_bi', 'script', 'Kiểm tra đầu vào', ket_qua='thiếu đầu vào', chi_tiet={'thieu': thieu})
        loi.thoat_loi('Thiếu đầu vào:\n- ' + '\n- '.join(thieu))
    lap_khung_moi()
    loi.ghi_nhat_ky(b['skill'], b['id'] + '.chuan_bi', 'script', 'Lập khung tài liệu từ đặc tả và dữ liệu',
                    vao=[spec_path] + [loi.duong_dan_nut(sd, n) for n in b['vao'] if ton_tai(n)], ra=[P('khung.json')], ket_qua='đạt')
    print(f'Tiếp theo: agent Soạn thảo đọc {loi.tuong_doi(P("khung.json"))} (khóa can_soan) và viết {loi.tuong_doi(P("ban_soan.json"))}.')
    sys.exit(0)

if a.lenh == 'hoan_thien':
    if not os.path.exists(P('ban_soan.json')):
        loi.thoat_loi('Chưa có ' + loi.tuong_doi(P('ban_soan.json')) + '. Agent Soạn thảo viết trước.', 2)
    if loi.doc_json(P('khung_nguon.json'), {}) != bam_nguon():
        print('Dữ liệu nguồn hoặc đặc tả đã đổi sau khi lập khung, lập lại khung trước khi ghép bản soạn.')
        lap_khung_moi()
        loi.ghi_nhat_ky(b['skill'], b['id'] + '.chuan_bi', 'script', 'Lập lại khung do dữ liệu nguồn đã đổi', vao=[spec_path], ra=[P('khung.json')], ket_qua='đạt')
    r = py(os.path.join(HERE, 'dien_khung.py'), P('khung.json'), P('ban_soan.json'), P('noi_dung.json'))
    print(r.stdout.strip())
    if r.returncode:
        loi.ghi_nhat_ky(b['skill'], b['id'] + '.ghep', 'script', 'Ghép bản soạn vào khung', vao=[P('ban_soan.json')], ket_qua='lỗi', chi_tiet={'thong_bao': r.stdout[-2000:]})
        print('DỪNG: agent Soạn thảo sửa ban_soan.json theo thông báo trên.'); sys.exit(2)
    nut_ra = spec.get('nut_ra') or next(k for k in b['ra'] if k.startswith('doc_'))
    tep_ra = b['ra'][nut_ra]
    theo_ky = not os.path.splitext(tep_ra)[1]
    if theo_ky:  # đầu ra là thư mục: tên tệp theo đặc tả (ví dụ theo kỳ báo cáo)
        nguon_ = loi.nap_nguon(spec.get('nguon', {}))
        tep_ra = tep_ra + '/' + loi.giai_bieu_thuc(spec.get('ten_tep', b['id'] + '.docx'), nguon_)
    ten_ra = os.path.splitext(os.path.basename(tep_ra))[0]
    # tài liệu theo kỳ: tên bằng chứng có tên tệp đầu ra để kỳ sau không ghi đè kỳ trước
    tien_to_bc = f'{b["id"]}_{ten_ra}' if theo_ky else b['id']
    nguon_ng = loi.nap_nguon(dict({'da': 'dau_vao/du_an.json'}, **spec.get('nguon', {})))
    ngay_tl = loi.ngay(loi.ngay_hien_hanh())  # ngày máy, hoặc QLDA_NGAY khi mô phỏng dự án
    if a.ngay:
        try:
            ngay_tl = loi.ngay(dt.date.fromisoformat(a.ngay).isoformat())
        except ValueError:
            loi.thoat_loi(f'--ngay phải theo dạng yyyy-mm-dd, nhận được "{a.ngay}"')
    else:
        for bt_ in ([spec['ngay_tai_lieu']] if isinstance(spec.get('ngay_tai_lieu'), str) else spec.get('ngay_tai_lieu', [])):
            loi_ng = []
            v_ = loi.giai_bieu_thuc(bt_, nguon_ng, loi_ng)
            if not loi_ng and v_.strip():
                ngay_tl = v_; break
    for n in range(1, a.vong_toi_da + 1):
        nd = json.load(open(P('noi_dung.json'), encoding='utf-8'))
        h = loi.bam_obj(nd['blocks'])
        pb, moi = loi.du_kien_phien_ban(tep_ra, h)
        cu_ = loi.doc_json('du_lieu/phien_ban.json', {'tai_lieu': {}})['tai_lieu'].get(tep_ra, [])
        if not moi and cu_ and cu_[-1].get('ngay_tai_lieu') and not a.ngay:
            ngay_tl = cu_[-1]['ngay_tai_lieu']  # nội dung không đổi: giữ ngày của phiên bản đã đăng ký
        nd['meta']['phien_ban'] = pb
        nd['meta']['ngay'] = ngay_tl
        loi.ghi_json(P('noi_dung.json'), nd)
        ban = P(f'{b["id"]}_vong{n}.docx')
        r = py(os.path.join(HERE, 'build_docx.py'), P('noi_dung.json'), ban, *(['--co-dinh', spec['co_dinh']] if spec.get('co_dinh') else []))
        if r.returncode:
            print(r.stderr.strip()); sys.exit(1)
        bc = P(f'bao_cao_kiem_tra_vong{n}.json')
        r = py(os.path.join(HERE, 'kiem_tra_tai_lieu.py'), spec_path, ban, '--json', bc)
        ket = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()
        print(f'[vòng {n}] {ket}')
        loi.ghi_nhat_ky('qlda-loi', b['id'] + f'.kiem_tra_vong{n}', 'script', 'Kiểm tra lớp A', vao=[ban], ra=[bc], ket_qua=ket)
        if r.returncode == 0:
            os.makedirs(os.path.dirname(loi.duong_dan(tep_ra)), exist_ok=True)
            shutil.copy(ban, loi.duong_dan(tep_ra))
            nd_luu = P('noi_dung_' + os.path.splitext(os.path.basename(tep_ra))[0] + '.json')
            shutil.copy(P('noi_dung.json'), nd_luu)
            pb = loi.dang_ky_phien_ban(b['id'], tep_ra, b['vao'], a.ghi_chu, hash_noi_dung=h,
                                       them={'noi_dung': loi.tuong_doi(nd_luu), 'co_dinh': spec.get('co_dinh', ''), 'ngay_tai_lieu': ngay_tl})
            os.makedirs(loi.duong_dan('bang_chung/kiem_tra'), exist_ok=True)
            shutil.copy(bc, loi.duong_dan(f'bang_chung/kiem_tra/{tien_to_bc}_v{pb}_lopA.json'))
            luu = luu_theo_ky(ten_ra, n) if theo_ky else None
            loi.ghi_nhat_ky(b['skill'], b['id'] + '.hoan_thien', 'script', f'Tạo tài liệu {b["ten"]}, đạt kiểm tra lớp A sau {n} vòng',
                            vao=[P('noi_dung.json')], ra=[tep_ra], ket_qua='đạt', chi_tiet={'phien_ban': pb, 'so_vong': n, 'luu_theo_ky': luu})
            print(f'ĐẠT lớp A. Tài liệu: {tep_ra}, phiên bản {pb}.' + (f' Bản soạn và các vòng lưu tại {luu}.' if luu else ''))
            print(f'Tiếp theo: agent Kiểm tra lớp B theo qlda-loi/prompts/vai_kiem_tra.md với đặc tả {loi.tuong_doi(spec_path)}, '
                  f'chép báo cáo vào bang_chung/kiem_tra/{tien_to_bc}_v{pb}_lopB.json.')
            sys.exit(0)
        r = py(os.path.join(HERE, 'sua_tu_dong.py'), bc, P('noi_dung.json'), '--ban-soan', P('ban_soan.json'))
        print('[vòng %d sửa] ' % n + r.stdout.strip())
        loi.ghi_nhat_ky('qlda-loi', b['id'] + f'.sua_vong{n}', 'script', 'Sửa tự động lỗi cơ học', vao=[bc], ra=[P('noi_dung.json'), P('ban_soan.json')], ket_qua=r.stdout.strip().splitlines()[0] if r.stdout else '')
        if r.returncode == 2:
            print('DỪNG: còn lỗi cần agent Soạn thảo hoặc người dùng xử lý, xem ' + loi.tuong_doi(bc))
            sys.exit(2)
    print('DỪNG: quá số vòng tối đa vẫn còn lỗi.')
    sys.exit(1)

loi.thoat_loi('Lệnh không hợp lệ: ' + a.lenh)
