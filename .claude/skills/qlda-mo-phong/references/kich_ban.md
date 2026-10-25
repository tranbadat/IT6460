# Định dạng kịch bản biến cố một sprint

Tệp lam_viec/mo_phong/kich_ban_S<n>.json (kỳ giai đoạn Kết thúc sau cut over là kich_ban_KT.json). Agent Mô phỏng viết theo `prompts/vai_mo_phong.md`, script `scripts/mo_phong_sprint.py` kiểm tra (KB01 đến KB15) rồi sinh số liệu. Ví dụ: `references/vi_du/kich_ban_S1.json`, `kich_ban_S2.json`.

```json
{"sprint": "S2", "tom_tat": "một hai câu về diễn biến sprint", "nhieu_md": 0.03, "bien_co": [ ... ]}
```

- `nhieu_md` không bắt buộc, chỉ có hiệu lực ở sprint đầu (lưu trong du_lieu/mo_phong.json). Mặc định theo `references/cau_hinh.json`.
- Mọi biến cố có `loai` và `ly_do`. Ngày dạng yyyy-mm-dd, ngày phát sinh phải nằm trong sprint và là ngày làm việc (chi phí, mốc, yêu cầu thay đổi chỉ cần trong sprint).
- Mọi biến cố liên kết tới gói, rủi ro, vấn đề hoặc yêu cầu thay đổi: qua `ma_goi`, `ma_rui_ro`, `ma_van_de`, `ma_cr` hoặc `lien_ket` (danh sách mã RRxx, VDxx, CRxx, Mx, Sx, Lxx, NTxx, mã gói WBS).

Công thực tế không ghi trong kịch bản. Script tự phân công theo ngày từ lịch hiện hành, biến cố chỉ thay đổi công cần, ngày bắt đầu và quỹ ngày của người.

## Các loại biến cố

