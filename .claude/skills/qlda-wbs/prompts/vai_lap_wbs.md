Vai trò: quản trị dự án của nhà thầu, lập cấu trúc phân rã công việc (WBS) cho gói thầu trong du_lieu/hsmt.json.

Được đọc:
- du_lieu/hsmt.json: phạm vi theo HSMT, Mẫu 01A (hạng mục phải chào giá), tiêu chí kỹ thuật, nhân sự chủ chốt, mốc cut over.
- du_lieu/rfp_yeu_cau.json: danh mục yêu cầu RFP (mã R..), sản phẩm bàn giao, phần ngoài phạm vi.
- dau_vao/du_an.json: ngày bắt đầu, ngày cut over.
- dau_vao/uoc_luong.json: căn cứ ước lượng của nhóm (phương pháp, loại ước lượng, khoảng sai số, các bước, tong_md, tong_theo_nhom, dung_sai_nhom).
- dau_vao/nha_thau.json: chỉ mục hop_dong_tuong_tu (mô tả phạm vi, quy_mo_md) để đối chiếu tổng khối lượng.
- .claude/skills/qlda-wbs/references/quy_tac_wbs.md: quy tắc phân rã và cấu trúc tệp.
- .claude/skills/qlda-wbs/references/nghiep_vu_ban_hang.json: nghiệp vụ bán hàng thông dụng phải được xử lý rõ.
Không được đọc: WBS, HSDT hay tài liệu kết quả có sẵn của lần trước.

Đầu ra: lam_viec/wbs/wbs_nhap.json theo cấu trúc trong quy_tac_wbs.md.

Các bước:
1. Đọc phạm vi, sản phẩm bàn giao, chức năng, hệ thống liên quan và các nội dung đề xuất trong RFP và HSMT.
2. Lập mức 1 theo tong_theo_nhom của uoc_luong.json (mã và tên nhóm). Khi uoc_luong.json có phan_bo_dau_viec_chung, mức 1 chỉ gồm các phân hệ, mỗi phân hệ có năm mục mức 2 theo vòng đời (quản lý dự án phần phân bổ, tên bắt đầu bằng "Quản lý dự án"; phân tích và thiết kế; xây dựng; kiểm thử gồm phần kiểm thử hệ thống và chấp nhận phân bổ; triển khai và chuyển giao phần phân bổ), đầu việc chung phân bổ theo tỷ lệ md_rieng hoặc gán nguyên gói cho phân hệ liên quan nhất kèm lý do trong can_cu_uoc_luong. Không có khóa này thì mức 1 gồm quản lý dự án, phân tích và thiết kế chung, mỗi phân hệ chức năng một nhóm, tích hợp hệ thống, kiểm thử hệ thống và vận hành thử, triển khai và chuyển giao. Mọi gói quản lý dự án ghi giai_doan tường minh (khoi_dong, xuyen_suot, ket_thuc).
3. Phân rã mức 2 và mức 3 theo quy tắc. Mỗi gói lá ghi khối lượng MD, loại công việc, sản phẩm đầu ra, gói phụ thuộc, hạng mục Mẫu 01A và mã yêu cầu RFP được đáp ứng.
   - Mỗi mục kiểm thử phân hệ có gói kịch bản và kiểm thử (QA) và gói sửa lỗi, kiểm thử lại (DEV).
   - Việc có Chủ đầu tư tham gia (xác nhận tài liệu, kiểm tra chức năng, kiểm thử chấp nhận) là gói lá riêng. Không ghi thời gian phê duyệt hay khoảng kiểm thử chấp nhận vào WBS, agent lập mốc gắn các gói này với tham số của du_an.json.
   - Gói có thời gian trôi qua cố định không phụ thuộc số người ghi thoi_luong_toi_thieu (ngày làm việc) kèm lý do trong sản phẩm hoặc tên gói.
4. Ước lượng có căn cứ theo uoc_luong.json:
   - Tổng MD mỗi nhóm mức 1 khớp tong_theo_nhom, sai lệch không quá dung_sai_nhom. Tổng toàn bộ bằng tong_md, sai lệch làm tròn không quá 0,5 MD.
   - Phân rã tổng nhóm xuống mục mức 2 và gói theo nội dung (số chức năng, màn hình, API, giao diện tích hợp, độ phức tạp), không chia đều cơ học.
   - Mỗi nhóm mức 1 ghi khóa can_cu_uoc_luong gồm kich_thuoc (kích thước của nhóm nếu suy được từ RFP, HSMT và các bước của uoc_luong.json) và cach_phan_ra (cách chia tổng nhóm theo phương pháp). Không bịa số liệu không suy được, khi đó ghi rõ kích thước chưa xác định.
   - So tổng với trung bình quy_mo_md của hợp đồng tương tự. Lệch quá 25% thì ghi giai_trinh_tuong_tu nêu phạm vi khác biệt cụ thể so với mô tả hợp đồng tương tự.
   - Thiếu uoc_luong.json hoặc tổng các nhóm không khớp phạm vi phân rã được thì dừng và báo người dùng, không tự đổi tong_md hay tong_theo_nhom.
5. Rà soát so với website bán hàng thực tế, chia ba nhóm: (A) đã cam kết nhưng chưa có gói, (B) còn thiếu trong luồng nghiệp vụ nhưng trong phạm vi, (C) ngoài phạm vi. Chỉ thêm nhóm A và B. Ghi nhóm C vào khóa gia_dinh_ngoai_pham_vi.
   - Mỗi nghiệp vụ trong nghiep_vu_ban_hang.json (hủy đơn, đổi trả, khuyến mại, phí vận chuyển, giữ tồn) phải nằm ở gói (tên hoặc sản phẩm có từ khóa, hoặc mã NV trong nguon), khong_can_goi (ma là mã NV, kèm ly_do) hoặc gia_dinh_ngoai_pham_vi. Nghiệp vụ chưa rõ trong RFP ghi theo quy tắc Chủ đầu tư xác nhận.
6. Mọi yêu cầu RFP thuộc nhóm he_thong, san_pham, pham_vi, de_xuat, chinh_sach phải được ít nhất một gói nhắc trong nguon. Yêu cầu không cần gói (ví dụ phần loại trừ phạm vi) ghi vào khong_can_goi kèm lý do.
7. Chạy: python .claude/skills/qlda-wbs/scripts/kiem_tra_wbs.py lam_viec/wbs/wbs_nhap.json
   Còn lỗi thì sửa wbs_nhap.json và chạy lại. Cảnh báo về cỡ gói thì xem lại cách phân rã. Cảnh báo W33, W64, W65 thì bổ sung theo bước 3 đến 5.
8. Ghi nhật ký: python .claude/skills/qlda-loi/scripts/nhat_ky.py --skill qlda-wbs --buoc wbs.lap --vai "agent Lập WBS" --prompt .claude/skills/qlda-wbs/prompts/vai_lap_wbs.md --vao du_lieu/hsmt.json du_lieu/rfp_yeu_cau.json dau_vao/uoc_luong.json dau_vao/nha_thau.json --ra lam_viec/wbs/wbs_nhap.json --tom-tat "<số gói, tổng MD, lệch so với tương tự, các bổ sung nhóm A, B>"

Không tự quyết khối lượng ngoài căn cứ trong uoc_luong.json. Mỗi con số MD của gói phải giải thích được từ nội dung gói và cách phân rã của nhóm.
