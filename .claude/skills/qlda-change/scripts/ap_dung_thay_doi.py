"""Áp dụng yêu cầu thay đổi đã phê duyệt vào dữ liệu nguồn, do yeu_cau_thay_doi.py import (không chạy trực tiếp).

Lệnh ap_dung CRxx kiểm tra trước dữ liệu đề xuất bằng kiem_tra_wbs, kiem_tra_giao_viec, lap_lich trên bản sao tạm (cảnh báo TD24), sinh tệp đề xuất trong lam_viec/thay_doi/CRxx/de_xuat/ (giữ đường dẫn của tệp đích), bảng thay đổi
lam_viec/thay_doi/CRxx/thay_doi_du_lieu.json, ghi phụ lục hợp đồng và thứ tự chạy lại vào du_lieu/thay_doi.json. --ghi áp thẳng vào tệp đích.
- lam_viec/wbs/wbs_nhap.json: mục mới, gói mới (nguồn ghi mã CR), gói thay đổi cộng MD và phụ thuộc.
- dau_vao/uoc_luong.json: tong_md và tong_theo_nhom cộng MD của CR, thêm bước ước lượng ghi mã CR và phụ lục.
- lam_viec/giao_viec/phan_cong_nhap.json: giao việc gói mới theo phương án đã chọn, trách nhiệm (A) của mục mới mức 1, 2.
- dau_vao/du_an.json: ngay_cut_over theo phụ lục, khoảng uat dời cùng số ngày, cam kết "phụ lục có hiệu lực" làm ngày sớm nhất
  của gói mới, dấu vết dieu_chinh_theo_cr.
- lam_viec/lich/moc_nhap.json: ràng buộc không sớm hơn và mốc ngày cố định từ ngày CR dời theo cut over, hạn mốc theo phụ lục,
  gói mới gắn cam kết phụ lục, mục tiêu sprint cho sprint mới khi số sprint tăng.
- dau_vao/don_gia.json: gia_chao_muc_tieu cộng giá điều chỉnh của phụ lục, dấu vết dieu_chinh_gia_theo_phu_luc.
- dau_vao/thanh_vien.json: thêm người khi phương án đã chọn là them_nguoi.
- dau_vao/chi_tieu_ky_thuat.json: khoảng hỗ trợ tăng cường sau cut over (bao_hanh.ho_tro_tang_cuong) dời để bắt đầu ngày làm việc sau cut over
  mới, giữ số ngày làm việc. du_an.json giai_doan.ket_thuc khai báo ngày (tu, den) cũng dời như vậy. Ngày rà soát kết thúc (master plan,
  theo cuối khoảng hỗ trợ tăng cường) và ngày đóng dự án (lich.json ngay_dong_du_an, theo số ngày giai đoạn Kết thúc sau cut over) tính lại
  khi chạy lại các bước. Hiệu lực bảo đảm thực hiện hợp đồng của HSMT (đã khóa) sớm hơn ngày đóng dự án mới thì cảnh báo TD25 để ghi gia hạn
  trong phụ lục.
Phụ lục có thể khai báo đợt thanh toán riêng cho phần giá điều chỉnh (--dot-thanh-toan <tệp json> khi áp dụng, hoặc lệnh phu_luc sau khi đã
áp dụng): [{"dot": 6, "su_kien": "...", "phan_tram_gia_dieu_chinh": 100, "moc": "M6", "nguon": "quyết định ..."}]. Tổng phần trăm bằng 100.
Khi có, các đợt gốc của hợp đồng tính trên giá hợp đồng ban đầu (qlda-cost-estimate/scripts/tinh_chi_phi.py), đợt đã thu trước ngày phụ lục
không bao giờ tính lại.
Sau khi chạy lại, CR đổi đường cơ sở hợp đồng (phụ lục hoặc mức lớn) lập đường cơ sở mới bằng so_phien_ban.py duong_co_so BLn --cr <ma_cr>.
Mã kiểm tra TD19 (áp dụng khi chưa phê duyệt hoặc đã áp dụng, đợt thanh toán của phụ lục chưa hợp lệ), TD20 (dữ liệu nguồn chưa áp dụng khi đóng CR), TD23 (chưa có đường cơ sở sau CR), TD24 (cảnh báo: lịch lập lại với dữ liệu đề xuất chưa đạt), TD25 (cảnh báo: hiệu lực bảo đảm thực hiện sớm hơn ngày đóng dự án mới).
"""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'qlda-loi', 'scripts'))
import loi  # noqa: E402
import lich_thay_doi as ltd  # noqa: E402

TEP = {'wbs': 'lam_viec/wbs/wbs_nhap.json', 'uoc_luong': 'dau_vao/uoc_luong.json', 'giao_viec': 'lam_viec/giao_viec/phan_cong_nhap.json',
       'du_an': 'dau_vao/du_an.json', 'moc': 'lam_viec/lich/moc_nhap.json', 'don_gia': 'dau_vao/don_gia.json', 'thanh_vien': 'dau_vao/thanh_vien.json',
       'chi_tieu': 'dau_vao/chi_tieu_ky_thuat.json'}
LENH = loi.doc_json(os.path.join(HERE, '..', 'references', 'lenh_chay_lai.json'))


def doc_tho(p):
    """Đọc tệp JSON đúng như trên đĩa (không gán trường ngầm như loi.doc_json với du_an.json)."""
    with open(loi.duong_dan(p), encoding='utf-8') as f:
        return json.load(f)


def md_theo_nhom(cr):
    out = {}
    for x in cr.get('goi_thay_doi', []):
        out[x['ma'].split('.')[0]] = out.get(x['ma'].split('.')[0], 0) + float(x.get('md_tang', 0))
    for g in cr.get('goi_moi', []):
        out[g['ma'].split('.')[0]] = out.get(g['ma'].split('.')[0], 0) + float(g['md'])
    return {k: round(v, 2) for k, v in out.items() if v}


