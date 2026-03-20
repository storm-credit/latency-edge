# CLAUDE.md

## Project overview
- Latency Edge: BTC 자동매매 시스템 (모의 투자)
- Backend: FastAPI (Python) - WebSocket 기반 실시간 데이터 + 전략 엔진
- Frontend: Next.js 14 (TypeScript) - TradingView 스타일 대시보드
- Backend port: 8009, Frontend port: 3100 (Docker), 3000 (dev)

## Architecture
- `src/api/server.py` : FastAPI 서버, WebSocket 브로드캐스트, 전략 오케스트레이션
- `src/strategies/` : 매매 전략 (LeadLag, MomentumBreakout)
- `src/collectors/` : Binance/Upbit WebSocket 수집기
- `src/risk/` : DailyRiskManager + KellyPositionSizer
- `src/backtest/` : BacktestEngine + SlippageModel
- `src/features/` : OU캘리브레이션, ATR, Donchian, EWMA레짐, VWAP, TFI, 거래량필터
- `src/config.py` : 중앙 설정 관리 (환경변수 오버라이드 가능)
- `dashboard-web/` : Next.js 프론트엔드

## Rules
- Do not edit .env files directly
- Always run `python -m pytest tests/ -v` before finalizing changes
- Prefer minimal diffs
- Keep Korean comments (한글 주석 유지)
- Use `src/config.py` for all configuration values - no hardcoded magic numbers
- Fee calculation must be bilateral (매수/매도 양방향 수수료 0.05%)
- PnL must use actual KRW invested vs KRW recovered (not price difference)
- No leverage (1x spot only, no margin/shorting)
- WebSocket broadcast must use dead-list pattern (not remove during iteration)
- Signal history uses deque(maxlen=500), never unbounded list

## ECC Integration
- Rules: `.claude/rules/` (common + python + typescript)
- Skills: `.claude/skills/` (14 skills — TDD, security, patterns, etc.)
- Agents: `.claude/agents/` (6 — planner, code-reviewer, security-reviewer, etc.)
- Commands: `.claude/commands/` (9 — /plan, /tdd, /code-review, etc.)
- Hooks: `.claude/hooks/` (post-edit Python lint, stop-phase debug check)

## Testing
- Test framework: pytest + pytest-asyncio
- Run: `python -m pytest tests/ -v`
- Current: 49 tests covering strategies, risk, slippage, backtest, OU, ATR, Donchian, regime, VWAP, TFI, Kelly
- When adding strategy parameters, update tests with backward-compatible defaults

## Key concepts
- Lead-Lag: OU z-score 기반 동적 김프 진입/청산 (폴백: 고정 -2%/+0.5%)
- Momentum: Donchian 앙상블 + ATR 동적 스탑 + 거래량 퍼센타일 + VWAP + TFI
- EWMA 레짐 감지: 고변동성 시 포지션 축소 + 스탑 확대
- Kelly 포지션 사이징: 승률/손익비 기반 Half-Kelly (폴백: 고정 사이즈)
- Per-strategy independent portfolios (500만원 each, total 1000만원)

## Docker
- `docker compose up -d --build` → backend:8009 + frontend:3100
- Port 3000 is reserved for ask-anything project
