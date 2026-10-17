---
name: qlda-hsdt
description: Lập hồ sơ dự thầu (HSDT) của nhà thầu (thông tin tại dau_vao/nha_thau.json) đáp ứng HSMT Mẫu 5A cho gói thầu ABC Wear Web Selling Site System - đơn dự thầu, bảng đáp ứng HSMT, năng lực và kinh nghiệm, nhân sự chủ chốt, đề xuất kỹ thuật, Mẫu 10A giá dự thầu, liên kết với WBS, master schedule, cost estimate và sổ rủi ro. Dùng khi người dùng muốn lập, kiểm tra hoặc cập nhật HSDT.
---

# Hồ sơ dự thầu

Đầu vào (bắt buộc có trước, xem `python .claude/skills/qlda-loi/scripts/chay.py trang_thai`):
- HSMT: du_lieu/hsmt.json, du_lieu/rfp_yeu_cau.json (skill hsmt-mau-5a).
- WBS, giao việc, master schedule, sổ rủi ro, cost estimate (du_lieu/wbs.json, phan_cong.json, lich.json, rui_ro.json, chi_phi.json).
- dau_vao/nha_thau.json: pháp nhân (tên, địa chỉ, đại diện, mã số thuế, điện thoại, e-mail, năm thành lập), ngày ký đơn (trong khoảng phát hành HSMT đến đóng thầu), nghĩa vụ thuế năm gần nhất, hợp đồng tương tự, hợp đồng không hoàn thành (hop_dong_khong_hoan_thanh: nam, phan_viec, mo_ta, chu_dau_tu, dia_chi, nguyen_nhan, gia_tri), doanh thu, bảo đảm dự thầu. Nhóm điền, không agent nào bịa. Giá trị dạng giữ chỗ như [Nhóm bổ sung ...] bị coi là thiếu. Hợp đồng tương tự phải trong khoảng thời gian HSMT yêu cầu (gần nhất hợp lệ).
- dau_vao/thanh_vien.json: người giữ vị trí nhân sự chủ chốt phải có trình độ, kinh nghiệm liên quan dạng "mm/yyyy - mm/yyyy: nội dung; ..." (dùng cho Mẫu 06C và số năm kinh nghiệm). Vị trí bổ sung phải có họ tên thật (bỏ khóa _can_xac_nhan). Mẫu 06B dùng thêm các khóa tùy chọn can_cuoc, ngay_sinh (hoặc nam_sinh), so_nam_lam_viec_hien_tai, nguoi_lien_lac, nguoi_su_dung_lao_dong, dia_chi_nguoi_su_dung_lao_dong, dien_thoai_lien_lac. Thành viên loại nhom được coi là nhân sự của nhà thầu. Khóa chưa có thì bảng ghi "Theo hồ sơ nhân sự trên Hệ thống" và script cảnh báo.
- dau_vao/chi_tieu_ky_thuat.json: chỉ tiêu kỹ thuật định lượng (chi_tieu: ma, yeu_cau_hsmt, chi_tieu, giai_phap, cach_kiem_chung), bảo hành (thoi_han_thang, muc_loi, ho_tro_tang_cuong), dieu_kien_cut_over. Thiếu hoặc rỗng thì bước dừng. Trường null là chưa thống nhất, bảng ghi "Hai bên thống nhất khi xác nhận đặc tả".
- dau_vao/du_an.json nguong_su_dung_quy_toi_thieu: tỷ lệ MD công việc trên quỹ huy động tối thiểu (lấy lich.json ty_le_su_dung_quy, chưa có thì chi_phi.json ty_le_su_dung). Thấp hơn thì bước dừng.