# ---------------------------------------------------------------- từng tệp nguồn
def de_xuat_wbs(cr, pl):
    wn = doc_tho(TEP['wbs'])
    thay = {x['ma']: x for x in cr.get('goi_thay_doi', [])}
    goi = []
    for g in wn['goi']:
        x = thay.get(g['ma'])
        if x:
            g = dict(g, md=round(float(g['md']) + float(x.get('md_tang', 0)), 2), phu_thuoc=list(dict.fromkeys(g.get('phu_thuoc', []) + x.get('them_phu_thuoc', []))),
                     nguon=list(dict.fromkeys(g.get('nguon', []) + [cr['ma']])),
                     md_tang_theo_cr=dict(g.get('md_tang_theo_cr') or {}, **{cr['ma']: float(x.get('md_tang', 0))}))
        goi.append(g)
    co = {g['ma'] for g in goi}
    nhom = md_theo_nhom(cr)
    for m in cr.get('muc_moi', []):
        if m['ma'] in co:
            continue
        x = {'ma': m['ma'], 'ten': m['ten'], 'muc': m['ma'].count('.') + 1}
        if '.' not in m['ma']:
            x['can_cu_uoc_luong'] = m.get('can_cu_uoc_luong') or {
                'kich_thuoc': f'{len([g for g in cr.get("goi_moi", []) if g["ma"].startswith(m["ma"] + ".")])} gói theo yêu cầu thay đổi {cr["ma"]}',
                'cach_phan_ra': f'Tổng nhóm {loi.md(nhom.get(m["ma"], 0))} MD theo đánh giá tác động của {cr["ma"]} và phụ lục hợp đồng {pl["so"]}, MD từng gói do người đánh giá '
                                'ước lượng trong phiếu yêu cầu thay đổi, gồm phân tích, lập trình, kiểm thử và triển khai'}
        goi.append(x)
    for g in cr.get('goi_moi', []):
        x = {k: g[k] for k in ('ma', 'ten', 'md', 'loai', 'san_pham', 'phu_thuoc', 'hang_muc_01a', 'thoi_luong_toi_thieu', 'giai_doan') if k in g}
        goi.append(dict(x, muc=g['ma'].count('.') + 1, nguon=list(dict.fromkeys([cr['ma']] + list(g.get('nguon', []))))))
    return dict(wn, goi=sorted(goi, key=lambda g: loi.khoa_ma(g['ma'])))


def de_xuat_uoc_luong(cr, pl):
    ul = doc_tho(TEP['uoc_luong'])
    nhom, ttn = md_theo_nhom(cr), dict(ul.get('tong_theo_nhom', {}))
    ten_moi = {m['ma']: m['ten'] for m in cr.get('muc_moi', [])}
    for k, v in nhom.items():
        # md_theo_cr: phần MD của nhóm do yêu cầu thay đổi, để truy vết phần tăng của gói hiện có về mã CR (từ 1.4.6)
        ttn[k] = dict(ttn[k], md=round(float(ttn[k]['md']) + v, 2), md_theo_cr=dict(ttn[k].get('md_theo_cr') or {}, **{cr['ma']: v})) if k in ttn \
            else {'ten': ten_moi.get(k, k), 'md': v, 'md_theo_cr': {cr['ma']: v}}
    md = round(sum(nhom.values()), 2)
    buoc = list(ul.get('cac_buoc', []))
    tang = [x['ma'] for x in cr.get('goi_thay_doi', []) if float(x.get('md_tang', 0))]  # gói tăng MD và gói chỉ thêm phụ thuộc tách riêng (từ 1.4.7)
    pt_ = [x['ma'] for x in cr.get('goi_thay_doi', []) if not float(x.get('md_tang', 0))]
    buoc.append({'buoc': len(buoc) + 1, 'noi_dung': f'Yêu cầu thay đổi {cr["ma"]} ({cr["tieu_de"]}) theo {pl["so"]}: {len(cr.get("goi_moi", []))} gói mới, '
                 f'{len(tang)} gói tăng khối lượng' + (f' ({", ".join(tang)})' if tang else '')
                 + (f', {len(pt_)} gói chỉ thêm phụ thuộc ({", ".join(pt_)})' if pt_ else '') + ', ước lượng theo từng gói trong phiếu',
                 'md': md, 'ma_cr': cr['ma'], 'phu_luc': pl['so']})
    return dict(ul, tong_md=round(float(ul['tong_md']) + md, 2), tong_theo_nhom=ttn, cac_buoc=buoc)


def keo_dan_trai(gv, da_cu, da_moi):
    """Gói dàn trải đến sprint cuối cũ (giám sát, kiểm soát suốt dự án) kéo đến sprint cuối mới khi cut over lùi."""
    cu, moi = len(loi.danh_sach_sprint(da_cu)), len(loi.danh_sach_sprint(da_moi))
    if moi <= cu:
        return gv, []
    keo = [x['ma'] for x in gv if x.get('dan_trai') and str(x.get('den_sprint')) == str(cu)]
    return [dict(x, den_sprint=moi) if x['ma'] in keo else x for x in gv], keo


def de_xuat_giao_viec(cr, pa, vai, da_moi):
    pc = doc_tho(TEP['giao_viec'])
    them = {g['ma']: g for g in pa.get('ho_tro_goi_thay_doi', []) + ((pa.get('them_nguoi') or {}).get('giao_viec', []))}
    gv = [dict(x, **{k: v for k, v in them.get(x['ma'], {}).items() if k in ('R', 'ho_tro')}) for x in pc['giao_viec']]
    gv, _ = keo_dan_trai(gv, loi.du_an(), da_moi)
    co = {x['ma'] for x in gv}
    gv += [{'ma': x['ma'], 'R': x['R'], 'ho_tro': x['ho_tro'], 'dan_trai': False, 'tu_sprint': None, 'den_sprint': None,
            'ly_do': '. '.join(y for y in (f'Gói mới theo {cr["ma"]}, {x["nguon"]}', x.get('ly_do', '')) if y)} for x in pa['giao_viec_de_xuat'] if x['ma'] not in co]
    tn = list(pc.get('trach_nhiem', []))
    co_tn = {x['ma'] for x in tn}
    qtda = (vai or {}).get('qtda', {}).get('id', '')
    ngoai = [b['id'] for b in pc.get('ben_ngoai', [])][:1]
    for m in cr.get('muc_moi', []):
        if m['ma'].count('.') > 1 or m['ma'] in co_tn:
            continue
        md = {}
        for x in pa['giao_viec_de_xuat']:
            if x['ma'].startswith(m['ma'] + '.'):
                g = next(g for g in cr['goi_moi'] if g['ma'] == x['ma'])
                md[x['R']] = md.get(x['R'], 0) + float(g['md'])
        r_chinh = max(md, key=md.get) if md else qtda
        a_ = qtda if '.' not in m['ma'] else r_chinh
        # vai trò bên ngoài (C, phê duyệt) của mục mới mức 2 theo mục cùng vị trí của các nhóm hiện có, ví dụ 5.2 theo 1.2 đến 4.2 (từ 1.4.7)
        id_ngoai = {b['id'] for b in pc.get('ben_ngoai', [])}
        cung = [x for x in tn if '.' in m['ma'] and x['ma'].count('.') == 1 and x['ma'].split('.')[1] == m['ma'].split('.')[1]]
        c_ngoai = sorted({c for x in cung for c in x.get('C', []) if c in id_ngoai})
        pd = sorted({c for x in cung for c in x.get('phe_duyet', [])})
        tn.append({'ma': m['ma'], 'A': a_, 'C': ([r_chinh] if r_chinh != a_ else []) + c_ngoai, 'I': [qtda] if qtda != a_ else ngoai,
                   **({'phe_duyet': ngoai} if '.' not in m['ma'] and ngoai else {'phe_duyet': pd} if pd else {})})
    return dict(pc, giao_viec=gv, trach_nhiem=sorted(tn, key=lambda x: loi.khoa_ma(x['ma'])))


