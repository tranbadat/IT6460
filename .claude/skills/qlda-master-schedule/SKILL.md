---
name: qlda-master-schedule
description: Lập master schedule có ràng buộc nguồn lực từ WBS, giao việc, lịch làm việc và mốc hợp đồng - đường găng, dự trữ, mốc gắn đợt thanh toán, mục tiêu và sản phẩm demo từng sprint, xuất Excel Gantt có công thức. Dùng khi người dùng muốn lập, kiểm tra hoặc cập nhật tiến độ tổng thể, Gantt, sprint, mốc dự án.
---

# Master schedule

Đầu vào: du_lieu/wbs.json, du_lieu/phan_cong.json (qlda-phan-cong), dau_vao/thanh_vien.json, dau_vao/du_an.json (ngày bắt đầu, ngày nghỉ, độ dài sprint), du_lieu/hsmt.json (cut over, đợt thanh toán).

## Quy trình

1. Agent Lập mốc theo `prompts/vai_lap_moc.md`, viết lam_viec/lich/moc_nhap.json: mốc (ngày cố định hoặc sau gói), hạn, đợt thanh toán, mục tiêu và sản phẩm demo từng sprint.
2. `python .claude/skills/qlda-master-schedule/scripts/lap_lich.py lam_viec/lich/moc_nhap.json`
   Tính thời lượng gói theo MD và tỷ lệ tham gia, xếp lịch theo nguồn lực (mỗi người làm lần lượt, ưu tiên gói có thời điểm bắt đầu muộn nhất sớm hơn), đường găng CPM, dự trữ, mốc. Lỗi khi vượt cut over, mốc trễ hạn, sprint thiếu mục tiêu. Khi lỗi, lịch dự thảo ở lam_viec/lich/lich_du_thao.json và đường găng in ra màn hình.
   Không sửa ngày mốc để che chậm trễ. Điều chỉnh giao việc (người hỗ trợ, cân bằng tải) hoặc phụ thuộc WBS rồi chạy lại.
3. `python .claude/skills/qlda-master-schedule/scripts/xuat_gantt.py`
   Ra ket_qua/04_Master_schedule/Master_schedule.xlsx: Gantt theo tuần, sprint, mốc, tải nguồn lực. Công thức được tính lại và đối chiếu với lich.json.
4. Agent Kiểm tra lớp B: tính khả thi đến cut over, mốc khớp điều kiện thanh toán của HSMT, tải nguồn lực không vượt.

Đầu ra: du_lieu/lich.json, Master_schedule.xlsx. Dùng bởi WBS (tài liệu), rủi ro, dự toán, HSDT, master plan, phân công, báo cáo tiến độ.
