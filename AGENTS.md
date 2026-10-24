# Bài tập lớn Quản trị dự án và Quản lý thay đổi, nhóm PM_26I_02

Dự án: Xây dựng và triển khai hệ thống website bán hàng trực tuyến (Web Selling Site System) cho Công ty Cổ phần ABC Wear. Nhóm đóng hai vai: tư vấn lập HSMT theo Mẫu 5A (Thông tư 79/2025/TT-BTC) và nhà thầu lập HSDT, kế hoạch, thực hiện, kết thúc dự án. Thông tin nhà thầu nằm trong dau_vao/nha_thau.json (hiện là đơn vị tạm PM_26I_02), đổi nhà thầu chỉ sửa tệp này.

## Nguyên tắc bắt buộc

1. Không dùng HSMT, HSDT hay bất kỳ tài liệu hoàn chỉnh có sẵn nào của nhóm hoặc người khác làm đầu vào hay để so sánh. Mọi tài liệu lập từ RFP, Mẫu 5A, tệp trong dau_vao/ và dữ liệu do bộ skill tạo.
2. Số liệu do script tính và lưu trong du_lieu/. Agent chỉ viết lời văn, mọi con số viết bằng tham chiếu dữ liệu. Sai số liệu thì sửa ở bước tạo dữ liệu, không sửa trong Word.
3. Mỗi tài liệu đi qua vòng làm, kiểm tra lớp A (script), kiểm tra lớp B (agent độc lập, phiên riêng, không đọc bản soạn), sửa. Tối đa 3 vòng, sau đó dừng và báo người dùng.
4. Mỗi bước agent ghi nhật ký bằng `.claude/skills/qlda-loi/scripts/nhat_ky.py`. Không xóa bang_chung/ và lam_viec/.
5. Văn phong trang trọng, không khẩu ngữ, không ghi chú nháp hay lời dẫn. Trình bày theo `.claude/skills/qlda-loi/references/van_phong.md`: Times New Roman 13, bảng lưới, không in đậm (trừ mục cha WBS), không viết hoa toàn bộ, không dùng ngoặc kép để nhấn mạnh, gạch ngang đơn thay cho gạch dài, hạn chế dấu chấm phẩy.
6. Với tài liệu đã lưu, khi được yêu cầu sửa thì đưa chỉ dẫn sửa từng phần (vị trí, hiện tại, sửa thành). Chỉ chạy lại và xuất tệp khi được yêu cầu rõ.
7. Không tự quyết thay nhóm các tham số: giá, phạm vi, nhân sự, thông tin nhà thầu, dữ liệu thực tế. Thiếu thì hỏi.
8. Trả lời người dùng bằng tiếng Việt, văn phong trang trọng.

## Bắt đầu mỗi phiên

`python .claude/skills/qlda-loi/scripts/chay.py trang_thai` cho biết bước nào cập nhật, cũ, thiếu đầu vào, sẵn sàng. Làm theo gợi ý "Nên làm tiếp". Quy trình chung: `.claude/skills/qlda-loi/references/quy_trinh_chung.md`.

## Thứ tự các skill

| Giai đoạn | Bước | Skill |
|---|---|---|
| Lập kế hoạch | Hồ sơ mời thầu | hsmt-mau-5a, sau đó `qlda-loi/scripts/trich_hsmt.py` |
| | WBS (dữ liệu) | qlda-wbs |
| | Giao việc | qlda-phan-cong |
| | Master schedule | qlda-master-schedule |
| | Sổ rủi ro | qlda-risk |
| | Cost estimate | qlda-cost-estimate |
| | Hồ sơ dự thầu | qlda-hsdt |
| | Kế hoạch rủi ro, kế hoạch thay đổi | qlda-risk, qlda-change |
| | Master plan, tài liệu WBS, phân công | qlda-master-plan, qlda-wbs, qlda-phan-cong |
| | Ký hợp đồng | `qlda-phien-ban/scripts/so_phien_ban.py duong_co_so BL1 --ten "..." --hop-dong` |
| Thực hiện | Báo cáo tiến độ mỗi sprint | qlda-bao-cao-tien-do |
| | Yêu cầu thay đổi | qlda-change |
| | Số liệu thực tế mô phỏng mỗi sprint, bản phát hành | qlda-mo-phong (chu_trinh.py), qlda-master-schedule (phat_hanh.py) |
| Kết thúc | Số liệu kết thúc, tổng kết | qlda-tong-ket |
| | Đánh giá, bài học | qlda-danh-gia, qlda-bai-hoc |
| | Bảng phân chia lương | qlda-bang-luong |
| | Quản lý phiên bản, phụ lục bằng chứng | qlda-phien-ban, `chay.py bang_chung` |

## Agent con

Kiểm tra lớp B giao cho agent con (công cụ Agent hoặc Task) với prompt `.claude/skills/qlda-loi/prompts/vai_kiem_tra.md`, chỉ chuyển đường dẫn tài liệu và đặc tả. Không có agent con thì tự đóng vai và chỉ đọc các tệp được phép.
