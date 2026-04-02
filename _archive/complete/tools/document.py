"""
Document Tools - Word, Excel, Markdown generation

Enhanced Word document support with:
- Multiple heading levels (# ## ###)
- Table of Contents
- Bullet lists (- item)
- Numbered lists (1. item)
- Bold (**text**) and Italic (*text*)
- Tables (| col1 | col2 |)
- Page breaks (---PAGE---)
- Headers and footers
"""
import os
import re

# Lazy import
Tool = None


def _get_tool_class():
    global Tool
    if Tool is None:
        from core.tools import Tool as T
        Tool = T
    return Tool


def create_word_doc(args: dict, ctx) -> str:
    """Create Word document with rich styling."""
    filepath = args["filepath"]
    content = args["content"]
    title = args.get("title", "")
    include_toc = args.get("include_toc", False)
    header_text = args.get("header", "")
    footer_text = args.get("footer", "")

    # Handle relative paths
    if not os.path.isabs(filepath):
        filepath = os.path.join(ctx.working_dir, filepath)

    # Ensure .docx extension
    if not filepath.endswith(".docx"):
        filepath += ".docx"

    try:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.style import WD_STYLE_TYPE
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement

        doc = Document()

        # Add header if specified
        if header_text:
            section = doc.sections[0]
            header = section.header
            header_para = header.paragraphs[0]
            header_para.text = header_text
            header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add footer if specified
        if footer_text:
            section = doc.sections[0]
            footer = section.footer
            footer_para = footer.paragraphs[0]
            footer_para.text = footer_text
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add title
        if title:
            title_para = doc.add_heading(title, 0)
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add Table of Contents placeholder
        if include_toc:
            doc.add_paragraph("Table of Contents", style="Heading 1")
            # Add TOC field code
            paragraph = doc.add_paragraph()
            run = paragraph.add_run()
            fld_char_begin = OxmlElement('w:fldChar')
            fld_char_begin.set(qn('w:fldCharType'), 'begin')
            run._r.append(fld_char_begin)

            run = paragraph.add_run()
            instr_text = OxmlElement('w:instrText')
            instr_text.text = 'TOC \\o "1-3" \\h \\z \\u'
            run._r.append(instr_text)

            run = paragraph.add_run()
            fld_char_end = OxmlElement('w:fldChar')
            fld_char_end.set(qn('w:fldCharType'), 'end')
            run._r.append(fld_char_end)

            doc.add_paragraph("[Update TOC: Right-click → Update Field]")
            doc.add_page_break()

        # Parse and add content
        _parse_styled_content(doc, content, ctx.working_dir)

        # Create directory if needed
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        doc.save(filepath)

        features = []
        if include_toc:
            features.append("TOC")
        if header_text:
            features.append("header")
        if footer_text:
            features.append("footer")

        feature_str = f" (with {', '.join(features)})" if features else ""
        return f"Created Word document: {filepath}{feature_str}"

    except ImportError:
        return "Error: python-docx not installed. Run: pip install python-docx"
    except Exception as e:
        return f"Error creating Word document: {e}"


