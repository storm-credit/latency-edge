"""
CLI dry-run engine (standalone mode).
For the full API server, use: uvicorn src.api.server:app

This module is kept for backward compatibility with direct CLI usage.
"""
import asyncio
from src.api.server import ApiEngine


async def main():
    engine = ApiEngine()
    await engine.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[System] Engine shutdown by user.")
