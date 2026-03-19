---
name: test-runner
description: Run project tests and report results
---

# Test Runner

## Commands
- Full test suite: `python -m pytest tests/ -v`
- With coverage: `python -m pytest tests/ --cov=src --cov-report=term-missing`
- Single test: `python -m pytest tests/test_strategies.py::test_name -v`

## Test Structure
- `tests/test_strategies.py` : All strategy, risk, slippage, and backtest tests

## Rules
- Always run tests after modifying strategy logic, risk management, or backtest engine
- When adding new strategy parameters, include backward-compatible defaults in existing tests
- Stop loss tests should set `min_hold_ticks` high to verify stop loss bypasses hold requirement
- Cooldown tests must account for decrement timing (happens in `on_tick`)
