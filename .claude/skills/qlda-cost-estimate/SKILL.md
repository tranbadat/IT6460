---
name: qlda-cost-estimate
description: Lập cost estimate (dự toán, giá dự thầu) từ WBS, đơn giá vai trò, giao việc, lịch và sổ rủi ro - nhân công theo loại công việc, chi phí khác, dự phòng so với EMV, giá chào, thuế GTGT có căn cứ, đối chiếu lương từng người theo cách trả lương nhóm khai báo, phân bổ Mẫu 11A, dòng tiền theo sprint, Excel có công thức và thuyết minh dự toán. Dùng khi người dùng muốn lập, kiểm tra hoặc cập nhật dự toán, giá chào, cost estimate.
---

# Cost estimate

Đầu vào: du_lieu/wbs.json, phan_cong.json, lich.json, rui_ro.json, hsmt.json, dau_vao/don_gia.json (đơn giá trọn gói theo người-tháng, lương tham chiếu, hệ số bảo hiểm, chi phí khác, du_phong_rui_ro, cach_tra_luong, cách tính giá, thuế), thanh_vien.json. Quy tắc dùng dự phòng lấy từ .claude/skills/qlda-change/references/phan_loai.json khóa du_phong (nguồn chung, tệp tĩnh).

## Quy trình

1. `python .claude/skills/qlda-cost-estimate/scripts/tinh_chi_phi.py`
   - A: nhân công theo loại công việc = MD / MD mỗi tháng x đơn giá trọn gói.
   - B: chi phí khác. D: dự phòng theo cách tính khai báo, so với tổng EMV của sổ rủi ro. Khi dự phòng nằm trong B (cach_tinh nam_trong_chi_phi_khac), du_phong_rui_ro.so_tien để trống hoặc null là cả khoản B, 0 là không có dự phòng, số từ 0 đến B là phần dự phòng, ngoài khoảng này là lỗi C33. Quy ước này dùng chung với tổng kết.
   - chi_phi.json ghi du_phong_hien_co (số tiền dự phòng) và du_phong_ca_khoan_b (true khi dự phòng bằng toàn bộ khoản B vì so_tien trống, false khi có so_tien riêng hoặc dự phòng là dòng D) để kế hoạch rủi ro và các tài liệu khác dùng trực tiếp, không tự suy ra.
   - Giá chào theo mục tiêu (C là phần còn lại) hoặc cộng dồn. Thuế GTGT theo thuế suất và căn cứ khai báo, kèm phương án độ nhạy 10%.
   - Đối chiếu chi phí lương kế hoạch theo từng người = lương x hệ số bảo hiểm / ngày làm việc mỗi tháng x MD tính lương. MD tính lương theo cach_tra_luong (nhóm quyết định, thiếu thì dừng C31): cong_suc là MD công việc giao theo lich.json (tổng bằng tổng WBS), huy_dong và ket_hop là MD huy động. Giá trước thuế không đủ bù chi phí là lỗi (C30).
   - Quỹ huy động, MD sẵn sàng, tỷ lệ sử dụng quỹ và lương của toàn bộ ngày huy động luôn được tính để theo dõi năng lực, chỉ là chi phí khi trả theo huy động. Dòng tiền lũy kế chi theo cách trả lương.
   - Cùng cơ sở với báo cáo tiến độ, tổng kết, bảng lương qua qlda-bao-cao-tien-do/scripts/thuc_te.py; các bước sau cảnh báo khi cost estimate lập theo cách trả lương khác.
   - Bảng quy tắc dùng dự phòng (quy_tac_du_phong) do script lập từ nguồn chung, agent không viết lại.
   - Ra du_lieu/chi_phi.json và ket_qua/06_Cost_estimate/Cost_estimate.xlsx (công thức, đã tính lại và đối chiếu với Python).
2. Thuyết minh: `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi chi_phi`, agent Soạn thảo viết bản soạn, `chay.py hoan_thien chi_phi`.
3. Agent Kiểm tra lớp B với `dac_ta/thuyet_minh_du_toan.json`.

Đầu ra: Cost_estimate.xlsx, Thuyet_minh_du_toan.docx. Dùng bởi HSDT, master plan, kế hoạch rủi ro, báo cáo tiến độ (đường cơ sở chi phí).