def ma_cam_ket_moi(da):
    so_ = [int(c['ma'][2:]) for c in da.get('cam_ket_chu_dau_tu', []) if str(c.get('ma', '')).startswith('CK') and c['ma'][2:].isdigit()]
    return f'CK{max(so_ + [0]) + 1}'


def de_xuat_du_an(cr, pl, ext, k, ck, e=0):
    """du_an.json mới: cut over theo phụ lục, sprint.cut_over_goc giữ bố cục các sprint đã qua, khoảng uat dời k ngày và kéo dài e ngày,
    cam kết của Chủ đầu tư dời theo phụ lục, cam kết phụ lục có hiệu lực. k là số ngày dời đến hết khoảng uat gốc, cut over lùi k + e ngày."""
    da = doc_tho(TEP['du_an'])
    uat = dict(da.get('uat') or {})
    if (k or e) and uat.get('tu') and uat['tu'] >= cr['ngay_de_xuat']:
        uat = dict(uat, tu=ltd.dich(ext, uat['tu'], k), den=ltd.dich(ext, uat['den'], k + e))
    han_ck = {c['ma']: c['han_moi'] for c in pl.get('cam_ket_chu_dau_tu', [])}
    ds_ck = [dict(c, han=han_ck[c['ma']]) if c.get('ma') in han_ck else c for c in da.get('cam_ket_chu_dau_tu', [])]
    ds_ck = cam_ket_trong_uat(ds_ck, da.get('uat') or {}, uat, pl)
    sprint = dict(da.get('sprint') or {})
    if pl['cut_over_moi'] > da['ngay_cut_over']:
        sprint.setdefault('cut_over_goc', da['ngay_cut_over'])
    if cr.get('goi_moi'):
        # ngày sớm nhất của gói mới: phụ lục có hiệu lực, không sớm hơn ngày bắt đầu phần thay đổi đã dùng khi đánh giá (để lịch lập lại khớp)
        ds_ck.append({'ma': ck, 'noi_dung': f'Phụ lục hợp đồng {pl["so"]} điều chỉnh hợp đồng theo yêu cầu thay đổi {cr["ma"]} có hiệu lực, bắt đầu phần thay đổi',
                      'han': max(pl['ngay'], cr.get('lich_thay_doi', {}).get('ngay_bat_dau_thay_doi', ''))})
    vet = list(da.get('dieu_chinh_theo_cr', [])) + [{'ma_cr': cr['ma'], 'phu_luc': pl['so'], 'ngay': pl['ngay'], 'ngay_cut_over_truoc': da['ngay_cut_over'],
                                                     'ngay_cut_over_moi': pl['cut_over_moi'], 'uat_truoc': da.get('uat'), 'uat_moi': uat}]
    out = dict(da, ngay_cut_over=pl['cut_over_moi'], sprint=sprint, uat=uat, cam_ket_chu_dau_tu=ds_ck, dieu_chinh_theo_cr=vet)
    gd = dict(da.get('giai_doan') or {})
    kt_moi = doi_khoang_sau_cut_over(gd.get('ket_thuc') or {}, pl['cut_over_moi'], ext)
    if kt_moi:  # giai đoạn Kết thúc khai báo ngày: dời theo cut over mới, giữ số ngày làm việc
        out['giai_doan'] = dict(gd, ket_thuc=kt_moi)
    return out


def thay_ngay_chuoi(s_, cu, moi):
    """Thay ngày trong văn bản (dd/mm/yyyy, dd/mm) theo cặp ngày ISO cũ, mới."""
    for a_, b_ in zip(cu, moi):
        if a_ and b_ and a_ != b_:
            s_ = s_.replace(loi.ngay(a_), loi.ngay(b_)).replace(loi.ngay(a_)[:5], loi.ngay(b_)[:5])
    return s_


def cam_ket_trong_uat(ds_ck, uat_cu, uat_moi, pl):
    """Cam kết của Chủ đầu tư gắn khoảng kiểm thử chấp nhận (hạn là ngày cuối khoảng gốc, ví dụ người dùng tham gia kiểm thử chấp nhận)
    dời theo khoảng mới: hạn là ngày cuối khoảng mới, ngày trong nội dung đổi theo (từ 1.4.6). Ghi vào phụ lục (cam_ket_chu_dau_tu)."""
    if not uat_cu.get('den') or uat_cu == uat_moi:
        return ds_ck
    out = []
    for c in ds_ck:
        if c.get('han') == uat_cu['den']:
            c2 = dict(c, han=uat_moi['den'], noi_dung=thay_ngay_chuoi(c.get('noi_dung', ''), (uat_cu.get('tu'), uat_cu['den']), (uat_moi.get('tu'), uat_moi['den'])),
                      _nguon=f'Phụ lục hợp đồng {pl["so"]}: dời theo khoảng kiểm thử chấp nhận {loi.ngay(uat_moi.get("tu"))} đến {loi.ngay(uat_moi["den"])}')
            if not any(x['ma'] == c['ma'] for x in pl.get('cam_ket_chu_dau_tu', [])):
                pl.setdefault('cam_ket_chu_dau_tu', []).append({'ma': c['ma'], 'noi_dung': c2['noi_dung'], 'han_truoc': c['han'], 'han_moi': c2['han'],
                                                                'trong_khoang_uat': True})
            c = c2
        out.append(c)
    return out


def doi_khoang_sau_cut_over(kh, cut, ext):
    """Khoảng {tu, den} nằm sau cut over (hỗ trợ tăng cường, giai đoạn Kết thúc): bắt đầu ngày làm việc sau cut over mới, giữ số ngày
    làm việc. Trả khoảng mới hoặc None khi không có ngày hoặc đã bắt đầu sau cut over mới."""
    tu, den = loi.ngay_iso(kh.get('tu')), loi.ngay_iso(kh.get('den'))
    if not tu or not den or tu > cut:
        return None
    n = ltd.so_ngay_giua(ext, tu, den)
    tu_moi = ltd.dich(ext, cut, 1)
    return dict(kh, tu=tu_moi, den=ltd.dich(ext, tu_moi, n))


def de_xuat_chi_tieu(cr, pl, ext):
    """chi_tieu_ky_thuat.json mới: khoảng hỗ trợ tăng cường sau cut over dời theo cut over mới. None khi không cần đổi."""
    ct = doc_tho(TEP['chi_tieu'])
    ht = (ct.get('bao_hanh') or {}).get('ho_tro_tang_cuong') or {}
    moi = doi_khoang_sau_cut_over(ht, pl['cut_over_moi'], ext)
    if not moi:
        return None
    moi['_ghi_chu'] = f'Dời theo {pl["so"]} ({cr["ma"]}): bắt đầu ngày làm việc sau cut over mới {loi.ngay(pl["cut_over_moi"])}, giữ số ngày làm việc.'
    return dict(ct, bao_hanh=dict(ct['bao_hanh'], ho_tro_tang_cuong=moi))


