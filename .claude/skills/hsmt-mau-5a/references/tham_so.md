# Tham số chủ đầu tư

RFP chỉ nêu yêu cầu nghiệp vụ, mốc và điều khoản hợp đồng cơ bản. HSMT theo Mẫu 5A còn cần các giá trị do chủ đầu tư hoặc bên lập HSMT quyết định. Các giá trị này nằm trong `tham_so_chu_dau_tu.json`. File chỉ chứa giá trị và lựa chọn ngắn, không chứa câu văn của HSMT.

| Nhóm | Trường | Ý nghĩa và giới hạn |
|---|---|---|
| chu_dau_tu | ten, dia_chi, nguoi_dai_dien, nguoi_co_tham_quyen, dia_diem_ban_hanh | Thông tin pháp nhân |
| goi_thau | ten, du_an, nguon_von, gia_goi_thau | Từ kế hoạch lựa chọn nhà thầu. RFP không có giá |
| goi_thau | hinh_thuc, phuong_thuc, loai_hop_dong, chia_phan | Mẫu 5A áp dụng cho một giai đoạn một túi hồ sơ |
| nam_ap_dung_cho_20XX | | Năm thay cho 20XX trong RFP |
| lich | gio_dong_thau, hoi_nghi_tien_dau_thau, ngay_hop_dong_hieu_luc_du_kien | Hội nghị phải nằm giữa ngày phát hành và hạn làm rõ |
| chinh_sach | hieu_luc_hsdt_ngay | Thường 60 đến 180 ngày |
| chinh_sach | ty_le_bao_dam_du_thau_phan_tram | Trong khoảng luật định. Dưới 50 triệu đồng thì nhà thầu chỉ cam kết trong đơn |
| chinh_sach | nam_lich_su_hop_dong, nam_hop_dong_tuong_tu, nam_doanh_thu | Theo ghi chú (1), (5), (9) Bảng số 01: thông thường 03 năm, hoặc 03 đến 05 năm trước năm đóng thầu. Mặc định lấy khoảng gần nhất hợp lệ là 03 năm |
| chinh_sach | he_so_k_doanh_thu, ty_le_hop_dong_tuong_tu_phan_tram | Doanh thu tối thiểu bằng giá gói thầu nhân k với gói dưới 12 tháng. Hợp đồng tương tự theo tỷ lệ giá gói thầu |
| chinh_sach | trong_so_tieu_chi_ky_thuat, diem_ky_thuat_toi_thieu_phan_tram, diem_toi_thieu_tung_tieu_chi_phan_tram | Tổng trọng số 100. Ngưỡng chung thường 70% đến 80% |
| chinh_sach | ty_le_bao_dam_thuc_hien_phan_tram | Từ 2% đến 10% |
| chinh_sach | tam_ung_phan_tram, bao_lanh_tam_ung, thanh_toan | Đợt 1 bằng tạm ứng nếu có. Tổng các đợt 100%. Sự kiện ghi ngắn, agent diễn đạt gắn với sản phẩm của RFP |
| chinh_sach | phat_cham_tien_do_phan_tram_ngay, phat_toi_da_phan_tram | Mức phạt tối đa theo pháp luật |
| chinh_sach | hoa_giai_toi_da_ngay, co_quan_giai_quyet_tranh_chap | Cơ chế tranh chấp |
| nhan_su_chu_chot | vi_tri, so_luong, kinh_nghiem | Không đặt yêu cầu hạn chế cạnh tranh |
| can_cu_phap_ly | luat, nghi_dinh, thong_tu | Cập nhật khi văn bản thay đổi |

Script `tinh_gia_tri.py` kiểm tra các giới hạn trên và dừng nếu tham số vi phạm.

Khi dùng cho RFP khác: sao chép file mẫu, sửa giá trị, giữ nguyên tên trường.
