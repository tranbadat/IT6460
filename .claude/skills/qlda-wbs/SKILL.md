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
   Kiểm tra mã phân cấp, quy tắc 100%, gói lá có MD, loại công việc, sản phẩm, thời lượng tối thiểu (W19), phụ thuộc không vòng, mọi hạng mục Mẫu 01A được phủ, mọi yêu cầu RFP được truy vết, nghiệp vụ bán hàng thông dụng (W33), cỡ gói 2 đến 14 MD, gói sửa lỗi của kiểm thử phân hệ (W65), giai_doan của gói lá (W66, chỉ gói lá, giá trị khoi_dong, thuc_hien, xuyen_suot, ket_thuc; W67 cảnh báo khi gói quản lý dự án chưa ghi giai_doan tường minh; gói quản lý dự án là gói lá thuộc mục WBS có tên bắt đầu bằng "Quản lý dự án" (nhóm mức 1 riêng hoặc mục mức 2 phần phân bổ trong từng phân hệ) hoặc gói loại PM (loi.goi_quan_ly_du_an), không phụ thuộc số thứ tự nhóm; gói này không gắn sprint phát triển. Từ 1.4.0 không còn giả định nhóm 1 là quản lý dự án).
   Lời căn cứ ước lượng của nhóm, gia_dinh_ngoai_pham_vi, giai_trinh_tuong_tu viết số liệu bằng tham chiếu ({nhom#7.md|md}, {cc#7.md_muc_tieu|md}, {wbs#goi[ma=7.2].md|md}, {buoc#2.thanh_phan.giai_phap|md}, {lich#so_sprint}, {da#uat.tu|ngay}, {ct#bao_hanh.ho_tro_tang_cuong.tu|ngay}, {cr#CR01.chi_tiet_goi[ma=7.2.1].md_tang|md}, {kl#truoc_cr|md}, {cc#1.md_rieng|md}, {cc#1.md_chung_phan_bo|md}, {pb#theo_nhom.1.quan_ly_du_an|md}, {pb#theo_nhom.1.tong|md}, {ul#trung_binh_tuong_tu_md|md}, {ul#hop_dong_tuong_tu[0].quy_mo_md|md}), không ghi tên tệp hay tên khóa dữ liệu trong lời văn; xuat_wbs.py thay khi xuất.
   Cấu trúc WBS theo căn cứ ước lượng của nhóm: khi uoc_luong.json có phan_bo_dau_viec_chung (từ 1.4.0), mức 1 chỉ gồm các phân hệ trong tong_theo_nhom (md, md_rieng, md_chung_phan_bo), đầu việc chung (quản lý dự án, phân tích thiết kế chung, kiểm thử hệ thống và vận hành, triển khai chuyển giao) không tách nhóm riêng mà phân bổ vào từng phân hệ; mỗi phân hệ có mục mức 2 theo vòng đời (quản lý dự án phần phân bổ, phân tích và thiết kế, xây dựng, kiểm thử, triển khai và chuyển giao). wbs.json ghi can_cu_uoc_luong.phan_bo_chung (phân bổ từng đầu việc chung theo tỷ lệ md_rieng, làm tròn phần dư lớn nhất) và md_rieng, md_chung_phan_bo của từng nhóm; tài liệu tổng hợp có bảng phân bổ đầu việc chung. Yêu cầu thay đổi được duyệt sau ký hợp đồng lập thành nhóm mức 1 riêng.
   Giả định ngoài phạm vi (từ 1.4.0): kiem_tra_wbs.py giải tham chiếu của gia_dinh_ngoai_pham_vi khi ghi du_lieu/wbs.json (bí danh da, ct, wbs, nhom, cc, buoc, pb, ul), để HSDT, master plan dẫn nguyên văn không còn tham chiếu; còn tham chiếu không giải được (ví dụ lich) thì giữ nguyên và cảnh báo W68.
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
   Mỗi nhóm mức 1 một tệp và một tệp tổng hợp trong ket_qua/03_WBS/. Tệp tổng hợp có mục Căn cứ ước lượng khi wbs.json có can_cu_uoc_luong. Khi lịch có giai đoạn, bảng chi tiết có cột Giai đoạn, sprint: gói phát triển ghi sprint, gói quản lý dự án ghi giai đoạn (Khởi động, Suốt dự án, Kết thúc) thay cho sprint, thời gian thực hiện của nhóm quản lý dự án ghi theo giai đoạn. Sau yêu cầu thay đổi có phụ lục (du_lieu/thay_doi.json): bìa ghi đường cơ sở hiện hành và phụ lục thay cho dòng kèm theo HSDT, thông tin chung của nhóm có dòng Yêu cầu thay đổi (gói mới, gói tăng MD, gói chỉ thêm phụ thuộc ghi không tăng khối lượng, từ 1.4.3), tệp tổng hợp có mục Truy vết yêu cầu thay đổi (tên gói lấy theo wbs.json) và câu nêu bước ước lượng theo phiếu yêu cầu thay đổi. Mục cha WBS in đậm, còn lại theo van_phong.md. Mỗi tệp được kiểm tra lớp A theo `dac_ta/tai_lieu_wbs.json`.
2. Agent Kiểm tra lớp B (qlda-loi/prompts/vai_kiem_tra.md): phạm vi đủ theo RFP, khối lượng hợp lý và có căn cứ, sản phẩm kiểm chứng được.

## Khi WBS thay đổi

Thay đổi sau khi có giao việc, lịch, dự toán phải đi qua yêu cầu thay đổi (skill qlda-change) nếu đã ký hợp đồng. Sửa wbs_nhap.json, chạy lại bước 2, rồi `python .claude/skills/qlda-loi/scripts/chay.py anh_huong wbs` để cập nhật các bước sau theo thứ tự. Tài liệu WBS xuất lại theo yêu cầu thay đổi dùng `xuat_wbs.py --ngay yyyy-mm-dd` (ngày cập nhật theo lịch dự án), ngày này được giữ khi xuất lại mà nội dung không đổi. Mặc định tài liệu WBS đề ngày ký đơn dự thầu hiện hành, đổi ngay_ky_don thì tài liệu đổi ngày và tăng phiên bản.
