# Văn phong và trình bày

Áp dụng cho mọi tài liệu của bộ skill. Bộ sinh file và script kiểm tra tự áp dụng phần trình bày. Agent soạn thảo phải tuân thủ phần văn phong.

## Trình bày
- Word: Times New Roman, cỡ 13 (bảng cỡ 12), khổ A4, bảng kẻ lưới đơn, dòng tiêu đề bảng lặp lại khi sang trang.
- Không in đậm, không viết hoa toàn bộ, không dùng ngoặc kép để nhấn mạnh. Riêng WBS: mục cha in đậm, gói công việc để thường.
- Gạch ngang đơn, không dùng gạch dài.
- Excel: Times New Roman, ô nhập liệu chữ xanh dương, ô công thức chữ đen, ô cần nhóm điền nền vàng, mọi con số tổng hợp là công thức.
- Ngày dạng dd/mm/yyyy. Tiền dạng 1.000.000 đồng hoặc 1.411,98 triệu đồng. MD viết số thập phân với dấu phẩy.

## Văn phong
- Trang trọng, văn bản quản lý dự án. Không khẩu ngữ, không nhân hóa, không câu cảm thán, không lời dẫn kiểu "dưới đây là".
- Không ký hiệu hay dấu vết do máy sinh: mũi tên, dấu tích, biểu tượng, ghi chú nháp.
- Hạn chế dấu chấm phẩy. Tách câu hoặc dùng từ nối. Không quá ba dấu chấm phẩy trong một câu.
- Tiêu đề ngắn gọn, dạng danh từ: "Kế hoạch theo sprint", không viết "Kế hoạch 7 sprint đã lập".
- Từ cần tránh và từ thay thế: xem `van_phong.json`.
- Tên chức năng, sản phẩm theo RFP giữ tiếng Anh trong ngoặc sau tên tiếng Việt.

## Số liệu
- Mọi con số trong đoạn văn agent soạn viết bằng tham chiếu dữ liệu `{bi_danh#duong_dan|dinh_dang}`, ví dụ `{cp#gia_chao|tien}` đồng, `{lich#cut_over|ngay}`. Khi dữ liệu thay đổi, tài liệu tạo lại tự cập nhật số. Số viết tay bị cảnh báo.
- Định dạng: tien, trieu, md, pt, ngay, so, so1, so2, so3, nguyen, chu.
