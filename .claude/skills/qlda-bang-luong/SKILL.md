---
name: qlda-bang-luong
description: Lập bảng phân chia lương của nhóm theo công sức thực tế - lương mỗi thành viên bằng MD thực tế trong nhật ký công việc nhân đơn giá ngày của vai trò, bảo hiểm phần doanh nghiệp, tỷ trọng, theo sprint, đối chiếu MD kế hoạch và khoản A của cost estimate, Excel có công thức SUMIFS, INDEX/MATCH và cột ký xác nhận. Dùng khi người dùng muốn chia lương, tính thù lao, bảng lương theo đóng góp của thành viên.
---

# Bảng phân chia lương

Cách tính do nhóm chọn: lương = MD thực tế x đơn giá ngày vai trò. Đơn giá ngày = lương tham chiếu tháng của vai trò / số ngày làm việc mỗi tháng (dau_vao/don_gia.json). Chi phí doanh nghiệp = lương x hệ số bảo hiểm.

Đầu vào: dau_vao/thuc_te/nhat_ky_cong_viec.csv (cách ghi ở qlda-bao-cao-tien-do/references/nhap_lieu.md), dau_vao/thanh_vien.json, don_gia.json, du_lieu/lich.json (sprint, MD kế hoạch theo người), du_lieu/chi_phi.json (khoản A), dau_vao/du_an.json.

## Quy trình

1. `python .claude/skills/qlda-bang-luong/scripts/chia_luong.py [--den yyyy-mm-dd]`
   - Kiểm tra nhật ký. Lỗi chặn: thành viên lạ, vai trò chưa có đơn giá, vượt tỷ lệ tham gia trong ngày, MD không hợp lệ. Cảnh báo: ghi công ngày nghỉ, ngoài lịch, ngoài thời gian huy động.
   - Lập ket_qua/14_Bang_phan_chia_luong/Bang_phan_chia_luong.xlsx gồm các sheet Thuyet_minh, Bang_luong, Theo_sprint, Doi_chieu, Tham_so, Sprint, Nhat_ky.
   - Công thức được tính lại và đối chiếu với tính toán Python (MD, lương từng người, tổng theo sprint).
2. Trưởng nhóm rà soát chênh lệch MD so với kế hoạch (ô tô màu khi lệch quá 10%), các thành viên ký xác nhận ở cột cuối.
3. Có thay đổi nhật ký thì chạy lại bước 1. Phiên bản chỉ tăng khi số liệu đổi.

Đầu ra: du_lieu/luong.json, Bang_phan_chia_luong.xlsx. Không có văn bản Word riêng, phần thuyết minh nằm trong sheet Thuyet_minh.
