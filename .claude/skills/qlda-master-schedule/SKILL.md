---
name: qlda-master-schedule
description: Lập master schedule có ràng buộc nguồn lực từ WBS, giao việc, lịch làm việc và mốc hợp đồng - giai đoạn Khởi động, Thực hiện (sprint), Kết thúc, đường găng, dự trữ, mốc gắn đợt thanh toán, mục tiêu và sản phẩm demo từng sprint, xuất Excel Gantt có công thức, bản phát hành cuối mỗi sprint. Dùng khi người dùng muốn lập, kiểm tra hoặc cập nhật tiến độ tổng thể, Gantt, sprint, mốc dự án.
---

# Master schedule

Đầu vào: du_lieu/wbs.json, du_lieu/phan_cong.json (qlda-phan-cong), dau_vao/thanh_vien.json, dau_vao/du_an.json (ngày bắt đầu, ngày nghỉ, độ dài sprint, thời gian phê duyệt tài liệu, khoảng kiểm thử chấp nhận uat, cam kết của Chủ đầu tư, ngưỡng sử dụng quỹ, giai đoạn), du_lieu/hsmt.json (cut over, đợt thanh toán).

## Giai đoạn dự án

| Giai đoạn | Thời gian | Gói |
|---|---|---|
| Khởi động | du_an.giai_doan.khoi_dong {tu, den}. Chưa khai báo thì 5 ngày làm việc đầu dự án | Gói quản lý dự án thuộc mục mức 2 đầu của nhóm WBS 1 (khởi động, lập kế hoạch) |
| Thực hiện | Ngày bắt đầu đến cut over, chia sprint | Gói phát triển, kiểm thử, triển khai, gói nhóm 1 không phải loại PM, QA |
| Suốt dự án | Cửa sổ sprint của gói dàn trải | Gói quản lý dự án dàn trải (giám sát, kiểm soát thay đổi, hồ sơ thanh toán) |
| Kết thúc | du_an.giai_doan.ket_thuc.so_ngay_lam_viec ngày làm việc sau cut over. Chưa khai báo thì 10 ngày | Gói quản lý dự án thuộc mục mức 2 cuối của nhóm WBS 1 (nghiệm thu, đóng dự án), không dàn trải |

Gói lá ghi giai_doan (khoi_dong, thuc_hien, xuyen_suot, ket_thuc) trong WBS thì dùng giá trị đó, không ghi thì suy theo bảng trên (loi.phan_giai_doan, nhóm WBS 1 và loại PM, QA). Gói quản lý dự án không gắn sprint phát triển: lịch, Gantt và tài liệu WBS ghi giai đoạn thay cho sprint, mục tiêu, sản phẩm trình diễn và goi_hoan_thanh của sprint không gồm các gói này. Gói Kết thúc bắt đầu sau cut over, không làm lùi cut over, không tính vào đường găng, ngày kết thúc dự kiến và dự trữ đến cut over (dự trữ chỉ tính trên gói phải xong trước cut over).

## Quy trình

1. Agent Lập mốc theo `prompts/vai_lap_moc.md`, viết lam_viec/lich/moc_nhap.json: mốc (ngày cố định hoặc sau gói), hạn, đợt thanh toán, gói có Chủ đầu tư tham gia (chu_dau_tu_tham_gia), ánh xạ cam kết đầu vào của Chủ đầu tư sang gói (dau_vao_ben_ngoai), mục tiêu và sản phẩm demo từng sprint.
2. `python .claude/skills/qlda-master-schedule/scripts/lap_lich.py lam_viec/lich/moc_nhap.json`
   Tính thời lượng gói theo MD và tỷ lệ tham gia, lấy giá trị lớn hơn với thời lượng tối thiểu (thoi_luong_toi_thieu của WBS, thời gian phê duyệt tài liệu, khoảng uat). Gói có thời lượng tối thiểu kéo dài đủ thời lượng, người làm chỉ bận phần MD của mình. Xếp lịch theo nguồn lực (mỗi người làm lần lượt, ưu tiên gói có thời điểm bắt đầu muộn nhất sớm hơn), gói phụ thuộc cam kết không bắt đầu trước hạn cam kết, đường găng CPM, dự trữ, mốc. Lỗi khi vượt cut over, mốc trễ hạn, sprint thiếu mục tiêu, gói bắt đầu trước hạn cam kết (L17), kiểm thử chấp nhận vượt khoảng uat (L23), ràng buộc Chủ đầu tư khai báo sai (L19, L24), giai đoạn khai báo sai (L25), gói Kết thúc xong sau ngày đóng dự án hoặc gói trước cut over phụ thuộc gói Kết thúc (L26). Cảnh báo cam kết có hạn chưa gắn gói (L18), tham số Chủ đầu tư chưa gắn gói (L22), người được huy động dùng dưới 30% quỹ sprint (L07), tỷ lệ sử dụng quỹ dưới nguong_su_dung_quy_toi_thieu (L08), mốc có hạn đến cut over dẫn chiếu gói Kết thúc, ngày mốc không tính gói đó (L27), MD giai đoạn Kết thúc chưa có quỹ huy động sau cut over (L28, nhóm quyết định huy động), mục tiêu sprint nêu công việc quản lý dự án (L29). Khi lỗi, lịch dự thảo ở lam_viec/lich/lich_du_thao.json và đường găng in ra màn hình.
   Không sửa ngày mốc để che chậm trễ. Điều chỉnh giao việc (người hỗ trợ, cân bằng tải) hoặc phụ thuộc WBS rồi chạy lại.
   Lập lại từ một ngày (sau yêu cầu thay đổi, cập nhật tiến độ): moc_nhap.json khóa `lap_lai_tu` {ngay, lich_goc, ma_cr} (qlda-change ap_dung ghi) hoặc `lap_lich.py <moc_nhap> --tu-ngay yyyy-mm-dd [--lich-goc <tệp>]` (scripts/lap_lai.py). Gói đã xong trước ngày đó giữ ngày thực tế (nhật ký công việc) hoặc ngày của lịch gốc, gói đang làm giữ ngày bắt đầu và chỉ xếp phần MD còn lại của từng người, gói chưa bắt đầu và gói mới xếp từ ngày đó. lich.json ghi phan_chi_so (khoảng làm của từng người) và trang_thai_lap_lai của gói. Tốc độ mỗi ngày của từng người (lap_lai.toc_do_ngay: tỷ lệ tham gia trừ việc dàn trải) dùng chung với kiem_tra_giao_viec.py của qlda-phan-cong; phan_bo làm tròn theo từng người sao cho tổng các kỳ của một người bằng tổng phan_nguoi của người đó (khớp tải theo người của phan_cong.json và tài liệu phân công). Khi cut over lùi, du_an.sprint.cut_over_goc giữ nguyên các sprint đã lập (loi.danh_sach_sprint), ngày thêm chia thành sprint mới.
