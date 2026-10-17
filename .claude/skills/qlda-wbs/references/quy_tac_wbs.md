# Quy tắc WBS

## Cấu trúc tệp lam_viec/wbs/wbs_nhap.json
```json
{
 "goi": [
  {"ma": "3", "ten": "Quản lý khách hàng", "muc": 1,
   "can_cu_uoc_luong": {"kich_thuoc": "12 chức năng, 9 màn hình, 6 API", "cach_phan_ra": "Tổng nhóm theo uoc_luong.json chia cho các mục mức 2 theo số chức năng và độ phức tạp"}},
  {"ma": "3.1", "ten": "Phân tích yêu cầu phân hệ", "muc": 2, "san_pham": "SRS phân hệ khách hàng"},
  {"ma": "3.1.1", "ten": "Đặc tả use case đăng ký, đăng nhập, quản lý hồ sơ", "muc": 3, "md": 6, "loai": "BA",
   "san_pham": "Đặc tả use case", "phu_thuoc": ["2.1.3"], "hang_muc_01a": [6], "nguon": ["R05"]}
 ],
 "khong_can_goi": [{"ma": "R24", "ly_do": "Yêu cầu loại trừ phạm vi, không phát sinh công việc"}],
 "gia_dinh_ngoai_pham_vi": ["Chức năng quản trị nội bộ (RFP loại khỏi phạm vi)"],
 "giai_trinh_tuong_tu": "Lý do tổng khối lượng khác quy mô các hợp đồng tương tự (bắt buộc khi lệch quá 25%)"
}
```
- ma: mã phân cấp n, n.m, n.m.k. Mục cha phải có trước. muc bằng số cấp của mã.
- Chỉ gói lá (không có mục con) ghi md. Khối lượng mục cha do script tính bằng tổng mục con.
- loai: loại công việc dùng để áp đơn giá, một trong PM, BA, QA, DEV, DEVOPS (hoặc mã khác có trong dau_vao/don_gia.json).
- phu_thuoc: mã gói lá phải hoàn thành trước. Không tạo vòng phụ thuộc.
- hang_muc_01a: danh sách số nguyên (ví dụ [5, 6], không ghi "5"), là số thứ tự hạng mục Mẫu 01A của HSMT mà gói đóng góp (dùng để lập Mẫu 10A, 11A). Mọi hạng mục 01A phải có ít nhất một gói.
- nguon: mã yêu cầu RFP (R..) hoặc dẫn chiếu HSMT (ví dụ "HSMT Chương V 3.4") mà gói đáp ứng. Gói xử lý nghiệp vụ bán hàng thông dụng ghi thêm mã nghiệp vụ (NV01 đến NV05, references/nghiep_vu_ban_hang.json).
- thoi_luong_toi_thieu (không bắt buộc, chỉ gói lá): số nguyên dương, ngày làm việc. Lịch lấy giá trị lớn hơn giữa thời lượng tính từ MD và giá trị này. Dùng cho gói mà thời gian trôi qua không phụ thuộc số người (vận hành thử theo số ngày cam kết, chờ bên ngoài xem xét). Thời gian Chủ đầu tư phê duyệt tài liệu và khoảng kiểm thử chấp nhận không ghi ở đây mà do agent lập mốc gắn trong moc_nhap.json (khóa chu_dau_tu_tham_gia), lấy số ngày từ dau_vao/du_an.json.
- can_cu_uoc_luong (bắt buộc ở mỗi nhóm mức 1 khi có dau_vao/uoc_luong.json): kich_thuoc (số chức năng, màn hình, API, giao diện tích hợp, đầu việc phi chức năng của nhóm nếu suy được), cach_phan_ra (cách chia tổng nhóm theo phương pháp trong uoc_luong.json xuống mục mức 2 và gói).
- giai_trinh_tuong_tu: lý do khi tổng WBS lệch quá 25% so với quy mô trung bình (quy_mo_md) của hợp đồng tương tự trong dau_vao/nha_thau.json, nêu phạm vi khác biệt cụ thể.

