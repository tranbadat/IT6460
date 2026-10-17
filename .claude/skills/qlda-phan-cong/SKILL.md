---
name: qlda-phan-cong
description: Giao việc cho thành viên nhóm theo gói WBS và lập danh sách phân chia công việc (responsibilities) - người thực hiện, người hỗ trợ, ma trận RACI mục mức 1 và mức 2, nhân sự chủ chốt theo HSMT, tải từng người theo sprint so với quỹ thời gian. Dùng khi người dùng muốn phân công nhiệm vụ, lập RACI, cân bằng tải, cập nhật danh sách trách nhiệm trong nhóm.
---

# Phân công nhiệm vụ

Đầu vào: du_lieu/wbs.json, dau_vao/thanh_vien.json (thành viên nhóm và vị trí bổ sung, vai trò, năng lực, tỷ lệ tham gia, thời gian huy động), du_lieu/hsmt.json (nhân sự chủ chốt). Tài liệu còn dùng du_lieu/lich.json.

## Bước dữ liệu (giao_viec)

1. Agent Giao việc theo `prompts/vai_giao_viec.md`, viết lam_viec/giao_viec/phan_cong_nhap.json.
2. `python .claude/skills/qlda-phan-cong/scripts/kiem_tra_giao_viec.py lam_viec/giao_viec/phan_cong_nhap.json`
   Mọi gói lá có một R, năng lực phù hợp (hoặc có lý do), mỗi mục mức 1, mức 2 có đúng một A, C và I hợp lệ, tổng MD mỗi người không vượt quỹ thời gian, nhân sự chủ chốt khớp HSMT.
3. Chạy lại master schedule (qlda-master-schedule) để kiểm tra lịch khả thi với cách giao.

## Bước tài liệu (phan_cong_tai_lieu)

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi phan_cong_tai_lieu` (tự chạy scripts/tinh_bang_phan_cong.py: RACI, giao việc theo người, tải theo sprint).
2. Agent Soạn thảo viết bản soạn: nguyên tắc phân công, trách nhiệm từng vai trò, cơ chế thay thế khi vắng mặt.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien phan_cong_tai_lieu --ghi-chu "..."`. Ma trận RACI in trang ngang.
4. Agent Kiểm tra lớp B với `dac_ta/phan_cong_tai_lieu.json`.

Đầu ra: du_lieu/phan_cong.json, ket_qua/10_Responsibilities/Phan_cong_nhiem_vu.docx. Bảng phân chia lương (qlda-bang-luong) dựa trên công sức thực tế, không dựa trên bảng giao việc.
