---
name: codebase-overview
description: Explain project architecture, folder structure, and where things live
---

# Codebase Overview - Latency Edge

## Backend (Python / FastAPI)

### Core
- `src/config.py` : 중앙 설정 (환경변수 오버라이드)
- `src/api/server.py` : FastAPI 앱, WebSocket, 전략 오케스트레이션
- `run_server.py` : 서버 진입점

### Strategies
- `src/strategies/base.py` : BaseStrategy 추상 클래스
- `src/strategies/lead_lag_scalper.py` : 김프 역이용 전략 (cooldown + min_hold)
- `src/strategies/momentum_breakout.py` : 모멘텀 돌파 전략 (trailing stop + stop loss)

### Data Collection
- `src/collectors/binance_ws.py` : Binance BTC-USDT WebSocket
- `src/collectors/upbit_ws.py` : Upbit KRW-BTC WebSocket

### Risk Management
- `src/risk/daily_stop.py` : DailyRiskManager (500K KRW 한도, 5연패 차단)

### Backtesting
- `src/backtest/engine.py` : BacktestEngine (전략 시뮬레이션)
- `src/backtest/slippage.py` : SlippageModel (스프레드 + 변동성 + 마켓임팩트)

## Frontend (Next.js / TypeScript)
- `dashboard-web/src/app/page.tsx` : 메인 대시보드 (3패널 레이아웃)
- `dashboard-web/src/app/globals.css` : 다크 테마 스타일
- `dashboard-web/src/app/layout.tsx` : 루트 레이아웃 + 폰트

## Tests
- `tests/test_strategies.py` : 13 tests (전략, 리스크, 슬리피지, 백테스트)

## Conventions
- All config via `src/config.py`, never hardcode
- Korean UI, Korean comments in code
- WebSocket reconnection with exponential backoff (frontend)
- Strategy state managed via `strategy.state` dict
