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
| `dau_vao/Mau_5A.docx`, `dau_vao/RFP.pdf` của dự án | Mẫu gốc và RFP. Đây là nguồn duy nhất, skill không giữ bản sao. Cách tải lại mẫu: `assets/README.txt` |
| `dau_vao/tham_so_chu_dau_tu.json` của dự án | Tham số chủ đầu tư (giá trị RFP không có) |
| `scripts/rfp_sang_anh.py` | Bước 2: chuyển RFP sang ảnh để agent xem |
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

Skill chạy được trên máy cá nhân (Claude Code trong VS Code, terminal) và trên claude.ai. Lệnh Python: dùng `python` trên Windows, `python3` trên macOS, Linux. Cần thư viện `python-docx` và `pymupdf` (`pip install python-docx pymupdf`). Thiếu thì cài trước khi chạy.

Thư mục, tính từ thư mục gốc của dự án (thư mục đang mở):
- Đầu vào: `dau_vao/` của dự án (RFP.pdf, Mau_5A.docx, tham_so_chu_dau_tu.json). Trên claude.ai, tải ba tệp này lên cùng tin nhắn. Thiếu tệp nào thì dừng và hỏi người dùng.
- Làm việc: `hsmt_lam_viec/`. Trên claude.ai dùng `/home/claude/hsmt`.
- Kết quả: `ket_qua/`. Trên claude.ai chép thêm vào `/mnt/user-data/outputs/` và gọi `present_files`.
- `<skill>` là thư mục chứa file SKILL.md này, ví dụ `.claude/skills/hsmt-mau-5a`.

Các bước:
1. Xác định đầu vào như trên. RFP khác ABC Wear mà chưa có tham số thì dừng và hỏi các trường trong `references/tham_so.md`.
2. Agent Phân tích RFP theo `prompts/vai_phan_tich_rfp.md`. Chuyển RFP thành ảnh bằng `python <skill>/scripts/rfp_sang_anh.py <RFP.pdf> hsmt_lam_viec/anh_rfp`, xem từng ảnh, ghi `hsmt_lam_viec/rfp_yeu_cau.json`.
3. `python <skill>/scripts/chay_quy_trinh.py chuan_bi <Mau_5A.docx> <tham_so.json> hsmt_lam_viec`. Lỗi tham số thì dừng và báo người dùng.
4. Agent Soạn thảo theo `prompts/vai_soan_thao.md`, ghi `hsmt_lam_viec/ban_soan.json`.
5. `python <skill>/scripts/chay_quy_trinh.py hoan_thien <Mau_5A.docx> hsmt_lam_viec`. Mã thoát 2 thì xử lý theo `prompts/vai_sua.md` và chạy lại. Tối đa 3 vòng.
6. Agent Kiểm tra lớp B theo `prompts/vai_kiem_tra.md`. Có công cụ tạo agent con (Task, Agent) thì giao cho agent con, chỉ chuyển các file được phép đọc. Không có thì tự đóng vai và chỉ đọc các file được phép. Có lỗi thì quay lại bước 4 hoặc 5.
7. Đạt:
   - Trong bộ BTL_QLDA (có `.claude/skills/qlda-loi`): `python .claude/skills/qlda-loi/scripts/trich_hsmt.py hsmt_lam_viec`. Lệnh chép HSMT vào `ket_qua/01_HSMT/HSMT.docx`, trích `du_lieu/hsmt.json`, `du_lieu/rfp_yeu_cau.json` cho các skill WBS, lịch, dự toán, HSDT, kế hoạch, đăng ký phiên bản và ghi nhật ký.
   - Dùng riêng skill: chép `hsmt_lam_viec/HSMT_ket_qua.docx` vào `ket_qua/` với tên `HSMT_<tên gói thầu ngắn>.docx`, kèm báo cáo kiểm tra.
   - Nếu máy có LibreOffice thì chuyển PDF (`soffice --headless --convert-to pdf`) để xem bố cục.
8. Trả lời ngắn: số vòng, kết quả hai lớp kiểm tra, điểm lệch RFP có căn cứ, mục cần người dùng quyết.

## Nhật ký bằng chứng (trong bộ BTL_QLDA)

Sau mỗi bước của agent, ghi nhật ký để nộp kèm bằng chứng prompt:
`python .claude/skills/qlda-loi/scripts/nhat_ky.py --skill hsmt-mau-5a --buoc hsmt.<phan_tich_rfp|soan|kiem_tra_lop_B|sua> --vai "<tên vai>" --prompt .claude/skills/hsmt-mau-5a/prompts/<tệp prompt> --vao <tệp đã đọc> --ra <tệp đã ghi> --tom-tat "<kết quả>" --moi-truong "<công cụ, mô hình>"`

## Khi người dùng muốn sửa

- Sửa giá trị (ngày, tiền, tỷ lệ, chính sách): sửa tham số, chạy lại từ bước 3, rồi chạy lại bước 7 và `python .claude/skills/qlda-loi/scripts/chay.py anh_huong hsmt` để biết tài liệu sau cần cập nhật.
- Sau khi ký hợp đồng, HSMT là đường cơ sở đấu thầu: không tạo lại, thay đổi ghi bằng phụ lục hợp đồng hoặc biên bản.
- Sửa nội dung diễn đạt: sửa `ban_soan.json` ở ID tương ứng, chạy lại bước 5.
- Mặc định đưa chỉ dẫn sửa từng phần (vị trí, hiện tại, sửa thành). Chỉ tự chạy lại và xuất file khi người dùng yêu cầu rõ.
- Không sửa Chương I, Chương VI, Mục 1 Chương III, các cột cố định của mẫu.
