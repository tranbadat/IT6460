"""Sinh công thực tế theo ngày cho một sprint, bám kế hoạch hiện hành (du_lieu/lich.json goi[].phan_nguoi, bat_dau, ket_thuc, phu_thuoc).

Quy tắc phân công theo ngày:
- Công cần của người p trên gói g = phan_nguoi[p] x hệ số gói + MD phát sinh (rủi ro, sửa lỗi) chia theo tỷ trọng phan_nguoi.
  Hệ số gói = (1 + tổng ty_le_md của biến cố gói) hoặc, khi gói không có biến cố, 1 + nhiễu ngẫu nhiên trong +-nhieu_md theo hạt giống.
- Cửa sổ làm của gói là [bat_dau, ket_thuc] kế hoạch, lùi theo số ngày trễ của biến cố (so_ngay_tre, ngay_tac_dong của rủi ro).
- Gói chỉ được làm khi đã đến ngày bắt đầu của cửa sổ và mọi gói tiền nhiệm đã hoàn thành trước ngày đó (đủ phụ thuộc).
- Mỗi ngày người p làm tối đa ty_le MD (thanh_vien.json), chỉ trong sprint được huy động (lich.json phan_bo quy > 0), trừ ngày nghỉ.
  Công dồn tới mức kế hoạch lũy kế tuyến tính theo cửa sổ (làm bù khi chậm), ưu tiên gói có ngày kết thúc muộn nhất (cuối cửa sổ cộng dự trữ) sớm hơn. Gói hụt công xong
  sớm hơn kế hoạch, gói vượt công làm phần vượt sau ngày cuối cửa sổ. Ngày còn quỹ mà không có việc đến lịch là ngày sẵn sàng
  không ghi công.
- Công ghi theo bội số don_vi_md (0,25 MD). Gói hoàn thành khi mọi người đủ công cần, ngày hoàn thành là ngày ghi công cuối.
"""
import math
import random

import mp_chung as C


def tron_q(md, q):
    return int(round(float(md) * q))