def ngay_tu_chuoi(v):
    """Ngày ISO từ yyyy-mm-dd, dd/mm/yyyy hoặc 'dd tháng mm năm yyyy' (văn bản HSMT)."""
    m = re.search(r'(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})', str(v or ''))
    return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}' if m else loi.ngay_iso(v)


def muc_tieu_sprint_moi(cr, mn, da_moi):
    co = {x['sprint'] for x in mn.get('muc_tieu_sprint', [])}
    moi = [s['ma'] for s in loi.danh_sach_sprint(da_moi) if s['ma'] not in co]
    return [{'sprint': s, 'muc_tieu': f'Hoàn thành phần việc theo yêu cầu thay đổi {cr["ma"]} ({cr["tieu_de"]}), kiểm thử chấp nhận và chuẩn bị đưa hệ thống '
             'vào vận hành theo ngày cut over điều chỉnh', 'san_pham_demo': f'Bản phát hành gồm phần thay đổi {cr["ma"]} trên môi trường kiểm thử', 'nguon': cr['ma']}
            for s in moi]


def de_xuat_moc(cr, pl, pa, ext, k, ck, da_moi, e=0):
    mn = doc_tho(TEP['moc'])
    # ngày lập lại lịch: như khi đánh giá (ngày làm việc sau ngày CR khi đã có số liệu thực tế của chính ngày CR, lich_thay_doi.ngay_lap_lai)
    ngay_cr = (cr.get('lich_thay_doi') or {}).get('ngay_lap_lai') or cr['ngay_de_xuat']
    uat_den = (doc_tho(TEP['du_an']).get('uat') or {}).get('den', '')
    ksh = {m: ltd.dich_theo_uat(ext, d, k, e, uat_den) if d >= ngay_cr else d for m, d in (mn.get('khong_som_hon') or {}).items()}
    lui = ltd.lui_ghim_thay_doi(cr, loi.doc_json('du_lieu/lich.json'), mn.get('khong_som_hon'))  # như khi đánh giá (từ 1.4.6)
    ksh = {m: ltd.dich(ext, d, -lui.get(m, 0)) for m, d in ksh.items()}
    han_moi = {m['ma']: han_theo_phu_luc(m, ext, k + e, pa) for m in pa['moc'] if m['han_de_xuat'] != m['han']}
    # mốc có hạn sau cut over gốc (đóng dự án, giai đoạn Kết thúc) không có trong lịch đánh giá: hạn dời cùng số ngày cut over lùi
    for m in mn.get('moc', []):
        if m.get('han') and m['han'] > pa['cut_over_goc'] and m['ma'] not in han_moi and k + e:
            han_moi[m['ma']] = ltd.dich(ext, m['han'], k + e)
    moc = []
    for m in mn.get('moc', []):
        m2 = dict(m)
        if m.get('ngay') and m['ngay'] >= ngay_cr:
            m2['ngay'] = ltd.dich_theo_uat(ext, m['ngay'], k, e, uat_den)
        if m.get('han') and m['ma'] in han_moi:
            m2['han'] = han_moi[m['ma']]
        moc.append(m2)
    bn = dict(mn.get('dau_vao_ben_ngoai') or {})
    if cr.get('goi_moi'):
        bn[ck] = [g['ma'] for g in cr['goi_moi']]
    # lịch lập lại từ ngày CR: phần đã làm giữ theo lịch trước CR (lap_lich.py, scripts/lap_lai.py của qlda-master-schedule)
    mn2 = dict(mn, khong_som_hon=ksh, moc=moc, dau_vao_ben_ngoai=bn, lap_lai_tu={'ngay': ngay_cr, 'lich_goc': tep_lich_goc(cr), 'ma_cr': cr['ma']})
    return dict(mn2, muc_tieu_sprint=list(mn.get('muc_tieu_sprint', [])) + muc_tieu_sprint_moi(cr, mn, da_moi))


def tep_lich_goc(cr):
    return f'lam_viec/thay_doi/{cr["ma"]}/lich_truoc_cr.json'


def de_xuat_don_gia(cr, pl):
    dg = doc_tho(TEP['don_gia'])
    vet = list(dg.get('dieu_chinh_gia_theo_phu_luc', [])) + [{'ma_cr': cr['ma'], 'phu_luc': pl['so'], 'ngay': pl['ngay'], 'gia_truoc': dg['gia_chao_muc_tieu'],
                                                              'gia_dieu_chinh': pl['gia_dieu_chinh'], 'gia_sau': dg['gia_chao_muc_tieu'] + pl['gia_dieu_chinh']}]
    return dict(dg, gia_chao_muc_tieu=dg['gia_chao_muc_tieu'] + pl['gia_dieu_chinh'], dieu_chinh_gia_theo_phu_luc=vet)


def de_xuat_thanh_vien(pa):
    tv = doc_tho(TEP['thanh_vien'])
    co = {t['id'] for t in tv['thanh_vien']}
    return dict(tv, thanh_vien=tv['thanh_vien'] + [t for t in pa['them_nguoi']['thanh_vien'] if t['id'] not in co])


