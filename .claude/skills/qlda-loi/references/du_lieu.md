# Thư mục và tệp dữ liệu

| Thư mục | Nội dung | Ai ghi |
|---|---|---|
| dau_vao/ | RFP.pdf, Mau_5A.docx, tham_so_chu_dau_tu.json, du_an.json, thanh_vien.json, don_gia.json, nha_thau.json, uoc_luong.json (căn cứ ước lượng), chi_tieu_ky_thuat.json (chỉ tiêu kỹ thuật của nhà thầu), kpi.json | Nhóm |
| dau_vao/thuc_te/ | nhat_ky_cong_viec.csv, hoan_thanh.csv, moc_thuc_te.csv, theo_doi_rui_ro.csv, nghiem_thu.csv, loi.csv, chi_phi_thuc_te.csv, so_van_de.csv, hanh_dong.csv (sổ vấn đề và hành động, mở từ M0), retro.md. Cột từng tệp: qlda-bao-cao-tien-do/references/nhap_lieu.md. Tệp chỉ có dòng tiêu đề được coi là chưa có dữ liệu | Nhóm, trong quá trình thực hiện |
| du_lieu/ | Dữ liệu chuẩn do script tạo, mọi tài liệu đọc từ đây. Không sửa tay | Script |
| lam_viec/<buoc>/ | Tệp nhập của agent (…_nhap.json), khung, bản soạn, bản Word từng vòng, báo cáo kiểm tra | Agent, script |
| ket_qua/ | Tài liệu nộp, đánh số theo thứ tự 01 đến 16 | Script |
| bang_chung/ | nhat_ky_chay.jsonl, prompts/ (bản sao prompt theo băm), kiem_tra/ (báo cáo lớp B) | Script, agent |

Sơ đồ phụ thuộc giữa các bước: references/so_do_phu_thuoc.json. Mỗi bước khai báo đầu vào (vao) và đầu ra (ra). Sổ phiên bản du_lieu/phien_ban.json lưu băm đầu vào của từng phiên bản, nhờ đó chay.py biết tài liệu nào đã cũ.

Giai đoạn dự án (loi.giai_doan_du_an, loi.phan_giai_doan): Khởi động (du_an.giai_doan.khoi_dong {tu, den}, mặc định SO_NGAY_KHOI_DONG_MAC_DINH = 5 ngày làm việc đầu), Thực hiện (các sprint đến cut over), Kết thúc (du_an.giai_doan.ket_thuc.so_ngay_lam_viec ngày làm việc sau cut over, mặc định SO_NGAY_KET_THUC_MAC_DINH = 10). Gói lá thuộc một trong khoi_dong, thuc_hien, xuyen_suot (gói quản lý dàn trải suốt dự án), ket_thuc, theo giai_doan của WBS hoặc suy từ nhóm WBS 1 và loại PM, QA. du_lieu/lich.json ghi giai_doan, giai_doan_hien_thi của mỗi gói, danh sách giai_doan, ngay_dong_du_an và kỳ KT (sau cut over) trong phan_bo, nhu_cau_theo_sprint.

Bản phát hành: du_lieu/phat_hanh.json (qlda-master-schedule/scripts/phat_hanh.py), mỗi sprint một bản R<n> {ma, sprint, ngay, loai, chinh_thuc, nguon thuc_te hoặc ke_hoach, goi, hang_muc_01a, yeu_cau_rfp, loi_da_sua, loi_con_mo, cr_dua_vao, ghi_chu}. loi.ban_phat_hanh_hien_hanh(ngày) trả mã bản hiện hành. Sau ký hợp đồng, loi.dang_ky_phien_ban ghi khóa phat_hanh vào phiên bản mới theo ngày tài liệu.

Ngày hiện hành: loi.ngay_hien_hanh() là biến môi trường QLDA_NGAY (yyyy-mm-dd) khi mô phỏng dự án, không có thì ngày máy. Dùng cho ngày tài liệu mặc định của chay.py hoan_thien, bản phát hành hiện hành, phat_hanh.py tat_ca.

