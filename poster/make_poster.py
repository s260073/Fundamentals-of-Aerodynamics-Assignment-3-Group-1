#!/usr/bin/env python3
"""
A1 Scientific Poster — 46110 Fundamentals of Aerodynamics, DTU Spring 2026
Mars UAV Aerodynamic Design: Ingenuity Legacy
Group 1: Søren Skovborg, Andrea Luigi Scardino, Christopher Brown
"""

import os
from reportlab.lib.pagesizes import A1
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

# ── PATHS ─────────────────────────────────────────────────────────────────────
HERE        = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR  = os.path.dirname(HERE)
TASK2_DIR   = os.path.join(REPORT_DIR, "Assignment3_Task2")
TASK3_DIR   = os.path.join(REPORT_DIR, "Assignment3_Task3")
TASK4_DIR   = os.path.join(REPORT_DIR, "Assignment3_Task4")
TASK5_DIR   = os.path.join(REPORT_DIR, "Assignment3_Task5")
TASK6_DIR   = os.path.join(REPORT_DIR, "Assignment3_Task6")
OUTPUT      = os.path.join(HERE, "poster_A1.pdf")

DTU_LOGO    = os.path.join(HERE,       "DTU.png")
IMG_AIRFOIL = os.path.join(TASK5_DIR,  "airfoil_stats.png")
IMG_BEM     = os.path.join(TASK2_DIR,  "bem_results.png")
IMG_BATT    = os.path.join(TASK3_DIR,  "Assignment3_Task3_updated_flight_time_vs_batteries.png")
IMG_SPEED   = os.path.join(TASK6_DIR,  "task6_speed_sweep.png")
IMG_WING    = os.path.join(TASK6_DIR,  "task6_wing_sweep_zoom.png")
IMG_OSWALD  = os.path.join(TASK6_DIR,  "task6_llt_oswald.png")

# ── COLORS ────────────────────────────────────────────────────────────────────
RED     = HexColor("#990000")
NAVY    = HexColor("#1C1C55")
LGRAY   = HexColor("#F3F3F6")
MGRAY   = HexColor("#C8C8D0")
DGRAY   = HexColor("#222222")
BGBODY  = HexColor("#FAFAFA")
GOLD    = HexColor("#C8A600")
TBLHDR  = HexColor("#2A2A5A")

# ── PAGE & LAYOUT ─────────────────────────────────────────────────────────────
PW, PH  = A1                        # 1683.78 × 2383.94 pt
MARG    = 24                        # outer margin
HDRH    = 135                       # header height
FTRBOTT = 28                        # footer height
GUTTER  = 13                        # gap between columns
NCO     = 3                         # number of columns
BDY_TOP = PH - HDRH - 5
BDY_BOT = FTRBOTT + 4
BDY_H   = BDY_TOP - BDY_BOT        # ≈ 2212 pt
AVAIL_W = PW - 2 * MARG
COL_W   = (AVAIL_W - GUTTER * (NCO - 1)) / NCO   # ≈ 538 pt
COL_X   = [MARG + i * (COL_W + GUTTER) for i in range(NCO)]

SEC_TH  = 22    # section title bar height
SEC_PAD = 8     # padding inside section (left/right and top)
GAP     = 9     # gap between sections

# ── COLUMN SECTION HEIGHTS (must sum to BDY_H each) ──────────────────────────
# Column 1: Overview(370) + gap(9) + Task1(320) + gap(9) + Task4(1504) = 2212
C1_H = [370, 320, BDY_H - 370 - GAP - 320 - GAP]   # [370, 320, 1513]

# Column 2: Task2(1090) + gap(9) + Task3(1113) = 2212
C2_H = [1090, BDY_H - 1090 - GAP]                    # [1090, 1113]

# Column 3: Task5(1050) + gap(9) + Task6(800) + gap(9) + Conclusions(344) = 2212
C3_H = [1050, 800, BDY_H - 1050 - GAP - 800 - GAP]  # [1050, 800, 344]


# ══════════════════════════════════════════════════════════════════════════════
# DRAWING UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def section_box(c, x, y_top, w, h, title, hdr_color=NAVY):
    """
    Draw a section box.  Returns y_content — the y-coordinate for the first
    line of content (below title bar, after top padding).
    """
    bx, by = x, y_top - h
    # Body fill
    c.setFillColor(LGRAY)
    c.setStrokeColor(MGRAY)
    c.setLineWidth(0.6)
    c.roundRect(bx, by, w, h, 6, fill=1, stroke=1)
    # Title bar — rounded top, flat bottom
    c.setFillColor(hdr_color)
    c.roundRect(bx, y_top - SEC_TH, w, SEC_TH, 6, fill=1, stroke=0)
    # Flat-bottom overlay for title bar
    c.rect(bx, y_top - SEC_TH, w, SEC_TH // 2, fill=1, stroke=0)
    # Title text
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(bx + 9, y_top - SEC_TH + 6.5, title)
    return y_top - SEC_TH - SEC_PAD


def para(c, html, x, y, w,
         size=10, color=DGRAY, leading=14, align=TA_JUSTIFY,
         font="Helvetica"):
    """Render a Paragraph and return height consumed."""
    sty = ParagraphStyle("s", fontName=font, fontSize=size, textColor=color,
                          leading=leading, alignment=align, wordWrap="LTR")
    p = Paragraph(html, sty)
    _, h = p.wrap(w, 9999)
    p.drawOn(c, x, y - h)
    return h


def rule(c, x, y, w, color=MGRAY, lw=0.5):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x, y, x + w, y)