# ---------------------------------------------------------------- phụ lục, kiểm tra vết, thứ tự chạy lại
def lap_phu_luc(cr, pa, a, ext):
    """Phụ lục hợp đồng: số, ngày, giá điều chỉnh, cut over mới, mốc thanh toán điều chỉnh. Trả (phụ lục, số ngày cut over lùi, cảnh báo)."""
    so_ = (a.so_phu_luc or cr.get('van_ban') or '').strip()
    if cr.get('phu_luc_hop_dong') and not so_:
        ltd.thoat('TD19', f'{cr["ma"]} cần phụ lục hợp đồng: ghi --so-phu-luc "<số, ngày phụ lục>" hoặc --van-ban khi quyết định')
    cut = a.cut_over or pa.get('cut_over_kiem_tra') or pa['cut_over_moi']  # cut_over_kiem_tra: lịch lập lại trên dữ liệu đề xuất (từ 1.4.6)
    dt.date.fromisoformat(cut)
    k = max(0, ltd.so_ngay_giua(ext, pa['cut_over_goc'], cut))
    cb = []
    if k < pa.get('ngay_lui_cut_over_kiem_tra', pa['ngay_lui_cut_over']):
        cb.append(f'Cut over theo phụ lục {loi.ngay(cut)} sớm hơn kết quả mô phỏng {loi.ngay(pa["cut_over_moi"])}, lịch chạy lại có thể không khả thi (L01, L16)')
    gia = int(a.gia) if a.gia is not None else (int(cr.get('gia_de_nghi') or 0) if cr.get('phu_luc_hop_dong') else 0)
    cp = loi.doc_json('du_lieu/chi_phi.json', {})
    gia_truoc = int(round(cp.get('gia_chao') or loi.doc_json(TEP['don_gia'])['gia_chao_muc_tieu']))
    ngay_pl = a.ngay_phu_luc or cr.get('ngay_quyet_dinh') or cr['ngay_de_xuat']
    moc = [{'ma': m['ma'], 'ten': m['ten'], 'dot': m['dot'], 'han_truoc': m['han'], 'han_moi': han_theo_phu_luc(m, ext, k, pa), 'ngay_du_kien': m['ngay_moi']}
           for m in pa['moc'] if m['dot'] and m['han_de_xuat'] != m['han']]
    bd = cr.get('lich_thay_doi', {}).get('ngay_bat_dau_thay_doi', '')
    if cr.get('goi_moi') and bd and ngay_pl > bd:
        cb.append(f'Phụ lục ngày {loi.ngay(ngay_pl)} muộn hơn ngày bắt đầu phần thay đổi giả định khi đánh giá {loi.ngay(bd)}, lịch có thể cần lùi thêm')
    dot = doc_dot_thanh_toan(a.dot_thanh_toan, gia) if getattr(a, 'dot_thanh_toan', None) else []
    return {'so': so_, 'ngay': ngay_pl, 'gia_dieu_chinh': gia, 'gia_hop_dong_truoc': gia_truoc, 'gia_hop_dong_sau': gia_truoc + gia,
            'cut_over_truoc': pa['cut_over_goc'], 'cut_over_moi': cut, 'so_ngay_lui_cut_over': k, 'moc_thanh_toan': moc,
            'cam_ket_chu_dau_tu': cam_ket_phu_luc(pa, ext, k), 'phuong_an': pa['phuong_an'], 'dot_thanh_toan': dot,
            **({'bao_dam_thuc_hien_den': loi.ngay_iso(a.gia_han_bao_dam)} if getattr(a, 'gia_han_bao_dam', None) else {})}, k, cb


def doc_dot_thanh_toan(tep, gia):
    """Đợt thanh toán riêng của phần giá điều chỉnh: [{dot, su_kien, phan_tram_gia_dieu_chinh, moc, nguon}], tổng phần trăm bằng 100 (TD19)."""
    with open(loi.duong_dan(tep), encoding='utf-8') as f:
        ds = json.load(f)
    ds = ds.get('dot_thanh_toan', ds) if isinstance(ds, dict) else ds
    moc = {m['ma'] for m in loi.doc_json('du_lieu/lich.json', {'moc': []}).get('moc', [])}
    loi_ds = [f'đợt {d.get("dot")} thiếu {k}' for d in ds for k in ('dot', 'su_kien', 'phan_tram_gia_dieu_chinh', 'moc') if d.get(k) in (None, '')]
    loi_ds += [f'đợt {d.get("dot")} gắn mốc {d.get("moc")} không có trong lịch' for d in ds if d.get('moc') and d['moc'] not in moc]
    if ds and abs(sum(float(d.get('phan_tram_gia_dieu_chinh') or 0) for d in ds) - 100) > 1e-6:
        loi_ds.append('tổng phan_tram_gia_dieu_chinh phải bằng 100')
    if not gia:
        loi_ds.append('phụ lục không có giá điều chỉnh, không khai báo đợt thanh toán riêng')
    if loi_ds:
        ltd.thoat('TD19', 'Đợt thanh toán của phụ lục chưa hợp lệ: ' + '; '.join(loi_ds))
    return [{k: d[k] for k in ('dot', 'su_kien', 'phan_tram_gia_dieu_chinh', 'moc', 'nguon') if k in d} for d in ds]


def ghi_dot_thanh_toan(cr, a, ngay):
    """Lệnh phu_luc: ghi đợt thanh toán riêng cho phụ lục của CR đã áp dụng (quyết định của hai bên sau khi ký phụ lục)."""
    pl = cr.get('phu_luc') or {}
    if not pl:
        ltd.thoat('TD19', f'{cr["ma"]} chưa có phụ lục hợp đồng (chạy ap_dung trước)')
    if not getattr(a, 'dot_thanh_toan', None):
        ltd.thoat('TD19', 'Cần --dot-thanh-toan <tệp json>')
    pl['dot_thanh_toan'] = doc_dot_thanh_toan(a.dot_thanh_toan, pl.get('gia_dieu_chinh', 0))
    pl.setdefault('lich_su', []).append({'ngay': ngay, 'ghi_luc': loi.bay_gio(), 'noi_dung': 'Ghi đợt thanh toán riêng của phần giá điều chỉnh',
                                         'dot_thanh_toan': pl['dot_thanh_toan']})
    return pl


def canh_bao_ngay_khoa(pl, ext):
    """TD25: hiệu lực bảo đảm thực hiện hợp đồng (HSMT đã khóa) sớm hơn ngày đóng dự án mới (cut over mới cộng giai đoạn Kết thúc)."""
    hl = ngay_tu_chuoi((loi.doc_json('du_lieu/hsmt.json', {}).get('thoi_han') or {}).get('hieu_luc_bao_dam_thuc_hien_den'))
    so_kt = int(((loi.du_an().get('giai_doan') or {}).get('ket_thuc') or {}).get('so_ngay_lam_viec') or loi.SO_NGAY_KET_THUC_MAC_DINH)
    dong = ltd.dich(ext, pl['cut_over_moi'], so_kt)
    if pl.get('bao_dam_thuc_hien_den'):  # phụ lục ghi gia hạn bảo đảm thực hiện (--gia-han-bao-dam, từ 1.4.6)
        return [] if pl['bao_dam_thuc_hien_den'] >= dong else [
            f'TD25 Phụ lục {pl["so"]} gia hạn bảo đảm thực hiện đến {loi.ngay(pl["bao_dam_thuc_hien_den"])}, vẫn sớm hơn ngày đóng dự án dự kiến {loi.ngay(dong)}']
    if hl and hl < dong:
        return [f'TD25 Hiệu lực bảo đảm thực hiện hợp đồng theo HSMT đến {loi.ngay(hl)}, sớm hơn ngày đóng dự án dự kiến {loi.ngay(dong)} '
                f'sau cut over mới. Ghi gia hạn bảo đảm thực hiện trong {pl["so"]} hoặc văn bản thỏa thuận']
    return []


def cam_ket_phu_luc(pa, ext, k):
    """Cam kết của Chủ đầu tư có hạn sau ngày CR dời theo cut over (khi gói nhận đầu vào bắt đầu sau hạn mới), số ngày dời là phần đến hết
    khoảng uat gốc."""
    k0 = max(0, k - pa.get('uat_keo_dai', 0) - pa.get('sau_uat_keo_dai', 0))
    return [dict(c, han_moi=ltd.dich(ext, c['han_truoc'], k0)) for c in pa.get('cam_ket', []) if k0]


