"""Latency Edge 기술 문서 PDF 생성"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── Font Registration (한글 지원) ──
FONT_REGISTERED = False
FONT_NAME = "Helvetica"
FONT_NAME_BOLD = "Helvetica-Bold"

# Try to register a Korean font
korean_font_paths = [
    "C:/Windows/Fonts/malgun.ttf",      # 맑은 고딕
    "C:/Windows/Fonts/malgunbd.ttf",     # 맑은 고딕 Bold
    "C:/Windows/Fonts/NanumGothic.ttf",
    "C:/Windows/Fonts/NanumGothicBold.ttf",
]

if os.path.exists("C:/Windows/Fonts/malgun.ttf"):
    pdfmetrics.registerFont(TTFont("MalgunGothic", "C:/Windows/Fonts/malgun.ttf"))
    pdfmetrics.registerFont(TTFont("MalgunGothicBold", "C:/Windows/Fonts/malgunbd.ttf"))
    FONT_NAME = "MalgunGothic"
    FONT_NAME_BOLD = "MalgunGothicBold"
    FONT_REGISTERED = True
elif os.path.exists("C:/Windows/Fonts/NanumGothic.ttf"):
    pdfmetrics.registerFont(TTFont("NanumGothic", "C:/Windows/Fonts/NanumGothic.ttf"))
    pdfmetrics.registerFont(TTFont("NanumGothicBold", "C:/Windows/Fonts/NanumGothicBold.ttf"))
    FONT_NAME = "NanumGothic"
    FONT_NAME_BOLD = "NanumGothicBold"
    FONT_REGISTERED = True

# ── Colors ──
PRIMARY = HexColor("#1a1a2e")
ACCENT = HexColor("#0f3460")
HIGHLIGHT = HexColor("#e94560")
LIGHT_BG = HexColor("#f0f0f5")
BORDER = HexColor("#cccccc")
TEXT_DARK = HexColor("#1a1a1a")
TEXT_GRAY = HexColor("#555555")

# ── Styles ──
styles = getSampleStyleSheet()

style_title = ParagraphStyle(
    "DocTitle", parent=styles["Title"],
    fontName=FONT_NAME_BOLD, fontSize=28, textColor=PRIMARY,
    spaceAfter=6*mm, alignment=TA_CENTER
)
style_subtitle = ParagraphStyle(
    "DocSubtitle", parent=styles["Normal"],
    fontName=FONT_NAME, fontSize=13, textColor=TEXT_GRAY,
    spaceAfter=12*mm, alignment=TA_CENTER
)
style_h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontName=FONT_NAME_BOLD, fontSize=20, textColor=PRIMARY,
    spaceBefore=10*mm, spaceAfter=5*mm, borderPadding=(0, 0, 2, 0),
)
style_h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontName=FONT_NAME_BOLD, fontSize=15, textColor=ACCENT,
    spaceBefore=7*mm, spaceAfter=3*mm,
)
style_h3 = ParagraphStyle(
    "H3", parent=styles["Heading3"],
    fontName=FONT_NAME_BOLD, fontSize=12, textColor=TEXT_DARK,
    spaceBefore=4*mm, spaceAfter=2*mm,
)
style_body = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontName=FONT_NAME, fontSize=10, textColor=TEXT_DARK,
    leading=16, spaceAfter=3*mm, alignment=TA_JUSTIFY
)
style_bullet = ParagraphStyle(
    "Bullet", parent=style_body,
    leftIndent=15*mm, bulletIndent=8*mm, spaceAfter=2*mm,
)
style_code = ParagraphStyle(
    "Code", parent=styles["Normal"],
    fontName="Courier", fontSize=9, textColor=HexColor("#333333"),
    backColor=LIGHT_BG, borderPadding=6, leftIndent=5*mm,
    spaceAfter=3*mm, leading=13
)
style_caption = ParagraphStyle(
    "Caption", parent=styles["Normal"],
    fontName=FONT_NAME, fontSize=9, textColor=TEXT_GRAY,
    alignment=TA_CENTER, spaceAfter=5*mm
)

def make_table(headers, rows, col_widths=None):
    """Create a styled table."""
    data = [headers] + rows
    if col_widths is None:
        col_widths = [160*mm / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_NAME_BOLD),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTNAME", (0, 1), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t

def hr():
    return HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=5*mm, spaceBefore=3*mm)

def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title="Latency Edge - Technical Documentation",
        author="Latency Edge Team"
    )

    story = []
    B = lambda t: f"<b>{t}</b>"
    I = lambda t: f"<i>{t}</i>"

    # ════════════════════════════════════════════════════
    # COVER PAGE
    # ════════════════════════════════════════════════════
    story.append(Spacer(1, 40*mm))
    story.append(Paragraph("LATENCY EDGE", style_title))
    story.append(Paragraph("Crypto Arbitrage &amp; Trading System", style_subtitle))
    story.append(hr())
    story.append(Paragraph(
        "Binance-Upbit 간 시간차(Lead-Lag)를 활용한 자동 트레이딩 시스템의 "
        "전체 아키텍처, 투자 알고리즘, 리스크 관리 및 백테스팅 기술 문서",
        ParagraphStyle("CoverDesc", parent=style_body, alignment=TA_CENTER, fontSize=11, leading=18)
    ))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("2026.03", ParagraphStyle("CoverDate", parent=style_caption, fontSize=12)))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ════════════════════════════════════════════════════
    story.append(Paragraph("목차 (Table of Contents)", style_h1))
    story.append(hr())
    toc_items = [
        "1. 시스템 개요 (System Overview)",
        "2. 프로젝트 구조 (Project Structure)",
        "3. 핵심 개념: 시간차 전략 (Lead-Lag Strategy)",
        "4. 투자 알고리즘 상세 (Trading Algorithms)",
        "    4.1 Lead-Lag Scalper (김치 프리미엄 역이용)",
        "    4.2 Momentum Breakout (모멘텀 돌파)",
        "5. 멀티 전략 운용 구조 (Multi-Strategy Architecture)",
        "6. 리스크 관리 (Risk Management)",
        "7. 수수료 및 슬리피지 모델 (Fee &amp; Slippage)",
        "8. 백테스팅 엔진 (Backtesting Engine)",
        "9. 실시간 데이터 수집 (WebSocket Collectors)",
        "10. 대시보드 &amp; API (Dashboard &amp; API)",
        "11. 전체 데이터 흐름 (End-to-End Flow)",
    ]
    for item in toc_items:
        indent = 15*mm if item.startswith("    ") else 5*mm
        story.append(Paragraph(item.strip(), ParagraphStyle(
            "TOC", parent=style_body, leftIndent=indent, spaceAfter=2*mm
        )))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 1. SYSTEM OVERVIEW
    # ════════════════════════════════════════════════════
    story.append(Paragraph("1. 시스템 개요 (System Overview)", style_h1))
    story.append(hr())
    story.append(Paragraph(
        "Latency Edge는 글로벌 거래소(Binance)와 한국 거래소(Upbit) 간의 "
        f"{B('가격 전파 지연(latency)')}을 활용하는 자동 페이퍼 트레이딩 시스템입니다. "
        "Binance의 BTC/USDT 가격이 먼저 움직이고, Upbit의 KRW-BTC 가격이 뒤따르는 "
        f"{B('Lead-Lag 관계')}를 핵심 엣지로 삼습니다.",
        style_body
    ))
    story.append(Paragraph(
        "현재 시스템은 실제 자금을 사용하지 않는 "
        f"{B('페이퍼 트레이딩(Paper Trading)')} 모드로 운영되며, "
        "실시간 WebSocket 데이터를 기반으로 전략 시뮬레이션을 수행합니다.",
        style_body
    ))

    story.append(Paragraph("핵심 특징", style_h2))
    features = [
        f"{B('실시간 이중 거래소 모니터링')}: Binance + Upbit WebSocket 동시 수집",
        f"{B('멀티 전략 독립 운용')}: 전략별 독립 포트폴리오 (각 500만원)",
        f"{B('리스크 관리')}: 일일 손실 한도 + 연속 손실 차단",
        f"{B('실시간 대시보드')}: Next.js 기반 라이브 모니터링",
        f"{B('백테스팅')}: 슬리피지 포함 과거 데이터 검증",
    ]
    for f in features:
        story.append(Paragraph(f, style_bullet, bulletText="\u2022"))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 2. PROJECT STRUCTURE
    # ════════════════════════════════════════════════════
    story.append(Paragraph("2. 프로젝트 구조 (Project Structure)", style_h1))
    story.append(hr())
    structure = [
        ["src/api/server.py", "FastAPI 서버 + 트레이딩 엔진 (메인 진입점)"],
        ["src/collectors/binance_ws.py", "Binance WebSocket 실시간 데이터 수집기"],
        ["src/collectors/upbit_ws.py", "Upbit WebSocket 실시간 데이터 수집기"],
        ["src/strategies/lead_lag_scalper.py", "김치 프리미엄 역이용 전략 (Lead-Lag)"],
        ["src/strategies/momentum_breakout.py", "모멘텀 돌파 전략 (Trailing Stop)"],
        ["src/strategies/base.py", "전략 베이스 클래스 (인터페이스)"],
        ["src/risk/daily_stop.py", "일일 리스크 관리자 (회로 차단기)"],
        ["src/backtest/engine.py", "백테스팅 엔진"],
        ["src/backtest/slippage.py", "슬리피지 시뮬레이션 모델"],
        ["dashboard-web/", "Next.js 실시간 대시보드 (React)"],
        ["run_server.py", "서버 실행 진입점 (포트 8009)"],
        ["tests/test_strategies.py", "전략 단위 테스트"],
    ]
    story.append(make_table(
        ["파일 / 디렉토리", "설명"],
        structure,
        col_widths=[65*mm, 100*mm]
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 3. LEAD-LAG STRATEGY CONCEPT
    # ════════════════════════════════════════════════════
    story.append(Paragraph("3. 핵심 개념: 시간차 전략 (Lead-Lag Strategy)", style_h1))
    story.append(hr())
    story.append(Paragraph(
        "전 세계 암호화폐 시장에서 Binance는 가장 큰 유동성과 거래량을 보유하고 있어 "
        f"가격 발견(price discovery)에서 {B('선행(Lead)')} 역할을 합니다. "
        f"반면 Upbit 등 지역 거래소는 가격이 {B('후행(Lag)')}하여 따라가는 경향이 있습니다.",
        style_body
    ))

    story.append(Paragraph("시간차 발생 원리", style_h2))
    reasons = [
        f"{B('유동성 차이')}: Binance의 거래량이 Upbit 대비 수십 배 → 가격 변동이 Binance에서 먼저 발생",
        f"{B('정보 전파 지연')}: 글로벌 트레이더들의 주문이 Binance에 먼저 반영 → Upbit 전파에 수백ms~수초 소요",
        f"{B('시장 참여자 구조')}: Binance에는 고빈도 트레이더(HFT), 마켓 메이커가 집중 → 빠른 가격 반영",
        f"{B('환율 변환 지연')}: USD→KRW 환산 과정에서 추가 지연 발생",
    ]
    for r in reasons:
        story.append(Paragraph(r, style_bullet, bulletText="\u2022"))

    story.append(Paragraph("활용 방법", style_h2))
    story.append(Paragraph(
        "Binance BTC/USDT 가격을 환율(FX Rate)로 변환하여 Upbit KRW-BTC와 비교합니다. "
        "이 차이를 '김치 프리미엄(Kimchi Premium)'이라 부르며, "
        "프리미엄이 비정상적으로 낮을 때(역프리미엄) 매수하고, "
        "정상 수준으로 회복될 때 매도하는 전략입니다.",
        style_body
    ))
    story.append(Paragraph(
        f"Premium = (Upbit가격 - Binance가격 x 환율) / (Binance가격 x 환율)",
        style_code
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 4. TRADING ALGORITHMS
    # ════════════════════════════════════════════════════
    story.append(Paragraph("4. 투자 알고리즘 상세 (Trading Algorithms)", style_h1))
    story.append(hr())
    story.append(Paragraph(
        "본 시스템은 두 가지 독립 전략을 동시에 운용하며, "
        "각 전략은 서로 다른 시장 비효율성을 포착합니다.",
        style_body
    ))

    # 4.1 Lead-Lag Scalper
    story.append(Paragraph("4.1 Lead-Lag Scalper (김치 프리미엄 역이용)", style_h2))
    story.append(Paragraph(
        f"김치 프리미엄의 {B('역프리미엄 수렴')} 패턴을 이용합니다. "
        "Upbit 가격이 Binance 대비 비정상적으로 저평가되었을 때(역프리미엄) 매수하고, "
        "프리미엄이 정상으로 회복되면 매도합니다.",
        style_body
    ))

    story.append(Paragraph("매매 조건", style_h3))
    ll_params = [
        ["진입 조건 (Entry)", "프리미엄 <= -2.0% (역프리미엄 발생 시)"],
        ["청산 조건 (Exit)", "프리미엄 >= +0.5% (정상 수준 회복)"],
        ["환율 (FX Rate)", "기본 1,400 KRW/USD (환경변수 설정 가능)"],
        ["포지션 크기", "최대 1,000,000 KRW / 거래"],
    ]
    story.append(make_table(["파라미터", "값"], ll_params, col_widths=[55*mm, 110*mm]))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("작동 흐름", style_h3))
    ll_flow = [
        "1. Binance 가격 수신 -> FX Rate로 KRW 변환",
        "2. Upbit 가격과 비교하여 프리미엄 계산",
        "3. 프리미엄 <= -2% -> 매수 신호 (Upbit이 저평가)",
        "4. 프리미엄 >= +0.5% -> 매도 신호 (가격 수렴 완료)",
    ]
    for f in ll_flow:
        story.append(Paragraph(f, style_bullet, bulletText="\u2022"))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("왜 역프리미엄에 매수하는가?", style_h3))
    story.append(Paragraph(
        "역프리미엄(-2% 이하)은 Upbit 가격이 글로벌 시장 대비 과도하게 낮은 상태입니다. "
        "이는 일시적인 현상으로, 차익거래자들의 활동과 시장 효율성에 의해 "
        "프리미엄은 결국 정상 수준(0% 부근)으로 회귀합니다. "
        "이 수렴 과정에서 수익을 포착하는 것이 핵심 전략입니다.",
        style_body
    ))
    story.append(PageBreak())

    # 4.2 Momentum Breakout
    story.append(Paragraph("4.2 Momentum Breakout (모멘텀 돌파)", style_h2))
    story.append(Paragraph(
        f"최근 N틱 최고가를 돌파하고 거래량이 급증하는 {B('브레이크아웃')} 시점에 진입합니다. "
        "진입 후에는 Trailing Stop과 Stop Loss 두 가지 청산 메커니즘으로 수익을 보호합니다.",
        style_body
    ))

    story.append(Paragraph("매매 조건", style_h3))
    mb_params = [
        ["진입: 가격 조건", "현재가 > 최근 5틱 최고가 (돌파)"],
        ["진입: 거래량 조건", "현재 거래량 > 평균 거래량 x 1.5배"],
        ["청산: Trailing Stop", "최고점 대비 -1.0% 하락 시 매도"],
        ["청산: Stop Loss", "진입가 대비 -2.0% 하락 시 매도"],
        ["Lookback 기간", "최근 5틱"],
    ]
    story.append(make_table(["파라미터", "값"], mb_params, col_widths=[55*mm, 110*mm]))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Trailing Stop 메커니즘", style_h3))
    story.append(Paragraph(
        "진입 후 가격이 상승하면 highest_since_entry를 지속적으로 갱신합니다. "
        "가격이 최고점에서 1% 이상 하락하면 자동으로 청산합니다. "
        "이를 통해 상승 추세에서는 수익을 극대화하고, 반전 시 빠르게 이탈합니다.",
        style_body
    ))
    story.append(Paragraph(
        "Trailing Stop: price &lt;= highest_since_entry x (1 - 0.01)\n"
        "Stop Loss:     price &lt;= entry_price x (1 - 0.02)",
        style_code
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 5. MULTI-STRATEGY
    # ════════════════════════════════════════════════════
    story.append(Paragraph("5. 멀티 전략 운용 구조 (Multi-Strategy Architecture)", style_h1))
    story.append(hr())
    story.append(Paragraph(
        "두 전략은 완전히 독립적으로 운용됩니다. "
        "각 전략에 500만원씩 배정하여 총 1,000만원의 페이퍼 자본을 운용합니다.",
        style_body
    ))

    ms_data = [
        ["Lead-Lag Scalper", "5,000,000 KRW", "김치 프리미엄 수렴", "단기 (수분~수시간)"],
        ["Momentum Breakout", "5,000,000 KRW", "가격 돌파 + 거래량 급증", "초단기 (수초~수분)"],
    ]
    story.append(make_table(
        ["전략명", "배정 자본", "포착 대상", "보유 기간"],
        ms_data,
        col_widths=[40*mm, 35*mm, 50*mm, 40*mm]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("왜 멀티 전략인가?", style_h3))
    multi_reasons = [
        f"{B('상관관계 분산')}: 프리미엄 수렴과 모멘텀 돌파는 서로 다른 시장 상황에서 작동",
        f"{B('리스크 격리')}: 전략별 독립 포트폴리오로 한 전략의 손실이 다른 전략에 영향 없음",
        f"{B('기회 극대화')}: 시장 상황에 따라 최소 하나의 전략이 기회를 포착",
    ]
    for r in multi_reasons:
        story.append(Paragraph(r, style_bullet, bulletText="\u2022"))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 6. RISK MANAGEMENT
    # ════════════════════════════════════════════════════
    story.append(Paragraph("6. 리스크 관리 (Risk Management)", style_h1))
    story.append(hr())
    story.append(Paragraph(
        f"DailyRiskManager는 시스템 전체의 {B('회로 차단기(Circuit Breaker)')} 역할을 합니다. "
        "일일 기준으로 누적 손실과 연속 손실을 추적하며, 한도 초과 시 모든 신규 진입을 차단합니다.",
        style_body
    ))

    risk_params = [
        ["일일 최대 손실 한도", "500,000 KRW (50만원)"],
        ["최대 연속 손실 횟수", "5회"],
        ["리셋 주기", "일일 (매일 자정 기준)"],
        ["차단 시 동작", "BLOCKED_BY_RISK 시그널 발송, 신규 진입 거부"],
    ]
    story.append(make_table(["파라미터", "값"], risk_params, col_widths=[55*mm, 110*mm]))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("작동 로직", style_h3))
    story.append(Paragraph(
        "def check_trade_allowed():\n"
        "    if current_loss >= max_daily_loss:  # 50만원 초과\n"
        "        return False\n"
        "    if consecutive_losses >= max_consecutive:  # 5연패\n"
        "        return False\n"
        "    return True",
        style_code
    ))
    story.append(Paragraph(
        "손실 발생 시(PnL &lt; 0) 누적 손실에 가산하고 연속 손실 카운터를 증가시킵니다. "
        "수익 발생 시 연속 손실 카운터만 리셋합니다. 누적 손실은 일일 리셋 시에만 초기화됩니다.",
        style_body
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 7. FEE & SLIPPAGE
    # ════════════════════════════════════════════════════
    story.append(Paragraph("7. 수수료 및 슬리피지 모델 (Fee &amp; Slippage)", style_h1))
    story.append(hr())

    story.append(Paragraph("거래 수수료", style_h2))
    story.append(Paragraph(
        f"모든 거래에 Upbit 메이커 수수료 {B('0.05%')}를 양방향(매수+매도) 적용합니다.",
        style_body
    ))
    fee_data = [
        ["매수 시", "투입 KRW x 0.9995 = 실제 매수 가능 금액"],
        ["매도 시", "BTC x 현재가 x 0.9995 = 실제 수령 KRW"],
        ["왕복 수수료", "약 0.10% (매수 0.05% + 매도 0.05%)"],
    ]
    story.append(make_table(["구분", "계산"], fee_data, col_widths=[40*mm, 125*mm]))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("슬리피지 모델 (백테스팅용)", style_h2))
    story.append(Paragraph(
        "백테스팅에서는 실제 시장의 체결 미끄러짐을 시뮬레이션하기 위해 "
        "3가지 요소를 결합한 슬리피지 모델을 적용합니다.",
        style_body
    ))
    slip_data = [
        ["고정 슬리피지", "2.0 bps (0.02%)", "기본 스프레드 비용"],
        ["변동성 페널티", "가격 x 변동성 x (지연ms/1000)", "급변 시장 체결 미끄러짐"],
        ["시장 충격", "가격 x 충격계수 x ln(1+주문크기)", "대량 주문 시 가격 영향"],
    ]
    story.append(make_table(
        ["요소", "수식", "설명"],
        slip_data,
        col_widths=[40*mm, 65*mm, 60*mm]
    ))
    story.append(Paragraph(
        "Slippage = Base + Volatility Penalty + Size Impact\n"
        "         = price x (bps/10000)\n"
        "         + price x volatility x (latency_ms/1000)\n"
        "         + price x impact_factor x ln(1 + order_size)",
        style_code
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 8. BACKTESTING
    # ════════════════════════════════════════════════════
    story.append(Paragraph("8. 백테스팅 엔진 (Backtesting Engine)", style_h1))
    story.append(hr())
    story.append(Paragraph(
        "BacktestEngine은 과거 데이터(DataFrame)를 시간순으로 순회하며 "
        "전략의 진입/청산 시그널을 검증합니다. 슬리피지 모델이 자동 적용되어 "
        "실제 체결가에 가까운 시뮬레이션을 제공합니다.",
        style_body
    ))

    story.append(Paragraph("백테스팅 흐름", style_h3))
    bt_flow = [
        "1. 각 데이터 행(row)을 전략의 on_tick()에 전달",
        "2. 전략이 should_enter() 반환 -> 슬리피지 적용 후 매수 기록",
        "3. 전략이 should_exit() 반환 -> 슬리피지 적용 후 매도 기록",
        "4. 매 틱마다 equity curve 갱신",
        "5. 최종 결과: 총 자본, 거래 내역, 자산 곡선 반환",
    ]
    for f in bt_flow:
        story.append(Paragraph(f, style_bullet, bulletText="\u2022"))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("결과 지표", style_h3))
    bt_results = [
        ["final_capital", "최종 잔여 자본 (초기 10,000 기준)"],
        ["total_trades", "총 거래 횟수"],
        ["trades", "개별 거래 내역 (진입/청산 시간, 가격, PnL)"],
        ["equity", "시간별 자산 곡선 (equity curve)"],
    ]
    story.append(make_table(["지표", "설명"], bt_results, col_widths=[45*mm, 120*mm]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 9. WEBSOCKET COLLECTORS
    # ════════════════════════════════════════════════════
    story.append(Paragraph("9. 실시간 데이터 수집 (WebSocket Collectors)", style_h1))
    story.append(hr())
    story.append(Paragraph(
        "두 거래소의 실시간 데이터를 WebSocket으로 수집합니다. "
        "연결 끊김 시 지수 백오프(exponential backoff)로 자동 재연결합니다.",
        style_body
    ))

    ws_data = [
        ["Binance", "wss://stream.binance.com:9443/ws/...", "btcusdt@ticker", "symbol, price, volume"],
        ["Upbit", "wss://api.upbit.com/websocket/v1", "ticker (KRW-BTC)", "symbol, price, volume"],
    ]
    story.append(make_table(
        ["거래소", "WebSocket URI", "구독 채널", "수집 데이터"],
        ws_data,
        col_widths=[25*mm, 60*mm, 40*mm, 40*mm]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("자동 재연결 (Exponential Backoff)", style_h3))
    story.append(Paragraph(
        "연결 실패 시: 1초 -> 2초 -> 4초 -> 8초 -> ... -> 최대 60초 대기 후 재시도. "
        "연결 성공 시 대기 시간이 1초로 리셋됩니다.",
        style_body
    ))
    story.append(Paragraph(
        "retry_delay = 1\n"
        "while True:\n"
        "    try:\n"
        "        connect()  # 연결 시도\n"
        "        retry_delay = 1  # 성공 시 리셋\n"
        "    except ConnectionError:\n"
        "        sleep(retry_delay)\n"
        "        retry_delay = min(retry_delay * 2, 60)  # 지수 백오프",
        style_code
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 10. DASHBOARD & API
    # ════════════════════════════════════════════════════
    story.append(Paragraph("10. 대시보드 &amp; API (Dashboard &amp; API)", style_h1))
    story.append(hr())

    story.append(Paragraph("FastAPI 백엔드 (포트 8009)", style_h2))
    api_endpoints = [
        ["GET /api/state", "현재 시장 상태, 포트폴리오, 최근 시그널 조회"],
        ["WS /ws", "실시간 WebSocket 스트림 (tick, signal 이벤트)"],
    ]
    story.append(make_table(
        ["엔드포인트", "설명"],
        api_endpoints,
        col_widths=[50*mm, 115*mm]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Next.js 대시보드", style_h2))
    dash_features = [
        f"{B('Portfolio 카드')}: 총 자산, PnL, 현금/BTC 잔고, 승률",
        f"{B('Market 카드')}: Upbit/Binance 실시간 가격, 김치 프리미엄",
        f"{B('Signal Feed')}: 실시간 매매 시그널 (ENTRY/EXIT/BLOCKED) 색상 구분",
        f"{B('BTC/KRW 차트')}: lightweight-charts 기반 실시간 가격 차트",
        f"{B('WebSocket 연결')}: localhost:8009 실시간 양방향 통신",
    ]
    for f in dash_features:
        story.append(Paragraph(f, style_bullet, bulletText="\u2022"))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # 11. END-TO-END FLOW
    # ════════════════════════════════════════════════════
    story.append(Paragraph("11. 전체 데이터 흐름 (End-to-End Flow)", style_h1))
    story.append(hr())
    story.append(Paragraph(
        "시스템의 전체 데이터 흐름은 다음과 같습니다:",
        style_body
    ))

    flow_steps = [
        f"{B('[데이터 수집]')} Binance/Upbit WebSocket -> asyncio.Queue -> 시장 상태 갱신",
        f"{B('[프리미엄 계산]')} (Upbit가격 - Binance가격 x FX Rate) / (Binance가격 x FX Rate)",
        f"{B('[전략 실행]')} 각 전략의 on_tick() -> should_enter() / should_exit() 판단",
        f"{B('[리스크 체크]')} DailyRiskManager.check_trade_allowed() 통과 여부 확인",
        f"{B('[주문 시뮬레이션]')} 0.05% 수수료 적용 후 포트폴리오 업데이트",
        f"{B('[PnL 기록]')} 청산 시 손익 계산 -> 리스크 매니저 갱신",
        f"{B('[대시보드 브로드캐스트]')} WebSocket으로 tick/signal 이벤트 전송",
    ]
    for i, step in enumerate(flow_steps):
        story.append(Paragraph(step, style_bullet, bulletText=f"{i+1}."))

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "모든 알고리즘(Lead-Lag, Momentum)과 안전장치(리스크 관리, 수수료, 슬리피지)가 "
        "하나의 파이프라인에서 유기적으로 맞물려 동작합니다. "
        "각 컴포넌트는 독립적으로 테스트 가능하며, 백테스팅을 통해 과거 데이터로도 검증할 수 있습니다.",
        style_body
    ))

    story.append(Spacer(1, 15*mm))
    story.append(hr())
    story.append(Paragraph(
        "Latency Edge - Technical Documentation v1.0 | 2026.03",
        style_caption
    ))

    # Build
    doc.build(story)
    print(f"PDF created: {output_path}")


if __name__ == "__main__":
    output = os.path.join(os.path.dirname(__file__), "Latency_Edge_Documentation.pdf")
    build_pdf(output)
