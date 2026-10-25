---
name: qlda-bao-cao-tien-do
description: Lập báo cáo tiến độ theo kỳ (cuối sprint hoặc ngày bất kỳ) bằng phương pháp giá trị thu được - PV, EV, AC theo MD và tiền, SPI, CPI theo công và CPI theo chi phí thực (lương theo cách trả lương nhóm khai báo cộng chi phí khác), tỷ lệ sử dụng quỹ huy động, EAC, ETC, VAC, TCPI, dự báo ngày hoàn thành so với cut over, gói chậm, mốc so với hạn, công sức và ngày huy động từng thành viên, rủi ro, yêu cầu thay đổi, sổ vấn đề và hành động, kế hoạch kỳ tới. Dùng khi người dùng muốn báo cáo tiến độ, tình hình dự án, EVM, SPI, CPI, vấn đề cho một sprint.
---

# Báo cáo tiến độ

Đầu vào kế hoạch: du_lieu/lich.json (gồm huy động theo người, sprint), wbs.json, chi_phi.json, dau_vao/don_gia.json, thanh_vien.json, du_an.json (ngưỡng cảnh báo). Đầu vào thực tế do nhóm ghi trong dau_vao/thuc_te/, cách ghi ở `references/nhap_lieu.md`: nhat_ky_cong_viec.csv, hoan_thanh.csv, moc_thuc_te.csv, theo_doi_rui_ro.csv, chi_phi_thuc_te.csv, so_van_de.csv, hanh_dong.csv. Sổ rủi ro và sổ thay đổi nếu có.

## Chỉ số chi phí

- CPI theo công: EV chia AC theo công (MD nhật ký nhân đơn giá loại công việc). Đo năng suất trên phần việc đã giao.
- CPI theo chi phí thực: EV nhân sự chia AC nhân sự, cùng cơ sở lương với cost estimate theo don_gia.json cach_tra_luong. AC nhân sự là lương đến ngày báo cáo (cong_suc: MD nhật ký, huy_dong và ket_hop: ngày huy động theo lich.json phan_bo[].quy, nhân lương ngày vai trò và hệ số bảo hiểm). EV nhân sự là lương kế hoạch lũy kế tại thời điểm kế hoạch đạt khối lượng bằng EV, nên đúng kế hoạch thì CPI thực bằng 1 với cả hai cách trả lương. Chi phí khác (khoản B) chưa có kế hoạch chi theo thời gian nên so với dự toán B + D, không tính vào CPI thực. EAC thực = AC nhân sự + (BAC nhân sự - EV nhân sự) + chi phí khác đã chi và còn lại theo dự toán. Chênh lệch giữa khoản A và lương kế hoạch thuộc cost estimate, không vào trạng thái. Thiếu cach_tra_luong thì dừng (T30), cost estimate lập theo cách khác thì cảnh báo (T28).
- Tỷ lệ sử dụng quỹ huy động: MD ghi công chia MD huy động đến ngày báo cáo. Phần còn lại là MD sẵn sàng không ghi công, có cả theo từng thành viên. Khi trả theo công sức, đây là chỉ số năng lực, không phải chi phí.
- Trạng thái chung lấy mức xấu nhất của SPI, CPI theo công, CPI theo chi phí thực. Dự báo vượt cut over thì tối thiểu vàng.
- SPI, CPI, CPI thực, TCPI lưu 4 chữ số thập phân (SO_LE_CHI_SO) trong tien_do/<ky>.json, hien_tai.json, lich_su.json, chỉ làm tròn khi hiển thị (so2), tránh làm tròn hai lần (0,9349 thành 0,935 rồi 0,94).
- Bảng yêu cầu thay đổi ghi trạng thái tại ngày báo cáo theo lịch sử của CR (lập lại báo cáo sau quyết định vẫn ra Chờ phê duyệt), MD tăng, giá đề nghị, số ngày cut over phải lùi (ngay_cham_cut_over), cut over mới đề xuất, mức. Lập lại số liệu một kỳ cũ sau khi kế hoạch đã đổi (lịch lập lại sau CR) thì đặt QLDA_KE_HOACH_KY=S<k> (từ qlda-loi 1.6.3): lịch, WBS, dự toán, sổ rủi ro (mức rủi ro tại kỳ đó), phân công, dự án, đơn giá, thành viên được đọc từ bản chụp lam_viec/mo_phong/ke_hoach_S<k>/ do mo_phong_sprint.py lưu khi sinh kỳ, cho cả tinh_tien_do.py, chay.py chuan_bi và hoan_thien; không chạy trên kế hoạch hiện hành. Từ 1.5.1: SPI, CPI hiển thị ba chữ số khi làm tròn hai chữ số chạm ngưỡng (spi_hien_thi, cpi_hien_thi, cpi_thuc_hien_thi), bảng công sức có ghi chú cơ sở tính kế hoạch theo thành viên. Từ 1.5.2: bảng lịch sử các kỳ lấy td#lich_su_den_ky (chỉ các kỳ có ngày báo cáo không muộn hơn kỳ đang lập, chỉ số theo cùng quy tắc hiển thị); tỷ lệ dùng định dạng pt1 (luôn một chữ số thập phân), MD dùng md2 (luôn hai chữ số) để các kỳ cùng định dạng, bản soạn cũng dùng |pt1, |md2.

