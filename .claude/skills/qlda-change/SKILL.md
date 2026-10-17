---
name: qlda-change
description: Lập kế hoạch quản lý thay đổi (change management plan) và vận hành quy trình yêu cầu thay đổi (CR) - phân loại theo tác động, cấp phê duyệt, thời hạn đánh giá, đánh giá tác động MD, chi phí, tiến độ, đường găng, danh sách tài liệu phải cập nhật theo sơ đồ phụ thuộc, tài liệu khóa cần phụ lục hợp đồng, quyết định và đóng CR có kiểm tra phiên bản. Dùng khi người dùng muốn lập kế hoạch quản lý thay đổi, ghi hoặc đánh giá một yêu cầu thay đổi, phê duyệt, đóng CR.
---

# Quản lý thay đổi

Đầu vào kế hoạch: du_lieu/hsmt.json, ket_qua/02_HSDT/HSDT.docx, phan_cong.json, lich.json, chi_phi.json, dau_vao/don_gia.json, thanh_vien.json. Phân loại và trạng thái: `references/phan_loai.json`.

## Kế hoạch (ke_hoach_thay_doi)

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi ke_hoach_thay_doi` (tự chạy scripts/tinh_bang_thay_doi.py: phân loại, ma trận lan truyền theo sơ đồ phụ thuộc, sổ thay đổi).
2. Agent Soạn thảo viết bản soạn: quy trình, vai trò ban kiểm soát thay đổi, kênh tiếp nhận, kiểm soát thay đổi không chính thức.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien ke_hoach_thay_doi --ghi-chu "..."`
4. Agent Kiểm tra lớp B với `dac_ta/ke_hoach_thay_doi.json`.

## Một yêu cầu thay đổi

1. Agent Đánh giá thay đổi theo `prompts/vai_danh_gia_thay_doi.md`, viết lam_viec/thay_doi/cr_nhap.json.
2. `python .claude/skills/qlda-change/scripts/yeu_cau_thay_doi.py danh_gia lam_viec/thay_doi/cr_nhap.json`
   Tính MD tăng, chi phí theo đơn giá, số ngày chậm (gói găng hoặc vượt dự trữ), ảnh hưởng cut over, mức và người phê duyệt, tài liệu phải cập nhật, tài liệu khóa, có cần phụ lục hợp đồng.
3. Người có thẩm quyền quyết định: `yeu_cau_thay_doi.py quyet_dinh CRxx --ket-qua "Đã phê duyệt" --nguoi "..." --ngay yyyy-mm-dd`. Ngày theo lịch dự án (biên bản, email).
4. Phê duyệt thì sửa dữ liệu nguồn, chạy lại các bước trong tai_lieu_cap_nhat theo thứ tự `chay.py trang_thai`.
5. `yeu_cau_thay_doi.py dong CRxx --ngay yyyy-mm-dd --ghi-chu "..."`. Chỉ đóng được khi mọi tài liệu phải cập nhật đã dùng đầu vào mới. Phiên bản sau thay đổi được ghi vào sổ.

Đầu ra: du_lieu/thay_doi.json, ket_qua/08_Change_management_plan/Ke_hoach_quan_ly_thay_doi.docx.
