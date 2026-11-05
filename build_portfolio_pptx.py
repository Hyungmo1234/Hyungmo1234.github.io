"""양형모 포트폴리오 PPT. 이력서·프로젝트 모음에 적힌 사실만 넣는다."""

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree

W = Inches(13.333)
H = Inches(7.5)

INK = RGBColor(0x1F, 0x1B, 0x16)
CREAM = RGBColor(0xF3, 0xEF, 0xE7)
PAPER = RGBColor(0xFF, 0xFC, 0xF8)
FOREST = RGBColor(0x21, 0x5C, 0x4A)
FOREST_DEEP = RGBColor(0x1C, 0x3D, 0x38)
MUTED = RGBColor(0x6B, 0x65, 0x5C)
LINE = RGBColor(0xDD, 0xD6, 0xCB)
GOLD = RGBColor(0xC9, 0xA2, 0x27)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Malgun Gothic"
OUT = r"C:\Users\LT-013\chkAPJ\양형모_포트폴리오.pptx"


def set_run(run, size, color, bold=False, font=FONT):
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = font
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = etree.SubElement(rPr, qn("a:ea"))
    ea.set("typeface", font)


def add_textbox(slide, l, t, w, h, text, size, color, bold=False, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_run(run, size, color, bold)
    return box


def add_para(tf, text, size, color, bold=False, space_before=6, space_after=0):
    p = tf.add_paragraph()
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    run = p.add_run()
    run.text = text
    set_run(run, size, color, bold)
    return p


def fill_shape(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def rect(slide, l, t, w, h, color):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    fill_shape(s, color)
    return s


def round_rect(slide, l, t, w, h, color):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    fill_shape(s, color)
    return s


def bg(slide, color=CREAM):
    rect(slide, 0, 0, W, H, color)


def footer(slide, page, total=15):
    rect(slide, 0, Inches(7.22), W, Inches(0.28), FOREST_DEEP)
    add_textbox(slide, Inches(0.4), Inches(7.22), Inches(8), Inches(0.28),
                "양형모  ·  웹 개발 8년  ·  나라원시스템 과장", 10, WHITE)
    add_textbox(slide, Inches(11.6), Inches(7.22), Inches(1.3), Inches(0.28),
                f"{page} / {total}", 10, WHITE, align=PP_ALIGN.RIGHT)


def kicker_bar(slide, title, subtitle=""):
    rect(slide, 0, 0, Inches(0.14), H, FOREST)
    add_textbox(slide, Inches(0.45), Inches(0.28), Inches(12), Inches(0.32),
                subtitle or "PORTFOLIO", 11, FOREST, True)
    add_textbox(slide, Inches(0.45), Inches(0.52), Inches(12.4), Inches(0.55),
                title, 26, INK, True)


def card(slide, l, t, w, h):
    s = round_rect(slide, l, t, w, h, PAPER)
    s.line.color.rgb = LINE
    s.line.width = Pt(0.75)
    return s


def cover(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s, FOREST_DEEP)
    rect(s, 0, 0, Inches(0.18), H, GOLD)
    add_textbox(s, Inches(0.7), Inches(1.55), Inches(12), Inches(0.35),
                "PORTFOLIO  ·  2026", 14, GOLD, True)
    add_textbox(s, Inches(0.7), Inches(2.05), Inches(12), Inches(1.1),
                "양형모", 60, WHITE, True)
    add_textbox(s, Inches(0.7), Inches(3.25), Inches(12), Inches(0.7),
                "웹 개발 경력 8년  ·  SI · SM", 24, CREAM)
    add_textbox(s, Inches(0.7), Inches(3.95), Inches(12), Inches(0.45),
                "AI, 공정 자동화 수련중", 20, GOLD)
    add_textbox(s, Inches(0.7), Inches(5.55), Inches(12), Inches(0.4),
                "나라원시스템 과장  ·  백석대학교 소프트웨어학", 14, RGBColor(0xC5, 0xD4, 0xCE))
    add_textbox(s, Inches(0.7), Inches(6.0), Inches(12), Inches(0.35),
                "010-8438-9060  ·  tytyrrr13@gmail.com  ·  github.com/Hyungmo1234", 13, RGBColor(0xC5, 0xD4, 0xCE))
    add_textbox(s, Inches(0.7), Inches(6.45), Inches(12), Inches(0.3),
                "hyungmo1234.github.io", 13, GOLD)


def about(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "한 장으로 보는 소개", "ABOUT")
    footer(s, 2)
    facts = [
        ("이름", "양형모"),
        ("나이", "35세 (한국 나이, 1992.10.05)"),
        ("소속", "나라원시스템 · 과장  ·  2021.07 ~ 재직"),
        ("학력", "백석대학교 졸업 · 소프트웨어학 전공"),
        ("경력", "웹 개발 8년 (SI · SM)"),
        ("지금", "공공기관 웹 시스템 개발·유지보수, AI·공정 자동화 수련"),
    ]
    y = Inches(1.25)
    for label, value in facts:
        add_textbox(s, Inches(0.55), y, Inches(1.6), Inches(0.4), label, 13, FOREST, True)
        add_textbox(s, Inches(2.2), y, Inches(10.4), Inches(0.4), value, 16, INK)
        y += Inches(0.52)
    card(s, Inches(0.5), Inches(4.55), Inches(12.3), Inches(2.4))
    add_textbox(s, Inches(0.75), Inches(4.7), Inches(11.8), Inches(0.4), "엉덩이를 무겁게", 18, FOREST, True)
    box = s.shapes.add_textbox(Inches(0.75), Inches(5.15), Inches(11.8), Inches(1.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "빠르게 발전하는 AI 시대에도 업무의 시작과 마무리는 사람이 결정하고, 완성도는 끈기가 만듭니다."
    set_run(r, 14, INK)
    add_para(tf, "작업물의 묘한 불편함과 적당한 완성도를 불쾌해하며 자리를 떠나지 않았습니다. 그 보상은 남들보다 아주 조금 더 나은 작업물이었습니다.", 14, INK, space_before=8)
    add_para(tf, "99.9%와 99.99%의 차이를 이해하고, 일정이 허락하는 한 마지막 소수점까지 팀을 설득할 것입니다.", 14, INK, space_before=8)


def timeline(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "경력 한눈에", "CAREER")
    footer(s, 3)
    items = [
        ("2019.05 — 2020.04", "IPSG", "개발", "RICOH 업무 시스템 개발"),
        ("2020.08 — 2021.06", "유니버셜 리얼타임", "개발", "마이데이터 API 솔루션 개발 · 동부화재 적용"),
        ("2021.07 — 재직", "나라원시스템", "과장", "공공기관 웹 시스템 개발·유지보수  (행정안전부, 문체부, 경찰청, 서울시 등)"),
    ]
    y = Inches(1.3)
    for when, co, role, desc in items:
        card(s, Inches(0.5), y, Inches(12.3), Inches(1.7))
        add_textbox(s, Inches(0.75), y + Inches(0.22), Inches(3.4), Inches(0.35), when, 13, FOREST, True)
        add_textbox(s, Inches(4.2), y + Inches(0.18), Inches(8.3), Inches(0.45), f"{co}  ·  {role}", 20, INK, True)
        add_textbox(s, Inches(4.2), y + Inches(0.75), Inches(8.3), Inches(0.7), desc, 15, MUTED)
        y += Inches(1.85)


def narawon_now(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "나라원시스템  ·  최근 공공 시스템", "2024 — 2026")
    footer(s, 4)
    rows = [
        ("2026.05 — 2026.12", "사행산업관리감독위원회 유지보수", "PM", "문화체육관광부"),
        ("2026.05 — 2026.12", "소통혁신24 유지보수", "PL", "행정안전부"),
        ("2025.04 — 2026.11", "소통24 고도화·유지보수", "PL", "행정안전부"),
        ("2025.03 — 2026.05", "혁신24 유지보수", "개발", "행정안전부"),
        ("2024.10 — 2025.03", "의정부문화재단 시스템 개발", "개발", "문화체육관광부"),
        ("2024.02 — 2025.02", "혁신24 유지보수", "개발", "행정안전부"),
        ("2024.04 — 2024.12", "건강관리마일리지시스템 유지보수", "개발", "서울시청"),
    ]
    y = Inches(1.22)
    add_textbox(s, Inches(0.55), y, Inches(3.2), Inches(0.3), "기간", 11, MUTED, True)
    add_textbox(s, Inches(3.7), y, Inches(5.6), Inches(0.3), "사업", 11, MUTED, True)
    add_textbox(s, Inches(9.4), y, Inches(1.3), Inches(0.3), "역할", 11, MUTED, True)
    add_textbox(s, Inches(10.7), y, Inches(2.1), Inches(0.3), "발주", 11, MUTED, True)
    y += Inches(0.38)
    for i, (when, what, role, org) in enumerate(rows):
        shade = PAPER if i % 2 == 0 else RGBColor(0xEB, 0xE4, 0xD8)
        rect(s, Inches(0.45), y - Inches(0.06), Inches(12.4), Inches(0.68), shade)
        add_textbox(s, Inches(0.55), y, Inches(3.2), Inches(0.55), when, 13, FOREST, True)
        add_textbox(s, Inches(3.7), y, Inches(5.6), Inches(0.55), what, 15, INK, True)
        add_textbox(s, Inches(9.4), y, Inches(1.3), Inches(0.55), role, 14, INK)
        add_textbox(s, Inches(10.7), y, Inches(2.1), Inches(0.55), org, 13, MUTED)
        y += Inches(0.68)


def narawon_early(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "나라원시스템  ·  공공 웹 기반", "2021 — 2024")
    footer(s, 5)
    rows = [
        ("2023.07 — 2024.01", "행정안전부 NPAS시스템 고도화", "개발", "행정안전부"),
        ("2023.05 — 2023.06", "서울시청 복지포털 유지보수", "개발", "서울시청"),
        ("2023.04 — 2023.04", "한국중견기업진흥원 유지보수", "개발", "한국중견기업진흥원"),
        ("2021.07 — 2023.03", "경찰청 신원정보시스템 유지보수", "개발", "경찰청"),
    ]
    y = Inches(1.3)
    for i, (when, what, role, org) in enumerate(rows):
        card(s, Inches(0.5), y, Inches(12.3), Inches(1.2))
        add_textbox(s, Inches(0.75), y + Inches(0.18), Inches(3.4), Inches(0.35), when, 13, FOREST, True)
        add_textbox(s, Inches(4.2), y + Inches(0.18), Inches(8.2), Inches(0.45), what, 18, INK, True)
        add_textbox(s, Inches(4.2), y + Inches(0.68), Inches(8.2), Inches(0.35), f"{role}  ·  {org}", 14, MUTED)
        y += Inches(1.32)
    add_textbox(s, Inches(0.55), Inches(6.65), Inches(12), Inches(0.4),
                "공공기관 웹 — 행정안전부 · 문화체육관광부 · 경찰청 · 서울시 중심의 SI · SM.", 13, MUTED)


def earlier(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "이전 경력", "2019 — 2021")
    footer(s, 6)
    card(s, Inches(0.5), Inches(1.3), Inches(12.3), Inches(2.4))
    add_textbox(s, Inches(0.75), Inches(1.5), Inches(12), Inches(0.35), "유니버셜 리얼타임  ·  개발", 20, INK, True)
    add_textbox(s, Inches(0.75), Inches(1.95), Inches(12), Inches(0.3), "2020.08 — 2021.06", 14, FOREST, True)
    add_textbox(s, Inches(0.75), Inches(2.45), Inches(11.8), Inches(0.4), "2020.08 — 2021.03    마이데이터 API 솔루션 개발  ·  자사", 16, INK)
    add_textbox(s, Inches(0.75), Inches(2.95), Inches(11.8), Inches(0.4), "2021.04 — 2021.06    동부화재 마이데이터 API 솔루션 적용  ·  동부화재", 16, INK)

    card(s, Inches(0.5), Inches(4.0), Inches(12.3), Inches(2.4))
    add_textbox(s, Inches(0.75), Inches(4.2), Inches(12), Inches(0.35), "IPSG  ·  개발", 20, INK, True)
    add_textbox(s, Inches(0.75), Inches(4.65), Inches(12), Inches(0.3), "2019.05 — 2020.04", 14, FOREST, True)
    add_textbox(s, Inches(0.75), Inches(5.2), Inches(11.8), Inches(0.4), "2019.05 — 2020.04    RICOH 업무 시스템 개발  ·  RICOH", 16, INK)


def skills(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "기술", "STACK")
    footer(s, 7)
    groups = [
        ("주력", Inches(0.45), [
            "Java", "Spring (eGov)", "JSP", "JavaScript", "Python", "Tibero", "Oracle", "Cubrid",
        ]),
        ("그 외", Inches(4.55), [
            "FastAPI", "Spring Boot", "JPA", "React", "TypeScript", "PostgreSQL",
            "GitHub Actions", "PWA", "Fly.io", "Cursor SDK", "Whisper",
            "scikit-learn", "XGBoost", "LightGBM", "Jinja2", "Pillow",
        ]),
        ("외부 API", Inches(8.65), [
            "공공데이터포털", "국토부 실거래", "K-APT", "청약홈",
            "한국은행 ECOS", "VWorld", "네이버 뉴스 API", "YouTube API", "OpenAI",
        ]),
    ]
    for title, x, items in groups:
        card(s, x, Inches(1.25), Inches(3.95), Inches(5.7))
        add_textbox(s, x + Inches(0.22), Inches(1.4), Inches(3.5), Inches(0.4), title, 16, FOREST, True)
        box = s.shapes.add_textbox(x + Inches(0.22), Inches(1.9), Inches(3.5), Inches(4.8))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = items[0]
        set_run(r, 14, INK)
        for name in items[1:]:
            add_para(tf, name, 14, INK, space_before=6)


def algo(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "데일리하우스에 쓴 처리", "PIPELINE")
    footer(s, 8)
    steps = [
        ("1", "수집", "네이버 뉴스 API로 부동산 기사를 매일 모읍니다."),
        ("2", "거르기", "규칙 기반 관련성 점수, 키워드 카테고리 분류."),
        ("3", "중복", "제목 정규화·동의어, 문자 바이그램 Jaccard, SequenceMatcher."),
        ("4", "묶기", "같은 사건은 LLM으로 클러스터링해 병합합니다."),
        ("5", "랭킹", "관련성·중복 매체·주요 언론 가중, 중요도 스코어링."),
        ("6", "발행", "OpenAI 요약, GitHub Pages, 인스타 카드(Pillow)."),
    ]
    positions = [
        (0.5, 1.3), (4.55, 1.3), (8.6, 1.3),
        (0.5, 4.05), (4.55, 4.05), (8.6, 4.05),
    ]
    for (n, title, desc), (x, y) in zip(steps, positions):
        card(s, Inches(x), Inches(y), Inches(3.9), Inches(2.45))
        add_textbox(s, Inches(x + 0.25), Inches(y + 0.25), Inches(0.5), Inches(0.4), n, 20, GOLD, True)
        add_textbox(s, Inches(x + 0.7), Inches(y + 0.28), Inches(2.9), Inches(0.4), title, 18, INK, True)
        add_textbox(s, Inches(x + 0.25), Inches(y + 0.85), Inches(3.4), Inches(1.3), desc, 14, MUTED)


def projects_map(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "개인 프로젝트", "APPS  ·  SYSTEMS  ·  TOOLS")
    footer(s, 9)
    items = [
        ("매일하루 시리즈", "영단어 · 일본인용 영단어 · 일본어\nPWA + GitHub Actions 숏츠"),
        ("데일리하우스", "매일 부동산 뉴스 브리핑\nPages + Instagram"),
        ("Prophecy", "공공 데이터 아파트 가치·전망\nSpring Boot · React · ML"),
        ("모바일 청첩장", "2026년 5월 결혼용\nTypeScript · Next.js · Vercel"),
        ("로컬 도구", "강의 녹음 툴 · Cursor Desk\nVS Workspace Theme"),
        ("공부", "파이썬 기초와 매일 노트\nGitHub에 자동 기록"),
    ]
    positions = [
        (0.45, 1.25), (4.55, 1.25), (8.65, 1.25),
        (0.45, 4.1), (4.55, 4.1), (8.65, 4.1),
    ]
    for (title, desc), (x, y) in zip(items, positions):
        card(s, Inches(x), Inches(y), Inches(3.95), Inches(2.55))
        add_textbox(s, Inches(x + 0.25), Inches(y + 0.28), Inches(3.45), Inches(0.55), title, 18, FOREST, True)
        add_textbox(s, Inches(x + 0.25), Inches(y + 1.0), Inches(3.45), Inches(1.25), desc, 14, INK)


def daily_words(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "매일하루 학습 앱", "PWA  ·  YOUTUBE SHORTS")
    footer(s, 10)
    blocks = [
        ("매일하루영단어",
         "하루 한 장의 영단어·숙어. 폰 홈 화면 PWA.\nGitHub Actions로 유튜브 숏츠를 올립니다.",
         "daily-english-hyungmo.fly.dev\nyoutube.com  ·  UCIBCHpm-Y71wkQBVet9wXzw"),
        ("매일하루영단어 (일본인)",
         "뜻과 예문을 일본어로. 毎日英単語 숏츠를 같은 파이프라인으로 발행.",
         "daily-english-hyungmo.fly.dev/#ja\nyoutube.com  ·  UCVguZaN1HSqr8uhzFE4momQ"),
        ("매일하루일본어",
         "일본어 단어·숙어. 히라가나 후리가나와 유튜브 채널 발행.",
         "YouTube  ·  UC8TVY1GZN0MPReRj0iiXjIg"),
    ]
    y = Inches(1.25)
    for title, desc, link in blocks:
        card(s, Inches(0.5), y, Inches(12.3), Inches(1.75))
        add_textbox(s, Inches(0.75), y + Inches(0.18), Inches(11.8), Inches(0.4), title, 18, FOREST, True)
        add_textbox(s, Inches(0.75), y + Inches(0.6), Inches(11.8), Inches(0.45), desc, 14, INK)
        add_textbox(s, Inches(0.75), y + Inches(1.15), Inches(11.8), Inches(0.4), link, 12, MUTED)
        y += Inches(1.85)


def daily_house(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "데일리하우스", "부동산 뉴스 브리핑")
    footer(s, 11)
    card(s, Inches(0.5), Inches(1.25), Inches(12.3), Inches(1.5))
    add_textbox(s, Inches(0.75), Inches(1.45), Inches(11.8), Inches(1.1),
                "매일 아침 뉴스를 모아 관련 없는 것과 중복을 빼고, 같은 사건을 묶은 뒤 요약·중요도를 매겨 GitHub Pages와 인스타그램에 올립니다.",
                16, INK)
    bits = [
        ("수집", "네이버 뉴스 API"),
        ("정제", "Jaccard · SequenceMatcher · LLM 클러스터"),
        ("요약", "OpenAI"),
        ("발행", "Pages + Pillow 인스타 카드"),
    ]
    x = Inches(0.5)
    for title, desc in bits:
        card(s, x, Inches(3.0), Inches(3.0), Inches(2.0))
        add_textbox(s, x + Inches(0.2), Inches(3.2), Inches(2.6), Inches(0.45), title, 16, FOREST, True)
        add_textbox(s, x + Inches(0.2), Inches(3.7), Inches(2.6), Inches(1.0), desc, 13, INK)
        x += Inches(3.15)
    add_textbox(s, Inches(0.55), Inches(5.3), Inches(12), Inches(0.4),
                "hyungmo1234.github.io/daily-house", 14, FOREST, True)
    add_textbox(s, Inches(0.55), Inches(5.75), Inches(12), Inches(0.4),
                "instagram.com/penguin.91557373", 14, MUTED)
    add_textbox(s, Inches(0.55), Inches(6.25), Inches(12), Inches(0.4),
                "Jinja2 템플릿  ·  GitHub Actions 스케줄", 13, MUTED)


def prophecy(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "Prophecy", "AI 부동산 인텔리전스")
    footer(s, 12)
    add_textbox(s, Inches(0.55), Inches(1.25), Inches(12.2), Inches(0.9),
                "공공 원천 데이터로 아파트 현재 가치와 가격 전망을 보는 플랫폼입니다. 서울·경기 단지 검색·실거래 조회와 예측을 Spring Boot API와 React 웹에 붙였습니다.",
                16, INK)
    cols = [
        ("원천", "국토부 실거래\nK-APT 단지\n청약홈\n한국은행 ECOS\nVWorld 입지"),
        ("데이터", "RAW → CLEAN 정제\nPostgreSQL 적재"),
        ("모델", "XGBoost\nLightGBM\nscikit-learn"),
        ("앱", "Spring Boot · JPA\nReact · TypeScript"),
    ]
    x = Inches(0.45)
    for title, body in cols:
        card(s, x, Inches(2.3), Inches(3.05), Inches(3.7))
        add_textbox(s, x + Inches(0.2), Inches(2.5), Inches(2.65), Inches(0.4), title, 16, FOREST, True)
        add_textbox(s, x + Inches(0.2), Inches(3.05), Inches(2.65), Inches(2.6), body, 14, INK)
        x += Inches(3.2)
    add_textbox(s, Inches(0.55), Inches(6.25), Inches(12), Inches(0.4),
                "비공개 저장소  ·  공개 웹 링크 없음", 13, MUTED)


def tools(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "로컬 도구 · 그 밖", "TOOLS")
    footer(s, 13)
    items = [
        ("강의 녹음 툴", "수업 마이크·휴대폰 녹음을 Whisper로 받아쓰고, Cursor로 강의 노트를 정리합니다. PC에서 실행."),
        ("형모 Cursor Desk", "Cursor SDK를 쓰는 Windows 데스크톱 채팅 앱. 세션, 첨부, 로컬 에이전트 작업을 한 창에서 합니다."),
        ("VS Workspace Theme", "커뮤니티 페이지를 VS Code 워크스페이스처럼 보이게 하는 크롬 확장 프로그램."),
        ("모바일 청첩장", "2026년 5월 결혼을 위해 TypeScript·Next.js로 직접 만들고 Vercel에 띄웠습니다."),
        ("파이썬 공부", "파이썬 기초 연습과 매일 공부 노트. 날짜 폴더에 기록하고 GitHub에 자동으로 올립니다."),
    ]
    y = Inches(1.22)
    for title, desc in items:
        card(s, Inches(0.5), y, Inches(12.3), Inches(1.05))
        add_textbox(s, Inches(0.75), y + Inches(0.12), Inches(3.3), Inches(0.8), title, 15, FOREST, True)
        add_textbox(s, Inches(4.1), y + Inches(0.18), Inches(8.4), Inches(0.75), desc, 13, INK)
        y += Inches(1.1)
    add_textbox(s, Inches(0.55), Inches(6.7), Inches(12), Inches(0.3),
                "청첩장  ·  mobile-invitation-by-cursor.vercel.app", 12, MUTED)


def site(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    kicker_bar(s, "웹에 모아 둔 것", "GITHUB PAGES")
    footer(s, 14)
    card(s, Inches(0.5), Inches(1.3), Inches(12.3), Inches(5.4))
    add_textbox(s, Inches(0.8), Inches(1.55), Inches(11.7), Inches(0.5), "개인 사이트", 20, FOREST, True)
    add_textbox(s, Inches(0.8), Inches(2.15), Inches(11.7), Inches(0.4),
                "https://hyungmo1234.github.io/", 18, INK)
    add_textbox(s, Inches(0.8), Inches(2.7), Inches(11.7), Inches(0.7),
                "프로젝트 모음과 웹 이력서를 GitHub Pages 계정 홈에 띄웠습니다. 저장소 목록 대신 웹·Git·유튜브·인스타를 한 페이지에서 엽니다.",
                15, MUTED)
    lines = [
        "이력서    hyungmo1234.github.io/resume.html",
        "데일리하우스    hyungmo1234.github.io/daily-house/",
        "GitHub    github.com/Hyungmo1234",
        "메일 · 전화    tytyrrr13@gmail.com  ·  010-8438-9060",
    ]
    y = Inches(3.6)
    for line in lines:
        add_textbox(s, Inches(0.8), y, Inches(11.7), Inches(0.45), line, 16, INK)
        y += Inches(0.55)


def close(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s, FOREST_DEEP)
    rect(s, 0, 0, Inches(0.18), H, GOLD)
    add_textbox(s, Inches(0.7), Inches(2.0), Inches(12), Inches(0.4), "감사합니다", 18, GOLD, True)
    add_textbox(s, Inches(0.7), Inches(2.5), Inches(12), Inches(0.9), "엉덩이를 무겁게", 40, WHITE, True)
    add_textbox(s, Inches(0.7), Inches(3.7), Inches(12), Inches(0.45),
                "양형모  ·  나라원시스템 과장", 18, CREAM)
    add_textbox(s, Inches(0.7), Inches(5.2), Inches(12), Inches(0.35),
                "010-8438-9060", 16, WHITE)
    add_textbox(s, Inches(0.7), Inches(5.6), Inches(12), Inches(0.35),
                "tytyrrr13@gmail.com", 16, WHITE)
    add_textbox(s, Inches(0.7), Inches(6.0), Inches(12), Inches(0.35),
                "github.com/Hyungmo1234   ·   hyungmo1234.github.io", 16, GOLD)


def main():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    cover(prs)
    about(prs)
    timeline(prs)
    narawon_now(prs)
    narawon_early(prs)
    earlier(prs)
    skills(prs)
    algo(prs)
    projects_map(prs)
    daily_words(prs)
    daily_house(prs)
    prophecy(prs)
    tools(prs)
    site(prs)
    close(prs)
    prs.save(OUT)
    print(OUT, "slides", len(prs.slides))


if __name__ == "__main__":
    main()
