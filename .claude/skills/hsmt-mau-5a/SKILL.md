---
name: hsmt-mau-5a
description: Lập hồ sơ mời thầu (E-HSMT) theo Mẫu số 5A, Thông tư 79/2025/TT-BTC, từ file mẫu và file RFP của khách hàng, bằng chuỗi agent phân tích RFP, soạn thảo, kiểm tra độc lập và sửa lỗi, ra file Word. Dùng skill này khi người dùng muốn lập, xuất, kiểm tra hoặc sửa HSMT, hồ sơ mời thầu, E-HSMT, bảng dữ liệu đấu thầu, điều kiện cụ thể hợp đồng cho gói thầu dịch vụ phi tư vấn (ví dụ bài tập lớn ABC Wear Web Selling Site System), hoặc đưa một RFP và muốn có hồ sơ mời thầu theo Mẫu 5A.
---

# Lập HSMT theo Mẫu 5A từ RFP

Đầu vào: Mẫu 5A, RFP và tham số chủ đầu tư. HSMT được lập từ đầu. Skill không chứa, không đọc và không so với bất kỳ HSMT hay HSDT có sẵn nào. Chất lượng được bảo đảm bằng kiểm tra theo nguồn chuẩn (mẫu, RFP, luật, tham số), không bằng cách đối chiếu với một bản hoàn chỉnh.

Đọc `references/quy_trinh.md` trước khi chạy.

## Thành phần

| File | Vai trò |
|---|---|
| `assets/Mau_5A.docx`, `assets/RFP.pdf` | Mẫu gốc và RFP của ABC Wear. RFP khác thì dùng file người dùng tải lên |
| `dau_vao/tham_so_chu_dau_tu.json` | Tham số chủ đầu tư cho ABC Wear (giá trị RFP không có) |
| `scripts/phan_tich_mau.py` | Bước 1: trích nguyên văn và danh sách mục cần điền của mẫu |
| `scripts/tinh_gia_tri.py` | Bước 3: tính ngày, tiền, tỷ lệ, mốc năm theo RFP, tham số, quy tắc luật |
| `scripts/lap_khung.py` | Bước 4: dựng khung HSMT, đánh dấu mục cần agent soạn |
| `scripts/dien_khung.py` | Bước 5: ghép bản soạn vào khung |
| `scripts/build_hsmt.py` | Bước 6: sinh file Word |
| `scripts/verify_hsmt.py` | Bước 7 lớp A: kiểm tra theo nguồn chuẩn, không ghi cứng giá trị |
| `scripts/fix_hsmt.py` | Bước 8: sửa lỗi cơ học |
| `scripts/chay_quy_trinh.py` | Điều phối các bước script (chuan_bi, hoan_thien) |
| `prompts/vai_phan_tich_rfp.md`, `vai_soan_thao.md`, `vai_kiem_tra.md`, `vai_sua.md` | Chỉ dẫn cho từng agent |
| `references/quy_tac_soan_thao.md`, `van_phong.md`, `tham_so.md`, `quy_trinh.md` | Quy tắc |

## Cách chạy

Thư mục làm việc: `/home/claude/hsmt`.

1. Xác định đầu vào: Mẫu 5A (`assets/` hoặc file người dùng tải lên), RFP (file người dùng tải lên, nếu không có thì `assets/RFP.pdf`), tham số (file người dùng đưa, nếu không có thì `dau_vao/`). RFP khác ABC Wear mà người dùng chưa đưa tham số thì dừng và hỏi các trường trong `references/tham_so.md`.
2. Agent Phân tích RFP: theo `prompts/vai_phan_tich_rfp.md`, ra `rfp_yeu_cau.json` trong thư mục làm việc.
3. `python3 <skill>/scripts/chay_quy_trinh.py chuan_bi <Mau_5A> <tham_so> /home/claude/hsmt`. Lỗi tham số thì dừng và báo người dùng.
4. Agent Soạn thảo: theo `prompts/vai_soan_thao.md`, ra `ban_soan.json`.
5. `python3 <skill>/scripts/chay_quy_trinh.py hoan_thien <Mau_5A> /home/claude/hsmt`. Mã thoát 2 thì xử lý theo `prompts/vai_sua.md` và chạy lại. Tối đa 3 vòng.
6. Agent Kiểm tra lớp B: theo `prompts/vai_kiem_tra.md`. Nếu có công cụ tạo agent con, giao cho agent con, không chuyển khung và bản soạn. Nếu không, tự đóng vai và chỉ đọc những file được phép. Có lỗi thì quay lại bước 4 hoặc 5.
7. Đạt: chuyển PDF bằng `python /mnt/skills/public/docx/scripts/office/soffice.py --headless --convert-to pdf` để xem bố cục, chép `HSMT_ket_qua.docx` (đổi tên theo gói thầu) và báo cáo kiểm tra vào `/mnt/user-data/outputs/`, gọi `present_files`.
8. Trả lời ngắn: số vòng, kết quả hai lớp kiểm tra, điểm lệch RFP có căn cứ, các mục cần người dùng quyết.

## Khi người dùng muốn sửa

- Sửa giá trị (ngày, tiền, tỷ lệ, chính sách): sửa tham số, chạy lại từ bước 3.
- Sửa nội dung diễn đạt: sửa `ban_soan.json` ở ID tương ứng, chạy lại bước 5.
- Mặc định đưa chỉ dẫn sửa từng phần (vị trí, hiện tại, sửa thành). Chỉ tự chạy lại và xuất file khi người dùng yêu cầu rõ.
- Không sửa Chương I, Chương VI, Mục 1 Chương III, các cột cố định của mẫu.