def han_theo_phu_luc(m, ext, k, pa):
    """Hạn mới của mốc vượt hạn: hạn đề xuất khi đánh giá, cut over theo phụ lục khác kết quả đánh giá thì dời thêm phần chênh
    (mốc gắn cut over và mốc không gắn đợt thanh toán, vì khoảng kiểm thử chấp nhận và ngày ghim cũng dời theo phần chênh)."""
    lech = k - pa['ngay_lui_cut_over']
    return ltd.dich(ext, m['han_de_xuat'], lech) if lech > 0 and (m.get('gan_cut_over') or not m.get('dot')) else m['han_de_xuat']


def gia_tri_vet(obj, duong):
    try:
        return loi.lay(obj, duong)
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def co_vet(v, chua):
    if isinstance(v, dict):
        return chua in v
    if isinstance(v, list):
        return any((x.get('ma_cr') == chua or x.get('ma') == chua or x.get('id') == chua) if isinstance(x, dict) else x == chua for x in v)
    return v == chua


def nguon_chua_ap_dung(cr):
    """Vết áp dụng chưa có trong dữ liệu nguồn hiện tại (tệp, đường dẫn, giá trị cần có)."""
    out = []
    for x in (cr.get('ap_dung') or {}).get('kiem_tra', []):
        p = loi.duong_dan(x['tep'])
        obj = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
        if not co_vet(gia_tri_vet(obj, x['duong']), x['chua']):
            out.append(f'{x["tep"]} ({x["duong"]} chưa có {x["chua"]})')
    return out


def can_duong_co_so(cr):
    """CR đổi đường cơ sở hợp đồng (phụ lục hoặc mức lớn) cần đường cơ sở mới sau thay đổi trước khi đóng."""
    return bool(cr.get('phu_luc_hop_dong') or cr.get('muc') == 'lon')


def ma_duong_co_so_moi():
    so_ = [int(x['ma'][2:]) for x in loi.doc_json('du_lieu/phien_ban.json', {}).get('duong_co_so', []) if str(x.get('ma', ''))[2:].isdigit()]
    return f'BL{max(so_ + [1]) + 1}'


def co_duong_co_so(cr):
    return any(x.get('ma_cr') == cr['ma'] for x in loi.doc_json('du_lieu/phien_ban.json', {}).get('duong_co_so', []))


def thu_tu_chay_lai(cr, ngay):
    """Lệnh chạy lại theo thứ tự tai_lieu_cap_nhat. Đường cơ sở mới (CR có phụ lục hoặc mức lớn) lập sau các tài liệu kế hoạch,
    trước tài liệu quản lý phiên bản để tài liệu này ghi nhận đường cơ sở mới."""
    buoc = [s_.split(' ')[0] for s_ in cr.get('tai_lieu_cap_nhat', []) if '/' not in s_.split(' ')[0]]
    sau = [b for b in buoc if b in LENH.get('sau_duong_co_so', [])] if can_duong_co_so(cr) else []
    lenh = lambda ds: [l_.format(ma=cr['ma'], ngay=ngay, buoc=b) for b in ds for l_ in LENH['buoc'].get(b, LENH['mac_dinh'])]  # noqa: E731
    out = lenh([b for b in buoc if b not in sau])
    if can_duong_co_so(cr):
        out += [l_.format(ma=cr['ma'], ngay=ngay, bl=ma_duong_co_so_moi()) for l_ in LENH['duong_co_so']]
    return out + lenh(sau)


def vet_kiem_tra(cr, de_xuat, ck, pa):
    k_ = []
    if TEP['wbs'] in de_xuat:
        k_ += [{'tep': TEP['wbs'], 'duong': 'goi.ma', 'chua': g['ma']} for g in cr.get('goi_moi', [])]
        k_ += [{'tep': TEP['wbs'], 'duong': f'goi[ma={x["ma"]}].nguon', 'chua': cr['ma']} for x in cr.get('goi_thay_doi', [])]
    if TEP['uoc_luong'] in de_xuat:
        k_.append({'tep': TEP['uoc_luong'], 'duong': 'cac_buoc', 'chua': cr['ma']})
    if TEP['giao_viec'] in de_xuat:
        k_ += [{'tep': TEP['giao_viec'], 'duong': 'giao_viec.ma', 'chua': x['ma']} for x in pa['giao_viec_de_xuat']]
    if TEP['du_an'] in de_xuat:
        k_.append({'tep': TEP['du_an'], 'duong': 'dieu_chinh_theo_cr', 'chua': cr['ma']})
    if TEP['moc'] in de_xuat and cr.get('goi_moi'):
        k_.append({'tep': TEP['moc'], 'duong': 'dau_vao_ben_ngoai', 'chua': ck})
    if TEP['don_gia'] in de_xuat:
        k_.append({'tep': TEP['don_gia'], 'duong': 'dieu_chinh_gia_theo_phu_luc', 'chua': cr['ma']})
    if TEP['thanh_vien'] in de_xuat:
        k_ += [{'tep': TEP['thanh_vien'], 'duong': 'thanh_vien.id', 'chua': t['id']} for t in pa['them_nguoi']['thanh_vien']]
    if TEP['chi_tieu'] in de_xuat:
        k_.append({'tep': TEP['chi_tieu'], 'duong': 'bao_hanh.ho_tro_tang_cuong.tu', 'chua': de_xuat[TEP['chi_tieu']]['bao_hanh']['ho_tro_tang_cuong']['tu']})
    return k_


