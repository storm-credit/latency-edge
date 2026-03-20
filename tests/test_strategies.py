import pytest
import numpy as np
import pandas as pd
from src.strategies.lead_lag_scalper import LeadLagScalper
from src.strategies.momentum_breakout import MomentumBreakout
from src.strategies.multi_premium import MultiPremiumStrategy, CoinPremiumState
from src.risk.daily_stop import DailyRiskManager
from src.risk.position_sizer import KellyPositionSizer
from src.backtest.slippage import SlippageModel
from src.backtest.engine import BacktestEngine
from src.features.ou_calibration import OUCalibrator
from src.features.atr import ATRCalculator
from src.features.donchian import DonchianChannel, DonchianEnsemble
from src.features.regime import RegimeDetector
from src.features.volume_filter import VolumePercentileFilter
from src.features.vwap import VWAPCalculator
from src.features.trade_flow import TradeFlowImbalance


# ═══ Lead-Lag Scalper ═══

def test_lead_lag_scalper_discount_entry():
    """역프리미엄 수렴 전략: 디스카운트 시 매수, 프리미엄 복귀 시 매도"""
    config = {
        "entry_threshold": -0.05,
        "exit_threshold": 0.01,
        "fx_rate": 1000.0,
        "position_size": 1.0,
        "min_hold_ticks": 0,  # 테스트용: 즉시 청산 허용
        "cooldown_ticks": 0,
    }
    strategy = LeadLagScalper(config)

    # 0% premium → 진입 안 함
    strategy.on_tick({'upbit_price': 60000, 'binance_price': 60})
    assert not strategy.should_enter()

    # -10% 역프리미엄 → 진입
    strategy.on_tick({'upbit_price': 54000, 'binance_price': 60})
    assert strategy.should_enter()
    strategy.state["in_position"] = True

    # +2% 복귀 → 청산
    strategy.on_tick({'upbit_price': 61200, 'binance_price': 60})
    assert strategy.should_exit()


def test_lead_lag_scalper_no_exit_while_discount():
    """역프리미엄 지속 시 청산하지 않음"""
    config = {
        "entry_threshold": -0.05,
        "exit_threshold": 0.01,
        "fx_rate": 1000.0,
        "min_hold_ticks": 0,
        "cooldown_ticks": 0,
    }
    strategy = LeadLagScalper(config)

    strategy.on_tick({'upbit_price': 54000, 'binance_price': 60})
    assert strategy.should_enter()
    strategy.state["in_position"] = True

    # -3% → 아직 청산 안 함
    strategy.on_tick({'upbit_price': 58200, 'binance_price': 60})
    assert not strategy.should_exit()


def test_lead_lag_cooldown():
    """청산 후 쿨다운 기간 동안 재진입 차단"""
    config = {
        "entry_threshold": -0.05,
        "exit_threshold": 0.01,
        "fx_rate": 1000.0,
        "min_hold_ticks": 0,
        "cooldown_ticks": 2,
    }
    strategy = LeadLagScalper(config)

    # 진입
    strategy.on_tick({'upbit_price': 54000, 'binance_price': 60})
    assert strategy.should_enter()
    strategy.state["in_position"] = True

    # 청산 → 쿨다운 시작
    strategy.on_tick({'upbit_price': 61200, 'binance_price': 60})
    assert strategy.should_exit()
    strategy.state["in_position"] = False
    strategy.on_exit()  # on_exit()에서 cooldown 설정

    # 쿨다운 중 → 재진입 차단
    # on_exit()에서 cooldown=2 설정, on_tick에서 1씩 감소
    strategy.on_tick({'upbit_price': 54000, 'binance_price': 60})
    assert not strategy.should_enter()  # cooldown: 2→1 (on_tick 감소 후 1)

    strategy.on_tick({'upbit_price': 54000, 'binance_price': 60})
    assert strategy.should_enter()  # cooldown: 1→0 (on_tick 감소 후 0, 진입 가능)


