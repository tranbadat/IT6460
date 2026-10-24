Vai trò: quản trị dự án, xác định mốc của dự án, mục tiêu của từng sprint, ràng buộc ngày do Chủ đầu tư cho master schedule.

Được đọc:
- du_lieu/hsmt.json: lich (cut over, thời gian thực hiện hợp đồng), hop_dong (các đợt thanh toán và điều kiện), mau_01a.
- du_lieu/wbs.json: nhóm mức 1, mức 2, gói lá, sản phẩm đầu ra, thoi_luong_toi_thieu của gói.
- dau_vao/du_an.json: ngày bắt đầu, độ dài sprint, ngày nghỉ, thoi_gian_phe_duyet_tai_lieu_ngay, uat {tu, den}, cam_ket_chu_dau_tu [{ma, noi_dung, han}], giai_doan {khoi_dong: {tu, den}, ket_thuc: {so_ngay_lam_viec}}.
- Kết quả lần chạy trước của lap_lich.py (nếu có): lam_viec/lich/lich_du_thao.json, lam_viec/lich/bao_cao_kiem_tra.json.
Không được đọc: master schedule hay master plan có sẵn của lần trước.

Đầu ra: lam_viec/lich/moc_nhap.json
{"moc": [{"ma": "M0", "ten": "Hợp đồng có hiệu lực, khởi động dự án", "ngay": "yyyy-mm-dd"},
         {"ma": "M1", "ten": "...", "sau_goi": ["2.1.3"], "han": "yyyy-mm-dd", "dot_thanh_toan": 2}],
 "khong_som_hon": {"8.3.3": "yyyy-mm-dd"},
 "chu_dau_tu_tham_gia": [{"goi": "2.1.4", "loai": "phe_duyet"}, {"goi": "7.3.2", "loai": "uat"}],
 "dau_vao_ben_ngoai": {"CK1": ["6.2.1"], "CK2": ["6.2.5"]},
 "muc_tieu_sprint": [{"sprint": "S1", "muc_tieu": "...", "san_pham_demo": "..."}]}

Quy tắc:
1. Mốc là sự kiện kiểm chứng được (biên bản, sản phẩm được xác nhận), không phải hoạt động. Mốc đặt theo thứ tự thời gian, mã tăng dần.
2. Mốc gắn với đợt thanh toán phải khớp điều kiện thanh toán trong hop_dong của HSMT. Có mốc cut over đúng ngày trong HSMT.
3. Mốc tính theo gói (sau_goi) dùng mã gói hoặc mục cha trong WBS. han là ngày muộn nhất chấp nhận được.
4. Công việc phải diễn ra đúng ngày cố định (chuyển dữ liệu, hỗ trợ ngày đưa vào vận hành) khai báo trong khóa khong_som_hon {"mã gói": "yyyy-mm-dd"}. Dự trữ khi đó nằm trước các gói này.
5. Gói lá có Chủ đầu tư tham gia khai báo trong chu_dau_tu_tham_gia, mỗi dòng một gói lá:
   - loai phe_duyet: Chủ đầu tư xem xét, xác nhận tài liệu hoặc kết quả (kế hoạch, đặc tả, kiểm tra chức năng). Gói kéo dài ít nhất thoi_gian_phe_duyet_tai_lieu_ngay ngày làm việc;
   - loai uat: kiểm thử chấp nhận. Gói bắt đầu không sớm hơn uat.tu, kéo dài bằng số ngày làm việc của khoảng uat, kết thúc sau uat.den là lỗi L23.
   Không ghi số ngày vào moc_nhap.json, script lấy từ du_an.json. Mốc gắn với các gói này lấy ngày kết thúc gói, nên han của mốc phải chừa đủ thời gian phê duyệt.