| loai | Trường | Tác động khi sinh |
|---|---|---|
| goi | ma_goi, ty_le_md (vượt dương, hụt âm, ví dụ 0.2 hoặc -0.1), so_ngay_tre (ngày làm việc), ly_do | Công cần của gói nhân (1 + ty_le_md), từ sprint này về sau. so_ngay_tre lùi cửa sổ làm của gói. Gói phải đã đến lịch (bắt đầu kế hoạch không sau ngày cuối sprint) và chưa hoàn thành |
| nghi | thanh_vien (id), so_ngay, tu_ngay (không bắt buộc, trống thì chọn ngẫu nhiên theo hạt giống), lien_ket, ly_do | Người đó không ghi công các ngày nghỉ, việc dồn sang ngày sau |
| huy_dong | thanh_vien (id), so_md, lien_ket, ly_do | Huy động bổ sung thực tế theo nhu cầu (từ 1.0.5): cộng so_md vào quỹ của thành viên trong sprint (kể cả thành viên có quỹ kế hoạch 0), không vượt số ngày làm việc của sprint nhân ty_le trừ quỹ kế hoạch (KB01). Không ghi CSV, lưu trong kịch bản của du_lieu/mo_phong.json. Dùng khi gói chậm dồn vào sprint có quỹ sát nhu cầu; lương theo công sức chỉ tính MD thực làm |
| rui_ro | ma_rui_ro, ngay, trang_thai (mặc định Đã xảy ra), hanh_dong (bắt buộc khi Đã xảy ra), md_tac_dong, ngay_tac_dong, chi_phi_tac_dong, ma_goi, ngay_kich_hoat, hanh_dong_kich_hoat, ngay_dong, ma_cr, ten (rủi ro ngoài sổ), ly_do | Ghi theo_doi_rui_ro.csv: dòng Đã kích hoạt ứng phó (khi có ngay_kich_hoat), dòng trạng thái, dòng Đã đóng (ngày ngay_dong, sprint sau thì hẹn). md_tac_dong cộng vào công cần của ma_goi (trống thì gói lá đầu tiên trong lien_ket_wbs của rủi ro còn đang làm), ngay_tac_dong lùi cửa sổ gói. chi_phi_tac_dong trống thì script tính md_tac_dong x đơn giá loại công việc của rủi ro |
| loi | ma_goi, so_loi {"Nghiêm trọng": 0, "Cao": 1, "Trung bình": 2, "Thấp": 1}, ngay_phat_hien (không bắt buộc), ngay_sua {mức: số ngày làm việc}, con_mo {mức: số lỗi để mở}, md_sua, mo_ta, ly_do | Ghi loi.csv mã L01 trở đi. Ngày đóng = ngày phát hiện + ngày sửa (mặc định theo cau_hinh.json), sau sprint thì hẹn đóng ở sprint chứa ngày đó. md_sua cộng vào công cần của gói (gói còn đang làm) |
| van_de | ma (VDxx, nên ghi để liên kết), ngay_ghi_nhan, nguoi_bao, mo_ta (nêu mã gói, mốc liên quan), phan_loai, uu_tien, nguoi_phu_trach, han, ma_rui_ro, ma_cr, hanh_dong [{ma, viec, nguoi, han, ngay_xong, bang_chung}], ngay_dong, ket_qua, nguoi_dong, trang_thai (Chuyển cấp), ly_do | Ghi so_van_de.csv và hanh_dong.csv. Hành động xong khi đến ngay_xong, vấn đề đóng khi đến ngay_dong (hẹn sang sprint sau nếu cần). ma đã có trong sổ thì cập nhật dòng cũ (hạn, hành động mới, đóng) |
| chi_phi | ngay, khoan_muc (mã hoặc tên trong don_gia.json chi_phi_khac), so_tien, ghi_chu, loai_chi (da_chi, cam_ket), lien_ket, ly_do | Ghi chi_phi_thuc_te.csv |
| nghiem_thu | ma (NTxx, trống thì tự cấp), tieu_chi (bắt đầu bằng mã yêu cầu RFP), hang_muc (stt Mẫu 01A), ket_qua (Đạt, Không đạt), ngay, nguoi_xac_nhan, ghi_chu, ly_do | Ghi nghiem_thu.csv. Nghiệm thu lại: cùng ma, ngày mới |
| moc | ma_moc, ngay_dat, ghi_chu (biên bản), ly_do | Ghi moc_thuc_te.csv khi mọi gói căn cứ của mốc đã hoàn thành đến ngày đạt, không thì báo KB07 kèm ngày sớm nhất. Mốc cut over sau ngày cut over cần CR đã phê duyệt có phụ lục (KB13) |
| retro | y [{loai: tốt, cần cải thiện, hành động; noi_dung; lien_ket}], ly_do | Thêm mục "## S<n>" vào retro.md, mã R-S<n>-01 trở đi |
| cr | ma_cr (mã danh_gia sẽ cấp), ngay, tieu_de, mo_ta, nguon, nguoi_de_xuat, goi_moi [{ten, md, loai, cha}], goi_thay_doi [{ma, md_tang}], ma_rui_ro, nhan_dinh_ban_dau, ly_do | Ghi lam_viec/mo_phong/cr_S<n>_<ma>.json làm đầu vào cho agent Đánh giá thay đổi. Gói mới chỉ được mô phỏng sau khi CR được phê duyệt, áp dụng và lịch được lập lại |

## Việc hẹn

Lỗi đóng, hành động xong, vấn đề đóng, rủi ro đóng có ngày sau sprint hiện tại được lưu trong du_lieu/mo_phong.json khóa cho_xu_ly. Sprint chứa ngày đó ghi vào CSV, nên mỗi báo cáo kỳ đọc đúng trạng thái tại kỳ đó.

## Tóm tắt sau khi sinh

lam_viec/mo_phong/ket_qua_S<n>.json: MD theo người so với quỹ, gói hoàn thành, gói chậm (cùng ngưỡng với tinh_tien_do.py), SPI ước tính, số dòng thêm, gợi ý (mốc đủ điều kiện chưa ghi, gói chậm chưa có vấn đề trong sổ). Agent đọc tệp này để chỉnh kịch bản rồi chạy `--lam-lai` khi cần.
