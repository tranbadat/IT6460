---
name: qlda-mo-phong
description: Mô phỏng giai đoạn thực hiện dự án theo kế hoạch đã duyệt - agent viết kịch bản biến cố từng sprint (gói chậm hoặc nhanh, người nghỉ, rủi ro trong sổ xảy ra, lỗi, vấn đề và hành động, chi phí khác, nghiệm thu, mốc đạt, họp cải tiến, yêu cầu thay đổi), script sinh số liệu thực tế nhất quán với lịch và phân công (mỗi người mỗi ngày không vượt 1 MD, chỉ làm gói đã đến lịch và đủ phụ thuộc, hạt giống tái lập, chặn ghi trùng, làm lại một sprint), kiểm tra nhất quán, điều phối chu trình mỗi sprint (báo cáo tiến độ, bản phát hành, phiên bản, yêu cầu thay đổi, đường cơ sở BL2) và các bước kết thúc. Dùng khi người dùng muốn mô phỏng dự án chạy thật, sinh dữ liệu thực tế cho sprint, chạy chu trình sprint, làm lại số liệu một sprint.
---

# Mô phỏng thực hiện dự án

Mọi dữ liệu thực tế do skill này sinh là số liệu mô phỏng. du_lieu/mo_phong.json ghi rõ điều đó (khóa `_ghi_chu`, `so_lieu_mo_phong`), cùng hạt giống, toàn văn kịch bản từng sprint và việc hẹn. Tài liệu dùng dữ liệu thực tế ghi "số liệu mô phỏng" ở phần căn cứ, dẫn chiếu tệp này.