def _parse_styled_content(doc, content: str, working_dir: str = "."):
    """Parse markdown-like content and add to Word document with styling.

    Supports:
    - # ## ### headings
    - **bold**, *italic*, ***bold-italic***
    - - bullet lists
    - 1. numbered lists
    - | tables |
    - ---PAGE--- page breaks
    - ![alt](path) images (must be actual image files .png/.jpg)
    """
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    lines = content.split("\n")
    i = 0
    in_table = False
    table_data = []

    while i < len(lines):
        line = lines[i]

        # Page break
        if line.strip() == "---PAGE---":
            doc.add_page_break()
            i += 1
            continue

        # Image embed: ![alt](path)
        img_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if img_match:
            img_alt = img_match.group(1)
            img_path = img_match.group(2)
            # Resolve path - strip leading ./ and normalize
            img_path = img_path.lstrip("./").lstrip(".\\")
            if not os.path.isabs(img_path):
                img_path = os.path.join(working_dir, img_path)
            img_path = os.path.normpath(img_path)
            if os.path.exists(img_path):
                try:
                    doc.add_picture(img_path, width=Inches(5.5))
                    if img_alt:
                        caption = doc.add_paragraph(img_alt)
                        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                except Exception as e:
                    doc.add_paragraph(f"[Image error: {e}]")
            else:
                doc.add_paragraph(f"[Image not found: {img_path}]")
            i += 1
            continue

        # Headings
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
            i += 1
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
            i += 1
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
            i += 1
            continue

        # Table detection - more robust: detect any line with | separators
        stripped = line.strip()
        # Match: | col1 | col2 | OR col1 | col2 (without leading |)
        is_table_line = (stripped.startswith("|") and "|" in stripped[1:]) or \
                        ("|" in stripped and re.match(r'^[^|]+\|.+$', stripped))

        if is_table_line:
            if not in_table:
                in_table = True
                table_data = []
            # Normalize: ensure leading/trailing | for consistent parsing
            if not stripped.startswith("|"):
                stripped = "|" + stripped
            if not stripped.endswith("|"):
                stripped = stripped + "|"
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            # Skip separator rows (|---|---|)
            if not all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                table_data.append(cells)
            i += 1
            continue
        elif in_table:
            # End of table, create it
            if table_data:
                _add_table(doc, table_data)
            in_table = False
            table_data = []

        # Bullet list
        if line.strip().startswith("- "):
            para = doc.add_paragraph(style="List Bullet")
            _add_formatted_text(para, line.strip()[2:])
            i += 1
            continue

        # Numbered list
        match = re.match(r"^\d+\.\s+", line.strip())
        if match:
            para = doc.add_paragraph(style="List Number")
            _add_formatted_text(para, line.strip()[match.end():])
            i += 1
            continue

        # Regular paragraph
        if line.strip():
            para = doc.add_paragraph()
            _add_formatted_text(para, line.strip())

        i += 1

    # Handle remaining table
    if in_table and table_data:
        _add_table(doc, table_data)


def _add_formatted_text(paragraph, text: str):
    """Add text with bold/italic formatting to paragraph."""
    # Pattern for **bold**, *italic*, and ***bold italic***
    pattern = r"(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*)"
    parts = re.split(pattern, text)

    for part in parts:
        if not part:
            continue
        if part.startswith("***") and part.endswith("***"):
            run = paragraph.add_run(part[3:-3])
            run.bold = True
            run.italic = True
        elif part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("*") and part.endswith("*"):
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        else:
            paragraph.add_run(part)


