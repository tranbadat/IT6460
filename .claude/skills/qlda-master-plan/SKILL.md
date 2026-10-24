---
name: qlda-master-plan
description: Lập kế hoạch tổng thể dự án (master plan) tổng hợp từ HSMT, HSDT, WBS, master schedule, phân công, cost estimate, kế hoạch rủi ro và kế hoạch thay đổi - điều lệ dự án với mục tiêu SMART và người phê duyệt, các bên liên quan, phạm vi, tiến độ, tổ chức, mua sắm và thuê ngoài, chi phí với một đường cơ sở BAC, chất lượng và nghiệm thu theo chỉ tiêu kỹ thuật, truyền thông và báo cáo, rủi ro, vấn đề, thay đổi, cấu hình, lịch rà soát, kết thúc dự án. Dùng khi người dùng muốn lập hoặc cập nhật master plan, kế hoạch quản lý dự án, điều lệ dự án.
---

# Master plan

Master plan không tạo số liệu mới. Mọi con số, mốc, tên người lấy từ dữ liệu của các bước trước, nên lập sau cùng trong giai đoạn lập kế hoạch.

Đầu vào: du_lieu/hsmt.json, rfp_yeu_cau.json, wbs.json, lich.json, phan_cong.json, chi_phi.json, rui_ro.json, hsdt_bang.json (tùy chọn), ket_qua/02_HSDT/HSDT.docx, ket_qua/07_Risk_management_plan, ket_qua/08_Change_management_plan, dau_vao/thanh_vien.json, du_an.json, nha_thau.json, chi_tieu_ky_thuat.json.

## Quy trình

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi ke_hoach_tong_the`
   Tự chạy hai script trước khi lập khung:
   - qlda-change/scripts/tinh_bang_thay_doi.py: du_lieu/thay_doi_bang.json (bí danh tdb), gồm vai_ban, thẩm quyền, hạng mục cấu hình và bảng quy tắc dùng dự phòng dùng chung với kế hoạch rủi ro và thuyết minh dự toán.
   - scripts/tinh_bang_ke_hoach.py: du_lieu/ke_hoach_bang.json (bí danh kb), gồm mục tiêu SMART (chỉ số, ngưỡng, hạn, người xác nhận), phê duyệt, cam kết của Chủ đầu tư, các bên liên quan, thuê ngoài, huy động vị trí bổ sung, bảo hành, lịch rà soát, việc kết thúc, tổng EMV theo triệu đồng kèm khoảng. Trong giai đoạn thực hiện (từ 1.2.0): bảng mục tiêu có cột tình trạng đến ngày hiện hành (mốc đã đạt, đúng hạn hoặc trễ bao nhiêu ngày làm việc), bảng phê duyệt thêm dòng phê duyệt phiên bản sau mỗi phụ lục hợp đồng, bảng đường cơ sở (duong_co_so, từ du_lieu/phien_ban.json), nhãn giá (nhan_gia: giá hợp đồng sau phụ lục), phu_luc_goc cho cột tài liệu gốc, EMV còn lại khi sổ rủi ro có rủi ro đã xảy ra, đợt thanh toán của phụ lục ghi căn cứ phụ lục, rà soát kết thúc tại ngày đóng dự án của lịch.
   Mã kiểm tra: KH01 đặc tả thiếu mục bắt buộc (khai báo trong kiem_tra.muc_bat_buoc), KH02 bên liên quan phía Chủ đầu tư chỉ có một dòng, KH03 khoản B chưa có danh mục, KH04 thiếu chỉ tiêu kỹ thuật, KH05 chưa có vai trong tdb, KH06 vị trí bổ sung chưa có hồ sơ năng lực. Lỗi dừng, cảnh báo in.
2. Agent Soạn thảo (qlda-loi/prompts/vai_soan_thao.md) đọc thêm `references/huong_dan_soan.md`, viết lam_viec/ke_hoach_tong_the/ban_soan.json. Các mục rủi ro, thay đổi, cấu hình tóm tắt và dẫn sang kế hoạch chuyên đề, không viết lại.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien ke_hoach_tong_the --ghi-chu "..."`. Lớp A kiểm thêm các mục bắt buộc (9 kế hoạch con, thay đổi, cấu hình, vấn đề, rà soát, kết thúc, đường cơ sở).
4. Agent Kiểm tra lớp B với `dac_ta/ke_hoach_tong_the.json`: nhất quán với HSDT (cam kết), lịch, dự toán, phân công, kế hoạch rủi ro và thay đổi; tiêu chí nghiệm thu đo được; một đường cơ sở chi phí.

Mặc định đánh giá bên liên quan theo vai và vai xác nhận mục tiêu ở `references/ke_hoach.json`. Dòng trong phan_cong ben_ngoai có anh_huong, quan_tam, cach_tham_gia, vai_tro thì ghi đè, dòng có ky_hop_dong: true là người có thẩm quyền của Chủ đầu tư.

Đầu ra: ket_qua/05_Master_plan/Ke_hoach_tong_the.docx. Khi một kế hoạch thành phần thay đổi, `chay.py trang_thai` báo master plan cũ.
