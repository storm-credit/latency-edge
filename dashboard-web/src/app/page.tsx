"use client";

import { useEffect, useState, useRef } from "react";
import { createChart, AreaSeries, IChartApi, ISeriesApi } from "lightweight-charts";

interface MarketState { upbit_price: number; binance_price: number; price: number; volume: number; }
interface Signal { type: string; strategy: string; action: string; local: number; global: number; pnl?: number; ts?: number; }
interface Portfolio { KRW: number; BTC: number; Equity: number; }

const fmt = (n: number) => {
  if (n >= 1e8) return (n / 1e8).toFixed(2) + "억";
  if (n >= 1e6) return (n / 1e4).toFixed(0) + "만";
  if (n >= 1e4) return (n / 1e4).toFixed(1) + "만";
  return n.toLocaleString();
};
const fmtP = (n: number) => n.toLocaleString("ko-KR");
const fmtUSD = (n: number) => "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtBTC = (n: number) => n === 0 ? "0.0000" : n < 0.001 ? n.toFixed(8) : n.toFixed(4);
const ago = (ts: number) => {
  const s = Math.floor((Date.now() - ts) / 1000);
  return s < 60 ? `${s}초 전` : s < 3600 ? `${Math.floor(s / 60)}분 전` : `${Math.floor(s / 3600)}시간 전`;
};

