---
name: qlda-cost-estimate
description: Lập cost estimate (dự toán, giá dự thầu) từ WBS, đơn giá vai trò, giao việc, lịch và sổ rủi ro - nhân công theo loại công việc, chi phí khác, dự phòng so với EMV, giá chào, thuế GTGT có căn cứ, đối chiếu lương từng người, phân bổ Mẫu 11A, dòng tiền theo sprint, Excel có công thức và thuyết minh dự toán. Dùng khi người dùng muốn lập, kiểm tra hoặc cập nhật dự toán, giá chào, cost estimate.
---

# Cost estimate

Đầu vào: du_lieu/wbs.json, phan_cong.json, lich.json, rui_ro.json, hsmt.json, dau_vao/don_gia.json (đơn giá trọn gói theo người-tháng, lương tham chiếu, hệ số bảo hiểm, chi phí khác, cách tính giá, thuế), thanh_vien.json.

## Quy trình

1. `python .claude/skills/qlda-cost-estimate/scripts/tinh_chi_phi.py`
   - A: nhân công theo loại công việc = MD / MD mỗi tháng x đơn giá trọn gói.
   - B: chi phí khác. D: dự phòng theo cách tính khai báo, so với tổng EMV của sổ rủi ro.
   - Giá chào theo mục tiêu (C là phần còn lại) hoặc cộng dồn. Thuế GTGT theo thuế suất và căn cứ khai báo, kèm phương án độ nhạy 10%.
   - Đối chiếu chi phí lương theo từng người (lương x hệ số bảo hiểm / ngày làm việc mỗi tháng x MD huy động). Giá trước thuế không đủ bù chi phí là lỗi.
   - Ra du_lieu/chi_phi.json và ket_qua/06_Cost_estimate/Cost_estimate.xlsx (công thức, đã tính lại và đối chiếu với Python).
2. Thuyết minh: `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi chi_phi`, agent Soạn thảo viết bản soạn, `chay.py hoan_thien chi_phi`.
3. Agent Kiểm tra lớp B với `dac_ta/thuyet_minh_du_toan.json`.

Đầu ra: Cost_estimate.xlsx, Thuyet_minh_du_toan.docx. Dùng bởi HSDT, master plan, kế hoạch rủi ro, báo cáo tiến độ (đường cơ sở chi phí).