def fit_image(c, path, x, y_top, max_w, max_h, center=True):
    """Draw image scaled to fit; return actual height drawn."""
    if not os.path.exists(path):
        c.setFillColor(MGRAY)
        c.setStrokeColor(HexColor("#AAAAAA"))
        c.setLineWidth(0.5)
        c.rect(x, y_top - max_h, max_w, max_h, fill=1, stroke=1)
        c.setFillColor(DGRAY)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + max_w / 2, y_top - max_h / 2,
                            "[" + os.path.basename(path) + "]")
        return max_h
    img    = ImageReader(path)
    iw, ih = img.getSize()
    scale  = min(max_w / iw, max_h / ih)
    dw, dh = iw * scale, ih * scale
    dx = x + (max_w - dw) / 2 if center else x
    c.drawImage(path, dx, y_top - dh, dw, dh,
                preserveAspectRatio=True, mask="auto")
    return dh


def highlight_box(c, x, y_top, w, h, bg=HexColor("#FFF5F5"),
                  border=RED, radius=5):
    c.setFillColor(bg)
    c.setStrokeColor(border)
    c.setLineWidth(1.2)
    c.roundRect(x, y_top - h, w, h, radius, fill=1, stroke=1)


def draw_bar_chart(c, x, y_top, w, h, bars, title="", label_size=8):
    """
    Simple horizontal bar chart.
    bars = list of (label, value, color) tuples.
    max value taken from data.
    """
    max_v  = max(v for _, v, _ in bars)
    bar_h  = (h - 20) / len(bars)
    pad    = 4
    lw     = 110  # label area width
    bw_max = w - lw - 10  # bar area width

    if title:
        c.setFont("Helvetica-Bold", label_size)
        c.setFillColor(DGRAY)
        c.drawString(x, y_top, title)

    for i, (lbl, val, col) in enumerate(bars):
        by  = y_top - 18 - i * bar_h
        bw  = bw_max * val / max_v
        # bar
        c.setFillColor(col)
        c.roundRect(x + lw, by - bar_h + pad, bw, bar_h - 2 * pad, 3,
                    fill=1, stroke=0)
        # label
        c.setFont("Helvetica", label_size)
        c.setFillColor(DGRAY)
        c.drawRightString(x + lw - 4, by - bar_h / 2 - 3, lbl)
        # value
        c.setFont("Helvetica-Bold", label_size)
        c.setFillColor(NAVY)
        c.drawString(x + lw + bw + 4, by - bar_h / 2 - 3, f"{val:.0f} W")


def kv_table(c, rows, x, y_top, col_w_label, col_w_value,
             size=9.5, row_h=14):
    """
    Compact label/value table drawn with canvas.
    rows = [(label_html, value_html), ...]
    Returns total height drawn.
    """
    for i, (lbl, val) in enumerate(rows):
        yrow = y_top - i * row_h
        # alternating row shading
        if i % 2 == 0:
            c.setFillColor(HexColor("#EBEBF0"))
            c.rect(x - 2, yrow - row_h + 2, col_w_label + col_w_value + 4,
                   row_h - 1, fill=1, stroke=0)
        h_l = para(c, lbl, x, yrow, col_w_label, size=size, color=DGRAY,
                   leading=row_h, align=TA_LEFT)
        h_v = para(c, val, x + col_w_label, yrow, col_w_value, size=size,
                   color=NAVY, leading=row_h, align=TA_LEFT,
                   font="Helvetica-Bold")
    return len(rows) * row_h


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

