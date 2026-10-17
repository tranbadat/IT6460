---
name: qlda-master-schedule
description: Lập master schedule có ràng buộc nguồn lực từ WBS, giao việc, lịch làm việc và mốc hợp đồng - đường găng, dự trữ, mốc gắn đợt thanh toán, mục tiêu và sản phẩm demo từng sprint, xuất Excel Gantt có công thức. Dùng khi người dùng muốn lập, kiểm tra hoặc cập nhật tiến độ tổng thể, Gantt, sprint, mốc dự án.
---

# Master schedule

Đầu vào: du_lieu/wbs.json, du_lieu/phan_cong.json (qlda-phan-cong), dau_vao/thanh_vien.json, dau_vao/du_an.json (ngày bắt đầu, ngày nghỉ, độ dài sprint, thời gian phê duyệt tài liệu, khoảng kiểm thử chấp nhận uat, cam kết của Chủ đầu tư, ngưỡng sử dụng quỹ), du_lieu/hsmt.json (cut over, đợt thanh toán).

## Quy trình

1. Agent Lập mốc theo `prompts/vai_lap_moc.md`, viết lam_viec/lich/moc_nhap.json: mốc (ngày cố định hoặc sau gói), hạn, đợt thanh toán, gói có Chủ đầu tư tham gia (chu_dau_tu_tham_gia), ánh xạ cam kết đầu vào của Chủ đầu tư sang gói (dau_vao_ben_ngoai), mục tiêu và sản phẩm demo từng sprint.
2. `python .claude/skills/qlda-master-schedule/scripts/lap_lich.py lam_viec/lich/moc_nhap.json`
   Tính thời lượng gói theo MD và tỷ lệ tham gia, lấy giá trị lớn hơn với thời lượng tối thiểu (thoi_luong_toi_thieu của WBS, thời gian phê duyệt tài liệu, khoảng uat). Gói có thời lượng tối thiểu kéo dài đủ thời lượng, người làm chỉ bận phần MD của mình. Xếp lịch theo nguồn lực (mỗi người làm lần lượt, ưu tiên gói có thời điểm bắt đầu muộn nhất sớm hơn), gói phụ thuộc cam kết không bắt đầu trước hạn cam kết, đường găng CPM, dự trữ, mốc. Lỗi khi vượt cut over, mốc trễ hạn, sprint thiếu mục tiêu, gói bắt đầu trước hạn cam kết (L17), kiểm thử chấp nhận vượt khoảng uat (L23), ràng buộc Chủ đầu tư khai báo sai (L19, L24). Cảnh báo cam kết có hạn chưa gắn gói (L18), tham số Chủ đầu tư chưa gắn gói (L22), người được huy động dùng dưới 30% quỹ sprint (L07), tỷ lệ sử dụng quỹ dưới nguong_su_dung_quy_toi_thieu (L08). Khi lỗi, lịch dự thảo ở lam_viec/lich/lich_du_thao.json và đường găng in ra màn hình.
   Không sửa ngày mốc để che chậm trễ. Điều chỉnh giao việc (người hỗ trợ, cân bằng tải) hoặc phụ thuộc WBS rồi chạy lại.
3. `python .claude/skills/qlda-master-schedule/scripts/xuat_gantt.py`
   Ra ket_qua/04_Master_schedule/Master_schedule.xlsx: Gantt theo tuần có cột ràng buộc ngày, sprint, mốc, tải nguồn lực (ô vàng là dùng dưới ngưỡng quỹ), nhu cầu theo loại công việc và sprint (Nhu_cau), cam kết và gói có Chủ đầu tư tham gia (Cam_ket). Công thức được tính lại và đối chiếu với lich.json.
4. Agent Kiểm tra lớp B: tính khả thi đến cut over, mốc khớp điều kiện thanh toán của HSMT, tải nguồn lực không vượt.

Đầu ra: du_lieu/lich.json, Master_schedule.xlsx. Dùng bởi WBS (tài liệu), rủi ro, dự toán, HSDT, master plan, phân công, báo cáo tiến độ.
Khóa của lich.json dùng cho bước sau: ty_le_su_dung_quy (tổng MD công việc chia tổng quỹ huy động, bước hsdt so với du_an.nguong_su_dung_quy_toi_thieu), nhu_cau_theo_sprint (MD theo loại công việc và sprint), su_dung_theo_nguoi_sprint (MD, quỹ, tỷ lệ từng người theo sprint, sprint dưới ngưỡng), cam_ket_chu_dau_tu (hạn, gói phụ thuộc, ngày bắt đầu sớm nhất), chu_dau_tu_tham_gia (gói, loại, thời lượng tối thiểu, ngày), rang_buoc và thoi_luong_toi_thieu của gói lá.