def test_lead_lag_min_hold():
    """최소 보유 틱 미달 시 청산 차단"""
    config = {
        "entry_threshold": -0.05,
        "exit_threshold": 0.01,
        "fx_rate": 1000.0,
        "min_hold_ticks": 3,
        "cooldown_ticks": 0,
    }
    strategy = LeadLagScalper(config)

    strategy.on_tick({'upbit_price': 54000, 'binance_price': 60})
    assert strategy.should_enter()
    strategy.state["in_position"] = True

    # +2% 복귀지만 아직 1틱만 보유 → 청산 안 함
    strategy.on_tick({'upbit_price': 61200, 'binance_price': 60})
    assert not strategy.should_exit()  # ticks=1

    strategy.on_tick({'upbit_price': 61200, 'binance_price': 60})
    assert not strategy.should_exit()  # ticks=2

    strategy.on_tick({'upbit_price': 61200, 'binance_price': 60})
    assert strategy.should_exit()  # ticks=3 → 최소 보유 충족


# ═══ Momentum Breakout ═══

def test_momentum_breakout():
    config = {
        "lookback": 3,
        "volume_multiplier": 1.5,
        "trail_pct": 0.02,
        "stop_loss_pct": 0.03,
        "min_hold_ticks": 0,  # 테스트용
    }
    strategy = MomentumBreakout(config)

    strategy.on_tick({'price': 100, 'volume': 10})
    assert not strategy.should_enter()
    strategy.on_tick({'price': 105, 'volume': 12})
    assert not strategy.should_enter()
    strategy.on_tick({'price': 102, 'volume': 11})
    assert not strategy.should_enter()

    # breakout
    strategy.on_tick({'price': 110, 'volume': 20})
    assert strategy.should_enter()
    strategy.state["in_position"] = True
    strategy.on_enter()

    # 상승
    strategy.on_tick({'price': 115, 'volume': 15})
    assert not strategy.should_exit()

    # 소폭 하락 (112.7 위)
    strategy.on_tick({'price': 113, 'volume': 10})
    assert not strategy.should_exit()

    # trailing stop (115 * 0.98 = 112.7)
    strategy.on_tick({'price': 112, 'volume': 10})
    assert strategy.should_exit()


def test_momentum_breakout_stop_loss():
    """Stop Loss는 최소 보유 틱 무시하고 즉시 발동"""
    config = {
        "lookback": 3,
        "volume_multiplier": 1.5,
        "trail_pct": 0.02,
        "stop_loss_pct": 0.03,
        "min_hold_ticks": 10,  # 높은 최소 보유 → 하지만 stop loss는 무시
    }
    strategy = MomentumBreakout(config)

    strategy.on_tick({'price': 100, 'volume': 10})
    strategy.on_tick({'price': 105, 'volume': 12})
    strategy.on_tick({'price': 102, 'volume': 11})
    strategy.on_tick({'price': 110, 'volume': 20})
    assert strategy.should_enter()
    strategy.state["in_position"] = True
    strategy.on_enter()

    # 즉시 급락 → stop loss (110 * 0.97 = 106.7)
    strategy.on_tick({'price': 106, 'volume': 10})
    assert strategy.should_exit()  # min_hold=10이지만 stop loss 우선


# ═══ DailyRiskManager ═══

def test_risk_manager_daily_limit():
    """일일 손실 한도 초과 시 거래 차단"""
    rm = DailyRiskManager(max_daily_loss=1000.0, max_consecutive_losses=10)

    rm.update_result(-500.0)
    assert rm.check_trade_allowed()

    rm.update_result(-600.0)
    assert not rm.check_trade_allowed()  # 1100 >= 1000


def test_risk_manager_consecutive():
    """연속 손실 한도 초과 시 거래 차단"""
    rm = DailyRiskManager(max_daily_loss=999999.0, max_consecutive_losses=3)

    rm.update_result(-1.0)
    rm.update_result(-1.0)
    assert rm.check_trade_allowed()

    rm.update_result(-1.0)
    assert not rm.check_trade_allowed()  # 3연패


