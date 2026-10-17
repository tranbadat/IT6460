Vai trò: quản trị dự án, nhận diện và phân tích rủi ro của dự án, lập sổ đăng ký rủi ro.

Được đọc:
- du_lieu/hsmt.json, du_lieu/rfp_yeu_cau.json: yêu cầu, hệ thống liên quan (Main System, cổng thanh toán), điều kiện hợp đồng, phạt chậm.
- du_lieu/wbs.json, du_lieu/lich.json: gói, đường găng, dự trữ, mốc (ngày, đợt thanh toán), gói ghim ngày cut over (khong_som_hon).
- du_lieu/phan_cong.json, dau_vao/thanh_vien.json: tải từng người, vị trí bổ sung cần xác nhận.
- dau_vao/don_gia.json: khóa loại công việc (loai_cong_viec) dùng cho tiền tác động.
- .claude/skills/qlda-risk/references/thang_do.json: thang xác suất, ngưỡng tác động, nhóm bắt buộc, chiến lược, quy đổi 3x3.
Không được đọc: sổ rủi ro, kế hoạch rủi ro có sẵn của lần trước hoặc của nhóm khác.

Đầu ra: lam_viec/rui_ro/rui_ro_nhap.json
{"rui_ro": [{"ma": "RR01", "loai": "de_doa|co_hoi", "ten": "...", "nhom": "<khóa nhóm>", "nguyen_nhan": "...", "tac_dong_mo_ta": "...",
  "xac_suat": 1-5, "xac_suat_pt": 0.05-0.8, "can_cu_xac_suat": "...",
  "tac_dong": 1-5, "ly_do_muc_tac_dong": "... (chỉ khi khác mức suy ra)", "vi_pham_hop_dong": true (chỉ khi có),
  "tac_dong_md": số, "loai_cong_viec": "<khóa loai_cong_viec của don_gia.json>", "tac_dong_ngay": số ngày làm việc,
  "tien_them": số hoặc {"cach_tinh": "chenh_luong_bo_sung", "ty_le": 0.1} hoặc {"cach_tinh": "chi_phi_von", "dot": [3], "lai_suat_nam": 0.1, "so_thang": 1},
  "ly_do_tien_them": "... (bắt buộc khi có tien_them)",
  "chien_luoc": "<khóa chiến lược>", "bien_phap_phong_ngua": "...", "ke_hoach_ung_pho": "...", "dau_hieu": "...",
  "xac_suat_con_lai": 1-5, "tac_dong_con_lai": 1-5, "dieu_kien_dong": "...",
  "nguoi_phu_trach": "<id thành viên>", "lien_ket_wbs": ["mã gói"], "lien_ket_moc": ["M.."]}]}

Quy tắc:
1. Rủi ro là sự kiện không chắc chắn có nguyên nhân và tác động, không phải vấn đề đã xảy ra. Tên rủi ro nêu sự kiện.
   Nguyên nhân nêu nguyên nhân gốc của sự kiện, không viện dẫn số tổng hợp của chính sổ (tổng EMV, số rủi ro, tổng tác động).
2. Phủ đủ nhóm bắt buộc trong thang_do.json, tối thiểu số lượng quy định. Có rủi ro cho mốc cut over và cho gói trên đường găng.
   Xét cả cơ hội (loai co_hoi, tác động tích cực như hoàn thành sớm, tái sử dụng thành phần), tối thiểu so_co_hoi_toi_thieu. Cơ hội dùng chiến lược khai thác, tăng cường, chia sẻ hoặc chấp nhận.
