---
name: qlda-hsdt
description: Lập hồ sơ dự thầu (HSDT) của nhà thầu Inter Solution đáp ứng HSMT Mẫu 5A cho gói thầu ABC Wear Web Selling Site System - đơn dự thầu, bảng đáp ứng HSMT, năng lực và kinh nghiệm, nhân sự chủ chốt, đề xuất kỹ thuật, Mẫu 10A giá dự thầu, liên kết với WBS, master schedule, cost estimate và sổ rủi ro. Dùng khi người dùng muốn lập, kiểm tra hoặc cập nhật HSDT.
---

# Hồ sơ dự thầu

Đầu vào (bắt buộc có trước, xem `python .claude/skills/qlda-loi/scripts/chay.py trang_thai`):
- HSMT: du_lieu/hsmt.json, du_lieu/rfp_yeu_cau.json (skill hsmt-mau-5a).
- WBS, giao việc, master schedule, sổ rủi ro, cost estimate (du_lieu/wbs.json, phan_cong.json, lich.json, rui_ro.json, chi_phi.json).
- dau_vao/nha_thau.json: pháp nhân, ngày ký đơn (trong khoảng phát hành HSMT đến đóng thầu), hợp đồng tương tự, doanh thu, bảo đảm dự thầu. Nhóm điền, không agent nào bịa. Hợp đồng tương tự phải trong khoảng thời gian HSMT yêu cầu (gần nhất hợp lệ).
- dau_vao/thanh_vien.json: người giữ vị trí nhân sự chủ chốt phải có trình độ, số năm kinh nghiệm, kinh nghiệm liên quan. Vị trí bổ sung phải có họ tên thật (bỏ khóa _can_xac_nhan).

## Quy trình

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi hsdt`
   Tự chạy `scripts/tinh_hsdt.py`: kiểm tra thông tin nhà thầu, ngày ký đơn, hợp đồng tương tự, doanh thu, nhân sự chủ chốt so với Bảng số 02, bảo đảm dự thầu, giá dự thầu không vượt giá gói thầu, mọi hạng mục Mẫu 01A hoàn thành trước cut over. Đơn dự thầu lấy nguyên văn Mẫu số 02 trong dau_vao/Mau_5A.docx và điền các trường. Lỗi thì dừng và báo người dùng trường cần bổ sung trong nha_thau.json.
2. Agent Soạn thảo (qlda-loi/prompts/vai_soan_thao.md) viết lam_viec/hsdt/ban_soan.json: giải pháp kỹ thuật, phương pháp, tổ chức thực hiện, bảo đảm chất lượng, quản lý thay đổi và rủi ro, đề xuất khác. Bám tiêu chí đánh giá kỹ thuật trong du_lieu/hsmt.json (ky_thuat.tieu_chi).
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien hsdt --ghi-chu "..."`
4. Agent Kiểm tra lớp B theo qlda-loi/prompts/vai_kiem_tra.md với `dac_ta/hsdt.json`: đáp ứng từng tiêu chí của HSMT, nhất quán giá, tiến độ, nhân sự với dữ liệu nguồn.
5. Còn lỗi thì qlda-loi/prompts/vai_sua.md.

Đầu ra: ket_qua/02_HSDT/HSDT.docx.

## Khóa sau ký hợp đồng

HSDT là đường cơ sở đấu thầu. Sau `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py duong_co_so BL1 --ten "Đường cơ sở hợp đồng" --hop-dong`, HSDT không tạo lại. Thay đổi về giá, mốc, phạm vi ghi bằng phụ lục hợp đồng hoặc biên bản qua skill qlda-change.