def draw_header(c):
    # Background
    c.setFillColor(NAVY)
    c.rect(0, PH - HDRH, PW, HDRH, fill=1, stroke=0)
    # Red accent stripe at bottom of header
    c.setFillColor(RED)
    c.rect(0, PH - HDRH, PW, 5, fill=1, stroke=0)

    # DTU logo (left side)
    logo_max_w, logo_max_h = 160, 80
    if os.path.exists(DTU_LOGO):
        img    = ImageReader(DTU_LOGO)
        iw, ih = img.getSize()
        sc     = min(logo_max_w / iw, logo_max_h / ih)
        dw, dh = iw * sc, ih * sc
        c.drawImage(DTU_LOGO, MARG + 5,
                    PH - HDRH + (HDRH - 5 - dh) / 2,
                    dw, dh, preserveAspectRatio=True, mask="auto")

    # Main title
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(PW / 2, PH - 42,
                        "Aerodynamic Design of a Mars UAV: Ingenuity Legacy")

    # Subtitle
    c.setFont("Helvetica", 16)
    c.setFillColor(HexColor("#DDDDDD"))
    c.drawCentredString(PW / 2, PH - 67,
                        "46110 Fundamentals of Aerodynamics  —  DTU, Spring 2026")

    # Thin separator
    c.setStrokeColor(RED)
    c.setLineWidth(1.2)
    c.line(PW / 2 - 350, PH - 76, PW / 2 + 350, PH - 76)

    # Authors
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(white)
    c.drawCentredString(PW / 2, PH - 95,
        "Søren Skovborg   ·   Andrea Luigi Scardino   ·   Christopher Brown   —   Group 1")

    # Right: exam info
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#BBBBBB"))
    c.drawRightString(PW - MARG - 5, PH - 50, "Exam: Wednesday 27 May 2026")
    c.drawRightString(PW - MARG - 5, PH - 63, "Building 403, Room 211")
    c.drawRightString(PW - MARG - 5, PH - 76, "DTU — Technical University of Denmark")


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════

def draw_footer(c):
    c.setFillColor(NAVY)
    c.rect(0, 0, PW, FTRBOTT, fill=1, stroke=0)
    c.setFillColor(RED)
    c.rect(0, FTRBOTT - 4, PW, 4, fill=1, stroke=0)
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#BBBBBB"))
    c.drawCentredString(PW / 2, 8,
        "46110 Fundamentals of Aerodynamics  ·  DTU Spring 2026  ·  Group 1  "
        "·  Mars UAV: Ingenuity Legacy")


# ══════════════════════════════════════════════════════════════════════════════
# COLUMN 1
# ══════════════════════════════════════════════════════════════════════════════