def mo_ta_thay_doi(cr, pl, k, ck, de_xuat, keo):
    """Mô tả ngắn thay đổi của từng tệp nguồn, de_xuat là {đường dẫn: nội dung mới}."""
    md = sum(md_theo_nhom(cr).values())
    m = {TEP['wbs']: f'Thêm {len(cr.get("muc_moi", []))} mục, {len(cr.get("goi_moi", []))} gói mới, '
                     f'{sum(1 for x in cr.get("goi_thay_doi", []) if float(x.get("md_tang", 0)))} gói tăng MD, '
                     f'{sum(1 for x in cr.get("goi_thay_doi", []) if not float(x.get("md_tang", 0)))} gói thêm phụ thuộc, nguồn ghi {cr["ma"]}',
         TEP['uoc_luong']: f'tong_md cộng {loi.so(md, 2)} MD, tong_theo_nhom cộng theo nhóm {", ".join(sorted(md_theo_nhom(cr)))}, thêm bước ước lượng ghi {cr["ma"]}',
         TEP['giao_viec']: 'Giao việc gói mới: ' + ', '.join(f'{x["ma"]} {x["R"]}' for x in cr['lich_thay_doi'][pl['phuong_an']]['giao_viec_de_xuat'])
         + ''.join(f'; {x["ma"]} thêm hỗ trợ {", ".join(x["them"])}' for x in cr['lich_thay_doi'][pl['phuong_an']].get('ho_tro_goi_thay_doi', []))
         + '; trách nhiệm của mục mới mức 1, 2' + (f'; gói dàn trải {", ".join(keo)} kéo đến sprint cuối mới' if keo else ''),
         TEP['du_an']: f'ngay_cut_over {loi.ngay(pl["cut_over_truoc"])} thành {loi.ngay(pl["cut_over_moi"])}, khoảng uat '
         + ', '.join(f'{x} {loi.ngay(y)}' for x, y in (de_xuat.get(TEP['du_an'], {}).get('uat') or {}).items())
         + ''.join(f', hạn {c["ma"]} {loi.ngay(c["han_truoc"])} thành {loi.ngay(c["han_moi"])}' for c in pl.get('cam_ket_chu_dau_tu', []))
         + (f', thêm cam kết {ck} (phụ lục có hiệu lực ngày {loi.ngay(pl["ngay"])})' if cr.get('goi_moi') else '') + ', sprint.cut_over_goc giữ các sprint đã qua',
         TEP['moc']: f'Ràng buộc không sớm hơn và mốc ngày cố định từ {loi.ngay(cr["ngay_de_xuat"])} dời theo cut over ({k} ngày), hạn mốc theo phụ lục: '
         + (', '.join(f'{x["ma"]} {loi.ngay(x["han_moi"])}' for x in pl['moc_thanh_toan']) or 'không đổi') + (f', gói mới gắn {ck}' if cr.get('goi_moi') else '')
         + f', lập lại lịch từ {loi.ngay((cr.get("lich_thay_doi") or {}).get("ngay_lap_lai") or cr["ngay_de_xuat"])} (lap_lai_tu)',
         TEP['don_gia']: f'gia_chao_muc_tieu cộng {loi.tien(pl["gia_dieu_chinh"])} đồng theo {pl["so"]}',
         TEP['thanh_vien']: 'Thêm người theo phương án thêm nhân sự',
         TEP['chi_tieu']: 'bao_hanh.ho_tro_tang_cuong ' + ' đến '.join(loi.ngay(x) for x in (
             (de_xuat.get(TEP['chi_tieu']) or {}).get('bao_hanh', {}).get('ho_tro_tang_cuong', {}).get(y, '') for y in ('tu', 'den')))
         + ' (bắt đầu sau cut over mới, giữ số ngày làm việc)'}
    return [{'tep': p, 'de_xuat': f'lam_viec/thay_doi/{cr["ma"]}/de_xuat/{p}', 'thay_doi': m[p]} for p in de_xuat]


BUOC_KIEM_TRA = (('qlda-wbs', 'kiem_tra_wbs.py', TEP['wbs']), ('qlda-phan-cong', 'kiem_tra_giao_viec.py', TEP['giao_viec']),
                 ('qlda-master-schedule', 'lap_lich.py', TEP['moc']))
TEP_SAO_KIEM_TRA = ('du_lieu/hsmt.json', 'du_lieu/rfp_yeu_cau.json', 'du_lieu/wbs.json', 'du_lieu/phan_cong.json', 'du_lieu/lich.json',
                    'du_lieu/phien_ban.json', TEP['wbs'], TEP['giao_viec'], TEP['moc'])


def kiem_tra_lap_lai(de_xuat, lich_goc, lich_goc_tam=None, tra_lich=False):
    """Chạy kiem_tra_wbs, kiem_tra_giao_viec, lap_lich (lập lại từ ngày CR) trên bản sao có dữ liệu đề xuất (thư mục tạm),
    trả lỗi của bước đầu tiên chưa đạt. lich_goc_tam: tệp lịch gốc chép vào đường dẫn lich_goc của bản sao (khi đánh giá, lịch gốc chưa lưu)."""
    tmp = tempfile.mkdtemp(prefix='qlda_ap_dung_')
    try:
        shutil.copytree(loi.duong_dan('dau_vao'), os.path.join(tmp, 'dau_vao'))
        for p in TEP_SAO_KIEM_TRA + (lich_goc,):
            if os.path.exists(loi.duong_dan(p)):
                os.makedirs(os.path.dirname(os.path.join(tmp, p)), exist_ok=True)
                shutil.copy(loi.duong_dan(p), os.path.join(tmp, p))
        if lich_goc_tam:
            os.makedirs(os.path.dirname(os.path.join(tmp, lich_goc)), exist_ok=True)
            shutil.copy(lich_goc_tam, os.path.join(tmp, lich_goc))
        for p, obj in de_xuat.items():
            os.makedirs(os.path.dirname(os.path.join(tmp, p)), exist_ok=True)
            with open(os.path.join(tmp, p), 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False, indent=1)
        env = dict(os.environ, QLDA_GOC=tmp, PYTHONUTF8='1')
        for skill, tep, nhap in BUOC_KIEM_TRA:
            r = subprocess.run([sys.executable, os.path.join(loi.THU_MUC_SKILLS, skill, 'scripts', tep), nhap], capture_output=True, text=True,
                               encoding='utf-8', errors='replace', cwd=tmp, env=env)
            if r.returncode:
                ds = [x for x in r.stdout.splitlines() if x.startswith('[loi]') or x.startswith('LỖI')]
                loi_ = [f'{tep}: ' + x for x in (ds or [r.stdout.strip()[-300:]])[:6]]
                return (loi_, lich_tam(tmp)) if tra_lich else loi_
        return ([], lich_tam(tmp)) if tra_lich else []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def lap_de_xuat(cr, pa, a, ext, vai=None):
    """Phụ lục và dữ liệu nguồn đề xuất của CR theo phương án pa, không ghi tệp. Dùng chung cho ap_dung và kiem_tra_cut_over (từ 1.4.6).
    Trả (phụ lục, k, cảnh báo, mã cam kết mới, de_xuat, gói dàn trải kéo dài)."""
    pl, k, cb = lap_phu_luc(cr, pa, a, ext)
    ck = ma_cam_ket_moi(doc_tho(TEP['du_an']))
    co_md = bool(md_theo_nhom(cr))
    de_xuat = {}
    if co_md:
        de_xuat[TEP['wbs']] = de_xuat_wbs(cr, pl)
        de_xuat[TEP['uoc_luong']] = de_xuat_uoc_luong(cr, pl)
    da_moi = loi.du_an()
    e = min(k, pa.get('uat_keo_dai', 0))  # cut over lùi k ngày: các ngày đến hết khoảng uat gốc dời k - e - g, sau khoảng dời k
    g = min(k - e, pa.get('sau_uat_keo_dai', 0))  # khoảng sau uat kéo dài g ngày (từ 1.4.6)
    if k or cr.get('goi_moi'):
        de_xuat[TEP['du_an']] = de_xuat_du_an(cr, pl, ext, k - e - g, ck, e)
        da_moi = loi.gan_don_vi_thuc_hien(de_xuat[TEP['du_an']])
        pl['uat'] = {'truoc': doc_tho(TEP['du_an']).get('uat') or {}, 'moi': de_xuat[TEP['du_an']].get('uat') or {}}
        de_xuat[TEP['moc']] = de_xuat_moc(cr, pl, pa, ext, k - e - g, ck, da_moi, e + g)
    keo = keo_dan_trai(doc_tho(TEP['giao_viec'])['giao_viec'], loi.du_an(), da_moi)[1]
    if cr.get('goi_moi') or (pa.get('them_nguoi') or {}).get('giao_viec') or pa.get('ho_tro_goi_thay_doi') or keo:
        de_xuat[TEP['giao_viec']] = de_xuat_giao_viec(cr, pa, vai, da_moi)
    if pl['gia_dieu_chinh']:
        de_xuat[TEP['don_gia']] = de_xuat_don_gia(cr, pl)
    if pa.get('them_nguoi'):
        de_xuat[TEP['thanh_vien']] = de_xuat_thanh_vien(pa)
    if k:
        ct_moi = de_xuat_chi_tieu(cr, pl, ext)
        if ct_moi:
            de_xuat[TEP['chi_tieu']] = ct_moi
        cb += canh_bao_ngay_khoa(pl, ext)
    return pl, k, cb, ck, de_xuat, keo