## Vấn đề và hành động

Sổ vấn đề (so_van_de.csv) và hành động (hanh_dong.csv) mở từ M0. Script kiểm tra mã trùng, trường bắt buộc, liên kết mã rủi ro và mã yêu cầu thay đổi, hành động trỏ tới vấn đề có trong sổ, điều kiện đóng (mọi hành động hoàn thành trước ngày đóng, có người đóng, kết quả), quá hạn so với ngày báo cáo (T13 đến T25, xem scripts/so_van_de.py). Bảng vấn đề, hành động của báo cáo lấy từ sổ tại ngày báo cáo (vấn đề chưa đóng và vấn đề đóng trong kỳ). Script vẫn sinh tín hiệu tự động từ gói chậm, chỉ số dưới ngưỡng, rủi ro đã xảy ra, mốc quá hạn, ghi nguồn và vấn đề tương ứng trong sổ, tín hiệu chưa ghi sổ được cảnh báo (T25). Sổ rỗng thì báo cáo ghi không có vấn đề mở.

## Kỳ KT và số liệu mô phỏng

- Lịch có giai đoạn Kết thúc (lich.json giai_doan mã ket_thuc, ngay_dong_du_an) thì ngày làm việc của dự án tính đến ngày đóng dự án (thuc_te.ngay_lam_viec_du_an), các kỳ gồm sprint và kỳ KT (thuc_te.cac_ky). Nhật ký sau cut over không bị T04, T05, PV gồm gói Kết thúc, MD kế hoạch theo người gồm phan_bo kỳ KT.
- `--ky KT`: ngày báo cáo là ngày đóng dự án, từ ngày là ngày đầu giai đoạn Kết thúc. Lịch chưa có giai đoạn này thì dừng.
- Dự báo hoàn thành chỉ xét gói phải xong trước cut over. Ngày báo cáo sau ngày kết thúc kế hoạch (kỳ KT): gói đã xong thì lấy ngày xong thực tế của gói cuối, chưa xong thì MD còn lại chia nhịp EV bình quân mỗi ngày đã qua. EV bằng toàn bộ khối lượng thì EV nhân sự bằng BAC nhân sự.
- Có du_lieu/mo_phong.json (dữ liệu do qlda-mo-phong sinh) thì đầu ra ghi so_lieu_mo_phong và can_cu_mo_phong. Đặc tả khai báo bí danh nguồn tùy chọn mo_phong, khối doan_ds td#can_cu_mo_phong in câu "Số liệu thực tế trong báo cáo là số liệu mô phỏng" kèm {mo_phong#_ghi_chu}. Không có tệp thì không in gì.

## Quy trình mỗi kỳ

1. `python .claude/skills/qlda-bao-cao-tien-do/scripts/tinh_tien_do.py --ky S3` (hoặc `--ky KT`, `--ky yyyy-mm-dd [--ma KT]`)
   Kiểm tra dữ liệu thực tế (thành viên, mã gói, ngày, không vượt tỷ lệ tham gia trong ngày, tỷ lệ hoàn thành không giảm, mã rủi ro, định dạng mốc và chi phí khác, sổ vấn đề). Tính EVM theo công và theo chi phí thực, trạng thái xanh, vàng, đỏ theo ngưỡng, dự báo hoàn thành, mốc so với hạn (mốc cut over so với ngày cut over hợp đồng). Mọi dữ liệu thực tế chỉ tính đến ngày báo cáo. Ra du_lieu/tien_do/<ky>.json, hien_tai.json, lich_su.json.
2. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi bao_cao_tien_do`
   chuan_bi đọc du_lieu/tien_do/hien_tai.json, tức kỳ tính gần nhất. Lập lại báo cáo một kỳ cũ thì chạy lại bước 1 với đúng mã kỳ đó trước.
3. Agent Soạn thảo viết bản soạn: tóm tắt (nêu cả CPI theo chi phí thực và MD sẵn sàng), kết quả trong kỳ, nhận xét vấn đề dựa trên bảng sổ vấn đề (không lập lại bảng, không thêm vấn đề ngoài sổ), kế hoạch kỳ tới ưu tiên đường găng và hành động đến hạn.
4. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien bao_cao_tien_do --ghi-chu "Kỳ S3"`
5. Agent Kiểm tra lớp B với `dac_ta/bao_cao_tien_do.json`.

Đầu ra: ket_qua/09_Bao_cao_tien_do/Bao_cao_tien_do_<ky>.docx, mỗi kỳ một tệp. Lịch sử SPI, CPI, CPI thực các kỳ nằm trong báo cáo và được báo cáo tổng kết dùng lại.

Khi SPI hoặc CPI dưới ngưỡng: nêu nguyên nhân theo gói, ghi vấn đề vào sổ, kích hoạt kế hoạch ứng phó rủi ro tương ứng (ghi theo_doi_rui_ro.csv), hoặc lập yêu cầu thay đổi (skill qlda-change) nếu cần điều chỉnh phạm vi, mốc, huy động.

Thư viện dùng chung: scripts/thuc_te.py (ngày làm việc gồm kỳ KT, ngày huy động, chi phí lương theo huy động, chi phí khác thực tế, kiểm tra ô CSV, căn cứ số liệu mô phỏng) được qlda-tong-ket và qlda-bang-luong dùng lại.