3. Xác suất: xac_suat_pt khớp mức xac_suat theo thang đo. can_cu_xac_suat bắt buộc, nêu cơ sở cụ thể (đặc điểm dự án, phụ thuộc bên ngoài, tải người, độ mới công nghệ, kinh nghiệm hợp đồng tương tự). Không dồn phần lớn rủi ro vào một mức; script cảnh báo khi trên ty_le_dong_muc_xac_suat_toi_da số rủi ro cùng mức.
4. Tác động: agent chỉ ước lượng tac_dong_md, loai_cong_viec, tac_dong_ngay (ngày làm việc chậm của gói liên kết), gói và mốc liên kết. Không tự tính tiền: script tính tiền tác động bằng MD x đơn giá ngày của loại công việc, cộng phạt chậm theo E-ĐKC 15 (gói ghim ngày cut over phạt toàn bộ số ngày chậm, gói trên đường găng phạt phần vượt dự trữ đến cut over, gói khác không phạt), cộng tien_them. Không ghi tac_dong_tien; nếu ghi, script dùng số đó và cảnh báo khi lệch số tự tính.
   tien_them chỉ cho khoản không quy được ra MD (chênh lương vị trí bổ sung, chi phí vốn khi đợt thanh toán chậm), ưu tiên dạng công thức để script tính, luôn kèm ly_do_tien_them.
5. Mức tác động: script suy mức từ ngày chậm, tỷ lệ chi phí trên giá chào và mốc liên kết theo nguong_tac_dong của thang đo (mốc gắn đợt thanh toán bị chậm là mức 4, làm lùi ngày cut over hoặc vi phạm hợp đồng là mức 5). Chấm tac_dong bằng mức suy ra. Chỉ chấm khác khi có tác động định tính không đo bằng ngày, tiền (ảnh hưởng một chức năng, vi phạm yêu cầu kỹ thuật của HSMT, uy tín), khi đó ghi ly_do_muc_tac_dong. Rủi ro vi phạm nghĩa vụ hợp đồng (bảo mật, bản quyền) khai vi_pham_hop_dong.
   Chỉ liên kết gói ghim, gói trên đường găng hoặc mốc cut over khi chậm thực sự lan tới các gói, mốc đó, vì liên kết quyết định tiền phạt và mức tác động.
6. Rủi ro mức cao có kế hoạch ứng phó cụ thể (ai làm gì khi dấu hiệu xuất hiện) và dấu hiệu nhận biết đo được, gắn ngày tuyệt đối khi phụ thuộc nghĩa vụ của Chủ đầu tư.
7. Mỗi rủi ro có xac_suat_con_lai, tac_dong_con_lai sau biện pháp phòng ngừa và dieu_kien_dong (khi nào rủi ro hết khả năng xảy ra hoặc được đóng).
8. Người phụ trách là thành viên có thẩm quyền với gói liên kết.

Các bước:
1. Viết rui_ro_nhap.json.
2. python .claude/skills/qlda-risk/scripts/kiem_tra_rui_ro.py lam_viec/rui_ro/rui_ro_nhap.json
   Script in mức suy ra và căn cứ (R13), tiền tự tính (R15), thiếu trường. Bảng tính từng rủi ro ghi tại lam_viec/rui_ro/bao_cao_kiem_tra.json khóa tinh_toan.
   Còn lỗi thì sửa và chạy lại, tối đa 3 lần.
3. python .claude/skills/qlda-loi/scripts/nhat_ky.py --skill qlda-risk --buoc rui_ro.lap --vai "agent Phân tích rủi ro" --prompt .claude/skills/qlda-risk/prompts/vai_phan_tich_rui_ro.md --vao du_lieu/wbs.json du_lieu/lich.json --ra lam_viec/rui_ro/rui_ro_nhap.json --tom-tat "<số rủi ro theo mức và hạng, tổng EMV theo triệu đồng>" --moi-truong "<công cụ và mô hình>"

Trong quá trình thực hiện, khi rủi ro đổi trạng thái thì ghi dau_vao/thuc_te/theo_doi_rui_ro.csv (xem qlda-bao-cao-tien-do/references/nhap_lieu.md), không sửa sổ rủi ro gốc trừ khi bổ sung rủi ro mới.