MAU_VUOT = re.compile(r'L01 .*?sau ngày cut over \S+ (\d+) ngày làm việc')


def kiem_tra_cut_over(cr, pa, ngay_phu_luc, vai=None, so_vong=6):
    """Ngày cut over khả thi trên đúng dữ liệu đề xuất của bước áp dụng (lịch lập lại có dàn trải kéo dài, cam kết phụ lục, sprint mới), bắt đầu từ
    kết quả mô phỏng của bước đánh giá, lùi thêm phần vượt L01 đến khi lịch không vượt cut over. Bước đánh giá ghi kết quả này để số ngày cut over
    lùi của đánh giá và của áp dụng khớp nhau (từ 1.4.6). Trả {cut_over, ngay_lui, them, loi_con_lai}."""
    import types
    _, ext = ltd.ngay_mo_rong(loi.du_an())
    cut, them, lap, lich_kt = pa['cut_over_moi'], 0, [], {}
    tmp = tempfile.mkdtemp(prefix='qlda_kt_cut_')
    try:
        goc = os.path.join(tmp, 'lich_goc.json')
        shutil.copy(loi.duong_dan('du_lieu/lich.json'), goc)
        for _ in range(so_vong):
            a = types.SimpleNamespace(cut_over=cut, so_phu_luc=f'phụ lục dự kiến của {cr["ma"]}', ngay_phu_luc=ngay_phu_luc, gia=None, dot_thanh_toan=None)
            _, _, _, _, de_xuat, _ = lap_de_xuat(cr, dict(pa, cut_over_kiem_tra=None), a, ext, vai)
            if TEP['moc'] not in de_xuat:
                break
            lap, lich_kt = kiem_tra_lap_lai(de_xuat, tep_lich_goc(cr), lich_goc_tam=goc, tra_lich=True)
            v = max([int(m_.group(1)) for x in lap for m_ in [MAU_VUOT.search(x)] if m_] + [0])
            if not v:
                break
            cut, them = ltd.dich(ext, cut, v), them + v
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {'cut_over': cut, 'ngay_lui': max(0, ltd.so_ngay_giua(ext, pa['cut_over_goc'], cut)), 'them': them,
            'loi_con_lai': [x for x in lap if not MAU_VUOT.search(x)], 'moc': {m['ma']: m['ngay'] for m in lich_kt.get('moc', [])}}


def lich_tam(tmp):
    """Lịch của bản sao kiểm tra: lịch dự thảo khi lap_lich.py còn lỗi, không thì du_lieu/lich.json vừa lập."""
    for p in ('lam_viec/lich/lich_du_thao.json', 'du_lieu/lich.json'):
        if os.path.exists(os.path.join(tmp, p)):
            with open(os.path.join(tmp, p), encoding='utf-8') as f:
                return json.load(f)
    return {}


def ap_dung(cr, a, ngay, vai):
    """Sinh đề xuất thay đổi dữ liệu nguồn, ghi phụ lục, ghi thẳng khi a.ghi. Trả (bản ghi áp dụng, cảnh báo)."""
    if cr['trang_thai'] != 'Đã phê duyệt':
        ltd.thoat('TD19', f'{cr["ma"]} đang ở trạng thái {cr["trang_thai"]}, chỉ áp dụng yêu cầu đã phê duyệt (quyet_dinh --ket-qua "Đã phê duyệt")')
    if (cr.get('ap_dung') or {}).get('da_ghi'):
        ltd.thoat('TD19', f'{cr["ma"]} đã áp dụng vào dữ liệu nguồn ngày {loi.ngay(cr["ap_dung"]["ngay"])}, không áp dụng lại')
    if not cr.get('lich_thay_doi'):
        ltd.thoat('TD19', f'{cr["ma"]} được đánh giá bằng phiên bản cũ, chưa có kết quả đưa vào lịch. Đánh giá lại bằng danh_gia')
    pa = cr['lich_thay_doi'][cr.get('phuong_an_chon') or 'hien_tai']
    _, ext = ltd.ngay_mo_rong(loi.du_an())
    pl, k, cb, ck, de_xuat, keo = lap_de_xuat(cr, pa, a, ext, vai)
    shutil.copy(loi.duong_dan('du_lieu/lich.json'), loi.duong_dan(tep_lich_goc(cr)))  # lịch gốc của chế độ lập lại từ ngày CR
    lap_lai = kiem_tra_lap_lai(de_xuat, tep_lich_goc(cr))
    if lap_lai:
        cb.append('TD24 Lịch lập lại từ ngày CR bằng lap_lich.py với dữ liệu đề xuất chưa đạt: ' + '; '.join(lap_lai)
                  + '. Điều chỉnh giao việc gói mới (R, ho_tro trong phiếu hoặc phương án), --cut-over, hoặc sửa sau khi ghi')
    for p, obj in de_xuat.items():
        loi.ghi_json(f'lam_viec/thay_doi/{cr["ma"]}/de_xuat/{p}', obj)
        if a.ghi:
            loi.ghi_json(p, obj)
    bang = mo_ta_thay_doi(cr, pl, k, ck, de_xuat, keo)
    rec = {'ngay': ngay, 'ghi_luc': loi.bay_gio(), 'da_ghi': bool(a.ghi), 'phuong_an': pa['phuong_an'], 'tep': bang,
           'kiem_tra': vet_kiem_tra(cr, de_xuat, ck, pa), 'thu_tu_chay_lai': thu_tu_chay_lai(cr, ngay), 'canh_bao': cb}
    loi.ghi_json(f'lam_viec/thay_doi/{cr["ma"]}/thay_doi_du_lieu.json', {'ma': cr['ma'], 'phu_luc': pl, **rec})
    return pl, rec
