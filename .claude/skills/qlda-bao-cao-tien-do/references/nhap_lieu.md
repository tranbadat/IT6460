# Nhập dữ liệu thực tế

Các skill báo cáo tiến độ, tổng kết, đánh giá, bài học, bảng lương đọc dữ liệu thực tế trong dau_vao/thuc_te/. Mỗi thành viên ghi hằng ngày hoặc cuối tuần.

| Tệp | Cột | Cách ghi |
|---|---|---|
| nhat_ky_cong_viec.csv | ngay, thanh_vien, ma_goi, md, ghi_chu | Một dòng cho mỗi người, mỗi gói, mỗi ngày. thanh_vien là id trong thanh_vien.json. ma_goi là mã gói lá WBS. md là phần ngày làm việc (0,5 là nửa ngày), dùng dấu chấm thập phân. Tổng mỗi người mỗi ngày không vượt tỷ lệ tham gia |
| hoan_thanh.csv | ngay_cap_nhat, ma_goi, phan_tram, ghi_chu | Cập nhật tỷ lệ hoàn thành (0 đến 100) của gói khi có tiến triển, tối thiểu cuối mỗi sprint. Không giảm tỷ lệ, nếu phát hiện làm lại thì ghi chú |
| moc_thuc_te.csv | ma_moc, ngay_dat, ghi_chu | Ghi khi đạt mốc (M0 đến M6), kèm biên bản |
| nghiem_thu.csv | ma, tieu_chi, hang_muc, ket_qua, ngay, nguoi_xac_nhan, ghi_chu | Mỗi tiêu chí một mã NT01, NT02. tieu_chi bắt đầu bằng mã yêu cầu RFP (R03, R05...) rồi đến nội dung. hang_muc là số thứ tự hạng mục Mẫu 01A (1 đến 10). ket_qua là Đạt hoặc Không đạt. Nghiệm thu lại thì thêm dòng mới cùng mã với ngày mới, không sửa dòng cũ. Ô có dấu phẩy phải đặt trong ngoặc kép. Ví dụ: NT05,R04 Thời gian phản hồi không quá 2 giây,6,Không đạt,2027-06-18,ABC Wear,"Đo được 2,6 giây" |
| loi.csv | ma, ngay_phat_hien, muc_do, ma_goi, trang_thai, ngay_dong, mo_ta | muc_do: Nghiêm trọng, Cao, Trung bình, Thấp. trang_thai: Mở hoặc Đã đóng |
| theo_doi_rui_ro.csv | ngay, ma_rui_ro, trang_thai, hanh_dong, md_tac_dong, chi_phi_tac_dong, ma_cr, ghi_chu | Ghi khi rủi ro thay đổi trạng thái. trang_thai: Đang theo dõi, Đã kích hoạt ứng phó, Đã xảy ra, Đã đóng. ma_rui_ro là mã trong du_lieu/rui_ro.json. md_tac_dong và chi_phi_tac_dong là tác động thực tế khi rủi ro xảy ra. Rủi ro phát sinh chưa có trong sổ: đặt mã mới (ví dụ RR13) và ghi tên rủi ro ở ghi_chu của dòng đầu tiên, sau đó bổ sung vào sổ bằng skill qlda-risk. ma_cr nếu ứng phó dẫn đến yêu cầu thay đổi |
| chi_phi_thuc_te.csv | ngay, khoan_muc, so_tien, ghi_chu | Chi phí khác thực tế (ngoài công nhân sự), khoan_muc theo chi_phi_khac trong don_gia.json. Không bắt buộc |
| retro.md | | Họp cải tiến cuối sprint, mỗi ý một mã R-Sx-nn |

Lệnh báo cáo kỳ: python .claude/skills/qlda-bao-cao-tien-do/scripts/tinh_tien_do.py --ky S3
