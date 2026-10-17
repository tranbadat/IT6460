---
name: qlda-risk
description: Lập sổ đăng ký rủi ro và kế hoạch quản lý rủi ro (risk management plan) cho dự án - nhận diện theo nhóm bắt buộc gồm cả cơ hội, chấm xác suất có căn cứ và tác động theo ngưỡng định lượng thang 1 đến 5, tiền tác động do script tính (MD nhân đơn giá, phạt chậm E-ĐKC 15), ma trận 5x5 quy đổi sang 3x3 hạng A, B, C, EMV theo MD, tiền, ngày kèm khoảng, đánh giá dự trữ thời gian và phương án khi thiếu, chiến lược, biện pháp phòng ngừa, kế hoạch ứng phó, dấu hiệu, rủi ro còn lại, điều kiện đóng, người phụ trách, liên kết gói WBS và mốc, đối chiếu dự phòng của dự toán, theo dõi trạng thái trong thực hiện. Dùng khi người dùng muốn lập, kiểm tra, cập nhật rủi ro hoặc kế hoạch quản lý rủi ro.
---

# Quản lý rủi ro

Đầu vào: du_lieu/hsmt.json (thanh toán, phạt chậm), rfp_yeu_cau.json, wbs.json, lich.json (đường găng, dự trữ, mốc, gói ghim), phan_cong.json, dau_vao/thanh_vien.json, dau_vao/don_gia.json (đơn giá loại công việc, giá chào mục tiêu, lương tham chiếu). Kế hoạch còn dùng chi_phi.json để đối chiếu dự phòng.

## Bước dữ liệu (rui_ro)

1. Agent Phân tích rủi ro theo `prompts/vai_phan_tich_rui_ro.md`, viết lam_viec/rui_ro/rui_ro_nhap.json. Agent chỉ khai MD, ngày, loại công việc, gói, mốc, căn cứ xác suất; không tự tính tiền.
2. `python .claude/skills/qlda-risk/scripts/kiem_tra_rui_ro.py lam_viec/rui_ro/rui_ro_nhap.json`
   - Tính tiền tác động (`scripts/rui_ro_chung.py`): MD x đơn giá ngày của loai_cong_viec, cộng phạt chậm E-ĐKC 15 trên giá trị đợt thanh toán gắn mốc cut over (gói ghim phạt toàn bộ ngày chậm, gói trên đường găng phạt phần vượt dự trữ, gói khác không phạt, tối đa phat_toi_da_phan_tram; số ngày làm việc làm lùi cut over được quy đổi sang ngày lịch theo lịch dự án, tính từ ngày cut over đến ngày làm việc thứ n sau đó, khóa phat_cham_quy_doi_ngay_lich của thang_do.json), cộng tien_them (số hoặc công thức chenh_luong_bo_sung, chi_phi_von). tac_dong_tien do agent khai vẫn được dùng, kèm cảnh báo R15 khi lệch số tự tính.
   - Suy mức tác động từ ngày chậm, tỷ lệ chi phí trên giá và mốc liên kết theo `nguong_tac_dong` của `references/thang_do.json`. Mức chấm khác mức suy ra mà thiếu ly_do_muc_tac_dong là lỗi R13.
   - Tính điểm, mức, hạng A, B, C (quy đổi 3x3), EMV kèm khoảng theo cận mức xác suất, EMV thời gian của rủi ro trên đường găng hoặc gắn cut over, ma trận 5x5 và 3x3 ghi mã.
   - Kiểm tra đủ trường (gồm can_cu_xac_suat), người phụ trách, liên kết WBS và mốc, rủi ro mức cao có kế hoạch ứng phó và dấu hiệu, đủ nhóm bắt buộc, rủi ro cho cut over và đường găng; cảnh báo dồn xác suất (R24), thiếu cơ hội (R25), thiếu rủi ro còn lại, điều kiện đóng (R26), nguyên nhân viện dẫn số tổng hợp của sổ (R19).

Mã kiểm tra mới từ 1.1.0: R13 mức tác động lệch mức suy ra, R14 thiếu hoặc sai loai_cong_viec, R15 tiền khai lệch tiền tự tính, R16 loại rủi ro sai, R17 tien_them thiếu lý do hoặc sai công thức, R18 chiến lược không hợp loại, R19 nguyên nhân tự tham chiếu, R24 dồn xác suất, R25 thiếu cơ hội, R26 thiếu rủi ro còn lại hoặc điều kiện đóng.

## Bước tài liệu (ke_hoach_rui_ro)

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi ke_hoach_rui_ro` (tự chạy scripts/tinh_bang_rui_ro.py: thang tác động có ngưỡng, quy đổi 3x3, ma trận ghi mã, EMV theo triệu đồng kèm khoảng, dòng đánh giá dự trữ thời gian, bảng phương án khi dự trữ thiếu).
2. Agent Soạn thảo viết bản soạn: phương pháp (EMV là ước tính định hướng, đoạn đối chiếu 3x3 và lý do dùng thang 5 mức), vai trò, nhận xét ma trận, dự phòng (khi dự trữ thời gian thiếu nêu bốn phương án để nhóm quyết định), chu kỳ rà soát, ngưỡng kích hoạt, báo cáo.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien ke_hoach_rui_ro --ghi-chu "..."`
4. Agent Kiểm tra lớp B với `dac_ta/ke_hoach_rui_ro.json`, chú trọng CL05 (phát hiện, quyết định, hành động).

Dòng đánh giá dự phòng chi phí theo chi_phi.json: du_phong_hien_co, cach_tinh_du_phong; chỉ ghi "khi toàn bộ khoản B được dùng làm dự phòng" khi dự phòng bằng cả khoản B.

Phương án khi dự trữ thời gian thiếu do nhóm quyết định: ghi `phuong_an_du_tru_thoi_gian` trong dau_vao/du_an.json (một hoặc nhiều khóa tang_du_tru, dua_viec_len_som, thu_hep_pham_vi, chap_nhan_bao_cdt). Chưa ghi thì tinh_bang_rui_ro.py cảnh báo và bảng phương án không có cột Áp dụng.

Đầu ra: du_lieu/rui_ro.json, du_lieu/rui_ro_bang.json, ket_qua/07_Risk_management_plan/Ke_hoach_quan_ly_rui_ro.docx.

## Chuyển rui_ro_nhap.json định dạng trước 1.1.0

Bỏ tac_dong_tien, thêm loai_cong_viec (khóa đơn giá đã dùng để quy MD ra tiền), chuyển khoản không quy ra MD sang tien_them kèm ly_do_tien_them, thêm can_cu_xac_suat, xac_suat_con_lai, tac_dong_con_lai, dieu_kien_dong, loai. Chạy kiem_tra_rui_ro.py, chấm lại tac_dong theo mức suy ra hoặc ghi ly_do_muc_tac_dong cho từng lỗi R13.

## Trong quá trình thực hiện

- Mỗi khi rủi ro đổi trạng thái (Đang theo dõi, Đã kích hoạt ứng phó, Đã xảy ra, Đã đóng), nhóm ghi dau_vao/thuc_te/theo_doi_rui_ro.csv kèm hành động, tác động thực tế, mã CR nếu ứng phó dẫn đến thay đổi. Báo cáo tiến độ, tổng kết, đánh giá, bài học đọc tệp này.
- Rủi ro mới: bổ sung vào rui_ro_nhap.json, chạy lại bước 2, rồi `chay.py anh_huong rui_ro`.
