---
name: qlda-tong-ket
description: Tổng hợp số liệu kết thúc dự án và lập báo cáo tổng kết dự án - kế hoạch so với thực tế về phạm vi, sản phẩm bàn giao theo Mẫu 01A, mốc, SPI và CPI các kỳ, chi phí nhân sự và chi phí khác, công sức từng thành viên, nghiệm thu, lỗi, yêu cầu thay đổi, rủi ro đã xảy ra, công việc sau dự án, bộ chỉ tiêu KPI dùng cho báo cáo đánh giá. Dùng khi dự án kết thúc và người dùng muốn báo cáo tổng kết, chốt số liệu cuối dự án.
---

# Tổng kết dự án

Đầu vào: dữ liệu kế hoạch (wbs, lich, phan_cong, chi_phi, rui_ro, hsmt, rfp_yeu_cau, thay_doi) và toàn bộ dữ liệu thực tế trong dau_vao/thuc_te/ (xem qlda-bao-cao-tien-do/references/nhap_lieu.md): nhật ký công việc, hoàn thành, mốc, theo dõi rủi ro, nghiệm thu (tiêu chí ghi mã yêu cầu RFP R.., hạng mục ghi số thứ tự Mẫu 01A), lỗi, chi phí khác thực tế. Ngưỡng KPI mặc định: `references/kpi_mac_dinh.json`, ghi đè trong dau_vao/kpi.json kèm lý do.

## Quy trình

1. `python .claude/skills/qlda-tong-ket/scripts/tong_hop_ket_thuc.py [--ngay yyyy-mm-dd]`
   Gọi tinh_tien_do.py cho kỳ cuối (mã sprint hoặc KT), tổng hợp phạm vi, tiến độ, chi phí, nhân lực, nghiệm thu, lỗi, thay đổi, rủi ro, tính 13 KPI và xếp loại. Lỗi dữ liệu thì dừng, cảnh báo thì in ra (thiếu chi phí thực tế, chưa ghi mốc cut over, chưa có nhật ký rủi ro).
   Ra du_lieu/ket_thuc.json, dùng chung cho tổng kết, đánh giá, bài học.
2. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi tong_ket`
3. Agent Soạn thảo viết bản soạn: tóm tắt, nhận xét phạm vi, tiến độ, chi phí, chất lượng, thay đổi và rủi ro, bảng công việc sau dự án, kết luận. Báo cáo tổng kết nêu kết quả, phần đánh giá thuộc báo cáo đánh giá.
4. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien tong_ket --ghi-chu "..."`
5. Agent Kiểm tra lớp B với `dac_ta/bao_cao_tong_ket.json`.

Đầu ra: ket_qua/11_Bao_cao_tong_ket/Bao_cao_tong_ket_du_an.docx.
