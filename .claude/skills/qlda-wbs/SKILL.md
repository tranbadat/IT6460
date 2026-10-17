---
name: qlda-wbs
description: Lập cấu trúc phân rã công việc (WBS) cho gói thầu từ HSMT và RFP - phân rã ba mức, ước lượng MD từng gói, loại công việc, sản phẩm, phụ thuộc, truy vết yêu cầu RFP và hạng mục Mẫu 01A, kiểm tra quy tắc 100%, xuất tài liệu WBS từng nhóm và tổng hợp. Dùng khi người dùng muốn lập, hoàn thiện, kiểm tra hoặc cập nhật WBS.
---

# WBS

Đầu vào: du_lieu/hsmt.json, du_lieu/rfp_yeu_cau.json (skill hsmt-mau-5a), dau_vao/du_an.json, dau_vao/uoc_luong.json (căn cứ ước lượng của nhóm), dau_vao/nha_thau.json (hợp đồng tương tự, ngày ký đơn).
Tài liệu WBS còn dùng giao việc và master schedule (nếu đã có) để ghi người chịu trách nhiệm, thời gian.

## Bước dữ liệu (wbs)

1. Agent Lập WBS theo `prompts/vai_lap_wbs.md` và `references/quy_tac_wbs.md`, viết lam_viec/wbs/wbs_nhap.json.
2. `python .claude/skills/qlda-wbs/scripts/kiem_tra_wbs.py lam_viec/wbs/wbs_nhap.json`
   Kiểm tra mã phân cấp, quy tắc 100%, gói lá có MD, loại công việc, sản phẩm, thời lượng tối thiểu (W19), phụ thuộc không vòng, mọi hạng mục Mẫu 01A được phủ, mọi yêu cầu RFP được truy vết, nghiệp vụ bán hàng thông dụng (W33), cỡ gói 2 đến 14 MD, gói sửa lỗi của kiểm thử phân hệ (W65).
   Căn cứ ước lượng:
   - thiếu uoc_luong.json: cảnh báo W60, bỏ qua các kiểm tra dưới (dữ liệu cũ vẫn chạy);
   - nhóm mức 1 thiếu can_cu_uoc_luong: lỗi W61;
   - tổng lệch tong_md quá 0,5 MD: lỗi W62;
   - nhóm lệch tong_theo_nhom quá dung_sai_nhom: lỗi W63;
   - tổng lệch quá 25% so với trung bình quy_mo_md của hợp đồng tương tự mà không có giai_trinh_tuong_tu: cảnh báo W64.
   Còn lỗi thì sửa và chạy lại, tối đa 3 lần.
3. Đạt thì ghi du_lieu/wbs.json, gồm khối can_cu_uoc_luong (phương pháp, loại ước lượng, khoảng sai số quy ra MD, các bước, bảng theo nhóm, đối chiếu từng hợp đồng tương tự, giải trình).

## Bước tài liệu (tai_lieu_wbs)

Sau khi có giao việc (qlda-phan-cong) và master schedule (qlda-master-schedule):
1. `python .claude/skills/qlda-wbs/scripts/xuat_wbs.py [--ngay yyyy-mm-dd]`
   Mỗi nhóm mức 1 một tệp và một tệp tổng hợp trong ket_qua/03_WBS/. Tệp tổng hợp có mục Căn cứ ước lượng khi wbs.json có can_cu_uoc_luong. Mục cha WBS in đậm, còn lại theo van_phong.md. Mỗi tệp được kiểm tra lớp A theo `dac_ta/tai_lieu_wbs.json`.
2. Agent Kiểm tra lớp B (qlda-loi/prompts/vai_kiem_tra.md): phạm vi đủ theo RFP, khối lượng hợp lý và có căn cứ, sản phẩm kiểm chứng được.

## Khi WBS thay đổi

Thay đổi sau khi có giao việc, lịch, dự toán phải đi qua yêu cầu thay đổi (skill qlda-change) nếu đã ký hợp đồng. Sửa wbs_nhap.json, chạy lại bước 2, rồi `python .claude/skills/qlda-loi/scripts/chay.py anh_huong wbs` để cập nhật các bước sau theo thứ tự. Tài liệu WBS xuất lại theo yêu cầu thay đổi dùng `xuat_wbs.py --ngay yyyy-mm-dd` (ngày cập nhật theo lịch dự án), ngày này được giữ khi xuất lại mà nội dung không đổi. Mặc định tài liệu WBS đề ngày ký đơn dự thầu hiện hành, đổi ngay_ky_don thì tài liệu đổi ngày và tăng phiên bản.