class MoPhongLich:
    def __init__(self, ctx, ma_sp, tac_dong, nghi, nk_cu, ht_cu, hat_giong, nhieu):
        """tac_dong: {mã gói: {'ty_le': tổng ty_le_md, 'md_them': MD, 'tre': ngày, 'co_bien_co': bool}};
        nghi: tập (id, date); nk_cu, ht_cu: dòng nhật ký, hoàn thành đã có."""
        self.ctx, self.sp = ctx, ma_sp
        self.Q = int(round(1 / float(C.cau_hinh()['don_vi_md'])))
        self.ngay = ctx.ngay_sprint(ma_sp)
        self.tac_dong, self.nghi, self.seed, self.nhieu = tac_dong, nghi, hat_giong, float(nhieu)
        self.done = {}
        for r in nk_cu:
            k = (r['thanh_vien'], r['ma_goi'])
            self.done[k] = self.done.get(k, 0) + tron_q(r['md'], self.Q)
        self.xong, self.pt_cu = {}, {}
        for r in sorted(ht_cu, key=lambda r: r['ngay_cap_nhat']):
            v = float(r['phan_tram'])
            self.pt_cu[r['ma_goi']] = max(v, self.pt_cu.get(r['ma_goi'], 0))
            if v >= 100 and r['ma_goi'] not in self.xong:
                self.xong[r['ma_goi']] = C.D(r['ngay_cap_nhat'])
        self.need = self._cong_can()
        self.cua_so = {g: self._cua_so(g) for g in ctx.goi}
        self._ket_thuc_muon = {}

    def he_so(self, g):
        t = self.tac_dong.get(g, {})
        if t.get('co_bien_co'):
            return 1 + float(t.get('ty_le', 0))
        r = random.Random(f'{self.seed}:{g}')
        return 1 + round(r.uniform(-self.nhieu, self.nhieu), 3)

    def _cong_can(self):
        out = {}
        for g, x in self.ctx.goi.items():
            pn = {p: float(m) for p, m in (x.get('phan_nguoi') or {}).items() if float(m) > 0}
            tong = sum(pn.values())
            if not tong:
                continue
            hs, them = self.he_so(g), float(self.tac_dong.get(g, {}).get('md_them', 0))
            ds = list(pn)
            # chia theo phần dư lớn nhất để tổng công cần của gói đúng bội số don_vi_md gần nhất (không cộng dồn sai số làm tròn từng người)
            q = C.loi.lam_tron_tong([(pn[p] * hs + them * pn[p] / tong) * self.Q for p in ds], 0)
            for p, v in zip(ds, q):
                out[(p, g)] = max(1, int(v))
        return out

    def _cua_so(self, g):
        x, tre = self.ctx.goi[g], int(self.tac_dong.get(g, {}).get('tre', 0))
        a = self.ctx.cong_ngay_lam_viec(x['bat_dau'], tre)
        b = self.ctx.cong_ngay_lam_viec(x['ket_thuc'], tre)
        n = sum(1 for d in self.ctx.days if a <= d <= b) or 1
        return a, b, n

    def frac(self, g, d):
        a, b, n = self.cua_so[g]
        return min(1.0, sum(1 for x in self.ctx.days if a <= x <= min(b, d)) / n)

    def uu_tien(self, g):
        """Thứ tự làm trong ngày: ngày kết thúc muộn nhất (cuối cửa sổ cộng dự trữ du_tru_cpm) sớm hơn, gói găng trước."""
        x = self.ctx.goi[g]
        if g not in self._ket_thuc_muon:
            self._ket_thuc_muon[g] = self.ctx.cong_ngay_lam_viec(self.cua_so[g][1], int(x.get('du_tru_cpm') or 0))
        return self._ket_thuc_muon[g], not x.get('gang'), self.cua_so[g][1], C.loi.khoa_ma(g)

    def muc_tieu(self, k, d):
        """Công lũy kế cần đạt cuối ngày d: theo nhịp kế hoạch (phan_nguoi tuyến tính trên cửa sổ), gói hụt công xong sớm hơn;
        từ ngày cuối cửa sổ là toàn bộ công cần, gói vượt công làm bù bằng quỹ còn lại."""
        p, g = k
        if d >= self.cua_so[g][1]:
            return self.need[k]
        ke_hoach = float(self.ctx.goi[g]['phan_nguoi'][p]) * self.Q
        return min(self.need[k], math.ceil(ke_hoach * self.frac(g, d) - 1e-9))

    def du_phu_thuoc(self, g, d):
        for p in self.ctx.goi[g].get('phu_thuoc', []):
            for la in self.ctx.la_cua(p):
                if la not in self.xong or self.xong[la] >= d:
                    return False
        return True

    def cap(self, p, d):
        if (p, d) in self.nghi or not self.ctx.quy.get((p, self.sp)):
            return 0
        return int(round(self.Q * float(self.ctx.tv[p].get('ty_le', 1.0))))

    def chay(self):
        """Trả về (dòng nhật ký mới, {gói: ngày hoàn thành mới}, dòng hoàn thành mới, thống kê)."""
        rows, xong_moi = [], {}
        theo_nguoi = {}
        for p in self.ctx.tv:
            for g in [g for (q, g) in self.need if q == p]:
                theo_nguoi.setdefault(p, []).append(g)
        cham_vi_khong_huy_dong = set()
        # quỹ huy động của người trong kỳ (lich.json phan_bo, gồm huy động theo nhu cầu ty_le_theo_sprint của thanh_vien.json): tổng công
        # ghi trong kỳ không vượt quỹ (MP05), tốc độ mỗi ngày vẫn theo ty_le (từ 1.0.4)
        con_ky = {p: int(round(float(self.ctx.quy.get((p, self.sp), 0)) * self.Q)) for p in theo_nguoi}
        for d in self.ngay:
            cham_hom_nay = set()
            for p, ds in theo_nguoi.items():
                con = min(self.cap(p, d), con_ky[p])
                ung_vien = [g for g in ds if g not in self.xong and self.done.get((p, g), 0) < self.need[(p, g)]
                            and d >= self.cua_so[g][0] and self.du_phu_thuoc(g, d)]
                if ung_vien and not self.ctx.quy.get((p, self.sp)):
                    cham_vi_khong_huy_dong.update((p, g) for g in ung_vien)
                for g in sorted(ung_vien, key=self.uu_tien):
                    if con <= 0:
                        break
                    k = (p, g)
                    muc = self.muc_tieu(k, d)
                    giao = min(max(0, muc - self.done.get(k, 0)), con)
                    if giao:
                        self.done[k] = self.done.get(k, 0) + giao; con -= giao; con_ky[p] -= giao
                        rows.append({'ngay': d.isoformat(), 'thanh_vien': p, 'ma_goi': g, 'md': giao / self.Q, 'ghi_chu': ''})
                        cham_hom_nay.add(g)
            for g in cham_hom_nay:
                if all(self.done.get((p, g), 0) >= n for (p, gg), n in self.need.items() if gg == g):
                    self.xong[g] = d; xong_moi[g] = d
        return rows, xong_moi, self._hoan_thanh(rows, xong_moi), {'khong_huy_dong': sorted(cham_vi_khong_huy_dong)}

    def phan_tram(self, g):
        n = sum(v for (p, gg), v in self.need.items() if gg == g)
        dn = sum(min(self.done.get((p, g), 0), v) for (p, gg), v in self.need.items() if gg == g)
        return 100 if g in self.xong else min(99, math.floor(100 * dn / n)) if n else 0

    def _hoan_thanh(self, rows, xong_moi):
        out, cham = [], {r['ma_goi'] for r in rows}
        den = self.ngay[-1].isoformat()
        for g in sorted(cham, key=C.loi.khoa_ma):
            if g in xong_moi:
                out.append({'ngay_cap_nhat': xong_moi[g].isoformat(), 'ma_goi': g, 'phan_tram': 100, 'ghi_chu': 'Hoàn thành'})
                continue
            v = self.phan_tram(g)
            if v > self.pt_cu.get(g, 0):
                out.append({'ngay_cap_nhat': den, 'ma_goi': g, 'phan_tram': v, 'ghi_chu': f'Cập nhật cuối sprint {self.sp}'})
        return out

    def spi_uoc_tinh(self):
        """SPI theo MD tại ngày cuối kỳ, cùng cách tính PV, EV với tinh_tien_do.py (để agent điều chỉnh mức biến cố)."""
        den, pv, ev = self.ngay[-1], 0.0, 0.0
        for g, x in self.ctx.goi.items():
            a, b = C.D(x['bat_dau']), C.D(x['ket_thuc'])
            tot = sum(1 for d in self.ctx.days if a <= d <= b) or 1
            pv += float(x['md']) * sum(1 for d in self.ctx.days if a <= d <= min(b, den)) / tot
            ev += float(x['md']) * self.phan_tram(g) / 100
        return round(ev / pv, 3) if pv else 0

    def goi_cham(self, nguong):
        """Gói chậm tại ngày cuối sprint, cùng cách tính với tinh_tien_do.py (tỷ lệ kế hoạch theo cửa sổ kế hoạch gốc)."""
        den, out = self.ngay[-1], []
        for g, x in self.ctx.goi.items():
            a, b = C.D(x['bat_dau']), C.D(x['ket_thuc'])
            tot = sum(1 for d in self.ctx.days if a <= d <= b) or 1
            f = sum(1 for d in self.ctx.days if a <= d <= min(b, den)) / tot
            e = self.phan_tram(g) / 100 if (g in self.xong or any(gg == g and v for (p, gg), v in self.done.items())) else 0
            if f > 0 and e < 1 and e - f < -nguong:
                out.append({'ma': g, 'ke_hoach': round(f, 4), 'thuc_te': round(e, 4), 'ket_thuc_ke_hoach': x['ket_thuc'], 'gang': bool(x.get('gang'))})
        return out
