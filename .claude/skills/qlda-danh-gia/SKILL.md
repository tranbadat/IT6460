---
name: qlda-danh-gia
description: Lập báo cáo đánh giá dự án - kết quả theo bộ chỉ tiêu KPI và xếp loại, đánh giá nghiệm thu theo từng yêu cầu RFP và tiêu chí kỹ thuật HSMT, hiệu quả quản lý thay đổi (thời hạn xử lý, đúng cấp, cập nhật tài liệu), hiệu quả quản lý rủi ro (EMV so với tác động thực tế, dự phòng đã dùng, rủi ro ngoài sổ), thực hiện cam kết HSMT và HSDT, kiến nghị. Dùng khi người dùng muốn đánh giá dự án sau khi kết thúc, đánh giá nghiệm thu, đánh giá khả năng ứng phó rủi ro và thay đổi.
---

# Đánh giá dự án

Đầu vào: du_lieu/ket_thuc.json (skill qlda-tong-ket, bước so_lieu_ket_thuc), du_lieu/hsmt.json, rfp_yeu_cau.json, rui_ro.json, ket_qua/11_Bao_cao_tong_ket/Bao_cao_tong_ket_du_an.docx, dau_vao/thuc_te/nghiem_thu.csv.

## Quy trình

1. Bảo đảm ket_thuc.json mới nhất: `python .claude/skills/qlda-loi/scripts/chay.py trang_thai` (so_lieu_ket_thuc phải ở trạng thái cập nhật).
2. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi danh_gia`
3. Agent Soạn thảo viết bản soạn:
   - Phương pháp và người tham gia đánh giá, ngưỡng đã ghi đè.
   - Bảng nhận định từng chỉ tiêu không đạt hoặc sát ngưỡng, có nguyên nhân và mã bằng chứng.
   - Nhận xét nghiệm thu theo mã yêu cầu R và mã nghiệm thu NT.
   - Bảng đánh giá quy trình thay đổi và quy trình rủi ro theo từng tiêu chí.
   - Đối chiếu cam kết HSMT, HSDT với kết quả. Kết luận và kiến nghị kiểm chứng được.
4. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien danh_gia --ghi-chu "..."`
5. Agent Kiểm tra lớp B với `dac_ta/bao_cao_danh_gia.json`. Người đánh giá không đồng thời là người soạn.

Số liệu mô phỏng: đặc tả có bí danh nguồn tùy chọn mo_phong (du_lieu/mo_phong.json). Khi tệp có, khối doan_ds kt#can_cu_mo_phong (do tong_hop_ket_thuc.py ghi) in ở mục 1 câu số liệu thực tế là số liệu mô phỏng kèm {mo_phong#_ghi_chu}. Không có tệp thì không in gì. Agent Soạn thảo không viết lại câu này, phần phương pháp có thể nêu đánh giá dựa trên số liệu mô phỏng.

Đầu ra: ket_qua/12_Bao_cao_danh_gia/Bao_cao_danh_gia_du_an.docx. Báo cáo bài học (qlda-bai-hoc) dùng các nhận định đã kiểm tra trong báo cáo này.
