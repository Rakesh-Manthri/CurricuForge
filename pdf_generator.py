"""
pdf_generator.py — Generates a polished PDF curriculum document using ReportLab.
"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable


# ── Color palette ────────────────────────────────────────────────────
PRIMARY = HexColor("#6366f1")
PRIMARY_LIGHT = HexColor("#e0e1ff")
ACCENT_GREEN = HexColor("#10b981")
ACCENT_CYAN = HexColor("#06b6d4")
ACCENT_AMBER = HexColor("#f59e0b")
TEXT_DARK = HexColor("#1e293b")
TEXT_MEDIUM = HexColor("#475569")
TEXT_LIGHT = HexColor("#94a3b8")
BG_LIGHT = HexColor("#f8fafc")
BORDER = HexColor("#e2e8f0")

SEMESTER_COLORS = [
    HexColor("#6366f1"),
    HexColor("#06b6d4"),
    HexColor("#f59e0b"),
    HexColor("#10b981"),
    HexColor("#a855f7"),
    HexColor("#ef4444"),
]


# ── Custom Flowables ─────────────────────────────────────────────────
class ColoredBar(Flowable):
    """A thin colored bar for visual separation."""
    def __init__(self, color, width, height=2):
        super().__init__()
        self.color = color
        self.bar_width = width
        self.bar_height = height

    def wrap(self, availWidth, availHeight):
        return (self.bar_width, self.bar_height)

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.bar_width, self.bar_height, 1, fill=1, stroke=0)


class RoundedBox(Flowable):
    """A rounded rectangle background for badges."""
    def __init__(self, text, bg_color, text_color, font_size=7, padding=(3, 6)):
        super().__init__()
        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color
        self.font_size = font_size
        self.pad_v, self.pad_h = padding

    def wrap(self, availWidth, availHeight):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        w = stringWidth(self.text, "Helvetica-Bold", self.font_size) + self.pad_h * 2
        h = self.font_size + self.pad_v * 2
        return (w, h)

    def draw(self):
        w, h = self.wrap(0, 0)
        self.canv.setFillColor(self.bg_color)
        self.canv.roundRect(0, 0, w, h, 3, fill=1, stroke=0)
        self.canv.setFillColor(self.text_color)
        self.canv.setFont("Helvetica-Bold", self.font_size)
        self.canv.drawString(self.pad_h, self.pad_v, self.text)


# ── Styles ───────────────────────────────────────────────────────────
def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'DocTitle', fontName='Helvetica-Bold', fontSize=22,
        textColor=TEXT_DARK, leading=28, alignment=TA_CENTER, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'DocSubTitle', fontName='Helvetica', fontSize=10,
        textColor=TEXT_MEDIUM, alignment=TA_CENTER, spaceAfter=16
    ))
    styles.add(ParagraphStyle(
        'SectionLabel', fontName='Helvetica-Bold', fontSize=8,
        textColor=PRIMARY, leading=12, spaceAfter=4,
        spaceBefore=0
    ))
    styles.add(ParagraphStyle(
        'SummaryText', fontName='Helvetica', fontSize=10,
        textColor=TEXT_MEDIUM, leading=16, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        'SemesterHeader', fontName='Helvetica-Bold', fontSize=13,
        textColor=TEXT_DARK, leading=18, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        'CourseName', fontName='Helvetica-Bold', fontSize=10,
        textColor=TEXT_DARK, leading=14, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        'CourseDesc', fontName='Helvetica', fontSize=9,
        textColor=TEXT_MEDIUM, leading=13, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'TopicText', fontName='Helvetica', fontSize=8,
        textColor=TEXT_MEDIUM, leading=11
    ))
    styles.add(ParagraphStyle(
        'BadgeText', fontName='Helvetica-Bold', fontSize=7.5,
        textColor=PRIMARY, leading=10
    ))
    styles.add(ParagraphStyle(
        'FooterText', fontName='Helvetica', fontSize=7,
        textColor=TEXT_LIGHT, alignment=TA_CENTER
    ))

    return styles


# ── PDF Builder ──────────────────────────────────────────────────────
def generate_curriculum_pdf(curriculum_data: dict, params: dict) -> bytes:
    """
    Generates a polished PDF from curriculum data.
    Returns the PDF as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20*mm, bottomMargin=20*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title=f"Curriculum — {params.get('skill', 'Curriculum')}",
        author="CurricuForge"
    )

    styles = get_styles()
    story = []
    page_width = A4[0] - 36*mm  # available width

    # ── Title ────────────────────────────────────────────────────
    story.append(Spacer(1, 5*mm))
    story.append(ColoredBar(PRIMARY, page_width, 3))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(f"Curriculum: {params.get('skill', 'Untitled')}", styles['DocTitle']))

    level_labels = {
        'beginner': 'Beginner / K-12',
        'undergraduate': 'Undergraduate',
        'graduate': 'Graduate',
        'expert': 'Expert / Professional'
    }
    level_str = level_labels.get(params.get('level', ''), params.get('level', ''))
    subtitle_parts = [level_str]
    if params.get('industry'):
        subtitle_parts.append(params['industry'])
    subtitle_parts.append(f"{params.get('semesters', 4)} Semesters")
    subtitle_parts.append(f"{params.get('hours', 15)} hrs/week")

    story.append(Paragraph(" · ".join(subtitle_parts), styles['DocSubTitle']))
    story.append(ColoredBar(PRIMARY, page_width, 1))
    story.append(Spacer(1, 6*mm))

    # ── Overview ─────────────────────────────────────────────────
    summary = curriculum_data.get('summary', '')
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", styles['SectionLabel']))
        story.append(Paragraph(summary, styles['SummaryText']))
        story.append(Spacer(1, 3*mm))

    # ── Stats table ──────────────────────────────────────────────
    semesters = curriculum_data.get('semesters', [])
    total_courses = sum(len(s.get('courses', [])) for s in semesters)
    total_credits = sum(
        sum(c.get('credits', 3) for c in s.get('courses', []))
        for s in semesters
    )

    stats_data = [[
        Paragraph(f"<b>{len(semesters)}</b><br/><font size=7 color='#{TEXT_LIGHT.hexval()[2:]}'>Semesters</font>", styles['Normal']),
        Paragraph(f"<b>{total_courses}</b><br/><font size=7 color='#{TEXT_LIGHT.hexval()[2:]}'>Total Courses</font>", styles['Normal']),
        Paragraph(f"<b>{total_credits}</b><br/><font size=7 color='#{TEXT_LIGHT.hexval()[2:]}'>Total Credits</font>", styles['Normal']),
        Paragraph(f"<b>{params.get('hours', 15)}</b><br/><font size=7 color='#{TEXT_LIGHT.hexval()[2:]}'>Hrs/Week</font>", styles['Normal']),
    ]]

    col_w = page_width / 4
    stats_table = Table(stats_data, colWidths=[col_w]*4)
    stats_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_DARK),
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('LINEAFTER', (0, 0), (-2, -1), 0.5, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 6*mm))

    # ── Separator ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=4*mm))

    # ── Semesters ────────────────────────────────────────────────
    for sem in semesters:
        sem_num = sem.get('number', 0)
        sem_color = SEMESTER_COLORS[(sem_num - 1) % len(SEMESTER_COLORS)]

        sem_elements = []

        # Semester header bar
        sem_elements.append(ColoredBar(sem_color, page_width, 3))
        sem_elements.append(Spacer(1, 2*mm))
        sem_elements.append(Paragraph(
            f"<font color='#{sem_color.hexval()[2:]}'>SEMESTER {sem_num}</font> — {sem.get('title', '')}",
            styles['SemesterHeader']
        ))
        sem_elements.append(Spacer(1, 2*mm))

        # Courses as a horizontal table
        courses = sem.get('courses', [])
        if courses:
            # Build each course as a cell
            course_cells = []
            for course in courses:
                cell_parts = []

                # Course name
                cell_parts.append(Paragraph(
                    f"📘 {course.get('name', 'Untitled')}",
                    styles['CourseName']
                ))

                # Credits + Duration badges
                badge_text = f"<font color='#{PRIMARY.hexval()[2:]}'>{course.get('credits', 3)} Credits</font>  ·  <font color='#{ACCENT_GREEN.hexval()[2:]}'>{course.get('duration', 15)} Weeks</font>"
                cell_parts.append(Paragraph(badge_text, styles['BadgeText']))
                cell_parts.append(Spacer(1, 2*mm))

                # Description
                desc = course.get('description', '')
                if desc:
                    cell_parts.append(Paragraph(desc, styles['CourseDesc']))

                # Topics
                topics = course.get('topics', [])
                if topics:
                    cell_parts.append(Spacer(1, 1*mm))
                    cell_parts.append(Paragraph(
                        "<font color='#94a3b8'><b>TOPICS:</b></font>",
                        ParagraphStyle('TopicLabel', fontName='Helvetica-Bold', fontSize=7, textColor=TEXT_LIGHT, leading=10, spaceAfter=2)
                    ))
                    for j, topic in enumerate(topics, 1):
                        cell_parts.append(Paragraph(
                            f"<font color='#{sem_color.hexval()[2:]}'>•</font> {topic}",
                            styles['TopicText']
                        ))

                course_cells.append(cell_parts)

            # Build table — up to 3 columns
            num_cols = min(len(course_cells), 3)
            col_width = (page_width - (num_cols - 1) * 3*mm) / num_cols

            # Pad to fill columns if needed
            while len(course_cells) % num_cols != 0:
                course_cells.append([Paragraph("", styles['Normal'])])

            # Create rows
            rows = []
            for i in range(0, len(course_cells), num_cols):
                rows.append(course_cells[i:i+num_cols])

            course_table = Table(rows, colWidths=[col_width]*num_cols, hAlign='LEFT')
            course_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
                ('BACKGROUND', (0, 0), (-1, -1), white),
            ]))
            sem_elements.append(course_table)

        sem_elements.append(Spacer(1, 6*mm))
        story.append(KeepTogether(sem_elements))

    # ── Agent Review (if provided) ───────────────────────────────
    # Not included in PDF since it's internal quality check

    # ── Footer ───────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=4*mm, spaceAfter=4*mm))
    story.append(Paragraph(
        "Generated by CurricuForge · Powered by IBM Granite 3.3 2B · AI-powered curriculum design",
        styles['FooterText']
    ))

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
