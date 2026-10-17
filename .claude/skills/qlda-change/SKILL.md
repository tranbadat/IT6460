---
name: qlda-change
description: Lập kế hoạch quản lý thay đổi (change management plan) và vận hành quy trình yêu cầu thay đổi (CR) - phân loại theo điểm tác động 1 đến 10 và điều kiện hợp đồng (cut over, mốc thanh toán, đặc tả đã xác nhận, phạm vi, giá), ban kiểm soát thay đổi có người ký phụ lục của hai bên, thời hạn đánh giá và quyết định, chi phí nội bộ và giá đề nghị Chủ đầu tư, mốc bị ảnh hưởng, tài liệu phải cập nhật theo sơ đồ phụ thuộc, mẫu phiếu CR, quản lý cấu hình, thay đổi về con người, quy tắc dùng dự phòng dùng chung, quyết định, kiểm tra đạt và đóng CR (cả nhánh từ chối, hoãn). Dùng khi người dùng muốn lập kế hoạch quản lý thay đổi, ghi hoặc đánh giá một yêu cầu thay đổi, phê duyệt, đóng CR.
---

# Quản lý thay đổi

Đầu vào kế hoạch: du_lieu/hsmt.json, rfp_yeu_cau.json, wbs.json, lich.json, phan_cong.json, chi_phi.json, rui_ro.json, hsdt_bang.json (tùy chọn), ket_qua/02_HSDT/HSDT.docx, dau_vao/nha_thau.json (dai_dien, chuc_vu_dai_dien), chi_tieu_ky_thuat.json (thoi_han_danh_gia_thay_doi_ngay), du_an.json (thoi_gian_phe_duyet_tai_lieu_ngay, uat), don_gia.json, thanh_vien.json.

Quy tắc trong `references/`:
- `phan_loai.json`: ba mức với khoảng điểm 1-3, 4-7, 8-10, ngưỡng MD, chi phí nội bộ, tiêu hao dự trữ, chậm cut over (bằng 0 ở mức nhỏ và trung bình khi cut_over_co_dinh), phạm vi áp dụng (mức nhỏ chỉ cho thay đổi nội bộ), thẩm quyền theo vai, thời hạn đánh giá (theo cam kết trong chi_tieu_ky_thuat.json khi có) và quyết định (theo du_an.json khi có), điều kiện buộc mức kèm căn cứ HSMT, cách tính giá đề nghị, nhánh đóng, quy tắc dùng dự phòng (nguồn chung cho kế hoạch rủi ro, thuyết minh dự toán, master plan).
- `mau_phieu_cr.json`: trường của phiếu yêu cầu thay đổi.

Script: `scripts/quy_tac_thay_doi.py` (dùng chung), `tinh_bang_thay_doi.py`, `yeu_cau_thay_doi.py`. Mã kiểm tra TD01 đến TD17 (lỗi dừng, cảnh báo in), xem đầu mỗi script.

## Kế hoạch (ke_hoach_thay_doi)

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi ke_hoach_thay_doi`
   Tự chạy scripts/tinh_bang_thay_doi.py, ra du_lieu/thay_doi_bang.json: phân loại, điều kiện, thẩm quyền và thời hạn, ban kiểm soát thay đổi, lan truyền, mẫu phiếu, nhánh đóng, quy tắc dự phòng, hạng mục cấu hình, sổ thay đổi, vai_ban (họ tên theo vai, master plan dùng).
   Ban kiểm soát gồm quản trị dự án, người đại diện ký hợp đồng của nhà thầu, đầu mối và người có thẩm quyền của Chủ đầu tư (phan_cong ben_ngoai, thiếu thì lấy Mục 4.1, 1.3 E-ĐKCT). Dừng (TD08) khi mức đòi phụ lục hợp đồng mà một bên không có người ký được.
2. Agent Soạn thảo viết bản soạn: căn cứ, vai trò và quy tắc quyết định, quy trình, tác động, cấu hình, thay đổi về con người, theo dõi.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien ke_hoach_thay_doi --ghi-chu "..."`
4. Agent Kiểm tra lớp B với `dac_ta/ke_hoach_thay_doi.json`.

## Một yêu cầu thay đổi

1. Agent Đánh giá thay đổi theo `prompts/vai_danh_gia_thay_doi.md`, viết lam_viec/thay_doi/cr_nhap.json (noi_bo, dieu_kien, ma_rui_ro, can_cu_hsmt, gói thay đổi, gói mới).
2. `python .claude/skills/qlda-change/scripts/yeu_cau_thay_doi.py danh_gia lam_viec/thay_doi/cr_nhap.json`
   Tính MD tăng, chi phí nội bộ, giá đề nghị Chủ đầu tư, số ngày chậm, chậm cut over, mốc gắn đợt thanh toán bị dời hoặc vượt hạn, điểm tác động, mức, người phê duyệt, hạn đánh giá, hạn quyết định, tài liệu phải cập nhật, tài liệu khóa, có cần phụ lục hợp đồng.
3. Người có thẩm quyền quyết định: `yeu_cau_thay_doi.py quyet_dinh CRxx --ket-qua "Đã phê duyệt|Từ chối|Hoãn" --nguoi "..." --ngay yyyy-mm-dd`.
   Mức lớn phê duyệt cần `--van-ban` (số, ngày văn bản thống nhất hoặc phụ lục). Hoãn cần `--xem-lai yyyy-mm-dd`. Quyết định quá hạn được cảnh báo (TD16).
4. Phê duyệt thì sửa dữ liệu nguồn, chạy lại các bước trong tai_lieu_cap_nhat theo thứ tự `chay.py trang_thai`.
5. Sau khi phần thay đổi được kiểm tra đạt (Chủ đầu tư theo Mục 20.1 E-ĐKCT, thay đổi nội bộ do quản trị dự án): `yeu_cau_thay_doi.py thuc_hien CRxx --kiem-tra "<biên bản>" --nguoi "..." --ngay yyyy-mm-dd`.
6. `yeu_cau_thay_doi.py dong CRxx --ngay yyyy-mm-dd --ghi-chu "..."`. CR đã thực hiện chỉ đóng được khi mọi tài liệu phải cập nhật đã dùng đầu vào mới, phiên bản sau thay đổi được ghi vào sổ. CR từ chối hoặc hoãn đóng với ghi chú lý do đã thông báo.

Đầu ra: du_lieu/thay_doi.json, du_lieu/thay_doi_bang.json, ket_qua/08_Change_management_plan/Ke_hoach_quan_ly_thay_doi.docx.