def test_risk_manager_reset():
    """수익 시 연속 카운터 리셋, 일일 리셋"""
    rm = DailyRiskManager(max_daily_loss=1000.0, max_consecutive_losses=3)

    rm.update_result(-1.0)
    rm.update_result(-1.0)
    rm.update_result(100.0)  # 수익 → 연속 리셋
    assert rm.consecutive_losses == 0

    rm.reset_daily()
    assert rm.current_loss == 0.0


# ═══ SlippageModel ═══

def test_slippage_always_positive():
    """슬리피지는 항상 양수"""
    sm = SlippageModel(constant_slippage_bps=2.0, latency_ms=50, impact_factor=0.1)
    for side in ["buy", "sell"]:
        slip = sm.calculate_slippage(order_size=1.0, current_price=60000, side=side, volatility=0.01)
        assert slip > 0

def test_slippage_increases_with_size():
    """주문 크기 증가 시 슬리피지 증가 (market impact)"""
    sm = SlippageModel(constant_slippage_bps=2.0, latency_ms=50, impact_factor=0.1)
    slip_small = sm.calculate_slippage(order_size=0.1, current_price=60000, side="buy")
    slip_large = sm.calculate_slippage(order_size=10.0, current_price=60000, side="buy")
    assert slip_large > slip_small

def test_slippage_increases_with_volatility():
    """변동성 증가 시 슬리피지 증가"""
    sm = SlippageModel(constant_slippage_bps=2.0, latency_ms=50, impact_factor=0.1)
    slip_calm = sm.calculate_slippage(order_size=1.0, current_price=60000, side="buy", volatility=0.001)
    slip_wild = sm.calculate_slippage(order_size=1.0, current_price=60000, side="buy", volatility=0.05)
    assert slip_wild > slip_calm


# ═══ BacktestEngine ═══

def test_backtest_engine_basic():
    """백테스트 엔진: 상승 시나리오에서 수익 발생"""
    config = {
        "lookback": 3, "volume_multiplier": 1.5,
        "trail_pct": 0.02, "stop_loss_pct": 0.03, "min_hold_ticks": 0,
    }
    strategy = MomentumBreakout(config)
    sm = SlippageModel(constant_slippage_bps=1.0, latency_ms=10, impact_factor=0.01)
    engine = BacktestEngine(strategy, sm, initial_capital=1000000)

    data = pd.DataFrame([
        {"price": 100, "volume": 10, "volatility": 0.01},
        {"price": 105, "volume": 12, "volatility": 0.01},
        {"price": 102, "volume": 11, "volatility": 0.01},
        {"price": 110, "volume": 20, "volatility": 0.01},  # breakout entry
        {"price": 115, "volume": 15, "volatility": 0.01},  # hold
        {"price": 120, "volume": 15, "volatility": 0.01},  # hold
        {"price": 116, "volume": 10, "volatility": 0.01},  # trailing stop (120*0.98=117.6 > 116)
    ])

    engine.run(data)
    results = engine.get_results()
    assert results["total_trades"] == 1
    assert len(results["equity"]) == 7
    assert results["trades"][0]["pnl"] > 0  # 수익 거래


# ═══ 추가 커버리지 테스트 ═══

def test_lead_lag_stop_loss():
    """LeadLag: 진입 후 가격 급락 시 손절"""
    config = {
        "entry_threshold": -0.05,
        "exit_threshold": 0.01,
        "fx_rate": 1000.0,
        "min_hold_ticks": 0,
        "cooldown_ticks": 0,
        "max_loss_pct": 0.03,  # 3% 손절
    }
    strategy = LeadLagScalper(config)

    strategy.on_tick({'upbit_price': 54000, 'binance_price': 60})
    assert strategy.should_enter()
    strategy.state["in_position"] = True
    strategy.state["entry_price"] = 54000
    strategy.state["_current_local_price"] = 54000
    strategy.on_enter()

    # 3% 이상 하락 → 손절 (54000 * 0.97 = 52380)
    strategy.state["_current_local_price"] = 52000
    assert strategy.should_exit()


