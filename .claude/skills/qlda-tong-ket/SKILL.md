---
name: qlda-tong-ket
description: Tổng hợp số liệu kết thúc dự án và lập báo cáo tổng kết dự án - kế hoạch so với thực tế về phạm vi, sản phẩm bàn giao theo Mẫu 01A, mốc so với hạn, SPI và CPI các kỳ, chi phí nhân sự theo cách trả lương nhóm khai báo (MD công việc hoặc ngày huy động, ngày sẵn sàng tách riêng), chi phí khác đã chi, dự phòng và nghĩa vụ cam kết, công sức và huy động từng thành viên, nghiệm thu, lỗi, yêu cầu thay đổi, rủi ro đã xảy ra, vấn đề tồn đọng, công việc sau dự án, bộ chỉ tiêu KPI dùng cho báo cáo đánh giá. Dùng khi dự án kết thúc và người dùng muốn báo cáo tổng kết, chốt số liệu cuối dự án.
---

# Tổng kết dự án

Đầu vào: dữ liệu kế hoạch (wbs, lich, phan_cong, chi_phi, rui_ro, hsmt, rfp_yeu_cau, thay_doi) và toàn bộ dữ liệu thực tế trong dau_vao/thuc_te/ (xem qlda-bao-cao-tien-do/references/nhap_lieu.md): nhật ký công việc, hoàn thành, mốc, theo dõi rủi ro, nghiệm thu (tiêu chí ghi mã yêu cầu RFP R.., hạng mục ghi số thứ tự Mẫu 01A), lỗi, chi phí khác thực tế (cột loai da_chi, cam_ket), sổ vấn đề và hành động. Ngưỡng KPI mặc định: `references/kpi_mac_dinh.json`, ghi đè trong dau_vao/kpi.json kèm lý do. K14 (tỷ lệ sử dụng nhân lực huy động) lấy ngưỡng từ du_an.json nguong_su_dung_quy_toi_thieu.

## Cách tính chi phí

- Chi phí nhân sự theo don_gia.json cach_tra_luong, cùng cơ sở với cost estimate (thiếu thì dừng K18). cong_suc: kế hoạch là MD công việc giao, thực tế là MD nhật ký, ngày huy động và ngày sẵn sàng chỉ hiển thị để theo dõi năng lực, chi phí bằng 0. huy_dong, ket_hop: ngày huy động (lich.json phan_bo[].quy) cắt theo ngày chốt, tách ngày có ghi công và ngày sẵn sàng. Chênh lệch giá hợp đồng và chi phí dùng chi phí nhân sự này.
- Yêu cầu thay đổi đúng hạn khi ngày quyết định không muộn hơn han_quyet_dinh của CR (qlda-change ghi khi tiếp nhận). CR cũ không có khóa này thì so số ngày xử lý với thời hạn đánh giá trong qlda-change/references/phan_loai.json.
- Khoản B, cùng quy ước với cost estimate: du_phong_rui_ro.so_tien để trống hoặc null là cả khoản B làm dự phòng (cảnh báo K14), 0 là không có dự phòng, số từ 0 đến B được tách khỏi B làm dự phòng, ngoài khoảng là lỗi K19. Tỷ lệ dùng dự phòng (K13) tính trên số dự phòng này.
- chi_phi_thuc_te.csv: dòng loai cam_ket là nghĩa vụ đã cam kết chưa chi (bảo hành), cộng vào chi phí thực tế. Không có dòng cam kết thì cảnh báo K15.
- MD kế hoạch theo người lấy lich.json phan_bo (gồm kỳ KT), làm tròn sao cho tổng bằng tổng MD của WBS.

## Kỳ KT và số liệu mô phỏng

- Lịch có giai đoạn Kết thúc (lich.json giai_doan mã ket_thuc, ngay_dong_du_an) thì ngày làm việc tính đến ngày đóng dự án (qlda-bao-cao-tien-do/scripts/thuc_te.py ngay_lam_viec_du_an). Ngày chốt thuộc giai đoạn này thì kỳ cuối là KT (`tinh_tien_do.py --ky KT` khi ngày chốt là ngày đóng dự án).
- Không truyền --ngay: ngày chốt là ngày ghi nhận cuối của nhật ký. Ngày đó thuộc kỳ KT thì chốt tại ngày đóng dự án khi ngày hiện hành (QLDA_NGAY khi mô phỏng) đã đến, để trùng báo cáo tiến độ kỳ KT.
- ket_thuc.json ghi ngay_dong_du_an, so_lieu_mo_phong, can_cu_mo_phong, dùng chung cho tổng kết, đánh giá, bài học.
- Số liệu mô phỏng: có du_lieu/mo_phong.json (dữ liệu thực tế do qlda-mo-phong sinh) thì đặc tả dùng bí danh nguồn tùy chọn mo_phong (nguon_tuy_chon), khối doan_ds kt#can_cu_mo_phong in ở phần đầu câu "Số liệu thực tế trong báo cáo là số liệu mô phỏng" kèm {mo_phong#_ghi_chu}. Không có tệp thì không in gì. Agent Soạn thảo không viết lại câu này.

## Quy trình

1. `python .claude/skills/qlda-tong-ket/scripts/tong_hop_ket_thuc.py [--ngay yyyy-mm-dd]`
   Kiểm tra định dạng các tệp CSV (K11, báo tệp, dòng, cột). Gọi tinh_tien_do.py cho kỳ cuối (mã sprint hoặc KT), tổng hợp phạm vi, tiến độ, chi phí, nhân lực, nghiệm thu, lỗi, thay đổi, rủi ro, vấn đề tồn đọng, tính 14 KPI và xếp loại. Mốc so với hạn của mốc (mốc cut over so với ngày cut over hợp đồng), kèm lệch so với ngày kế hoạch hiện hành. Lỗi dữ liệu thì dừng, cảnh báo thì in ra (thiếu chi phí thực tế, chưa ghi mốc cut over, chưa có nhật ký rủi ro, dự phòng chưa khai báo, còn vấn đề mở).
   Ra du_lieu/ket_thuc.json, dùng chung cho tổng kết, đánh giá, bài học.
2. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi tong_ket`
3. Agent Soạn thảo viết bản soạn: tóm tắt, nhận xét phạm vi, tiến độ, chi phí (nêu chi phí của ngày sẵn sàng, không kết luận tiết kiệm khi còn nghĩa vụ chưa chi), chất lượng, thay đổi và rủi ro, bảng công việc sau dự án (gồm vấn đề tồn đọng), kết luận. Báo cáo tổng kết nêu kết quả, phần đánh giá thuộc báo cáo đánh giá.
4. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien tong_ket --ghi-chu "..."`
5. Agent Kiểm tra lớp B với `dac_ta/bao_cao_tong_ket.json`.

Đầu ra: ket_qua/11_Bao_cao_tong_ket/Bao_cao_tong_ket_du_an.docx.
