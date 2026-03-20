"""중앙 설정 관리 — 하드코딩된 값을 환경변수/기본값으로 통합"""
import os


class Config:
    # 환율
    FX_RATE: float = float(os.environ.get("FX_RATE", "1400.0"))

    # 포트폴리오
    CAPITAL_PER_STRATEGY: float = float(os.environ.get("CAPITAL_PER_STRATEGY", "5000000.0"))
    TRADE_SIZE_KRW: float = float(os.environ.get("TRADE_SIZE_KRW", "1000000.0"))

    # 수수료
    FEE_RATE: float = float(os.environ.get("FEE_RATE", "0.0005"))  # 0.05%

    # 리스크
    MAX_DAILY_LOSS: float = float(os.environ.get("MAX_DAILY_LOSS", "500000.0"))
    MAX_CONSECUTIVE_LOSSES: int = int(os.environ.get("MAX_CONSECUTIVE_LOSSES", "5"))

    # 전략: Lead-Lag
    LL_ENTRY_THRESHOLD: float = float(os.environ.get("LL_ENTRY_THRESHOLD", "-0.02"))
    LL_EXIT_THRESHOLD: float = float(os.environ.get("LL_EXIT_THRESHOLD", "0.005"))

    # 전략: Momentum
    MOM_LOOKBACK: int = int(os.environ.get("MOM_LOOKBACK", "5"))
    MOM_VOLUME_MULT: float = float(os.environ.get("MOM_VOLUME_MULT", "1.5"))
    MOM_TRAIL_PCT: float = float(os.environ.get("MOM_TRAIL_PCT", "0.01"))
    MOM_STOP_LOSS_PCT: float = float(os.environ.get("MOM_STOP_LOSS_PCT", "0.02"))

    # OU 모델 (김프 동적 임계값)
    OU_LOOKBACK: int = int(os.environ.get("OU_LOOKBACK", "60"))
    OU_ENTRY_ZSCORE: float = float(os.environ.get("OU_ENTRY_ZSCORE", "-2.0"))
    OU_EXIT_ZSCORE: float = float(os.environ.get("OU_EXIT_ZSCORE", "0.0"))

    # ATR (동적 스탑)
    ATR_PERIOD: int = int(os.environ.get("ATR_PERIOD", "14"))
    ATR_TRAIL_MULT: float = float(os.environ.get("ATR_TRAIL_MULT", "2.0"))
    ATR_STOP_MULT: float = float(os.environ.get("ATR_STOP_MULT", "1.5"))

    # Donchian 앙상블
    DONCHIAN_PERIODS: list = [5, 10, 20]

    # EWMA 레짐 감지
    REGIME_FAST_SPAN: int = int(os.environ.get("REGIME_FAST_SPAN", "10"))
    REGIME_SLOW_SPAN: int = int(os.environ.get("REGIME_SLOW_SPAN", "50"))

    # Kelly 포지션 사이징
    KELLY_ENABLED: bool = os.environ.get("KELLY_ENABLED", "true").lower() == "true"
    KELLY_MIN_TRADES: int = int(os.environ.get("KELLY_MIN_TRADES", "10"))
    KELLY_MAX_FRACTION: float = float(os.environ.get("KELLY_MAX_FRACTION", "0.25"))

    # 서버
    PORT: int = int(os.environ.get("PORT", "8009"))
    SIGNAL_HISTORY_SIZE: int = 500
