"""Chuyển từng trang RFP.pdf thành ảnh PNG để agent Phân tích RFP xem (RFP thường là bản scan, không có lớp chữ).

Dùng: python rfp_sang_anh.py <RFP.pdf> <thu_muc_anh>
Ưu tiên PyMuPDF (pip install pymupdf, chạy được trên Windows, macOS, Linux). Nếu không có thì dùng pdftoppm.
"""
import os as _os, sys as _sys  # noqa: E401
_os.environ.setdefault('PYTHONUTF8', '1')  # tiến trình con đọc, ghi UTF-8 (Windows)
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass
import os, shutil, subprocess, sys

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
try:
    import fitz  # PyMuPDF
    doc = fitz.open(src)
    for i, page in enumerate(doc, 1):
        page.get_pixmap(dpi=90).save(os.path.join(out, f'trang-{i}.png'))
    print(f'Đã tạo {len(doc)} ảnh trong {out}')
except ImportError:
    if not shutil.which('pdftoppm'):
        sys.exit('Cần cài một trong hai: pip install pymupdf, hoặc poppler (pdftoppm).')
    subprocess.run(['pdftoppm', '-png', '-r', '90', src, os.path.join(out, 'trang')], check=True)
    print('Đã tạo ảnh trong', out)