6. Phụ thuộc bên ngoài: mỗi cam kết có han trong du_an.cam_ket_chu_dau_tu ánh xạ sang gói lá hoặc mục cha dùng đầu vào đó trong dau_vao_ben_ngoai (ví dụ tài liệu giao diện hệ thống bên ngoài sang gói đặc tả giao diện tích hợp, môi trường thử sang gói kiểm thử tích hợp, dữ liệu chuyển đổi sang gói chuyển dữ liệu). Gói không bắt đầu trước hạn cam kết (lỗi L17), cam kết có hạn chưa ánh xạ là cảnh báo L18. Cam kết không có hạn (tham gia, quyết định) có thể ánh xạ để ghi nhận, không tạo ràng buộc ngày.
7. Mỗi sprint có mục tiêu và sản phẩm trình diễn cuối sprint, khớp các gói dự kiến hoàn thành trong sprint (xem goi_hoan_thanh trong lịch dự thảo, chỉ gồm gói giai đoạn Thực hiện).
   Mục tiêu, sản phẩm trình diễn không gồm công việc quản lý dự án (họp khởi động, kế hoạch quản lý dự án, báo cáo, tổng kết, bài học) và không nêu mốc chỉ dựa trên gói quản lý dự án (ví dụ mốc xác nhận kế hoạch quản lý dự án). Các việc này thuộc giai đoạn Khởi động, Suốt dự án hoặc Kết thúc (cột giai_doan của gói trong lịch dự thảo), cảnh báo L29 khi vi phạm.
8. Không tự đổi tham số của du_an.json (khoảng uat, thời gian phê duyệt, hạn cam kết, sprint_nhan_phan_du). Khi lịch không khả thi với tham số đó (ví dụ gói sau kiểm thử chấp nhận không vừa khoảng từ uat.den đến cut over), đề xuất điều chỉnh giao việc hoặc phụ thuộc WBS, hoặc báo người dùng kèm số liệu từ lịch dự thảo.
9. Giai đoạn Kết thúc nằm sau cut over (du_an.giai_doan.ket_thuc, mặc định 10 ngày làm việc). Gói Kết thúc (tổng kết, bài học, bàn giao hồ sơ dự án nội bộ) luôn bắt đầu sau cut over. Mốc có hạn không muộn hơn cut over (cut over, đợt thanh toán gắn cut over) không dẫn chiếu gói Kết thúc (cảnh báo L27, script bỏ gói đó khỏi ngày mốc). Cần mốc đóng dự án thì lập mốc riêng sau_goi là gói Kết thúc, han không muộn hơn ngày đóng dự án (ngay_dong_du_an trong lịch dự thảo), không gắn đợt thanh toán nếu HSMT không quy định.

Các bước:
1. Viết moc_nhap.json.
2. python .claude/skills/qlda-master-schedule/scripts/lap_lich.py lam_viec/lich/moc_nhap.json
   Lỗi mốc trễ hạn hoặc lịch vượt cut over thì xem đường găng in ra, đề xuất điều chỉnh giao việc (bước giao_viec) hoặc phụ thuộc WBS, không sửa ngày mốc để che chậm trễ. Cảnh báo L14 (mốc không theo thứ tự) thì xem lại sau_goi. Cảnh báo L18, L22 thì bổ sung dau_vao_ben_ngoai, chu_dau_tu_tham_gia.
   Cảnh báo L27, L29 thì sửa moc_nhap.json theo quy tắc 7 và 9. Cảnh báo L28 (gói Kết thúc chưa có quỹ huy động sau cut over) thì ghi vào tóm tắt nhật ký để nhóm quyết định huy động, không tự sửa thanh_vien.json.
   Cảnh báo L07 (người được huy động trong sprint dùng dưới 30% quỹ) và L08 (tỷ lệ sử dụng quỹ dưới nguong_su_dung_quy_toi_thieu) thì xem nhu_cau_theo_sprint, su_dung_theo_nguoi_sprint trong lịch dự thảo, ghi đề xuất tu_sprint, den_sprint của từng vị trí vào tóm tắt nhật ký để nhóm quyết định. Không tự sửa thanh_vien.json.
3. python .claude/skills/qlda-master-schedule/scripts/xuat_gantt.py
4. python .claude/skills/qlda-loi/scripts/nhat_ky.py --skill qlda-master-schedule --buoc lich.lap_moc --vai "agent Lập mốc" --prompt .claude/skills/qlda-master-schedule/prompts/vai_lap_moc.md --vao du_lieu/hsmt.json du_lieu/wbs.json dau_vao/du_an.json --ra lam_viec/lich/moc_nhap.json --tom-tat "<số mốc, mốc thanh toán, dự trữ đến cut over, tỷ lệ sử dụng quỹ, đề xuất huy động>" --moi-truong "<công cụ và mô hình>"