Đầu vào kế hoạch: du_lieu/lich.json (sprint, gói lá với phan_nguoi, bat_dau, ket_thuc, phu_thuoc, du_tru_cpm; phan_bo quỹ huy động; mốc), wbs.json, rui_ro.json, thay_doi.json, hsmt.json, rfp_yeu_cau.json, dau_vao/thanh_vien.json, don_gia.json, du_an.json, chi_tieu_ky_thuat.json. Đầu ra: dau_vao/thuc_te/*.csv và retro.md theo định dạng của `qlda-bao-cao-tien-do/references/nhap_lieu.md`, du_lieu/mo_phong.json, lam_viec/mo_phong/.

## Kịch bản và sinh số liệu

1. Agent Mô phỏng viết lam_viec/mo_phong/kich_ban_S<n>.json theo `prompts/vai_mo_phong.md`. Định dạng: `references/kich_ban.md`, ví dụ `references/vi_du/`.
2. `python .claude/skills/qlda-mo-phong/scripts/mo_phong_sprint.py S<n>`
   - Kiểm tra kịch bản KB01 đến KB15 (`scripts/kich_ban.py`): lý do, liên kết gói, rủi ro, vấn đề, yêu cầu thay đổi, gói đã đến lịch, thành viên được huy động, ngày trong sprint, mốc, tiêu chí nghiệm thu có mã RFP và hạng mục Mẫu 01A, cut over, mức vừa phải (cảnh báo).
   - Sinh công theo ngày (`scripts/mo_phong_lich.py`): công cần của người trên gói theo phan_nguoi nhân hệ số biến cố (gói không có biến cố có nhiễu ngẫu nhiên nhỏ theo hạt giống), cộng MD tác động của rủi ro và sửa lỗi. Gói chỉ làm khi đã đến ngày bắt đầu (lùi theo số ngày trễ) và mọi gói tiền nhiệm đã hoàn thành trước đó. Mỗi người mỗi ngày tối đa tỷ lệ tham gia, chỉ trong sprint được huy động, trừ ngày nghỉ. Nhịp làm theo kế hoạch tuyến tính, làm bù khi chậm, ưu tiên gói có ngày kết thúc muộn nhất sớm hơn. Ghi theo bội số 0,25 MD. Không có biến cố và không nhiễu thì số liệu trùng kế hoạch (SPI, CPI bằng 1).
   - Ghi biến cố (`scripts/ghi_bien_co.py`): rủi ro, lỗi, vấn đề, hành động, chi phí khác, nghiệm thu, mốc, họp cải tiến. Việc hẹn ngày sau sprint (lỗi đóng, hành động xong, vấn đề và rủi ro đóng) được ghi khi sinh sprint chứa ngày đó.
   - Kiểm tra nhất quán MP01 đến MP12 (`scripts/kiem_tra_mo_phong.py`) trên toàn bộ dữ liệu trước khi ghi: MD theo người mỗi ngày và theo quỹ sprint, gói chưa đến lịch, phụ thuộc, ghi công sau khi gói đạt 100%, lỗi đóng có ngày sửa, mốc khi gói căn cứ chưa xong, rủi ro xảy ra chưa có vấn đề. Có lỗi thì không ghi tệp nào.
   - Ra: dòng nối tiếp trong dau_vao/thuc_te/, lam_viec/mo_phong/ket_qua_S<n>.json (MD theo người, gói hoàn thành, gói chậm, SPI ước tính, gợi ý), lich_S<n>.json (lịch dùng khi sinh), truoc_S<n>/ (bản chụp trước khi sinh), cr_S<n>_<mã>.json khi kịch bản có yêu cầu thay đổi.
3. Sinh lại một sprint: `mo_phong_sprint.py S<n> --lam-lai`. Khôi phục bản chụp trước S<n> (xóa luôn các sprint sau, sinh lại theo thứ tự) rồi sinh lại. Tệp bị sửa tay sau lần sinh cuối thì dừng, `--ep` để chấp nhận mất phần sửa. Sinh lại không thành công thì dữ liệu giữ như trước lệnh. Chạy lại không có `--lam-lai` cho sprint đã sinh thì dừng, không ghi trùng. Sinh lại sprint có biến cố cr sau khi `yeu_cau_thay_doi.py danh_gia` đã ghi CR đó vào sổ (cùng mã, tiêu đề, ngày) không bị KB11 (từ 1.0.1); mã đã có trong sổ với tiêu đề hoặc ngày khác vẫn là lỗi KB11.
4. Kiểm tra riêng dữ liệu hiện có (kể cả dòng nhập tay): `mo_phong_sprint.py kiem_tra`.

Hạt giống: `--hat-giong` ở sprint đầu, mặc định `references/cau_hinh.json`, cố định trong du_lieu/mo_phong.json. Cùng hạt giống, kịch bản và lịch thì ra cùng số liệu.

Kỳ KT: giai đoạn Kết thúc sau cut over đến ngày đóng dự án (lich.json giai_doan mã ket_thuc, ngay_dong_du_an). `mo_phong_sprint.py KT` sinh số liệu cho các gói Kết thúc sau sprint cuối, chu trình `chu_trinh.py KT`. Báo cáo kỳ: `tinh_tien_do.py --ky <ngày đóng dự án> --ma KT`. Kỳ KT không có họp cải tiến và bản phát hành.

## Chu trình mỗi sprint

`python .claude/skills/qlda-mo-phong/scripts/chu_trinh.py S<n>` in các bước, trạng thái và lệnh, kèm QLDA_NGAY=<ngày cuối sprint> là ngày hiện hành khi mô phỏng (ngày tài liệu, bản phát hành, đường cơ sở). `--chay` chạy liên tiếp các bước script đến bước cần agent hoặc người dùng. Windows đặt biến bằng `set QLDA_NGAY=yyyy-mm-dd` trước lệnh.

0. Trước S1, ký hợp đồng: đường cơ sở BL1 (`qlda-phien-ban/scripts/so_phien_ban.py duong_co_so BL1 --ten "Đường cơ sở hợp đồng" --hop-dong`).
1. Agent Mô phỏng viết kịch bản (mục trên).
2. `mo_phong_sprint.py S<n>`.
3. Kịch bản có yêu cầu thay đổi: agent Đánh giá thay đổi đọc lam_viec/mo_phong/cr_S<n>_<mã>.json, lập lam_viec/thay_doi/cr_nhap.json theo `qlda-change/prompts/vai_danh_gia_thay_doi.md`, chạy `qlda-change/scripts/yeu_cau_thay_doi.py danh_gia lam_viec/thay_doi/cr_nhap.json` trước bước 4 để sổ vấn đề liên kết được mã CR (T18).
4. `qlda-bao-cao-tien-do/scripts/tinh_tien_do.py --ky S<n>`.
5. Bản phát hành R<n> ngay sau khi có hoan_thanh.csv, loi.csv của sprint: `qlda-master-schedule/scripts/phat_hanh.py S<n>` (gói, tính năng, lỗi của sprint). Phiên bản tài liệu đăng ký sau đó trong kỳ gắn bản phát hành hiện hành tại ngày tài liệu. Không có lệnh này thì ghi chú và gọi khi có.
6. `qlda-loi/scripts/chay.py chuan_bi bao_cao_tien_do`, agent Soạn thảo viết bản soạn (căn cứ ghi số liệu mô phỏng), `chay.py hoan_thien bao_cao_tien_do --ghi-chu "Kỳ S<n>, số liệu mô phỏng"`, agent Kiểm tra lớp B với `qlda-bao-cao-tien-do/dac_ta/bao_cao_tien_do.json`.
7. Phiên bản: `qlda-phien-ban/scripts/so_phien_ban.py trang_thai <báo cáo> --trang-thai "Đã kiểm tra" --nguoi "..."`, `so_phien_ban.py tong_hop`.
8. Yêu cầu thay đổi được phê duyệt: `yeu_cau_thay_doi.py quyet_dinh <mã> --ket-qua "Đã phê duyệt" ... --van-ban "<phụ lục>"`, áp dụng vào dữ liệu nguồn theo quy trình qlda-change (lệnh ap_dung khi có), chạy lại các bước kế hoạch theo `chay.py trang_thai`, đặt `so_phien_ban.py duong_co_so BL2 --ten "Đường cơ sở sau <mã>" --cr <mã>`. Sprint sau được mô phỏng theo lịch mới, gói mới có trong lịch mới được phân công như gói khác.

Mọi lệnh của chu trình chạy với QLDA_NGAY bằng ngày cuối sprint (kỳ KT là ngày đóng dự án), để phiên bản, nhật ký và khóa phat_hanh mang ngày dự án.

## Sau sprint cuối

`chu_trinh.py ket_thuc`: kỳ KT (khi lịch có giai đoạn Kết thúc), `qlda-tong-ket/scripts/tong_hop_ket_thuc.py`, báo cáo tổng kết, đánh giá (qlda-danh-gia), bài học (qlda-bai-hoc, đọc retro.md và mã R-Sx-nn do mô phỏng ghi), bảng lương (`qlda-bang-luong/scripts/chia_luong.py`), tài liệu quản lý phiên bản, `chay.py bang_chung`. Sprint cuối nên có nghiệm thu theo chỉ tiêu kỹ thuật và yêu cầu RFP, mốc cut over, chi phí cam kết bảo hành (loai_chi cam_ket), để tổng kết không cảnh báo K01, K06, K15.

## Ghi nhật ký

mo_phong_sprint.py tự ghi nhật ký bước script (mo_phong.S<n>.sinh, mo_phong.kiem_tra). Agent Mô phỏng ghi bước viết kịch bản bằng `qlda-loi/scripts/nhat_ky.py` (lệnh trong prompt).
