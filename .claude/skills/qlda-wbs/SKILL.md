---
name: qlda-wbs
description: Lập cấu trúc phân rã công việc (WBS) cho gói thầu từ HSMT và RFP - phân rã ba mức, ước lượng MD từng gói, loại công việc, sản phẩm, phụ thuộc, truy vết yêu cầu RFP và hạng mục Mẫu 01A, kiểm tra quy tắc 100%, xuất tài liệu WBS từng nhóm và tổng hợp. Dùng khi người dùng muốn lập, hoàn thiện, kiểm tra hoặc cập nhật WBS.
---

# WBS

Đầu vào: du_lieu/hsmt.json, du_lieu/rfp_yeu_cau.json (skill hsmt-mau-5a), dau_vao/du_an.json.
Tài liệu WBS còn dùng giao việc và master schedule (nếu đã có) để ghi người chịu trách nhiệm, thời gian.

## Bước dữ liệu (wbs)

1. Agent Lập WBS theo `prompts/vai_lap_wbs.md` và `references/quy_tac_wbs.md`, viết lam_viec/wbs/wbs_nhap.json.
2. `python .claude/skills/qlda-wbs/scripts/kiem_tra_wbs.py lam_viec/wbs/wbs_nhap.json`
   Kiểm tra mã phân cấp, quy tắc 100%, gói lá có MD, loại công việc, sản phẩm, phụ thuộc không vòng, mọi hạng mục Mẫu 01A được phủ, mọi yêu cầu RFP được truy vết, cỡ gói 2 đến 14 MD. Còn lỗi thì sửa và chạy lại, tối đa 3 lần.
3. Đạt thì ghi du_lieu/wbs.json.

## Bước tài liệu (tai_lieu_wbs)

Sau khi có giao việc (qlda-phan-cong) và master schedule (qlda-master-schedule):
1. `python .claude/skills/qlda-wbs/scripts/xuat_wbs.py [--ngay yyyy-mm-dd]`
   Mỗi nhóm mức 1 một tệp và một tệp tổng hợp trong ket_qua/03_WBS/. Mục cha WBS in đậm, còn lại theo van_phong.md. Mỗi tệp được kiểm tra lớp A theo `dac_ta/tai_lieu_wbs.json`.
2. Agent Kiểm tra lớp B (qlda-loi/prompts/vai_kiem_tra.md): phạm vi đủ theo RFP, khối lượng hợp lý, sản phẩm kiểm chứng được.

## Khi WBS thay đổi

Thay đổi sau khi có giao việc, lịch, dự toán phải đi qua yêu cầu thay đổi (skill qlda-change) nếu đã ký hợp đồng. Sửa wbs_nhap.json, chạy lại bước 2, rồi `python .claude/skills/qlda-loi/scripts/chay.py anh_huong wbs` để cập nhật các bước sau theo thứ tự. Tài liệu WBS xuất lại theo yêu cầu thay đổi dùng `xuat_wbs.py --ngay yyyy-mm-dd` (ngày cập nhật theo lịch dự án). Mặc định tài liệu WBS đề ngày ký đơn dự thầu.
