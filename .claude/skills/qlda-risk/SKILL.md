---
name: qlda-risk
description: Lập sổ đăng ký rủi ro và kế hoạch quản lý rủi ro (risk management plan) cho dự án - nhận diện theo nhóm bắt buộc, chấm xác suất và tác động thang 1 đến 5, ma trận 5x5, EMV theo MD, tiền, ngày, chiến lược, biện pháp phòng ngừa, kế hoạch ứng phó, dấu hiệu, người phụ trách, liên kết gói WBS và mốc, đối chiếu dự phòng của dự toán, theo dõi trạng thái trong thực hiện. Dùng khi người dùng muốn lập, kiểm tra, cập nhật rủi ro hoặc kế hoạch quản lý rủi ro.
---

# Quản lý rủi ro

Đầu vào: du_lieu/hsmt.json, rfp_yeu_cau.json, wbs.json, lich.json (đường găng, dự trữ, mốc), phan_cong.json, dau_vao/thanh_vien.json. Kế hoạch còn dùng chi_phi.json để đối chiếu dự phòng.

## Bước dữ liệu (rui_ro)

1. Agent Phân tích rủi ro theo `prompts/vai_phan_tich_rui_ro.md`, viết lam_viec/rui_ro/rui_ro_nhap.json.
2. `python .claude/skills/qlda-risk/scripts/kiem_tra_rui_ro.py lam_viec/rui_ro/rui_ro_nhap.json`
   Tính điểm, mức, EMV, ma trận. Kiểm tra đủ trường, người phụ trách, liên kết WBS và mốc, rủi ro mức cao có kế hoạch ứng phó và dấu hiệu, đủ nhóm bắt buộc, có rủi ro cho cut over và cho gói trên đường găng. Thang đo: `references/thang_do.json`.

## Bước tài liệu (ke_hoach_rui_ro)

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi ke_hoach_rui_ro` (tự chạy scripts/tinh_bang_rui_ro.py).
2. Agent Soạn thảo viết bản soạn: phương pháp, vai trò, chu kỳ rà soát, ngưỡng kích hoạt, báo cáo.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien ke_hoach_rui_ro --ghi-chu "..."`
4. Agent Kiểm tra lớp B với `dac_ta/ke_hoach_rui_ro.json`, chú trọng CL05 (phát hiện, quyết định, hành động).

Đầu ra: du_lieu/rui_ro.json, ket_qua/07_Risk_management_plan/Ke_hoach_quan_ly_rui_ro.docx.

## Trong quá trình thực hiện

- Mỗi khi rủi ro đổi trạng thái (Đang theo dõi, Đã kích hoạt ứng phó, Đã xảy ra, Đã đóng), nhóm ghi dau_vao/thuc_te/theo_doi_rui_ro.csv kèm hành động, tác động thực tế, mã CR nếu ứng phó dẫn đến thay đổi. Báo cáo tiến độ, tổng kết, đánh giá, bài học đọc tệp này.
- Rủi ro mới: bổ sung vào rui_ro_nhap.json, chạy lại bước 2, rồi `chay.py anh_huong rui_ro`.