def draw_col1(c):
    x, w  = COL_X[0], COL_W
    y     = BDY_TOP
    inner = w - 2 * SEC_PAD   # content width inside section

    # ── SECTION A: PROJECT OVERVIEW ──────────────────────────────────────────
    sec_h = C1_H[0]
    yi = section_box(c, x, y, w, sec_h,
                     "Project Overview & Motivation", hdr_color=RED)

    h = para(c, (
        "On <b>19 April 2021</b>, NASA's Ingenuity helicopter made history as the "
        "<b>first powered aircraft to fly on another planet</b>. Weighing just 1.8 kg, "
        "it completed 72 flights — far exceeding its initial 5-flight goal — before a "
        "rotor failure ended its mission on 18 January 2024."
    ), x + SEC_PAD, yi, inner, size=10, leading=14)
    yi -= h + 7

    h = para(c, (
        "This project designs the <b>next-generation Mars UAV</b>: a rotorcraft capable "
        "of carrying a <b>2 kg payload</b> within the constraints of the thin Martian "
        "atmosphere. The full design chain is covered — from first-principles power "
        "estimation and configuration selection, through airfoil choice and blade "
        "optimisation, to forward-flight wing analysis."
    ), x + SEC_PAD, yi, inner, size=10, leading=14)
    yi -= h + 10

    rule(c, x + SEC_PAD, yi, inner)
    yi -= 8

    # Mars vs Earth: compact two-column facts
    h = para(c, "<b>Key Martian conditions used throughout:</b>",
             x + SEC_PAD, yi, inner, size=10, leading=14, align=TA_LEFT)
    yi -= h + 4

    facts = [
        ("Atmospheric density", "ρ = 0.020 kg/m³", "Gravitational acc.", "g = 3.73 m/s²"),
        ("Dynamic viscosity",   "µ = 1.05×10⁻⁵ Pa·s", "Pressure (avg.)",   "~600–700 Pa"),
        ("vs Earth density",    "0.020/1.225 ≈ 1.6%",   "vs Earth gravity",  "3.73/9.81 ≈ 38%"),
    ]
    half = inner / 2 - 4
    for row in facts:
        lbl1, val1, lbl2, val2 = row
        h1 = para(c, f"<b>{lbl1}:</b>  {val1}",
                  x + SEC_PAD, yi, half, size=9, leading=13, align=TA_LEFT)
        h2 = para(c, f"<b>{lbl2}:</b>  {val2}",
                  x + SEC_PAD + half + 8, yi, half, size=9, leading=13, align=TA_LEFT)
        yi -= max(h1, h2) + 1

    yi -= 10

    # Design goals highlight
    hbox_h = 70
    highlight_box(c, x + SEC_PAD, yi, inner, hbox_h, bg=HexColor("#FFF4F4"))
    para(c, "<b>Design objectives:</b>",
         x + SEC_PAD + 8, yi - 12, inner - 16, size=10,
         color=RED, align=TA_LEFT, leading=13)
    goals = [
        "Carry 2 kg payload in Martian hover and forward flight",
        "Compare twin-rotor vs. quadcopter configurations",
        "Select optimal airfoil for Re ≈ 1.8 × 10<super>4</super>",
        "Evaluate fixed-wing benefit in forward flight",
    ]
    gy = yi - 24
    for g in goals:
        gh = para(c, f"• {g}", x + SEC_PAD + 8, gy, inner - 16,
                  size=9, color=NAVY, leading=13, align=TA_LEFT)
        gy -= gh + 1

    y -= sec_h + GAP

    # ── SECTION B: TASK 1 — INGENUITY POWER ─────────────────────────────────
    sec_h = C1_H[1]
    yi = section_box(c, x, y, w, sec_h,
                     "Task 1 — Ingenuity Power Reference", hdr_color=NAVY)

    h = para(c, (
        "Momentum theory applied to Ingenuity's <b>coaxial counter-rotating</b> "
        "rotor system (m = 1.8 kg, R = 0.6 m, Ω = 2800 rpm). The lower rotor "
        "operates in the wake of the upper rotor (interference factor f = 0.5)."
    ), x + SEC_PAD, yi, inner, size=10, leading=14)
    yi -= h + 8

    # Power breakdown bar chart
    chart_h = 90
    draw_bar_chart(c, x + SEC_PAD, yi, inner, chart_h,
                   bars=[
                       ("Upper rotor", 56.4, RED),
                       ("Lower rotor", 43.7, NAVY),
                       ("Total system", 100.1, GOLD),
                   ],
                   title="Rotor power breakdown [W]", label_size=9)
    yi -= chart_h + 12

    rule(c, x + SEC_PAD, yi, inner)
    yi -= 7

    kv_rows = [
        ("Induced velocity (upper):", "v<sub>i,u</sub> = 8.61 m/s"),
        ("Induced velocity (lower):", "v<sub>i,l</sub> = 5.32 m/s"),
        ("Profile power per rotor:",  "P₀ = 23.1 W"),
        ("Upper rotor power:",        "P<sub>u</sub> = 56.4 W"),
        ("Lower rotor power:",        "P<sub>l</sub> = 43.7 W"),
        ("Total rotor power:",        "<b>P<sub>tot</sub> ≈ 100 W</b>"),
    ]
    kv_table(c, kv_rows, x + SEC_PAD, yi,
             col_w_label=inner * 0.55, col_w_value=inner * 0.42)
    yi -= len(kv_rows) * 14 + 6

    h = para(c, (
        "<i>Note: real Ingenuity peaks at ≈360 W — this simplified model "
        "underestimates total system power but establishes a valid design baseline.</i>"
    ), x + SEC_PAD, yi, inner, size=8.5, color=HexColor("#555555"),
             leading=12, align=TA_LEFT)

    y -= sec_h + GAP

    # ── SECTION C: TASK 4 — AIRFOIL SELECTION ───────────────────────────────
    sec_h = C1_H[2]
    yi = section_box(c, x, y, w, sec_h,
                     "Task 4 — Airfoil Selection for Low-Re Martian Flight",
                     hdr_color=NAVY)

    # Re analysis
    h = para(c, "<b>Reynolds number analysis</b>  "
             "(same velocity V, same chord c — varying only ρ and µ):",
             x + SEC_PAD, yi, inner, size=10, leading=14, align=TA_LEFT)
    yi -= h + 4

    re_rows = [
        ("Re<sub>Mars</sub> / Re<sub>Earth</sub> :", "≈ 0.028  →  36× lower on Mars"),
        ("Re at r = 0.75R  (Ingenuity):",
         "Re = ρ V c / µ  =  (0.020)(133)(0.071) / 1.05×10<super>−5</super>  ≈ <b>1.8×10<super>4</super></b>"),
        ("Flow regime:", "Very-low-Re — viscous forces dominant, early separation likely"),
    ]
    kv_table(c, re_rows, x + SEC_PAD, yi,
             col_w_label=inner * 0.45, col_w_value=inner * 0.52, size=9, row_h=15)
    yi -= len(re_rows) * 15 + 8

    rule(c, x + SEC_PAD, yi, inner)
    yi -= 8

    h = para(c, "<b>Candidate airfoils</b> — selected from NASA Mars rotorcraft literature:",
             x + SEC_PAD, yi, inner, size=10, leading=14, align=TA_LEFT)
    yi -= h + 3

    candidates = [
        ("<b>ROAMX-0201</b>",
         "Mars-optimised thin cambered profile — highest C<sub>l,max</sub> &gt; 1.3, "
         "smooth stable polar; specifically designed for Martian Re conditions."),
        ("<b>CLF5605</b>",
         "Ingenuity flight-proven baseline — lower lift, higher drag than ROAMX; "
         "practical structural compromise."),
        ("<b>5% circular-arc plate</b>",
         "Simple thin profile — robust laminar behaviour at very low Re; "
         "slightly lower C<sub>l,max</sub> than ROAMX."),
    ]
    for name, desc in candidates:
        h = para(c, f"{name}: {desc}",
                 x + SEC_PAD + 4, yi, inner - 4, size=9.5, leading=13.5,
                 align=TA_LEFT)
        yi -= h + 3

    yi -= 6

    # Airfoil polars image
    avail_img = yi - (y - sec_h) - 55
    img_h = min(avail_img, 560)
    act_h = fit_image(c, IMG_AIRFOIL, x + SEC_PAD / 2, yi,
                      w - SEC_PAD, img_h)
    yi -= act_h + 4

    h = para(c, (
        "<i>Fig. 1 — C<sub>l</sub> vs α and C<sub>l</sub> vs C<sub>d</sub> polars "
        "for the three candidate airfoils at Re ≈ 1.8×10<super>4</super> "
        "(data from NASA literature).</i>"
    ), x + SEC_PAD, yi, inner, size=8.5, color=HexColor("#555555"),
             leading=11.5, align=TA_CENTER)
    yi -= h + 6

    # Selection result
    sel_h = 48
    highlight_box(c, x + SEC_PAD, yi, inner, sel_h,
                  bg=HexColor("#F5FFF5"), border=HexColor("#007700"))
    para(c, "&#10003;  <b>ROAMX-0201 selected</b> — highest lift capability, "
         "smooth stall, and purpose-optimised for very-low-Re Martian conditions.  "
         "No turbulator required for the conceptual design phase.",
         x + SEC_PAD + 7, yi - 6, inner - 14, size=9.5,
         color=HexColor("#004400"), leading=13.5, align=TA_LEFT)


