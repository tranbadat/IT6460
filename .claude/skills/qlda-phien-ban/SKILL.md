---
name: qlda-phien-ban
description: Quản lý phiên bản bộ tài liệu dự án (version control) - sổ phiên bản tự động theo băm nội dung và băm đầu vào, trạng thái dự thảo, đã kiểm tra, đã duyệt, đường cơ sở, khóa hồ sơ đấu thầu sau ký hợp đồng, liên kết yêu cầu thay đổi với phiên bản sau thay đổi, lịch sử git, xuất sổ phiên bản Excel và tài liệu quản lý phiên bản. Dùng khi người dùng muốn lập tài liệu quản lý phiên bản, đặt đường cơ sở, cập nhật trạng thái tài liệu, xem lịch sử phiên bản.
---

# Quản lý phiên bản

Mọi script của bộ skill tự đăng ký phiên bản vào du_lieu/phien_ban.json khi tạo tệp: 0.1 lần đầu, tăng 0.1 khi nội dung đổi, giữ nguyên khi chạy lại cùng nội dung. Quy ước: `references/quy_uoc.json`.

## Lệnh

| Lệnh | Khi dùng |
|---|---|
| `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py trang_thai <tệp> --trang-thai "Đã kiểm tra" --nguoi "..."` | Sau khi đạt kiểm tra lớp B (agent Kiểm tra tự chạy) hoặc khi trưởng nhóm phê duyệt ("Đã duyệt") |
| `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py duong_co_so BL1 --ten "Đường cơ sở hợp đồng" --ngay yyyy-mm-dd --hop-dong` | Ký hợp đồng: HSMT, HSDT chuyển Khóa, các tài liệu kế hoạch lên 1.0 |
| `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py duong_co_so BL2 --ten "..."` | Đường cơ sở tiếp theo (sau CR lớn, khi nghiệm thu). Không lập được nếu tài liệu còn dùng đầu vào cũ |
| `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py tong_hop` | Tổng hợp sổ phiên bản, nhật ký chạy, sổ thay đổi, git thành So_phien_ban.xlsx |

## Tài liệu quản lý phiên bản

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi phien_ban` (tự chạy tong_hop).
2. Agent Soạn thảo viết phạm vi, vai trò quản lý cấu hình, nhận xét đường cơ sở và tình hình kiểm soát phiên bản.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien phien_ban --ghi-chu "..."`
4. Agent Kiểm tra lớp B với `dac_ta/tai_lieu_phien_ban.json`.

Đầu ra: ket_qua/15_Quan_ly_phien_ban/So_phien_ban.xlsx, Tai_lieu_quan_ly_phien_ban.docx.

Thư mục dự án nên là kho git: commit sau mỗi lần hoàn thiện tài liệu với nội dung "<bước> <phiên bản>", gắn thẻ khi lập đường cơ sở. Lịch sử git được đưa vào sổ phiên bản.