def test_slippage_default_zero_impact():
    """SlippageModel: 기본 impact_factor=0이면 base slippage만 적용"""
    sm = SlippageModel(constant_slippage_bps=2.0, latency_ms=0)
    slip = sm.calculate_slippage(order_size=1.0, current_price=10000, side="buy")
    # 2 bps of 10000 = 2.0
    assert abs(slip - 2.0) < 0.01


def test_slippage_negative_volatility_guard():
    """SlippageModel: 음수 변동성은 0으로 클램핑"""
    sm = SlippageModel(constant_slippage_bps=2.0, latency_ms=50)
    slip = sm.calculate_slippage(order_size=1.0, current_price=10000, side="buy", volatility=-0.1)
    assert slip > 0  # 음수 변동성이 슬리피지를 줄이지 않음


def test_risk_manager_breakeven():
    """DailyRiskManager: 보합(pnl=0)은 수익으로 취급 → 연속 손실 리셋"""
    rm = DailyRiskManager(max_daily_loss=1000.0, max_consecutive_losses=3)
    rm.update_result(-1.0)
    rm.update_result(-1.0)
    rm.update_result(0.0)  # 보합 → 연속 리셋
    assert rm.consecutive_losses == 0


def test_momentum_position_size_from_config():
    """MomentumBreakout: config에서 position_size 읽기"""
    strategy = MomentumBreakout({"lookback": 5, "position_size": 2.5})
    assert strategy.position_size() == 2.5


# ═══ OU Calibrator ═══

def test_ou_calibrator_mean_reverting():
    """OU: 평균 회귀 시계열에서 z-score 정상 계산"""
    ou = OUCalibrator(lookback=50)
    np.random.seed(42)
    # OU 시뮬레이션: mu=0, theta=0.5
    s = 0.0
    for _ in range(50):
        s += 0.5 * (0.0 - s) + np.random.normal(0, 0.01)
        ou.update(s)

    assert ou.is_mean_reverting()
    zscore = ou.get_zscore(s)
    assert zscore is not None
    assert -5.0 < zscore < 5.0


def test_ou_calibrator_insufficient_data():
    """OU: 데이터 부족 시 None 반환"""
    ou = OUCalibrator(lookback=60)
    for i in range(5):
        ou.update(float(i) * 0.01)
    assert ou.get_zscore(0.05) is None
    assert not ou.is_mean_reverting()


def test_ou_leadlag_fallback():
    """LeadLag: OU 데이터 부족 시 기존 고정 임계값으로 폴백"""
    config = {
        "entry_threshold": -0.05,
        "exit_threshold": 0.01,
        "fx_rate": 1000.0,
        "min_hold_ticks": 0,
        "cooldown_ticks": 0,
        "ou_lookback": 100,  # 높게 설정 → OU 캘리브레이션 안 됨
    }
    strategy = LeadLagScalper(config)

    # 5틱만 → OU 미활성 → 고정 임계값 폴백
    strategy.on_tick({'upbit_price': 54000, 'binance_price': 60})
    assert strategy.should_enter()  # -10% < -5% → 진입


# ═══ ATR Calculator ═══

def test_atr_basic():
    """ATR: 일정 변동 시 ATR 계산"""
    atr = ATRCalculator(period=3)
    prices = [100, 102, 98, 103, 97]
    for p in prices:
        atr.update(p)
    val = atr.get_atr()
    assert val is not None
    assert val > 0


def test_atr_pct():
    """ATR: 가격 대비 ATR 비율"""
    atr = ATRCalculator(period=3)
    for p in [100, 101, 99, 102]:
        atr.update(p)
    pct = atr.get_atr_pct(100)
    assert pct is not None
    assert 0 < pct < 0.1  # 합리적 범위


def test_atr_insufficient_data():
    """ATR: 데이터 부족 시 None"""
    atr = ATRCalculator(period=14)
    atr.update(100)
    atr.update(101)
    assert atr.get_atr() is None


