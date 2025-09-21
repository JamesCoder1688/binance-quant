# ws_buy1_dual.py
# -*- coding: utf-8 -*-
"""
WebSocket + 双层信号（预警/确认）
- 订阅：
  BTCUSDT: 4h, 1h
  DOGEUSDT: 1h, 15m, 1m
- 触发：
  1) 预警：任何 DOGE kline 推送且 x=false 时（节流控制）
  2) 确认：任何订阅 kline 推送且 x=true 时
口径保持：
  - 24h振幅 = (high-low)/low*100
  - 24h涨幅 = priceChangePercent
  - 触碰口径 = 影线法
"""

import json
import math
import time
import requests
import websocket
from typing import List, Dict, Tuple

BINANCE = "https://api.binance.com"

# ---------- 基础工具 ----------
def to_f(x): return float(x)

def get_24hr_ticker(symbol: str) -> Dict:
    r = requests.get(f"{BINANCE}/api/v3/ticker/24hr", params={"symbol": symbol}, timeout=10)
    r.raise_for_status()
    return r.json()

def klines(symbol: str, interval: str, limit: int=200) -> List[Dict]:
    r = requests.get(f"{BINANCE}/api/v3/klines", params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10)
    r.raise_for_status()
    data = r.json()
    return [{
        "open":  float(k[1]),
        "high":  float(k[2]),
        "low":   float(k[3]),
        "close": float(k[4]),
        "openTime":  int(k[0]),
        "closeTime": int(k[6]),
    } for k in data]

# ---------- 24h 振幅/涨幅 ----------
def amp_chg_24h(tkr: Dict) -> Tuple[float,float]:
    amp24 = (to_f(tkr["highPrice"]) - to_f(tkr["lowPrice"])) / to_f(tkr["lowPrice"]) * 100.0  # 口径A
    chg24 = float(tkr["priceChangePercent"])
    return amp24, chg24

# ---------- KDJ(9,3,3) ----------
def kdj_max_at(ohlc: List[Dict], idx: int=-1, n: int=9) -> float:
    L = len(ohlc)
    if L < n: raise ValueError(f"KDJ需要至少 {n} 根K线")
    pos = L + idx if idx < 0 else idx
    if pos < n-1: raise ValueError("数据不足以在该索引处计算KDJ")
    K = D = J = 50.0
    for i in range(0, pos+1):
        if i < n-1: 
            continue
        win = ohlc[i-n+1:i+1]
        h9 = max(c["high"] for c in win)
        l9 = min(c["low"]  for c in win)
        c  = ohlc[i]["close"]
        RSV = 50.0 if h9==l9 else (c - l9) / (h9 - l9) * 100.0
        K = (2/3)*K + (1/3)*RSV
        D = (2/3)*D + (1/3)*K
        J = 3*K - 2*D
    return max(K,D,J)

# ---------- BOLL(20,2) ----------
def _mean(vals): return sum(vals)/len(vals)
def _std(vals):
    m = _mean(vals)
    return math.sqrt(sum((v-m)**2 for v in vals)/len(vals))  # population std

def boll_at(ohlc: List[Dict], idx: int=-1, n: int=20, k: float=2.0) -> Tuple[float,float,float]:
    closes = [c["close"] for c in ohlc]
    L = len(closes)
    if L < n: raise ValueError(f"BOLL需要至少 {n} 根K线")
    pos = L + idx if idx < 0 else idx
    if pos < n-1: raise ValueError("数据不足以在该索引处计算BOLL")
    win = closes[pos-n+1:pos+1]
    mb = _mean(win); sd = _std(win)
    up = mb + k*sd;  dn = mb - k*sd
    return mb, up, dn

# ---------- 影线法触碰 ----------
def touch_dn_by_wick(low: float, dn: float) -> bool:  return low <= dn
def touch_mb_by_wick(low: float, high: float, mb: float) -> bool: return low <= mb <= high
def touch_up_by_wick(high: float, up: float) -> bool: return high >= up

