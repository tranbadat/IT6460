---
name: qlda-bai-hoc
description: Rút và lập báo cáo bài học kinh nghiệm của dự án - mỗi bài học có tình huống, nguyên nhân gốc, bài học, khuyến nghị, phạm vi áp dụng và mã bằng chứng (CR, RR, ghi chép họp cải tiến R-Sx-nn, nghiệm thu NT, lỗi L, KPI K, mốc, sprint, gói WBS), kiểm tra phủ đủ nhóm, rủi ro đã xảy ra, yêu cầu thay đổi, chỉ tiêu không đạt, đề xuất cải tiến quy trình. Dùng khi người dùng muốn lập báo cáo bài học kinh nghiệm, lessons learned, tổng hợp retro.
---

# Bài học kinh nghiệm

Đầu vào: du_lieu/ket_thuc.json, rui_ro.json, thay_doi.json, dau_vao/thuc_te/retro.md (mỗi ý một mã R-Sx-nn và loại), theo_doi_rui_ro.csv, nghiem_thu.csv, loi.csv, ket_qua/12_Bao_cao_danh_gia/Bao_cao_danh_gia_du_an.docx. Nhóm bài học và quy tắc: `references/nhom_bai_hoc.json`.

## Bước dữ liệu

1. Agent Rút bài học theo `prompts/vai_rut_bai_hoc.md`, viết lam_viec/bai_hoc/bai_hoc_nhap.json.
2. `python .claude/skills/qlda-bai-hoc/scripts/kiem_tra_bai_hoc.py lam_viec/bai_hoc/bai_hoc_nhap.json`
   Lỗi khi: thiếu số lượng tối thiểu, thiếu nhóm bắt buộc, mã bằng chứng không tồn tại, bài học không có bằng chứng, rủi ro đã xảy ra hoặc CR hoặc KPI không đạt chưa được rút bài học, thiếu bài học tích cực hoặc cần cải thiện. Cảnh báo khi ghi chép cải tiến cần cải thiện hoặc tiêu chí nghiệm thu lại chưa được trích dẫn.
   Đạt thì ghi du_lieu/bai_hoc.json.

## Bước tài liệu

1. `python .claude/skills/qlda-loi/scripts/chay.py chuan_bi bai_hoc`
2. Agent Soạn thảo viết cách thu thập, tổng hợp, đề xuất cải tiến quy trình (mỗi đề xuất dẫn mã BH), kết luận.
3. `python .claude/skills/qlda-loi/scripts/chay.py hoan_thien bai_hoc --ghi-chu "..."`. Bảng bài học in trang ngang.
4. Agent Kiểm tra lớp B với `dac_ta/bao_cao_bai_hoc.json`.

Đầu ra: du_lieu/bai_hoc.json, ket_qua/13_Bai_hoc_kinh_nghiem/Bao_cao_bai_hoc_kinh_nghiem.docx.
