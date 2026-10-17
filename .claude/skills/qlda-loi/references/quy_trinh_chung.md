# Quy trình chung: làm, kiểm tra, sửa

Mọi tài liệu của bộ skill đi qua cùng một vòng. Số liệu do script tính, agent chỉ viết lời văn, kiểm tra do script và agent độc lập thực hiện.

## 1. Tạo dữ liệu (bước dữ liệu)

| Bước | Agent viết | Script kiểm tra và tính | Dữ liệu chuẩn |
|---|---|---|---|
| hsmt | theo skill hsmt-mau-5a | trich_hsmt.py | du_lieu/hsmt.json, rfp_yeu_cau.json |
| wbs | wbs_nhap.json (vai_lap_wbs.md) | kiem_tra_wbs.py | du_lieu/wbs.json |
| giao_viec | phan_cong_nhap.json (vai_giao_viec.md) | kiem_tra_giao_viec.py | du_lieu/phan_cong.json |
| lich | moc_nhap.json (vai_lap_moc.md) | lap_lich.py, xuat_gantt.py | du_lieu/lich.json, Master_schedule.xlsx |
| rui_ro | rui_ro_nhap.json (vai_phan_tich_rui_ro.md) | kiem_tra_rui_ro.py | du_lieu/rui_ro.json |
| chi_phi | không | tinh_chi_phi.py | du_lieu/chi_phi.json, Cost_estimate.xlsx |
| thay đổi | cr_nhap.json (vai_danh_gia_thay_doi.md) | yeu_cau_thay_doi.py | du_lieu/thay_doi.json |
| tiến độ | không, nhóm ghi CSV thực tế | tinh_tien_do.py --ky Sx | du_lieu/tien_do/ |
| so_lieu_ket_thuc | không | tong_hop_ket_thuc.py | du_lieu/ket_thuc.json |
| bai_hoc | bai_hoc_nhap.json (vai_rut_bai_hoc.md) | kiem_tra_bai_hoc.py | du_lieu/bai_hoc.json |
| bang_luong | không | chia_luong.py | du_lieu/luong.json, Bang_phan_chia_luong.xlsx |
| phien_ban | không | so_phien_ban.py tong_hop | du_lieu/phien_ban_tong_hop.json, So_phien_ban.xlsx |

Script kiểm tra trả mã 1 khi còn lỗi. Agent sửa tệp nhập rồi chạy lại, tối đa 3 lần.

## 2. Tạo tài liệu Word (bước tài liệu)

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi <buoc>`
   Kiểm tra đầu vào, chạy script tính trước (khóa truoc của đặc tả), lập lam_viec/<buoc>/khung.json. Phần bảng và số liệu đã điền sẵn từ dữ liệu chuẩn, khóa can_soan liệt kê các đoạn agent phải viết.
2. Agent Soạn thảo (qlda-loi/prompts/vai_soan_thao.md) viết lam_viec/<buoc>/ban_soan.json. Mọi con số viết bằng tham chiếu {bi_danh#duong_dan|dinh_dang}.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien <buoc> --ghi-chu "<tóm tắt>"`
   Ghép bản soạn, dựng Word, kiểm tra lớp A (kiem_tra_tai_lieu.py), sửa tự động lỗi cơ học, lặp tối đa 3 vòng. Đạt thì chép vào ket_qua, đăng ký phiên bản, ghi nhật ký.
4. Agent Kiểm tra độc lập (vai_kiem_tra.md), chạy trong phiên riêng, không đọc bản soạn, kiểm tra lớp B theo CL01 đến CL06 và tiêu chí doc_hieu.
5. Còn lỗi thì agent Sửa (vai_sua.md) phân loại: sửa bản soạn, sửa dữ liệu nguồn ở bước trước, hoặc chuyển người dùng quyết định.

## 3. Khi có thay đổi

- `python .claude/skills/qlda-loi/scripts/chay.py trang_thai` liệt kê bước cập nhật, cũ (đầu vào đã đổi), thiếu đầu vào, sẵn sàng.
- `python .claude/skills/qlda-loi/scripts/chay.py anh_huong <nút hoặc tệp>` liệt kê bước bị ảnh hưởng theo thứ tự, tách tài liệu khóa (HSMT, HSDT sau ký hợp đồng) cần phụ lục hoặc biên bản.
- Yêu cầu thay đổi đi qua yeu_cau_thay_doi.py: đánh giá, quyết định, cập nhật các bước, đóng (chỉ đóng khi mọi tài liệu đã tạo lại sau quyết định). Khi hoàn thiện lại tài liệu theo CR, dùng `chay.py hoan_thien <buoc> --ghi-chu "CRxx" --ngay <ngày cập nhật theo lịch dự án>` để ngày trên tài liệu khớp lịch dự án.
- Ngày ghi trên tài liệu lấy theo lịch dự án (khóa ngay_tai_lieu của đặc tả): HSDT theo ngày ký đơn, tài liệu kế hoạch theo ngày bắt đầu dự án, báo cáo tiến độ theo ngày báo cáo, tài liệu kết thúc theo ngày chốt số liệu. Sổ phiên bản và phụ lục bằng chứng ghi thời điểm chạy thực tế.
- Đường cơ sở: so_phien_ban.py duong_co_so (ký hợp đồng thì thêm --hop-dong).

## 4. Bằng chứng

- Mọi script và agent ghi bang_chung/nhat_ky_chay.jsonl: thời điểm, skill, phiên bản skill, vai, prompt (lưu bản sao theo băm), đầu vào, đầu ra kèm băm, kết quả.
- Báo cáo kiểm tra lớp A, lớp B lưu trong lam_viec/<buoc>/ và bang_chung/kiem_tra/.
- `python .claude/skills/qlda-loi/scripts/chay.py bang_chung` xuất Phụ lục bằng chứng prompt và skill (ket_qua/16_Bang_chung).
