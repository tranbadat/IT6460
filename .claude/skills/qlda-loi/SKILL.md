---
name: qlda-loi
description: Lõi dùng chung của bộ skill quản lý dự án BTL_QLDA (ABC Wear Web Selling Site System) - điều phối các bước, xem trạng thái và tài liệu nào đã cũ, phân tích ảnh hưởng khi có thay đổi, dựng và kiểm tra tài liệu Word, ghi nhật ký và xuất phụ lục bằng chứng prompt, skill. Dùng khi người dùng hỏi nên làm bước nào tiếp, tài liệu nào cần cập nhật, chạy vòng làm - kiểm tra - sửa cho một tài liệu, hoặc cần bằng chứng prompt và skill để nộp.
---

# Lõi bộ skill quản lý dự án

Các skill tài liệu (qlda-*) và hsmt-mau-5a dùng chung thư viện, quy trình và sơ đồ phụ thuộc trong skill này. Đọc trước:
- `references/quy_trinh_chung.md`: vòng làm, kiểm tra, sửa và bảng các bước dữ liệu.
- `references/du_lieu.md`: thư mục, tệp dữ liệu, cú pháp tham chiếu số liệu (khóa có dấu chấm, lọc mọi phần tử, đếm |dem), khóa đặc tả cho bảng (dong_tong.tong, mau_so, bìa hồ sơ thầu) và khóa kiểm tra lớp A (muc_bat_buoc, bieu_mau, ngoac_cho_phep).
- `references/van_phong.md`: văn phong, trình bày (Times New Roman 13, bảng lưới, không in đậm trừ mục cha WBS, gạch ngang đơn).
- `references/so_do_phu_thuoc.json`: đầu vào, đầu ra của từng bước, tài liệu khóa.

Mọi lệnh chạy từ thư mục gốc của dự án (thư mục có `dau_vao/` và `.claude/`). Windows dùng `python`, macOS và Linux dùng `python3`.

## Lệnh điều phối

| Lệnh | Tác dụng |
|---|---|
| `python .claude/skills/qlda-loi/scripts/chay.py trang_thai` | Trạng thái mọi bước: cập nhật, cũ (đầu vào đã đổi), thiếu đầu vào, sẵn sàng, đã khóa. Gợi ý bước tiếp theo |
| `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi <buoc>` | Lập khung tài liệu, điền sẵn bảng và số liệu, liệt kê đoạn cần agent soạn |
| `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien <buoc> --ghi-chu "..." [--ngay yyyy-mm-dd]` | Ghép bản soạn (tự lập lại khung nếu dữ liệu nguồn đã đổi), dựng Word, kiểm tra lớp A, sửa tự động, tối đa 3 vòng, đăng ký phiên bản. --ngay là ngày ghi trên tài liệu, dùng khi cập nhật theo yêu cầu thay đổi |
| `python .claude/skills/qlda-loi/scripts/chay.py anh_huong <nút hoặc tệp>` | Các bước bị ảnh hưởng khi một đầu vào thay đổi, tách tài liệu khóa |
| `python .claude/skills/qlda-loi/scripts/chay.py dang_ky <buoc> --ghi-chu "..."` | Đăng ký phiên bản cho đầu ra của một bước tạo bằng tay hoặc bằng công cụ khác |
| `python .claude/skills/qlda-loi/scripts/chay.py bang_chung` | Xuất Phụ lục bằng chứng prompt và skill vào ket_qua/16_Bang_chung |
| `python .claude/skills/qlda-loi/scripts/nhat_ky.py --skill ... --buoc ... --vai ... --prompt ... --vao ... --ra ... --tom-tat ...` | Ghi nhật ký một bước do agent thực hiện |

## Vai agent

- Soạn thảo: `prompts/vai_soan_thao.md`. Chỉ viết lời văn vào `lam_viec/<buoc>/ban_soan.json`, mọi con số bằng tham chiếu dữ liệu.
- Kiểm tra độc lập (lớp B): `prompts/vai_kiem_tra.md`. Có công cụ tạo agent con thì giao cho agent con trong phiên riêng, chỉ chuyển các tệp được phép đọc. Không có thì tự đóng vai, không mở bản soạn.
- Sửa: `prompts/vai_sua.md`. Phân loại lỗi ở bản soạn, ở dữ liệu nguồn hay thuộc quyết định của nhóm.

## Nguyên tắc

1. Không agent nào dùng HSMT, HSDT hay tài liệu hoàn chỉnh có sẵn của nhóm hoặc của người khác làm đầu vào hay để so sánh. Tài liệu được lập từ RFP, Mẫu 5A, tham số và dữ liệu do bộ skill tạo ra.
2. Số liệu chỉ do script tính, tài liệu đọc từ `du_lieu/`. Sai số liệu thì sửa ở bước tạo dữ liệu, không sửa trong Word.
3. Mỗi lần chạy được ghi nhật ký kèm băm đầu vào, đầu ra và bản sao prompt. Không xóa `bang_chung/`.
4. Khi người dùng muốn sửa tài liệu đã lưu, mặc định đưa chỉ dẫn sửa từng phần (vị trí, hiện tại, sửa thành). Chỉ chạy lại và xuất tệp khi người dùng yêu cầu rõ.
