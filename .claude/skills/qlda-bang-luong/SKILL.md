---
name: qlda-bang-luong
description: Lập bảng phân chia lương của nhóm theo cách trả lương nhóm khai báo (theo ngày huy động, theo công sức thực tế hoặc kết hợp) - ngày huy động cùng nguồn với cost estimate, MD thực tế trong nhật ký công việc, đơn giá ngày của vai trò, bảo hiểm phần doanh nghiệp, tỷ trọng đóng góp theo MD thực tế, ngày sẵn sàng không ghi công, theo sprint, đối chiếu MD kế hoạch, khoản A và chi phí lương kế hoạch của cost estimate cùng cách trả lương, Excel có công thức SUMIFS, INDEX/MATCH và cột ký xác nhận. Dùng khi người dùng muốn chia lương, tính thù lao, bảng lương theo đóng góp của thành viên.
---

# Bảng phân chia lương

Cách trả lương là quyết định của nhóm, khai báo trong dau_vao/don_gia.json khóa cach_tra_luong. Cost estimate, báo cáo tiến độ, tổng kết dùng cùng khóa này (qlda-bao-cao-tien-do/scripts/thuc_te.py). Chưa khai báo thì script dừng (L09) và đề nghị nhóm chọn:

| cach_tra_luong | Lương | Ghi chú |
|---|---|---|
| huy_dong | Ngày huy động x đơn giá ngày | Cùng cách tính với cost estimate (đối chiếu lương theo người) |
| cong_suc | MD thực tế trong nhật ký x đơn giá ngày | Kế hoạch là MD công việc giao. Ngày sẵn sàng không ghi công không được trả, chỉ là năng lực |
| ket_hop | Ngày huy động x đơn giá ngày, cộng phần chia theo đóng góp | Cần quy_chia_theo_dong_gop {so_tien, can_cu} do nhóm quyết định, thiếu thì dừng (L10). Phần chia = so_tien x tỷ trọng đóng góp, không nhân hệ số bảo hiểm, lấy từ khoản C nên không tính vào chi phí lương kế hoạch |

Đơn giá ngày = lương tham chiếu tháng của vai trò / số ngày làm việc mỗi tháng. Chi phí doanh nghiệp = lương x hệ số bảo hiểm. Ngày huy động theo lich.json phan_bo[].quy (kế hoạch huy động của master schedule), tính đến ngày --den. Tỷ trọng đóng góp = MD thực tế của thành viên / tổng MD thực tế, áp dụng cho mọi cách trả lương. Ngày sẵn sàng không ghi công = ngày huy động - MD thực tế, là cột riêng để đối chiếu, không dùng để trừ lương. luong.json doi_chieu.chi_phi_ke_hoach và chenh_chi_phi tính cùng cách trả lương (ngày huy động hoặc MD công việc kế hoạch, cắt đến --den), chi_phi_theo_md_ke_hoach để tham khảo.

Kỳ KT: lịch có giai đoạn Kết thúc (lich.json giai_doan mã ket_thuc, ngay_dong_du_an) thì ngày làm việc tính đến ngày đóng dự án, kỳ KT là một cột như sprint (sheet Sprint, Theo_sprint, luong.json theo_sprint), nhật ký sau cut over không bị L03. Lương kỳ KT theo cách trả lương: cong_suc trả theo MD nhật ký, huy_dong và ket_hop theo quỹ kỳ KT trong phan_bo (lịch ghi 0 khi nhóm chưa quyết định huy động sau cut over, cảnh báo L28 của master schedule).

Số liệu mô phỏng: có du_lieu/mo_phong.json (dữ liệu do qlda-mo-phong sinh) thì sheet Thuyet_minh thêm mục căn cứ số liệu thực tế là số liệu mô phỏng kèm ghi chú của tệp, luong.json ghi so_lieu_mo_phong và can_cu_mo_phong.

Đầu vào: dau_vao/thuc_te/nhat_ky_cong_viec.csv (cách ghi ở qlda-bao-cao-tien-do/references/nhap_lieu.md), dau_vao/thanh_vien.json, don_gia.json, du_lieu/lich.json (sprint, MD kế hoạch và MD huy động theo người), du_lieu/chi_phi.json (khoản A, tong_chi_phi_nguoi), dau_vao/du_an.json.

## Quy trình

1. `python .claude/skills/qlda-bang-luong/scripts/chia_luong.py [--den yyyy-mm-dd]`
   - Kiểm tra tham số và nhật ký. Lỗi chặn: chưa khai báo cách trả lương (L09, L10), thành viên lạ, vai trò chưa có đơn giá, vượt tỷ lệ tham gia trong ngày, MD không hợp lệ. Cảnh báo: ghi công ngày nghỉ, ngoài lịch, ngoài thời gian huy động, chi phí lương kế hoạch lệch cost estimate hoặc cost estimate lập theo cách trả lương khác (L08).
   - Lập ket_qua/14_Bang_phan_chia_luong/Bang_phan_chia_luong.xlsx gồm các sheet Thuyet_minh, Bang_luong, Theo_sprint, Doi_chieu, Tham_so (có cách trả lương, quỹ chia), Sprint, Nhat_ky, Huy_dong.
   - Công thức được tính lại và đối chiếu với tính toán Python (MD thực tế, MD huy động, lương, thu nhập từng người, tổng theo sprint).
2. Trưởng nhóm rà soát chênh lệch MD so với kế hoạch (ô tô màu khi lệch quá 10%) và ngày sẵn sàng, các thành viên ký xác nhận ở cột cuối.
3. Có thay đổi nhật ký hoặc huy động thì chạy lại bước 1. Phiên bản chỉ tăng khi số liệu đổi.

Đầu ra: du_lieu/luong.json, Bang_phan_chia_luong.xlsx. Không có văn bản Word riêng, phần thuyết minh nằm trong sheet Thuyet_minh.