Định dạng tham chiếu dữ liệu trong bản soạn: {bi_danh#duong_dan|dinh_dang}
- bi_danh: khóa trong nguon của đặc tả, ví dụ cp cho du_lieu/chi_phi.json.
- duong_dan:
  - a.b.c, phần tử danh sách a[0];
  - lọc a[ma=RR01].ten (phần tử đầu tiên khớp), a[?muc=cao] (mọi phần tử khớp, ra danh sách);
  - khóa có dấu chấm hoặc khoảng trắng: a['8.3.2'], a["E-ĐKC 17.4"] (trong JSON nên dùng nháy đơn);
  - a.ds.ma: lấy khóa ma ở mọi phần tử của danh sách ds.
- Giá trị là danh sách được in thành chuỗi phân cách bằng dấu phẩy, mỗi phần tử theo định dạng đã chọn (phần tử là đối tượng thì in mã hoặc tên).
  Ví dụ {lich#duong_gang} ra "1.1.1, 1.1.2, 2.1.2", {lich#ngay_nghi|ngay} ra các ngày dạng dd/mm/yyyy. Danh sách số có phần thập phân dễ lẫn với dấu phẩy phân cách, nên tham chiếu từng phần tử.
- dinh_dang: tien (1.750.000.000, số âm in "âm 296.981.818"), trieu (1.750,00), md (12,50), pt (41,4%), ngay (01/07/2027), so, so1, so2, so3, nguyen,
  chu (bằng chữ), dem (số phần tử của danh sách hoặc đối tượng, ví dụ {hsmt#mau_01a|dem}, {rr#danh_sach[?muc=cao]|dem}).

Nguồn của đặc tả (khóa nguon):
- Đường dẫn tương đối thư mục dự án, hoặc "skill:<skill>/references/<tệp>.json" cho tệp tham chiếu tĩnh của skill dùng chung giữa các đặc tả
  (ví dụ "skill:qlda-change/references/phan_loai.json" chứa quy tắc dùng dự phòng, in cùng một bảng ở thuyết minh dự toán, kế hoạch rủi ro, master plan).
- nguon_tuy_chon: [bí danh]. Thiếu tệp thì không dừng. Bảng bang, bang_san dùng bí danh đó được bỏ qua kèm cảnh báo. Đoạn văn tham chiếu bí danh thiếu vẫn báo lỗi.

Bảng trong đặc tả (lap_khung.py):
- dong_tong.tong: {"chỉ số cột": "bi_danh#duong_dan"} khai báo tổng gốc cho cột MD hoặc phần trăm, ví dụ {"2": "wbs#tong_md"}. Khi các dòng đã làm tròn
  cộng lệch tổng gốc trong phạm vi sai số làm tròn (ví dụ 351,01 so với 351), phần lệch được phân bổ lại bằng loi.lam_tron_tong trên các dòng đã làm tròn,
  dòng tổng in đúng tổng gốc. Lệch lớn hơn là sai dữ liệu, giữ nguyên và in cảnh báo.
- mau_so: "10A" đánh dấu bảng theo biểu mẫu Mẫu 5A. Script của skill (ví dụ tinh_hsdt.py) so tiêu đề cột với dau_vao/Mau_5A.docx.
- bia.kieu = "ho_so_thau": bìa hồ sơ gửi bên ngoài (HSDT), chỉ in dong_tren, tiêu đề, dong_phu và bảng bia.bang, không in môn học, nhóm, giảng viên.

Khóa kiểm tra lớp A trong đặc tả (kiem_tra, kiem_tra_tai_lieu.py), ngoài gia_tri, ma_phai_co, tu_khoa, cam:
- muc_bat_buoc: [{"tieu_de": "cụm từ trong tiêu đề", "toi_thieu": số khối nội dung, "de_xuat": ...}] hoặc chuỗi. Thiếu tiêu đề chứa cụm từ thì lỗi CT02,
  mục có ít khối nội dung (đoạn, bảng) hơn toi_thieu thì lỗi CT03. Dùng để kiểm đủ khối bắt buộc, ví dụ các kế hoạch con của master plan.
- bieu_mau: [{"mau_so": "10A", "tep": "dau_vao/Mau_5A.docx"}]. Tài liệu phải có bảng đúng tiêu đề cột của biểu mẫu, sai thì lỗi BM01.
- ngoac_cho_phep: ["[văn bản cố định của mẫu]"]. Ngoại lệ của CT00 cho ngoặc vuông chứa chữ thuộc văn bản cố định.
