# Hướng dẫn soạn master plan

Bổ sung cho qlda-loi/prompts/vai_soan_thao.md, áp dụng cho bước ke_hoach_tong_the.

1. Bảng do script sinh (kb#..., tdb#...) đã chứa số liệu, tên người, mốc. Đoạn soạn chỉ giải thích và dẫn chiếu bảng, không chép lại số liệu của bảng.
2. Tên người lấy theo vai trong tdb#vai_ban (qtda, dai_dien_nt, dau_moi_cdt, tham_quyen_cdt) hoặc tv#thanh_vien[id=...].ho_ten. Không dùng mã nội bộ (K, D1, Q2). Không đặt tên người, bộ phận không có trong dữ liệu. Bên liên quan chưa có người cụ thể thì nêu theo nhóm kèm căn cứ RFP, HSMT và ghi rõ được bổ sung tại họp khởi động.
3. Chi phí: đường cơ sở chi phí duy nhất là BAC bằng khoản A ({cp#A|tien}). Giá hợp đồng ({cp#gia_chao|tien}) là giá trị thanh toán, không gọi là đường cơ sở. Tổng EMV dùng {kb#emv}.
4. Dự phòng: không viết lại điều kiện, người đề xuất, người phê duyệt. Chỉ dẫn chiếu bảng quy tắc dùng dự phòng (tdb#du_phong), bảng này là nguồn chung với kế hoạch quản lý rủi ro và thuyết minh dự toán.
5. Chất lượng: tiêu chí và ngưỡng lấy từ ct#chi_tieu, ct#dieu_kien_cut_over, ct#bao_hanh, ngưỡng lỗi lấy từ dấu hiệu rủi ro trong rr. Không tự đặt ngưỡng mới.
6. Đường găng liệt kê đúng mã trong lich#duong_gang, không viết khoảng mã.
7. Mua sắm: chỉ nêu hạng mục có trong cp#chi_phi_khac. Khoản B chưa có danh mục chi tiết thì ghi rõ. Thuê ngoài theo Mục 6.4 E-ĐKCT và đi qua quy trình yêu cầu thay đổi.
8. Quản lý vấn đề: tám bước nhận diện, ghi sổ, giao rà soát, đánh giá, giao hành động, thực hiện, rà soát hành động, thống nhất đóng. Thẩm quyền theo cấp gắn với mức của yêu cầu thay đổi khi vấn đề cần đổi phạm vi, mốc, chi phí.
9. Kế hoạch họp đối chiếu kế hoạch họp đã cam kết trong HSDT (ket_qua/02_HSDT/HSDT.docx), gồm họp kiểm tra chức năng chính tại mốc gắn Đợt 3, họp cải tiến cuối sprint, rà soát rủi ro định kỳ, họp ban kiểm soát thay đổi.