def _add_table(doc, table_data: list):
    """Add a styled table to the document."""
    from docx.shared import Pt, Inches
    from docx.enum.table import WD_TABLE_ALIGNMENT

    if not table_data:
        return

    rows = len(table_data)
    cols = max(len(row) for row in table_data)

    table = doc.add_table(rows=rows, cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, row_data in enumerate(table_data):
        row = table.rows[i]
        for j, cell_text in enumerate(row_data):
            if j < cols:
                cell = row.cells[j]
                cell.text = cell_text
                # Bold header row
                if i == 0:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.bold = True

    doc.add_paragraph()  # Space after table


def create_excel(args: dict, ctx) -> str:
    """Create Excel spreadsheet."""
    filepath = args["filepath"]
    data = args["data"]
    sheet_name = args.get("sheet_name", "Sheet1")

    # Handle relative paths
    if not os.path.isabs(filepath):
        filepath = os.path.join(ctx.working_dir, filepath)

    # Ensure .xlsx extension
    if not filepath.endswith(".xlsx"):
        filepath += ".xlsx"

    try:
        import pandas as pd

        df = pd.DataFrame(data)

        # Create directory if needed
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        df.to_excel(filepath, sheet_name=sheet_name, index=False)
        return f"Created Excel file: {filepath} ({len(df)} rows)"

    except ImportError:
        return "Error: pandas/openpyxl not installed. Run: pip install pandas openpyxl"
    except Exception as e:
        return f"Error creating Excel file: {e}"


def create_markdown(args: dict, ctx) -> str:
    """Create Markdown file."""
    filepath = args["filepath"]
    content = args["content"]

    # Handle relative paths
    if not os.path.isabs(filepath):
        filepath = os.path.join(ctx.working_dir, filepath)

    # Ensure .md extension
    if not filepath.endswith(".md"):
        filepath += ".md"

    try:
        # Create directory if needed
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Created Markdown file: {filepath}"

    except Exception as e:
        return f"Error creating Markdown file: {e}"


def _parse_markdown_table(text: str) -> list:
    """Parse markdown table into list of lists for PDF/reportlab."""
    lines = text.strip().split("\n")
    table_data = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip separator lines (all dashes/colons)
        if re.match(r'^[\|\s\-:]+$', stripped):
            continue
        # Parse table row
        if "|" in stripped:
            # Normalize: ensure leading/trailing | for consistent parsing
            if not stripped.startswith("|"):
                stripped = "|" + stripped
            if not stripped.endswith("|"):
                stripped = stripped + "|"
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            if cells and any(c for c in cells):  # Skip empty rows
                table_data.append(cells)
    return table_data


def create_pdf(args: dict, ctx) -> str:
    """Create PDF document with text, tables, and images.

    For tables, you can provide either:
    1. Structured data: [["City", "2020"], ["Sydney", "1200000"]]
    2. Markdown table: "| City | 2020 |\\n| --- | --- |\\n| Sydney | 1200000 |"
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
    except ImportError:
        return "Error: reportlab not installed. Run: pip install reportlab"

    filepath = args.get("filepath")
    content = args.get("content")
    title = args.get("title", "Document")
    page_size = args.get("page_size", "letter")

    # Validate filepath
    if not filepath or not isinstance(filepath, str):
        return "Error: 'filepath' is required and must be a string (e.g., 'report.pdf')"

    # Validate content
    if not content:
        return "Error: 'content' is required. Must be list of dicts: [{type: 'heading'|'text'|'table'|'image', data: ...}]"

    if isinstance(content, str):
        content = [{"type": "text", "data": content}]
    elif not isinstance(content, list):
        return "Error: 'content' must be a list of sections"

    if not os.path.isabs(filepath):
        filepath = os.path.join(ctx.working_dir, filepath)
    if not filepath.lower().endswith('.pdf'):
        filepath += ".pdf"

    try:
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        doc = SimpleDocTemplate(filepath, pagesize=letter if page_size == "letter" else A4)
        styles = getSampleStyleSheet()
        story = []

        styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Title'], fontSize=24, spaceAfter=30))
        styles.add(ParagraphStyle(name='CustomHeading', parent=styles['Heading1'], fontSize=16, spaceAfter=12))
        styles.add(ParagraphStyle(name='CustomBody', parent=styles['Normal'], fontSize=11, spaceAfter=10))

        story.append(Paragraph(title, styles['CustomTitle']))
        story.append(Spacer(1, 12))

        for section in content:
            if isinstance(section, str):
                section = {"type": "text", "data": section}
            elif not isinstance(section, dict):
                continue

            section_type = section.get("type", "text")
            data = section.get("data", "")

            if section_type == "heading":
                story.append(Paragraph(str(data), styles['CustomHeading']))

            elif section_type == "text":
                for para in str(data).split('\n\n'):
                    if para.strip():
                        story.append(Paragraph(para.replace('\n', '<br/>'), styles['CustomBody']))

            elif section_type == "table":
                table_data = data
                if isinstance(data, str):
                    table_data = _parse_markdown_table(data)
                if isinstance(table_data, list) and len(table_data) > 0:
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a9eff')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 12))

            elif section_type == "image":
                img_path = data if os.path.isabs(data) else os.path.join(ctx.working_dir, data)
                if os.path.exists(img_path):
                    img = Image(img_path)
                    orig_width = img.drawWidth
                    orig_height = img.drawHeight
                    img.drawWidth = min(orig_width, 6*inch)
                    img.drawHeight = orig_height * (img.drawWidth / orig_width)
                    story.append(img)
                    story.append(Spacer(1, 12))

            story.append(Spacer(1, 6))

        doc.build(story)
        return f"Created PDF: {filepath}"
    except Exception as e:
        return f"Error creating PDF: {e}"


# Tool definitions
def get_tools():
    """Get all document tools."""
    Tool = _get_tool_class()

    CREATE_WORD = Tool(
        name="create_word",
        description="""Create styled Word document (.docx) with rich formatting.

Supports markdown-like syntax:
- Headings: # H1, ## H2, ### H3
- Bold: **text**
- Italic: *text*
- Bullet lists: - item
- Numbered lists: 1. item
- Tables: | col1 | col2 |
- Page breaks: ---PAGE---
- Images: ![caption](image.png)

NOTE: Images must be actual image files (.png, .jpg). For charts, first use create_chart to generate an image file, then reference it with ![caption](chart.png).

Example content:
# Main Title
## Section One
This is **bold** and *italic* text.

- First bullet
- Second bullet

| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |

![Sales Chart](sales_chart.png)

---PAGE---
## Section Two
More content here.""",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Output path (.docx)",
                },
                "content": {
                    "type": "string",
                    "description": "Document content with markdown-like formatting",
                },
                "title": {
                    "type": "string",
                    "description": "Document title (centered at top)",
                },
                "include_toc": {
                    "type": "boolean",
                    "description": "Include Table of Contents (default: false)",
                },
                "header": {
                    "type": "string",
                    "description": "Header text for all pages",
                },
                "footer": {
                    "type": "string",
                    "description": "Footer text for all pages",
                },
            },
            "required": ["filepath", "content"],
        },
        execute=create_word_doc,
        requires_approval=False,
    )

    CREATE_EXCEL = Tool(
        name="create_excel",
        description="Create Excel spreadsheet (.xlsx). Data should be list of dicts (rows) with consistent keys (columns).",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Output path (.xlsx)",
                },
                "data": {
                    "type": "array",
                    "description": "Data as list of dicts, e.g., [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]",
                    "items": {"type": "object"},
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Sheet name (default: Sheet1)",
                },
            },
            "required": ["filepath", "data"],
        },
        execute=create_excel,
        requires_approval=False,
    )

    CREATE_MARKDOWN = Tool(
        name="create_markdown",
        description="Create Markdown file (.md).",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Output path (.md)",
                },
                "content": {
                    "type": "string",
                    "description": "Markdown content",
                },
            },
            "required": ["filepath", "content"],
        },
        execute=create_markdown,
        requires_approval=False,
    )

    CREATE_PDF = Tool(
        name="create_pdf",
        description="Create PDF with text, tables, images. Tables can be list-of-lists OR markdown format. Images must be actual image files (.png/.jpg).",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Output PDF path",
                },
                "title": {
                    "type": "string",
                    "description": "Document title",
                },
                "content": {
                    "type": "array",
                    "description": "List of sections: [{type: 'heading'|'text'|'table'|'image', data: ...}]. Table data can be list-of-lists or markdown string.",
                    "items": {"type": "object"},
                },
                "page_size": {
                    "type": "string",
                    "enum": ["letter", "a4"],
                    "description": "Page size",
                },
            },
            "required": ["filepath", "content"],
        },
        execute=create_pdf,
        requires_approval=False,
    )

    return CREATE_WORD, CREATE_EXCEL, CREATE_MARKDOWN, CREATE_PDF


# Export tools
CREATE_WORD, CREATE_EXCEL, CREATE_MARKDOWN, CREATE_PDF = get_tools()
