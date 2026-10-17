# Thư mục và tệp dữ liệu

| Thư mục | Nội dung | Ai ghi |
|---|---|---|
| dau_vao/ | RFP.pdf, Mau_5A.docx, tham_so_chu_dau_tu.json, du_an.json, thanh_vien.json, don_gia.json, nha_thau.json, kpi.json | Nhóm |
| dau_vao/thuc_te/ | nhat_ky_cong_viec.csv, hoan_thanh.csv, moc_thuc_te.csv, theo_doi_rui_ro.csv, nghiem_thu.csv, loi.csv, chi_phi_thuc_te.csv, retro.md | Nhóm, trong quá trình thực hiện |
| du_lieu/ | Dữ liệu chuẩn do script tạo, mọi tài liệu đọc từ đây. Không sửa tay | Script |
| lam_viec/<buoc>/ | Tệp nhập của agent (…_nhap.json), khung, bản soạn, bản Word từng vòng, báo cáo kiểm tra | Agent, script |
| ket_qua/ | Tài liệu nộp, đánh số theo thứ tự 01 đến 16 | Script |
| bang_chung/ | nhat_ky_chay.jsonl, prompts/ (bản sao prompt theo băm), kiem_tra/ (báo cáo lớp B) | Script, agent |

Sơ đồ phụ thuộc giữa các bước: references/so_do_phu_thuoc.json. Mỗi bước khai báo đầu vào (vao) và đầu ra (ra). Sổ phiên bản du_lieu/phien_ban.json lưu băm đầu vào của từng phiên bản, nhờ đó chay.py biết tài liệu nào đã cũ.

Định dạng tham chiếu dữ liệu trong bản soạn: {bi_danh#duong_dan|dinh_dang}
- bi_danh: khóa trong nguon của đặc tả, ví dụ cp cho du_lieu/chi_phi.json.
- duong_dan: a.b.c, phần tử danh sách a[0], lọc a[ma=RR01].ten.
- dinh_dang: tien (1.750.000.000), trieu (1.750,00), md (12,50), pt (41,4%), ngay (01/07/2027), so, so1, so2, so3, nguyen, chu (bằng chữ).
