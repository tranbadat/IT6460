# Quy trình lập HSMT từ Mẫu 5A và RFP

## 1. Đầu vào

| File | Nguồn | Ghi chú |
|---|---|---|
| Mau_5A.docx | Thông tư 79/2025/TT-BTC | Đặt trong `dau_vao/` của dự án. Cách tải lại: `assets/README.txt` |
| RFP.pdf | Khách hàng | Đặt trong `dau_vao/` của dự án. RFP khác thì thay tệp này |
| tham_so_chu_dau_tu.json | Chủ đầu tư hoặc bên lập HSMT | Các giá trị RFP không có: giá gói thầu, năm, chính sách hợp đồng, nhân sự chủ chốt. Bản cho ABC Wear: `dau_vao/tham_so_chu_dau_tu.json` của dự án. Giải thích: `references/tham_so.md` |

Skill không chứa, không đọc và không so với HSMT, HSDT có sẵn. Không agent nào được dùng một hồ sơ hoàn chỉnh làm đầu vào hay làm chuẩn đánh giá.

## 2. Các bước

```
 Mau_5A.docx ──[1 Phân tích mẫu: script]──> mau5a_fixed.json, mau5a_cau_truc.json
 RFP.pdf ──────[2 Phân tích RFP: agent]───> rfp_yeu_cau.json
 tham số + RFP ─[3 Tính giá trị: script]──> gia_tri_tinh.json
 tất cả ───────[4 Lập khung: script]──────> hsmt_khung.json (mục cơ học điền sẵn, mục cần soạn để <<SOẠN:ID>>)
 khung + nguồn ─[5 Soạn thảo: agent]──────> ban_soan.json ──[ghép: script]──> hsmt_noi_dung_v1.json
 nội dung ─────[6 Tạo: script]────────────> HSMT_vN.docx
 HSMT ─────────[7 Kiểm tra: lớp A script, lớp B agent độc lập]──> bao_cao_kiem_tra.json
 đạt? ── không ─[8 Sửa: script và agent]──> quay lại bước 5 hoặc 6 (tối đa 3 vòng)
   └── có ──> HSMT_ket_qua.docx
```

Lệnh cho các bước có script:
- Bước 1, 3, 4: `python3 scripts/chay_quy_trinh.py chuan_bi <Mau_5A.docx> <tham_so.json> <thu_muc>` (cần `rfp_yeu_cau.json` có sẵn trong thư mục).
- Bước 5 (ghép), 6, 7 lớp A, 8 phần tự động: `python3 scripts/chay_quy_trinh.py hoan_thien <Mau_5A.docx> <thu_muc>` (cần `ban_soan.json`).

## 3. Phân công giữa script và agent

| Loại nội dung | Ai làm | Lý do |
|---|---|---|
| Chương I, VI, Mục 1 Chương III | Script chép từ mẫu | Phải nguyên văn |
| Cột cố định của Bảng số 01, danh mục biểu mẫu, mã mục E-BDL, E-ĐKCT | Script lấy từ mẫu | Không được đổi |
| Ngày, tiền, tỷ lệ, mốc năm | Script tính | Mọi agent cho cùng một kết quả |
| Mục mẫu ghi "Hệ thống trích xuất", lựa chọn có hoặc không | Script điền theo tham số | Cơ học |
| Chương V, Mẫu 01A, tiêu chí kỹ thuật, điều khoản hợp đồng từ RFP | Agent Soạn thảo | Cần đọc hiểu RFP và diễn đạt |
| Danh mục yêu cầu RFP | Agent Phân tích RFP | RFP là bản scan |
| Đánh giá đọc hiểu | Agent Kiểm tra | Bắt lỗi script không thấy |

## 4. Tính độc lập

- Agent Kiểm tra không đọc khung, bản soạn, nhật ký. Chỉ đọc file Word và nguồn chuẩn.
- Agent Kiểm tra tự đối chiếu RFP.pdf, không chỉ tin `rfp_yeu_cau.json`.
- Nên chạy mỗi agent trong một phiên hoặc ngữ cảnh riêng.

## 5. Điều kiện dừng

- Đạt cả lớp A và lớp B: giao `HSMT_ket_qua.docx` và báo cáo kiểm tra.
- Còn lỗi thuộc quyết định của chủ đầu tư: dừng, hỏi người dùng.
- Quá 3 vòng: dừng, báo người dùng.

## 6. Bảng kiểm tra đọc hiểu (lớp B)

| Mã | Nội dung |
|---|---|
| MH01 | Đối chiếu từng trang RFP.pdf: mọi yêu cầu, điều khoản, sản phẩm đều có trong HSMT hoặc được ghi thành điểm lệch có căn cứ |
| MH02 | Các mốc ngày thống nhất giữa E-TBMT, Chương II, V, VII và đúng `gia_tri_tinh.json` |
| MH03 | Số liệu thống nhất giữa các chương |
| MH04 | Mỗi mục E-BDL, E-ĐKCT trả lời đúng và đủ câu hỏi của mẫu (`mau5a_cau_truc.json`) |
| MH05 | Tiêu chí kỹ thuật phủ đủ nội dung đề xuất của RFP, không chấm giá |
| MH06 | Mẫu 01A phủ đủ sản phẩm bàn giao, chức năng, tích hợp, kiểm thử, cut over của RFP và khớp Chương V |
| MH07 | Bảng số 02 khớp tham số, không đặt điều kiện hạn chế cạnh tranh |
| MH08 | Văn phong theo `van_phong.md` |
| MH09 | Điểm lệch RFP chỉ gồm các mục `lech_co_can_cu`, mỗi mục có giải pháp tương đương |
| MH10 | Không có nội dung mâu thuẫn hoặc lặp giữa các mục bổ sung và các mục khác của Chương VII |
