# BTL_QLDA: bộ skill lập và quản lý tài liệu dự án ABC Wear

Bộ gồm 16 skill cho Claude Code (VS Code hoặc terminal) để lập toàn bộ tài liệu của bài tập lớn từ RFP và Mẫu 5A, theo vòng làm, kiểm tra, sửa với agent độc lập, kèm nhật ký bằng chứng prompt và skill.

## 1. Cài đặt

1. Mở thư mục gốc của kho git này bằng VS Code (File, Open Folder). Thư mục `.claude/skills/` chứa các skill, Claude Code tự nhận khi mở thư mục. Khi cần nộp dạng thư mục BTL_QLDA, đóng gói bằng `git archive --prefix=BTL_QLDA/ -o BTL_QLDA.zip HEAD`.
2. Cài Python 3.10 trở lên, rồi chạy trong terminal của VS Code: `pip install -r requirements.txt`
3. Nên cài LibreOffice để script tính lại công thức Excel và đối chiếu số liệu. Không có LibreOffice thì Excel tự tính khi mở tệp.
4. Dự án đã là kho git. Commit sau mỗi bước để lịch sử git được đưa vào sổ phiên bản.
5. Mở Claude Code, gõ: `Xem trạng thái dự án` (Claude chạy `chay.py trang_thai`).

Windows dùng lệnh `python`, macOS và Linux dùng `python3`.

Dùng với công cụ khác: Codex CLI và các agent lập trình khác đọc AGENTS.md. CLAUDE.md chỉ nhập AGENTS.md (`@AGENTS.md`), nên hướng dẫn agent chỉ sửa ở AGENTS.md, skill nằm ở .claude/skills/, mỗi skill mở bằng SKILL.md. ChatGPT có chạy mã: tải tệp zip lên, yêu cầu giải nén, đọc AGENTS.md và SKILL.md của skill cần dùng rồi chạy các lệnh trong đó. Skill HSMT có hướng dẫn riêng cho ChatGPT tại .claude/skills/hsmt-mau-5a/INSTRUCTIONS_GPT.md.

## 2. Nhóm cần điền trước

