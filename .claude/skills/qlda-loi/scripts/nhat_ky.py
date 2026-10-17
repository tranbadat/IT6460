"""Ghi một bước do agent (hoặc người dùng) thực hiện vào nhật ký bằng chứng.

Dùng: python nhat_ky.py --skill <tên skill> --buoc <mã bước> --vai "<vai agent>" --prompt <tệp prompt đã dùng>
         [--vao tệp ...] [--ra tệp ...] --tom-tat "<việc đã làm, kết quả>" [--moi-truong "Claude Code trong VS Code, model ..."]
         [--loai agent|nguoi_dung]
Nội dung prompt được chụp lại vào bang_chung/prompts/ kèm mã băm, để chứng minh prompt nào đã tạo ra kết quả nào.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loi  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--skill', required=True); ap.add_argument('--buoc', required=True); ap.add_argument('--vai', default='')
ap.add_argument('--prompt'); ap.add_argument('--vao', nargs='*', default=[]); ap.add_argument('--ra', nargs='*', default=[])
ap.add_argument('--tom-tat', required=True); ap.add_argument('--moi-truong', default=''); ap.add_argument('--loai', default='agent')
ap.add_argument('--ket-qua', default='hoàn thành')
a = ap.parse_args()
rec = loi.ghi_nhat_ky(a.skill, a.buoc, a.loai, (a.vai + ': ' if a.vai else '') + a.tom_tat, vao=a.vao, ra=a.ra,
                      ket_qua=a.ket_qua, prompt=a.prompt, chi_tiet={'moi_truong': a.moi_truong, 'vai': a.vai})
print(f'Đã ghi nhật ký: {rec["thoi_gian"]} {a.skill} {a.buoc}' + (f' (prompt {rec["prompt_hash"]})' if rec['prompt_hash'] else ''))
