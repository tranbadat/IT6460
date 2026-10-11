"""Sinh file Word E-HSMT từ nội dung, dùng được trên Claude và ChatGPT (Code Interpreter).

Dùng: python3 build_hsmt.py <hsmt_noi_dung.json> <mau5a_fixed.json> <file_ra.docx>
- hsmt_noi_dung.json: nội dung HSMT sau khi ghép khung và bản soạn (dien_khung.py).
- mau5a_fixed.json: Chương I, Chương VI, Mục 1 Chương III trích nguyên văn từ Mẫu 5A (phan_tich_mau.py).
Chỉ cần thư viện python-docx.
"""
import json, re, sys
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Twips, RGBColor

data_path, fixed_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.load(open(data_path, encoding='utf-8'))
fixed = json.load(open(fixed_path, encoding='utf-8'))
meta = data['meta']
FONT, SIZE = meta['font'], meta['size_pt']

def clean(s):
    return re.sub('[\u2013\u2014]', '-', str(s))

def set_font(run, size=SIZE, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = False
    run.font.italic = italic
    run.font.all_caps = False
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rf.set(qn(a), FONT)

def fmt(par, align=None, before=0, after=0, line=None):
    pf = par.paragraph_format
    if align is not None: pf.alignment = align
    pf.space_before = Pt(before); pf.space_after = Pt(after)
    if line: pf.line_spacing = line

doc = Document()
# kiểu mặc định và kiểu tiêu đề: Times New Roman, không đậm, màu đen
for sname, sz in (('Normal', SIZE), ('Heading 1', SIZE + 2), ('Heading 2', SIZE)):
    st = doc.styles[sname]
    st.font.name = FONT; st.font.size = Pt(sz); st.font.bold = False; st.font.italic = False
    st.font.color.rgb = RGBColor(0, 0, 0)
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rf.set(qn(a), FONT)
    for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]

sec = doc.sections[0]
sec.page_width, sec.page_height = Twips(11907), Twips(16840)
m = meta['margin_twip']
sec.top_margin, sec.bottom_margin = Twips(m['top']), Twips(m['bottom'])
sec.left_margin, sec.right_margin = Twips(m['left']), Twips(m['right'])

hp = sec.header.paragraphs[0]; fmt(hp, WD_ALIGN_PARAGRAPH.RIGHT)
set_font(hp.add_run(clean(meta['header'])), 10, italic=True)
fp = sec.footer.paragraphs[0]; fmt(fp, WD_ALIGN_PARAGRAPH.CENTER)
r = fp.add_run(); set_font(r, 11)
for tag, txt in (('begin', None), (None, 'PAGE'), ('end', None)):
    if tag:
        el = OxmlElement('w:fldChar'); el.set(qn('w:fldCharType'), tag)
    else:
        el = OxmlElement('w:instrText'); el.set(qn('xml:space'), 'preserve'); el.text = txt
    r._element.append(el)

def para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=SIZE, before=0, after=5, line=1.25, style=None):
    pr = doc.add_paragraph(style=style)
    fmt(pr, align, before, after, line)
    set_font(pr.add_run(clean(text)), size)
    return pr

def cell_margins(tbl):
    tblPr = tbl._tbl.tblPr
    mar = OxmlElement('w:tblCellMar')
    for side, v in (('top', 50), ('left', 80), ('bottom', 50), ('right', 80)):
        e = OxmlElement('w:' + side); e.set(qn('w:w'), str(v)); e.set(qn('w:type'), 'dxa'); mar.append(e)
    tblPr.append(mar)

def table(rows, widths, center_cols=()):
    ncol = len(widths)
    tbl = doc.add_table(rows=0, cols=ncol)
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl.autofit = False
    cell_margins(tbl)
    for row in rows:
        cells = tbl.add_row().cells
        for i, content in enumerate(row):
            items = content if isinstance(content, list) else [content]
            c = cells[i]; c.width = Twips(widths[i])
            first = True
            for t in items:
                pr = c.paragraphs[0] if first else c.add_paragraph()
                first = False
                fmt(pr, WD_ALIGN_PARAGRAPH.CENTER if i in center_cols else WD_ALIGN_PARAGRAPH.LEFT, 0, 3)
                set_font(pr.add_run(clean(t)))
    for i, w in enumerate(widths):
        tbl.columns[i].width = Twips(w)
    return tbl

for b in data['blocks']:
    t = b['t']
    if t == 'center':
        para(b['text'], WD_ALIGN_PARAGRAPH.CENTER, b.get('size', SIZE), 0, 6, None)
    elif t == 'h1':
        para(b['text'], WD_ALIGN_PARAGRAPH.CENTER, SIZE + 2, 12, 8, None, 'Heading 1')
    elif t == 'h2':
        para(b['text'], WD_ALIGN_PARAGRAPH.LEFT, SIZE, 10, 6, None, 'Heading 2')
    elif t == 'p':
        para(b['text'])
    elif t == 'blank':
        doc.add_paragraph()
    elif t == 'pagebreak':
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    elif t == 'table':
        table(b['rows'], b['widths'], b.get('center_cols', []))
    elif t == 'fixed_table':
        table([[l, r] for l, r in fixed[b['key']]], b['widths'])
    elif t == 'fixed_paras':
        for txt in fixed[b['key']]:
            para(txt)
    else:
        raise ValueError('Khối không hợp lệ: ' + t)

doc.core_properties.author = 'Tran Ba Dat'
doc.core_properties.title = meta['ten']
doc.save(out_path)
print('Đã tạo', out_path)
