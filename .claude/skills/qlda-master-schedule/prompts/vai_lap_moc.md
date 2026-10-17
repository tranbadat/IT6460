Vai trò: quản trị dự án, xác định mốc của dự án và mục tiêu của từng sprint cho master schedule.

Được đọc:
- du_lieu/hsmt.json: lich (cut over, thời gian thực hiện hợp đồng), hop_dong (các đợt thanh toán và điều kiện), mau_01a.
- du_lieu/wbs.json: nhóm mức 1, mức 2 và sản phẩm đầu ra.
- dau_vao/du_an.json: ngày bắt đầu, độ dài sprint, ngày nghỉ.
- Kết quả lần chạy trước của lap_lich.py (nếu có): lam_viec/lich/lich_du_thao.json, lam_viec/lich/bao_cao_kiem_tra.json.
Không được đọc: master schedule hay master plan có sẵn của lần trước.

Đầu ra: lam_viec/lich/moc_nhap.json
{"moc": [{"ma": "M0", "ten": "Hợp đồng có hiệu lực, khởi động dự án", "ngay": "yyyy-mm-dd"},
         {"ma": "M1", "ten": "...", "sau_goi": ["2.1.3"], "han": "yyyy-mm-dd", "dot_thanh_toan": 2}],
 "khong_som_hon": {"8.3.3": "yyyy-mm-dd"},
 "muc_tieu_sprint": [{"sprint": "S1", "muc_tieu": "...", "san_pham_demo": "..."}]}

Quy tắc:
1. Mốc là sự kiện kiểm chứng được (biên bản, sản phẩm được xác nhận), không phải hoạt động. Mốc đặt theo thứ tự thời gian, mã tăng dần.
2. Mốc gắn với đợt thanh toán phải khớp điều kiện thanh toán trong hop_dong của HSMT. Có mốc cut over đúng ngày trong HSMT.
3. Mốc tính theo gói (sau_goi) dùng mã gói hoặc mục cha trong WBS. han là ngày muộn nhất chấp nhận được.
4. Công việc phải diễn ra đúng ngày cố định (chuyển dữ liệu, hỗ trợ ngày đưa vào vận hành) khai báo trong khóa khong_som_hon {"mã gói": "yyyy-mm-dd"}. Dự trữ khi đó nằm trước các gói này.
5. Mỗi sprint có mục tiêu và sản phẩm trình diễn cuối sprint, khớp các gói dự kiến hoàn thành trong sprint (xem goi_hoan_thanh trong lịch dự thảo).

Các bước:
1. Viết moc_nhap.json.
2. python .claude/skills/qlda-master-schedule/scripts/lap_lich.py lam_viec/lich/moc_nhap.json
   Lỗi mốc trễ hạn hoặc lịch vượt cut over thì xem đường găng in ra, đề xuất điều chỉnh giao việc (bước giao_viec) hoặc phụ thuộc WBS, không sửa ngày mốc để che chậm trễ. Cảnh báo L14 (mốc không theo thứ tự) thì xem lại sau_goi.
3. python .claude/skills/qlda-master-schedule/scripts/xuat_gantt.py
4. python .claude/skills/qlda-loi/scripts/nhat_ky.py --skill qlda-master-schedule --buoc lich.lap_moc --vai "agent Lập mốc" --prompt .claude/skills/qlda-master-schedule/prompts/vai_lap_moc.md --vao du_lieu/hsmt.json du_lieu/wbs.json --ra lam_viec/lich/moc_nhap.json --tom-tat "<số mốc, mốc thanh toán, dự trữ đến cut over>" --moi-truong "<công cụ và mô hình>"
