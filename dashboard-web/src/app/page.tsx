"use client";

import { useEffect, useState, useRef } from "react";
import { createChart, IChartApi, ISeriesApi } from "lightweight-charts";
import { Activity, ArrowRightLeft, TrendingUp, AlertCircle } from "lucide-react";

interface MarketState {
  upbit_price: number;
  binance_price: number;
  price: number;
  volume: number;
}

interface Signal {
  type: string;
  strategy: string;
  action: string;
  local: number;
  global: number;
}

interface Portfolio {
  KRW: number;
  BTC: number;
  Equity: number;
}

export default function Dashboard() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  const [marketState, setMarketState] = useState<MarketState>({
    upbit_price: 0,
    binance_price: 0,
    price: 0,
    volume: 0,
  });
  const [portfolio, setPortfolio] = useState<Portfolio>({ KRW: 10000000, BTC: 0, Equity: 10000000 });
  const [signals, setSignals] = useState<Signal[]>([]);
  const [connected, setConnected] = useState(false);

  // Initialize Chart
  useEffect(() => {
    if (chartContainerRef.current && !chartRef.current) {
      chartRef.current = createChart(chartContainerRef.current, {
        width: chartContainerRef.current.clientWidth,
        height: 400,
        layout: {
          background: { color: "#1e293b" }, // slate-800
          textColor: "#cbd5e1", // slate-300
        },
        grid: {
          vertLines: { color: "#334155" }, // slate-700
          horzLines: { color: "#334155" }, // slate-700
        },
        timeScale: {
          timeVisible: true,
          secondsVisible: true,
        },
      });

      seriesRef.current = chartRef.current.addLineSeries({
        color: "#3b82f6", // blue-500
        lineWidth: 2,
      });
    }

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []);

  // WebSocket Connection
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "tick") {
        setMarketState(data.state);
        if (data.portfolio) setPortfolio(data.portfolio);
        
        // Update chart
        if (seriesRef.current && data.state.upbit_price > 0) {
          const timestamp = Math.floor(Date.now() / 1000);
          try {
             seriesRef.current.update({
               time: timestamp as any,
               value: data.state.upbit_price,
             });
          } catch (e) {
            // Ignore duplicate time errors on rapid ticks
          }
        }
      } else if (data.type === "signal") {
        setSignals((prev) => [data, ...prev].slice(0, 15));
      }
    };

    return () => ws.close();
  }, []);

  const premium =
    marketState.binance_price > 0
      ? ((marketState.upbit_price - marketState.binance_price * 1400) / (marketState.binance_price * 1400)) * 100
      : 0;

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto space-y-6">
      <header className="flex items-center justify-between pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Latency Edge ⚡
          </h1>
          <p className="text-slate-400 mt-1">Daily Trading Strategy Platform</p>
        </div>
        <div className="flex items-center gap-3 bg-slate-800 px-4 py-2 rounded-full border border-slate-700">
          <div className={`w-3 h-3 rounded-full ${connected ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" : "bg-red-500"}`} />
          <span className="text-sm font-medium text-slate-300">
            {connected ? "Live Engine Connected" : "Connecting to Engine..."}
          </span>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Market Stats */}
        <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700/50 backdrop-blur-sm">
          <div className="flex items-center gap-3 mb-4 text-slate-400">
            <Activity className="w-5 h-5" />
            <h2 className="font-semibold">Local Market (Upbit)</h2>
          </div>
          <p className="text-3xl font-bold text-slate-100">
            ₩{marketState.upbit_price.toLocaleString()}
          </p>
        </div>

        <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700/50 backdrop-blur-sm">
          <div className="flex items-center gap-3 mb-4 text-slate-400">
            <ArrowRightLeft className="w-5 h-5" />
            <h2 className="font-semibold">Global Market (Binance)</h2>
          </div>
          <p className="text-3xl font-bold text-slate-100">
            ${marketState.binance_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        </div>

        <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700/50 backdrop-blur-sm">
          <div className="flex items-center gap-3 mb-4 text-slate-400">
            <TrendingUp className="w-5 h-5" />
            <h2 className="font-semibold">Kimchi Premium</h2>
          </div>
          <p className={`text-3xl font-bold ${premium > 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {premium.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Virtual Portfolio */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/80 rounded-2xl p-6 border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
          <h2 className="text-slate-400 font-semibold mb-2 text-sm uppercase tracking-wider">Total Equity (KRW)</h2>
          <p className="text-3xl font-bold text-emerald-400">₩{portfolio.Equity.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
        </div>
        <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700/50">
          <h2 className="text-slate-400 font-semibold mb-2 text-sm uppercase tracking-wider">Available KRW</h2>
          <p className="text-2xl font-bold text-slate-200">₩{portfolio.KRW.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
        </div>
        <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700/50">
          <h2 className="text-slate-400 font-semibold mb-2 text-sm uppercase tracking-wider">Holding BTC</h2>
          <p className="text-2xl font-bold text-slate-200">{portfolio.BTC.toFixed(6)} ₿</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2 bg-slate-800/50 rounded-2xl border border-slate-700/50 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-700/50 flex justify-between items-center">
             <h2 className="font-semibold text-slate-200">Live Price Action</h2>
             <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">KRW-BTC</span>
          </div>
          <div ref={chartContainerRef} className="flex-1 w-full relative" />
        </div>

        {/* Signals Feed */}
        <div className="bg-slate-800/50 rounded-2xl border border-slate-700/50 flex flex-col h-[500px]">
          <div className="p-4 border-b border-slate-700/50 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-indigo-400" />
            <h2 className="font-semibold text-slate-200">Live Signal Feed</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {signals.map((sig, idx) => (
              <div 
                key={idx} 
                className={`p-3 rounded-lg border ${
                  sig.action === "ENTRY" 
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" 
                    : "bg-rose-500/10 border-rose-500/20 text-rose-400"
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-sm">{sig.action}</span>
                  <span className="text-xs opacity-70">{sig.strategy}</span>
                </div>
                <div className="text-xs opacity-80 flex justify-between">
                  <span>Local: {sig.local}</span>
                  <span>Global: {sig.global}</span>
                </div>
              </div>
            ))}
            {signals.length === 0 && (
               <div className="text-center text-slate-500 py-10 text-sm">Waiting for incoming signals...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