3. `python .claude/skills/qlda-master-schedule/scripts/xuat_gantt.py`
   Ra ket_qua/04_Master_schedule/Master_schedule.xlsx: Gantt theo tuần đến hết giai đoạn Kết thúc có cột giai đoạn, sprint (gói quản lý dự án ghi giai đoạn thay cho sprint), ràng buộc ngày, sheet Giai_doan, sprint, mốc, tải nguồn lực (ô vàng là dùng dưới ngưỡng quỹ), nhu cầu theo loại công việc và sprint (Nhu_cau), cam kết và gói có Chủ đầu tư tham gia (Cam_ket). Công thức được tính lại và đối chiếu với lich.json.
4. Agent Kiểm tra lớp B: tính khả thi đến cut over, mốc khớp điều kiện thanh toán của HSMT, tải nguồn lực không vượt.

## Bản phát hành theo sprint (giai đoạn thực hiện)

Cuối mỗi sprint, sau khi nhóm ghi dữ liệu thực tế:
`python .claude/skills/qlda-master-schedule/scripts/phat_hanh.py S1 [S2 ...] [--ghi-chu "..."]` hoặc `phat_hanh.py tat_ca [--ke-hoach]`
- Mỗi sprint một bản R<n>, ngày là ngày cuối sprint. Bản của sprint có ngày cut over là bản phát hành chính thức.
- Gói hoàn thành lấy từ dau_vao/thuc_te/hoan_thanh.csv (100% trong kỳ). Chưa có dữ liệu từ ngày đầu sprint thì lấy gói kế hoạch xong trong sprint, nguồn ghi kế hoạch. Chỉ gói giai đoạn Thực hiện.
- Tính năng: hạng mục Mẫu 01A, yêu cầu RFP được phủ và trạng thái đủ gói tích lũy. Lỗi đã sửa, lỗi còn mở theo dau_vao/thuc_te/loi.csv. CR đã phê duyệt có gói hoàn thành trong bản (du_lieu/thay_doi.json). Ghi chú phát hành do script tóm tắt cộng --ghi-chu.
- tat_ca lập các sprint đã kết thúc đến ngày hiện hành (biến môi trường QLDA_NGAY khi mô phỏng).
Ra du_lieu/phat_hanh.json. Có du_lieu/mo_phong.json thì tóm tắt ghi theo số liệu thực tế mô phỏng. Sau ký hợp đồng, mỗi phiên bản tài liệu mới ghi khóa phat_hanh là bản hiện hành tại ngày tài liệu (qlda-phien-ban).

Đầu ra: du_lieu/lich.json, Master_schedule.xlsx, du_lieu/phat_hanh.json. Dùng bởi WBS (tài liệu), rủi ro, dự toán, HSDT, master plan, phân công, báo cáo tiến độ.
Khóa của lich.json dùng cho bước sau: giai_doan (Khởi động, Suốt dự án, Thực hiện, Kết thúc: tu, den, so_ngay, goi), ngay_dong_du_an, giai_doan và giai_doan_hien_thi của mỗi gói, kỳ KT trong phan_bo và nhu_cau_theo_sprint (MD giai đoạn Kết thúc, quỹ 0), ty_le_su_dung_quy (tổng MD công việc chia tổng quỹ huy động, bước hsdt so với du_an.nguong_su_dung_quy_toi_thieu), nhu_cau_theo_sprint (MD theo loại công việc và sprint), su_dung_theo_nguoi_sprint (MD, quỹ, tỷ lệ từng người theo sprint, sprint dưới ngưỡng), cam_ket_chu_dau_tu (hạn, gói phụ thuộc, ngày bắt đầu sớm nhất), chu_dau_tu_tham_gia (gói, loại, thời lượng tối thiểu, ngày), rang_buoc và thoi_luong_toi_thieu của gói lá.