def test_momentum_atr_dynamic_stop():
    """Momentum: ATR 활성 시 동적 스탑 사용"""
    config = {
        "lookback": 3, "volume_multiplier": 1.5,
        "trail_pct": 0.01, "stop_loss_pct": 0.02,
        "min_hold_ticks": 0, "atr_period": 3,
        "atr_trail_mult": 2.0, "atr_stop_mult": 1.5,
    }
    strategy = MomentumBreakout(config)

    # ATR이 계산되면 동적 스탑 사용
    strategy.on_tick({'price': 100, 'volume': 10})
    strategy.on_tick({'price': 105, 'volume': 12})
    strategy.on_tick({'price': 102, 'volume': 11})
    strategy.on_tick({'price': 110, 'volume': 20})
    assert strategy.should_enter()
    strategy.state["in_position"] = True
    strategy.on_enter()

    # ATR 기반 스탑이 고정 스탑과 다른 값인지 확인
    dynamic_stop = strategy._get_stop_loss_pct()
    dynamic_trail = strategy._get_trail_pct()
    assert dynamic_stop != strategy.stop_loss_pct or dynamic_trail != strategy.trail_pct


# ═══ Kelly Position Sizer ═══

def test_kelly_fallback_insufficient_trades():
    """Kelly: 최소 거래 미달 시 고정 사이즈 폴백"""
    sizer = KellyPositionSizer(max_fraction=0.25, min_trades=10)
    # 5거래만 기록 → 폴백
    for _ in range(5):
        sizer.update(1000.0)
    size = sizer.get_trade_size(5000000.0)
    assert size == min(1000000.0, 5000000.0)  # Config.TRADE_SIZE_KRW 폴백


def test_kelly_winning_strategy():
    """Kelly: 높은 승률 → 큰 포지션"""
    sizer = KellyPositionSizer(max_fraction=0.25, min_trades=5)
    # 8승 2패
    for _ in range(8):
        sizer.update(50000.0)   # 5만원 수익
    for _ in range(2):
        sizer.update(-20000.0)  # 2만원 손실
    size = sizer.get_trade_size(5000000.0)
    # Kelly가 활성화되고, 고정 100만원보다 클 수 있음
    assert size > 0
    assert size <= 5000000.0 * 0.25  # max_fraction 제한


def test_kelly_losing_strategy():
    """Kelly: 낮은 승률 → 최소 포지션"""
    sizer = KellyPositionSizer(max_fraction=0.25, min_trades=5)
    # 2승 8패
    for _ in range(2):
        sizer.update(10000.0)
    for _ in range(8):
        sizer.update(-50000.0)
    size = sizer.get_trade_size(5000000.0)
    # Kelly f* 음수 → 최소 5% 클램프
    assert size >= 100000  # 최소 10만원


# ═══ Donchian Channel 앙상블 ═══

def test_donchian_single_channel():
    """Donchian: 단일 채널 상/하단 밴드"""
    ch = DonchianChannel(period=3)
    ch.update(100)
    ch.update(110)
    ch.update(90)
    assert ch.ready
    assert ch.upper == 110
    assert ch.lower == 90
    assert ch.mid == 100


def test_donchian_ensemble_breakout():
    """Donchian 앙상블: 과반수 채널 돌파 시 시그널"""
    ens = DonchianEnsemble(periods=[3, 5])
    # 3틱 채널만 채움 (5틱은 미준비)
    for p in [100, 102, 98]:
        ens.update(p)
    # 3틱 채널 준비됨, 5틱 미준비 → min_votes=2 불충족
    assert not ens.breakout_signal(105)

    # 5틱 채널도 채움
    ens.update(101)
    ens.update(99)
    # 이제 둘 다 준비 → 105가 두 채널 모두 돌파
    assert ens.breakout_signal(105)
    # 100은 돌파 아님
    assert not ens.breakout_signal(100)


def test_donchian_ensemble_breakdown():
    """Donchian 앙상블: 하향 이탈 시그널"""
    ens = DonchianEnsemble(periods=[3, 5])
    for p in [100, 102, 98, 101, 99]:
        ens.update(p)
    # 가장 짧은(3틱) 채널 하단 = 99 → 97은 이탈
    assert ens.breakdown_signal(97)
    assert not ens.breakdown_signal(100)