# ══════════════════════════════════════════════════════════════════════════════
# COLUMN 2
# ══════════════════════════════════════════════════════════════════════════════

def draw_col2(c):
    x, w  = COL_X[1], COL_W
    y     = BDY_TOP
    inner = w - 2 * SEC_PAD

    # ── SECTION A: TASK 2 — CONCEPTUAL DESIGN ───────────────────────────────
    sec_h = C2_H[0]
    yi = section_box(c, x, y, w, sec_h,
                     "Task 2 — Conceptual Design & Configuration Selection",
                     hdr_color=RED)

    h = para(c, (
        "Two configurations evaluated for 2 kg payload capacity. Mass model scales "
        "Ingenuity's component weights with rotor radius, blade count, and power. "
        "Optimal rotor radius found by minimising total hover power subject to "
        "the coupled mass–power system."
    ), x + SEC_PAD, yi, inner, size=10, leading=14)
    yi -= h + 10

    # Comparison table
    tdata = [
        ["Parameter",              "Twin-Rotor Helicopter", "Quadcopter ✓"],
        ["Number of rotors",        "2",                     "4"],
        ["Rotor radius",            "0.69 m",                "0.59 m"],
        ["Blades per rotor",        "2",                     "2"],
        ["Total mass (w/ payload)", "≈ 4.4 kg",              "≈ 2.5 kg"],
        ["Total hover power",       "197.3 W",               "105.4 W"],
        ["Flight time (hover)",     "6.1 min",               "11.4 min"],
    ]
    cws = [inner * 0.40, inner * 0.30, inner * 0.30]
    tbl = Table(tdata, colWidths=cws)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), TBLHDR),
        ("TEXTCOLOR",    (0, 0), (-1, 0), white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9.5),
        ("BACKGROUND",   (2, 1), (2, -1), HexColor("#FFF0F0")),
        ("BACKGROUND",   (0, 1), (0, -1), HexColor("#F0F4FA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#F7F7FA")]),
        ("GRID",         (0, 0), (-1, -1), 0.4, MGRAY),
        ("ALIGN",        (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("FONTNAME",     (2, 5), (2, 6), "Helvetica-Bold"),
        ("TEXTCOLOR",    (2, 5), (2, 6), RED),
    ]))
    tw, th = tbl.wrap(inner, 600)
    tbl.drawOn(c, x + SEC_PAD, yi - th)
    yi -= th + 10

    h = para(c, (
        "The <b>quadcopter is selected</b>: 47% lower total power and 87% longer "
        "hover endurance than the twin-rotor configuration. Additional rotors allow "
        "a smaller optimal radius per rotor, improving aerodynamic efficiency."
    ), x + SEC_PAD, yi, inner, size=10, leading=14)
    yi -= h + 10

    # Power comparison chart
    chart_h = 85
    draw_bar_chart(c, x + SEC_PAD, yi, inner, chart_h,
                   bars=[
                       ("Twin-rotor (2R)", 197.3, HexColor("#AA3333")),
                       ("Quadcopter (4R)", 105.4, HexColor("#224488")),
                   ],
                   title="Total hover power comparison", label_size=9)
    yi -= chart_h + 12

    # Selected design highlight box
    hbh = 72
    highlight_box(c, x + SEC_PAD, yi, inner, hbh, bg=HexColor("#F8F0FF"),
                  border=NAVY)
    para(c, "<b>Selected quadcopter design parameters:</b>",
         x + SEC_PAD + 8, yi - 13, inner - 16, size=10,
         color=NAVY, align=TA_LEFT, leading=14)
    dp_h = para(c, (
        "N<sub>rot</sub> = 4  ·  R = 0.59 m  ·  N<sub>b</sub> = 2  ·  "
        "Ω = 2800 rpm  ·  c̄ = 0.071 m  ·  P<sub>hover</sub> = 105.4 W"
    ), x + SEC_PAD + 8, yi - 30, inner - 16, size=11,
               color=RED, align=TA_CENTER, leading=15, font="Helvetica-Bold")
    yi -= hbh + 10

    rule(c, x + SEC_PAD, yi, inner)
    yi -= 8

    # Power equation summary
    h = para(c, "<b>Governing equations:</b>", x + SEC_PAD, yi, inner,
             size=10, leading=14, align=TA_LEFT)
    yi -= h + 3

    eqns = [
        ("Induced power:",
         "P<sub>i</sub> = √(51.895 m<sub>tot</sub><super>3</super> / "
         "(2 N<sub>rot</sub><super>2</super> ρ π R<super>2</super>))"),
        ("Profile power:",
         "P₀ = ⅛ ρ c̄ N<sub>b</sub> C<sub>d0</sub> Ω<super>3</super> R<super>4</super>  =  178.7 R<super>4</super>  [W]"),
        ("Total power:",
         "P<sub>tot</sub> = κ P<sub>i</sub> + P₀  (κ = 1.15, C<sub>d0</sub> = 0.02)"),
        ("Mass model:",
         "m<sub>tot</sub> = 1.2(1500 + 29.2·R·N<sub>b</sub>·N<sub>rot</sub> + 2.5·P<sub>tot</sub>)  [g]"),
    ]
    for lbl, eq in eqns:
        h = para(c, f"<b>{lbl}</b>  {eq}",
                 x + SEC_PAD + 3, yi, inner - 3, size=9, leading=13,
                 align=TA_LEFT)
        yi -= h + 2

    y -= sec_h + GAP

    # ── SECTION B: TASK 3 — BATTERY OPTIMIZATION ────────────────────────────
    sec_h = C2_H[1]
    yi = section_box(c, x, y, w, sec_h,
                     "Task 3 — Battery Optimisation & Extended Flight Time",
                     hdr_color=NAVY)

    h = para(c, (
        "Payload (2 kg) replaced with additional battery cells "
        "(m<sub>cell</sub> = 47 g, E<sub>cell</sub> = 10/6 Wh). "
        "Two competing effects: more batteries → more energy <i>and</i> more mass "
        "→ higher power demand. The net effect determines the optimal count."
    ), x + SEC_PAD, yi, inner, size=10, leading=14)
    yi -= h + 6

    # Flight-time vs battery count plot
    avail_img = yi - (y - sec_h) - 150
    img_h = min(avail_img, 520)
    act_h = fit_image(c, IMG_BATT, x + SEC_PAD / 2, yi,
                      w - SEC_PAD, img_h)
    yi -= act_h + 4

    h = para(c, (
        "<i>Fig. 2 — Flight time vs. number of extra battery cells. "
        "Energy benefit dominates over mass penalty across the full 0–42 cell range.</i>"
    ), x + SEC_PAD, yi, inner, size=8.5, color=HexColor("#555555"),
             leading=11.5, align=TA_CENTER)
    yi -= h + 10

    rule(c, x + SEC_PAD, yi, inner)
    yi -= 8

    # Results table
    res_rows = [
        ("Baseline flight time (original battery only):",
         "≈ 26.6 min"),
        ("Maximum allowed extra batteries  (2 kg payload limit):",
         "N<sub>max</sub> = ⌊2/0.047⌋ = <b>42</b>"),
        ("Total added battery mass:",
         "42 × 47 g = 1.97 kg  &lt; 2 kg  ✓"),
        ("Maximum flight time  (N = 42):",
         "<b>t<sub>max</sub> ≈ 51.7 min</b>  (+94%)"),
        ("Total aircraft mass at optimum:",
         "m<sub>tot</sub> = 4.52 kg"),
        ("Hover power at optimum:",
         "P<sub>tot</sub> = 104.5 W"),
    ]
    kv_table(c, res_rows, x + SEC_PAD, yi,
             col_w_label=inner * 0.60, col_w_value=inner * 0.37,
             size=9.5, row_h=16)
    yi -= len(res_rows) * 16 + 8

    h = para(c, (
        "In this configuration the optimal solution is at the payload mass limit: "
        "energy grows linearly with battery count while power grows sub-linearly, "
        "so adding batteries always improves endurance up to the maximum allowed mass."
    ), x + SEC_PAD, yi, inner, size=9.5, color=HexColor("#444444"), leading=13.5)


