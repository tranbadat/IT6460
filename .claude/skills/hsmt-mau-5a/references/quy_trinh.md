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
 báo cáo ──────[ghi nhận vòng: script]────> so_phat_hien.json (phát hiện mở mang sang vòng sau)
 đạt? ── không ─[8 Sửa: script và agent]──> quay lại bước 5 hoặc 6 (tối đa 3 vòng)
   └── có ──> HSMT_ket_qua.docx
```

Lệnh cho các bước có script:
- Bước 1, 3, 4: `python3 scripts/chay_quy_trinh.py chuan_bi <Mau_5A.docx> <tham_so.json> <thu_muc>` (cần `rfp_yeu_cau.json` có sẵn trong thư mục).
- Bước 5 (ghép), 6, 7 lớp A, 8 phần tự động: `python3 scripts/chay_quy_trinh.py hoan_thien <Mau_5A.docx> <thu_muc>` (cần `ban_soan.json`). Đạt hẳn thì ra `HSMT_ket_qua.docx`. Lớp A không còn lỗi mới nhưng còn mục chờ thì ra `HSMT_du_thao.docx` để lớp B kiểm tra.
- Kết thúc vòng, sau lớp B: `python3 scripts/chay_quy_trinh.py ghi_nhan <thu_muc> [bao_cao_kiem_tra.json]`.
- Người dùng quyết giữ nguyên một phát hiện: `python3 scripts/chay_quy_trinh.py giai_trinh <thu_muc> <PHxxx> "<lý do>"`.

## 3. Phân công giữa script và agent

| Loại nội dung | Ai làm | Lý do |
|---|---|---|
| Chương I, VI, Mục 1 Chương III, các đoạn quy phạm Mục 2.2 Chương III | Script chép từ mẫu | Phải nguyên văn |
| Bảng số 01 dòng 3, 4 (thuế GTGT, cộng gộp hợp đồng tương tự), câu phạt nhân sự chủ chốt E-ĐKC 15, E-ĐKC 18 (e) | Script theo tham số | Lựa chọn của Chủ đầu tư |
| Cột cố định của Bảng số 01, danh mục biểu mẫu, mã mục E-BDL, E-ĐKCT | Script lấy từ mẫu | Không được đổi |
| Ngày, tiền, tỷ lệ, mốc năm | Script tính | Mọi agent cho cùng một kết quả |
| Mục mẫu ghi "Hệ thống trích xuất", lựa chọn có hoặc không | Script điền theo tham số | Cơ học |
| Chương V, Mẫu 01A, tiêu chí kỹ thuật tổng quát và chi tiết, điều khoản hợp đồng từ RFP | Agent Soạn thảo (vai tư vấn lập HSMT) | Cần đọc hiểu RFP và diễn đạt. Script dựng khung bảng tiêu chí, kiểm tra tổng điểm, số tiêu chí chi tiết, mức chấm, độ phủ |
| Chương V mục 3.5 phân định trách nhiệm và giả định, câu mẫu E-ĐKC 15 | Script theo tham số | Lựa chọn của Chủ đầu tư. Tham số trống thì giữ câu mẫu kèm dấu [Chủ đầu tư quyết định ...] |
| Danh mục yêu cầu RFP | Agent Phân tích RFP | RFP là bản scan |
| Đánh giá đọc hiểu | Agent Kiểm tra | Bắt lỗi script không thấy |

## 4. Tính độc lập

- Agent Kiểm tra không đọc khung, bản soạn, nhật ký sửa. Chỉ đọc file Word, nguồn chuẩn và sổ phát hiện `so_phat_hien.json` (do bên kiểm tra ghi).
- Agent Kiểm tra tự đối chiếu RFP.pdf, không chỉ tin `rfp_yeu_cau.json`.
- Nên chạy mỗi agent trong một phiên hoặc ngữ cảnh riêng.

## 5. Điều kiện dừng

Kết luận của lớp A và của vòng có ba mức:

| Kết luận | Điều kiện |
|---|---|
| dat | Không còn lỗi, không còn tham số chờ Chủ đầu tư, không còn phát hiện mở chưa giải trình |
| chua_dat | Còn lỗi mới hoặc lỗi mang sang chưa giải trình |
| cho_nguoi_dung | Chưa hoàn tất, chờ người dùng: không còn lỗi nhưng còn tham số bắt buộc trống (TS01, xem `tham_so.md`) hoặc cảnh báo cần người dùng còn mở |

- Đạt cả lớp A và kết luận vòng: giao `HSMT_ket_qua.docx` và báo cáo kiểm tra.
- Kết luận cho_nguoi_dung hoặc còn lỗi thuộc quyết định của chủ đầu tư: dừng, hỏi người dùng. Không kết luận đạt khi còn dấu chờ Chủ đầu tư quyết định.
- Quá 3 vòng: dừng, báo người dùng.

## 6. Bảng kiểm tra đọc hiểu (lớp B)

| Mã | Nội dung |
|---|---|
| MH01 | Đối chiếu từng trang RFP.pdf: mọi yêu cầu, điều khoản, sản phẩm đều có trong HSMT hoặc được ghi thành điểm lệch có căn cứ |
| MH02 | Các mốc ngày thống nhất giữa E-TBMT, Chương II, V, VII và đúng `gia_tri_tinh.json` |
| MH03 | Số liệu thống nhất giữa các chương |
| MH04 | Mỗi mục E-BDL, E-ĐKCT trả lời đúng và đủ câu hỏi của mẫu (`mau5a_cau_truc.json`) |
| MH05 | Tiêu chí kỹ thuật phủ đủ nội dung đề xuất của RFP và yêu cầu phi chức năng, không chấm giá. Mỗi tiêu chí tổng quát có 3 đến 6 tiêu chí chi tiết có điểm, mức chấm rõ ràng, phân biệt được các E-HSDT, tiêu chí cơ bản hợp lý. Tiêu chí 5 không chấm điều kiện, đề nghị của nhà thầu |
| MH06 | Mẫu 01A phủ đủ sản phẩm bàn giao, chức năng, tích hợp, kiểm thử, cut over của RFP và khớp Chương V |
| MH07 | Bảng số 02 khớp tham số, không đặt điều kiện hạn chế cạnh tranh |
| MH08 | Văn phong theo `van_phong.md` |
| MH09 | Điểm lệch RFP chỉ gồm các mục `lech_co_can_cu`, mỗi mục có giải pháp tương đương |
| MH10 | Không có nội dung mâu thuẫn hoặc lặp giữa các mục bổ sung và các mục khác của Chương VII |
| MH11 | Chương V mục 3.5 phân định đủ hạ tầng, môi trường kiểm thử, thông tin hệ thống hiện có và thời hạn cung cấp, phù hợp hợp đồng trọn gói. Mỗi yêu cầu phi chức năng có điều kiện đo hoặc cơ chế nhà thầu đề xuất và hai bên xác nhận trong đặc tả |
| MH12 | Từng phát hiện còn mở trong `so_phat_hien.json` được kiểm tra lại. Đã khắc phục thì ghi vào `dong_phat_hien` kèm cách xác nhận, chưa khắc phục thì để mở |

## 7. Sổ phát hiện qua các vòng

- `so_phat_hien.json` trong thư mục làm việc ghi mọi phát hiện lớp B và phát hiện lớp A là lỗi hoặc cần người dùng, kèm mã PHxxx, vòng phát hiện, trạng thái mo, da_dong hoặc giai_trinh.
- Số vòng bằng số vòng đã ghi nhận trong sổ cộng 1. Chỉ ghi_nhan làm tăng vòng. Sửa script, chạy lại chuan_bi (lập lại khung) và hoan_thien bao nhiêu lần trước ghi_nhan vẫn thuộc cùng một vòng, tệp Word mang cùng số vòng.
- `chay_quy_trinh.py ghi_nhan` cập nhật sổ cuối mỗi vòng. Phát hiện lớp A tự đóng khi lớp A không còn bắt được. Phát hiện lớp B chỉ đóng khi lớp B vòng sau ghi trong `dong_phat_hien` kèm ghi chú cách đã xác nhận.
- `verify_hsmt.py` đọc sổ và mang phát hiện mở sang vòng đang kiểm tra (mã PH01). Vòng sau không kết luận đạt khi còn phát hiện mở chưa giải trình.
- Giải trình chỉ ghi khi người dùng quyết định giữ nguyên, bằng `chay_quy_trinh.py giai_trinh`.
- Giải trình sau ghi_nhan: `chay_quy_trinh.py chot_vong <thu_muc>` chốt lại vòng đang ghi trong sổ. Lệnh yêu cầu báo cáo đã ghi_nhan của đúng vòng đó, tính lại kết luận (mục mở trong sổ, TS01 của báo cáo), không tăng vòng, không hợp nhất lại báo cáo. Đạt thì nâng tệp lớp B đã kiểm tra (đúng md5, đúng vòng) thành `HSMT_ket_qua.docx`, ghi ket_luan, tep_giao, md5_giao, giai_trinh_khi_chot vào báo cáo. trich_hsmt.py chấp nhận vòng đạt có mục giải trình và liệt kê các mục đó. Không chạy lại ghi_nhan trên cùng báo cáo: ghi_nhan luôn tăng vòng.
- Bản giao: build_hsmt.py ghi vòng (thuộc tính version) và md5 của hsmt_noi_dung đã dùng (thuộc tính identifier) vào tệp Word. verify_hsmt.py ghi md5 tệp được kiểm tra vào báo cáo và báo CT07 khi tệp không thuộc vòng đang kiểm tra. ghi_nhan vòng đạt nâng đúng tệp đó thành `HSMT_ket_qua.docx` (md5_giao). trich_hsmt.py chỉ chép tệp có md5 bằng md5_giao và trích từ tệp nội dung khớp identifier.