| Tệp | Nội dung | Ghi chú |
|---|---|---|
| dau_vao/RFP.pdf, Mau_5A.docx | RFP của ABC Wear, Mẫu 5A gốc | Đã có sẵn |
| dau_vao/tham_so_chu_dau_tu.json | Tham số chủ đầu tư cho HSMT | Đã có, rà lại |
| dau_vao/du_an.json | Ngày bắt đầu, cut over, ngày nghỉ, sprint, ngưỡng SPI, CPI | Rà lại ngày nghỉ 2027 |
| dau_vao/thanh_vien.json | Thành viên và vị trí bổ sung, trình độ, số năm kinh nghiệm | Ghi họ tên thật cho các dòng có _can_xac_nhan rồi bỏ khóa này. Người giữ vị trí chủ chốt phải có trình độ và kinh nghiệm |
| dau_vao/don_gia.json | Đơn giá trọn gói, lương tham chiếu, chi phí khác, giá chào mục tiêu, thuế | Rà lại nguồn đơn giá |
| dau_vao/nha_thau.json | Pháp nhân, ngày ký đơn, hợp đồng tương tự, doanh thu, bảo đảm dự thầu của Inter Solution | Để trống, nhóm tự điền. HSDT không lập được khi còn trống |
| dau_vao/kpi.json | Ghi đè ngưỡng KPI đánh giá | Không bắt buộc |
| dau_vao/thuc_te/*.csv, retro.md | Dữ liệu thực tế trong quá trình thực hiện | Cách ghi: .claude/skills/qlda-bao-cao-tien-do/references/nhap_lieu.md |

## 3. Thứ tự thực hiện

Có thể yêu cầu Claude theo từng câu, ví dụ "Lập WBS", "Lập master schedule", "Báo cáo tiến độ sprint S3". Claude đọc skill tương ứng và chạy đúng các bước.

| Giai đoạn | Yêu cầu Claude | Kết quả trong ket_qua/ |
|---|---|---|
| Lập kế hoạch | Lập hồ sơ mời thầu | 01_HSMT |
| | Lập hồ sơ dự thầu (sau WBS, lịch, rủi ro, dự toán) | 02_HSDT |
| | Lập WBS | 03_WBS (mỗi nhóm một tệp và tệp tổng hợp) |
| | Lập master schedule | 04_Master_schedule (Excel Gantt) |
| | Lập master plan | 05_Master_plan |
| | Lập cost estimate | 06_Cost_estimate (Excel, thuyết minh) |
| Kế hoạch thực hiện | Lập kế hoạch quản lý rủi ro | 07_Risk_management_plan |
| | Lập kế hoạch quản lý thay đổi | 08_Change_management_plan |
| | Báo cáo tiến độ sprint Sx | 09_Bao_cao_tien_do |
| | Lập danh sách phân chia công việc | 10_Responsibilities |
| Kết thúc | Báo cáo tổng kết dự án | 11_Bao_cao_tong_ket |
| | Báo cáo đánh giá dự án | 12_Bao_cao_danh_gia |
| | Báo cáo bài học kinh nghiệm | 13_Bai_hoc_kinh_nghiem |
| | Bảng phân chia lương | 14_Bang_phan_chia_luong (Excel) |
| | Tài liệu quản lý phiên bản | 15_Quan_ly_phien_ban (Word, Excel) |
| Nộp kèm | Xuất phụ lục bằng chứng | 16_Bang_chung |

Thứ tự phụ thuộc thực tế: HSMT, WBS, giao việc, master schedule, sổ rủi ro, cost estimate, HSDT, kế hoạch rủi ro, kế hoạch thay đổi, master plan, tài liệu WBS, phân công. Sau khi ký hợp đồng thì lập đường cơ sở có khóa HSMT, HSDT. `chay.py trang_thai` luôn gợi ý bước tiếp theo.

## 4. Ứng phó rủi ro và thay đổi

- Rủi ro đổi trạng thái: ghi dau_vao/thuc_te/theo_doi_rui_ro.csv. Báo cáo tiến độ, tổng kết, đánh giá, bài học đều đọc tệp này.
- Yêu cầu thay đổi: "Đánh giá yêu cầu thay đổi: <nội dung>". Claude lập CR, script tính tác động và danh sách tài liệu phải cập nhật, chờ quyết định, cập nhật lần lượt, chỉ đóng CR khi mọi tài liệu đã tạo lại.
- Bất kỳ đầu vào nào thay đổi: `python .claude/skills/qlda-loi/scripts/chay.py anh_huong <tệp>` liệt kê tài liệu bị ảnh hưởng.

## 5. Bằng chứng nộp kèm

- bang_chung/nhat_ky_chay.jsonl: mọi lần chạy script và agent, kèm băm đầu vào, đầu ra, phiên bản skill, bản sao prompt (bang_chung/prompts/).
- lam_viec/<bước>/: tệp nhập của agent, khung, bản soạn, bản Word từng vòng, báo cáo kiểm tra lớp A. bang_chung/kiem_tra/: báo cáo lớp B.
- ket_qua/16_Bang_chung/Phu_luc_bang_chung_prompt_skill.docx: phụ lục tổng hợp skill, sơ đồ phụ thuộc, phiên bản, kết quả kiểm tra, nhật ký, danh mục prompt.
- Bản thân thư mục .claude/skills/ là bằng chứng skill. Nộp kèm toàn bộ thư mục dự án hoặc kho git.

## 6. Giới hạn

- Bộ skill không chứa tài liệu hoàn chỉnh của nhóm. Chất lượng phụ thuộc dữ liệu nhóm điền và kiểm tra của agent độc lập.
- Thông tin nhà thầu, dữ liệu thực tế (nhật ký công việc, nghiệm thu, lỗi, rủi ro, retro) do nhóm ghi. Script kiểm tra tính hợp lệ, không kiểm tra được tính trung thực.
- Ngày nghỉ năm 2027 trong du_an.json là dự kiến, cần cập nhật theo thông báo chính thức.
- Ngày ghi trên tài liệu theo lịch dự án (HSDT theo ngày ký đơn, kế hoạch theo ngày bắt đầu, báo cáo theo ngày báo cáo hoặc ngày chốt). Sổ phiên bản và phụ lục bằng chứng ghi thời điểm chạy thực tế.
- Mục lục là trường tự động: khi mở tệp, Word hỏi cập nhật trường, chọn Yes để có số trang. Cập nhật mục lục trong Word trước khi xuất PDF, vì bản chuyển bằng LibreOffice không có số trang.
- Kiểm tra lớp B do agent thực hiện, nên đọc lại các tài liệu chính trước khi nộp.
