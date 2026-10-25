---
name: qlda-phien-ban
description: Quản lý phiên bản bộ tài liệu dự án (version control) - sổ phiên bản tự động theo băm nội dung và băm đầu vào, trạng thái dự thảo, đã kiểm tra, đã duyệt, đường cơ sở BL1 (ký hợp đồng) và BL2 (sau yêu cầu thay đổi), khóa hồ sơ đấu thầu sau ký hợp đồng, phiên bản tài liệu gắn bản phát hành theo sprint, liên kết yêu cầu thay đổi với phiên bản sau thay đổi, lịch sử git, xuất sổ phiên bản Excel và tài liệu quản lý phiên bản. Dùng khi người dùng muốn lập tài liệu quản lý phiên bản, đặt đường cơ sở, cập nhật trạng thái tài liệu, xem lịch sử phiên bản.
---

# Quản lý phiên bản

Mọi script của bộ skill tự đăng ký phiên bản vào du_lieu/phien_ban.json khi tạo tệp: 0.1 lần đầu, tăng 0.1 khi nội dung đổi, giữ nguyên khi chạy lại cùng nội dung. Quy ước: `references/quy_uoc.json`.

## Lệnh

| Lệnh | Khi dùng |
|---|---|
| `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py trang_thai <tệp> --trang-thai "Đã kiểm tra" --nguoi "..."` | Sau khi đạt kiểm tra lớp B (agent Kiểm tra tự chạy) hoặc khi trưởng nhóm phê duyệt ("Đã duyệt"). Không đổi trạng thái phiên bản Đường cơ sở, Khóa |
| `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py duong_co_so BL1 --ten "Đường cơ sở hợp đồng" --ngay yyyy-mm-dd --hop-dong` | Ký hợp đồng: HSMT, HSDT chuyển Khóa, các tài liệu kế hoạch lên 1.0. Chỉ một lần, lệnh thứ hai có --hop-dong bị từ chối |
| `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py duong_co_so BL2 --ten "..." --cr CR03 --ngay yyyy-mm-dd` | Đường cơ sở sau yêu cầu thay đổi đã phê duyệt (CR phải có trong du_lieu/thay_doi.json, trạng thái Đã phê duyệt, Đã thực hiện hoặc Đã đóng sau thực hiện), lập sau khi đã cập nhật các tài liệu bị ảnh hưởng. Không lập được nếu tài liệu còn dùng đầu vào cũ |
| `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py duong_co_so BL2 --ten "..." --cr CR03 --ngay yyyy-mm-dd --lap-lai "<lý do>"` | Từ 1.2.5: lập lại đường cơ sở sau thay đổi cùng mã, cùng ngày sau khi sửa tài liệu theo kiểm tra lớp B. Bản cũ chuyển vào duong_co_so_thay_the, phiên bản cũ giữ trong sổ (đánh dấu duong_co_so_da_thay), phiên bản mới giữ số chính và tăng số phụ, lý do ghi vào lam_lai |
| `python .claude/skills/qlda-phien-ban/scripts/so_phien_ban.py tong_hop` | Tổng hợp sổ phiên bản, nhật ký chạy, sổ thay đổi, git thành So_phien_ban.xlsx |

## Bản phát hành và đường cơ sở

- Bản phát hành R<n> lập cuối mỗi sprint bằng `qlda-master-schedule/scripts/phat_hanh.py` (du_lieu/phat_hanh.json), bản của sprint có cut over là bản chính thức.
- Sau ký hợp đồng (giai đoạn thực hiện), mỗi phiên bản tài liệu mới trong du_lieu/phien_ban.json ghi khóa phat_hanh: bản phát hành hiện hành tại ngày tài liệu (ngay_tai_lieu, không có thì ngày hiện hành). Rỗng khi chưa có bản phát hành. Khi mô phỏng dự án đặt biến môi trường QLDA_NGAY=yyyy-mm-dd.
- Mỗi đường cơ sở lưu ngày, căn cứ (ký hợp đồng hoặc mã CR), bản phát hành tại ngày lập, danh sách tài liệu và phiên bản. Bản ghi phiên bản đường cơ sở lưu thêm băm đầu vào tại lúc lập (vao_duong_co_so).
- Phiên bản Đường cơ sở, Khóa không bị ghi đè: đăng ký lại cùng nội dung chỉ cập nhật thông tin kiểm tra, không đổi số phiên bản, trạng thái, đường cơ sở, bản phát hành, ghi chú. Thay đổi sau đường cơ sở tạo phiên bản 1.1, 1.2 qua yêu cầu thay đổi.
- Yêu cầu thay đổi và phiên bản (từ 1.2.0): phiên bản đăng ký sau quyết định phê duyệt một CR (thu_tu lớn hơn dem_phien_ban_khi_quyet_dinh) của bước thuộc tai_lieu_cap_nhat, đến khi CR đóng, được gắn ma_cr và mã CR trong ghi chú (loi.dang_ky_phien_ban khi đăng ký, tong_hop và duong_co_so --cr bổ sung cho sổ cũ), gồm cả bản sửa sau đường cơ sở sau thay đổi (vẫn thuộc đường cơ sở đó). duong_co_so --cr ghi phien_ban_sau của CR trong du_lieu/thay_doi.json (tài liệu có phiên bản thuộc đường cơ sở, không gồm tài liệu khóa); tong_hop suy phien_ban_sau từ đường cơ sở khi CR chưa ghi.
- Bảng tổng hợp: tên tài liệu có dấu theo bước (WBS theo tên nhóm, báo cáo tiến độ theo kỳ, Cost estimate tách bảng tính và thuyết minh), bảng tài liệu thuộc đường cơ sở có mã TL và tệp, cột tài liệu cập nhật của CR ghi tên dữ liệu nguồn thay đường dẫn, ngày tài liệu suy từ ngày phát hành HSMT, tệp cùng bước cùng phiên bản hoặc ngày đường cơ sở khi phiên bản chưa ghi.
- Sổ phiên bản Excel: cột Bản phát hành ở Danh_muc và Lich_su, sheet Duong_co_so có bản phát hành và căn cứ, sheet Phat_hanh (số gói, lỗi, CR, số phiên bản tài liệu gắn từng bản bằng công thức).

## Tài liệu quản lý phiên bản

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi phien_ban` (tự chạy tong_hop).
2. Agent Soạn thảo viết phạm vi, vai trò quản lý cấu hình, nhận xét đường cơ sở và tình hình kiểm soát phiên bản.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien phien_ban --ghi-chu "..."`
4. Agent Kiểm tra lớp B với `dac_ta/tai_lieu_phien_ban.json`.

Đầu ra: ket_qua/15_Quan_ly_phien_ban/So_phien_ban.xlsx, Tai_lieu_quan_ly_phien_ban.docx.

Thư mục dự án nên là kho git: commit sau mỗi lần hoàn thiện tài liệu với nội dung "<bước> <phiên bản>", gắn thẻ khi lập đường cơ sở. Lịch sử git được đưa vào sổ phiên bản.

Từ 1.2.6: tong_hop đếm so_lan_agent theo loai agent, tách so_lan_nguoi_dung; chuẩn hóa tên skill bị ghép mã bước; ghi chú lịch sử thay dấu chấm phẩy; phien_ban_tong_hop có lam_lai và duong_co_so_thay_the (sheet Duong_co_so có phần Đường cơ sở đã thay); ngày trong Excel dạng dd/mm/yyyy.
