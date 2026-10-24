---
name: qlda-cost-estimate
description: Lập cost estimate (dự toán, giá dự thầu) từ WBS, đơn giá vai trò, giao việc, lịch và sổ rủi ro - nhân công theo loại công việc, chi phí khác, dự phòng so với EMV, giá chào, thuế GTGT có căn cứ, đối chiếu lương từng người theo cách trả lương nhóm khai báo, phân bổ Mẫu 11A, dòng tiền theo sprint, Excel có công thức và thuyết minh dự toán. Dùng khi người dùng muốn lập, kiểm tra hoặc cập nhật dự toán, giá chào, cost estimate.
---

# Cost estimate

Đầu vào: du_lieu/wbs.json, phan_cong.json, lich.json, rui_ro.json, hsmt.json, dau_vao/don_gia.json (đơn giá trọn gói theo người-tháng, lương tham chiếu, hệ số bảo hiểm, chi phí khác, du_phong_rui_ro, cach_tra_luong, cách tính giá, thuế), thanh_vien.json. Quy tắc dùng dự phòng lấy từ .claude/skills/qlda-change/references/phan_loai.json khóa du_phong (nguồn chung, tệp tĩnh).

## Quy trình

1. `python .claude/skills/qlda-cost-estimate/scripts/tinh_chi_phi.py`
   - A: nhân công theo loại công việc = MD / MD mỗi tháng x đơn giá trọn gói.
   - B: chi phí khác. D: dự phòng theo cách tính khai báo, so với EMV còn lại của sổ rủi ro (rui_ro.json tong_emv_tien_con_lai: bỏ rủi ro đã xảy ra, đã đóng theo nhật ký theo dõi rủi ro; chi_phi.json ghi tong_emv_rui_ro là EMV còn lại, tong_emv_rui_ro_ban_dau là tổng EMV của sổ, rui_ro_da_xay_ra kèm tác động thực tế). Khi dự phòng nằm trong B (cach_tinh nam_trong_chi_phi_khac), du_phong_rui_ro.so_tien để trống hoặc null là cả khoản B, 0 là không có dự phòng, số từ 0 đến B là phần dự phòng, ngoài khoảng này là lỗi C33. Quy ước này dùng chung với tổng kết.
   - chi_phi.json ghi du_phong_hien_co (số tiền dự phòng) và du_phong_ca_khoan_b (true khi dự phòng bằng toàn bộ khoản B vì so_tien trống, false khi có so_tien riêng hoặc dự phòng là dòng D) để kế hoạch rủi ro và các tài liệu khác dùng trực tiếp, không tự suy ra.
   - Phụ lục hợp đồng: sau khi CR được phê duyệt và áp dụng (qlda-change `yeu_cau_thay_doi.py ap_dung`, cộng giá điều chỉnh vào gia_chao_muc_tieu, ghi dieu_chinh_gia_theo_phu_luc), giá gói thầu chỉ là trần của giá dự thầu ban đầu (giá chào trừ giá điều chỉnh, C20). Giá chào so với giá hợp đồng sau phụ lục cuối trong du_lieu/thay_doi.json (khóa phu_luc của CR): vượt là lỗi C20, thấp hơn là cảnh báo C42; vết điều chỉnh không khớp phụ lục là lỗi C42. chi_phi.json ghi gia_chao_ban_dau, gia_dieu_chinh_phu_luc, gia_hop_dong_sau_phu_luc, phu_luc_hop_dong, doan_phu_luc (thuyết minh in khi có phụ lục). Tham_so có dòng giá điều chỉnh, Tong_hop so giá gói thầu với giá dự thầu ban đầu.
   - Giá chào theo mục tiêu (C là phần còn lại) hoặc cộng dồn. Thuế GTGT theo thuế suất và căn cứ khai báo, kèm phương án độ nhạy 10%.
   - Đối chiếu chi phí lương kế hoạch theo từng người = lương x hệ số bảo hiểm / ngày làm việc mỗi tháng x MD tính lương. MD tính lương theo cach_tra_luong (nhóm quyết định, thiếu thì dừng C31): cong_suc là MD công việc giao theo lich.json (tổng bằng tổng WBS), huy_dong và ket_hop là MD huy động. Giá trước thuế không đủ bù chi phí là lỗi (C30).
   - Quỹ huy động, MD sẵn sàng, tỷ lệ sử dụng quỹ và lương của toàn bộ ngày huy động luôn được tính để theo dõi năng lực, chỉ là chi phí khi trả theo huy động. Dòng tiền lũy kế chi theo cách trả lương.
   - Đợt thanh toán sau phụ lục: đợt gốc của hợp đồng tính trên giá hợp đồng ban đầu khi phụ lục khai báo đợt thanh toán riêng (phu_luc.dot_thanh_toan, ghi bằng `yeu_cau_thay_doi.py phu_luc CRxx --dot-thanh-toan`), đợt có ngày thu trước ngày phụ lục không bao giờ tính lại; đợt của phụ lục là phần trăm giá điều chỉnh, gắn mốc của lịch. Phụ lục chưa khai báo đợt thì phần chênh của các đợt đã thu thành dòng thu sau cut over và cảnh báo C43; tổng phần trăm đợt của phụ lục khác 100 hoặc tổng các đợt khác giá hợp đồng là lỗi C43. thanh_toan ghi co_so, co_so_ten, ma_cr; sheet Dong_tien có cột Giá làm cơ sở (công thức theo ô giá điều chỉnh của từng phụ lục ở Tham_so).
   - Quan hệ với Mẫu 11A (doan_mau_11a, nhan_gia_chao): trước ký hợp đồng bảng phân bổ là số liệu Mẫu 11A; sau đường cơ sở hợp đồng HSDT đã khóa, Mẫu 11A giữ giá dự thầu ban đầu, bảng phân bổ là phân bổ giá hợp đồng hiện hành, nêu hạng mục 01A của gói theo CR.
   - Chi phí lương từng người làm tròn bằng lam_tron_tong để tổng khớp lũy kế chi của dòng tiền, khoản còn lại sau lương tính trên các số đã in.
   - Dòng tiền: MD của kỳ sau cut over trong lich.json phan_bo (kỳ KT của giai đoạn Kết thúc, do master schedule xếp gói Kết thúc sau cut over) vào cột Sau cut over (sheet Phan_bo_luong cột Kỳ dòng tiền), nên tổng chi lương theo MD công việc bằng chi phí lương cả dự án. Giá chào không đổi.
   - Cùng cơ sở với báo cáo tiến độ, tổng kết, bảng lương qua qlda-bao-cao-tien-do/scripts/thuc_te.py; các bước sau cảnh báo khi cost estimate lập theo cách trả lương khác.
   - Bảng quy tắc dùng dự phòng (quy_tac_du_phong) do script lập từ nguồn chung, agent không viết lại.
   - Ra du_lieu/chi_phi.json và ket_qua/06_Cost_estimate/Cost_estimate.xlsx (công thức, đã tính lại và đối chiếu với Python).
2. Thuyết minh: `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi chi_phi`, agent Soạn thảo viết bản soạn, `chay.py hoan_thien chi_phi`.
3. Agent Kiểm tra lớp B với `dac_ta/thuyet_minh_du_toan.json`.

Đầu ra: Cost_estimate.xlsx, Thuyet_minh_du_toan.docx. Dùng bởi HSDT, master plan, kế hoạch rủi ro, báo cáo tiến độ (đường cơ sở chi phí).