## Quy trình

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi hsdt`
   Tự chạy `scripts/tinh_hsdt.py`. Lỗi thì dừng và báo trường cần bổ sung:
   - thông tin nhà thầu (kể cả điện thoại, e-mail, nghĩa vụ thuế), ngày ký đơn, hợp đồng tương tự, doanh thu, bảo đảm dự thầu, giá dự thầu không vượt giá gói thầu, tổng Mẫu 11A bằng giá dự thầu;
   - nhân sự chủ chốt so với Bảng số 02. Số năm kinh nghiệm tính từ thời điểm sớm nhất trong kinh_nghiem đến ngày đóng thầu, không suy được thì dùng so_nam_kinh_nghiem. Số năm kê khai lớn hơn số chứng minh được thì cảnh báo và dùng số chứng minh được;
   - tỷ lệ sử dụng quỹ huy động không thấp hơn ngưỡng;
   - Mẫu 10A: ngày bắt đầu theo gói riêng của hạng mục, ngày hoàn thành theo mọi gói chính (bỏ gói dàn trải và gói quản lý dự án). Hạng mục hoàn thành trước cut over. Hạng mục gắn đợt thanh toán (theo hop_dong.thanh_toan[].hang_muc_01a, chưa có thì suy từ nội dung từng đợt tại E-ĐKC 13.1) không hoàn thành muộn hơn mốc của đợt trong lich.json, sai thì báo gói gây trễ;
   - chi_tieu_ky_thuat.json có chỉ tiêu, bảo hành không ngắn hơn HSMT, điều kiện cut over;
   - tiêu đề cột các bảng có khóa mau_so trong dac_ta/hsdt.json khớp dau_vao/Mau_5A.docx, đặc tả có đủ Mẫu 06A, 06B, 06C, 07, 10A, 11A.
   Đơn dự thầu lấy nguyên văn Mẫu số 02, Mẫu số 07 lấy nguyên văn lựa chọn trong dau_vao/Mau_5A.docx. Kết quả: du_lieu/hsdt_bang.json.
2. Agent Soạn thảo (qlda-loi/prompts/vai_soan_thao.md) viết lam_viec/hsdt/ban_soan.json: giải pháp kỹ thuật, phương pháp, tổ chức thực hiện, bảo đảm chất lượng, quản lý thay đổi và rủi ro, đề xuất khác. Bám tiêu chí đánh giá kỹ thuật trong du_lieu/hsmt.json (ky_thuat.tieu_chi) và chỉ tiêu trong chi_tieu_ky_thuat.json (bí danh kt). Không nêu khoản chi phí chung và lợi nhuận, không nêu mức sử dụng nhân lực theo người, không nêu biện pháp ngoài sổ rủi ro.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien hsdt --ghi-chu "..."`
4. Agent Kiểm tra lớp B theo qlda-loi/prompts/vai_kiem_tra.md với `dac_ta/hsdt.json`: đáp ứng từng tiêu chí của HSMT, nhất quán giá, tiến độ, nhân sự với dữ liệu nguồn.
5. Còn lỗi thì qlda-loi/prompts/vai_sua.md.

Đầu ra: ket_qua/02_HSDT/HSDT.docx. Bìa kiểu hồ sơ thầu (không có môn học, nhóm, giảng viên). Gồm bảng đáp ứng HSMT (tính hợp lệ, Bảng số 01, Bảng số 02, năm tiêu chí kỹ thuật), bảng chỉ dẫn vị trí đáp ứng tiêu chí kỹ thuật (mục có khóa tieu_chi trong đặc tả), Mẫu 05, 06A, 06B, 06C, 07, 08, 09A, bảng chỉ tiêu kỹ thuật, bảo hành, huy động nhân sự theo sprint, Mẫu 10A, 11A đúng cột Mẫu 5A.

## Khóa sau ký hợp đồng

HSDT là đường cơ sở đấu thầu. Sau `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py duong_co_so BL1 --ten "Đường cơ sở hợp đồng" --hop-dong`, HSDT không tạo lại. Thay đổi về giá, mốc, phạm vi ghi bằng phụ lục hợp đồng hoặc biên bản qua skill qlda-change.
