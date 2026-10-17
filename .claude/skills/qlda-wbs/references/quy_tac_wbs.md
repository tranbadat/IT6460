# Quy tắc WBS

## Cấu trúc tệp lam_viec/wbs/wbs_nhap.json
```json
{
 "goi": [
  {"ma": "3", "ten": "Quản lý khách hàng", "muc": 1},
  {"ma": "3.1", "ten": "Phân tích yêu cầu phân hệ", "muc": 2, "san_pham": "SRS phân hệ khách hàng"},
  {"ma": "3.1.1", "ten": "Đặc tả use case đăng ký, đăng nhập, quản lý hồ sơ", "muc": 3, "md": 6, "loai": "BA",
   "san_pham": "Đặc tả use case", "phu_thuoc": ["2.1.3"], "hang_muc_01a": [6], "nguon": ["R05"]}
 ],
 "khong_can_goi": [{"ma": "R24", "ly_do": "Yêu cầu loại trừ phạm vi, không phát sinh công việc"}],
 "gia_dinh_ngoai_pham_vi": ["Chức năng quản trị nội bộ (RFP loại khỏi phạm vi)"]
}
```
- ma: mã phân cấp n, n.m, n.m.k. Mục cha phải có trước. muc bằng số cấp của mã.
- Chỉ gói lá (không có mục con) ghi md. Khối lượng mục cha do script tính bằng tổng mục con.
- loai: loại công việc dùng để áp đơn giá, một trong PM, BA, QA, DEV, DEVOPS (hoặc mã khác có trong dau_vao/don_gia.json).
- phu_thuoc: mã gói lá phải hoàn thành trước. Không tạo vòng phụ thuộc.
- hang_muc_01a: danh sách số nguyên (ví dụ [5, 6], không ghi "5"), là số thứ tự hạng mục Mẫu 01A của HSMT mà gói đóng góp (dùng để lập Mẫu 10A, 11A). Mọi hạng mục 01A phải có ít nhất một gói.
- nguon: mã yêu cầu RFP (R..) hoặc dẫn chiếu HSMT (ví dụ "HSMT Chương V 3.4") mà gói đáp ứng.

## Quy tắc phân rã
- Ba mức: nhóm công việc, hạng mục, gói công việc.
- Phân hệ chức năng phân rã mức 2 theo vòng đời: phân tích yêu cầu, thiết kế, lập trình và kiểm thử đơn vị, kiểm thử phân hệ, tài liệu và nghiệm thu nội bộ.
- Mỗi gói lá gắn một sản phẩm kiểm tra được, từ 2 đến 14 MD, giao được cho một người, theo dõi được theo tuần.
- Quy tắc 100%: tổng mục con bằng mục cha ở mọi mức (script tự kiểm).
- Không xây dựng chức năng quản trị nội bộ khi RFP loại khỏi phạm vi. Dữ liệu lấy từ hệ thống khác dùng "xử lý", "hiển thị" thay cho "quản lý".
- Kết nối với hệ thống, dịch vụ bên ngoài (hệ thống chính, vận chuyển, thanh toán, email) tách thành gói riêng trong nhóm tích hợp khi có cấu hình, xử lý lỗi, kiểm thử độc lập.
- Quy tắc nghiệp vụ chưa rõ ghi "theo quy tắc chủ đầu tư xác nhận".
- Tên gói dạng danh từ, văn phong trang trọng, không khẩu ngữ (xem qlda-loi/references/van_phong.md).

## Trình bày tài liệu (script xuất)
- Mỗi nhóm mức 1 một file WBS_n_Ten_khong_dau.docx và một file tổng hợp WBS_tong_hop.docx.
- File nhóm: thông tin chung (tổng MD, thời gian theo lịch, người chịu trách nhiệm theo phân công, phụ thuộc đầu vào), sơ đồ cây, bảng chi tiết (mục cha in đậm), kiểm tra quy tắc 100%.
- File tổng hợp: khối lượng theo nhóm mức 1, ma trận truy vết yêu cầu RFP sang gói, phân bổ theo hạng mục Mẫu 01A, giả định ngoài phạm vi.
