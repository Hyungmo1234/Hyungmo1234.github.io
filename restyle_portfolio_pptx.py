"""기존 포트폴리오 PPT의 글은 두고, 장 번호와 색·장식만 바꾼다."""

from __future__ import annotations

import re
from copy import deepcopy

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt
from pptx.enum.text import PP_ALIGN

SRC = r"C:\Users\LT-013\chkAPJ\양형모_포트폴리오.pptx"

NAVY = RGBColor(0x1B, 0x2A, 0x41)
NAVY_SOFT = RGBColor(0x2E, 0x4A, 0x6E)
COPPER = RGBColor(0xC4, 0x6A, 0x3A)
BG = RGBColor(0xF3, 0xF5, 0xF7)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
STRIPE = RGBColor(0xE4, 0xE9, 0xEF)
INK = RGBColor(0x14, 0x18, 0x20)
MUTED = RGBColor(0x5A, 0x62, 0x70)
LINE = RGBColor(0xC9, 0xD0, 0xD8)
FOOT = RGBColor(0xE8, 0xEC, 0xF0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x12, 0x16, 0x1C)
PAGE_RE = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")


def set_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    try:
        shape.line.fill.background()
    except Exception:
        pass


def set_line(shape, color, pt=0.75):
    shape.line.color.rgb = color
    shape.line.width = Pt(pt)


def fill_rgb(shape):
    try:
        return str(shape.fill.fore_color.rgb)
    except Exception:
        return ""


def set_run_color(run, color):
    run.font.color.rgb = color


def restyle_text(shape, *, dark_slide=False):
    if not shape.has_text_frame:
        return
    for p in shape.text_frame.paragraphs:
        for run in p.runs:
            try:
                cur = str(run.font.color.rgb)
            except Exception:
                cur = ""
            if dark_slide:
                if cur in {"C9A227", "C5D4CE"}:
                    set_run_color(run, COPPER)
                elif cur in {"F3EFE7", "FFFFFF"}:
                    set_run_color(run, WHITE)
                elif cur in {"215C4A", "1C3D38"}:
                    set_run_color(run, COPPER)
            else:
                if cur == "215C4A":
                    set_run_color(run, NAVY_SOFT)
                elif cur == "C9A227":
                    set_run_color(run, COPPER)
                elif cur == "6B655C":
                    set_run_color(run, MUTED)
                elif cur == "1F1B16":
                    set_run_color(run, INK)


def add_page_number(slide, page, total, dark=False):
    box = slide.shapes.add_textbox(Emu(10607040), Emu(6602040), Emu(1188360), Emu(255600))
    tf = box.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = f"{page} / {total}"
    run.font.size = Pt(10)
    run.font.name = "Malgun Gothic"
    run.font.color.rgb = WHITE if dark else MUTED
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = etree.SubElement(rPr, qn("a:ea"))
    ea.set("typeface", "Malgun Gothic")


def main():
    prs = Presentation(SRC)
    total = len(prs.slides)
    sw, sh = prs.slide_width, prs.slide_height

    for idx, slide in enumerate(prs.slides, 1):
        dark = False
        has_page = False
        for shape in list(slide.shapes):
            w, h, x, y = shape.width, shape.height, shape.left, shape.top
            color = fill_rgb(shape)
            text = shape.text_frame.text if shape.has_text_frame else ""

            if color == "1C3D38" and w > sw * 0.9 and h > sh * 0.8:
                dark = True
                set_fill(shape, DARK)
                continue
            if color == "F3EFE7" and w > sw * 0.9:
                set_fill(shape, BG)
                continue
            if color == "1C3D38" and y > Emu(6400000) and w > sw * 0.9:
                set_fill(shape, FOOT)
                continue
            if color in {"215C4A", "C9A227"} and w < Emu(200000) and h > sh * 0.8:
                # 왼쪽 세로띠 → 위쪽 얇은 라인
                shape.left = 0
                shape.top = 0
                shape.width = sw
                shape.height = Emu(54000)
                set_fill(shape, COPPER if dark or color == "C9A227" else NAVY)
                continue
            if color == "FFFCF8":
                set_fill(shape, CARD)
                set_line(shape, LINE, 0.75)
                continue
            if color == "EBE4D8":
                set_fill(shape, STRIPE)
                continue

            if PAGE_RE.match(text.strip()):
                has_page = True
                for p in shape.text_frame.paragraphs:
                    for run in p.runs:
                        run.text = f"{idx} / {total}"
                        set_run_color(run, MUTED)
                continue

            restyle_text(shape, dark_slide=dark)
            if y > Emu(6400000) and text.strip() and not dark:
                for p in shape.text_frame.paragraphs:
                    for run in p.runs:
                        set_run_color(run, MUTED)

        if not has_page:
            add_page_number(slide, idx, total, dark=dark)

    prs.save(SRC)
    print("saved", SRC, "slides", total)


if __name__ == "__main__":
    main()
