---
name: qlda-bao-cao-tien-do
description: Lập báo cáo tiến độ theo kỳ (cuối sprint hoặc ngày bất kỳ) bằng phương pháp giá trị thu được - PV, EV, AC theo MD và tiền, SPI, CPI, EAC, ETC, VAC, TCPI, dự báo ngày hoàn thành so với cut over, gói chậm, mốc, công sức từng thành viên, rủi ro, yêu cầu thay đổi, vấn đề và hành động, kế hoạch kỳ tới. Dùng khi người dùng muốn báo cáo tiến độ, tình hình dự án, EVM, SPI, CPI cho một sprint.
---

# Báo cáo tiến độ

Đầu vào kế hoạch: du_lieu/lich.json, wbs.json, phan_cong.json, chi_phi.json, dau_vao/don_gia.json, thanh_vien.json, du_an.json (ngưỡng cảnh báo). Đầu vào thực tế do nhóm ghi trong dau_vao/thuc_te/, cách ghi ở `references/nhap_lieu.md`: nhat_ky_cong_viec.csv, hoan_thanh.csv, moc_thuc_te.csv, theo_doi_rui_ro.csv. Sổ rủi ro và sổ thay đổi nếu có.

## Quy trình mỗi kỳ

1. `python .claude/skills/qlda-bao-cao-tien-do/scripts/tinh_tien_do.py --ky S3` (hoặc `--ky yyyy-mm-dd`)
   Kiểm tra dữ liệu thực tế (thành viên, mã gói, ngày, không vượt tỷ lệ tham gia trong ngày, tỷ lệ hoàn thành không giảm, mã rủi ro). Tính EVM, trạng thái xanh, vàng, đỏ theo ngưỡng, dự báo hoàn thành (vượt cut over thì tối thiểu vàng). Ra du_lieu/tien_do/<ky>.json, hien_tai.json, lich_su.json.
2. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi bao_cao_tien_do`
3. Agent Soạn thảo viết bản soạn: tóm tắt, kết quả trong kỳ, bảng vấn đề (mỗi vấn đề có hành động gắn mã rủi ro hoặc CR, người, hạn), kế hoạch kỳ tới ưu tiên đường găng.
4. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien bao_cao_tien_do --ghi-chu "Kỳ S3"`
5. Agent Kiểm tra lớp B với `dac_ta/bao_cao_tien_do.json`.

Đầu ra: ket_qua/09_Bao_cao_tien_do/Bao_cao_tien_do_<ky>.docx, mỗi kỳ một tệp. Lịch sử SPI, CPI các kỳ nằm trong báo cáo và được báo cáo tổng kết dùng lại.

Khi SPI hoặc CPI dưới ngưỡng: nêu nguyên nhân theo gói, kích hoạt kế hoạch ứng phó rủi ro tương ứng (ghi theo_doi_rui_ro.csv), hoặc lập yêu cầu thay đổi (skill qlda-change) nếu cần điều chỉnh phạm vi, mốc.
