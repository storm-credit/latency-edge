# CLAUDE.md

## Project overview
- Latency Edge: BTC 자동매매 시스템 (모의 투자)
- Backend: FastAPI (Python) - WebSocket 기반 실시간 데이터 + 전략 엔진
- Frontend: Next.js 14 (TypeScript) - TradingView 스타일 대시보드
- Backend port: 8009, Frontend port: 3000

## Architecture
- `src/api/server.py` : FastAPI 서버, WebSocket 브로드캐스트, 전략 오케스트레이션
- `src/strategies/` : 매매 전략 (LeadLag, MomentumBreakout)
- `src/collectors/` : Binance/Upbit WebSocket 수집기
- `src/risk/` : DailyRiskManager (일일 손실 한도, 연속 손실 차단)
- `src/backtest/` : BacktestEngine + SlippageModel
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
- Current: 13 tests covering strategies, risk manager, slippage, backtest engine
- When adding strategy parameters, update tests with backward-compatible defaults

## Key concepts
- Lead-Lag: Binance(선행) price change → Upbit(후행) price follows
- Kimchi Premium (김치 프리미엄): KRW/USD price gap between exchanges
- Entry: premium <= -2.0% (역프리미엄), Exit: premium >= +0.5%
- Momentum Breakout: N-tick high breakout + volume surge, trailing stop + stop loss
- Per-strategy independent portfolios (500만원 each, total 1000만원)