# ═══ EWMA 레짐 감지 ═══

def test_regime_normal_default():
    """RegimeDetector: 초기/데이터 부족 시 NORMAL"""
    rd = RegimeDetector()
    assert rd.regime == RegimeDetector.NORMAL
    assert rd.get_position_multiplier() == 1.0
    assert rd.get_stop_multiplier() == 1.0


def test_regime_high_volatility():
    """RegimeDetector: 급변 시 HIGH_VOL 감지"""
    rd = RegimeDetector(fast_span=3, slow_span=10, high_threshold=1.5)
    # 안정적 구간 (장기 변동성 세팅)
    for p in [100, 100.1, 99.9, 100.05, 99.95,
              100.02, 99.98, 100.01, 99.99, 100.03,
              100, 99.97, 100.04, 99.96, 100.02,
              99.99, 100.01, 100, 99.98, 100.03]:
        rd.update(p)
    # 급변 구간
    for p in [105, 95, 108, 92]:
        rd.update(p)
    assert rd.regime == RegimeDetector.HIGH_VOL
    assert rd.get_position_multiplier() == 0.5
    assert rd.get_stop_multiplier() == 1.5


def test_regime_multipliers_in_momentum():
    """Momentum: 레짐 배수가 스탑에 적용되는지 확인"""
    config = {
        "lookback": 3, "volume_multiplier": 1.5,
        "trail_pct": 0.01, "stop_loss_pct": 0.02,
        "min_hold_ticks": 0, "atr_period": 3,
        "use_donchian": False,  # Donchian 비활성화 (기존 방식 테스트)
    }
    strategy = MomentumBreakout(config)
    # 레짐 감지기가 존재하는지 확인
    assert hasattr(strategy, 'regime')
    assert strategy.regime.regime == RegimeDetector.NORMAL


# ═══ Volume Percentile Filter ═══

def test_volume_percentile_surge():
    """VolumePercentileFilter: 90th 퍼센타일 이상 시 surge"""
    vf = VolumePercentileFilter(window=10, threshold_pct=90.0)
    # 10개 거래량: 1~10
    for v in range(1, 11):
        vf.update(float(v))
    assert vf.ready
    assert vf.is_surge(15.0)    # 15 > 90th pct of [1..10]
    assert not vf.is_surge(5.0)  # 5 < 90th pct


def test_volume_percentile_not_ready():
    """VolumePercentileFilter: 데이터 부족 시 False"""
    vf = VolumePercentileFilter(window=50)
    vf.update(100.0)
    assert not vf.ready
    assert not vf.is_surge(200.0)


# ═══ VWAP ═══

def test_vwap_basic():
    """VWAP: 기본 계산"""
    vw = VWAPCalculator(window=20)
    # 가격 100, 거래량 10 × 10틱
    for _ in range(10):
        vw.update(100.0, 10.0)
    assert vw.ready
    vwap = vw.get_vwap()
    assert vwap is not None
    assert abs(vwap - 100.0) < 0.01


def test_vwap_deviation():
    """VWAP: 이탈도 계산"""
    vw = VWAPCalculator(window=20)
    for _ in range(10):
        vw.update(100.0, 10.0)
    dev = vw.get_deviation(105.0)
    assert dev is not None
    assert abs(dev - 0.05) < 0.001  # 5% 위
    assert vw.is_above_vwap(105.0)
    assert vw.is_below_vwap(95.0, threshold=-0.04)


# ═══ Trade Flow Imbalance ═══

def test_tfi_buying_pressure():
    """TFI: 연속 상승 시 매수 압력"""
    tfi = TradeFlowImbalance(window=5)
    prices = [100, 101, 102, 103, 104, 105]
    for p in prices:
        tfi.update(float(p), 10.0)
    assert tfi.ready
    assert tfi.is_buying_pressure(threshold=0.3)
    assert not tfi.is_selling_pressure()


