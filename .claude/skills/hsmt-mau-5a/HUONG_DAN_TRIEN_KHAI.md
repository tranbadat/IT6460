# Hướng dẫn triển khai

## Đầu vào cần có
- Mau_5A.docx và RFP.pdf của ABC Wear: đã đính kèm trong cả hai gói.
- tham_so_chu_dau_tu.json: đã có bản cho ABC Wear. Với gói thầu khác, sao chép và sửa giá trị theo references/tham_so.md.

## Claude
1. Cài hsmt-mau-5a.skill (mở thẻ file và bấm Save skill, hoặc tải lên ở phần Skills trong Settings).
2. Bật Code execution and file creation.
3. Gõ: "Lập HSMT theo Mẫu 5A cho RFP ABC Wear". Với RFP khác, tải RFP và file tham số lên cùng tin nhắn.

## ChatGPT (Custom GPT)
1. Instructions: dán nội dung INSTRUCTIONS_GPT.md.
2. Knowledge: tải lên toàn bộ file trong gói HSMT_Mau5A_cho_ChatGPT.zip (không cần thư mục).
3. Bật Code Interpreter & Data Analysis.
4. Gõ: "Lập HSMT theo Mẫu 5A cho RFP ABC Wear".
Nếu Code Interpreter báo thiếu thư viện docx, chạy các script tại máy cá nhân.

## Tách agent
| Môi trường | Cách làm |
|---|---|
| Claude Code, Cowork | Agent chính chạy script. Giao Phân tích RFP, Soạn thảo, Kiểm tra cho ba agent con, mỗi agent nhận đúng file prompts/vai_*.md và các file được phép đọc |
| claude.ai | Chat 1 chạy toàn bộ. Mở chat 2 không bật skill, dán prompts/vai_kiem_tra.md, tải lên file Word, Mau_5A.docx, RFP.pdf và 5 file nguồn chuẩn trong thư mục làm việc để kiểm tra lớp B |
| ChatGPT | GPT 1 (điều phối, Phân tích RFP, Soạn thảo, Sửa) dùng INSTRUCTIONS_GPT.md. GPT 2 (Kiểm tra) dùng vai_kiem_tra.md làm Instructions, Knowledge chỉ gồm verify_hsmt.py, Mau_5A.docx, RFP.pdf, van_phong.md, quy_trinh.md |
| API | Ba lần gọi với ba system prompt trong thư mục prompts, nối bằng chay_quy_trinh.py |

## Chạy các bước script tại máy cá nhân
```bash
pip install python-docx
mkdir hsmt   # đặt rfp_yeu_cau.json do agent Phân tích RFP lập vào đây
python3 scripts/chay_quy_trinh.py chuan_bi assets/Mau_5A.docx dau_vao/tham_so_chu_dau_tu.json hsmt
# đặt ban_soan.json do agent Soạn thảo lập vào hsmt
python3 scripts/chay_quy_trinh.py hoan_thien assets/Mau_5A.docx hsmt
```