## Căn cứ ước lượng
- dau_vao/uoc_luong.json do nhóm cung cấp: phương pháp, loại ước lượng, khoảng sai số, các bước, tong_md, tong_theo_nhom, dung_sai_nhom.
- Tổng mỗi nhóm mức 1 khớp tong_theo_nhom trong dung_sai_nhom (lỗi W63). Tổng toàn bộ bằng tong_md, sai lệch làm tròn không quá 0,5 MD (lỗi W62). Nhóm mức 1 thiếu can_cu_uoc_luong là lỗi W61. Thiếu uoc_luong.json chỉ cảnh báo W60.
- Đối chiếu tổng WBS với trung bình quy_mo_md của hợp đồng tương tự: lệch quá 25% mà không có giai_trinh_tuong_tu thì cảnh báo W64.
- MD từng gói phân rã từ tổng nhóm theo nội dung gói (kích thước, độ phức tạp), không chia đều cơ học.

## Quy tắc phân rã
- Ba mức: nhóm công việc, hạng mục, gói công việc.
- Phân hệ chức năng phân rã mức 2 theo vòng đời: phân tích yêu cầu, thiết kế, lập trình và kiểm thử đơn vị, kiểm thử phân hệ, tài liệu và nghiệm thu nội bộ.
- Mục kiểm thử phân hệ có ít nhất hai gói: kịch bản và kiểm thử (QA), sửa lỗi và kiểm thử lại (DEV, tên gói có cụm sửa lỗi hoặc khắc phục lỗi). Thiếu gói sửa lỗi thì cảnh báo W65.
- Nghiệp vụ bán hàng thông dụng trong references/nghiep_vu_ban_hang.json (hủy đơn, đổi trả, khuyến mại, phí vận chuyển, giữ tồn) phải nằm ở một trong ba chỗ: gói công việc (tên hoặc sản phẩm có từ khóa, hoặc mã NV trong nguon), khong_can_goi (ma là mã NV, kèm ly_do), gia_dinh_ngoai_pham_vi. Thiếu thì cảnh báo W33.
- Việc có Chủ đầu tư tham gia (xác nhận tài liệu, kiểm tra, kiểm thử chấp nhận) tách thành gói lá riêng để lịch gắn được thời gian phê duyệt và khoảng kiểm thử chấp nhận.
- Mỗi gói lá gắn một sản phẩm kiểm tra được, từ 2 đến 14 MD, giao được cho một người, theo dõi được theo tuần.
- Quy tắc 100%: tổng mục con bằng mục cha ở mọi mức (script tự kiểm).
- Không xây dựng chức năng quản trị nội bộ khi RFP loại khỏi phạm vi. Dữ liệu lấy từ hệ thống khác dùng "xử lý", "hiển thị" thay cho "quản lý".
- Kết nối với hệ thống, dịch vụ bên ngoài (hệ thống chính, vận chuyển, thanh toán, email) tách thành gói riêng trong nhóm tích hợp khi có cấu hình, xử lý lỗi, kiểm thử độc lập.
- Quy tắc nghiệp vụ chưa rõ ghi "theo quy tắc chủ đầu tư xác nhận".
- Tên gói dạng danh từ, văn phong trang trọng, không khẩu ngữ (xem qlda-loi/references/van_phong.md).

## Trình bày tài liệu (script xuất)
- Mỗi nhóm mức 1 một file WBS_n_Ten_khong_dau.docx và một file tổng hợp WBS_tong_hop.docx.
- File nhóm: thông tin chung (tổng MD, căn cứ ước lượng của nhóm, thời gian theo lịch, người chịu trách nhiệm theo phân công, phụ thuộc đầu vào), sơ đồ cây, bảng chi tiết (mục cha in đậm), kiểm tra quy tắc 100%.
- File tổng hợp: khối lượng theo nhóm mức 1 và theo loại công việc, căn cứ ước lượng (phương pháp, các bước, bảng theo nhóm, căn cứ từng nhóm, đối chiếu hợp đồng tương tự, khoảng sai số quy ra MD), cấu trúc mức 1 và mức 2, ma trận truy vết yêu cầu RFP sang gói, phân bổ theo hạng mục Mẫu 01A, giả định ngoài phạm vi.
- Ngày tài liệu: ngày ký đơn dự thầu hiện hành (nha_thau.json ngay_ky_don), đổi ngày ký đơn thì tài liệu đổi ngày và tăng phiên bản. Cập nhật theo yêu cầu thay đổi dùng --ngay, ngày này được giữ khi xuất lại mà nội dung không đổi.
