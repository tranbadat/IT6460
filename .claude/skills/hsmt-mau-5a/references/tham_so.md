# Tham số chủ đầu tư

RFP chỉ nêu yêu cầu nghiệp vụ, mốc và điều khoản hợp đồng cơ bản. HSMT theo Mẫu 5A còn cần các giá trị do chủ đầu tư hoặc bên lập HSMT quyết định. Các giá trị này nằm trong `tham_so_chu_dau_tu.json`. File chỉ chứa giá trị và lựa chọn ngắn, không chứa câu văn của HSMT.

| Nhóm | Trường | Ý nghĩa và giới hạn |
|---|---|---|
| chu_dau_tu | ten, dia_chi, nguoi_dai_dien, nguoi_co_tham_quyen, dia_diem_ban_hanh | Thông tin pháp nhân. dia_chi là địa chỉ cụ thể (số nhà, đường, phường, tỉnh hoặc thành phố), tinh_gia_tri.py báo lỗi nếu chỉ ghi theo tên Chủ đầu tư |
| chu_dau_tu | dien_thoai, fax, so_tai_khoan, ma_so_thue | Bắt buộc. Điền vào E-CDNT 5.1 (c), 7.5, 38.1 và E-ĐKC 1.3, 4.1 (Mẫu 5A yêu cầu ghi đủ trước khi phát hành, không hoãn đến khi hoàn thiện hợp đồng). Số điện thoại, fax ghi dạng trong nước, Mục 4.1 E-ĐKCT tự thêm mã quốc gia +84 |
| goi_thau | ten, du_an, nguon_von, gia_goi_thau | Từ kế hoạch lựa chọn nhà thầu. RFP không có giá |
| goi_thau | hinh_thuc, phuong_thuc, loai_hop_dong, chia_phan | Mẫu 5A áp dụng cho một giai đoạn một túi hồ sơ |
| nam_ap_dung_cho_20XX | | Năm thay cho 20XX trong RFP |
| lich | gio_dong_thau, hoi_nghi_tien_dau_thau, ngay_hop_dong_hieu_luc_du_kien | Hội nghị phải nằm giữa ngày phát hành và hạn làm rõ |
| chinh_sach | hieu_luc_hsdt_ngay | Thường 60 đến 180 ngày |
| chinh_sach | ty_le_bao_dam_du_thau_phan_tram | Trong khoảng luật định. Dưới 50 triệu đồng thì nhà thầu chỉ cam kết trong đơn |
| chinh_sach | nam_lich_su_hop_dong, nam_hop_dong_tuong_tu, nam_doanh_thu | Theo ghi chú (1), (5), (9) Bảng số 01: thông thường 03 năm, hoặc 03 đến 05 năm trước năm đóng thầu. Mặc định lấy khoảng gần nhất hợp lệ là 03 năm |
| chinh_sach | thue_gtgt_goi_thau, can_cu_thue_gtgt, thue_suat_gtgt_phan_tram | Bắt buộc thue_gtgt_goi_thau: `khong_chiu_thue` (cần can_cu_thue_gtgt, Bảng số 01 dòng 3 nêu căn cứ, thuế bằng 0) hoặc `chiu_thue` (cần thue_suat_gtgt_phan_tram). Doanh thu tối thiểu theo ghi chú (6) Bảng số 01: (giá gói thầu trừ thuế GTGT) nhân k, giá gói thầu đã gồm thuế |
| chinh_sach | hop_dong_tuong_tu_cong_gop, hang_muc_tuong_tu | Bắt buộc hop_dong_tuong_tu_cong_gop (true hoặc false). false: Bảng số 01 dòng 4 chỉ yêu cầu tối thiểu 01 hợp đồng tương tự đạt giá trị. true: cần hang_muc_tuong_tu [{ten, gia_tri}] nêu hạng mục chính và giá trị tối thiểu từng hạng mục theo ghi chú (11), thiếu thì tinh_gia_tri.py báo lỗi |
| chinh_sach | he_so_k_doanh_thu, ty_le_hop_dong_tuong_tu_phan_tram | Doanh thu tối thiểu bằng giá gói thầu nhân k với gói dưới 12 tháng. Hợp đồng tương tự theo tỷ lệ giá gói thầu |
| chinh_sach | trong_so_tieu_chi_ky_thuat, diem_ky_thuat_toi_thieu_phan_tram, diem_toi_thieu_tung_tieu_chi_phan_tram | Tổng trọng số 100. Ngưỡng chung thường 70% đến 80% |
| chinh_sach | ty_le_bao_dam_thuc_hien_phan_tram | Từ 2% đến 10% |
| chinh_sach | tam_ung_phan_tram, bao_lanh_tam_ung, thanh_toan | Đợt 1 bằng tạm ứng nếu có. Tổng các đợt 100%. Sự kiện ghi ngắn, agent diễn đạt gắn với sản phẩm của RFP |
| chinh_sach | phat_cham_tien_do_phan_tram_ngay, phat_toi_da_phan_tram | Mức phạt tối đa theo pháp luật |
| chinh_sach | phat_khac_phuc_sai_sot_phan_tram | Bắt buộc. Tỷ lệ phạt (% chi phí cần thiết để khắc phục, lớn hơn 0, không quá 100) khi nhà thầu không kịp thời khắc phục sai sót, Mục 15 E-ĐKCT. Còn null thì lap_khung.py giữ câu mẫu kèm dấu [Chủ đầu tư quyết định: tỷ lệ %], verify_hsmt.py kết luận cho_nguoi_dung |
| chinh_sach | boi_thuong_thiet_hai | Bắt buộc. Cách bồi thường thiệt hại tại Mục 15 E-ĐKCT, một trong hai cách của mẫu: `toan_bo_thiet_hai_thuc_te`, hoặc cụm ngắn nêu mức và phương thức bồi thường xác định. Còn null thì giữ câu mẫu kèm dấu chờ, kết luận cho_nguoi_dung |
| phan_dinh | ha_tang_ben_cung_cap | Bắt buộc. Đối tượng có bốn khóa `may_chu`, `duong_truyen`, `phan_mem_nen`, `moi_truong_kiem_thu`, mỗi khóa là `chu_dau_tu` hoặc `nha_thau` (bên cung cấp, chi phí của nhà thầu tính trong giá trọn gói). Chương V mục 3.5 |
| phan_dinh | thong_tin_he_thong_hien_co | Bắt buộc. `{ten, tai_lieu, thoi_han_cung_cap_ngay}`: tên hệ thống hiện có cần tích hợp, danh sách cụm ngắn các tài liệu, giao diện Chủ đầu tư cung cấp, số ngày kể từ ngày hợp đồng có hiệu lực. tinh_gia_tri.py tính hạn cung cấp, hạn phải trước ngày cut over. Chương V mục 3.5 |
| phan_dinh | cau_hinh_ha_tang | Bắt buộc. `nha_thau_de_xuat`: máy chủ, đường truyền, phần mềm nền do Chủ đầu tư cung cấp theo cấu hình tối thiểu nhà thầu đề xuất trong E-HSDT, hai bên thống nhất khi xác nhận đặc tả trước đợt thanh toán gắn với xác nhận đặc tả. Hoặc đối tượng `{may_chu, duong_truyen, phan_mem_nen}` nêu cấu hình do Chủ đầu tư quy định |
| phan_dinh | thoi_han_ha_tang | Bắt buộc. `{moi_truong_thu_he_thong_hien_co, ha_tang_van_hanh_chinh_thuc, thay_doi_he_thong_hien_co}` dạng dd/mm (khóa cuối: hạn Chủ đầu tư hoàn thành thay đổi phía hệ thống hiện có, E-ĐKC 18 (e) phủ cả trường hợp này): ngày Chủ đầu tư bàn giao môi trường thử của hệ thống hiện có và hạ tầng vận hành chính thức (máy chủ, đường truyền, phần mềm nền do Chủ đầu tư cung cấp). tinh_gia_tri.py tính ngày đầy đủ theo năm áp dụng, kiểm tra từ ngày hợp đồng có hiệu lực đến trước cut over |
| phan_dinh | kiem_thu_van_hanh_tren | Bắt buộc. `ha_tang_chinh_thuc` hoặc `moi_truong_kiem_thu` (môi trường của nhà thầu): nơi kiểm thử vận hành và đo yêu cầu phi chức năng |
| phan_dinh | thay_doi_he_thong_hien_co | Bắt buộc. `chu_dau_tu` hoặc `nha_thau`: bên thực hiện thay đổi phía hệ thống hiện có để trao đổi dữ liệu với hệ thống mới |
| phan_dinh | dieu_kien_do_phi_chuc_nang | Bắt buộc. `nha_thau_de_xuat` (nhà thầu đề xuất điều kiện đo, hai bên xác nhận trong đặc tả trước đợt thanh toán gắn với xác nhận đặc tả), hoặc `{so_nguoi_dung_dong_thoi, ty_le_san_sang_phan_tram}` do Chủ đầu tư quy định. Chương V mục 3.5 |
| chinh_sach | phat_khong_huy_dong_nhan_su_phan_tram_ngay | Bắt buộc. Từ 0 đến phat_toi_da_phan_tram. Bằng 0: không áp dụng phạt riêng, E-ĐKC 15 không có câu phạt nhân sự, Mục 2.2 điểm c dẫn chiếu Mục 21 E-ĐKC, 21.2 E-ĐKCT và phạt chậm tiến độ tại Mục 15 E-ĐKCT. Lớn hơn 0: E-ĐKC 15 thêm câu phạt (% giá hợp đồng mỗi ngày, tính chung trong mức phạt tối đa), điểm c dẫn chiếu khoản phạt này |
| chinh_sach | gia_han_khi_chu_dau_tu_cung_cap_cham | Bắt buộc (true hoặc false). true: E-ĐKC 18 (e) ghi trường hợp Chủ đầu tư cung cấp chậm tài liệu, hạ tầng, môi trường so với thời hạn tại mục 3.5 Chương V thì các mốc liên quan được lùi tương ứng số ngày chậm, câu dẫn mục 3.5 dẫn chiếu 18 (e). false: 18 (e) ghi không có, câu dẫn mục 3.5 dẫn sang Mục 17 E-ĐKC |
| chinh_sach | hoa_giai_toi_da_ngay, co_quan_giai_quyet_tranh_chap | Cơ chế tranh chấp |
| nhan_su_chu_chot | vi_tri, so_luong, kinh_nghiem | Không đặt yêu cầu hạn chế cạnh tranh |
| can_cu_phap_ly | luat, nghi_dinh, thong_tu | Cập nhật khi văn bản thay đổi |

Script `tinh_gia_tri.py` kiểm tra các giới hạn trên và dừng nếu tham số vi phạm.

Tham số bắt buộc (danh sách trong `scripts/quy_uoc.py`, THAM_SO_BAT_BUOC) còn null hoặc chưa có thì không tự đặt giá trị: script giữ câu mẫu kèm dấu [Chủ đầu tư quyết định ...], `tinh_gia_tri.py` cảnh báo, `verify_hsmt.py` ghi TS01 và kết luận cho_nguoi_dung (chưa hoàn tất, chờ người dùng). Agent hỏi người dùng giá trị rồi chạy lại từ bước chuẩn bị.

Khi dùng cho RFP khác: sao chép file mẫu, sửa giá trị, giữ nguyên tên trường.
