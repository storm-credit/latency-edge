---
name: deploy
description: Build and deploy backend and frontend services
---

# Deploy

## Local Development
- Backend: `python run_server.py` (port 8009)
- Frontend: `cd dashboard-web && npm run dev` (port 3000)

## Docker
- Build backend: `docker build --target backend -t latency-edge-api .`
- Build frontend: `docker build --target frontend -t latency-edge-web .`

## Environment Variables (via src/config.py)
- `FX_RATE` : KRW/USD 환율 (default: 1400)
- `CAPITAL_PER_STRATEGY` : 전략별 자본 (default: 5000000)
- `TRADE_SIZE_KRW` : 거래 단위 (default: 1000000)
- `FEE_RATE` : 수수료율 (default: 0.0005)
- `MAX_DAILY_LOSS` : 일일 손실 한도 (default: 500000)
- `MAX_CONSECUTIVE_LOSSES` : 최대 연속 손실 (default: 5)
- `PORT` : API 서버 포트 (default: 8009)
- `NEXT_PUBLIC_API_PORT` : 프론트엔드→백엔드 포트 (default: 8009)

## Pre-deploy Checklist
1. `python -m pytest tests/ -v` — all tests pass
2. `cd dashboard-web && npx next build` — frontend builds clean
3. Check `src/config.py` for any hardcoded values