def test_tfi_selling_pressure():
    """TFI: 연속 하락 시 매도 압력"""
    tfi = TradeFlowImbalance(window=5)
    prices = [105, 104, 103, 102, 101, 100]
    for p in prices:
        tfi.update(float(p), 10.0)
    assert tfi.ready
    assert tfi.is_selling_pressure(threshold=-0.3)
    assert not tfi.is_buying_pressure()


def test_tfi_neutral():
    """TFI: 혼합 시 중립"""
    tfi = TradeFlowImbalance(window=6)
    prices = [100, 101, 100, 101, 100, 101, 100]
    for p in prices:
        tfi.update(float(p), 10.0)
    tfi_val = tfi.get_tfi()
    assert tfi_val is not None
    assert abs(tfi_val) < 0.5  # 중립 근처


# ═══ Multi-Premium (빗각) ═══

def test_multi_premium_entry_candidates():
    """MultiPremium: 역프리미엄 코인 진입 후보 선정"""
    strategy = MultiPremiumStrategy(
        symbols=["BTC", "ETH", "XRP"],
        config={"fx_rate": 1000.0, "entry_threshold": -0.05, "max_positions": 2}
    )

    # BTC: 정프리미엄 (진입 안 함)
    strategy.on_tick("BTC", "upbit", 61000)
    strategy.on_tick("BTC", "binance", 60)

    # ETH: 역프리미엄 -10% (진입 후보)
    strategy.on_tick("ETH", "upbit", 5400000)
    strategy.on_tick("ETH", "binance", 6000)

    # XRP: 역프리미엄 -15% (진입 후보, 더 큼)
    strategy.on_tick("XRP", "upbit", 850)
    strategy.on_tick("XRP", "binance", 1.0)

    candidates = strategy.get_entry_candidates()
    assert len(candidates) == 2
    assert candidates[0] == "XRP"  # 더 큰 역프리미엄이 먼저
    assert candidates[1] == "ETH"


def test_multi_premium_exit():
    """MultiPremium: 프리미엄 복귀 시 청산"""
    strategy = MultiPremiumStrategy(
        symbols=["ETH"],
        config={"fx_rate": 1000.0, "entry_threshold": -0.05, "exit_threshold": 0.01}
    )

    # 역프리미엄 진입
    strategy.on_tick("ETH", "upbit", 5400000)
    strategy.on_tick("ETH", "binance", 6000)
    strategy.enter("ETH")
    assert "ETH" in strategy.positions

    # 프리미엄 복귀
    strategy.on_tick("ETH", "upbit", 6120000)  # +2%
    strategy.on_tick("ETH", "binance", 6000)

    exits = strategy.get_exit_candidates()
    assert "ETH" in exits


def test_multi_premium_max_positions():
    """MultiPremium: 최대 포지션 수 제한"""
    strategy = MultiPremiumStrategy(
        symbols=["BTC", "ETH", "XRP"],
        config={"fx_rate": 1000.0, "entry_threshold": -0.05, "max_positions": 1}
    )

    # 모두 역프리미엄
    for sym, upbit, binance in [("BTC", 54000, 60), ("ETH", 5400000, 6000), ("XRP", 850, 1.0)]:
        strategy.on_tick(sym, "upbit", upbit)
        strategy.on_tick(sym, "binance", binance)

    # 1개만 진입 가능
    candidates = strategy.get_entry_candidates()
    assert len(candidates) == 1
    strategy.enter(candidates[0])

    # 추가 진입 불가
    assert len(strategy.get_entry_candidates()) == 0


def test_multi_premium_dashboard_data():
    """MultiPremium: 대시보드 데이터 정상 반환"""
    strategy = MultiPremiumStrategy(
        symbols=["BTC", "ETH"],
        config={"fx_rate": 1400.0}
    )
    strategy.on_tick("BTC", "upbit", 104000000)
    strategy.on_tick("BTC", "binance", 70000)
    strategy.on_tick("ETH", "upbit", 5000000)
    strategy.on_tick("ETH", "binance", 3500)

    data = strategy.get_dashboard_data()
    assert len(data) == 2
    assert all("symbol" in d and "premium" in d for d in data)
