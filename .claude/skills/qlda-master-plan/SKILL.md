---
name: qlda-master-plan
description: Lập kế hoạch tổng thể dự án (master plan) tổng hợp từ HSMT, HSDT, WBS, master schedule, phân công, cost estimate, kế hoạch rủi ro và kế hoạch thay đổi - mục tiêu, phạm vi, tổ chức, tiến độ, chi phí, chất lượng, nghiệm thu, giao tiếp, rủi ro, thay đổi. Dùng khi người dùng muốn lập hoặc cập nhật master plan, kế hoạch quản lý dự án.
---

# Master plan

Master plan không tạo số liệu mới. Mọi con số, mốc, tên người lấy từ dữ liệu của các bước trước, nên lập sau cùng trong giai đoạn lập kế hoạch.

Đầu vào: du_lieu/hsmt.json, ket_qua/02_HSDT/HSDT.docx, du_lieu/wbs.json, lich.json, phan_cong.json, chi_phi.json, rui_ro.json, ket_qua/07_Risk_management_plan, ket_qua/08_Change_management_plan, dau_vao/thanh_vien.json, du_an.json.

## Quy trình

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi ke_hoach_tong_the`
2. Agent Soạn thảo (qlda-loi/prompts/vai_soan_thao.md) viết lam_viec/ke_hoach_tong_the/ban_soan.json. Các mục quản lý rủi ro và thay đổi tóm tắt và dẫn sang hai kế hoạch chuyên đề, không viết lại.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien ke_hoach_tong_the --ghi-chu "..."`
4. Agent Kiểm tra lớp B với `dac_ta/ke_hoach_tong_the.json`: nhất quán với HSDT (cam kết), lịch, dự toán, phân công; tiêu chí nghiệm thu đo được.

Đầu ra: ket_qua/05_Master_plan/Ke_hoach_tong_the.docx. Khi một kế hoạch thành phần thay đổi, `chay.py trang_thai` báo master plan cũ.