export default function Dashboard() {
  const chartRef = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const areaSeries = useRef<ISeriesApi<"Area"> | null>(null);
  const [equityHistory, setEquityHistory] = useState<number[]>([10000000]);

  const [m, setM] = useState<MarketState>({ upbit_price: 0, binance_price: 0, price: 0, volume: 0 });
  const [p, setP] = useState<Portfolio>({ KRW: 10000000, BTC: 0, Equity: 10000000 });
  const [sigs, setSigs] = useState<Signal[]>([]);
  const [live, setLive] = useState(false);
  const [counts, setCounts] = useState({ buy: 0, sell: 0 });
  const [tab, setTab] = useState<"all" | "buy" | "sell">("all");
  const [strats, setStrats] = useState({ leadlag: true, momentum: true });
  const [panel, setPanel] = useState<"signals" | "strategies">("signals");
  const [fxRate, setFxRate] = useState(1400);

  // Chart
  useEffect(() => {
    if (!chartRef.current || chart.current) return;
    chart.current = createChart(chartRef.current, {
      width: chartRef.current.clientWidth, height: chartRef.current.clientHeight,
      layout: { background: { color: "transparent" }, textColor: "#5a5a66", fontSize: 11, fontFamily: "JetBrains Mono, monospace" },
      grid: { vertLines: { visible: false }, horzLines: { color: "rgba(255,255,255,0.03)" } },
      timeScale: { timeVisible: true, secondsVisible: false, borderVisible: false, rightOffset: 3 },
      rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.08, bottom: 0.08 } },
      crosshair: {
        vertLine: { color: "rgba(59,130,246,0.4)", width: 1, style: 2, labelVisible: false },
        horzLine: { color: "rgba(59,130,246,0.4)", width: 1, style: 2, labelBackgroundColor: "#3b82f6" },
      },
    });
    areaSeries.current = chart.current.addSeries(AreaSeries, {
      lineColor: "#3b82f6", lineWidth: 2,
      topColor: "rgba(59,130,246,0.28)", bottomColor: "rgba(59,130,246,0.02)",
      priceLineVisible: false, lastValueVisible: true,
      crosshairMarkerRadius: 4, crosshairMarkerBorderColor: "#3b82f6", crosshairMarkerBackgroundColor: "#0b0b11",
    });
    const ro = new ResizeObserver(() => {
      if (chartRef.current && chart.current) chart.current.applyOptions({ width: chartRef.current.clientWidth, height: chartRef.current.clientHeight });
    });
    ro.observe(chartRef.current);
    return () => { ro.disconnect(); chart.current?.remove(); chart.current = null; areaSeries.current = null; };
  }, []);

  // [P0-5] WS 재연결 (지수 백오프) + [P0-3] FX Rate 동기화
  useEffect(() => {
    const port = process.env.NEXT_PUBLIC_API_PORT || "8009";
    let ws: WebSocket | null = null;
    let retryDelay = 1000;
    let retryTimer: ReturnType<typeof setTimeout>;
    let unmounted = false;

    function connect() {
      if (unmounted) return;
      ws = new WebSocket(`ws://localhost:${port}/ws`);
      ws.onopen = () => { setLive(true); retryDelay = 1000; };
      ws.onclose = () => {
        setLive(false);
        if (!unmounted) {
          retryTimer = setTimeout(connect, retryDelay);
          retryDelay = Math.min(retryDelay * 2, 30000);
        }
      };
      ws.onerror = () => { ws?.close(); };
      ws.onmessage = (e) => {
        try {
          const d = JSON.parse(e.data);
          if (d.type === "tick") {
            setM(d.state);
            if (d.portfolio) {
              setP(d.portfolio);
              setEquityHistory(prev => [...prev.slice(-59), d.portfolio.Equity]);
            }
            if (d.fx_rate) setFxRate(d.fx_rate);
            if (areaSeries.current && d.state.upbit_price > 0) {
              try { areaSeries.current.update({ time: Math.floor(Date.now() / 1000) as any, value: d.state.upbit_price }); } catch {}
            }
          } else if (d.type === "signal") {
            setSigs(prev => [{ ...d, ts: Date.now() }, ...prev].slice(0, 100));
            setCounts(prev => ({ buy: prev.buy + (d.action === "ENTRY" ? 1 : 0), sell: prev.sell + (d.action === "EXIT" ? 1 : 0) }));
          }
        } catch {}
      };
    }
    connect();
    return () => { unmounted = true; clearTimeout(retryTimer); ws?.close(); };
  }, []);

  // [P0-3] 하드코딩된 1400 → 백엔드에서 받은 fxRate 사용
  const prem = m.binance_price > 0 ? ((m.upbit_price - m.binance_price * fxRate) / (m.binance_price * fxRate)) * 100 : 0;
  const pnl = p.Equity - 10000000;
  const pnlPct = (pnl / 10000000) * 100;
  const wins = sigs.filter(s => s.action === "EXIT" && (s.pnl ?? 0) > 0).length;
  const winRate = counts.sell > 0 ? (wins / counts.sell * 100) : 0;
  const filtered = tab === "all" ? sigs : tab === "buy" ? sigs.filter(s => s.action === "ENTRY") : sigs.filter(s => s.action === "EXIT");

  return (
    <div className="h-screen flex flex-col" style={{ background: "var(--bg)" }}>

      {/* ═══ 상단바 ═══ */}
      <header className="flex items-center justify-between px-4 shrink-0" style={{ height: 44, background: "var(--bg2)", borderBottom: "1px solid var(--border)" }}>
        <div className="flex items-center gap-2.5">
          <div style={{ width: 26, height: 26, borderRadius: 7, background: "linear-gradient(135deg, #3b82f6, #8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "#fff", fontSize: 10, fontWeight: 800 }}>LE</span>
          </div>
          <span style={{ fontSize: 13, fontWeight: 700 }}>Latency Edge</span>
          <div style={{ width: 1, height: 14, background: "var(--border)", margin: "0 4px" }} />
          <span className="mono" style={{ fontSize: 10, color: "var(--t3)" }}>모의 투자</span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2" style={{ background: "rgba(34,197,94,0.08)", borderRadius: 6, padding: "3px 10px" }}>
            <span className="mono" style={{ fontSize: 11, fontWeight: 700, color: "var(--green)" }}>{counts.buy}</span>
            <span style={{ fontSize: 10, color: "var(--t3)" }}>매수</span>
          </div>
          <div className="flex items-center gap-2" style={{ background: "rgba(239,68,68,0.08)", borderRadius: 6, padding: "3px 10px" }}>
            <span className="mono" style={{ fontSize: 11, fontWeight: 700, color: "var(--red)" }}>{counts.sell}</span>
            <span style={{ fontSize: 10, color: "var(--t3)" }}>매도</span>
          </div>
          <div className="flex items-center gap-2">
            <div className={live ? "live-pulse" : ""} style={live ? {} : { width: 7, height: 7, borderRadius: "50%", background: "var(--red)" }} />
            <span className="mono" style={{ fontSize: 11, fontWeight: 600, color: live ? "var(--green)" : "var(--red)" }}>
              {live ? "연결됨" : "오프라인"}
            </span>
          </div>
        </div>
      </header>

      {/* ═══ 본문 ═══ */}
      <div className="flex-1 min-h-0 flex">

        {/* ── 좌측 사이드바 ── */}
        <div className="sidebar-left flex flex-col shrink-0" style={{ width: 260, borderRight: "1px solid var(--border)", background: "var(--bg2)" }}>

          {/* 총 자산 */}
          <div style={{ padding: "14px 16px 10px" }}>
            <div className="flex items-center justify-between">
              <span style={{ fontSize: 10, fontWeight: 600, color: "var(--t3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>총 자산</span>
              <span className="badge" style={{ background: "rgba(168,85,247,0.12)", color: "var(--purple)", fontSize: 9 }}>모의</span>
            </div>
            <p className="price-huge" style={{ marginTop: 4 }}>{fmt(p.Equity)}</p>
            <div className="flex items-center gap-2" style={{ marginTop: 2 }}>
              <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: pnl >= 0 ? "var(--green)" : "var(--red)" }}>
                {pnl >= 0 ? "+" : ""}{fmt(pnl)}
              </span>
              <span className="mono" style={{ fontSize: 11, color: pnl >= 0 ? "var(--green)" : "var(--red)", opacity: 0.7 }}>
                ({pnlPct >= 0 ? "+" : ""}{pnlPct.toFixed(2)}%)
              </span>
            </div>
            {/* 미니 자산 추이 */}
            {equityHistory.length > 1 && (() => {
              const min = Math.min(...equityHistory);
              const max = Math.max(...equityHistory);
              const range = max - min || 1;
              const w = 228; const h = 32;
              const pts = equityHistory.map((v, i) => `${(i / (equityHistory.length - 1)) * w},${h - ((v - min) / range) * (h - 4) - 2}`).join(" ");
              const eqColor = pnl >= 0 ? "var(--green)" : "var(--red)";
              return (
                <svg className="equity-sparkline" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
                  <defs><linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={eqColor} stopOpacity="0.2"/><stop offset="100%" stopColor={eqColor} stopOpacity="0"/></linearGradient></defs>
                  <polygon points={`0,${h} ${pts} ${w},${h}`} fill="url(#sparkGrad)" />
                  <polyline points={pts} fill="none" stroke={eqColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              );
            })()}
          </div>

          {/* 요약 */}
          <div className="grid grid-cols-3 gap-1.5" style={{ padding: "0 12px 10px" }}>
            {[
              { label: "현금", value: fmt(p.KRW) },
              { label: "BTC", value: fmtBTC(p.BTC) },
              { label: "승률", value: `${winRate.toFixed(0)}%`, color: winRate >= 50 ? "var(--green)" : undefined },
            ].map(s => (
              <div key={s.label} className="stat-box">
                <p style={{ fontSize: 8, fontWeight: 600, color: "var(--t3)", letterSpacing: "0.1em" }}>{s.label}</p>
                <p className="mono" style={{ fontSize: 12, fontWeight: 700, marginTop: 1, color: s.color }}>{s.value}</p>
              </div>
            ))}
          </div>

          <div style={{ height: 1, background: "var(--border)", margin: "0 12px" }} />

          {/* 시세 */}
          <div style={{ padding: "10px 12px" }}>
            {/* 업비트 */}
            <div style={{ padding: "8px 10px", borderRadius: 8 }}>
              <div className="flex items-center gap-2.5">
                <div style={{ width: 28, height: 28, borderRadius: 7, background: "linear-gradient(135deg, #3b82f6, #60a5fa)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 800, color: "#fff" }}>U</div>
                <div style={{ flex: 1 }}>
                  <div className="flex items-center justify-between">
                    <span style={{ fontSize: 12, fontWeight: 600 }}>업비트</span>
                    <span style={{ fontSize: 9, color: "var(--t3)" }}>KRW-BTC</span>
                  </div>
                  <p className="mono price-big" style={{ marginTop: 2, fontSize: 20 }}>
                    {m.upbit_price > 0 ? fmtP(m.upbit_price) : "---"}
                  </p>
                </div>
              </div>
            </div>

            {/* 바이낸스 */}
            <div style={{ padding: "8px 10px", borderRadius: 8, marginTop: 4 }}>
              <div className="flex items-center gap-2.5">
                <div style={{ width: 28, height: 28, borderRadius: 7, background: "linear-gradient(135deg, #eab308, #facc15)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 800, color: "#1a1a1a" }}>B</div>
                <div style={{ flex: 1 }}>
                  <div className="flex items-center justify-between">
                    <span style={{ fontSize: 12, fontWeight: 600 }}>바이낸스</span>
                    <span style={{ fontSize: 9, color: "var(--t3)" }}>BTC-USDT</span>
                  </div>
                  <p className="mono price-big" style={{ marginTop: 2, fontSize: 20 }}>
                    {m.binance_price > 0 ? fmtUSD(m.binance_price) : "---"}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div style={{ height: 1, background: "var(--border)", margin: "0 12px" }} />

          {/* 김치 프리미엄 */}
          <div style={{ padding: "10px 16px" }}>
            <div className="flex items-center justify-between">
              <span style={{ fontSize: 10, fontWeight: 600, color: "var(--t3)", letterSpacing: "0.08em" }}>김치 프리미엄</span>
              <span className="badge" style={{
                background: prem >= 0 ? "rgba(34,197,94,0.12)" : "rgba(239,68,68,0.12)",
                color: prem >= 0 ? "var(--green)" : "var(--red)", fontSize: 9
              }}>{prem >= 0 ? "프리미엄" : "디스카운트"}</span>
            </div>
            <p className="mono" style={{ fontSize: 28, fontWeight: 800, color: prem >= 0 ? "var(--green)" : "var(--red)", marginTop: 4, letterSpacing: "-0.03em" }}>
              {prem >= 0 ? "+" : ""}{prem.toFixed(3)}%
            </p>
          </div>

          <div style={{ height: 1, background: "var(--border)", margin: "0 12px" }} />

          {/* 빠른 거래 */}
          <div style={{ padding: "10px 12px" }}>
            <p style={{ fontSize: 10, fontWeight: 600, color: "var(--t3)", letterSpacing: "0.08em", marginBottom: 8 }}>빠른 거래</p>
            <div className="flex gap-2">
              <button className="btn btn-buy" style={{ flex: 1 }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
                매수
              </button>
              <button className="btn btn-sell" style={{ flex: 1 }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
                매도
              </button>
            </div>
          </div>

          <div style={{ flex: 1 }} />

          {/* 하단 정보 */}
          <div style={{ padding: "8px 12px 10px", borderTop: "1px solid var(--border)", background: "rgba(255,255,255,0.01)" }}>
            <div className="flex items-center justify-between">
              <span style={{ fontSize: 9, color: "var(--t3)" }}>일일 손실 한도</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--t2)" }}>50만원</span>
            </div>
            <div className="flex items-center justify-between" style={{ marginTop: 2 }}>
              <span style={{ fontSize: 9, color: "var(--t3)" }}>수수료</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--t2)" }}>0.05% 양방향</span>
            </div>
          </div>
        </div>

        {/* ── 가운데: 차트 ── */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center justify-between shrink-0" style={{ padding: "8px 16px", borderBottom: "1px solid var(--border)", background: "var(--bg2)" }}>
            <div className="flex items-center gap-3">
              <span style={{ fontSize: 14, fontWeight: 700 }}>BTC / KRW</span>
              <span style={{ fontSize: 11, color: "var(--t3)" }}>업비트</span>
              {m.upbit_price > 0 && <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: "var(--blue2)" }}>{fmtP(m.upbit_price)}</span>}
            </div>
            <div className="flex items-center gap-2">
              {m.volume > 0 && <span className="mono" style={{ fontSize: 10, color: "var(--t3)" }}>거래량 {m.volume.toFixed(1)}</span>}
              <div className="flex items-center gap-1.5" style={{ background: live ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)", borderRadius: 5, padding: "2px 8px" }}>
                <div style={{ width: 5, height: 5, borderRadius: "50%", background: live ? "var(--green)" : "var(--red)", animation: live ? "pulse 2s ease infinite" : "none" }} />
                <span className="mono" style={{ fontSize: 9, fontWeight: 700, color: live ? "var(--green)" : "var(--red)" }}>{live ? "실시간" : "대기중"}</span>
              </div>
            </div>
          </div>
          <div className="flex-1 min-h-0" ref={chartRef} />
        </div>

        {/* ── 우측 패널 ── */}
        <div className="sidebar-right flex flex-col shrink-0" style={{ width: 280, borderLeft: "1px solid var(--border)", background: "var(--bg2)" }}>

          {/* 패널 전환 */}
          <div className="flex" style={{ borderBottom: "1px solid var(--border)" }}>
            {([["signals", "시그널"], ["strategies", "전략"]] as const).map(([key, label]) => (
              <button key={key} onClick={() => setPanel(key as any)} style={{
                flex: 1, padding: "10px 0", fontSize: 11, fontWeight: 600, border: "none", cursor: "pointer",
                letterSpacing: "0.03em",
                background: panel === key ? "rgba(59,130,246,0.08)" : "transparent",
                color: panel === key ? "var(--blue)" : "var(--t3)",
                borderBottom: panel === key ? "2px solid var(--blue)" : "2px solid transparent",
                transition: "all 0.15s"
              }}>{label}</button>
            ))}
          </div>

          {/* ─ 시그널 패널 ─ */}
          {panel === "signals" && (
            <>
              <div className="flex gap-1" style={{ padding: "8px 10px", borderBottom: "1px solid var(--border)" }}>
                {([["all", `전체 ${sigs.length}`], ["buy", `매수 ${counts.buy}`], ["sell", `매도 ${counts.sell}`]] as const).map(([key, label]) => (
                  <button key={key} className="tab-btn" onClick={() => setTab(key as any)} style={{
                    flex: 1,
                    background: tab === key ? "rgba(255,255,255,0.08)" : "transparent",
                    color: tab === key ? "var(--t1)" : key === "buy" ? "var(--green)" : key === "sell" ? "var(--red)" : "var(--t2)",
                  }}>{label}</button>
                ))}
              </div>

              <div className="flex-1 overflow-y-auto min-h-0" style={{ padding: "4px 6px" }}>
                {filtered.map((s, i) => {
                  const isBuy = s.action === "ENTRY";
                  const isBlk = s.action === "BLOCKED_BY_RISK";
                  const c = isBuy ? "var(--green)" : isBlk ? "var(--orange)" : "var(--red)";
                  const label = isBuy ? "매수" : isBlk ? "차단" : "매도";
                  return (
                    <div key={i} className="signal-row flex items-center gap-2.5" style={{ padding: "7px 8px", borderRadius: 8, marginBottom: 1, cursor: "default" }}>
                      <div style={{
                        width: 24, height: 24, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 10, fontWeight: 800, color: c, flexShrink: 0,
                        background: isBuy ? "rgba(34,197,94,0.12)" : isBlk ? "rgba(245,158,11,0.12)" : "rgba(239,68,68,0.12)",
                      }}>
                        {isBuy ? "\u25B2" : isBlk ? "!" : "\u25BC"}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div className="flex items-center justify-between">
                          <span style={{ fontSize: 11, fontWeight: 700, color: c }}>{label}</span>
                          <span className="mono" style={{ fontSize: 9, color: "var(--t3)" }}>{s.ts ? ago(s.ts) : ""}</span>
                        </div>
                        <div className="flex items-center justify-between" style={{ marginTop: 1 }}>
                          <span className="mono" style={{ fontSize: 10, color: "var(--t2)" }}>{fmtP(s.local)}</span>
                          <div className="flex items-center gap-1.5">
                            <span style={{ fontSize: 9, color: "var(--t3)", background: "rgba(255,255,255,0.04)", borderRadius: 3, padding: "1px 5px" }}>
                              {s.strategy.includes("LeadLag") ? "김프" : "모멘텀"}
                            </span>
                            {s.pnl !== undefined && (
                              <span className="mono" style={{ fontSize: 10, fontWeight: 700, color: s.pnl >= 0 ? "var(--green)" : "var(--red)" }}>
                                {s.pnl >= 0 ? "+" : ""}{fmt(s.pnl)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {filtered.length === 0 && (
                  <div className="flex flex-col items-center justify-center gap-2" style={{ height: "100%", opacity: 0.4 }}>
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--t3)" strokeWidth="1.5"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                    <p style={{ fontSize: 11, color: "var(--t3)" }}>시그널 대기중...</p>
                  </div>
                )}
              </div>

              <div style={{ padding: "8px 14px", borderTop: "1px solid var(--border)" }}>
                <div className="flex justify-between"><span style={{ fontSize: 10, color: "var(--t3)" }}>총 거래</span><span className="mono" style={{ fontSize: 11, fontWeight: 700 }}>{counts.buy + counts.sell}회</span></div>
                <div className="flex justify-between" style={{ marginTop: 2 }}>
                  <span style={{ fontSize: 10, color: "var(--t3)" }}>승률</span>
                  <span className="mono" style={{ fontSize: 11, fontWeight: 700, color: winRate >= 50 ? "var(--green)" : "var(--t2)" }}>{winRate.toFixed(1)}%</span>
                </div>
              </div>
            </>
          )}

          {/* ─ 전략 패널 ─ */}
          {panel === "strategies" && (
            <div style={{ padding: "12px", flex: 1, overflow: "auto" }}>
              {/* 김치 프리미엄 전략 */}
              <div className="card" style={{ padding: "14px", marginBottom: 8 }}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div style={{ width: 8, height: 8, borderRadius: 4, background: "var(--cyan)" }} />
                    <span style={{ fontSize: 12, fontWeight: 700 }}>김프 역이용 전략</span>
                  </div>
                  <div className={`toggle ${strats.leadlag ? "on" : ""}`} onClick={() => setStrats(s => ({ ...s, leadlag: !s.leadlag }))} />
                </div>
                <p style={{ fontSize: 10, color: "var(--t3)", marginTop: 8, lineHeight: 1.5 }}>
                  바이낸스(선행) 가격 변동 감지<br/>
                  역프리미엄 매수 &rarr; 정상 복귀 시 매도
                </p>
                <div className="grid grid-cols-2 gap-2" style={{ marginTop: 10 }}>
                  <div className="stat-box">
                    <p style={{ fontSize: 8, color: "var(--t3)", letterSpacing: "0.08em" }}>진입 조건</p>
                    <p className="mono" style={{ fontSize: 12, fontWeight: 700, color: "var(--cyan)" }}>&le; -2.0%</p>
                  </div>
                  <div className="stat-box">
                    <p style={{ fontSize: 8, color: "var(--t3)", letterSpacing: "0.08em" }}>청산 조건</p>
                    <p className="mono" style={{ fontSize: 12, fontWeight: 700, color: "var(--green)" }}>&ge; +0.5%</p>
                  </div>
                </div>
                <div className="flex items-center gap-2" style={{ marginTop: 8 }}>
                  <span className="badge" style={{ background: "rgba(6,182,212,0.1)", color: "var(--cyan)" }}>환율 1,400</span>
                  <span className="badge" style={{ background: "rgba(255,255,255,0.04)", color: "var(--t3)" }}>500만원 배정</span>
                </div>
              </div>

              {/* 모멘텀 돌파 전략 */}
              <div className="card" style={{ padding: "14px" }}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div style={{ width: 8, height: 8, borderRadius: 4, background: "var(--orange)" }} />
                    <span style={{ fontSize: 12, fontWeight: 700 }}>모멘텀 돌파 전략</span>
                  </div>
                  <div className={`toggle ${strats.momentum ? "on" : ""}`} onClick={() => setStrats(s => ({ ...s, momentum: !s.momentum }))} />
                </div>
                <p style={{ fontSize: 10, color: "var(--t3)", marginTop: 8, lineHeight: 1.5 }}>
                  최근 고점 돌파 + 거래량 급증 시 진입<br/>
                  트레일링 스탑 + 손절 이중 안전장치
                </p>
                <div className="grid grid-cols-3 gap-2" style={{ marginTop: 10 }}>
                  <div className="stat-box">
                    <p style={{ fontSize: 8, color: "var(--t3)", letterSpacing: "0.08em" }}>거래량</p>
                    <p className="mono" style={{ fontSize: 12, fontWeight: 700, color: "var(--orange)" }}>1.5배</p>
                  </div>
                  <div className="stat-box">
                    <p style={{ fontSize: 8, color: "var(--t3)", letterSpacing: "0.08em" }}>추적</p>
                    <p className="mono" style={{ fontSize: 12, fontWeight: 700, color: "var(--red)" }}>-1%</p>
                  </div>
                  <div className="stat-box">
                    <p style={{ fontSize: 8, color: "var(--t3)", letterSpacing: "0.08em" }}>손절</p>
                    <p className="mono" style={{ fontSize: 12, fontWeight: 700, color: "var(--red)" }}>-2%</p>
                  </div>
                </div>
                <div className="flex items-center gap-2" style={{ marginTop: 8 }}>
                  <span className="badge" style={{ background: "rgba(245,158,11,0.1)", color: "var(--orange)" }}>5틱 기준</span>
                  <span className="badge" style={{ background: "rgba(255,255,255,0.04)", color: "var(--t3)" }}>500만원 배정</span>
                </div>
              </div>

              {/* 리스크 관리 */}
              <div style={{ marginTop: 12, padding: "12px", background: "rgba(255,255,255,0.02)", borderRadius: 10, border: "1px solid var(--border)" }}>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--t3)", letterSpacing: "0.08em", marginBottom: 8 }}>리스크 관리</p>
                <div className="flex items-center justify-between" style={{ marginBottom: 4 }}>
                  <span style={{ fontSize: 11, color: "var(--t2)" }}>일일 손실 한도</span>
                  <span className="mono" style={{ fontSize: 11, fontWeight: 700 }}>500,000원</span>
                </div>
                <div className="flex items-center justify-between" style={{ marginBottom: 4 }}>
                  <span style={{ fontSize: 11, color: "var(--t2)" }}>최대 연속 손실</span>
                  <span className="mono" style={{ fontSize: 11, fontWeight: 700 }}>5회</span>
                </div>
                <div className="flex items-center justify-between">
                  <span style={{ fontSize: 11, color: "var(--t2)" }}>거래 수수료</span>
                  <span className="mono" style={{ fontSize: 11, fontWeight: 700 }}>0.05% 양방향</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      {/* ═══ 모바일 하단바 ═══ */}
      <div className="mobile-bar items-center justify-between shrink-0" style={{ height: 48, padding: "0 16px", background: "var(--bg2)", borderTop: "1px solid var(--border)" }}>
        <div className="flex items-center gap-2">
          <div className={live ? "live-pulse" : ""} style={live ? {} : { width: 7, height: 7, borderRadius: "50%", background: "var(--red)" }} />
          <span className="mono" style={{ fontSize: 12, fontWeight: 700 }}>{m.upbit_price > 0 ? fmtP(m.upbit_price) : "---"}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="mono" style={{ fontSize: 12, fontWeight: 700, color: pnl >= 0 ? "var(--green)" : "var(--red)" }}>
            {pnl >= 0 ? "+" : ""}{fmt(pnl)}
          </span>
          <span className="badge" style={{ background: prem >= 0 ? "rgba(34,197,94,0.12)" : "rgba(239,68,68,0.12)", color: prem >= 0 ? "var(--green)" : "var(--red)" }}>
            {prem >= 0 ? "+" : ""}{prem.toFixed(2)}%
          </span>
        </div>
      </div>
    </div>
  );
}