# ---------- 单次计算：提示买点1 ----------
def _buy1_once(idx_last: int) -> Tuple[bool, Dict]:
    # BTC 24h
    tkr = get_24hr_ticker("BTCUSDT")
    amp24, chg24 = amp_chg_24h(tkr)
    # BTC KDJ
    btc4h = klines("BTCUSDT","4h",200)
    btc1h = klines("BTCUSDT","1h",200)
    kdj_btc_4h = kdj_max_at(btc4h, idx=idx_last)
    kdj_btc_1h = kdj_max_at(btc1h, idx=idx_last)
    BTC_ok = ((amp24 < 3.0) or (chg24 > 1.0)) and (kdj_btc_4h < 50.0) and (kdj_btc_1h < 50.0)
    if not BTC_ok:
        return False, {
            "btc_ok": False, "amp24": amp24, "chg24": chg24,
            "kdj_btc_4h": kdj_btc_4h, "kdj_btc_1h": kdj_btc_1h
        }
    # DOGE 指标
    d1h  = klines("DOGEUSDT","1h",200)
    d15m = klines("DOGEUSDT","15m",200)
    d1m  = klines("DOGEUSDT","1m",200)
    MB1h, UP1h, DN1h = boll_at(d1h,  idx=idx_last)
    MB15, UP15, DN15 = boll_at(d15m, idx=idx_last)
    def hi_lo(ohlc, idx):
        L = len(ohlc); pos = L+idx if idx<0 else idx
        return ohlc[pos]["high"], ohlc[pos]["low"]
    H1h, L1h = hi_lo(d1h,  idx_last)
    H15, L15 = hi_lo(d15m, idx_last)
    KDJ1h  = kdj_max_at(d1h,  idx=idx_last)
    KDJ15m = kdj_max_at(d15m, idx=idx_last)
    KDJ1m  = kdj_max_at(d1m,  idx=idx_last)
    touch_dn_1h  = touch_dn_by_wick(L1h, DN1h)
    touch_dn_15m = touch_dn_by_wick(L15, DN15)
    BUY_1 = (touch_dn_1h and (KDJ1h  < 10.0)) \
         and (touch_dn_15m and (KDJ15m < 20.0)) \
         and (KDJ1m < 20.0)
    info = {
        "btc_ok": True, "amp24": amp24, "chg24": chg24,
        "kdj_btc_4h": kdj_btc_4h, "kdj_btc_1h": kdj_btc_1h,
        "doge": {
            "1h":  {"touch": "DN" if touch_dn_1h else "NONE",  "KDJ": KDJ1h,  "MB": MB1h,  "UP": UP1h, "DN": DN1h, "H": H1h, "L": L1h},
            "15m": {"touch": "DN" if touch_dn_15m else "NONE", "KDJ": KDJ15m, "MB": MB15, "UP": UP15, "DN": DN15, "H": H15, "L": L15},
            "1m":  {"KDJ": KDJ1m}
        }
    }
    return bool(BUY_1), info

def buy_signal_1_realtime() -> Tuple[bool, Dict]:
    return _buy1_once(idx_last=-1)   # 预警：用正在形成的K线

def buy_signal_1_confirmed() -> Tuple[bool, Dict]:
    return _buy1_once(idx_last=-2)   # 确认：用上一根收盘的K线

# ---------- WebSocket 订阅 ----------
STREAMS = [
    "btcusdt@kline_4h",
    "btcusdt@kline_1h",
    "dogeusdt@kline_1h",
    "dogeusdt@kline_15m",
    "dogeusdt@kline_1m",
]
WS_URL = "wss://stream.binance.com:9443/stream?streams=" + "/".join(STREAMS)

_last_realtime_ts = 0  # 预警节流（秒）
REALTIME_COOLDOWN = 10  # 每 10 秒最多跑一次预警，避免过多请求

def on_message(ws, message):
    global _last_realtime_ts
    try:
        data = json.loads(message)
        if "data" not in data: 
            return
        evt = data["data"]
        if evt.get("e") != "kline":
            return
        k = evt["k"]
        sym = k["s"]
        itv = k["i"]
        closed = k["x"]

        # ---- 确认信号：任意订阅的K线收盘时跑一次 ----
        if closed:
            ok_cf, info_cf = buy_signal_1_confirmed()
            print(f"✅ [CONFIRMED] signal={ok_cf}  sym={sym} interval={itv}  info={info_cf}")
            return

        # ---- 预警信号：仅在 DOGE 的K线进行中时节流触发 ----
        if sym == "DOGEUSDT":
            now = time.time()
            if now - _last_realtime_ts >= REALTIME_COOLDOWN:
                _last_realtime_ts = now
                ok_rt, info_rt = buy_signal_1_realtime()
                print(f"📡 [REALTIME]  signal={ok_rt}  sym={sym} interval={itv}  info={info_rt}")

    except Exception as e:
        print("❌ on_message error:", e)

def on_error(ws, error):
    print("❌ WS Error:", error)

def on_close(ws, code, msg):
    print("🔌 WS Closed:", code, msg)

def on_open(ws):
    print("🚀 WS Connected:", WS_URL)

def run_ws_forever():
    while True:
        try:
            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as e:
            print("⚠️ WS reconnect in 5s, reason:", e)
            time.sleep(5)

if __name__ == "__main__":
    run_ws_forever()