# ══════════════════════════════════════════════════════════════════════════════
# COLUMN 3
# ══════════════════════════════════════════════════════════════════════════════

def draw_col3(c):
    x, w  = COL_X[2], COL_W
    y     = BDY_TOP
    inner = w - 2 * SEC_PAD

    # ── SECTION A: TASK 5 — BEM ROTOR DESIGN ────────────────────────────────
    sec_h = C3_H[0]
    yi = section_box(c, x, y, w, sec_h,
                     "Task 5 — Detailed Rotor Design via BEM Theory", hdr_color=RED)

    h = para(c, (
        "Blade Element Momentum theory with Prandtl tip-loss correction "
        "simultaneously optimises <b>tip chord, design AoA, collective pitch, and Ω</b> "
        "to minimise rotor power for the required thrust. "
        "Optimiser: Nelder-Mead (SciPy) with 50 radial elements."
    ), x + SEC_PAD, yi, inner, size=10, leading=14)
    yi -= h + 6

    # BEM result plot
    avail_img = yi - (y - sec_h) - 200
    img_h = min(avail_img, 480)
    act_h = fit_image(c, IMG_BEM, x + SEC_PAD / 2, yi,
                      w - SEC_PAD, img_h)
    yi -= act_h + 4

    h = para(c, (
        "<i>Fig. 3 — BEM optimised blade: chord distribution, total pitch & local AoA, "
        "spanwise thrust loading dC<sub>T</sub>/dy, and power loading dC<sub>P</sub>/dy.</i>"
    ), x + SEC_PAD, yi, inner, size=8.5, color=HexColor("#555555"),
             leading=11.5, align=TA_CENTER)
    yi -= h + 8

    rule(c, x + SEC_PAD, yi, inner)
    yi -= 7

    # Model comparison table
    tdata2 = [
        ["Quantity",                 "Momentum Theory\n(Task 2)", "BEM\n(Task 5)"],
        ["Method",                   "Actuator disk",              "Blade element + momentum"],
        ["Hover power per rotor",    "26.4 W",                     "107.7 W"],
        ["Total quadcopter power",   "105.4 W",                    "430.8 W"],
        ["Thrust per rotor",         "—",                          "4.27 N  ✓"],
        ["Figure of merit (FM)",     "—",                          "optimised"],
    ]
    cws2 = [inner * 0.38, inner * 0.31, inner * 0.31]
    tbl2 = Table(tdata2, colWidths=cws2)
    tbl2.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), TBLHDR),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("GRID",          (0, 0), (-1, -1), 0.4, MGRAY),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#F7F7FA")]),
        ("FONTNAME",      (2, 2), (2, 4), "Helvetica-Bold"),
        ("TEXTCOLOR",     (2, 2), (2, 4), RED),
    ]))
    _, th2 = tbl2.wrap(inner, 400)
    tbl2.drawOn(c, x + SEC_PAD, yi - th2)
    yi -= th2 + 7

    h = para(c, (
        "BEM power is <b>~4× higher</b> than the simplified momentum estimate "
        "due to tip losses, hub losses, and profile drag not captured by actuator-disk "
        "theory. The hyperbolic chord distribution and high twist at the root "
        "deliver required thrust with minimum power."
    ), x + SEC_PAD, yi, inner, size=9.5, color=HexColor("#444444"), leading=13.5)

    y -= sec_h + GAP

    # ── SECTION B: TASK 6 — FORWARD FLIGHT ──────────────────────────────────
    sec_h = C3_H[1]
    yi = section_box(c, x, y, w, sec_h,
                     "Task 6 — Forward Flight & Wing Integration",
                     hdr_color=NAVY)

    h = para(c, (
        "Forward flight at V = 10 m/s modelled with <b>Glauert momentum theory</b>. "
        "Fixed wing assessed via <b>Lifting Line Theory</b> (LLT) sweeping AR ∈ {5, 7, 9}, "
        "taper λ, and geometric washout θ<sub>tip</sub>."
    ), x + SEC_PAD, yi, inner, size=10, leading=14)
    yi -= h + 5

    # Key dynamic pressure box
    dp_h = 32
    highlight_box(c, x + SEC_PAD, yi, inner, dp_h,
                  bg=HexColor("#FFF4E0"), border=GOLD)
    para(c, "Mars dynamic pressure at V = 10 m/s:  "
         "<b>q = ½ρV<super>2</super> = 1.0 Pa</b>  "
         "— approximately <b>60× lower</b> than on Earth at the same speed.",
         x + SEC_PAD + 7, yi - 6, inner - 14, size=9.5,
         color=HexColor("#6A4000"), align=TA_CENTER, leading=13)
    yi -= dp_h + 7

    # Wing sweep image (zoomed)
    avail1 = yi - (y - sec_h) - 240
    img_h1 = min(avail1, 280)
    act_h1 = fit_image(c, IMG_WING, x + SEC_PAD / 2, yi,
                       w - SEC_PAD, img_h1)
    yi -= act_h1 + 3

    h = para(c, (
        "<i>Fig. 4 — Total rotor power vs. wingspan (zoomed). "
        "Maximum achievable reduction: <b>0.09%</b>. "
        "Dots mark optimal wingspan per AR.</i>"
    ), x + SEC_PAD, yi, inner, size=8.5, color=HexColor("#555555"),
             leading=11.5, align=TA_CENTER)
    yi -= h + 6

    # Speed sweep image
    avail2 = yi - (y - sec_h) - 90
    img_h2 = min(avail2, 230)
    if img_h2 > 50:
        act_h2 = fit_image(c, IMG_SPEED, x + SEC_PAD / 2, yi,
                           w - SEC_PAD, img_h2)
        yi -= act_h2 + 3
        h = para(c, (
            "<i>Fig. 5 — Total power & rotor tilt angle β vs. flight speed "
            "(0–12 m/s). Power dips below hover at low speeds "
            "(translational lift effect).</i>"
        ), x + SEC_PAD, yi, inner, size=8.5, color=HexColor("#555555"),
                 leading=11.5, align=TA_CENTER)
        yi -= h + 6

    # Wing results summary
    wing_rows = [
        ("Forward-flight power (no wing, V=10 m/s):", "<b>234.4 W</b>"),
        ("LLT-optimal planform:", "Rectangular, AR=9, λ=1, θ<sub>tip</sub>=−3°, e=0.988"),
        ("Best achievable power reduction:", "<b>0.09%</b>  (vs 10% target)"),
        ("Density needed for 10% reduction:", "ρ<sub>w</sub> ≤ 7.0 kg/m³  (unachievable)"),
        ("Final design decision:", "<b>No fixed wing added</b>"),
    ]
    kv_table(c, wing_rows, x + SEC_PAD, yi,
             col_w_label=inner * 0.52, col_w_value=inner * 0.46,
             size=9, row_h=15)

    y -= sec_h + GAP

    # ── SECTION C: CONCLUSIONS ───────────────────────────────────────────────
    sec_h = C3_H[2]
    yi = section_box(c, x, y, w, sec_h,
                     "Conclusions", hdr_color=RED)

    conclusions = [
        ("Task 1",
         "Ingenuity total rotor power <b>≈ 100 W</b> by momentum theory  "
         "(50 W per coaxial rotor)."),
        ("Task 2",
         "Quadcopter selected — <b>47% lower power</b> (105.4 W vs 197.3 W) "
         "and <b>87% longer flight time</b> than twin-rotor."),
        ("Task 3",
         "<b>42 extra batteries → 51.7 min</b> flight time, up from 26.6 min "
         "(+94%). Optimal solution is at the payload mass limit."),
        ("Task 4",
         "Re<sub>Mars</sub> ≈ 1.8×10<super>4</super>  (36× lower than Earth).  "
         "<b>ROAMX-0201</b> selected for highest C<sub>l,max</sub> and low-Re stability."),
        ("Task 5",
         "BEM gives <b>107.7 W/rotor</b> — ~4× the momentum estimate — due to "
         "tip &amp; profile losses not captured in the simplified model."),
        ("Task 6",
         "Wings are impractical on Mars (q = 1.0 Pa). Max reduction <b>0.09%</b>.  "
         "Final design: bare quadcopter, P<sub>fwd</sub> = 234.4 W at 10 m/s."),
    ]

    for lbl, txt in conclusions:
        # Coloured label chip
        lbl_w = 52
        c.setFillColor(NAVY)
        c.roundRect(x + SEC_PAD, yi - 15, lbl_w, 16, 3, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(white)
        c.drawCentredString(x + SEC_PAD + lbl_w / 2, yi - 11, lbl)
        h = para(c, txt, x + SEC_PAD + lbl_w + 5, yi, inner - lbl_w - 5,
                 size=9.5, leading=13.5, align=TA_LEFT)
        yi -= max(h, 16) + 5


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    c = rl_canvas.Canvas(OUTPUT, pagesize=A1)
    c.setAuthor("Group 1 — DTU 46110 Aerodynamics")
    c.setTitle("Aerodynamic Design of a Mars UAV: Ingenuity Legacy")

    # Page background
    c.setFillColor(BGBODY)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)

    # Column background strips (subtle alternating shading)
    for i in range(NCO):
        shade = HexColor("#F6F6F9") if i % 2 == 0 else HexColor("#F0F0F4")
        c.setFillColor(shade)
        c.rect(COL_X[i] - 2, BDY_BOT, COL_W + 4, BDY_H, fill=1, stroke=0)

    draw_header(c)
    draw_footer(c)
    draw_col1(c)
    draw_col2(c)
    draw_col3(c)

    c.save()
    print(f"Poster saved to:\n  {OUTPUT}")


if __name__ == "__main__":
    main()
